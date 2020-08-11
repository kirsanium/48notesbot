class DbService:
    def get_notes(self):
        pass

    def add_note(self):
        pass

    def delete_note(self, id):
        pass

    def create_notes_table(self):
        pass

import psycopg2
from psycopg2.extras import DictCursor

class PostgresService:
    def __init__(self, conn_string):
        self.connection = psycopg2.connect('dbname=postgres user=postgres')

    def get_notes(self):
        with self.connection.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT * from notes")
            for note in cursor:
                yield note

    def add_note(self, note):
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO notes(title, content) values (%s, %s)", (note.title, note.content))
            self.connection.commit()

    def delete_note(self, id):
        with self.connection.cursor() as cursor:
            cursor.execute("DELETE FROM notes WHERE id = %s", (id, ))
            self.connection.commit()

    def create_notes_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute("CREATE TABLE notes (id SERIAL PRIMARY KEY, " +
                "title VARCHAR(64), content VARCHAR(4096))")
            self.connection.commit()

    def __del__(self):
        self.connection.close() 
