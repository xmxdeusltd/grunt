# System Architecture

## High-Level Overview

The trading bot is designed as a modular system with clear separation of concerns. Each component is designed to be independently maintainable and extensible.

## Core Components

### 1. Trading Engine

- Handles all trading operations
- Manages positions and orders
- Integrates with Jupiter for execution
- Implements risk management (future module)

### 2. Strategy Engine

- Processes market data
- Generates trading signals
- Manages strategy parameters
- Supports multiple strategies per coin

### 3. Data Management

- Handles market data processing
- Manages persistent storage (PostgreSQL)
- Manages state storage (Redis)
- Provides data access interfaces

### 4. API Layer

- Provides REST endpoints
- Handles external service communication
- Manages authentication and rate limiting
- Exposes monitoring endpoints

## Data Flow

```
Market Data → Data Management → Strategy Engine → Trading Engine → Order Execution
     ↑                 ↓              ↓               ↓
     └─────────────── API Layer ─────────────────────┘
```

## Database Schema

### PostgreSQL Tables

#### Candles

```sql
CREATE TABLE candles (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    timestamp TIMESTAMPTZ,
    open DECIMAL,
    high DECIMAL,
    low DECIMAL,
    close DECIMAL,
    volume DECIMAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Positions

```sql
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20),
    entry_price DECIMAL,
    current_price DECIMAL,
    size DECIMAL,
    side VARCHAR(10),
    strategy VARCHAR(50),
    status VARCHAR(20),
    entry_time TIMESTAMPTZ,
    last_update TIMESTAMPTZ,
    pnl DECIMAL,
    stop_loss DECIMAL,
    trailing_stop DECIMAL
);
```

#### Trades

```sql
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    position_id INTEGER REFERENCES positions(id),
    price DECIMAL,
    size DECIMAL,
    side VARCHAR(10),
    timestamp TIMESTAMPTZ,
    fee DECIMAL,
    strategy VARCHAR(50)
);
```

### Redis Schema

#### Keys Structure

- `settings:{symbol}:strategy` - Strategy configuration
- `settings:{symbol}:risk` - Risk parameters
- `position:{symbol}:current` - Current position details
- `strategy:{symbol}:state` - Strategy state
- `market:{symbol}:latest` - Latest market data

## Event System

The event system is designed to be extensible and allows for easy addition of new event handlers.

### Core Events

- Trade execution (entry/exit)
- Position updates
- Strategy signals
- Risk threshold breaches
- Error events
- Settings changes

### Event Flow

```
Event Source → Event Bus → Event Handlers → Actions
                   ↓
             Event Storage
```

## Strategy Management

### Strategy Configuration Structure

```json
{
  "SOL-USDC": {
    "active_strategy": "ma_crossover",
    "parameters": {
      "template": "aggressive",
      "custom_params": {
        "fast_ma": 10,
        "slow_ma": 21
      }
    },
    "risk_settings": {
      "position_size": 100,
      "stop_loss": 0.02,
      "trailing_stop": {
        "active": true,
        "distance": 0.03
      }
    }
  }
}
```

### Strategy Templates

```json
{
  "ma_crossover": {
    "conservative": {
      "fast_ma": 20,
      "slow_ma": 50,
      "min_volume": 1000000
    },
    "aggressive": {
      "fast_ma": 10,
      "slow_ma": 21,
      "min_volume": 500000
    }
  }
}
```

## Future Extensibility

### Planned Modules

1. Risk Management Module
2. Market Making Capabilities
3. Limit Order Support
4. Web Dashboard Integration
5. Advanced Analytics

### Integration Points

- External notification systems
- Analytics services
- Risk management systems
- Portfolio management systems
