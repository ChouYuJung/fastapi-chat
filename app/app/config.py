import logging
import logging.config
from datetime import datetime
from typing import Text

import pytz
from colorama import Fore, Style, init
from pydantic_settings import BaseSettings

from .version import VERSION

init(autoreset=True)


class Settings(BaseSettings):
    app_name: Text = "fastapi-app-service"
    app_version: Text = VERSION

    # OAuth2
    token_url: Text = "token"
    SECRET_KEY: Text = (
        "ce7ea672b396d1e36d1b64d725414bee9529a84c8a73ba32fd0eb57e7298a5fa"
    )
    ALGORITHM: Text = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


settings = Settings()


class IsoDatetimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        record_datetime = datetime.fromtimestamp(record.created).astimezone(
            pytz.timezone("Asia/Taipei")
        )
        t = record_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        z = record_datetime.strftime("%z")
        ms_exp = record_datetime.microsecond // 1000
        s = f"{t}.{ms_exp:03d}{z}"
        return s


class ColoredIsoDatetimeFormatter(IsoDatetimeFormatter):
    COLORS = {
        "WARNING": Fore.YELLOW,
        "INFO": Fore.GREEN,
        "DEBUG": Fore.BLUE,
        "CRITICAL": Fore.RED,
        "ERROR": Fore.RED,
    }
    MSG_COLORS = {
        "WARNING": Fore.YELLOW,
        "INFO": Fore.GREEN,
        "CRITICAL": Fore.RED,
        "ERROR": Fore.RED,
    }

    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                self.COLORS[levelname] + f"{levelname:8s}" + Style.RESET_ALL
            )
            record.name = Fore.BLUE + record.name + Style.RESET_ALL
            if levelname in self.MSG_COLORS:
                record.msg = self.COLORS[levelname] + record.msg + Style.RESET_ALL
        return super(ColoredIsoDatetimeFormatter, self).format(record)


def default_logging_config():
    d = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "basic_formatter": {
                "()": ColoredIsoDatetimeFormatter,
                "format": "%(asctime)s %(levelname)-8s %(name)s  - %(message)s",
            },
            "message_formatter": {"format": "%(message)s"},
        },
        "handlers": {
            "console_handler": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "basic_formatter",
            }
        },
        "loggers": {
            settings.app_name: {
                "level": "DEBUG",
                "handlers": ["console_handler"],
                "propagate": True,
            }
        },
    }
    return d


logging.config.dictConfig(default_logging_config())
logger = logging.getLogger(settings.app_name)
