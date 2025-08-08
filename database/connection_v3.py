import os
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Database connection pool
connection_pool = None

def init_connection_pool():
    """Initialize the database connection pool with psycopg3."""
    global connection_pool
    
    try:
        DATABASE_URL = os.getenv('DATABASE_URL')
        
        if not DATABASE_URL:
            logger.error("DATABASE_URL not found in environment variables")
            return False
        
        # Create connection pool with psycopg3
        connection_pool = ConnectionPool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
            open=True
        )
        
        if connection_pool:
            logger.info("Database connection pool created successfully")
            return True
            
    except Exception as error:
        logger.error(f"Error creating connection pool: {error}")
        return False

def get_db_connection():
    """Get a connection from the pool."""
    global connection_pool
    
    if connection_pool is None:
        if not init_connection_pool():
            return None
    
    try:
        # Get connection from pool
        connection = connection_pool.getconn()
        if connection:
            # Set row factory to dict
            connection.row_factory = dict_row
            return connection
    except Exception as error:
        logger.error(f"Error getting connection from pool: {error}")
        return None

def return_db_connection(connection):
    """Return a connection to the pool."""
    global connection_pool
    
    if connection_pool and connection:
        try:
            connection_pool.putconn(connection)
        except Exception as error:
            logger.error(f"Error returning connection to pool: {error}")

def close_all_connections():
    """Close all connections in the pool."""
    global connection_pool
    
    if connection_pool:
        try:
            connection_pool.close()
            logger.info("All database connections closed")
        except Exception as error:
            logger.error(f"Error closing connections: {error}")

def test_connection():
    """Test the database connection."""
    try:
        DATABASE_URL = os.getenv('DATABASE_URL')
        
        if not DATABASE_URL:
            logger.error("DATABASE_URL not found")
            return False
        
        # Simple connection test
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute("SELECT version();")
                db_version = cursor.fetchone()
                logger.info(f"Connected to: {db_version['version']}")
                
                # Test if our table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'supervision_operativa_detalle'
                    );
                """)
                table_exists = cursor.fetchone()['exists']
                
                if table_exists:
                    logger.info("Table 'supervision_operativa_detalle' found")
                    
                    # Get table info
                    cursor.execute("""
                        SELECT COUNT(*) as count FROM supervision_operativa_detalle;
                    """)
                    record_count = cursor.fetchone()['count']
                    logger.info(f"Table has {record_count} records")
                else:
                    logger.warning("Table 'supervision_operativa_detalle' not found")
                
                return True
                
    except Exception as error:
        logger.error(f"Error testing connection: {error}")
        return False

def execute_query(query, params=None):
    """Execute a query and return results."""
    try:
        DATABASE_URL = os.getenv('DATABASE_URL')
        
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute(query, params)
                
                # Check if it's a SELECT query
                if query.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
                else:
                    conn.commit()
                    return cursor.rowcount
                    
    except Exception as error:
        logger.error(f"Error executing query: {error}")
        return None