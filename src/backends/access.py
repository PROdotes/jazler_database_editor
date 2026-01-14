"""
MS Access Backend implementation.

Connects to MS Access databases (.mdb, .accdb) via pyodbc.
"""

import pyodbc
import logging
from typing import List, Dict, Any, Optional

from src.backends.base import Backend, ColumnInfo

logger = logging.getLogger(__name__)


class AccessBackend(Backend):
    """
    Backend for MS Access databases using pyodbc.
    
    Connection string format:
        Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=path/to/file.accdb
    
    For convenience, you can also pass just the file path and we'll build the string.
    """
    
    # System tables to exclude from get_tables()
    SYSTEM_TABLE_PREFIXES = ('MSys', 'USys', '~')
    
    def __init__(self, connection_string: str):
        """
        Initialize Access backend.
        
        Args:
            connection_string: Either a full ODBC connection string or just the file path
        """
        # If it looks like a file path, convert to connection string
        if connection_string.endswith(('.mdb', '.accdb')):
            connection_string = (
                f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};"
                f"DBQ={connection_string}"
            )
        super().__init__(connection_string)
    
    def connect(self) -> None:
        """Establish connection to the Access database."""
        if self._connection is None:
            logger.info(f"Connecting to Access database: {self.connection_string}")
            try:
                self._connection = pyodbc.connect(self.connection_string)
                # Set encoding for Croatian/special characters
                self._connection.setdecoding(pyodbc.SQL_CHAR, encoding='cp1250')
                self._connection.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-16le')
                if hasattr(pyodbc, 'SQL_WMETADATA'):
                    self._connection.setdecoding(pyodbc.SQL_WMETADATA, encoding='utf-16le')
                self._connection.setencoding(encoding='utf-8')
            except Exception as e:
                logger.error(f"Failed to connect to Access database: {e}")
                raise
    
    def disconnect(self) -> None:
        """Close the connection."""
        if self._connection is not None:
            logger.info("Disconnecting from Access database")
            self._connection.close()
            self._connection = None
    
    def is_connected(self) -> bool:
        """Check if backend is connected."""
        return self._connection is not None
    
    def _ensure_connected(self):
        """Ensure we have an active connection."""
        if not self.is_connected():
            self.connect()
    
    def _get_cursor(self):
        """Get a cursor, connecting if necessary."""
        self._ensure_connected()
        return self._connection.cursor()
    
    # ─────────────────────────────────────────────────────────────
    # Schema Discovery
    # ─────────────────────────────────────────────────────────────
    
    def get_tables(self) -> List[str]:
        """Return list of user table names."""
        cursor = self._get_cursor()
        try:
            tables = []
            for table in cursor.tables():
                # Filter out system tables
                if table.table_type == 'TABLE':
                    name = table.table_name
                    if not any(name.startswith(p) for p in self.SYSTEM_TABLE_PREFIXES):
                        tables.append(name)
            return sorted(tables)
        finally:
            cursor.close()
    
    def get_columns(self, table: str) -> List[ColumnInfo]:
        """Return column metadata for a table."""
        cursor = self._get_cursor()
        try:
            columns = []
            # Using SELECT TOP 0 to get column info without fetching data
            cursor.execute(f"SELECT * FROM [{table}] WHERE 1=0")
            for col in cursor.description:
                columns.append(ColumnInfo(
                    name=col[0],
                    type_name=self._type_code_to_name(col[1]),
                    nullable=col[6] if len(col) > 6 else True,
                    max_length=col[3] if len(col) > 3 else None,
                    precision=col[4] if len(col) > 4 else None,
                    scale=col[5] if len(col) > 5 else None
                ))
            return columns
        finally:
            cursor.close()
    
    def _type_code_to_name(self, type_code) -> str:
        """Convert pyodbc type code to readable name."""
        type_map = {
            str: 'TEXT',
            int: 'INTEGER',
            float: 'FLOAT',
            bool: 'BOOLEAN',
            bytes: 'BINARY',
        }
        return type_map.get(type_code, str(type_code))
    
    def get_primary_key(self, table: str) -> Optional[str]:
        """
        Return the primary key column name.
        
        Note: Access doesn't always expose PK info via ODBC. 
        We try statistics first, then fall back to common patterns.
        """
        cursor = self._get_cursor()
        try:
            # Try to get PK from statistics
            try:
                stats = list(cursor.statistics(table))
                for stat in stats:
                    if stat.type == 1:  # SQL_INDEX_UNIQUE
                        return stat.column_name
            except:
                pass
            
            # Fallback: look for common PK patterns
            columns = self.get_columns(table)
            pk_candidates = ['AUID', 'ID', 'Id', 'id', 'Index', 'PrimaryKey']
            for col in columns:
                if col.name in pk_candidates:
                    return col.name
            
            # Last resort: first column
            if columns:
                return columns[0].name
            
            return None
        finally:
            cursor.close()
    
    # ─────────────────────────────────────────────────────────────
    # Read Operations
    # ─────────────────────────────────────────────────────────────
    
    def fetch(
        self, 
        table: str, 
        columns: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Fetch records from a table."""
        cursor = self._get_cursor()
        try:
            # Build column list
            col_str = "*" if not columns else ", ".join(f"[{c}]" for c in columns)
            
            # Build query - Access doesn't support OFFSET, use TOP
            # For offset support, we'd need a subquery approach
            query = f"SELECT TOP {limit + offset} {col_str} FROM [{table}]"
            params = []
            
            # Add WHERE clause
            if filters:
                conditions = []
                for col, val in filters.items():
                    conditions.append(f"[{col}] = ?")
                    params.append(val)
                query += " WHERE " + " AND ".join(conditions)
            
            # Add ORDER BY
            if order_by:
                query += f" ORDER BY [{order_by}]"
            
            cursor.execute(query, params)
            
            # Get column names from cursor description
            col_names = [desc[0] for desc in cursor.description]
            
            # Fetch and skip offset rows
            rows = cursor.fetchall()
            if offset > 0:
                rows = rows[offset:]
            
            # Convert to list of dicts
            return [dict(zip(col_names, row)) for row in rows]
        finally:
            cursor.close()
    
    def fetch_one(
        self, 
        table: str, 
        primary_key_value: Any,
        primary_key_column: str = "id"
    ) -> Optional[Dict[str, Any]]:
        """Fetch a single record by primary key."""
        results = self.fetch(
            table, 
            filters={primary_key_column: primary_key_value},
            limit=1
        )
        return results[0] if results else None
    
    def count(
        self, 
        table: str, 
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count records in a table."""
        cursor = self._get_cursor()
        try:
            query = f"SELECT COUNT(*) FROM [{table}]"
            params = []
            
            if filters:
                conditions = []
                for col, val in filters.items():
                    conditions.append(f"[{col}] = ?")
                    params.append(val)
                query += " WHERE " + " AND ".join(conditions)
            
            cursor.execute(query, params)
            return cursor.fetchone()[0]
        finally:
            cursor.close()
    
    def search(
        self,
        table: str,
        column: str,
        value: str,
        match_type: str = "contains"
    ) -> List[Dict[str, Any]]:
        """Search for records matching a pattern."""
        cursor = self._get_cursor()
        try:
            # Build LIKE pattern based on match type
            if match_type == "equals":
                query = f"SELECT * FROM [{table}] WHERE [{column}] = ?"
                params = [value]
            elif match_type == "starts_with":
                query = f"SELECT * FROM [{table}] WHERE [{column}] LIKE ?"
                params = [f"{value}%"]
            elif match_type == "ends_with":
                query = f"SELECT * FROM [{table}] WHERE [{column}] LIKE ?"
                params = [f"%{value}"]
            elif match_type == "is_empty":
                # Check schema to decide if we look for 0 or ''
                # This is safer than generic checks that might crash Access (Text = 0)
                is_numeric = False
                try:
                    columns = self.get_columns(table)
                    for col in columns:
                        if col.name.lower() == column.lower():
                            if col.type_name in ('INTEGER', 'FLOAT', 'DOUBLE', 'REAL', 'NUMERIC', 'DECIMAL', 'BYTE', 'LONG', 'CURRENCY', 'COUNTER'):
                                is_numeric = True
                            break
                except Exception:
                    pass # Fallback to text check if schema fails
                
                if is_numeric:
                    # For numbers: NULL or 0
                    query = f"SELECT * FROM [{table}] WHERE ([{column}] IS NULL OR [{column}] = 0)"
                else:
                    # For text: NULL or Empty String
                    query = f"SELECT * FROM [{table}] WHERE ([{column}] IS NULL OR [{column}] = '')"
                params = []
            else:  # contains (default)
                query = f"SELECT * FROM [{table}] WHERE [{column}] LIKE ?"
                params = [f"%{value}%"]
            
            cursor.execute(query, params)
            col_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            return [dict(zip(col_names, row)) for row in rows]
        finally:
            cursor.close()
    
    # ─────────────────────────────────────────────────────────────
    # Write Operations
    # ─────────────────────────────────────────────────────────────
    
    def update(
        self, 
        table: str, 
        primary_key_value: Any,
        fields: Dict[str, Any],
        primary_key_column: str = "id"
    ) -> bool:
        """Update a record."""
        if not fields:
            return False
            
        cursor = self._get_cursor()
        try:
            # Build SET clause
            set_parts = [f"[{col}] = ?" for col in fields.keys()]
            values = list(fields.values())
            values.append(primary_key_value)
            
            query = f"UPDATE [{table}] SET {', '.join(set_parts)} WHERE [{primary_key_column}] = ?"
            
            cursor.execute(query, values)
            self._connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def insert(
        self,
        table: str,
        fields: Dict[str, Any]
    ) -> Any:
        """Insert a new record."""
        if not fields:
            return None
            
        cursor = self._get_cursor()
        try:
            columns = ", ".join(f"[{c}]" for c in fields.keys())
            placeholders = ", ".join("?" for _ in fields)
            values = list(fields.values())
            
            query = f"INSERT INTO [{table}] ({columns}) VALUES ({placeholders})"
            
            cursor.execute(query, values)
            self._connection.commit()
            
            # Try to get the inserted ID
            try:
                cursor.execute("SELECT @@IDENTITY")
                result = cursor.fetchone()
                return result[0] if result else None
            except:
                return None
        except Exception as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def delete(
        self,
        table: str,
        primary_key_value: Any,
        primary_key_column: str = "id"
    ) -> bool:
        """Delete a record."""
        cursor = self._get_cursor()
        try:
            query = f"DELETE FROM [{table}] WHERE [{primary_key_column}] = ?"
            cursor.execute(query, [primary_key_value])
            self._connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()
    
    # ─────────────────────────────────────────────────────────────
    # Utility
    # ─────────────────────────────────────────────────────────────
    
    def fetch_sql(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute raw SQL and return list of dicts."""
        cursor = self._get_cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if not cursor.description:
                # No results (e.g. UPDATE/INSERT)
                self._connection.commit()
                return []
                
            col_names = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(col_names, row)) for row in rows]
        finally:
            cursor.close()

    def execute_raw(self, query: str, params: Optional[tuple] = None) -> List[Any]:
        """Execute a raw SQL query."""
        cursor = self._get_cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # If it's a SELECT, return results
            if cursor.description:
                return cursor.fetchall()
            else:
                # For INSERT/UPDATE/DELETE, commit and return empty
                self._connection.commit()
                return []
        finally:
            cursor.close()
    
    def get_lookup_map(self, table: str, key_column: str, value_column: str) -> Dict[Any, str]:
        """
        Build a lookup dictionary from a table.
        
        Useful for genre/decade/tempo category mappings.
        
        Args:
            table: Name of the lookup table
            key_column: Column to use as dictionary key
            value_column: Column to use as dictionary value
            
        Returns:
            Dict mapping key -> value
        """
        records = self.fetch(table, columns=[key_column, value_column], limit=10000)
        return {r[key_column]: r[value_column] for r in records}
