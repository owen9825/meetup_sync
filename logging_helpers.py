import logging
import sys

# https://stackoverflow.com/a/56944256/1495729
_gray = "\x1b[38;20m"
_yellow = "\x1b[33;20m"
_red = "\x1b[31;20m"
_bold_red = "\x1b[31;1m"
_reset = "\x1b[0m"
_formatting_string = "%(levelname)s %(name)s:%(lineno)d| %(message)s"


_LOGGING_FORMATS = {
    logging.DEBUG: _gray + _formatting_string + _reset,
    logging.INFO: _formatting_string,
    logging.WARNING: _yellow + _formatting_string + _reset,
    logging.ERROR: _red + _formatting_string + _reset,
    logging.CRITICAL: _bold_red + _formatting_string + _reset,
}


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        log_fmt = _LOGGING_FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def get_colored_logger(log_level=logging.INFO) -> logging.Logger:
    # This is intended for readers using the command line
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter())
    logger.addHandler(handler)
    return logger
