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
                'model_tests': {}
            }
            
            # Test 1: Import Base
            try:
                from src.db import Base
                debug_info['model_tests']['base_import'] = 'SUCCESS'
            except Exception as e:
                debug_info['model_tests']['base_import'] = f'FAILED: {e}'
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(debug_info, indent=2).encode())
                return
            
            # Test 2: Import models
            try:
                from src import models
                debug_info['model_tests']['models_import'] = 'SUCCESS'
            except Exception as e:
                debug_info['model_tests']['models_import'] = f'FAILED: {e}'
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(debug_info, indent=2).encode())
                return
            
            # Test 3: Check tables
            try:
                tables = list(Base.metadata.tables.keys())
                debug_info['model_tests']['tables_detected'] = 'SUCCESS'
                debug_info['model_tests']['tables'] = tables
                debug_info['model_tests']['table_count'] = len(tables)
            except Exception as e:
                debug_info['model_tests']['tables_detected'] = f'FAILED: {e}'
            
            # Test 4: Generate SQL (without executing)
            try:
                from sqlalchemy import create_engine
                # Create a dummy engine just for SQL generation
                dummy_engine = create_engine('sqlite:///:memory:')
                sql_statements = []
                for table in Base.metadata.sorted_tables:
                    sql = str(table.compile(dummy_engine))
                    sql_statements.append({
                        'table': table.name,
                        'sql': sql
                    })
                debug_info['model_tests']['sql_generation'] = 'SUCCESS'
                debug_info['model_tests']['sql_statements'] = sql_statements
            except Exception as e:
                debug_info['model_tests']['sql_generation'] = f'FAILED: {e}'
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(debug_info, indent=2).encode())
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': 'ModelTestError',
                'message': str(e),
                'type': type(e).__name__
            }).encode())
