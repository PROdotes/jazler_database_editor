import sys
import os
import argparse
import pyodbc
from pyodbc import connect

# Add root directory to path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.config import app_config

def probe_database(db_path):
    print(f"🔍 Probing Database (Robust Encoding): {db_path}")
    if not os.path.exists(db_path):
        print(f"❌ Error: File not found at {db_path}")
        return

    try:
        # Standard Access connection string
        conn_str = f'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path}'
        
        # Connect
        conn = connect(conn_str)
        
        # FORCE FIX: Using literals to avoid any constant resolution issues
        # SQL_CHAR = 1
        # SQL_WCHAR = -8
        # SQL_WMETADATA = -9 (in some versions)
        try:
            # First, try to fix the metadata decoding which often crashes on column names
            # We use Latin-1/CP1252 as a safe fallback that never fails to decode
            conn.setdecoding(pyodbc.SQL_CHAR, encoding='cp1250') 
            conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16le')
            
            # This is often the culprit for column name crashes
            if hasattr(pyodbc, 'SQL_WMETADATA'):
                conn.setdecoding(pyodbc.SQL_WMETADATA, encoding='utf-16le')
                
            conn.setencoding(encoding='utf-8')
            print("✅ Custom encoding layer applied.")
        except Exception as e:
            print(f"⚠️ Encoding setup failure (skipping): {e}")

        cursor = conn.cursor()

        # 1. List all tables
        print("\n--- Tables Found ---")
        try:
            tables = list(cursor.tables())
            user_tables = [t.table_name for t in tables if t.table_type == 'TABLE' and not t.table_name.startswith('MSys')]
            for name in user_tables:
                print(f"📋 {name}")
        except:
            user_tables = ["snDatabase"]

        # 2. Detailed Column View for snDatabase
        target_table = "snDatabase"
        if target_table in user_tables:
            print(f"\n--- Columns in {target_table} ---")
            
            # We fetch columns one by one and handle errors per-column
            # so one bad character doesn't kill the whole probe
            try:
                # cursor.columns returns a result set describing columns
                cursor.execute(f"SELECT TOP 1 * FROM {target_table}")
                description = cursor.description
                for i, col in enumerate(description):
                    # col[0] is name, col[1] is type
                    name = col[0]
                    print(f"{i:2}: {name:<25}")
            except Exception as e:
                print(f"❌ Primary column fetch failed, trying alternate: {e}")
                try:
                    cols = list(cursor.columns(table=target_table))
                    for i, c in enumerate(cols):
                        print(f"{i:2}: {c.column_name}")
                except Exception as e2:
                    print(f"⚠️ All column fetch methods failed: {e2}")

            # 3. Row count
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {target_table}")
                count = cursor.fetchone()[0]
                print(f"\n📈 Total Records in {target_table}: {count}")
            except:
                pass
        else:
            print(f"\n⚠️ Table '{target_table}' not found.")

        cursor.close()
        conn.close()
        print("\n✅ Probe Complete.")

    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Investigate MS Access Database Schema")
    parser.add_argument("--test", action="store_true", help="Use the test database path")
    parser.add_argument("--live", action="store_true", help="Use the live database path")
    
    args = parser.parse_args()
    db_path = app_config.db_path_test if args.test else app_config.db_path_live
    probe_database(db_path)
