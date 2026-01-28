import psycopg
from dotenv import load_dotenv
import os
import glob
from typing import LiteralString, Optional, Union, Sequence, Mapping, Any, Iterable

load_dotenv()

Params = Union[Sequence[Any], Mapping[str, Any]]

class Database:
    
    def __init__(self):
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL not found")
        
        self.connection = psycopg.connect(DATABASE_URL)

    def push(self, all: bool = False):
        migrations_path = "./migrations/*.sql"
        migration_files = sorted(glob.glob(migrations_path))
        
        if not migration_files:
            print("No migration files found")
            return
        
        files_to_execute = migration_files if all else [migration_files[-1]]
        
        cursor = self.connection.cursor()
        try:
            for file_path in files_to_execute:
                print(f"Executing migration: {file_path}")
                with open(file_path, 'r') as f:
                    sql = f.read()
                    cursor.execute(sql.encode('utf-8'))
                self.connection.commit()
            print("Migrations executed successfully")
        except Exception as e:
            self.connection.rollback()
            print(f"Error executing migrations: {e}")
            raise
        finally:
            cursor.close()

    def close(self):
        self.connection.close()

    def execute(self, query: LiteralString, params: Optional[Params] = None):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()

    def execute_many(self, query: LiteralString, params_seq: Iterable[Params]) -> list[tuple]:
        cursor = self.connection.cursor()
        try:
            cursor.executemany(query, params_seq, returning=True)
            results: list[tuple] = []
            for result_cursor in cursor.results():
                results.append(*result_cursor.fetchall())

            return results
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            cursor.close()