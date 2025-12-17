import pytest
from unittest.mock import MagicMock, patch, ANY
import sys
import threading
from contextlib import ExitStack

from src.ui.app import DatabaseEditor
from src.models.song import Song, SongID3

# -- Fixtures --

@pytest.fixture(autouse=True)
def no_threads():
    """Globally mock threading.Thread to prevent background execution."""
    with patch('threading.Thread') as mock_thread:
        yield mock_thread

@pytest.fixture
def mock_tk():
    """Patches all tkinter widgets used in app.py"""
    with ExitStack() as stack:
        mocks = {}
        
        # Global / Tkinter
        stack.enter_context(patch('src.ui.app.Tk'))
        stack.enter_context(patch('tkinter.Toplevel'))
        stack.enter_context(patch('tkinter.Frame'))
        stack.enter_context(patch('tkinter.Text'))
        stack.enter_context(patch('tkinter.Scrollbar'))
        stack.enter_context(patch('tkinter.ttk.Treeview'))
        stack.enter_context(patch('tkinter.ttk.PanedWindow'))
        stack.enter_context(patch('tkinter.ttk.Style'))
        
        # App Widgets
        stack.enter_context(patch('src.ui.app.Toplevel'))
        stack.enter_context(patch('src.ui.app.Label'))
        stack.enter_context(patch('src.ui.app.Button'))
        mocks['Entry'] = stack.enter_context(patch('src.ui.app.Entry'))
        stack.enter_context(patch('src.ui.app.Frame'))
        stack.enter_context(patch('src.ui.app.ttk.Style'))
        stack.enter_context(patch('src.ui.app.ttk.Label'))
        
        # Mapped Mocks
        mocks['Button'] = stack.enter_context(patch('src.ui.app.ttk.Button'))
        mocks['Combobox'] = stack.enter_context(patch('src.ui.app.Combobox'))
        mocks['MessageBox'] = stack.enter_context(patch('src.ui.app.messagebox'))
        mocks['ErrorHandler'] = stack.enter_context(patch('src.ui.app.ErrorHandler'))
        
        # Utils
        stack.enter_context(patch('src.utils.error_handler.ErrorHandler'))
        
        # ErrorLogViewer Specifics (to handle late imports)
        stack.enter_context(patch('src.ui.dialogs.error_log_viewer.Toplevel'))
        stack.enter_context(patch('src.ui.dialogs.error_log_viewer.Frame'))
        stack.enter_context(patch('src.ui.dialogs.error_log_viewer.Label'))
        stack.enter_context(patch('src.ui.dialogs.error_log_viewer.Button'))
        stack.enter_context(patch('src.ui.dialogs.error_log_viewer.Text'))
        stack.enter_context(patch('src.ui.dialogs.error_log_viewer.Scrollbar'))
        stack.enter_context(patch('src.ui.dialogs.error_log_viewer.ttk.Treeview'))
        stack.enter_context(patch('src.ui.dialogs.error_log_viewer.ttk.PanedWindow'))

        # Setup Entry widget behavior
        mocks['Entry'].return_value.get.return_value = ""
        
        yield mocks

@pytest.fixture
def mock_app_deps(mock_config):
    """Patches Database and Config interactions."""
    with patch('src.ui.app.Database') as MockDB, \
         patch('src.ui.app.AudioMetadata') as MockAudio:
         
        db_instance = MockDB.return_value
        
        # Helper to create long tuples for DB records
        def create_record():
            r = [None] * 30
            r[20] = "z:\\song.mp3" # Filename index
            return tuple(r)
            
        # Setup default DB responses
        db_instance.generate_genre_map.return_value = {0: "x", 1: "Pop"}
        db_instance.generate_decade_map.return_value = {1: "1990s"}
        db_instance.generate_tempo_map.return_value = {1: "Fast"}
        db_instance.fetch_all_songs.return_value = [create_record(), create_record()]
        db_instance.fetch_songs.return_value = [create_record()] 
        
        yield {
            "db": db_instance,
            "audio": MockAudio
        }

@pytest.fixture
def app(mock_tk, mock_app_deps):
    """Instantiates the App with mocked dependencies."""
    # Patch the BASE CLASS init to avoid Tcl creation
    with patch('tkinter.Tk.__init__', return_value=None), \
         patch('src.ui.app.threading.Thread'), \
         patch.object(DatabaseEditor, 'ask_database_mode', return_value=False), \
         patch.object(DatabaseEditor, 'setup_ui'), \
         patch.object(DatabaseEditor, 'get_song'), \
         patch.object(DatabaseEditor, 'lift'), \
         patch.object(DatabaseEditor, 'attributes'), \
         patch.object(DatabaseEditor, 'title'), \
         patch.object(DatabaseEditor, 'config'), \
         patch.object(DatabaseEditor, 'deiconify'), \
         patch.object(DatabaseEditor, 'withdraw'), \
         patch.object(DatabaseEditor, 'after_idle'), \
         patch.object(DatabaseEditor, 'protocol'), \
         patch.object(DatabaseEditor, '_load_song_thread_job'):
        
        app = DatabaseEditor()

        # Manually verify init state
        assert app.use_live is False
        
        # Populate widgets manually for testing logic
        app.texts_db = {k: MagicMock() for k in ["artist", "title", "album", "composer", "publisher", "year", "genre", "isrc", "decade", "duration"]}
        app.texts_id3 = {k: MagicMock() for k in ["artist", "title", "album", "composer", "publisher", "year", "genre", "isrc", "decade", "duration"]}
        
        # Populate Status Labels
        app.lbl_stat_genre = MagicMock()
        app.lbl_stat_isrc = MagicMock()
        app.lbl_stat_file = MagicMock()
        app.label_counter = MagicMock()
        app.label_filename = MagicMock()
        app.text_jump = MagicMock()
        
        # Populate Control Buttons (Fixes RecursionError in toggle_controls)
        app.button_previous = MagicMock()
        app.button_next = MagicMock()
        app.button_jump = MagicMock()
        app.button_query = MagicMock()
        app.button_save = MagicMock()
        app.button_rename = MagicMock()
        
        # Done Status Label Mock
        app.lbl_done_status = MagicMock()
        
        # UI State helpers override
        app.button_google = MagicMock()
        app.button_discog = MagicMock()
        
        # Ensure base class methods are mocked on instance if patch didn't catch specific calls
        app.withdraw = MagicMock()
        app.deiconify = MagicMock()
        
        # Setup initial song query data (simulating DB loaded 2 songs)
        # Re-use logic from create_record in deps or simple list
        r = [None] * 30
        r[20] = "z:\\song.mp3"
        app.song_query = [tuple(r), tuple(r)]
        app.position = 0
        
        # Setup simple song object
        app.song = MagicMock(spec=Song)
        app.song.id = 1
        app.song.artist = "Artist"
        app.song.title = "Title"
        app.song.album = "Album"
        app.song.composer = "Composer"
        app.song.publisher = "Publisher"
        app.song.year = 2000
        app.song.genre_01_name = "Pop"
        app.song.genres_all = "Pop"
        app.song.isrc = "US123"
        app.song.duration = 180.0
        app.song.location_local = "local.mp3"
        app.song.location_correct = "local.mp3"
        app.song.decade = "2000s"
        app.song.genre_02_name = "Rock"
        app.song.genre_03_name = "Jazz"
        app.song.genre_04_id = 1
        app.song.genre_04_name = "2000s"
        
        app.id3 = MagicMock(spec=Song)
        app.id3.error = "No error"
        app.id3.artist = "Artist"
        app.id3.title = "Title"
        app.id3.genres_all = "Pop"
        app.id3.isrc = "US123"
        app.id3.duration = 180.0
        app.id3.album = "Album"
        app.id3.composer = "Composer"
        app.id3.publisher = "Publisher"
        app.id3.year = 2000
        
        # Mock Validation to pass by default
        app.validator = MagicMock()
        app.validator.validate.return_value.is_valid = True
        app.validator.validate.return_value.issues = []
        
        return app

# -- Helpers --

def sync_inputs(app, field, value):
    """Helper to ensure both DB and ID3 inputs match to prevent silent mismatches."""
    app.texts_db[field].get.return_value = value
    app.texts_id3[field].get.return_value = value

# -- Existing Tests --

def test_gather_data_from_ui(app):
    """Test scraping data from UI widgets into the Song object."""
    app.texts_db["title"].get.return_value = "New Title"
    app.texts_db["year"].get.return_value = "2021"
    app._gather_data_from_ui()
    assert app.song.title == "New Title"
    assert app.song.year == 2021


    def test_save_song_validation_failure(app, mock_tk):
        """Test blocking save when validation fails."""
        # Override validation to fail
        issue = MagicMock()
        issue.message = "Title is required"
        app.validator.validate.return_value.is_valid = False
        app.validator.validate.return_value.issues = [issue]

        sync_inputs(app, "artist", "Artist")
        sync_inputs(app, "year", "2000")
        sync_inputs(app, "genre", "Pop")
        sync_inputs(app, "isrc", "US123")
        sync_inputs(app, "title", "") 
        
        with patch('src.models.song.Song.check_genre', return_value=True), \
             patch('src.models.song.Song.get_genre_id', return_value=1):
            app.save_song(False)
            
        mock_tk["ErrorHandler"].show_warning.assert_called_with("Title is required")

def test_save_song_success(app, mock_app_deps, mock_tk):
    sync_inputs(app, "artist", "Artist")
    sync_inputs(app, "title", "Title")
    sync_inputs(app, "album", "Album")
    sync_inputs(app, "composer", "Composer")
    sync_inputs(app, "publisher", "Publisher")
    sync_inputs(app, "year", "2000")
    app.texts_db["genre"].get.return_value = "Pop"
    app.texts_id3["genre"].get.return_value = "Pop"
    sync_inputs(app, "isrc", "US123")
    app.id3.artist = "Artist"
    app.id3.title = "Title"
    app.id3.album = "Album"
    app.id3.composer = "Composer"
    app.id3.publisher = "Publisher"
    app.id3.year = 2000
    app.id3.genres_all = "Pop"
    app.id3.isrc = "US123"
    
    with patch('src.models.song.Song.check_genre', return_value=True), \
         patch('src.models.song.Song.get_genre_id', return_value=1):
        app.save_song(False)
    
    if mock_tk["ErrorHandler"].show_warning.called:
         pass
         
    mock_app_deps["db"].update_song_fields.assert_called()

# -- NEW Path Validation Tests --

def test_save_song_bad_path_standard_genre(app, mock_tk, mock_app_deps):
    """Test warning triggers for standard genre in wrong folder."""
    # Ensure "Country" is valid in the map
    mock_app_deps["db"].generate_genre_map.return_value = {0: "x", 1: "Pop", 2: "Country"}
    app.genre_map = {0: "x", 1: "Pop", 2: "Country"}
    app.reverse_genre_map = {"x": 0, "pop": 1, "country": 2}
    
    sync_inputs(app, "artist", "Artist")
    sync_inputs(app, "title", "Title")
    sync_inputs(app, "album", "Album")
    sync_inputs(app, "composer", "Composer")
    sync_inputs(app, "publisher", "Publisher")
    sync_inputs(app, "year", "2000")
    
    app.texts_db["genre"].get.return_value = "Country"
    app.texts_id3["genre"].get.return_value = "Country"
    app.song.genre_01_name = "Country"
    sync_inputs(app, "isrc", "US123")
    
    # Setup Paths
    app.song.location_local = "z:\\downloads\\Artist - Title.mp3"
    app.song.location_correct = "z:\\songs\\Country\\2000\\Artist - Title.mp3"
    
    # Patch Config to include Country as Standard
    rules = {
        "standard_subfolder": ["country"],
        "path_overrides": {},
        "no_year_subfolder": [],
        "no_genre_subfolder": ["pop"]
    }
    mock_config_instance = MagicMock()
    mock_config_instance.genre_rules = rules
    
    # Mock Validator to fail with path issue (simulating what SongValidator would do)
    issue = MagicMock()
    issue.message = "File is in the wrong folder!"
    app.validator.validate.return_value.is_valid = False
    app.validator.validate.return_value.issues = [issue]
    
    with patch('src.models.song.Song.check_genre', return_value=True), \
         patch('src.models.song.Song.get_genre_id', return_value=2), \
         patch('src.ui.app.app_config', mock_config_instance):
        app.save_song(False)
        
    # Verify Warning for "Wrong Folder"
    # app.py calls ErrorHandler.show_warning(validation_result.issues[0].message)
    mock_tk["ErrorHandler"].show_warning.assert_called_with("File is in the wrong folder!")
    
    mock_app_deps["db"].update_song_fields.assert_not_called()

def test_save_song_unknown_genre(app, mock_tk, mock_app_deps):
    """Test warning triggers for genre not defined in config."""
    # Ensure "Mystery" is valid in the map (logic passes)
    mock_app_deps["db"].generate_genre_map.return_value = {0: "x", 1: "Pop", 2: "Mystery"}
    app.genre_map = {0: "x", 1: "Pop", 2: "Mystery"}
    app.reverse_genre_map = {"x": 0, "pop": 1, "mystery": 2}
    
    sync_inputs(app, "artist", "Artist")
    sync_inputs(app, "title", "Title")
    sync_inputs(app, "album", "Album")
    sync_inputs(app, "composer", "Composer")
    sync_inputs(app, "publisher", "Publisher")
    sync_inputs(app, "year", "2000")
    app.texts_db["genre"].get.return_value = "Mystery"
    app.texts_id3["genre"].get.return_value = "Mystery"
    app.song.genre_01_name = "Mystery"
    sync_inputs(app, "isrc", "US123")
    
    # Patch Config (Mystery is not in any list)
    rules = {
        "standard_subfolder": ["country"],
        "path_overrides": {},
        "no_year_subfolder": [],
        "no_genre_subfolder": ["pop"]
    }
    mock_config_instance = MagicMock()
    mock_config_instance.genre_rules = rules
    
    # Mock Validator to fail (simulating SongValidator catching unknown genre)
    issue = MagicMock()
    issue.message = "Genre 'Mystery' is not defined in config rules!"
    app.validator.validate.return_value.is_valid = False
    app.validator.validate.return_value.issues = [issue]
    
    with patch('src.models.song.Song.check_genre', return_value=True), \
         patch('src.models.song.Song.get_genre_id', return_value=2), \
         patch('src.ui.app.app_config', mock_config_instance):
        app.save_song(False)
        
    # Verify Warning for "Not Defined"
    mock_tk["ErrorHandler"].show_warning.assert_called_with("Genre 'Mystery' is not defined in config rules!")
    
    mock_app_deps["db"].update_song_fields.assert_not_called()

def test_save_song_bad_path_special_genre(app, mock_tk, mock_app_deps):
    """Test NO warning for special genre in wrong folder."""
    # "Pop" is special
    sync_inputs(app, "artist", "Artist")
    sync_inputs(app, "title", "Title")
    sync_inputs(app, "album", "Album")
    sync_inputs(app, "composer", "Composer")
    sync_inputs(app, "publisher", "Publisher")
    sync_inputs(app, "year", "2000")
    app.texts_db["genre"].get.return_value = "Pop"
    app.texts_id3["genre"].get.return_value = "Pop"
    sync_inputs(app, "isrc", "US123")
    
    app.song.location_local = "z:\\downloads\\Artist - Title.mp3"
    app.song.location_correct = "z:\\songs\\Pop\\Artist - Title.mp3"
    
    with patch('src.models.song.Song.check_genre', return_value=True), \
         patch('src.models.song.Song.get_genre_id', return_value=1):
        app.save_song(False)
        
    # Verify NO folder warning
    warnings = [call[0][0] for call in mock_tk["ErrorHandler"].show_warning.call_args_list]
    if any("wrong folder" in w for w in warnings):
        pytest.fail(f"Unexpected folder warning found: {warnings}")
            
    # Expect DB Update
    # If this fails, print warnings to debug why validation aborted
    if not mock_app_deps["db"].update_song_fields.called:
         pytest.fail(f"Save aborted unexpectedly. Warnings: {warnings}")
    
    mock_app_deps["db"].update_song_fields.assert_called()

# -- NEW Tests for Buttons & Navigation --

def test_nav_next(app):
    """Test clicking Next button logic."""
    app.position = 0
    with patch('threading.Thread') as MockThread:
        app.get_song(1)
        
        # Should increment position
        assert app.position == 1
        
        # Should start thread to load song at pos 1
        MockThread.assert_called()
        args = MockThread.call_args[1]
        assert args['args'][0] == 1 # Position 1
        MockThread.return_value.start.assert_called()

def test_nav_prev(app):
    """Test clicking Prev button logic."""
    app.position = 1
    with patch('threading.Thread') as MockThread:
        app.get_song(-1)
        assert app.position == 0
        MockThread.assert_called()
        
def test_nav_jump(app):
    """Test entering a number and jumping."""
    app.text_jump.get.return_value = "2"
    with patch('threading.Thread') as MockThread:
        app.get_song(None)
        assert app.position == 1 # 1-indexed input "2" -> 0-indexed pos 1
        MockThread.assert_called()

def test_query_flow(app, mock_tk):
    """Test opening query window and submitting."""
    # Ensure Toplevel is mocked to return a mock window we can pass around
    with patch('src.ui.app.Toplevel') as MockTop, \
         patch('threading.Thread') as MockThread:
         
        # app.query_db calls self.withdraw(). We mocked it on instance in fixture.
        
        app.query_db()
        
        # Verify popup created
        MockTop.assert_called()
        
        # Simulate button click triggering query_button_click
        window_mock = MockTop.return_value
        app.query_button_click("artist", "contains", "Abba", window_mock)
        
        # Verify thread started
        MockThread.assert_called()

def test_rename_song(app, mock_app_deps, mock_tk):
    """Test rename flow (F6)."""
    # Setup conditions
    app.song.location_local = "z:\\old.mp3"
    app.song.location_correct = "z:\\new.mp3"
    
    # We need to mock shutil and os interactions inside song_rename
    with patch('shutil.move') as mock_move, \
         patch('src.ui.app.makedirs') as mock_makedir, \
         patch('src.ui.app.path.exists', return_value=False):
         
        app.song_rename()
        
        mock_move.assert_called_with("z:\\old.mp3", "z:\\new.mp3")
        mock_app_deps["db"].update_song_filename.assert_called()
        
        args = mock_app_deps["db"].update_song_filename.call_args[0]
        assert "b:\\new.mp3" in args[1]
        
        # Verify Success Message
        mock_tk["ErrorHandler"].show_info.assert_called_with("File renamed successfully!")

def test_rename_song_move_failure(app, mock_app_deps, mock_tk):
    """Test rename rollback when file move fails."""
    app.song.location_local = "z:\\old.mp3"
    app.song.location_correct = "z:\\new.mp3"
    
    with patch('shutil.move', side_effect=PermissionError("Locked")), \
         patch('src.ui.app.makedirs'), \
         patch('src.ui.app.path.exists', return_value=False):
         
        app.song_rename()
        
        # Verify DB updated then rolled back
        # DB calls: 1. update to new, 2. update to old
        db_calls = mock_app_deps["db"].update_song_filename.call_args_list
        assert len(db_calls) == 2
        assert "b:\\new.mp3" in db_calls[0][0][1] # Initial update
        assert "b:\\old.mp3" in db_calls[1][0][1] # Rollback
        
        # Verify Error Dialog shown
        mock_tk["ErrorHandler"].show_error.assert_called()
        args = mock_tk["ErrorHandler"].show_error.call_args[0]
        assert "Rename Failed" in args[0]

def test_rename_song_rollback_failure(app, mock_app_deps, mock_tk):
    """Test critical error when rollback fails."""
    app.song.location_local = "z:\\old.mp3"
    app.song.location_correct = "z:\\new.mp3"
    
    # Mock DB to succeed first time, then fail
    mock_app_deps["db"].update_song_filename.side_effect = [None, Exception("DB Down")]
    
    with patch('shutil.move', side_effect=PermissionError("Locked")), \
         patch('src.ui.app.makedirs'), \
         patch('src.ui.app.path.exists', return_value=False):
         
        app.song_rename()
        
        # Verify Critical Error
        mock_tk["ErrorHandler"].show_critical.assert_called()
        args = mock_tk["ErrorHandler"].show_critical.call_args[0]
        assert "CRITICAL" in args[0]
        assert "DB thinks it is at" in args[1]


