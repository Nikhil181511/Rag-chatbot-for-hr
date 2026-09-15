import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config.settings import settings
from app.config.logging import setup_logging, get_logger, request_id_ctx, trace_id_ctx
from app.api.v1.health import router as health_router
from app.api.v1.documents import router as documents_router
from app.api.v1.chat import router as chat_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.suggestions import router as suggestions_router
from app.api.v1.knowledge_base import router as knowledge_base_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info(
        "Application starting up",
        app_env=settings.APP_ENV,
        llm_provider=settings.LLM_PROVIDER,
        embedding_provider=settings.EMBEDDING_PROVIDER,
        reranker_provider=settings.RERANKER_PROVIDER,
    )
    yield
    # Shutdown
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="HR Knowledge Assistant API",
        description="Enterprise RAG backend for HR policy lookup and employee assistance.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "Content-Type"],
    )

    # Request ID and correlation middleware
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        trc_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
        request_id_ctx.set(req_id)
        trace_id_ctx.set(trc_id)

        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Request-ID"] = req_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            return response
        except Exception as exc:
            logger.error("Unhandled exception processing request", exc_info=exc, path=request.url.path)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred while processing your request.",
                    }
                },
                headers={"X-Request-ID": req_id},
            )

    # Exception Handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        req_id = request_id_ctx.get()
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request payload.",
                    "details": exc.errors(),
                }
            },
            headers={"X-Request-ID": req_id},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        req_id = request_id_ctx.get()
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                }
            },
            headers={"X-Request-ID": req_id},
        )

    # Root health
    app.include_router(health_router)

    # V1 API Routers
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(conversations_router, prefix="/api/v1")
    app.include_router(suggestions_router, prefix="/api/v1")
    app.include_router(knowledge_base_router, prefix="/api/v1")

    return app


app = create_app()
