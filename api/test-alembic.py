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
                'alembic_tests': {}
            }
            
            # Get the project root directory
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            debug_info['project_root'] = project_root
            
            # Test 1: Check if alembic directory exists
            alembic_dir = os.path.join(project_root, "alembic")
            debug_info['alembic_tests']['alembic_dir_exists'] = os.path.exists(alembic_dir)
            debug_info['alembic_tests']['alembic_dir_path'] = alembic_dir
            
            if os.path.exists(alembic_dir):
                # Test 2: List contents of alembic directory
                try:
                    alembic_contents = os.listdir(alembic_dir)
                    debug_info['alembic_tests']['alembic_contents'] = alembic_contents
                except Exception as e:
                    debug_info['alembic_tests']['alembic_contents_error'] = str(e)
                
                # Test 3: Check if env.py exists
                env_py_path = os.path.join(alembic_dir, "env.py")
                debug_info['alembic_tests']['env_py_exists'] = os.path.exists(env_py_path)
                debug_info['alembic_tests']['env_py_path'] = env_py_path
                
                # Test 4: Check if versions directory exists
                versions_dir = os.path.join(alembic_dir, "versions")
                debug_info['alembic_tests']['versions_dir_exists'] = os.path.exists(versions_dir)
                
                if os.path.exists(versions_dir):
                    try:
                        versions_contents = os.listdir(versions_dir)
                        debug_info['alembic_tests']['versions_contents'] = versions_contents
                    except Exception as e:
                        debug_info['alembic_tests']['versions_contents_error'] = str(e)
            
            # Test 5: Check if alembic.ini exists
            alembic_ini_path = os.path.join(project_root, "alembic.ini")
            debug_info['alembic_tests']['alembic_ini_exists'] = os.path.exists(alembic_ini_path)
            debug_info['alembic_tests']['alembic_ini_path'] = alembic_ini_path
            
            # Test 6: Try to import alembic
            try:
                import alembic
                debug_info['alembic_tests']['alembic_import'] = 'SUCCESS'
                debug_info['alembic_tests']['alembic_version'] = alembic.__version__
            except Exception as e:
                debug_info['alembic_tests']['alembic_import'] = f'FAILED: {e}'
            
            # Test 7: List all files in project root
            try:
                root_contents = os.listdir(project_root)
                debug_info['project_root_contents'] = root_contents
            except Exception as e:
                debug_info['project_root_contents_error'] = str(e)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(debug_info, indent=2).encode())
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'AlembicTestError',
                'message': str(e),
                'type': type(e).__name__
            }).encode())
