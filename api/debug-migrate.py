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
            debug_info = {
                'environment': {
                    'DATABASE_URL': os.getenv("DATABASE_URL"),
                    'POSTGRES_URL_NON_POOLING': os.getenv("POSTGRES_URL_NON_POOLING"),
                    'VERCEL': os.getenv('VERCEL'),
                    'PYTHONPATH': os.getenv('PYTHONPATH')
                },
                'database': {
                    'engine_created': engine is not None,
                    'session_local_created': SessionLocal is not None
                }
            }
            
            # Test database connection if engine exists
            if engine is not None:
                try:
                    from sqlalchemy import text
                    with engine.connect() as conn:
                        result = conn.execute(text("SELECT version()"))
                        version = result.fetchone()[0]
                        debug_info['database']['connection_test'] = 'SUCCESS'
                        debug_info['database']['postgres_version'] = version
                except Exception as e:
                    debug_info['database']['connection_test'] = 'FAILED'
                    debug_info['database']['connection_error'] = str(e)
                    debug_info['database']['error_type'] = type(e).__name__
            else:
                debug_info['database']['connection_test'] = 'SKIPPED - No engine'
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(debug_info, indent=2).encode())
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'DebugError',
                'message': str(e),
                'type': type(e).__name__
            }).encode())
