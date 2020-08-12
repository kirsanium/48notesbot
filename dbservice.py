class DbService:
    def get_notes(self):
        pass

    def add_note(self):
        pass

    def delete_note(self, id):
        pass

    def create_notes_table(self):
        pass

NOTES_TABLE_NAME = 'notes'

import psycopg2
from psycopg2.extras import DictCursor

class PostgresService:
    def __init__(self, conn_string = 'dbname=postgres user=postgres'):
        self.connection = psycopg2.connect(conn_string)
        if not self.table_exists(NOTES_TABLE_NAME):
            self.create_notes_table()

    def get_notes(self):
        with self.connection.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT * from %s", (NOTES_TABLE_NAME))
            for note in cursor:
                yield note

    def add_note(self, note):
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO %s(title, content) values (%s, %s)", (NOTES_TABLE_NAME, note.title, note.content))
            self.connection.commit()

    def delete_note(self, id):
        with self.connection.cursor() as cursor:
            cursor.execute("DELETE FROM %s WHERE id = %s", (NOTES_TABLE_NAME, id, ))
            self.connection.commit()       

    def create_notes_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute("CREATE TABLE %s (id SERIAL PRIMARY KEY, " +
                "title VARCHAR(64), content VARCHAR(4096))", (NOTES_TABLE_NAME))
            self.connection.commit()

    def table_exists(self, table_name):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT EXISTS (" +
                            "SELECT FROM pg_catalog.pg_class c " +
                            "JOIN  pg_catalog.pg_namespace n ON n.oid = c.relnamespace " +
                            "WHERE c.relname = %s" + 
                            "AND    c.relkind = 'r' " +
                            ")", (table_name))
            exists = cursor.fetchone()[0]
        return exists           

    def __del__(self):
        self.connection.close() 
