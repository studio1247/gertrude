try:
    import sqlite3
except:
    from pysqlite2 import dbapi2 as sqlite3
from common import *
from sqlinterface import *

def Translate():
    cur = connection.cursor()
    try:
        cur.execute('SELECT value FROM DATA WHERE key="VERSION"')
        version = int(cur.fetchall()[0][0])
    except:
        version = None

    VERSION = 1
    if version == VERSION:
        print 'Pas de translations'
        return        
    
    if version is None:
        cur.execute("""
          CREATE TABLE DATA(
            key VARCHAR,
            value VARCHAR
          );""")
        
        cur.execute("""
          CREATE TABLE USERS(
            idx INTEGER PRIMARY KEY,
            login VARCHAR,
            password VARCHAR,
            profile INTEGER
          );""")

        cur.execute("INSERT INTO USERS (idx, login, password, profile) VALUES (NULL,?,?,?)", ("admin", "admin", PROFIL_ALL))
    
    try:
        cur.execute("DELETE FROM DATA WHERE key=VERSION")
    except sqlite3.OperationalError:
        pass
    cur.execute("INSERT INTO DATA (key, value) VALUES (?, ?)", ("VERSION", VERSION))

    connection.commit()
