import os
import sys
from http.server import BaseHTTPRequestHandler
import json

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
                'manual_tests': {}
            }
            
            # Test 1: Try to import SQLAlchemy
            try:
                from sqlalchemy import create_engine
                debug_info['manual_tests']['sqlalchemy_import'] = 'SUCCESS'
            except Exception as e:
                debug_info['manual_tests']['sqlalchemy_import'] = 'FAILED'
                debug_info['manual_tests']['sqlalchemy_error'] = str(e)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(debug_info, indent=2).encode())
                return
            
            # Test 2: Try to create engine with DATABASE_URL
            database_url = os.getenv("POSTGRES_URL_NON_POOLING") or os.getenv("DATABASE_URL")
            if database_url:
                try:
                    # Fix postgres:// to postgresql://
                    if database_url.startswith('postgres://'):
                        database_url = database_url.replace('postgres://', 'postgresql://', 1)
                    
                    engine = create_engine(
                        database_url,
                        pool_pre_ping=True,
                        future=True,
                        pool_size=1,
                        max_overflow=0,
                        pool_recycle=300,
                        pool_timeout=30,
                        connect_args={
                            "sslmode": "require",
                            "connect_timeout": 10,
                            "application_name": "math-question-app"
                        }
                    )
                    debug_info['manual_tests']['engine_creation'] = 'SUCCESS'
                    
                    # Test 3: Try to connect
                    try:
                        from sqlalchemy import text
                        with engine.connect() as conn:
                            result = conn.execute(text("SELECT 1"))
                            debug_info['manual_tests']['connection_test'] = 'SUCCESS'
                    except Exception as conn_e:
                        debug_info['manual_tests']['connection_test'] = 'FAILED'
                        debug_info['manual_tests']['connection_error'] = str(conn_e)
                        debug_info['manual_tests']['connection_error_type'] = type(conn_e).__name__
                        
                except Exception as e:
                    debug_info['manual_tests']['engine_creation'] = 'FAILED'
                    debug_info['manual_tests']['engine_error'] = str(e)
                    debug_info['manual_tests']['engine_error_type'] = type(e).__name__
            else:
                debug_info['manual_tests']['engine_creation'] = 'SKIPPED - No DATABASE_URL'
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(debug_info, indent=2).encode())
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'TestConnectionError',
                'message': str(e),
                'type': type(e).__name__
            }).encode())
