"""
DATABASE MODULE
===============

This module handles all database connections and operations.

KEY CONCEPT: Connection Pooling
-------------------------------
When multiple requests come in, they all need database connections.
Instead of creating a new connection for each request (slow!), we use
a "connection pool" - a group of pre-made connections that get reused.

For LangGraph's checkpointer, we use a separate connection pool because:
1. It needs to manage transaction state independently
2. It uses PostgreSQL's "pipeline mode" for efficiency
3. Sharing connections between the app and checkpointer causes conflicts
"""

import psycopg
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv
import os
import glob
from typing import LiteralString, Optional, Union, Sequence, Mapping, Any, Iterable
from langgraph.checkpoint.postgres import PostgresSaver

load_dotenv()

Params = Union[Sequence[Any], Mapping[str, Any]]


class Database:
    """
    Database class that manages connections for:
    1. Regular app queries (users, orders, etc.)
    2. LangGraph checkpointer (separate pool to avoid conflicts)
    """

    def __init__(self):
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL not found")

        self.database_url = DATABASE_URL

        # Connection for regular app queries
        self.connection = psycopg.connect(DATABASE_URL)

        # Create a separate connection pool for the checkpointer
        # This prevents the "failed to enter pipeline mode" error
        self.checkpointer_pool = ConnectionPool(
            DATABASE_URL, min_size=1, max_size=5, open=True
        )

        # Create checkpointer with the pool (not a single connection)
        self.checkpointer = PostgresSaver(self.checkpointer_pool)

    def setup_checkpointer(self):
        """
        Set up the checkpointer tables in the database.
        This creates the tables LangGraph needs to store conversation state.
        """
        self.checkpointer.setup()
        print("INFO: Database checkpointer initialized")

    def push(self):
        """
        Run database migrations.
        Migrations are SQL files that update the database schema.
        """
        migrations_path = "./migrations/*.sql"
        migration_files = sorted(glob.glob(migrations_path))

        if not migration_files:
            print("No migration files found")
            return

        cursor = self.connection.cursor()
        try:
            try:
                cursor.execute(
                    "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1"
                )
                result = cursor.fetchone()
                current_version = result[0] if result else "v0.0.0"
            except psycopg.errors.UndefinedTable:
                current_version = "v0.0.0"
                self.connection.rollback()

            def parse_version(version_str: str) -> tuple[int, int, int]:
                parts = version_str.lstrip("v").split(".")
                return (int(parts[0]), int(parts[1]), int(parts[2]))

            current_v = parse_version(current_version)

            for file_path in migration_files:
                filename = os.path.basename(file_path)
                file_version = filename.replace("migration-", "").replace(".sql", "")
                file_v = parse_version(file_version)

                if file_v > current_v:
                    print(f"Executing migration: {file_path}")
                    with open(file_path, "r") as f:
                        sql = f.read()
                        cursor.execute(sql.encode("utf-8"))

                    cursor.execute(
                        "INSERT INTO schema_version (version) VALUES (%s)",
                        (file_version,),
                    )
                    self.connection.commit()
                    current_v = file_v

            print("Migrations executed successfully")
        except Exception as e:
            self.connection.rollback()
            print(f"Error executing migrations: {e}")
            raise
        finally:
            cursor.close()

    def close(self):
        """Close all database connections."""
        self.connection.close()
        self.checkpointer_pool.close()

    def execute(self, query: LiteralString, params: Optional[Params] = None):
        """Execute a SQL query and return results."""
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            self.connection.commit()
            try:
                return cursor.fetchall()
            except psycopg.ProgrammingError:
                return []
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()

    def execute_many(
        self, query: LiteralString, params_seq: Iterable[Params]
    ) -> list[tuple]:
        """Execute a SQL query with multiple parameter sets."""
        cursor = self.connection.cursor()
        try:
            cursor.executemany(query, params_seq, returning=True)
            self.connection.commit()
            results: list[tuple] = []
            for result_cursor in cursor.results():
                results.append(*result_cursor.fetchall())
            return results
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()


# Create a single instance of Database
# This is called a "singleton pattern" - there's only one db object
db = Database()
