import os
import sys
from http.server import BaseHTTPRequestHandler
import json

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Get all relevant environment variables
            env_info = {
                'DATABASE_URL': os.getenv("DATABASE_URL"),
                'VERCEL': os.getenv('VERCEL'),
                'PYTHONPATH': os.getenv('PYTHONPATH'),
                'all_env_vars': dict(os.environ)
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(env_info, indent=2).encode())
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'EnvTestError',
                'message': str(e)
            }).encode())
