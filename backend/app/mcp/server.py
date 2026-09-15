import asyncio
from fastapi import FastAPI
import uvicorn
from app.mcp.tools import HRDocumentMCPTools
from app.config.settings import settings

mcp_app = FastAPI(
    title="HR Knowledge Assistant MCP Server",
    description="Model Context Protocol server for scoped filesystem tools",
    version="1.0.0",
)


@mcp_app.get("/tools")
async def list_tools():
    return {
        "tools": [
            {
                "name": "list_uploaded_documents",
                "description": "List all HR files in upload directory",
                "parameters": {},
            },
            {
                "name": "read_document_excerpt",
                "description": "Read text excerpt from an uploaded document",
                "parameters": {
                    "file_name": {"type": "string", "description": "Name of the file"},
                    "max_chars": {"type": "integer", "default": 2000},
                },
            },
        ]
    }


@mcp_app.post("/tools/list_uploaded_documents")
async def tool_list_documents():
    return HRDocumentMCPTools.list_uploaded_documents()


@mcp_app.post("/tools/read_document_excerpt")
async def tool_read_excerpt(file_name: str, max_chars: int = 2000):
    return HRDocumentMCPTools.read_document_excerpt(file_name, max_chars)


def start_mcp_server():
    uvicorn.run(mcp_app, host=settings.MCP_SERVER_HOST, port=settings.MCP_SERVER_PORT)


if __name__ == "__main__":
    start_mcp_server()
