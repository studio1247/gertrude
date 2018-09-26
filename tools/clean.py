# -*- coding: utf-8 -*-

#    This file is part of Gertrude.
#
#    Gertrude is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    Gertrude is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Gertrude; if not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
from __future__ import unicode_literals

import sys
import codecs

sys.path.append('..')
sys.stdout = codecs.open("/tmp/gertrude.log", "a", "utf-8")

from database import Database


def clean(filename):
    database = Database(filename)
    database.load()

    # print("Liste des sites ...")
    # for site in database.creche.sites:
    #     print(site.idx, site.nom)
    #

    # print("Suppression des enfants les plus anciens ...")
    # for inscrit in database.creche.inscrits:
    #     delete = True
    #     for inscription in inscrit.inscriptions:
    #         if not inscription.preinscription and (not inscription.fin or inscription.fin.year > 2016):
    #             delete = False
    #             break
    #         if inscription.preinscription and inscription.debut.year > 2017:
    #             delete = False
    #             break
    #     if delete:
    #         print("Suppression de %s %s" % (inscrit.prenom, inscrit.nom))
    #         for inscription in inscrit.inscriptions:
    #             if inscription.preinscription:
    #                 print("  - Préinscription", inscription.debut, inscription.fin)
    #             else:
    #                 print("  - Inscription", inscription.debut, inscription.fin)
    #         database.creche.inscrits.remove(inscrit)
    #     database.commit()

    print("Suppression des enfants en fonction du site ...")
    for inscrit in database.creche.inscrits:
        delete = True
        for inscription in inscrit.inscriptions:
            if inscription.site.nom.startswith("Les ptits"):
                delete = False
                break
        if delete:
            print("Suppression de %s %s" % (inscrit.prenom, inscrit.nom))
            database.creche.inscrits.remove(inscrit)
        database.commit()

    # print("Liste des préinscriptions")
    # for inscrit in database.creche.inscrits:
    #     if len(inscrit.inscriptions) != 1:
    #         continue
    #     display = True
    #     for inscription in inscrit.inscriptions:
    #         if not inscription.preinscription:
    #             display = False
    #             break
    #     if display:
    #         inscription = inscrit.inscriptions[0]
    #         print("%d : Préinscription de %s %s, groupe %s, %s" % (inscrit.idx, inscrit.prenom, inscrit.nom, inscription.groupe.nom if inscription.groupe else "---", inscrit.notes))

    # database.delete_all_inscriptions()
    # database.delete_users()
    # database.delete_site(2)


if __name__ == '__main__':
    clean(sys.argv[1])
