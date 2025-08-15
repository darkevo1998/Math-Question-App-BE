import os
import sys
from http.server import BaseHTTPRequestHandler
import json

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import engine, SessionLocal
from alembic import command
from alembic.config import Config

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if engine is None:
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'DatabaseError', 
                    'message': 'Database not configured',
                    'debug': f"DATABASE_URL: {os.getenv('DATABASE_URL')}"
                }).encode())
                return

            # Test if we can actually connect to the database
            try:
                from sqlalchemy import text
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            except Exception as conn_error:
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'DatabaseConnectionError', 
                    'message': 'Cannot connect to database',
                    'debug': f"Connection error: {str(conn_error)}"
                }).encode())
                return

            try:
                # Try Alembic first, but fallback to direct SQLAlchemy if it fails
                try:
                    # Check if alembic directory exists
                    alembic_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "alembic")
                    if not os.path.exists(alembic_dir):
                        raise Exception("Alembic directory not found")
                    
                    # Create Alembic config
                    alembic_cfg = Config()
                    alembic_cfg.set_main_option("script_location", "alembic")
                    
                    # Get the same DATABASE_URL that was used to create the engine
                    from src.db import ORIGINAL_DATABASE_URL as db_url
                    if db_url:
                        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
                    else:
                        # Fallback to environment variable
                        database_url = os.getenv("DATABASE_URL")
                        if database_url and database_url.startswith('postgres://'):
                            database_url = database_url.replace('postgres://', 'postgresql://', 1)
                        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
                    
                    # Run migration
                    command.upgrade(alembic_cfg, "head")
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'status': 'success',
                        'message': 'Database migration completed successfully using Alembic',
                        'method': 'alembic'
                    }).encode())
                    return
                    
                except Exception as alembic_error:
                    # Fallback: Create tables directly using SQLAlchemy
                    from src.db import Base
                    from src import models  # Import models to register them
                    
                    # Create all tables with check_if_exists=True to handle existing tables
                    try:
                        Base.metadata.create_all(bind=engine, checkfirst=True)
                        method_used = "direct_sqlalchemy"
                    except Exception as create_error:
                        # If tables already exist, that's fine - just check if they're accessible
                        from sqlalchemy import text
                        with engine.connect() as conn:
                            conn.execute(text("SELECT 1 FROM users LIMIT 1"))
                        method_used = "tables_already_exist"
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'status': 'success',
                        'message': f'Database tables ready successfully (fallback method)',
                        'method': method_used,
                        'alembic_error': str(alembic_error)
                    }).encode())
                    return

                
            except Exception as e:
                import traceback
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'MigrationError',
                    'message': str(e),
                    'type': type(e).__name__,
                    'traceback': traceback.format_exc()
                }).encode())
                
        except Exception as e:
            import traceback
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'InternalError',
                'message': str(e),
                'type': type(e).__name__,
                'traceback': traceback.format_exc()
            }).encode())
