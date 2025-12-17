import pytest
import pyodbc
from unittest.mock import MagicMock, patch
from src.core.database import Database

@pytest.fixture
def mock_cursor():
    cursor = MagicMock()
    cursor.fetchall.return_value = []
    # Support context manager if needed, mainly for fetchall/execute interactions
    return cursor

@pytest.fixture
def mock_connection(mock_cursor):
    conn = MagicMock()
    conn.cursor.return_value = mock_cursor
    return conn

@pytest.fixture
def db_instance(mock_connection):
    with patch('src.core.database.connect', return_value=mock_connection):
        db = Database("fake.mdb", "snDatabase")
        yield db

# -- Connection Logic --

def test_get_connection_success(db_instance, mock_connection):
    conn = db_instance._get_connection()
    assert conn == mock_connection

def test_connect_arg_verification():
    with patch('src.core.database.connect') as mock_connect:
        db = Database("C:\\path\\to\\db.mdb", "snDatabase")
        db._get_connection()
        args = mock_connect.call_args[0]
        assert "Driver={Microsoft Access Driver (*.mdb, *.accdb)}" in args[0]
        assert "DBQ=C:\\path\\to\\db.mdb" in args[0]

def test_get_connection_failure():
    with patch('src.core.database.connect', side_effect=pyodbc.Error("Connection Failed")):
        with pytest.raises(Exception):
            db = Database("bad.mdb", "snDatabase")
            db._get_connection()

# -- Fetch Logic --

def test_fetch_songs(db_instance, mock_cursor):
    mock_cursor.fetchall.return_value = [("Song1",), ("Song2",)]
    results = db_instance.fetch_songs("Artist", "Abba", False)
    assert len(results) == 2

def test_fetch_songs_exact_match(db_instance, mock_cursor):
    db_instance.fetch_songs("Artist", "Abba", exact_match=True)
    query = mock_cursor.execute.call_args[0][0]
    assert "WHERE Artist = ?" in query

def test_fetch_songs_contains_match(db_instance, mock_cursor):
    db_instance.fetch_songs("Artist", "Abba", exact_match=False)
    query = mock_cursor.execute.call_args[0][0]
    assert "WHERE Artist LIKE ?" in query

def test_fetch_all_songs(db_instance, mock_cursor):
    """Test fetching all songs (no params, no limit)."""
    db_instance.fetch_all_songs()
    query = mock_cursor.execute.call_args[0][0]
    assert "SELECT * FROM snDatabase" in query
    # Should call execute with NO params (hitting line 19 in _fetch)
    assert len(mock_cursor.execute.call_args[0]) == 1

def test_fetch_songs_error(db_instance, mock_cursor):
    mock_cursor.execute.side_effect = pyodbc.Error("SQL Syntax Error")
    with pytest.raises(pyodbc.Error):
        db_instance.fetch_songs("Artist", "Abba", False)

# -- Map Generation (Missing Coverage) --

def test_generate_genre_map(db_instance, mock_cursor):
    # Mock [(id, name)]
    mock_cursor.fetchall.return_value = [(1, "Pop"), (2, "Rock")]
    
    g_map = db_instance.generate_genre_map()
    
    # Assert query
    query = mock_cursor.execute.call_args[0][0]
    assert "SELECT * from snCat1" in query
    
    # Assert Logic
    assert g_map[1] == "pop"
    assert g_map[2] == "rock"
    assert g_map[0] == "x" # logic coverage

def test_generate_decade_map(db_instance, mock_cursor):
    mock_cursor.fetchall.return_value = [(1, "1990s"), (2, "2000s")]
    d_map = db_instance.generate_decade_map()
    assert "SELECT * from snCat2" in mock_cursor.execute.call_args[0][0]
    assert d_map[1] == "1990s"

def test_generate_tempo_map(db_instance, mock_cursor):
    mock_cursor.fetchall.return_value = [(1, "Fast")]
    t_map = db_instance.generate_tempo_map()
    assert "SELECT * from snCat3" in mock_cursor.execute.call_args[0][0]
    assert t_map[1] == "Fast"

# -- Update/Execute Logic --

def test_update_song_filename(db_instance, mock_cursor):
    db_instance.update_song_filename(1, "new.mp3")
    args = mock_cursor.execute.call_args[0]
    assert "UPDATE snDatabase SET fldFilename = ? WHERE AUID = ?" in args[0]

def test_update_song_fields(db_instance, mock_cursor):
    data = {"Title": "New Title", "Year": 2022}
    db_instance.update_song_fields(5, data)
    query = mock_cursor.execute.call_args[0][0]
    assert "UPDATE snDatabase SET" in query
    assert "Title=?" in query

def test_delete_song(db_instance, mock_cursor):
    """Test deletion (Lines 71-73)."""
    db_instance.delete_song(1)
    args = mock_cursor.execute.call_args[0]
    assert "DELETE FROM snDatabase WHERE AUID = ?" in args[0]
    assert args[1] == (1,)

def test_execute_no_params(db_instance, mock_cursor):
    """Test _execute method with no params to hit line 31-32."""
    # We can invoke _execute directly or find a method that uses it without params.
    # Currently only update/delete use params.
    # We will invoke private method _execute directly for coverage.
    db_instance._execute("UPDATE snDatabase SET fldTitle = 'Fixed'")
    mock_cursor.execute.assert_called_with("UPDATE snDatabase SET fldTitle = 'Fixed'")
