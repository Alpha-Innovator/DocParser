import logging

APP_LOGGER_NAME: str = "APP"


def setup_app_level_logger(
    logger_name: str = APP_LOGGER_NAME,
    level: str = "DEBUG",
    file_name: str = "app_debug.log",
    mode: str = "w",
):
    """create a logger

    Args:
        logger_name (str, optional): name of the logger.
            Defaults to APP_LOGGER_NAME.
        level (str, optional): controls the output level.
            Defaults to 'DEBUG'.
        file_name (str, optional): path where the log is saved.
            Defaults to "app_debug.log".
        mode (str, optional): mode of the file.
            Defaults to 'w'.

        level option: {
            'CRITICAL': CRITICAL,
            'FATAL': FATAL,
            'ERROR': ERROR,
            'WARN': WARNING,
            'WARNING': WARNING,
            'INFO': INFO,
            'DEBUG': DEBUG,
            'NOTSET': NOTSET,}
    Returns:
        _type_: the logger object
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    formatter = logging.Formatter(
        "[%(levelname)-s]:%(filename)s %(funcName)s [Line %(lineno)s] - %(message)s"
    )

    # create file handler which logs even debug messages
    fh = logging.FileHandler(file_name, mode=mode)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def get_logger(module_name):
    return logging.getLogger(APP_LOGGER_NAME).getChild(module_name)
