import os
import sys
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Flask app
from app import create_app

# Create Flask app instance
app = create_app()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse the URL
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # Create Flask request context
            with app.test_request_context(path, query_string=parsed_url.query):
                response = app.full_dispatch_request()
                
                # Send response
                self.send_response(response.status_code)
                
                # Set CORS headers
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                
                # Set content type
                if response.mimetype:
                    self.send_header('Content-Type', response.mimetype)
                
                self.end_headers()
                
                # Send response data
                if response.data:
                    self.wfile.write(response.data)
                    
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e), 'path': self.path}).encode())
    
    def do_POST(self):
        try:
            # Parse the URL
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b''
            
            # Create Flask request context
            with app.test_request_context(path, data=post_data, method='POST'):
                response = app.full_dispatch_request()
                
                # Send response
                self.send_response(response.status_code)
                
                # Set CORS headers
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                
                # Set content type
                if response.mimetype:
                    self.send_header('Content-Type', response.mimetype)
                
                self.end_headers()
                
                # Send response data
                if response.data:
                    self.wfile.write(response.data)
                    
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def do_OPTIONS(self):
        # Handle CORS preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
