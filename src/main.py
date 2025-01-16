import asyncio
import logging
import uvicorn
import yaml
import sys

from .api import APIServer, app
from .integration import TradingSystem
from .config.loader import config as config_loader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def start_application(config_path: str):
    """Start the trading application"""
    try:
        # Load configuration
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)

        # Load and validate configuration
        config = config_loader.load_config(config_dict)

        # Initialize components
        trading_system = TradingSystem(config)

        # Initialize API components
        api_server = APIServer(trading_system, config)

        # Start trading system
        await trading_system.start()

        # Start API server
        await api_server.start()

        # Run FastAPI application
        uvicorn_config = uvicorn.Config(
            app,
            host=config.api.host,
            port=config.api.port,
            log_level="info"
        )
        server = uvicorn.Server(uvicorn_config)
        await server.serve()

    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")
        raise


async def stop_application(
    trading_system: TradingSystem,
    api_server: APIServer,
):
    """Stop the trading application"""
    try:
        # Stop API server first to prevent new requests
        logger.info("Stopping API server...")
        await api_server.stop()

        # Stop trading system
        logger.info("Stopping trading system...")
        await trading_system.stop()

        logger.info("Shutdown completed successfully")

    except Exception as e:
        logger.error(f"Error stopping application: {str(e)}")
        raise


def main():
    """Main entry point"""
    try:
        if len(sys.argv) != 2:
            print("Usage: python -m src.main config.yaml")
            sys.exit(1)

        config_path = sys.argv[1]

        # Run application
        asyncio.run(start_application(config_path))

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutdown complete.")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
