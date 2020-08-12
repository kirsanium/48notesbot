class DbService:
    def get_notes(self):
        pass

    def add_note(self):
        pass

    def delete_note(self, id):
        pass

    def create_notes_table(self):
        pass

class PostgresSettings:
    def __init__(self, dbname, user, password="", port="5432"):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.port=port
        self.conn_string = f"dbname={dbname} user={user} password={password} port={port}"

import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor

from note import Note
import logging
logger = logging.getLogger(__name__)

class PostgresService:
    def __init__(self, pg_settings):
        self.connection = psycopg2.connect(pg_settings.conn_string)
        self.notes_table_name = 'notes'
        self.notes_table_sql_id = sql.Identifier(self.notes_table_name)
        if not self.table_exists(self.notes_table_name):
            self.create_notes_table()

    def get_notes(self):
        logger.info('get notes')
        with self.connection.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute(sql.SQL("SELECT * from {}").format(self.notes_table_sql_id))
            for note in cursor:
                yield Note(id=note[0], title=note[1], content=note[2])

    def get_note(self, id):
        logger.info(f'get note id=`{id}``')
        with self.connection.cursor() as cursor:
            cursor.execute(sql.SQL("SELECT * from {} where id = %s").format(self.notes_table_sql_id), (id, ))
            found = cursor.rowcount
            if found:
                note = cursor.fetchone()
                return Note(id=note[0], title=note[1], content=note[2])
            else:
                return None

    def add_note(self, note):
        logger.info(f'add note note=`{note}``')
        with self.connection.cursor() as cursor:
            cursor.execute(sql.SQL("INSERT INTO {}(title, content) values (%s, %s)").format(self.notes_table_sql_id),
             (note.title, note.content))
            self.connection.commit()

    def delete_note(self, id):
        logger.info(f'delete note id=`{id}``')
        with self.connection.cursor() as cursor:
            cursor.execute(sql.SQL("DELETE FROM {} WHERE id = %s").format(self.notes_table_sql_id), (id, ))
            deleted = cursor.rowcount
            self.connection.commit() 
            return deleted      

    def create_notes_table(self):
        logger.info('create notes table')
        with self.connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE TABLE {} (id SERIAL PRIMARY KEY, " +
                "title VARCHAR(64), content VARCHAR(4096))").format(self.notes_table_sql_id))
            self.connection.commit()

    def table_exists(self, table_name):
        logger.info('table exists')
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT EXISTS (" +
                            "SELECT FROM pg_catalog.pg_class c " +
                            "JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace " +
                            "WHERE c.relname = %s" + 
                            "AND c.relkind = 'r' " +
                            ")", (table_name, ))
            exists = cursor.fetchone()[0]
        return exists 

    def fix_notes_id(self):
        logger.info('fix notes id')
        with self.connection.cursor() as cursor:
            cursor.execute("SET @count := 0")
            cursor.execute("UPDATE notes SET notes.id = @count:= @count + 1")
            self.connection.commit()          

    def __del__(self):
        self.connection.close() 