import asyncio
import logging
import uvicorn
from typing import Dict, Any
import yaml
import signal
import sys

from .api import APIServer, app, RateLimiter, RateLimitMiddleware, AuthHandler
from .trading_system import TradingSystem
from .config.loader import ConfigLoader
from .events import EventManager, EventType

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GracefulShutdown:
    def __init__(self):
        self.shutdown = False
        self.trading_system = None
        self.api_server = None
        self.event_manager = None
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        if self.shutdown:
            logger.warning("Forced shutdown requested, exiting immediately...")
            sys.exit(1)

        logger.info("Shutdown signal received, starting graceful shutdown...")
        self.shutdown = True

        # Create and run shutdown task
        if asyncio.get_event_loop().is_running():
            asyncio.create_task(self._shutdown())

    async def _shutdown(self):
        """Perform graceful shutdown"""
        try:
            if self.event_manager:
                await self.event_manager.emit(
                    EventType.SYSTEM_STATUS,
                    {
                        "status": "shutting_down",
                        "message": "Graceful shutdown initiated"
                    }
                )

            if self.trading_system and self.api_server and self.event_manager:
                await stop_application(
                    self.trading_system,
                    self.api_server,
                    self.event_manager
                )

            # Stop the event loop
            asyncio.get_event_loop().stop()

        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
            sys.exit(1)


async def start_application(config_path: str, shutdown_manager: GracefulShutdown):
    """Start the trading application"""
    try:
        # Load configuration
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Initialize components
        config_loader = ConfigLoader()
        event_manager = EventManager()
        trading_system = TradingSystem(config, event_manager)

        # Store components in shutdown manager
        shutdown_manager.trading_system = trading_system
        shutdown_manager.event_manager = event_manager

        # Initialize API components
        auth_handler = AuthHandler(config)
        rate_limiter = RateLimiter(trading_system.state_manager.redis, config)
        api_server = APIServer(trading_system, config)
        shutdown_manager.api_server = api_server

        # Add middleware
        app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

        # Subscribe to system events
        await event_manager.subscribe(
            EventType.SYSTEM_ERROR,
            lambda data: logger.error(f"System error: {data}")
        )
        await event_manager.subscribe(
            EventType.SYSTEM_WARNING,
            lambda data: logger.warning(f"System warning: {data}")
        )

        # Start trading system
        await trading_system.start()

        # Start API server
        await api_server.start()

        # Emit system started event
        await event_manager.emit(
            EventType.SYSTEM_STATUS,
            {"status": "started", "message": "Trading system started successfully"}
        )

        # Run FastAPI application
        config = uvicorn.Config(
            app,
            host=config["api"]["host"],
            port=config["api"]["port"],
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

    except Exception as e:
        logger.error(f"Error starting application: {str(e)}")
        # Emit system error event
        if 'event_manager' in locals():
            await event_manager.emit(
                EventType.SYSTEM_ERROR,
                {"error": str(e), "message": "Failed to start trading system"}
            )
        raise


async def stop_application(
    trading_system: TradingSystem,
    api_server: APIServer,
    event_manager: EventManager
):
    """Stop the trading application"""
    try:
        # Emit stopping event
        await event_manager.emit(
            EventType.SYSTEM_STATUS,
            {"status": "stopping", "message": "Trading system stopping"}
        )

        # Stop API server first to prevent new requests
        logger.info("Stopping API server...")
        await api_server.stop()

        # Stop trading system
        logger.info("Stopping trading system...")
        await trading_system.stop()

        # Emit stopped event
        await event_manager.emit(
            EventType.SYSTEM_STATUS,
            {"status": "stopped", "message": "Trading system stopped successfully"}
        )

        logger.info("Shutdown completed successfully")

    except Exception as e:
        logger.error(f"Error stopping application: {str(e)}")
        await event_manager.emit(
            EventType.SYSTEM_ERROR,
            {"error": str(e), "message": "Error stopping trading system"}
        )
        raise


def main():
    """Main entry point"""
    try:
        if len(sys.argv) != 2:
            print("Usage: python -m src.main config.yaml")
            sys.exit(1)

        config_path = sys.argv[1]
        shutdown_manager = GracefulShutdown()

        # Run application
        asyncio.run(start_application(config_path, shutdown_manager))

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutdown complete.")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
