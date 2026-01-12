"""
Flask application factory for the Database Toolkit web UI.
"""

import json
import logging
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from flask_session import Session

from src.backends.access import AccessBackend
from src.core.schema import SchemaRegistry
from src.services.song_service import SongService
from src.services.media_service import MediaService
from src.services.vfs_service import VfsService
from src.services.snapshot_service import SnapshotService
from src.services.sync_service import SyncService
from src.services.audit_service import AuditService
from src.services.schema_settings_service import SchemaSettingsService
from src.services.export_service import ExportService
from src.services.lookup_service import LookupService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Service cache
_services = {
    'backend': None,
    'registry': None,
    'song_service': None,
    'media_service': None,
    'vfs_service': None,
    'snapshot_service': None,
    'sync_service': None,
    'audit_service': None,
    'schema_settings': None,
    'export_service': None,
    'lookup_service': None
}

def load_connections():
    """Load database connections from config."""
    config_path = Path(__file__).parent.parent.parent / 'config' / 'connections.json'
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load connections: {e}")
    return {'databases': {}}


def create_app():
    """Application factory."""
    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')
    
    # Secret key for sessions
    app.secret_key = 'dev-key-change-in-production'
    
    # Configure Server-side sessions
    # This stores session data in the .sessions folder instead of cookies
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = str(Path(__file__).parent.parent.parent / '.sessions')
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    
    # Ensure session dir exists
    Path(app.config['SESSION_FILE_DIR']).mkdir(exist_ok=True)
    
    # Initialize session
    Session(app)
    
    # Store shared objects
    app.config['CONNECTIONS'] = load_connections()
    
    # Register routes
    from src.web.routes.main import main_bp
    from src.web.routes.songs import songs_bp
    from src.web.routes.schema import schema_bp
    from src.web.routes.sync import sync_bp
    from src.web.routes.audit import audit_bp
    from src.web.routes.export import export_bp
    from src.web.routes.lookups import lookups_bp
    from src.web.routes.artists import bp as artists_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(songs_bp, url_prefix='/songs')
    app.register_blueprint(schema_bp, url_prefix='/schema')
    app.register_blueprint(sync_bp, url_prefix='/sync')
    app.register_blueprint(audit_bp, url_prefix='/audit')
    app.register_blueprint(export_bp, url_prefix='/export')
    app.register_blueprint(lookups_bp, url_prefix='/lookups')
    app.register_blueprint(artists_bp)
    
    @app.context_processor
    def inject_globals():
        db_name = session.get('db_name', 'Not Connected')
        is_live = 'live' in db_name.lower() or session.get('is_live', False)
        logger.info(f"Context Processor: db_name={db_name}, is_live={is_live}")
        return dict(
            db_name=db_name,
            is_live=is_live,
            sync_count=get_sync_service(app).count(),
            offline_mode=session.get('offline_mode', False)
        )
    
    @app.teardown_appcontext
    def teardown_backend(exception):
        """No-op for now, but good for cleanup."""
        pass
    
    return app


def get_backend(app):
    """Get or create the database backend."""
    global _services
    if _services['backend'] is None:
        db_name = session.get('db_name', 'jazler_test')
        # Use session override path if available (common for synced test DB)
        db_path = session.get('active_db_path')
        
        if not db_path:
            # Fallback to static config
            connections = app.config['CONNECTIONS']
            db_config = connections.get('databases', {}).get(db_name, {})
            db_path = db_config.get('path')
        
        if db_path:
            logger.info(f"Creating backend for database: {db_name} at {db_path}")
            backend = AccessBackend(db_path)
            try:
                backend.connect()
                _services['backend'] = backend
            except Exception as e:
                logger.error(f"Failed to connect to backend {db_name}: {e}")
    
    return _services['backend']


def get_registry(app):
    """Get or create the schema registry."""
    global _services
    if _services['registry'] is None:
        backend = get_backend(app)
        if backend:
            logger.info("Initializing schema registry")
            config_path = Path(__file__).parent.parent.parent / 'config' / 'schema_overrides.json'
            registry = SchemaRegistry.from_config(str(config_path))
            registry.load(backend)
            _services['registry'] = registry
    
    return _services['registry']


def get_song_service(app):
    """Get or create the song service."""
    global _services
    if _services['song_service'] is None:
        backend = get_backend(app)
        registry = get_registry(app)
        if backend and registry:
            logger.info("Initializing SongService")
            _services['song_service'] = SongService(backend, registry)
    
    return _services['song_service']

def get_audit_service(app):
    """Get or create the audit service."""
    global _services
    if _services['audit_service'] is None:
        song_service = get_song_service(app)
        vfs_service = get_vfs_service(app)
        media_service = get_media_service(app)
        if song_service and vfs_service and media_service:
            logger.info("Initializing AuditService")
            config = app.config.get('CONNECTIONS', {})
            _services['audit_service'] = AuditService(song_service, vfs_service, media_service, config)
    return _services['audit_service']

def get_artist_service(app):
    """Get or create the ArtistService singleton."""
    if 'artist_service' not in _services:
        backend = get_backend(app)
        registry = get_registry(app)
        if backend and registry:
            from src.services.artist_service import ArtistService
            _services['artist_service'] = ArtistService(backend, registry)
    return _services.get('artist_service')

def get_sync_service(app):
    """Get or create the sync service for offline changes."""
    global _services
    if _services['sync_service'] is None:
        queue_path = Path(app.root_path).parent.parent / 'config' / 'pending_sync.json'
        logger.info(f"Initializing SyncService with queue: {queue_path}")
        _services['sync_service'] = SyncService(str(queue_path))
    return _services['sync_service']

def get_snapshot_service(app):
    """Get or create the metadata snapshot service."""
    global _services
    if _services['snapshot_service'] is None:
        cache_path = Path(app.root_path).parent.parent / 'config' / 'metadata_snapshot.json'
        logger.info(f"Initializing SnapshotService with cache: {cache_path}")
        service = SnapshotService(str(cache_path))
        service.load_cache()
        _services['snapshot_service'] = service
    return _services['snapshot_service']


def get_vfs_service(app):
    """Get or create the virtual file system service."""
    global _services
    if _services['vfs_service'] is None:
        # Look for log files in root
        log_file = None
        for candidate in ['log.txt', 'log_flat.txt']:
            path = Path(app.root_path).parent.parent / candidate
            if path.exists():
                log_file = str(path)
                break
        
        logger.info(f"Initializing VfsService with log: {log_file}")
        _services['vfs_service'] = VfsService(log_file)
    
    return _services['vfs_service']

def get_media_service(app):
    """Get or create the media service."""
    global _services
    if _services['media_service'] is None:
        connections = app.config['CONNECTIONS']
        drive_map = connections.get('drive_map', {})
        base_path = connections.get('base_songs_path')
        
        vfs_service = get_vfs_service(app)
        snapshot_service = get_snapshot_service(app)
        
        logger.info("Initializing MediaService")
        _services['media_service'] = MediaService(drive_map, base_path, vfs_service, snapshot_service)
    
    return _services['media_service']


def reset_services():
    """Clear the service cache (e.g. when changing databases)."""
    global _services
    if _services['backend']:
        try:
            _services['backend'].disconnect()
        except:
            pass
    _services = {
        'backend': None,
        'registry': None,
        'song_service': None,
        'media_service': None,
        'vfs_service': None,
        'snapshot_service': None,
        'sync_service': None,
        'audit_service': None,
        'schema_settings': None,
        'export_service': None,
        'lookup_service': None
    }

def get_schema_settings(app):
    """Get or create the schema settings service."""
    global _services
    if _services['schema_settings'] is None:
        config_path = Path(app.root_path).parent.parent / 'config' / 'schema_settings.json'
        _services['schema_settings'] = SchemaSettingsService(str(config_path))
    return _services['schema_settings']


def get_export_service(app):
    """Get or create the export service."""
    global _services
    if _services['export_service'] is None:
        song_service = get_song_service(app)
        if song_service:
            _services['export_service'] = ExportService(song_service)
    return _services['export_service']


def get_lookup_service(app):
    """Get or create the generic lookup service."""
    global _services
    if _services['lookup_service'] is None:
        backend = get_backend(app)
        registry = get_registry(app)
        if backend and registry:
            logger.info("Initializing LookupService")
            _services['lookup_service'] = LookupService(backend, registry)
    return _services['lookup_service']


# Create app instance for running directly
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
