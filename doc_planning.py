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

from ooffice import *


class Ligne(object):
    def __init__(self, inscription):
        self.inscription = inscription
        self.inscrit = inscription.inscrit
        self.label = GetPrenomNom(self.inscrit)


class PlanningModifications(object):
    def __init__(self, site, debut):
        self.multi = False
        self.template = 'Planning.ods'
        self.default_output = "Planning %s.ods" % str(debut)
        self.site = site
        self.debut = debut
        self.metas = {"Format": 1, "Periodicite": 11}
        self.email = None
        self.site = None

    def GetMetas(self, dom):
        metas = dom.getElementsByTagName('meta:user-defined')
        for meta in metas:
            # print meta.toprettyxml()
            name = meta.getAttribute('meta:name')
            value = meta.childNodes[0].wholeText
            if meta.getAttribute('meta:value-type') == 'float':
                self.metas[name] = float(value)
            else:
                self.metas[name] = value

    def execute(self, filename, dom):
        if filename == 'meta.xml':
            self.GetMetas(dom)
            return None
        elif filename != 'content.xml':
            return None
              
        date_fin = self.debut + datetime.timedelta(self.metas["Periodicite"])
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table")[0]
        lignes = table.getElementsByTagName("table:table-row")

        # Les titres des pages
        ReplaceFields(lignes, [('date-debut', self.debut),
                               ('date-fin', date_fin)])

        if self.metas["Format"] == 1:
            # Le format utilisé par Les petits potes (séparation adaptation / halte-garderie / mi-temps / plein-temps
            table.setAttribute('table:name', '%d %s %d - %d %s %d' % (self.debut.day, months[self.debut.month - 1], date_fin.year, date_fin.day, months[date_fin.month - 1], date_fin.year))

            # Les jours
            ligne = lignes.item(1)
            cellules = ligne.getElementsByTagName("table:table-cell")
            for semaine in range(2):
                for jour in range(5):
                    date = self.debut + datetime.timedelta(semaine * 7 + jour)
                    cellule = cellules.item(1 + semaine * 6 + jour)
                    ReplaceFields([cellule], [('date', date)])
    
            ligne_total = lignes.item(15)
    
            # # Les enfants en adaptation
            # indexes = []  # TODO getAdaptationIndexes(self.debut, date_fin)
            # indexes = GetTriParPrenomIndexes(indexes)
            # self.printPresences(template, indexes, 15)
            # nb_ad = max(2, len(indexes))
    
            # Les halte-garderie
            indexes = GetInscritsByMode(self.debut, date_fin, MODE_HALTE_GARDERIE, self.site)
            indexes = GetTriParPrenomIndexes(indexes)
            self.printPresences(table, indexes, 11)
            nb_hg = 1 + max(2, len(indexes)) if len(indexes) > 0 else 0
    
            # Les mi-temps
            indexes = GetInscritsByMode(self.debut, date_fin, MODE_4_5 | MODE_3_5, self.site)
            indexes = GetTriParPrenomIndexes(indexes)
            self.printPresences(table, indexes, 7)
            nb_45 = 1 + max(2, len(indexes)) if len(indexes) > 0 else 0
    
            # Les plein-temps
            indexes = GetInscritsByMode(self.debut, date_fin, MODE_5_5, self.site)
            indexes = GetTriParPrenomIndexes(indexes)
            self.printPresences(table, indexes, 3)
            nb_55 = 1 + max(2, len(indexes)) if len(indexes) > 0 else 0
    
            cellules = ligne_total.getElementsByTagName("table:table-cell")
            for i in range(cellules.length):
                cellule = cellules.item(i)
                if cellule.hasAttribute('table:formula'):
                    formule = cellule.getAttribute('table:formula')
                    formule = formule.replace('14', '%d' % (3 + nb_55 + nb_45 + nb_hg))
                    cellule.setAttribute('table:formula', formule)
        elif self.metas["Format"] == 2:
            # Le format utilisé par une garderie périscolaire (tri par professeur)
            inscriptions = GetInscriptions(self.debut, date_fin)
            tableau = {}  # par professeur
            for inscription in inscriptions:
                if inscription.professeur in tableau:
                    tableau[inscription.professeur].append(inscription)
                else:
                    tableau[inscription.professeur] = [inscription]

            def GetState(local_inscription, delta):
                state = local_inscription.inscrit.GetStateSimple(self.debut + datetime.timedelta(delta))
                if state <= 0:
                    return 0
                else:
                    return state & PRESENT

            template = table
            for professeur in tableau:
                table = template.cloneNode(1)
                table.setAttribute('table:name', GetPrenomNom(professeur))
                template.parentNode.insertBefore(table, template)
                ligne_template = GetRow(table, 10)
                for inscription in tableau[professeur]:
                    ligne = ligne_template.cloneNode(1)
                    fields = [('prenom', GetPrenom(inscription.inscrit)),
                              ('nom', GetNom(inscription.inscrit)),
                              ('professeur-prenom', GetPrenom(inscription.professeur)),
                              ('professeur-nom', GetNom(inscription.professeur))] 
                    for i, day in enumerate(days):
                        fields.append((day.lower(), GetState(inscription, i)))
                    ReplaceFields(ligne, fields)
                    table.insertBefore(ligne, ligne_template)
                table.removeChild(ligne_template)
            template.parentNode.removeChild(template)
        elif self.metas["Format"] == 3:
            # Mon petit bijou
            # lecture des couleurs
            couleurs = {}
            for i, inscrit in enumerate(creche.inscrits):
                line = lignes[5 + (i % 40)]
                couleurs[GetPrenomNom(inscrit)] = [GetCell(line, j).getAttribute("table:style-name") for j in range(1, 5)]
            for line in lignes[5:45]:
                table.removeChild(line)
            del lignes[5:45]

            date = self.debut
            fin = self.debut + datetime.timedelta(5)
            jour = 0
            while date < fin:
                template = lignes[4 + 3 * jour]
                lignes_presence = GetLines(date, creche.inscrits, presence=True, site=self.site)
                for i, presence in enumerate(lignes_presence):
                    if i == 0:
                        line = lignes[3 + 3 * jour]
                        GetCell(line, 0).setAttribute("table:number-rows-spanned", str(len(lignes_presence)))
                    else:
                        line = template.cloneNode(1)
                        table.insertBefore(line, template)
                    nom_ecrit = False
                    for c in range(24):  # 12h
                        cell = GetCell(line, c + 1)
                        if IsPresentDuringTranche(presence, (7.0 + c * 0.5) * 12, (7.0 + c * 0.5 + 0.5) * 12):
                            if not nom_ecrit:
                                cell.setAttribute("office:value-type", "string")
                                text_node = GetCell(line, 3).childNodes[0]
                                GetCell(line, 3).removeChild(text_node)
                                ReplaceTextFields(text_node, [("nom", GetPrenomNom(presence))])
                                cell.appendChild(text_node)
                                nom_ecrit = True
                            cell.setAttribute("table:style-name", couleurs[presence.label][2 + (c & 1)])
                        else:
                            cell.setAttribute("table:style-name", couleurs[presence.label][c & 1])
                table.removeChild(template)               
                date += datetime.timedelta(1)
                jour += 1                
        elif self.metas["Format"] == 4:
            # Garderie Ribambelle
            fin = self.debut + datetime.timedelta(5)
            lignes_entete = lignes[0:6]
            template = lignes[4]
            total_template = lignes[6]
            inscriptions = GetInscriptions(self.debut, fin)
            for index, inscription in enumerate(inscriptions):
                if index != 0 and index % 24 == 0:
                    for i, line in enumerate(lignes_entete):
                        clone = line.cloneNode(1)
                        table.insertBefore(clone, total_template)
                        if i == 4:
                            table.removeChild(template)
                            template = clone
                    
                inscrit = inscription.inscrit
                line = template.cloneNode(1)
                date = self.debut
                cell = 0
                tranches = [(creche.ouverture, 12), (14, creche.fermeture)]
                while date < fin:
                    journee = inscrit.GetJournee(date)
                    for t in range(2):
                        cell += 1
                        if journee and IsPresentDuringTranche(journee, tranches[t][0] * 12, tranches[t][1] * 12):
                            ReplaceFields(GetCell(line, cell), [('p', 1)])
                        else:
                            ReplaceFields(GetCell(line, cell), [('p', '')])
                    date += datetime.timedelta(1)    
                table.insertBefore(line, template)
                ReplaceTextFields(GetCell(line, 0), GetInscritFields(inscription.inscrit))

            table.removeChild(template)
            
            cellules = total_template.getElementsByTagName("table:table-cell")
            for i in range(cellules.length):
                cellule = cellules.item(i)
                if cellule.hasAttribute('table:formula'):
                    formule = cellule.getAttribute('table:formula')
                    formule = formule.replace('6', '%d' % (5 + len(inscriptions) + 5 * (len(inscriptions) / 24)))
                    cellule.setAttribute('table:formula', formule)
        elif self.metas["Format"] == 5:
            # Au petit Saturnin
            fin = self.debut + datetime.timedelta(5)
            lignes_entete = lignes[0:2]
            templates = lignes[2:4]
            total_template = lignes[5]

            # Les jours
            ligne = lignes.item(1)
            cellules = ligne.getElementsByTagName("table:table-cell")
            for jour in range(5):
                date = self.debut + datetime.timedelta(jour)
                cellule = cellules.item(2 + jour)
                ReplaceFields([cellule], [('date', date)])

            inscriptions = GetInscriptions(self.debut, fin)
            lines = [Ligne(inscription) for inscription in inscriptions]
            lines = GetEnfantsTriesParGroupe(lines)

            for index, ligne in enumerate(lines):
                # if index != 0 and index % 24 == 0:
                #     for i, row in enumerate(lignes_entete):
                #         clone = row.cloneNode(1)
                #         table.insertBefore(clone, total_template)
                #         if i == 4:
                #             table.removeChild(template)
                #             template = clone

                inscrit = ligne.inscrit
                inscription = ligne.inscription
                if inscription.groupe is None or len(templates) <= inscription.groupe.ordre:
                    line = templates[0].cloneNode(1)
                else:
                    line = templates[inscription.groupe.ordre].cloneNode(1)
                cell = 0
                tranches = [(creche.ouverture, 12), (14, creche.fermeture)]
                date = self.debut
                while date <= fin:
                    if date in inscrit.journees:
                        journee = inscrit.journees[date]
                    else:
                        journee = inscrit.GetJourneeReferenceCopy(date)
                    for t in range(2):
                        cell += 1
                        if journee and IsPresentDuringTranche(journee, tranches[t][0] * 12, tranches[t][1] * 12):
                            ReplaceFields(GetCell(line, cell), [('p', 1)])
                        else:
                            ReplaceFields(GetCell(line, cell), [('p', '')])
                    date += datetime.timedelta(1)
                table.insertBefore(line, templates[0])
                ReplaceTextFields(line, GetInscritFields(inscription.inscrit) + GetInscriptionFields(inscription))

            for template in templates:
                table.removeChild(template)

            IncrementFormulas(total_template, row=+len(lines), flags=FLAG_SUM_MAX)

        #print dom.toprettyxml()
        return None

    def printPresences(self, dom, indexes, ligne_depart):
        lignes = dom.getElementsByTagName("table:table-row")
        if len(indexes) == 0:
            dom.removeChild(lignes.item(ligne_depart + 2))
            dom.removeChild(lignes.item(ligne_depart + 1))
            dom.removeChild(lignes.item(ligne_depart))
            dom.removeChild(lignes.item(ligne_depart - 1))
            return
        nb_lignes = 3
        if len(indexes) > 3:
            for i in range(3, len(indexes)):
                dom.insertBefore(lignes.item(ligne_depart + 1).cloneNode(1), lignes.item(ligne_depart + 2))
            nb_lignes = len(indexes)
        elif len(indexes) < 3:
            dom.removeChild(lignes.item(ligne_depart + 1))
            nb_lignes = 2
        lignes = dom.getElementsByTagName("table:table-row")
        for i in range(nb_lignes):
            if i < len(indexes):
                inscrit = creche.inscrits[indexes[i]]
            else:
                inscrit = None
            ligne = lignes.item(ligne_depart + i)
            cellules = ligne.getElementsByTagName("table:table-cell")
            for semaine in range(2):
                # Les infos
                cellule = cellules.item(semaine * 17)
                ReplaceFields([cellule], GetInscritFields(inscrit))
                # Les présences
                for jour in range(5):
                    date = self.debut + datetime.timedelta(semaine * 7 + jour)
                    if inscrit:
                        if date in inscrit.journees:
                            journee = inscrit.journees[date]
                        else:
                            journee = inscrit.GetJourneeReferenceCopy(date)
                    for t in range(3):
                        cellule = cellules.item(1 + semaine * 17 + jour * 3 + t)
                        if inscrit and journee:
                            tranches = [(creche.ouverture, 12), (12, 14), (14, creche.fermeture)]
                            ReplaceFields([cellule], [('p', int(IsPresentDuringTranche(journee, tranches[t][0] * 12, tranches[t][1] * 12)))])
                        else:
                            ReplaceFields([cellule], [('p', '')])


class PlanningHoraireModifications(PlanningModifications):
    def __init__(self, site, debut):
        PlanningModifications.__init__(self, site, debut)
        self.template = 'Planning horaire.ods'
        self.default_output = "Planning horaire %s.ods" % str(debut)

    def execute(self, filename, dom):
        if filename == 'meta.xml':
            self.GetMetas(dom)
            return None
        elif filename != 'content.xml':
            return None

        date_fin = self.debut + datetime.timedelta(self.metas["Periodicite"])
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table")[0]
        lines = table.getElementsByTagName("table:table-row")
        templates = lines[18:20]

        # Les titres des pages
        ReplaceFields(lines, [('date-debut', self.debut),
                              ('date-fin', date_fin),
                              ('numero-semaine', self.debut.isocalendar()[1])])

        inscriptions = GetInscriptions(self.debut, date_fin)
        lignes = [Ligne(inscription) for inscription in inscriptions]
        lignes = GetEnfantsTriesParGroupe(lignes)

        for index, ligne in enumerate(lignes):
            # if index != 0 and index % 24 == 0:
            #     for i, row in enumerate(lignes_entete):
            #         clone = row.cloneNode(1)
            #         table.insertBefore(clone, total_template)
            #         if i == 4:
            #             table.removeChild(template)
            #             template = clone

            inscrit = ligne.inscrit
            inscription = ligne.inscription
            if inscription.groupe is None or len(templates) <= inscription.groupe.ordre:
                template = templates[0]
            else:
                template = templates[inscription.groupe.ordre]
            line = template.cloneNode(1)

            # Les infos
            ReplaceFields(line, GetInscritFields(inscrit) + GetInscriptionFields(inscription))

            # Les présences
            for jour in range(5):
                date = self.debut + datetime.timedelta(jour)
                journee = inscrit.GetJournee(date)
                fields = [("arrivee", journee.GetHeureArrivee()),
                          ("depart", journee.GetHeureDepart())]
                ReplaceFields(GetCell(line, 2 + 2 * jour), fields)
                ReplaceFields(GetCell(line, 3 + 2 * jour), fields)

            table.insertBefore(line, templates[0])

        for template in templates:
            table.removeChild(template)

        self.FillPermanences(lines)

    def FillPermanences(self, lines):
        for jour in range(5):
            liste = GetListePermanences(self.debut + datetime.timedelta(jour))
            for start, end, inscrit in liste:
                if start <= 12.5 * 12:
                    line = lines[3 + int(float(start) / 12 - 7.5)]
                elif start <= 17.75 * 12:
                    line = lines[10 + int(float(start) / 12 - 14.75)]
                else:
                    continue
                cell = GetCell(line, 7 + jour, multiple=True)
                cell.setAttribute("table:number-rows-spanned", str((end - start) / 12))
                ReplaceFields(cell, [("a", GetPrenom(inscrit)),
                                     ("b", GetPrenom(inscrit))])
        for line in lines[3:14]:
            ReplaceFields(line, [("a", ""),
                                 ("b", "")])
