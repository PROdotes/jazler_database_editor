"""
CLI entry point.

Usage:
    python -m src.cli probe [--test|--live]
    python -m src.cli query --field FIELD --value VALUE
    python -m src.cli audit --ghosts
"""

import argparse
import sys

from src.cli.probe import probe_command
from src.cli.query import query_command


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='db-toolkit',
        description='MS Database Sync Toolkit - Universal database operations'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # ─────────────────────────────────────────────────────────────
    # probe command
    # ─────────────────────────────────────────────────────────────
    probe_parser = subparsers.add_parser('probe', help='Explore database schema')
    probe_parser.add_argument('--test', action='store_true', 
                             help='Use test database')
    probe_parser.add_argument('--live', action='store_true', 
                             help='Use live database')
    probe_parser.add_argument('--table', '-t', type=str,
                             help='Show details for a specific table')
    probe_parser.add_argument('--sample', '-s', type=int, default=0,
                             help='Show N sample rows from table')
    
    # ─────────────────────────────────────────────────────────────
    # query command
    # ─────────────────────────────────────────────────────────────
    query_parser = subparsers.add_parser('query', help='Search database records')
    query_parser.add_argument('--test', action='store_true', 
                             help='Use test database')
    query_parser.add_argument('--live', action='store_true', 
                             help='Use live database')
    query_parser.add_argument('--table', '-t', type=str, default='snDatabase',
                             help='Table to search')
    query_parser.add_argument('--field', '-f', type=str, required=True,
                             help='Field to search')
    query_parser.add_argument('--value', '-v', type=str, required=True,
                             help='Value to search for')
    query_parser.add_argument('--match', '-m', type=str, default='contains',
                             choices=['contains', 'equals', 'starts_with'],
                             help='Match type')
    query_parser.add_argument('--limit', '-l', type=int, default=100,
                             help='Maximum results to return')
    query_parser.add_argument('--output', '-o', type=str, default='table',
                             choices=['table', 'json', 'ids'],
                             help='Output format')
    
    # Parse args
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    # Dispatch to command handlers
    if args.command == 'probe':
        probe_command(args)
    elif args.command == 'query':
        query_command(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
