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

    def push(self):
        migrations_path = "./migrations/*.sql"
        migration_files = sorted(glob.glob(migrations_path))
        
        if not migration_files:
            print("No migration files found")
            return
        
        cursor = self.connection.cursor()
        try:
            try:
                cursor.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
                result = cursor.fetchone()
                current_version = result[0] if result else "v0.0.0"
            except psycopg.errors.UndefinedTable:
                current_version = "v0.0.0"
                self.connection.rollback() # Ensure the connection in't poisoned
            
            def parse_version(version_str: str) -> tuple[int, int, int]:
                parts = version_str.lstrip('v').split('.')
                return (int(parts[0]), int(parts[1]), int(parts[2]))
            
            current_v = parse_version(current_version)
            
            for file_path in migration_files:
                filename = os.path.basename(file_path)
                file_version = filename.replace("migration-", "").replace(".sql", "")
                file_v = parse_version(file_version)
                
                if file_v > current_v:
                    print(f"Executing migration: {file_path}")
                    with open(file_path, 'r') as f:
                        sql = f.read()
                        cursor.execute(sql.encode('utf-8'))
                    
                    cursor.execute("INSERT INTO schema_version (version) VALUES (%s)", (file_version,))
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
        self.connection.close()

    def execute(self, query: LiteralString, params: Optional[Params] = None):
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

    def execute_many(self, query: LiteralString, params_seq: Iterable[Params]) -> list[tuple]:
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