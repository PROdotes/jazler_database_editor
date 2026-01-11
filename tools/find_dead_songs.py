import sys
import os

# Add root directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.engine import JazlerEngine
from src.core.config import app_config

def main():
    # Use live DB by default unless a path is passed
    use_live = len(sys.argv) == 1
    engine = JazlerEngine(use_live=use_live)
    
    print(f"🕵️ Hunting for Dead Songs in: {engine.db_path}")
    
    dead_count = 0
    dead_songs = []

    print("\n🔍 Scanning filesystems (this may take a minute)...")
    
    # Use the generator from our new Headless Engine
    for song in engine.find_missing_files():
        dead_count += 1
        dead_songs.append((song.id, song.artist, song.title, song.location_local))
        print(f"❌ [{dead_count}] DEAD: {song.artist} - {song.title}")
        print(f"   Path: {song.location_local}")

    print("\n--- 🏁 SCAN COMPLETE ---")
    print(f"Total Dead Songs:    {dead_count}")
    
    if dead_songs:
        log_file = "dead_songs_report.txt"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"DEAD SONGS REPORT\n")
            f.write("-" * 50 + "\n")
            for sid, artist, title, path in dead_songs:
                f.write(f"ID: {sid:<5} | {artist} - {title}\n")
                f.write(f"PATH: {path}\n\n")
        print(f"📄 Detailed report saved to: {log_file}")

if __name__ == "__main__":
    main()
