"""
Abstract Backend interface for database operations.

All database backends must implement this interface to ensure
consistent behavior across different database types.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ColumnInfo:
    """Metadata about a database column."""
    name: str
    type_name: str
    nullable: bool = True
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    
    def __repr__(self):
        return f"ColumnInfo({self.name}: {self.type_name})"


class Backend(ABC):
    """
    Abstract interface for database backends.
    
    All methods should be stateless where possible. The connection
    is managed internally and should be opened/closed as needed.
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize the backend with a connection string.
        
        Args:
            connection_string: Database-specific connection string
        """
        self.connection_string = connection_string
        self._connection = None
    
    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the database."""
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Close the connection."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the backend is currently connected."""
        pass
    
    # ─────────────────────────────────────────────────────────────
    # Schema Discovery
    # ─────────────────────────────────────────────────────────────
    
    @abstractmethod
    def get_tables(self) -> List[str]:
        """
        Return list of user table names (excluding system tables).
        
        Returns:
            List of table names
        """
        pass
    
    @abstractmethod
    def get_columns(self, table: str) -> List[ColumnInfo]:
        """
        Return column metadata for a table.
        
        Args:
            table: Name of the table
            
        Returns:
            List of ColumnInfo objects describing each column
        """
        pass
    
    @abstractmethod
    def get_primary_key(self, table: str) -> Optional[str]:
        """
        Return the primary key column name for a table.
        
        Args:
            table: Name of the table
            
        Returns:
            Primary key column name, or None if not found
        """
        pass
    
    # ─────────────────────────────────────────────────────────────
    # Read Operations
    # ─────────────────────────────────────────────────────────────
    
    @abstractmethod
    def fetch(
        self, 
        table: str, 
        columns: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Fetch records from a table.
        
        Args:
            table: Name of the table
            columns: List of column names to fetch (None = all)
            filters: Dict of column->value for WHERE clause
            order_by: Column name to sort by
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of dicts, each representing a record
        """
        pass
    
    @abstractmethod
    def fetch_one(
        self, 
        table: str, 
        primary_key_value: Any,
        primary_key_column: str = "id"
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a single record by primary key.
        
        Args:
            table: Name of the table
            primary_key_value: Value of the primary key
            primary_key_column: Name of the primary key column
            
        Returns:
            Dict representing the record, or None if not found
        """
        pass
    
    @abstractmethod
    def count(
        self, 
        table: str, 
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count records in a table.
        
        Args:
            table: Name of the table
            filters: Optional dict of column->value for WHERE clause
            
        Returns:
            Number of matching records
        """
        pass
    
    @abstractmethod
    def search(
        self,
        table: str,
        column: str,
        value: str,
        match_type: str = "contains"
    ) -> List[Dict[str, Any]]:
        """
        Search for records matching a pattern.
        
        Args:
            table: Name of the table
            column: Column to search in
            value: Value to search for
            match_type: "contains", "equals", "starts_with", "ends_with"
            
        Returns:
            List of matching records
        """
        pass
    
    # ─────────────────────────────────────────────────────────────
    # Write Operations
    # ─────────────────────────────────────────────────────────────
    
    @abstractmethod
    def update(
        self, 
        table: str, 
        primary_key_value: Any,
        fields: Dict[str, Any],
        primary_key_column: str = "id"
    ) -> bool:
        """
        Update a record.
        
        Args:
            table: Name of the table
            primary_key_value: Value of the primary key
            fields: Dict of column->new_value to update
            primary_key_column: Name of the primary key column
            
        Returns:
            True if update was successful
        """
        pass
    
    @abstractmethod
    def insert(
        self,
        table: str,
        fields: Dict[str, Any]
    ) -> Any:
        """
        Insert a new record.
        
        Args:
            table: Name of the table
            fields: Dict of column->value for the new record
            
        Returns:
            The primary key of the inserted record, or None
        """
        pass
    
    @abstractmethod
    def delete(
        self,
        table: str,
        primary_key_value: Any,
        primary_key_column: str = "id"
    ) -> bool:
        """
        Delete a record.
        
        Args:
            table: Name of the table
            primary_key_value: Value of the primary key
            primary_key_column: Name of the primary key column
            
        Returns:
            True if deletion was successful
        """
        pass
    
    # ─────────────────────────────────────────────────────────────
    # Utility
    # ─────────────────────────────────────────────────────────────
    
    @abstractmethod
    def execute_raw(self, query: str, params: Optional[tuple] = None) -> List[Any]:
        """
        Execute a raw SQL query.
        
        Args:
            query: SQL query string
            params: Optional tuple of parameters for parameterized query
            
        Returns:
            Query results as list of tuples
        """
        pass
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
