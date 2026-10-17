"""Configuration per environment(dev/test/prod), read from environment variables or .env."""

import os
from dotenv import load_dotenv
load_dotenv()

dev_secret = "dev-only-change-me"

class config:
    SECRET_KEY = os.getenv("SECRET_KEY", dev_secret)
    MYSQL_HOST = os.getenv("MYSQL_HOST", 'localhost')
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "eyabantu")
    LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

class DevConfig(config):
        DEBUG = True

class TestConfig(config):
        Testing = True
        MYSQL_DB = os.getenv("MYSQL_TEST_DB", "eyabantu_test")

class ProdConfig(config):
        SESSION_COOKIE_SECURE = True

configs = {"dev":DevConfig, "test":TestConfig, "prod":ProdConfig}