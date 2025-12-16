from pyodbc import connect


class Database:
    def __init__(self, db_path, table_name):
        self.db_path = db_path
        self.table_name = table_name

    def _get_connection(self):
        return connect(f'Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.db_path}')

    def _fetch(self, query, params=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def _execute(self, query, params=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def generate_genre_map(self):
        query = "SELECT * from snCat1"
        rows = self._fetch(query)
        genre_map = {entry[0]: entry[1].lower() for entry in rows}
        genre_map[0] = "x"
        return genre_map

    def generate_decade_map(self):
        query = "SELECT * from snCat2"
        rows = self._fetch(query)
        return {entry[0]: entry[1] for entry in rows}

    def generate_tempo_map(self):
        query = "SELECT * from snCat3"
        rows = self._fetch(query)
        return {entry[0]: entry[1] for entry in rows}

    def update_song_filename(self, song_id, new_filename):
        query = f"UPDATE {self.table_name} SET fldFilename = ? WHERE AUID = ?"
        self._execute(query, (new_filename, song_id))

    def update_song_fields(self, song_id, fields):
        """
        Update multiple fields for a song by AUID.
        `fields` is a dict mapping column names to new values.
        """
        columns = ', '.join([f"{k}=?" for k in fields.keys()])
        values = list(fields.values())
        values.append(song_id)
        query = f"UPDATE {self.table_name} SET {columns} WHERE AUID = ?"
        self._execute(query, tuple(values))

    def delete_song(self, song_id):
        print(f"Deleting song with ID: {song_id}")
        query = f"DELETE FROM {self.table_name} WHERE AUID = ?"
        self._execute(query, (song_id,))

    def fetch_songs(self, field, value, exact_match):
        if exact_match:
            query = f"SELECT * FROM {self.table_name} WHERE {field} = ?"
            return self._fetch(query, (value,))
        else:
            query = f"SELECT * FROM {self.table_name} WHERE {field} LIKE ?"
            return self._fetch(query, (f'%{value}%',))

    def fetch_all_songs(self):
        query = f"SELECT * FROM {self.table_name}"
        return self._fetch(query)
