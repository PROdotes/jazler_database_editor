"""
Query command - search database records.

Usage:
    python -m src.cli query --field artist --value "Beatles"
    python -m src.cli query -f title -v "Love" --match contains
    python -m src.cli query -f artist -v "Queen" --limit 10
"""

import json
from pathlib import Path
from src.cli.probe import load_connections_config, get_backend_for_args


def query_command(args):
    """Execute the query command."""
    from src.core.schema import SchemaRegistry
    from src.services.song_service import SongService
    
    print(f"🔍 Searching: {args.field} {args.match} '{args.value}'")
    print("=" * 60)
    
    # Get backend
    backend = get_backend_for_args(args)
    if not backend:
        return
    
    # Load schema
    config_path = Path(__file__).parent.parent.parent / 'config' / 'schema_overrides.json'
    registry = SchemaRegistry.from_config(str(config_path))
    
    try:
        with backend:
            registry.load(backend)
            
            # Create service
            service = SongService(backend, registry)
            
            # Execute search
            limit = getattr(args, 'limit', 100) or 100
            results = service.search(
                args.field,
                args.value,
                args.match,
                limit=limit
            )
            
            print(f"📊 Found {results.count} results")
            
            if results.count == 0:
                print("No matching records.")
                return
            
            print("-" * 60)
            
            # Display results
            display_mode = getattr(args, 'output', 'table')
            
            if display_mode == 'json':
                show_results_json(results, service)
            elif display_mode == 'ids':
                show_results_ids(results)
            else:
                show_results_table(results, service, args.table)
                
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


def show_results_table(results, service, table_name: str):
    """Display results as a table."""
    # Determine columns to show based on table
    if table_name == "snDatabase":
        columns = [
            ('AUID', 'ID', 8),
            ('fldArtistName', 'Artist', 25),
            ('fldTitle', 'Title', 30),
            ('fldAlbum', 'Album', 20),
        ]
    else:
        # Generic: show first few columns
        if results.count > 0:
            first = results[0]
            keys = list(first.raw_data.keys())[:5]
            columns = [(k, k, 20) for k in keys]
        else:
            columns = []
    
    # Header
    header_parts = []
    for col_name, display, width in columns:
        header_parts.append(f"{display:<{width}}")
    print(" | ".join(header_parts))
    print("-" * (sum(w for _, _, w in columns) + 3 * (len(columns) - 1)))
    
    # Rows (limit display to 50)
    display_limit = min(results.count, 50)
    for i in range(display_limit):
        record = results[i]
        row_parts = []
        for col_name, display, width in columns:
            value = record.get(col_name, '')
            if value is None:
                value = ''
            value_str = str(value)[:width]
            row_parts.append(f"{value_str:<{width}}")
        print(" | ".join(row_parts))
    
    if results.count > display_limit:
        print(f"... and {results.count - display_limit} more")


def show_results_json(results, service):
    """Display results as JSON."""
    output = []
    for record in results:
        data = service.get_display_data(record)
        # Convert datetime objects to strings
        clean_data = {}
        for k, v in data.items():
            if hasattr(v, 'isoformat'):
                clean_data[k] = v.isoformat()
            else:
                clean_data[k] = v
        output.append(clean_data)
    
    print(json.dumps(output, indent=2, ensure_ascii=False))


def show_results_ids(results):
    """Display just the IDs."""
    ids = [str(record.primary_key) for record in results]
    print(", ".join(ids))
