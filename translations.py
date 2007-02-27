##    This file is part of Gertrude.
##
##    Gertrude is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 2 of the License, or
##    (at your option) any later version.
##
##    Gertrude is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with Gertrude; if not, write to the Free Software
##    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

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
        version = 0

    print version, '=>', VERSION

    if version < 1:
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

    if version < 2:
        cur.execute("ALTER TABLE CRECHE ADD server_url VARCHAR;")
        
    if version < VERSION:
        try:
            cur.execute("DELETE FROM DATA WHERE key=?", ("VERSION", ))
        except sqlite3.OperationalError:
            pass

        cur.execute("INSERT INTO DATA (key, value) VALUES (?, ?)", ("VERSION", VERSION))

        connection.commit()
