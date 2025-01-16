from typing import Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()


def get_env_config() -> Dict[str, Any]:
    """Load configuration from environment variables"""
    return {
        "database": {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "user": os.getenv("POSTGRES_USER", "trading_bot"),
            "password": os.getenv("POSTGRES_PASSWORD", ""),
            "database": os.getenv("POSTGRES_DB", "trading_bot"),
        },
        "redis": {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "password": os.getenv("REDIS_PASSWORD", None),
            "db": int(os.getenv("REDIS_DB", "0")),
        },
        "jupiter": {
            "rpc_endpoint": os.getenv("JUPITER_RPC_ENDPOINT"),
            "auth_token": os.getenv("JUPITER_AUTH_TOKEN"),
        },
        "api": {
            "secret_key": os.getenv("API_SECRET_KEY"),
        },
        "logging": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "format": os.getenv("LOG_FORMAT", "detailed"),
        }
    }
