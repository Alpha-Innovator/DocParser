import logging

APP_LOGGER_NAME: str = "APP"


def setup_app_level_logger(
    logger_name: str = APP_LOGGER_NAME,
    level: str = "DEBUG",
    file_name: str = "app_debug.log",
    mode: str = "w",
) -> logging.Logger:
    """
    Set up an application-level logger.

    Args:
        logger_name (str): The name of the logger (default: APP_LOGGER_NAME).
        level (str): The log level (default: "DEBUG").
        file_name (str): The name of the log file (default: "app_debug.log").
        mode (str): The file mode for logging (default: "w").

    Returns:
        logging.Logger: The configured logger object.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    formatter = logging.Formatter(
        "[%(asctime)s - %(levelname)-s]:%(filename)s %(funcName)s [Line %(lineno)s] - %(message)s"
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


def get_logger(module_name: str) -> logging.Logger:
    """
    Return a logger with the specified module name.

    Args:
        module_name (str): The name of the module.

    Returns:
        logging.Logger: A logger object.
    """
    return logging.getLogger(APP_LOGGER_NAME).getChild(module_name)
