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

database = "../tablette.db"

creche = u"Les choux à la crème"
noms = [ "Thiers", "de Mac Mahon", u"Grévy", "Carnot", "Casimir-Perier", "Faure", "Loubet", u"Fallières", u"Poincaré", u"Deschanel", "Millerand", "Doumergue", "Doumer", "Lebrun", "Auriol", "Coty", "de Gaulle", "Pompidou", "Giscard d'Estaing", "Mitterand", "Chirac", "Sarkozy", "Hollande", "Alanine", u"Cystéine", u"Phénylalanine", u"Glycine", "Histidine", "Isoleucine", "Lysine", "Leucine", u"Méthionine", "Asparagine", "Pyrrolysine", "Proline" ] * 50
ville = u"Lutèce"
adresse = u"Rue du faubourg Saint Honoré"
code_postal = 75000
email = "contact@gertrude-logiciel.org"
telephone = "06 12 34 56 78"
bureau = (u"Auguste Jullien", u"François Vatel", u"Cesare Frangipani", u"Pierre-François de la Varenne", u"Gaston Lenôtre", u"Pierre Hermé", u"Christophe Felder", u"Philippe Conticini")

con = sqlite3.connect(database)
cur = con.cursor()
cur.execute('SELECT idx FROM inscrits')
for i, entry in enumerate(cur.fetchall()):
    nom = noms[i]
    cur.execute('UPDATE inscrits SET nom=?, ville=?, code_postal=? WHERE idx=?', (nom, ville, code_postal, entry[0]))
    cur.execute('UPDATE parents SET nom=? WHERE inscrit=?', (nom, entry[0]))
    cur.execute('UPDATE parents SET telephone_domicile=?, telephone_travail=?, telephone_portable=?, email=? WHERE inscrit=?', (telephone, telephone, telephone, email, entry[0]))
cur.execute('UPDATE creche SET nom=?, ville=?, code_postal=?, adresse=?, telephone=?, email=?', (creche, ville, code_postal, adresse, telephone, email))
cur.execute('UPDATE bureaux SET president=?, vice_president=?, tresorier=?, secretaire=?, directeur=?, gerant=?, directeur_adjoint=?, comptable=?', bureau)
    
con.commit()
con.close()

print "Done"
        

