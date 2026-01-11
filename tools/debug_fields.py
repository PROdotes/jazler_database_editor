import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.web.app import create_app, get_song_service

def debug_search_fields():
    app = create_app()
    with app.app_context():
        # Mock session
        with app.test_request_context():
            from flask import session
            session['db_name'] = 'jazler_test'
            
            service = get_song_service(app)
            if not service:
                print("No service.")
                return

            print("Searchable Fields:")
            print("-" * 30)
            fields = service.get_searchable_fields()
            for key, label in fields:
                print(f"{key}: {label}")
                
            print("\nNon-Searchable but in Schema:")
            print("-" * 30)
            for col in service._schema.columns:
                if not col.display_name:
                    pass # print(f"{col.name} (No Display Name)")

if __name__ == "__main__":
    debug_search_fields()
