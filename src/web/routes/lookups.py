from flask import Blueprint, render_template, abort, request, redirect, url_for, flash, current_app
from src.web.app import get_lookup_service, get_registry

lookups_bp = Blueprint('lookups', __name__)

@lookups_bp.route('/')
def index():
    """List all available lookup tables."""
    registry = get_registry(current_app)
    # Get all tables that are marked as is_lookup
    tables = registry.get_lookup_tables()
    return render_template('lookups/index.html', tables=tables)

@lookups_bp.route('/<table_name>')
def list_entries(table_name):
    """List entries for a specific lookup table."""
    registry = get_registry(current_app)
    service = get_lookup_service(current_app)
    
    table_def = registry.get_table(table_name)
    if not table_def or not table_def.is_lookup:
        abort(404, description="Lookup table not found")
    
    # Get config for display settings
    config = table_def.lookup_config or {}
    sort_col = config.get('sort_column', 'Name')
    display_col = config.get('display_column', 'Name')
    key_col = config.get('key_column', 'ID')
    grid_cols = config.get('grid_columns', [key_col, display_col])
    
    # Fetch records
    records = service.get_all(table_name, sort_field=sort_col)
    
    return render_template(
        'lookups/list.html',
        table=table_def,
        records=records,
        config=config,
        grid_cols=grid_cols
    )

@lookups_bp.route('/<table_name>/create', methods=['GET', 'POST'])
def create(table_name):
    """Create a new entry."""
    registry = get_registry(current_app)
    service = get_lookup_service(current_app)
    
    table_def = registry.get_table(table_name)
    if not table_def or not table_def.is_lookup:
        abort(404, description="Lookup table not found")
        
    if request.method == 'POST':
        # Extract form data
        data = {}
        for col in table_def.columns:
            if col.is_ignored: continue
            # Skip AutoIncrement PKs
            if col.is_primary_key and col.type_name == 'INTEGER': continue
            
            val = request.form.get(col.name)
            
            # Handle booleans
            if col.type_name == 'BOOLEAN':
                data[col.name] = True if val else False
            # Handle empty strings for numbers -> None
            elif val == '' and col.type_name in ('INTEGER', 'FLOAT'):
                data[col.name] = None
            else:
                data[col.name] = val
                
        # Validate (Basic)
        if hasattr(table_def, 'lookup_config') and table_def.lookup_config:
            display_col = table_def.lookup_config.get('display_column')
            if display_col and not data.get(display_col):
                flash(f"{display_col} is required.", "error")
                return render_template('lookups/edit.html', table=table_def, record=data, columns=table_def.columns, pk_field=table_def.primary_key)

        # Create
        new_id = service.create(table_name, data)
        if new_id:
            flash(f"Created {table_def.display_name or table_name} successfully.", "success")
            return redirect(url_for('lookups.list_entries', table_name=table_name))
        else:
            flash("Failed to create record. See logs.", "error")
            
    return render_template('lookups/edit.html', 
                          table=table_def, 
                          record=None, 
                          columns=table_def.columns,
                          pk_field=table_def.primary_key)

@lookups_bp.route('/<table_name>/<id>/edit', methods=['GET', 'POST'])
def edit(table_name, id):
    """Edit an entry."""
    registry = get_registry(current_app)
    service = get_lookup_service(current_app)
    
    table_def = registry.get_table(table_name)
    if not table_def or not table_def.is_lookup:
        abort(404, description="Lookup table not found")
        
    # Determine PK
    pk_val = id
    # If PK is integer, convert
    pk_col_def = next((c for c in table_def.columns if c.is_primary_key), None)
    if pk_col_def and pk_col_def.type_name == 'INTEGER':
        try:
            pk_val = int(id)
        except ValueError:
            abort(400, "Invalid ID format")

    record = service.get_by_id(table_name, pk_val)
    if not record:
        abort(404, "Record not found")

    if request.method == 'POST':
        data = {}
        for col in table_def.columns:
            if col.is_ignored: continue
            
            # For updates, we usually don't change the PK
            if col.is_primary_key: continue
            
            val = request.form.get(col.name)
            
            if col.type_name == 'BOOLEAN':
                data[col.name] = True if val else False
            elif val == '' and col.type_name in ('INTEGER', 'FLOAT'):
                data[col.name] = None
            else:
                data[col.name] = val

        if service.update(table_name, pk_val, data):
            flash("Saved changes.", "success")
            return redirect(url_for('lookups.list_entries', table_name=table_name))
        else:
            flash("Failed to update record.", "error")

    return render_template('lookups/edit.html', 
                          table=table_def, 
                          record=record, 
                          columns=table_def.columns,
                          pk_field=table_def.primary_key)

@lookups_bp.route('/<table_name>/<id>/delete', methods=['POST'])
def delete(table_name, id):
    """Delete an entry."""
    registry = get_registry(current_app)
    service = get_lookup_service(current_app)
    
    table_def = registry.get_table(table_name)
    if not table_def or not table_def.is_lookup:
        abort(404)

    # Determine PK
    pk_val = id
    pk_col_def = next((c for c in table_def.columns if c.is_primary_key), None)
    if pk_col_def and pk_col_def.type_name == 'INTEGER':
        try:
            pk_val = int(id)
        except ValueError:
            abort(400, "Invalid ID format")

    if service.delete(table_name, pk_val):
        flash("Record deleted.", "success")
    else:
        flash("Failed to delete record. It may be in use.", "error")
        
    return redirect(url_for('lookups.list_entries', table_name=table_name))
