import logging


class LogFilter(logging.Filter):
    def filter(self, record):
        return record.name.startswith("myapp")


def get_logger() -> logging.Logger:
    logger = logging.getLogger("myapp")
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler("app.log")
    file_handler.setLevel(logging.INFO)

    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(log_format)

    logger.addHandler(file_handler)
    logger.addFilter(LogFilter())

    return logger
