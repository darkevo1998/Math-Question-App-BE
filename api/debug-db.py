import os
import sys
from http.server import BaseHTTPRequestHandler
import json
import traceback

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            debug_info = {
                'database_url': os.getenv("DATABASE_URL"),
                'vercel_env': os.getenv('VERCEL'),
                'pythonpath': os.getenv('PYTHONPATH'),
                'sqlalchemy_import': 'NOT_TESTED',
                'url_fix': 'NOT_TESTED',
                'engine_creation': 'NOT_TESTED',
                'connection_test': 'NOT_TESTED',
                'errors': []
            }
            
            # Test SQLAlchemy import
            try:
                from sqlalchemy import create_engine, text
                debug_info['sqlalchemy_import'] = 'SUCCESS'
            except Exception as e:
                debug_info['sqlalchemy_import'] = f'FAILED: {e}'
                debug_info['errors'].append(f'SQLAlchemy import failed: {e}')
            
            # Test URL fix
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                try:
                    if database_url.startswith('postgres://'):
                        fixed_url = database_url.replace('postgres://', 'postgresql://', 1)
                        debug_info['url_fix'] = f'FIXED: {fixed_url}'
                    else:
                        debug_info['url_fix'] = 'NO_FIX_NEEDED'
                except Exception as e:
                    debug_info['url_fix'] = f'FAILED: {e}'
                    debug_info['errors'].append(f'URL fix failed: {e}')
            
            # Test engine creation
            if database_url and debug_info['sqlalchemy_import'] == 'SUCCESS':
                try:
                    # Fix URL if needed
                    test_url = database_url
                    if test_url.startswith('postgres://'):
                        test_url = test_url.replace('postgres://', 'postgresql://', 1)
                    
                    engine = create_engine(
                        test_url,
                        pool_pre_ping=True,
                        future=True,
                        pool_size=1,
                        max_overflow=0,
                        pool_recycle=300,
                        pool_timeout=20,
                        # Supabase-specific settings
                        connect_args={
                            "sslmode": "require"
                        }
                    )
                    debug_info['engine_creation'] = 'SUCCESS'
                    
                    # Test connection
                    try:
                        with engine.connect() as conn:
                            result = conn.execute(text("SELECT 1"))
                            debug_info['connection_test'] = 'SUCCESS'
                    except Exception as conn_e:
                        debug_info['connection_test'] = f'FAILED: {conn_e}'
                        debug_info['errors'].append(f'Connection test failed: {conn_e}')
                        
                except Exception as e:
                    debug_info['engine_creation'] = f'FAILED: {e}'
                    debug_info['errors'].append(f'Engine creation failed: {e}')
                    debug_info['errors'].append(f'Full traceback: {traceback.format_exc()}')
            
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
                'traceback': traceback.format_exc()
            }).encode())
