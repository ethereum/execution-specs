"""
Custom Logging Module
^^^^^^^^^^^^^^^^^^^^^
Provides a CustomLogger class and a setup_logger function
to configure the logger using logger.cfg.
"""
import configparser
import logging
import logging.config
import os


def setup_logger(name):
    """
    Set up a logger with the provided name using the 'logger.cfg' file.
    """
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logger.cfg"))
    logging.config.fileConfig(config, disable_existing_loggers=False)

    logger = logging.getLogger(name)

    return logger
