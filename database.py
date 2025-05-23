from pyodbc import connect


class Database:
    def __init__(self, db_path, table_name):
        self.db_path = db_path
        self.table_name = table_name
        self.conn = connect(f'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path}')
        self.cursor = self.conn.cursor()

    def close(self):
        self.cursor.close()
        self.conn.close()

    def table_names(self):
        return [row.table_name for row in self.cursor.tables()]

    def column_names(self):
        self.cursor.execute(f'SELECT * FROM {self.table_name}')
        return [name[0] for name in self.cursor.description]

    def generate_genre_map(self):
        self.cursor.execute("SELECT * from snCat1")
        genre_query = self.cursor.fetchall()
        genre_map = {entry[0]: entry[1].lower() for entry in genre_query}
        genre_map[0] = "x"
        return genre_map

    def generate_decade_map(self):
        self.cursor.execute("SELECT * from snCat2")
        decade_query = self.cursor.fetchall()
        return {entry[0]: entry[1] for entry in decade_query}

    def generate_tempo_map(self):
        self.cursor.execute("SELECT * from snCat3")
        tempo_query = self.cursor.fetchall()
        return {entry[0]: entry[1] for entry in tempo_query}

    def update_song_filename(self, song_id, new_filename):
        self.cursor.execute(
            f"UPDATE {self.table_name} SET fldFilename = ? WHERE AUID = ?",
            new_filename, song_id
        )
        self.conn.commit()

    def update_song_fields(self, song_id, fields):
        """
        Update multiple fields for a song by AUID.
        `fields` is a dict mapping column names to new values.
        """
        columns = ', '.join([f"{k}=?" for k in fields.keys()])
        values = list(fields.values())
        values.append(song_id)
        self.cursor.execute(
            f"UPDATE {self.table_name} SET {columns} WHERE AUID = ?",
            *values
        )
        self.conn.commit()

    def delete_song(self, song_id):
        print(f"Deleting song with ID: {song_id}")
        self.cursor.execute(f"DELETE FROM {self.table_name} WHERE AUID = ?", song_id)
        self.conn.commit()

    def fetch_songs(self, field, value, exact_match):
        if exact_match:
            self.cursor.execute(f"SELECT * FROM {self.table_name} WHERE {field} = ?", value)
        else:
            self.cursor.execute(f"SELECT * FROM {self.table_name} WHERE {field} LIKE ?", f'%{value}%')
        return self.cursor.fetchall()
