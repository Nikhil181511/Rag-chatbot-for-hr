import logging
import sys
from contextvars import ContextVar
import structlog
from app.config.settings import settings

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="")


def add_correlation_ids(logger, method_name, event_dict):
    req_id = request_id_ctx.get()
    if req_id:
        event_dict["request_id"] = req_id
    trc_id = trace_id_ctx.get()
    if trc_id:
        event_dict["trace_id"] = trc_id
    return event_dict


def setup_logging() -> None:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        add_correlation_ids,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.APP_ENV in ("production", "staging"):
        renderer_processor = structlog.processors.JSONRenderer()
    else:
        renderer_processor = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer_processor,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    for noisy_logger in ["uvicorn.access", "httpcore", "httpx", "urllib3"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def get_logger(name: str = __name__):
    return structlog.get_logger(name)
