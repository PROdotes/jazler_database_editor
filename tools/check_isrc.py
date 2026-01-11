import sys
import os
import re

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.web.app import create_app, get_backend

def check_isrc_candidates():
    app = create_app()
    with app.app_context():
        # Mock session for backend connection
        with app.test_request_context():
            from flask import session
            session['db_name'] = 'jazler_test'
            
            backend = get_backend(app)
            if not backend:
                print("No backend connected.")
                return

            print("Scanning for ISRC-like data in candidate columns...")
            print("-" * 60)
            
            # ISRC Regex: 2 chars (country), 3 chars (registrant), 2 digits (year), 5 digits (designation)
            # Roughly: ^[A-Z]{2}-?[A-Z0-9]{3}-?\d{2}-?\d{5}$
            isrc_pattern = re.compile(r'[A-Z]{2}-?[A-Z0-9]{3}-?\d{2}-?\d{5}', re.IGNORECASE)
            
            columns = ['fldCDKey', 'fldBarCode', 'fldCodeString', 'fldComments', 'fldProperties']
            
            for col in columns:
                try:
                    # distinct values to save time
                    query = f"SELECT DISTINCT {col} FROM snDatabase WHERE {col} IS NOT NULL"
                    rows = backend.execute_raw(query)
                    
                    found = 0
                    samples = []
                    
                    for row in rows:
                        val = str(row[0]).strip()
                        if len(val) > 5 and isrc_pattern.search(val):
                            found += 1
                            if len(samples) < 5:
                                samples.append(val)
                    
                    print(f"Column: {col}")
                    print(f"  Matches found: {found}")
                    if samples:
                        print(f"  Samples: {', '.join(samples)}")
                    else:
                        print("  No ISRC-like patterns found.")
                    print("-" * 40)
                    
                except Exception as e:
                    print(f"Skipping {col}: {e}")

if __name__ == "__main__":
    check_isrc_candidates()
