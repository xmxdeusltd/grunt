import asyncpg
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config["host"],
                port=self.config["port"],
                user=self.config["user"],
                password=self.config["password"],
                database=self.config["database"],
                min_size=self.config.get("min_connections", 5),
                max_size=self.config.get("max_connections", 20)
            )
            await self._create_tables()
            logger.info("Database connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

    async def _create_tables(self):
        """Create necessary database tables if they don't exist"""
        if not self.pool:
            raise RuntimeError("Database not initialized")

        async with self.pool.acquire() as conn:
            # Create trades table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20),
                    price DECIMAL,
                    size DECIMAL,
                    timestamp TIMESTAMPTZ,
                    side VARCHAR(10),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_trades_symbol_timestamp 
                ON trades(symbol, timestamp);
            ''')

            # Create candles table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS candles (
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
                CREATE INDEX IF NOT EXISTS idx_candles_symbol_timestamp 
                ON candles(symbol, timestamp);
            ''')

            # Create custom_data table for extensibility
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS custom_data (
                    id SERIAL PRIMARY KEY,
                    data_type VARCHAR(50),
                    symbol VARCHAR(20),
                    timestamp TIMESTAMPTZ,
                    data JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_custom_data_type_symbol_timestamp 
                ON custom_data(data_type, symbol, timestamp);
            ''')

    async def execute_query(self, query: str, *args) -> Any:
        """Execute a database query"""
        if not self.pool:
            raise RuntimeError("Database not initialized")

        try:
            async with self.pool.acquire() as conn:
                return await conn.execute(query, *args)
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    async def fetch_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch results from a database query"""
        if not self.pool:
            raise RuntimeError("Database not initialized")

        try:
            async with self.pool.acquire() as conn:
                results = await conn.fetch(query, *args)
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Query fetch failed: {str(e)}")
            raise

    async def batch_insert(self, table: str, records: List[Dict[str, Any]]) -> None:
        """Insert multiple records into a table"""
        if not records:
            return

        if not self.pool:
            raise RuntimeError("Database not initialized")

        # Create the query based on the first record's keys
        keys = records[0].keys()
        columns = ', '.join(keys)
        placeholders = ', '.join(f'${i+1}' for i in range(len(keys)))
        query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    for record in records:
                        values = [record[key] for key in keys]
                        await conn.execute(query, *values)
        except Exception as e:
            logger.error(f"Batch insert failed: {str(e)}")
            raise

    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection closed")
