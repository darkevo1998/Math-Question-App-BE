import os
import sys
from http.server import BaseHTTPRequestHandler
import json

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Get the test type from query parameters
            test_type = self.path.split('?')[1] if '?' in self.path else 'all'
            if '=' in test_type:
                test_type = test_type.split('=')[1]
            
            debug_info = {
                'test_type': test_type,
                'environment': {
                    'DATABASE_URL': os.getenv("DATABASE_URL"),
                    'POSTGRES_URL_NON_POOLING': os.getenv("POSTGRES_URL_NON_POOLING"),
                    'VERCEL': os.getenv('VERCEL'),
                    'PYTHONPATH': os.getenv('PYTHONPATH')
                }
            }
            
            # Test 1: Module imports
            if test_type in ['all', 'modules']:
                debug_info['module_tests'] = {}
                
                # Test SQLAlchemy
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
                
                # Test pg8000
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
                
                # Test psycopg2
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
            
            # Test 2: Database connection
            if test_type in ['all', 'connection', 'db']:
                debug_info['database_tests'] = {}
                
                try:
                    from src.db import engine, SessionLocal
                    debug_info['database_tests']['engine_created'] = engine is not None
                    debug_info['database_tests']['session_local_created'] = SessionLocal is not None
                    
                    if engine is not None:
                        try:
                            from sqlalchemy import text
                            with engine.connect() as conn:
                                result = conn.execute(text("SELECT version()"))
                                version = result.fetchone()[0]
                                debug_info['database_tests']['connection_test'] = 'SUCCESS'
                                debug_info['database_tests']['postgres_version'] = version
                        except Exception as e:
                            debug_info['database_tests']['connection_test'] = 'FAILED'
                            debug_info['database_tests']['connection_error'] = str(e)
                    else:
                        debug_info['database_tests']['connection_test'] = 'SKIPPED - No engine'
                        
                except Exception as e:
                    debug_info['database_tests']['error'] = str(e)
            
            # Test 3: Models
            if test_type in ['all', 'models']:
                debug_info['model_tests'] = {}
                
                try:
                    from src.db import Base
                    debug_info['model_tests']['base_import'] = 'SUCCESS'
                except Exception as e:
                    debug_info['model_tests']['base_import'] = f'FAILED: {e}'
                
                try:
                    from src import models
                    debug_info['model_tests']['models_import'] = 'SUCCESS'
                except Exception as e:
                    debug_info['model_tests']['models_import'] = f'FAILED: {e}'
                
                try:
                    tables = list(Base.metadata.tables.keys())
                    debug_info['model_tests']['tables_detected'] = 'SUCCESS'
                    debug_info['model_tests']['tables'] = tables
                    debug_info['model_tests']['table_count'] = len(tables)
                except Exception as e:
                    debug_info['model_tests']['tables_detected'] = f'FAILED: {e}'
            
            # Test 4: Alembic
            if test_type in ['all', 'alembic']:
                debug_info['alembic_tests'] = {}
                
                # Get the project root directory
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                debug_info['project_root'] = project_root
                
                # Check if alembic directory exists
                alembic_dir = os.path.join(project_root, "alembic")
                debug_info['alembic_tests']['alembic_dir_exists'] = os.path.exists(alembic_dir)
                debug_info['alembic_tests']['alembic_dir_path'] = alembic_dir
                
                if os.path.exists(alembic_dir):
                    try:
                        alembic_contents = os.listdir(alembic_dir)
                        debug_info['alembic_tests']['alembic_contents'] = alembic_contents
                    except Exception as e:
                        debug_info['alembic_tests']['alembic_contents_error'] = str(e)
                    
                    # Check if env.py exists
                    env_py_path = os.path.join(alembic_dir, "env.py")
                    debug_info['alembic_tests']['env_py_exists'] = os.path.exists(env_py_path)
                    
                    # Check if versions directory exists
                    versions_dir = os.path.join(alembic_dir, "versions")
                    debug_info['alembic_tests']['versions_dir_exists'] = os.path.exists(versions_dir)
                
                # Check if alembic.ini exists
                alembic_ini_path = os.path.join(project_root, "alembic.ini")
                debug_info['alembic_tests']['alembic_ini_exists'] = os.path.exists(alembic_ini_path)
                
                # Try to import alembic
                try:
                    import alembic
                    debug_info['alembic_tests']['alembic_import'] = 'SUCCESS'
                    debug_info['alembic_tests']['alembic_version'] = alembic.__version__
                except Exception as e:
                    debug_info['alembic_tests']['alembic_import'] = f'FAILED: {e}'
            
            # Test 5: Database state (if connection works)
            if test_type in ['all', 'db', 'state'] and 'database_tests' in debug_info and debug_info['database_tests'].get('connection_test') == 'SUCCESS':
                try:
                    from sqlalchemy import inspect
                    inspector = inspect(engine)
                    tables = inspector.get_table_names()
                    
                    debug_info['database_state'] = {
                        'tables': tables,
                        'table_count': len(tables)
                    }
                    
                    # Get detailed info for each table
                    table_details = {}
                    for table_name in tables:
                        try:
                            columns = inspector.get_columns(table_name)
                            indexes = inspector.get_indexes(table_name)
                            foreign_keys = inspector.get_foreign_keys(table_name)
                            
                            table_details[table_name] = {
                                'columns': [col['name'] for col in columns],
                                'indexes': [idx['name'] for idx in indexes],
                                'foreign_keys': [fk['name'] for fk in foreign_keys if fk.get('name')]
                            }
                        except Exception as e:
                            table_details[table_name] = {'error': str(e)}
                    
                    debug_info['database_state']['table_details'] = table_details
                    
                except Exception as e:
                    debug_info['database_state_error'] = str(e)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(debug_info, indent=2).encode())
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'TestAllError',
                'message': str(e),
                'type': type(e).__name__
            }).encode())
