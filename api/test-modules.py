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
                'module_tests': {}
            }
            
            # Test 1: SQLAlchemy
            try:
                import sqlalchemy
                debug_info['module_tests']['sqlalchemy'] = {
                    'status': 'SUCCESS',
                    'version': sqlalchemy.__version__
                }
            except Exception as e:
                debug_info['module_tests']['sqlalchemy'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
            
            # Test 2: pg8000
            try:
                import pg8000
                debug_info['module_tests']['pg8000'] = {
                    'status': 'SUCCESS',
                    'version': pg8000.__version__ if hasattr(pg8000, '__version__') else 'unknown'
                }
            except Exception as e:
                debug_info['module_tests']['pg8000'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
            
            # Test 3: psycopg2
            try:
                import psycopg2
                debug_info['module_tests']['psycopg2'] = {
                    'status': 'SUCCESS',
                    'version': psycopg2.__version__ if hasattr(psycopg2, '__version__') else 'unknown'
                }
            except Exception as e:
                debug_info['module_tests']['psycopg2'] = {
                    'status': 'FAILED',
                    'error': str(e)
                }
            
            # Test 4: Try to create engine with each driver
            database_url = os.getenv("POSTGRES_URL_NON_POOLING") or os.getenv("DATABASE_URL")
            if database_url and database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            
            if database_url:
                debug_info['engine_tests'] = {}
                
                # Test with pg8000
                if debug_info['module_tests']['pg8000']['status'] == 'SUCCESS':
                    try:
                        from sqlalchemy import create_engine
                        engine = create_engine(database_url, module="pg8000")
                        debug_info['engine_tests']['pg8000'] = 'SUCCESS'
                    except Exception as e:
                        debug_info['engine_tests']['pg8000'] = f'FAILED: {str(e)}'
                
                # Test with psycopg2
                if debug_info['module_tests']['psycopg2']['status'] == 'SUCCESS':
                    try:
                        from sqlalchemy import create_engine
                        engine = create_engine(database_url, module="psycopg2")
                        debug_info['engine_tests']['psycopg2'] = 'SUCCESS'
                    except Exception as e:
                        debug_info['engine_tests']['psycopg2'] = f'FAILED: {str(e)}'
                
                # Test without explicit driver
                try:
                    from sqlalchemy import create_engine
                    engine = create_engine(database_url)
                    debug_info['engine_tests']['auto'] = 'SUCCESS'
                except Exception as e:
                    debug_info['engine_tests']['auto'] = f'FAILED: {str(e)}'
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(debug_info, indent=2).encode())
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'ModuleTestError',
                'message': str(e),
                'type': type(e).__name__
            }).encode())
