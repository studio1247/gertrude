# -*- coding: utf-8 -*-

##    This file is part of Gertrude.
##
##    Gertrude is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 3 of the License, or
##    (at your option) any later version.
##
##    Gertrude is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with Gertrude; if not, see <http://www.gnu.org/licenses/>.

import os, datetime
try:
    import sqlite3
except:
    from pysqlite2 import dbapi2 as sqlite3

database = "../gertrude.db"

con = sqlite3.connect(database)
cur = con.cursor()

formule_taux_horaire = []

def add_cell(condition, value):
    global formule_taux_horaire
    formule_taux_horaire.append((condition, value))

def et(cond1, cond2):
    if cond1 == "":
        return cond2
    else:
        return cond1 + " et " + cond2
    
def add_row(condition, row):
    add_cell(et(condition, "heures<20"), row[0])
    add_cell(et(condition, "heures<25"), row[1])
    add_cell(et(condition, "heures<30"), row[2])
    add_cell(et(condition, "heures<35"), row[3])
    add_cell(et(condition, "heures<40"), row[4])
    add_cell(condition, row[5])

def add_table(condition_enfants, seuils, max):
    add_row(et(condition_enfants, "revenus<%d" % seuils[0]), [max-1.0-0.25*i for i in range(6)])
    add_row(et(condition_enfants, "revenus<%d" % seuils[1]), [max-0.5-0.25*i for i in range(6)])
    add_row(condition_enfants, [max-0.25*i for i in range(6)])

add_table("enfants>3", (2879.0, 6398.0), 8.25)
add_table("enfants=3", (26043.0, 57873.0), 8.5)
add_table("enfants=2", (23164.0, 51475.0), 8.75)
add_table("", (20285.0, 45077.0), 9.0)

cur.execute('UPDATE creche SET formule_taux_horaire=?', (str(formule_taux_horaire),))
        
con.commit()
con.close()

print "Done"
