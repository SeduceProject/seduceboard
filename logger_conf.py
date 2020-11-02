import logging
from logging.handlers import RotatingFileHandler

formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%d-%b-%H:%M:%S')


def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = RotatingFileHandler(log_file, maxBytes=20000000, backupCount=5)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def setup_root_logger(log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = RotatingFileHandler(log_file, maxBytes=20000000, backupCount=5)
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
