"""
Probe command - explore database schema.

Usage:
    python -m src.cli probe --test              # Show all tables
    python -m src.cli probe --test -t snDatabase   # Show table details
    python -m src.cli probe --test -t snDatabase -s 5   # Show 5 sample rows
"""

import json
from pathlib import Path


def load_connections_config() -> dict:
    """Load the connections.json config file."""
    config_path = Path(__file__).parent.parent.parent / 'config' / 'connections.json'
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_backend_for_args(args):
    """Create the appropriate backend based on CLI args."""
    from src.backends.access import AccessBackend
    
    config = load_connections_config()
    databases = config.get('databases', {})
    
    if args.live:
        db_key = 'jazler_live'
    else:
        db_key = 'jazler_test'  # Default to test
    
    db_config = databases.get(db_key, {})
    db_path = db_config.get('path', '')
    
    if not db_path:
        print(f"❌ No path configured for '{db_key}' in config/connections.json")
        return None
    
    return AccessBackend(db_path)


def probe_command(args):
    """Execute the probe command."""
    from src.core.schema import SchemaRegistry
    
    print("🔍 Database Schema Probe")
    print("=" * 50)
    
    # Get backend
    backend = get_backend_for_args(args)
    if not backend:
        return
    
    db_type = "LIVE" if args.live else "TEST"
    print(f"📁 Database: {db_type}")
    
    # Load schema registry with overrides
    config_path = Path(__file__).parent.parent.parent / 'config' / 'schema_overrides.json'
    registry = SchemaRegistry.from_config(str(config_path))
    
    try:
        with backend:
            # Load schema
            registry.load(backend)
            
            if args.table:
                # Show specific table details
                show_table_details(backend, registry, args.table, args.sample)
            else:
                # Show all tables
                show_all_tables(registry)
                
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


def show_all_tables(registry):
    """Display list of all tables."""
    print("\n📋 Tables Found:")
    print("-" * 50)
    
    # Data tables
    data_tables = registry.get_data_tables()
    if data_tables:
        print("\n📊 Data Tables:")
        for table in sorted(data_tables, key=lambda t: t.name):
            col_count = len(table.get_visible_columns())
            pk = table.primary_key or "?"
            print(f"  • {table.name} ({col_count} columns, PK: {pk})")
    
    # Lookup tables
    lookup_tables = registry.get_lookup_tables()
    if lookup_tables:
        print("\n🔗 Lookup Tables:")
        for table in sorted(lookup_tables, key=lambda t: t.name):
            print(f"  • {table.name}")
    
    # Ignored tables
    all_tables = registry.get_tables(include_ignored=True)
    ignored = [t for t in all_tables if t.is_ignored]
    if ignored:
        print(f"\n⚪ Ignored: {len(ignored)} system tables")
    
    print("\n" + "=" * 50)
    print("Tip: Use `probe --test -t TABLE_NAME` for column details")


def show_table_details(backend, registry, table_name: str, sample_count: int):
    """Display detailed info about a specific table."""
    table = registry.get_table(table_name)
    
    if not table:
        print(f"❌ Table '{table_name}' not found")
        print("Available tables:", ", ".join(registry.get_table_names(include_ignored=True)))
        return
    
    print(f"\n📊 Table: {table.name}")
    if table.display_name:
        print(f"   Display Name: {table.display_name}")
    print(f"   Primary Key: {table.primary_key or 'Unknown'}")
    print(f"   Is Lookup: {'Yes' if table.is_lookup else 'No'}")
    
    # Record count
    try:
        count = backend.count(table_name)
        print(f"   Record Count: {count:,}")
    except:
        pass
    
    # Columns
    print(f"\n📝 Columns ({len(table.columns)}):")
    print("-" * 60)
    print(f"{'#':>3}  {'Column Name':<25} {'Type':<12} {'Display Name'}")
    print("-" * 60)
    
    for i, col in enumerate(table.columns):
        type_str = col.type_name
        if col.max_length:
            type_str += f"({col.max_length})"
        
        pk_marker = " 🔑" if col.is_primary_key else ""
        ignored_marker = " ⚪" if col.is_ignored else ""
        display = col.display_name or ""
        
        print(f"{i:>3}  {col.name:<25} {type_str:<12} {display}{pk_marker}{ignored_marker}")
    
    # Sample data
    if sample_count > 0:
        print(f"\n📄 Sample Data ({sample_count} rows):")
        print("-" * 60)
        
        try:
            # Get a few key columns for display
            visible_cols = table.visible_column_names[:6]  # Limit to 6 columns
            rows = backend.fetch(table_name, columns=visible_cols, limit=sample_count)
            
            if rows:
                # Header
                header = " | ".join(f"{c[:15]:<15}" for c in visible_cols)
                print(header)
                print("-" * len(header))
                
                # Rows
                for row in rows:
                    values = []
                    for col in visible_cols:
                        val = str(row.get(col, ''))[:15]
                        values.append(f"{val:<15}")
                    print(" | ".join(values))
            else:
                print("(no data)")
        except Exception as e:
            print(f"Error fetching sample: {e}")
