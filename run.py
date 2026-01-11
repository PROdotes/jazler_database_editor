import sys
from src.web.app import create_app

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'cli':
        print("CLI mode not yet implemented in run.py wrapper")
        return
        
    # Default to Web mode
    print("Starting Web Interface on http://localhost:5000")
    app = create_app()
    app.run(debug=True, port=5000, use_reloader=False)

if __name__ == "__main__":
    main()
