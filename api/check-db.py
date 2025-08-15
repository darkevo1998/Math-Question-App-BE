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
            if engine is None:
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'DatabaseError', 
                    'message': 'Database not configured'
                }).encode())
                return

            # Test if we can actually connect to the database
            try:
                from sqlalchemy import text, inspect
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                # Get database information
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                
                db_info = {
                    'connection': 'SUCCESS',
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
                
                db_info['table_details'] = table_details
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(db_info, indent=2).encode())
                
            except Exception as conn_error:
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'DatabaseConnectionError', 
                    'message': 'Cannot connect to database',
                    'debug': f"Connection error: {str(conn_error)}"
                }).encode())
                
        except Exception as e:
            import traceback
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'InternalError',
                'message': str(e),
                'type': type(e).__name__,
                'traceback': traceback.format_exc()
            }).encode())
