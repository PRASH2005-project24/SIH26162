import os
import asyncpg
import sys
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in .env")
    sys.exit(1)

# Convert SQLAlchemy URL to asyncpg URL if needed
# postgresql+asyncpg:// -> postgresql://
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    ASYNCPG_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
else:
    ASYNCPG_URL = DATABASE_URL

print(f"Connecting to database: {ASYNCPG_URL.split('@')[1] if '@' in ASYNCPG_URL else 'URL hidden'}")

# We'll mask the password in the URL for display
def mask_password(url):
    if '://' in url:
        protocol, rest = url.split('://', 1)
        if '@' in rest:
            credentials, hostpart = rest.rsplit('@', 1)
            if ':' in credentials:
                user, _ = credentials.split(':', 1)
                return f"{protocol}://{user}:****@{hostpart}"
    return url

print(f"Connection URL (masked): {mask_password(ASYNCPG_URL)}")

async def main():
    conn = None
    try:
        conn = await asyncpg.connect(ASYNCPG_URL)
        print("Successfully connected to the database")

        # Get PostgreSQL version
        pg_version = await conn.fetchval("SELECT version()")
        print(f"PostgreSQL version: {pg_version}")

        # Get PostGIS version
        try:
            postgis_version = await conn.fetchval("SELECT PostGIS_Version()")
            print(f"PostGIS version: {postgis_version}")
        except Exception as e:
            print(f"PostGIS not available or error: {e}")

        # List schemas
        schemas = await conn.fetch("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            ORDER BY schema_name;
        """)
        print(f"\nFound {len(schemas)} schemas: {[s['schema_name'] for s in schemas]}")

        # For each schema, get tables
        for schema in schemas:
            schema_name = schema['schema_name']
            print(f"\n--- Schema: {schema_name} ---")
            tables = await conn.fetch(f"""
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = '{schema_name}'
                ORDER BY table_type, table_name;
            """)
            if not tables:
                print("  No tables found.")
                continue
            print(f"  Found {len(tables)} tables:")
            for table in tables:
                table_name = table['table_name']
                table_type = table['table_type']
                # Get row count
                try:
                    row_count = await conn.fetchval(f"SELECT COUNT(*) FROM {schema_name}.{table_name}")
                except Exception as e:
                    row_count = f"Error: {e}"
                print(f"    - {table_name} ({table_type}) - Rows: {row_count}")

                # Get column info
                columns = await conn.fetch(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = '{schema_name}' AND table_name = '{table_name}'
                    ORDER BY ordinal_position;
                """)
                print(f"      Columns ({len(columns)}):")
                for col in columns:
                    print(f"        {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")

                # Check for geometry columns and PostGIS info
                try:
                    geom_columns = await conn.fetch(f"""
                        SELECT f_geometry_column as geom_column, type, srid
                        FROM geometry_columns
                        WHERE f_table_schema = '{schema_name}' AND f_table_name = '{table_name}';
                    """)
                    if geom_columns:
                        print("      Geometry columns:")
                        for geom in geom_columns:
                            print(f"        {geom['geom_column']}: {geom['type']} SRID={geom['srid']}")
                except Exception:
                    pass  # geometry_columns view may not exist if no PostGIS or no geometry

                # Look for potential label/target columns
                label_cols = [col for col in columns if col['column_name'].lower() in ('target_class', 'class', 'label', 'fire_type', 'source_type', 'classification', 'industrial_fire', 'wildfire', 'agricultural_fire', 'persistent_thermal_source', 'unknown')]
                if label_cols:
                    print("      Potential label/target columns:")
                    for col in label_cols:
                        print(f"        {col['column_name']}: {col['data_type']}")
                        # Get distinct values if the column is not too large
                        try:
                            # Limit to 10 distinct values
                            distinct_vals = await conn.fetch(f"""
                                SELECT DISTINCT {col['column_name']}
                                FROM {schema_name}.{table_name}
                                WHERE {col['column_name']} IS NOT NULL
                                LIMIT 10;
                            """)
                            vals = [str(v[col['column_name']]) for v in distinct_vals]
                            print(f"          Sample values: {', '.join(vals)}")
                        except Exception as e:
                            print(f"          Could not retrieve distinct values: {e}")

                # Check for persistence-related columns
                persistence_keywords = ['detections_24h', 'detections_3d', 'detections_7d', 'active_days', 'persistence_duration_days', 'persistence_score', 'first_detection', 'last_detection', 'detection_count', 'mean_frp', 'max_frp']
                pers_cols = [col for col in columns if any(kw in col['column_name'].lower() for kw in persistence_keywords)]
                if pers_cols:
                    print("      Persistence-related columns:")
                    for col in pers_cols:
                        print(f"        {col['column_name']}: {col['data_type']}")

                # Check for OSM-related columns
                osm_keywords = ['osm', 'facility', 'industrial', 'nearest', 'distance', 'water']
                osm_cols = [col for col in columns if any(kw in col['column_name'].lower() for kw in osm_keywords)]
                if osm_cols:
                    print("      OSM-related columns:")
                    for col in osm_cols:
                        print(f"        {col['column_name']}: {col['data_type']}")

                # Check for Dynamic World-related columns
                dw_keywords = ['dw_', 'dynamic_world']
                dw_cols = [col for col in columns if any(kw in col['column_name'].lower() for kw in dw_keywords)]
                if dw_cols:
                    print("      Dynamic World-related columns:")
                    for col in dw_cols:
                        print(f"        {col['column_name']}: {col['data_type']}")

    except Exception as e:
        print(f"Failed to connect or inspect database: {e}")
        sys.exit(1)
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())