# API Layer Module

## Overview

The API Layer provides the interface for external services to interact with the trading bot. It handles REST endpoints, WebSocket connections, and manages authentication and rate limiting.

## Core Responsibilities

### 1. REST API

- Handle HTTP requests
- Process API commands
- Return responses
- Manage authentication

### 2. WebSocket Server

- Real-time data streaming
- Event notifications
- Connection management
- State synchronization

### 3. External Communication

- Handle external service integration
- Manage API rate limits
- Process callbacks
- Error handling

## Components

### 1. REST API Server

```python
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

app = FastAPI(title="Trading Bot API")

class APIServer:
    def __init__(self):
        self.app = app
        self.trading_engine = TradingEngine()
        self.strategy_engine = StrategyEngine()

    async def start(self):
        """Start API server"""
        pass

    async def stop(self):
        """Stop API server"""
        pass
```

### 2. WebSocket Manager

```python
class WebSocketManager:
    def __init__(self):
        self.connections = {}
        self.handlers = {}

    async def handle_connection(self, websocket: WebSocket):
        """Handle new WebSocket connection"""
        pass

    async def broadcast_event(self, event: str, data: Dict):
        """Broadcast event to all connections"""
        pass

    async def send_to_client(self, client_id: str, event: str, data: Dict):
        """Send event to specific client"""
        pass
```

## API Endpoints

### 1. Trading Operations

#### Execute Trade

```python
@app.post("/api/v1/trade")
async def execute_trade(
    trade: TradeRequest,
    auth: Auth = Depends(get_auth)
):
    """
    Execute a trade

    Request:
    {
        "symbol": "SOL-USDC",
        "side": "buy",
        "size": 10.5,
        "type": "market"
    }
    """
    pass
```

#### Get Positions

```python
@app.get("/api/v1/positions")
async def get_positions(
    auth: Auth = Depends(get_auth)
):
    """Get all open positions"""
    pass
```

### 2. Strategy Management

#### Add Strategy

```python
@app.post("/api/v1/strategy")
async def add_strategy(
    strategy: StrategyConfig,
    auth: Auth = Depends(get_auth)
):
    """
    Add new strategy

    Request:
    {
        "symbol": "SOL-USDC",
        "type": "ma_crossover",
        "parameters": {
            "fast_ma": 10,
            "slow_ma": 21
        }
    }
    """
    pass
```

#### Update Strategy

```python
@app.put("/api/v1/strategy/{strategy_id}")
async def update_strategy(
    strategy_id: int,
    config: StrategyUpdate,
    auth: Auth = Depends(get_auth)
):
    """Update strategy configuration"""
    pass
```

### 3. Market Data

#### Get Candles

```python
@app.get("/api/v1/candles/{symbol}")
async def get_candles(
    symbol: str,
    interval: str = "1m",
    limit: int = 100,
    auth: Auth = Depends(get_auth)
):
    """Get historical candles"""
    pass
```

## WebSocket Events

### 1. Market Events

```python
class MarketEvents:
    TRADE = "trade"
    CANDLE = "candle"
    PRICE_UPDATE = "price_update"
```

### 2. Trading Events

```python
class TradingEvents:
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    POSITION_UPDATED = "position_updated"
    ORDER_FILLED = "order_filled"
```

## Authentication

```python
class AuthHandler:
    def __init__(self):
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        self.secret_key = settings.SECRET_KEY

    async def authenticate(self, token: str) -> Dict:
        """Authenticate API request"""
        pass

    async def create_token(self, data: Dict) -> str:
        """Create new access token"""
        pass
```

## Rate Limiting

```python
class RateLimiter:
    def __init__(self):
        self.redis = RedisClient()
        self.limits = {
            "trade": 10,  # per minute
            "query": 100  # per minute
        }

    async def check_limit(self, key: str, limit_type: str) -> bool:
        """Check if request is within rate limit"""
        pass

    async def increment_counter(self, key: str, limit_type: str):
        """Increment rate limit counter"""
        pass
```

## Error Handling

### 1. API Errors

```python
class APIError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

class ErrorHandler:
    @app.exception_handler(APIError)
    async def handle_api_error(error: APIError):
        return JSONResponse(
            status_code=error.code,
            content={"error": error.message}
        )
```

## Configuration

```python
API_CONFIG = {
    "server": {
        "host": "0.0.0.0",
        "port": 8000,
        "workers": 4
    },
    "websocket": {
        "ping_interval": 30,
        "max_connections": 1000
    },
    "rate_limits": {
        "trade": {
            "requests": 10,
            "period": 60
        },
        "query": {
            "requests": 100,
            "period": 60
        }
    },
    "auth": {
        "token_expiry": 3600,
        "refresh_expiry": 86400
    }
}
```

## API Response Format

### 1. Success Response

```json
{
  "success": true,
  "data": {
    // Response data
  },
  "timestamp": "2024-01-20T10:00:00Z"
}
```

### 2. Error Response

```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "Invalid request parameters"
  },
  "timestamp": "2024-01-20T10:00:00Z"
}
```

## Dependencies

- FastAPI
- WebSockets
- Redis (for rate limiting)
- JWT (for authentication)
- Pydantic (for request/response models)

## Security Considerations

1. Authentication (leave this for later)

   - JWT token validation
   - Role-based access control
   - Token refresh mechanism

2. Rate Limiting (leave this for later)

   - Per-endpoint limits
   - Per-user limits
   - IP-based limits

3. Input Validation (leave this for later)
   - Request schema validation
   - Parameter sanitization
   - Type checking

## Future Enhancements

1. GraphQL support
2. Advanced monitoring endpoints
3. API versioning
4. Documentation generation
