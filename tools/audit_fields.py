import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.web.app import create_app, get_backend
from src.core.schema.discovery import SchemaDiscovery

def audit_fields():
    app = create_app()
    with app.app_context():
        with app.test_request_context():
            # Mock the session db_name
            from flask import session
            session['db_name'] = 'jazler_test'
            
            backend = get_backend(app)
            if not backend:
                print("No backend connected.")
                return

            discovery = SchemaDiscovery()
            print("Probing table: snDatabase...")
            try:
                table_def = discovery.probe_table(backend, 'snDatabase')
                
                print(f"{'Column Name':<30} | {'Type':<15} | {'Nullable':<10}")
                print("-" * 60)
                
                for col in table_def.columns:
                    print(f"{col.name:<30} | {col.type_name:<15} | {str(col.nullable):<10}")
                    
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    audit_fields()
