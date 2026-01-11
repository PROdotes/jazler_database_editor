import sys
import os
import argparse
import re
from collections import defaultdict

# Add root directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.engine import JazlerEngine
from src.core.config import app_config
from src.models.db_schema import SongColumns as Col

def normalize_string(s):
    if not s:
        return ""
    # Lowercase, collapse spaces, remove special chars
    s = s.lower()
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def normalize_path(path):
    if not path:
        return ""
    p = path.lower().replace('/', '\\').strip()
    p = p.replace(".mp3.mp3", ".mp3")
    p = re.sub(r'\s+', ' ', p)
    p = p.replace(" .", ".")
    return p

def audit_and_resurrect(db_path, log_file, fuzzy=True):
    print(f"🕵️ Lost & Found Audit: Analyzing 50k+ records using {log_file}")
    
    if not os.path.exists(log_file):
        print(f"❌ Error: Log file not found at {log_file}")
        return

    # 1. Indexing the disk log
    print("⏳ Indexing files by path and name...")
    path_set = set()
    name_map = defaultdict(list) # filename -> list of full paths
    
    current_dir = ""
    dir_pattern = re.compile(r"^\s*Directory:\s*(.*)$")
    
    # Try different encodings
    encoding_list = ['utf-16', 'utf-8', 'cp1252']
    lines = []
    for enc in encoding_list:
        try:
            with open(log_file, 'r', encoding=enc, errors='ignore') as f:
                content = f.read()
                if content:
                    lines = content.splitlines()
                    print(f"✅ Reading with {enc}...")
                    break
        except Exception:
            continue

    if not lines:
        print("❌ Could not read log file.")
        return

    for line in lines:
        stripped = line.strip()
        dir_match = dir_pattern.match(line)
        if dir_match:
            current_dir = dir_match.group(1).strip()
            continue
            
        if current_dir and stripped.startswith("-a----"):
            parts = stripped.split()
            if len(parts) >= 5:
                filename = " ".join(parts[4:])
                full_path = os.path.join(current_dir, filename)
                
                norm_full = normalize_path(full_path)
                norm_name = normalize_string(filename)
                
                path_set.add(norm_full)
                name_map[norm_name].append(full_path)
    
    print(f"✅ Indexed {len(path_set)} files.")

    # 2. Initialize Engine
    try:
        engine = JazlerEngine(use_live=(db_path == app_config.db_path_live))
    except Exception as e:
        print(f"❌ Database error: {e}")
        return

    # 3. Audit
    print("🔍 Searching for missing songs in new locations...")
    results = {
        "ok": 0,
        "moved": [],
        "deleted": []
    }
    
    records = engine.db.fetch_all_songs()
    total = len(records)
    d_map = [(k.lower(), v.lower()) for k, v in app_config.drive_map.items()]
    
    for i, record in enumerate(records):
        raw_db_path = record[Col.FILENAME]
        
        # Drive map normalization
        local_path = raw_db_path.lower().replace('/', '\\')
        for k, v in d_map:
            if local_path.startswith(k):
                local_path = local_path.replace(k, v)
                break
        
        norm_db_path = normalize_path(local_path)
        
        # Check 1: Is it where it should be?
        if norm_db_path in path_set:
            results["ok"] += 1
        else:
            # Check 2: Did it move?
            filename = os.path.basename(raw_db_path)
            norm_filename = normalize_string(filename)
            
            potential_paths = name_map.get(norm_filename)
            
            artist = record[Col.ARTIST_NAME] or "Unknown"
            title = record[Col.TITLE] or "Unknown"
            entry = {
                "id": record[Col.AUID],
                "artist": artist,
                "title": title,
                "old_path": raw_db_path
            }

            if potential_paths:
                # Found somewhere else!
                entry["new_paths"] = potential_paths
                results["moved"].append(entry)
            else:
                # TRULY GHOSTED
                results["deleted"].append(entry)

        if i > 0 and i % 10000 == 0:
            print(f"--- Processed {i}/{total} records ---")

    # 4. Reporting
    print(f"\n--- 🏁 ANALYSIS COMPLETE ---")
    print(f"✅ Still in place: {results['ok']}")
    print(f"📦 Moved (Found elsewhere): {len(results['moved'])}")
    print(f"👻 Ghosted (Truly deleted): {len(results['deleted'])}")
    
    report_name = "library_investigation_report.txt"
    with open(report_name, "w", encoding="utf-8") as f:
        f.write("JAZLER LIBRARY INTEGRITY REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"--- 📦 MOVED SONGS ({len(results['moved'])}) ---\n")
        f.write("These exist in the DB but were found in DIFFERENT folders on disk.\n")
        for m in results["moved"]:
            f.write(f"[{m['id']}] {m['artist']} - {m['title']}\n")
            f.write(f"   DB Path:  {m['old_path']}\n")
            for new_p in m["new_paths"]:
                f.write(f"   FOUND AT: {new_p}\n")
            f.write("\n")

        f.write(f"\n--- 👻 GHOSTED SONGS ({len(results['deleted'])}) ---\n")
        f.write("These exist in the DB but were NOT FOUND ANYWHERE on the drive.\n")
        for d in results["deleted"]:
            f.write(f"[{d['id']}] {d['artist']} - {d['title']}\n")
            f.write(f"   DB Path: {d['old_path']}\n\n")
            
    print(f"📄 Full investigation saved to: {report_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find moved vs deleted songs using a disk log")
    parser.add_argument("log_file", help="Path to the log.txt")
    parser.add_argument("--test", action="store_true", help="Use the test database")
    
    args = parser.parse_args()
    db_path = app_config.db_path_test if args.test else app_config.db_path_live
    audit_and_resurrect(db_path, args.log_file)
