from typing import Dict, Any, Optional, List
from datetime import datetime
import numpy as np
import logging
from ..base import BaseStrategy
from ..models import Signal, DataPoint

logger = logging.getLogger(__name__)


class MACrossoverStrategy(BaseStrategy):
    def __init__(
        self,
        strategy_id: str,
        symbol: str,
        params: Dict[str, Any],
        state_manager: Any
    ):
        super().__init__(strategy_id, symbol, params, state_manager)
        self.fast_ma = params.get("fast_ma", 10)
        self.slow_ma = params.get("slow_ma", 21)
        self.min_volume = params.get("min_volume", 1000000)
        self.risk_factor = params.get("risk_factor", 0.02)
        self.prices: List[float] = []
        self.volumes: List[float] = []

    async def initialize(self) -> None:
        """Initialize strategy"""
        await self.load_state()
        self.indicators = {
            "fast_ma": [],
            "slow_ma": [],
            "last_cross": None,  # 'up' or 'down'
        }

    async def process_data(self, data_point: DataPoint) -> None:
        """Process new data point"""
        if data_point.data_type != "candle":
            return

        candle = data_point.value
        self.prices.append(float(candle["close"]))
        self.volumes.append(float(candle["volume"]))

        # Keep only necessary data points
        max_period = max(self.fast_ma, self.slow_ma)
        if len(self.prices) > max_period * 2:  # Keep extra for signal generation
            self.prices = self.prices[-max_period*2:]
            self.volumes = self.volumes[-max_period*2:]

        # Update indicators
        if len(self.prices) >= max_period:
            self.indicators["fast_ma"] = self._calculate_ma(
                self.prices, self.fast_ma)
            self.indicators["slow_ma"] = self._calculate_ma(
                self.prices, self.slow_ma)

    def _calculate_ma(self, data: List[float], period: int) -> List[float]:
        """Calculate moving average"""
        if len(data) < period:
            return []
        return list(np.convolve(data, np.ones(period)/period, mode='valid'))

    async def generate_signal(self) -> Optional[Signal]:
        """Generate trading signal based on MA crossover"""
        try:
            if not self.state or not self.state.active:
                return None

            if len(self.indicators["fast_ma"]) < 2 or len(self.indicators["slow_ma"]) < 2:
                return None

            # Get latest values
            fast_ma = self.indicators["fast_ma"][-2:]
            slow_ma = self.indicators["slow_ma"][-2:]
            current_price = self.prices[-1]
            current_volume = self.volumes[-1]

            # Check volume requirement
            if current_volume < self.min_volume:
                return None

            # Check for crossover
            prev_diff = fast_ma[0] - slow_ma[0]
            curr_diff = fast_ma[1] - slow_ma[1]

            signal = None
            if prev_diff <= 0 and curr_diff > 0:  # Bullish crossover
                if self.indicators["last_cross"] != "up":
                    signal = self._create_signal("buy", current_price)
                    self.indicators["last_cross"] = "up"

            elif prev_diff >= 0 and curr_diff < 0:  # Bearish crossover
                if self.indicators["last_cross"] != "down":
                    signal = self._create_signal("sell", current_price)
                    self.indicators["last_cross"] = "down"

            if signal:
                await self.update_state({
                    "last_signal": {
                        "timestamp": signal.timestamp.isoformat(),
                        "side": signal.side,
                        "price": signal.price
                    }
                })

            return signal

        except Exception as e:
            logger.error(f"Error generating signal: {str(e)}")
            return None

    def _create_signal(self, side: str, price: float) -> Signal:
        """Create a signal with position sizing"""
        # Calculate position size based on risk factor
        position_size = self.calculate_position_size(price)

        return Signal(
            strategy_id=self.strategy_id,
            symbol=self.symbol,
            side=side,
            size=position_size,
            price=price,
            timestamp=datetime.utcnow(),
            metadata={
                "fast_ma": self.indicators["fast_ma"][-1],
                "slow_ma": self.indicators["slow_ma"][-1],
                "risk_factor": self.risk_factor
            },
            signal_type="entry",
            confidence=0.8  # Could be calculated based on various factors
        )

    def calculate_position_size(self, price: float) -> float:
        """Calculate position size based on risk management rules"""
        # This is a simple implementation
        # In production, you'd want more sophisticated position sizing
        account_size = 1000  # This should come from account management
        risk_amount = account_size * self.risk_factor

        # Assuming a 5% stop loss
        stop_loss_percent = 0.05
        position_size = risk_amount / (price * stop_loss_percent)

        return position_size

    async def _validate_signal(self, signal: Signal) -> bool:
        """Validate signal based on strategy-specific rules"""
        try:
            # Check if we have enough data
            if len(self.prices) < max(self.fast_ma, self.slow_ma):
                return False

            # Check if volume is sufficient
            if self.volumes[-1] < self.min_volume:
                return False

            # Check if price is moving in signal direction
            price_change = (self.prices[-1] -
                            self.prices[-2]) / self.prices[-2]
            if (signal.side == "buy" and price_change < 0) or \
               (signal.side == "sell" and price_change > 0):
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating signal: {str(e)}")
            return False
