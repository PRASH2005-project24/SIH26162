"""
Database abstraction layer for SIH26162
Handles PostgreSQL+PostGIS connections and migrations
"""

import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)


class Database:
    """Async PostgreSQL database interface"""

    def __init__(self, config):
        self.config = config
        self.engine = None
        self.async_session_maker = None
        self._initialized = False

    async def connect(self):
        """Initialize database engine and connection pool"""
        if self._initialized:
            return

        try:
            # SQLAlchemy 2.0 doesn't support pool_size/max_overflow with NullPool
            # So we skip those parameters when using NullPool
            engine_kwargs = {
                "echo": False,  # Set to True for SQL debugging
            }

            if self.config.BACKEND_ENV != "development":
                # Use connection pooling in production
                engine_kwargs.update({
                    "pool_size": self.config.DB_POOL_MAX,
                    "max_overflow": 10,
                    "pool_recycle": 3600,
                })
            # else: development mode with NullPool (no pooling)

            self.engine = create_async_engine(
                self.config.DATABASE_URL,
                **engine_kwargs,
                poolclass=NullPool if self.config.BACKEND_ENV == "development" else None,
            )

            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            self._initialized = True
            logger.info("✓ Database connected")

        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}", exc_info=True)
            raise

    async def disconnect(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False
            logger.info("✓ Database disconnected")

    async def get_session(self) -> AsyncSession:
        """Get a new async session"""
        if not self._initialized or not self.async_session_maker:
            raise RuntimeError("Database not initialized. Call connect() first.")
        return self.async_session_maker()

    async def execute(self, query: str, params: Dict = None) -> List[Dict]:
        """Execute a raw SQL query and return results as list of dicts"""
        from datetime import datetime
        from decimal import Decimal

        async with await self.get_session() as session:
            result = await session.execute(text(query), params or {})
            rows = result.fetchall()

            # Convert rows to dicts and serialize datetime/Decimal objects
            result_list = []
            for row in rows:
                row_dict = dict(row._mapping)
                # Convert datetime objects to ISO strings and Decimal to float for JSON serialization
                for key, value in row_dict.items():
                    if isinstance(value, datetime):
                        row_dict[key] = value.isoformat()
                    elif isinstance(value, Decimal):
                        row_dict[key] = float(value)
                result_list.append(row_dict)

            return result_list

    async def execute_one(self, query: str, params: Dict = None) -> Optional[Dict]:
        """Execute a raw SQL query and return first result"""
        results = await self.execute(query, params)
        return results[0] if results else None

    async def execute_update(self, query: str, params: Dict = None) -> int:
        """Execute an UPDATE/DELETE query and return affected row count"""
        async with await self.get_session() as session:
            result = await session.execute(text(query), params or {})
            await session.commit()
            return result.rowcount

    async def execute_script(self, script: str) -> None:
        """
        Execute a multi-statement SQL script.
        Properly handles multi-line statements and function definitions.
        """
        async with await self.get_session() as session:
            statements = []
            current = []
            paren_depth = 0
            in_dollar_quote = False
            i = 0

            while i < len(script):
                char = script[i]

                # Track $$ delimiters (for functions)
                if i < len(script) - 1 and script[i:i+2] == '$$':
                    in_dollar_quote = not in_dollar_quote
                    current.append('$$')
                    i += 2
                    continue

                # Track parenthesis depth (for multi-line statements)
                if not in_dollar_quote:
                    if char == '(':
                        paren_depth += 1
                    elif char == ')':
                        paren_depth -= 1

                # Statement terminator: semicolon at paren depth 0
                if char == ';' and paren_depth == 0 and not in_dollar_quote:
                    current.append(';')
                    stmt = ''.join(current).strip()
                    # Remove comments
                    stmt = '\n'.join(
                        line for line in stmt.split('\n')
                        if not line.strip().startswith('--')
                    ).strip()
                    if stmt and not stmt.startswith('--'):
                        statements.append(stmt)
                    current = []
                    i += 1
                    continue

                current.append(char)
                i += 1

            # Handle remaining content
            if current:
                stmt = ''.join(current).strip()
                stmt = '\n'.join(
                    line for line in stmt.split('\n')
                    if not line.strip().startswith('--')
                ).strip()
                if stmt:
                    statements.append(stmt)

            # Execute each statement
            for i, stmt in enumerate(statements, 1):
                try:
                    await session.execute(text(stmt))
                except Exception as e:
                    logger.error(f"Statement {i}/{len(statements)} failed:")
                    logger.error(f"  {stmt[:100]}...")
                    raise

            await session.commit()

    async def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                return {
                    "status": "healthy",
                    "database": self.config.POSTGRES_DB,
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


async def init_db(db: Database):
    """
    Initialize database schema using migration files.
    Loads and executes SQL migration files in order.

    Migrations:
    1. 00_init_schema.sql - Creates all tables with PostGIS geometry types
    2. 01_spatial_indexes.sql - Creates indexes and clusters
    """
    import os

    try:
        logger.info("📦 Initializing PostgreSQL schema from migration files...")

        # Get migration directory
        migration_dir = os.path.join(
            os.path.dirname(__file__),
            "..",
            "infra",
            "migrations"
        )

        # List of migration files in order
        migration_files = [
            "00_init_schema.sql",
            "01_spatial_indexes.sql",
            "02_classifications.sql"
        ]

        # Execute each migration file
        for migration_file in migration_files:
            migration_path = os.path.join(migration_dir, migration_file)

            if not os.path.exists(migration_path):
                logger.warning(f"⚠️  Migration file not found: {migration_path}")
                continue

            try:
                with open(migration_path, 'r') as f:
                    migration_sql = f.read()

                logger.info(f"📝 Executing migration: {migration_file}")

                # Check if schema already exists
                check_result = await db.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'thermal_events'
                    ) as exists
                """)
                schema_exists = check_result[0].get('exists', False) if check_result else False

                if schema_exists and migration_file == "00_init_schema.sql":
                    logger.info("⊘ Schema already exists, skipping 00_init_schema.sql")
                    continue

                # Split migration into individual statements and execute each
                import psycopg2

                def run_migration():
                    db_url = db.config.DATABASE_URL.replace('postgresql+asyncpg://', 'postgresql://')
                    conn = psycopg2.connect(db_url)
                    cursor = conn.cursor()

                    try:
                        # Split on semicolons, track $$ blocks
                        statements = []
                        current = []
                        in_dollar = False

                        for line in migration_sql.split('\n'):
                            if '$$' in line:
                                in_dollar = not in_dollar
                            current.append(line)
                            if ';' in line and not in_dollar:
                                stmt = '\n'.join(current).strip()
                                if stmt and not stmt.startswith('--'):
                                    statements.append(stmt)
                                current = []

                        if current:
                            stmt = '\n'.join(current).strip()
                            if stmt and not stmt.startswith('--'):
                                statements.append(stmt)

                        # Execute each statement individually
                        for stmt in statements:
                            if stmt.strip():
                                cursor.execute(stmt)

                        conn.commit()
                    except Exception as e:
                        conn.rollback()
                        raise
                    finally:
                        cursor.close()
                        conn.close()

                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, run_migration)

                logger.info(f"✓ Completed migration: {migration_file}")

            except Exception as e:
                logger.error(f"❌ Migration {migration_file} failed: {e}", exc_info=True)
                raise

        logger.info("✓ PostgreSQL schema initialization complete")

        # Verify critical tables exist with correct schema
        verify_result = await db.execute("""
            SELECT
                table_name,
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_name IN ('thermal_events', 'ingestion_runs', 'event_spatial_enrichment')
            ORDER BY table_name, ordinal_position
            LIMIT 5
        """)

        if verify_result:
            logger.info(f"✓ Schema verification: found {len(verify_result)} key columns")
            # Check for PostGIS geometry
            geom_check = await db.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'thermal_events' AND column_name = 'point'
            """)
            if geom_check and 'geometry' in str(geom_check[0].get('data_type', '').lower()):
                logger.info("✓ PostGIS geometry type confirmed on thermal_events.point")
            else:
                logger.warning("⚠️  PostGIS geometry may not be properly configured")

    except Exception as e:
        logger.error(f"❌ Schema initialization failed: {e}", exc_info=True)
        raise
