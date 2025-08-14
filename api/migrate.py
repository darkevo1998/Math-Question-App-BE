import os
import sys
from http.server import BaseHTTPRequestHandler
import json

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db import engine, SessionLocal
from alembic import command
from alembic.config import Config

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

            try:
                # Create Alembic config
                alembic_cfg = Config()
                alembic_cfg.set_main_option("script_location", "alembic")
                alembic_cfg.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))
                
                # Run migration
                command.upgrade(alembic_cfg, "head")
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'success',
                    'message': 'Database migration completed successfully'
                }).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'MigrationError',
                    'message': str(e)
                }).encode())
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'InternalError',
                'message': str(e)
            }).encode())
