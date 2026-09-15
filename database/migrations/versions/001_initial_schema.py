"""Initial schema for HR Knowledge Assistant RAG

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-15 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # 1. documents table (T017)
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('file_name', sa.String(512), nullable=False),
        sa.Column('file_type', sa.String(32), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('status', sa.String(32), nullable=False, server_default='PENDING'),
        sa.Column('title', sa.String(512), nullable=True),
        sa.Column('document_category', sa.String(128), nullable=True),
        sa.Column('storage_path', sa.String(1024), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint(
            "status IN ('PENDING', 'UPLOADING', 'PROCESSING', 'INDEXING', 'READY', 'FAILED', 'DELETED')",
            name='ck_documents_status'
        )
    )
    op.create_index('ix_documents_content_hash', 'documents', ['content_hash'])
    op.create_index('ix_documents_status', 'documents', ['status'])

    # 2. document_versions table (T018)
    op.create_table(
        'document_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('parser_version', sa.String(32), nullable=False, server_default='1.0.0'),
        sa.Column('embedding_model', sa.String(128), nullable=False),
        sa.Column('embedding_dim', sa.Integer(), nullable=False, server_default='1536'),
        sa.Column('index_version', sa.String(32), nullable=False, server_default='v1'),
        sa.Column('effective_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_document_versions_document_id', 'document_versions', ['document_id'])
    op.create_index(
        'uq_document_current_version',
        'document_versions',
        ['document_id'],
        unique=True,
        postgresql_where=sa.text('is_current = true')
    )

    # 3. document_chunks table (T019)
    op.create_table(
        'document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('document_version_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('document_versions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('section', sa.String(512), nullable=True),
        sa.Column('parent_section', sa.String(512), nullable=True),
        sa.Column('sheet_name', sa.String(256), nullable=True),
        sa.Column('row_start', sa.Integer(), nullable=True),
        sa.Column('row_end', sa.Integer(), nullable=True),
        sa.Column('is_ocr', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('embedding', Vector(1536), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    # Add generated tsvector column
    op.execute(
        "ALTER TABLE document_chunks ADD COLUMN tsvector_content tsvector "
        "GENERATED ALWAYS AS (to_tsvector('english', content)) STORED"
    )
    op.create_index('ix_chunks_document_version_id', 'document_chunks', ['document_version_id'])
    op.create_index('uq_version_chunk_index', 'document_chunks', ['document_version_id', 'chunk_index'], unique=True)
    op.create_index('ix_chunks_tsvector', 'document_chunks', ['tsvector_content'], postgresql_using='gin')
    # HNSW Index for vector search
    op.execute(
        "CREATE INDEX ix_chunks_embedding_hnsw ON document_chunks "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 128)"
    )

    # 4. conversations table (T020)
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('title', sa.String(512), nullable=False, server_default='New Conversation'),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    # 5. rag_runs table (T022)
    op.create_table(
        'rag_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('request_id', sa.String(64), nullable=False, unique=True),
        sa.Column('trace_id', sa.String(64), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('rewritten_queries', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('intent', sa.String(64), nullable=True),
        sa.Column('domain', sa.String(64), nullable=True),
        sa.Column('retrieval_mode', sa.String(64), nullable=True),
        sa.Column('reranker', sa.String(64), nullable=True),
        sa.Column('retrieved_chunk_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default='{}'),
        sa.Column('selected_chunk_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default='{}'),
        sa.Column('retrieval_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('context_token_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('llm_model', sa.String(64), nullable=False, server_default='gpt-4o-mini'),
        sa.Column('input_token_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('output_token_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('generation_latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('citation_validation_result', sa.String(32), nullable=True),
        sa.Column('groundedness_result', sa.String(32), nullable=True),
        sa.Column('guardrail_result', sa.String(32), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('final_answer_status', sa.String(32), nullable=False, server_default='SUCCESS'),
        sa.Column('error_detail', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_rag_runs_conversation_id', 'rag_runs', ['conversation_id'])
    op.create_index('ix_rag_runs_request_id', 'rag_runs', ['request_id'])

    # 6. messages table (T021)
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(16), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('rag_run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rag_runs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('citations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant', 'system')", name='ck_message_role')
    )
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])

    # 7. evaluation tables (T023)
    op.create_table(
        'evaluation_datasets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(128), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(32), nullable=False, server_default='1.0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )

    op.create_table(
        'evaluation_cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('evaluation_datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('case_name', sa.String(128), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('expected_intent', sa.String(64), nullable=True),
        sa.Column('expected_domain', sa.String(64), nullable=True),
        sa.Column('ground_truth_answer', sa.Text(), nullable=True),
        sa.Column('reference_chunk_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default='{}'),
        sa.Column('expected_abstention', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_evaluation_cases_dataset_id', 'evaluation_cases', ['dataset_id'])

    op.create_table(
        'evaluation_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dataset_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('evaluation_datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('evaluation_cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('precision_score', sa.Float(), nullable=True),
        sa.Column('recall_score', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        sa.Column('mrr_score', sa.Float(), nullable=True),
        sa.Column('hit_rate_score', sa.Float(), nullable=True),
        sa.Column('faithfulness_score', sa.Float(), nullable=True),
        sa.Column('answer_relevance_score', sa.Float(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('passed', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_evaluation_results_run_id', 'evaluation_results', ['run_id'])
    op.create_index('ix_evaluation_results_dataset_id', 'evaluation_results', ['dataset_id'])
    op.create_index('ix_evaluation_results_case_id', 'evaluation_results', ['case_id'])


def downgrade() -> None:
    op.drop_table('evaluation_results')
    op.drop_table('evaluation_cases')
    op.drop_table('evaluation_datasets')
    op.drop_table('messages')
    op.drop_table('rag_runs')
    op.drop_table('conversations')
    op.drop_table('document_chunks')
    op.drop_table('document_versions')
    op.drop_table('documents')
