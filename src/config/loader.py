import json
import os
from typing import Dict, Any
from pathlib import Path
from .env import get_env_config


class ConfigLoader:
    def __init__(self):
        self.env_config = get_env_config()
        self.template_dir = Path(__file__).parent / "templates"
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Any]:
        """Load all template configurations"""
        templates = {}
        for template_file in self.template_dir.glob("*.json"):
            with open(template_file, 'r') as f:
                templates[template_file.stem] = json.load(f)
        return templates

    def get_strategy_template(self, strategy_type: str, template_name: str = "default") -> Dict[str, Any]:
        """Get strategy template configuration"""
        strategy_templates = self.templates.get("strategy_templates", {})
        strategy_config = strategy_templates.get(strategy_type, {})
        return strategy_config.get(template_name, {})

    def get_data_processor_config(self, processor_type: str) -> Dict[str, Any]:
        """Get data processor configuration"""
        processor_templates = self.templates.get("data_processors", {})
        return processor_templates.get(processor_type, {})

    def get_db_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.env_config["database"]

    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration"""
        return self.env_config["redis"]

    def get_jupiter_config(self) -> Dict[str, Any]:
        """Get Jupiter configuration"""
        return self.env_config["jupiter"]

    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration"""
        return self.env_config["api"]

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.env_config["logging"]


# Create a singleton instance
config = ConfigLoader()
