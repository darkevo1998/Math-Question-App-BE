import os
import sys
from http.server import BaseHTTPRequestHandler
import json

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import engine, SessionLocal

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
                # Import models to register them with SQLAlchemy
                from src.db import Base
                from src import models  # This imports all models
                
                # Check if tables already exist
                from sqlalchemy import text, inspect
                inspector = inspect(engine)
                existing_tables = inspector.get_table_names()
                
                if existing_tables:
                    # Tables exist, just verify they're accessible
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1 FROM users LIMIT 1"))
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'status': 'success',
                        'message': 'Database tables already exist and are accessible',
                        'method': 'tables_already_exist',
                        'existing_tables': existing_tables
                    }).encode())
                else:
                    # Create all tables
                    Base.metadata.create_all(bind=engine)
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'status': 'success',
                        'message': 'Database tables created successfully using SQLAlchemy',
                        'method': 'sqlalchemy_create_all',
                        'tables_created': list(Base.metadata.tables.keys())
                    }).encode())
                
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
