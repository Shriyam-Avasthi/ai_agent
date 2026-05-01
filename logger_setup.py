import logging
import sys


def setup_logger(verbose: bool) -> logging.Logger:
    """Configures and returns the main application logger."""
    logger = logging.getLogger("ai_agent")

    if not logger.handlers:
        log_level = logging.DEBUG if verbose else logging.INFO
        logger.setLevel(log_level)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger


logger = logging.getLogger("ai_agent")
