from PyInstaller.utils.hooks import collect_data_files
datas = collect_data_files("mutagen.id3")
datas += collect_data_files("pyodbc")
