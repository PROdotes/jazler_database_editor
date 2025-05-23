pyinstaller --clean main.py
pyinstaller --onefile --additional-hooks-dir=. main.py
.\dist\main.exe
