import logging
from contextvars import ContextVar

request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_context.get() or "-"
        return True


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(
        logging.Formatter(
            "%(levelname)s %(name)s request_id=%(request_id)s %(message)s"
        )
    )
    logging.basicConfig(level=level, handlers=[handler], force=True)
