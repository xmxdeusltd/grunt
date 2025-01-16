from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import logging
from abc import ABC, abstractmethod
from .models import Signal, StrategyState, DataPoint

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    def __init__(
        self,
        strategy_id: str,
        symbol: str,
        params: Dict[str, Any],
        state_manager: Any  # Will be properly typed when implementing state management
    ):
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.params = params
        self.state_manager = state_manager
        self.indicators: Dict[str, Any] = {}
        self.data_requirements: Set[str] = {"candle"}  # Base requirement
        self.custom_data: Dict[str, Any] = {}
        self.state: Optional[StrategyState] = None

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize strategy indicators and state"""
        pass

    @abstractmethod
    async def process_data(self, data_point: DataPoint) -> None:
        """Process incoming data"""
        logger.info(f"Processing data point: {data_point}")
        pass

    @abstractmethod
    async def generate_signal(self) -> Optional[Signal]:
        """Generate trading signal"""
        pass

    async def validate_signal(self, signal: Signal) -> bool:
        """Validate generated signal"""
        try:
            # Basic validation
            if not signal.price or signal.price <= 0:
                logger.warning(f"Invalid price in signal: {signal}")
                return False

            if not signal.size or signal.size <= 0:
                logger.warning(f"Invalid size in signal: {signal}")
                return False

            if signal.expiry and signal.expiry < datetime.utcnow():
                logger.warning(f"Signal already expired: {signal}")
                return False

            # Strategy-specific validation
            return await self._validate_signal(signal)

        except Exception as e:
            logger.error(f"Error validating signal: {str(e)}")
            return False

    async def _validate_signal(self, signal: Signal) -> bool:
        """Strategy-specific signal validation"""
        return True

    def get_data_requirements(self) -> Set[str]:
        """Get list of required data types"""
        return self.data_requirements

    def load_state(self) -> None:
        """Load strategy state"""
        try:
            state_data = self.state_manager.get_strategy_state(
                self.strategy_id)
            if state_data:
                self.state = StrategyState(
                    strategy_id=self.strategy_id,
                    symbol=self.symbol,
                    active=state_data.get("active", True),
                    last_update=state_data.get(
                        "last_update", datetime.utcnow()),
                    position_size=state_data.get("position_size", 0),
                    current_position=state_data.get("current_position"),
                    metadata=state_data.get("metadata", {})
                )
            else:
                # Initialize with default state
                self.update_state({
                    "active": True,
                    "position_size": 0,
                    "metadata": {}
                })

        except Exception as e:
            logger.error(f"Error loading strategy state: {str(e)}")
            raise

    def update_state(self, new_state: Dict[str, Any]) -> None:
        """Update strategy state"""
        try:
            if not self.state:
                self.state = StrategyState(
                    strategy_id=self.strategy_id,
                    symbol=self.symbol,
                    active=new_state.get("active", True),
                    last_update=datetime.utcnow(),
                    position_size=new_state.get("position_size", 0),
                    current_position=new_state.get("current_position"),
                    metadata=new_state.get("metadata", {})
                )
            else:
                # Update existing state
                for key, value in new_state.items():
                    setattr(self.state, key, value)
                self.state.last_update = datetime.utcnow()

            # Save to state storage
            state_dict = {
                "strategy_id": self.state.strategy_id,
                "symbol": self.state.symbol,
                "active": self.state.active,
                "last_update": self.state.last_update.isoformat(),
                "position_size": self.state.position_size,
                "current_position": self.state.current_position,
                "metadata": self.state.metadata
            }
            self.state_manager.update_strategy_state(
                self.strategy_id, state_dict)

        except Exception as e:
            logger.error(f"Error updating strategy state: {str(e)}")
            raise

    def cleanup(self) -> None:
        """Cleanup strategy resources"""
        try:
            # Update state as inactive
            self.update_state({"active": False})

            # Clear indicators and custom data
            self.indicators.clear()
            self.custom_data.clear()

            logger.info(f"Strategy {self.strategy_id} cleaned up successfully")

        except Exception as e:
            logger.error(f"Error cleaning up strategy: {str(e)}")
            raise
