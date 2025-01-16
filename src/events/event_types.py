from enum import Enum


class EventType(Enum):
    # Trading Events
    TRADE_EXECUTED = "trade_executed"
    ORDER_PLACED = "order_placed"
    ORDER_CANCELLED = "order_cancelled"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    POSITION_UPDATED = "position_updated"

    # Strategy Events
    STRATEGY_STARTED = "strategy_started"
    STRATEGY_STOPPED = "strategy_stopped"
    STRATEGY_UPDATED = "strategy_updated"
    STRATEGY_SIGNAL = "strategy_signal"

    # System Events
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    SYSTEM_STATUS = "system_status"

    # Market Events
    PRICE_UPDATE = "price_update"
    VOLUME_SPIKE = "volume_spike"
    VOLATILITY_ALERT = "volatility_alert"

    # Risk Events
    RISK_LIMIT_BREACH = "risk_limit_breach"
    MARGIN_CALL = "margin_call"
    ACCOUNT_VALUE_UPDATE = "account_value_update"
