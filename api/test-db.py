import os
import sys
from http.server import BaseHTTPRequestHandler
import json

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Get the DATABASE_URL
            database_url = os.getenv("DATABASE_URL")
            
            # Test basic SQLAlchemy import
            try:
                from sqlalchemy import create_engine
                sqlalchemy_import = "SUCCESS"
            except Exception as e:
                sqlalchemy_import = f"FAILED: {e}"
            
            # Test engine creation
            engine_status = "NOT_ATTEMPTED"
            if database_url:
                try:
                    # Fix postgres:// to postgresql:// for SQLAlchemy compatibility
                    if database_url.startswith('postgres://'):
                        database_url = database_url.replace('postgres://', 'postgresql://', 1)
                    
                    engine = create_engine(database_url)
                    engine_status = "SUCCESS"
                except Exception as e:
                    engine_status = f"FAILED: {e}"
            
            # Test connection
            connection_status = "NOT_ATTEMPTED"
            if database_url and engine_status == "SUCCESS":
                try:
                    # Fix postgres:// to postgresql:// for SQLAlchemy compatibility
                    test_url = database_url
                    if test_url.startswith('postgres://'):
                        test_url = test_url.replace('postgres://', 'postgresql://', 1)
                    
                    engine = create_engine(test_url)
                    with engine.connect() as conn:
                        result = conn.execute("SELECT 1")
                        connection_status = "SUCCESS"
                except Exception as e:
                    connection_status = f"FAILED: {e}"
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'database_url': database_url,
                'sqlalchemy_import': sqlalchemy_import,
                'engine_creation': engine_status,
                'connection_test': connection_status,
                'environment': {
                    'VERCEL': os.getenv('VERCEL'),
                    'PYTHONPATH': os.getenv('PYTHONPATH')
                }
            }, indent=2).encode())
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'TestError',
                'message': str(e)
            }).encode())
