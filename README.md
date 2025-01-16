# Solana Trading Bot

## Overview

A sophisticated trading bot for Solana-based tokens using Jupiter for swaps. The system is designed to be modular, extensible, and maintainable.

## Core Features

- Jupiter integration for token swaps
- Real-time market data processing
- Multiple trading strategies (MA Crossover, VWAP, TWAP)
- Position management with stop-loss and trailing stop
- PostgreSQL for persistent storage
- Redis for real-time state management
- Event-driven architecture for extensibility

## System Architecture

Detailed architecture documentation can be found in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

### Core Components

1. Trading Engine
2. Strategy Engine
3. Data Management
4. API Layer

## Module Documentation

- [Trading Engine](docs/modules/TRADING_ENGINE.md)
- [Strategy Engine](docs/modules/STRATEGY_ENGINE.md)
- [Data Management](docs/modules/DATA_MANAGEMENT.md)
- [API Layer](docs/modules/API_LAYER.md)
- [Event System](docs/modules/EVENT_SYSTEM.md)

## Prerequisites

- Python 3.8+
- PostgreSQL
- Redis
- Jupiter API access

## Development Setup

### Local Development (Recommended)

1. **Install Poetry** (Package Manager):

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. **Setup**:

```bash
# Install dependencies
poetry install
```

3. **Configure Environment**:

```bash
# Copy example files
cp .env.example .env
cp config.example.yaml config.yaml

# Edit .env with your credentials
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=trading_bot
POSTGRES_PASSWORD=your_password
POSTGRES_DB=trading_bot

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

JUPITER_RPC_ENDPOINT=https://api.mainnet-beta.solana.com
JUPITER_AUTH_TOKEN=your_jupiter_token

API_SECRET_KEY=your_api_secret
```

4. **Database Setup**:

```bash
# Create PostgreSQL database
createdb trading_bot

# Redis should be running locally
redis-server
```

5. **Run the Bot**:

```bash
# Activate virtual environment
poetry env activate

# Start the bot
poetry run start config.yaml
```

### Production Setup (Future Use)

1. **Docker Setup**:

```bash
# Build image
docker build -t trading-bot -f docker/Dockerfile .

# Run with docker-compose
docker-compose -f docker/docker-compose.yml up -d
```

2. **Production Configuration**:

- Use environment-specific .env files
- Configure proper security settings
- Set up monitoring and logging
- Use production-grade databases
- Implement backup strategies

## Usage

### Adding a Trading Strategy

```bash
# Using the API to add a strategy
curl -X POST http://localhost:8000/api/v1/strategy \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "SOL-USDC",
    "type": "ma_crossover",
    "template": "conservative",
    "parameters": {
      "fast_ma": 20,
      "slow_ma": 50,
      "min_volume": 1000000
    }
  }'
```

### Monitoring

#### API Endpoints

```bash
# Get system status
curl http://localhost:8000/api/v1/status \
  -H "Authorization: Bearer your_token"

# Get open positions
curl http://localhost:8000/api/v1/positions \
  -H "Authorization: Bearer your_token"

# Get trade history
curl http://localhost:8000/api/v1/trades \
  -H "Authorization: Bearer your_token"

# Get event history
curl http://localhost:8000/api/v1/events/trade_executed \
  -H "Authorization: Bearer your_token"
```

#### WebSocket Events

```javascript
const ws = new WebSocket("ws://localhost:8000/ws");
ws.send(
  JSON.stringify({
    type: "subscribe",
    events: [
      "trade_executed",
      "position_opened",
      "position_closed",
      "strategy_signal",
    ],
  })
);
```

## Configuration

### Environment Variables (.env)

- Database credentials
- Redis connection details
- API keys and secrets
- Security tokens

### Application Config (config.yaml)

- Trading parameters
- Risk management settings
- Strategy configurations
- API rate limits

### Strategy Templates

1. **MA Crossover**:

   - Conservative: Slower moving averages, larger volume requirements
   - Aggressive: Faster moving averages, lower volume requirements

2. **VWAP**:

   - Default: Daily VWAP with standard deviation bands
   - Scalping: Hourly VWAP with tighter bands

3. **TWAP**:
   - Default: 5-minute intervals over 1 hour
   - Aggressive: 1-minute intervals over 30 minutes

### Risk Management

- Position size limits
- Stop-loss implementation
- Trailing stop functionality
- Maximum positions per symbol

## Project Structure

```
trading-bot/
├── src/                 # Source code
│   ├── api/            # API endpoints
│   ├── trading_engine/ # Trading logic
│   ├── strategy_engine/# Trading strategies
│   └── events/         # Event system
├── tests/              # Test files
├── docker/             # Docker configuration (future use)
├── pyproject.toml      # Poetry configuration
├── config.yaml         # Application configuration
└── .env               # Environment variables
```

## Development

### Best Practices

1. **Strategy Development**:

   - Start with simple strategies
   - Test on multiple market conditions
   - Implement proper position sizing
   - Include transaction costs

2. **Testing**:
   - Unit tests for components
   - Integration tests
   - Paper trading validation
   - Production monitoring

```

```
