import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from .types import Config, StrategyTemplates


class ConfigLoader:
    def __init__(self):
        self.template_dir = Path(__file__).parent / "templates"
        self.config: Optional[Config] = None

    def load_config(self, config_dict: Dict[str, Any]) -> Config:
        """Load and validate configuration"""
        # Load strategy templates
        strategy_templates = self._load_strategy_templates()

        # Create config with templates
        self.config = Config(
            **config_dict,
            strategy_templates=strategy_templates
        )
        return self.config

    def _load_strategy_templates(self) -> StrategyTemplates:
        """Load strategy templates"""
        template_path = self.template_dir / "strategy_templates.yaml"
        if not template_path.exists():
            raise FileNotFoundError(
                f"Strategy templates not found at {template_path}")

        with open(template_path, 'r') as f:
            templates = yaml.safe_load(f)
            return StrategyTemplates(**templates)

    def get_strategy_template(self, strategy_type: str, template_name: str = "default") -> Dict[str, Any]:
        """Get strategy template configuration"""
        if not self.config or not self.config.strategy_templates:
            raise RuntimeError("Configuration not loaded")

        templates = self.config.strategy_templates
        if strategy_type == "ma_crossover":
            return templates.ma_crossover[template_name].dict()
        elif strategy_type == "vwap":
            return templates.vwap[template_name].dict()
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

    def get_db_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        return self.config.database.dict()

    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration"""
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        return self.config.redis.dict()

    def get_jupiter_config(self) -> Dict[str, Any]:
        """Get Jupiter configuration"""
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        return self.config.jupiter.dict()

    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration"""
        if not self.config:
            raise RuntimeError("Configuration not loaded")
        return self.config.api.dict()


# Create a singleton instance
config = ConfigLoader()
