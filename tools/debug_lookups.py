import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.web.app import create_app, get_lookup_service

def debug_lookups():
    app = create_app()
    with app.app_context():
        # Mock session
        with app.test_request_context():
            from flask import session
            session['db_name'] = 'jazler_test'
            
            service = get_lookup_service(app)
            if not service:
                print("No service.")
                return

            print("Fetching snCat2 (Decade)...")
            records = service.get_all("snCat2")
            print(f"Found {len(records)} records.")
            
            if records:
                first = records[0]
                print(f"First record raw data: {first._data}")
                
                print("Testing ID access:")
                try:
                    print(f"record['ID'] = {first['ID']}")
                except KeyError:
                    print("record['ID'] failed")
                    
                print("Testing fldName access:")
                try:
                    print(f"record['fldName'] = {first['fldName']}")
                except KeyError:
                    print("record['fldName'] failed")

if __name__ == "__main__":
    debug_lookups()
