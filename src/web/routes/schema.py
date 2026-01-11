"""
Schema routes - database structure and table exploration.
"""

import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from src.web.app import get_song_service, get_schema_settings

logger = logging.getLogger(__name__)
schema_bp = Blueprint('schema', __name__)

@schema_bp.route('/')
def index():
    """List all tables in the database."""
    service = get_song_service(current_app)
    settings = get_schema_settings(current_app)
    
    if not service:
        flash('Not connected to a database.', 'warning')
        return redirect(url_for('main.index'))
        
    # Get all table names from backend
    tables = []
    try:
        raw_tables = service.backend.get_tables()
        
        # Filter and mark tables based on settings
        tables = []
        for name in raw_tables:
            is_hidden = settings.is_table_hidden(name)
            if not is_hidden or settings.show_hidden:
                tables.append({
                    'name': name,
                    'is_hidden': is_hidden
                })
                
    except Exception as e:
        logger.error(f"Failed to get tables: {e}")
        flash(f"Error fetching schema: {e}", "error")
        
    return render_template('schema/index.html', 
                         tables=tables, 
                         show_hidden=settings.show_hidden)

@schema_bp.route('/<table>')
def view_table(table):
    """View columns and sample data for a table."""
    service = get_song_service(current_app)
    settings = get_schema_settings(current_app)
    
    if not service:
        return redirect(url_for('main.index'))
        
    try:
        # Get column definitions
        raw_columns = service.backend.get_columns(table)
        
        # Mark hidden columns
        columns = []
        visible_cols = []
        for col in raw_columns:
            is_hidden = settings.is_field_hidden(table, col.name)
            columns.append({
                'name': col.name,
                'type_name': col.type_name,
                'is_hidden': is_hidden
            })
            if not is_hidden:
                visible_cols.append(col.name)
        
        # Get primary key column
        pk_column = service.backend.get_primary_key(table)
        
        # Fetch first 10 rows for preview (only if at least one column is visible)
        rows = []
        if visible_cols:
            rows = service.backend.fetch(table, columns=visible_cols, limit=10)
        
        return render_template('schema/view.html', 
                             table=table, 
                             columns=columns, 
                             pk_column=pk_column,
                             rows=rows,
                             visible_cols=visible_cols)
    except Exception as e:
        logger.error(f"Error viewing table {table}: {e}")
        flash(f"Error: {e}", "error")
        return redirect(url_for('schema.index'))

@schema_bp.route('/toggle-show-hidden', methods=['POST'])
def toggle_show_hidden():
    settings = get_schema_settings(current_app)
    settings.toggle_show_hidden()
    return redirect(request.referrer or url_for('schema.index'))

@schema_bp.route('/toggle-table-hide/<table_name>', methods=['POST'])
def toggle_table_hide(table_name):
    settings = get_schema_settings(current_app)
    settings.toggle_table_visibility(table_name)
    return redirect(request.referrer or url_for('schema.index'))

@schema_bp.route('/toggle-field-hide/<table_name>/<field_name>', methods=['POST'])
def toggle_field_hide(table_name, field_name):
    settings = get_schema_settings(current_app)
    settings.toggle_field_visibility(table_name, field_name)
    return redirect(request.referrer or url_for('schema.view_table', table=table_name))
