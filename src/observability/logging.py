import logging
import sys
import time

try:
    import structlog
    HAS_STRUCTLOG = True
except ImportError:
    structlog = None
    HAS_STRUCTLOG = False

def now_ts() -> float:
    """Retorna timestamp float com precisão de microssegundos."""
    return time.time()

class FallbackLogger:
    """Wrapper para compatibilidade quando structlog não estiver instalado."""
    def __init__(self, name: str, std_logger: logging.Logger):
        self.name = name
        self._logger = std_logger

    def info(self, event: str, **kwargs):
        extra_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
        msg = f"{event} | {extra_str}" if extra_str else event
        self._logger.info(msg)

    def warning(self, event: str, **kwargs):
        extra_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
        msg = f"{event} | {extra_str}" if extra_str else event
        self._logger.warning(msg)

    def error(self, event: str, **kwargs):
        extra_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
        msg = f"{event} | {extra_str}" if extra_str else event
        self._logger.error(msg)

    def debug(self, event: str, **kwargs):
        extra_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
        msg = f"{event} | {extra_str}" if extra_str else event
        self._logger.debug(msg)

def setup_logger(name: str, level: str = "INFO"):
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    if HAS_STRUCTLOG:
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        formatter = logging.Formatter("%(message)s")
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        
        root_logger = logging.getLogger(name)
        root_logger.addHandler(handler)
        root_logger.setLevel(log_level)
        return structlog.get_logger(name)
    else:
        root_logger = logging.getLogger(name)
        if not root_logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s")
            handler.setFormatter(formatter)
            root_logger.addHandler(handler)
        root_logger.setLevel(log_level)
        return FallbackLogger(name, root_logger)
