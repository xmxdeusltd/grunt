from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
import logging
import json
from datetime import datetime

from .models import (
    TradeRequest,
    StrategyConfig,
    StrategyUpdate,
    TimeRange,
    APIResponse
)
from ..integration import TradingSystem
from ..strategy_engine.strategies import get_strategy_class
from ..events import EventType, EventManager

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trading Bot API",
    description="API for managing trading strategies and positions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class APIServer:
    def __init__(self, trading_system: TradingSystem, config: Dict[str, Any]):
        self.trading_system = trading_system
        self.config = config
        self.websocket_connections: Dict[str, Dict[str, Any]] = {}
        self.event_manager = EventManager()

    async def start(self):
        """Start API server"""
        # Add routes
        self._setup_routes()

        # Subscribe to events for broadcasting
        await self._setup_event_subscriptions()
        logger.info("API server started")

    async def stop(self):
        """Stop API server"""
        # Close all WebSocket connections
        for client_info in self.websocket_connections.values():
            await client_info["websocket"].close()
        logger.info("API server stopped")

    async def _setup_event_subscriptions(self):
        """Setup event subscriptions for broadcasting"""
        # Subscribe to all event types
        for event_type in EventType:
            await self.event_manager.subscribe(
                event_type,
                self._broadcast_event
            )

    async def _broadcast_event(self, event_data: Dict[str, Any]):
        """Broadcast event to subscribed WebSocket clients"""
        event_type = event_data["event_type"]

        for client_id, client_info in list(self.websocket_connections.items()):
            try:
                if event_type in client_info["subscriptions"]:
                    websocket = client_info["websocket"]
                    await websocket.send_text(json.dumps(event_data))
            except Exception as e:
                logger.error(
                    f"Error broadcasting to client {client_id}: {str(e)}")
                # Remove dead connection
                if client_id in self.websocket_connections:
                    del self.websocket_connections[client_id]

    def _setup_routes(self):
        """Setup API routes"""

        @app.post("/api/v1/trade", response_model=APIResponse)
        async def execute_trade(trade: TradeRequest, token: str = Depends(oauth2_scheme)):
            """Execute a trade"""
            try:
                order = await self.trading_system.trading_engine.execute_market_order(
                    symbol=trade.symbol,
                    side=trade.side,
                    size=trade.size,
                    stop_loss=trade.stop_loss,
                    metadata=trade.metadata
                )

                return APIResponse(
                    success=True,
                    data={"order_id": order.order_id}
                )
            except Exception as e:
                logger.error(f"Error executing trade: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))

        @app.get("/api/v1/positions", response_model=APIResponse)
        async def get_positions(token: str = Depends(oauth2_scheme)):
            """Get all open positions"""
            try:
                positions = await self.trading_system.trading_engine.get_position_summary()
                return APIResponse(success=True, data=positions)
            except Exception as e:
                logger.error(f"Error getting positions: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))

        @app.post("/api/v1/strategy", response_model=APIResponse)
        async def add_strategy(
            config: StrategyConfig,
            token: str = Depends(oauth2_scheme)
        ):
            """Add new strategy"""
            try:
                # Get strategy template
                template = await self.trading_system.config_loader.get_strategy_template(
                    config.type,
                    config.template
                )

                # Merge template with custom parameters
                params = {**template, **config.parameters}

                # Get strategy class
                strategy_class = get_strategy_class(config.type)

                # Generate strategy ID
                strategy_id = f"{config.type}_{config.symbol}_{datetime.utcnow().timestamp()}"

                # Add strategy
                await self.trading_system.add_strategy(
                    strategy_id=strategy_id,
                    strategy_class=strategy_class,
                    symbol=config.symbol,
                    params=params
                )

                return APIResponse(
                    success=True,
                    data={"strategy_id": strategy_id}
                )
            except Exception as e:
                logger.error(f"Error adding strategy: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))

        @app.delete("/api/v1/strategy/{strategy_id}", response_model=APIResponse)
        async def remove_strategy(
            strategy_id: str,
            token: str = Depends(oauth2_scheme)
        ):
            """Remove strategy"""
            try:
                await self.trading_system.remove_strategy(strategy_id)
                return APIResponse(success=True)
            except Exception as e:
                logger.error(f"Error removing strategy: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))

        @app.put("/api/v1/strategy/{strategy_id}", response_model=APIResponse)
        async def update_strategy(
            strategy_id: str,
            update: StrategyUpdate,
            token: str = Depends(oauth2_scheme)
        ):
            """Update strategy configuration"""
            try:
                await self.trading_system.strategy_manager.update_strategy(
                    strategy_id=strategy_id,
                    active=update.active,
                    parameters=update.parameters,
                    metadata=update.metadata
                )
                return APIResponse(success=True)
            except Exception as e:
                logger.error(f"Error updating strategy: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))

        @app.get("/api/v1/trades", response_model=APIResponse)
        async def get_trades(
            time_range: TimeRange = Depends(),
            symbol: Optional[str] = None,
            token: str = Depends(oauth2_scheme)
        ):
            """Get trade history"""
            try:
                trades = await self.trading_system.get_trade_history(
                    symbol=symbol,
                    start_time=time_range.start_time,
                    end_time=time_range.end_time
                )
                return APIResponse(success=True, data=trades)
            except Exception as e:
                logger.error(f"Error getting trades: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))

        @app.get("/api/v1/status", response_model=APIResponse)
        async def get_status(token: str = Depends(oauth2_scheme)):
            """Get system status"""
            try:
                status = await self.trading_system.get_system_status()
                return APIResponse(success=True, data=status)
            except Exception as e:
                logger.error(f"Error getting status: {str(e)}")
                raise HTTPException(status_code=400, detail=str(e))

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            try:
                await websocket.accept()
                client_id = f"client_{datetime.utcnow().timestamp()}"

                # Initialize client info
                self.websocket_connections[client_id] = {
                    "websocket": websocket,
                    "subscriptions": set(),
                    "connected_at": datetime.utcnow()
                }

                try:
                    while True:
                        data = await websocket.receive_text()
                        message = json.loads(data)

                        if message.get("type") == "subscribe":
                            # Handle subscription
                            events = message.get("events", [])
                            for event in events:
                                try:
                                    event_type = EventType(event)
                                    self.websocket_connections[client_id]["subscriptions"].add(
                                        event)

                                    # Send recent history
                                    history = await self.event_manager.get_event_history(
                                        event_type,
                                        limit=50
                                    )
                                    if history:
                                        await websocket.send_text(
                                            json.dumps({
                                                "type": "history",
                                                "event_type": event,
                                                "data": history
                                            })
                                        )
                                except ValueError:
                                    await websocket.send_text(
                                        json.dumps({
                                            "type": "error",
                                            "message": f"Invalid event type: {event}"
                                        })
                                    )

                        elif message.get("type") == "unsubscribe":
                            # Handle unsubscription
                            events = message.get("events", [])
                            for event in events:
                                self.websocket_connections[client_id]["subscriptions"].discard(
                                    event)

                except WebSocketDisconnect:
                    if client_id in self.websocket_connections:
                        del self.websocket_connections[client_id]

            except Exception as e:
                logger.error(f"WebSocket error: {str(e)}")
                if client_id in self.websocket_connections:
                    del self.websocket_connections[client_id]

        # Add event history endpoint
        @app.get("/api/v1/events/{event_type}", response_model=APIResponse)
        async def get_event_history(
            event_type: str,
            limit: int = 100,
            token: str = Depends(oauth2_scheme)
        ):
            """Get historical events for a specific type"""
            try:
                try:
                    event_enum = EventType(event_type)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid event type: {event_type}"
                    )

                history = await self.event_manager.get_event_history(
                    event_enum,
                    limit=limit
                )
                return APIResponse(success=True, data=history)
            except Exception as e:
                logger.error(f"Error getting event history: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail="Error retrieving event history"
                )
