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

from __future__ import unicode_literals
from __future__ import print_function

import glob
from constants import *
from functions import *
from cotisation import Cotisation
from ooffice import *
from generation.facture_mensuelle import FactureModifications
from math import *


class DocumentAccueilModifications(object):
    def __init__(self, who, date):
        self.inscrit = who
        self.date = date
        self.email = None
        self.site = None
        self.metas = {}

    def GetMetas(self, dom):
        metas = dom.getElementsByTagName('meta:user-defined')
        for meta in metas:
            # print(meta.toprettyxml())
            name = meta.getAttribute('meta:name')
            try:
                value = meta.childNodes[0].wholeText
                if meta.getAttribute('meta:value-type') == 'float':
                    self.metas[name] = float(value)
                else:
                    self.metas[name] = value
            except:
                pass

    def GetCustomFields(self, inscrit, famille, inscription, cotisation):
        fields = []
        for key in self.metas:
            if key.lower().startswith("formule "):
                label = key[8:]
                try:
                    value = eval(self.metas[key])
                except Exception as e:
                    print("Exception formule:", label, self.metas[key], e)
                    continue
                if isinstance(value, tuple):
                    field = label, value[0], value[1]
                else:
                    field = label, value
                fields.append(field)
        return fields

    def GetFields(self):
        president = tresorier = directeur = ""
        bureau = Select(database.creche.bureaux, self.date)
        if bureau:
            president = bureau.president
            tresorier = bureau.tresorier
            directeur = bureau.directeur

        bareme_caf = Select(database.creche.baremes_caf, self.date)
        try:
            plancher_caf = "%.2f" % bareme_caf.plancher
            plafond_caf = "%.2f" % bareme_caf.plafond
        except:
            plancher_caf = "non rempli"
            plafond_caf = "non rempli"
            
        inscription = self.inscrit.get_inscription(self.date, preinscription=True)
        self.cotisation = Cotisation(self.inscrit, self.date)
        
        fields = GetCrecheFields(database.creche) + GetInscritFields(self.inscrit) + GetInscriptionFields(inscription) + GetCotisationFields(self.cotisation)
        fields += [('president', president),
                   ('tresorier', tresorier),
                   ('directeur', directeur),
                   ('plancher-caf', plancher_caf),
                   ('plafond-caf', plafond_caf),
                   ('semaines-type', inscription.duree_reference // 7),
                   ('date', '%.2d/%.2d/%d' % (self.date.day, self.date.month, self.date.year)),
                   ('permanences', self.GetPermanences(inscription)),
                   ('carence-maladie', database.creche.minimum_maladie),
                   ('IsPresentDuringTranche', self.IsPresentDuringTranche),
                   ]
        
        if database.creche.mode_facturation != FACTURATION_FORFAIT_MENSUEL:
            fields.append(('montant-heure-garde', self.cotisation.montant_heure_garde))
            
        if inscription.mode == MODE_FORFAIT_MENSUEL:
            fields.append(('forfait-heures-presence', self.cotisation.forfait_mensuel_heures))

        if self.cotisation.assiette_annuelle is not None:
            fields.append(('annee-revenu', self.cotisation.date_revenus.year))
            fields.append(('assiette-annuelle', self.cotisation.assiette_annuelle))
            fields.append(('assiette-mensuelle', self.cotisation.assiette_mensuelle))
            if self.cotisation.taux_effort is not None:
                fields.append(('taux-effort', self.cotisation.taux_effort))
                fields.append(('mode-taux-effort', self.cotisation.mode_taux_effort))
            
            for i, (parent, revenu, abattement) in enumerate(self.cotisation.revenus_parents):
                i += 1
                fields.append(('revenu-parent%d' % i, revenu))
                fields.append(('abattement-parent%d' % i, abattement))
            
            if database.creche.mode_facturation != FACTURATION_FORFAIT_10H:
                if database.creche.conges_inscription:
                    fields.append(('dates-conges-inscription', ", ".join([GetDateString(d) for d in self.cotisation.conges_inscription]) if self.cotisation.conges_inscription else "(aucune)"))
                    fields.append(('nombre-jours-conges-inscription', len(self.cotisation.conges_inscription)))
                    
                if database.creche.conges_inscription or database.creche.facturation_jours_feries == ABSENCES_DEDUITES_EN_JOURS:
                    fields.append(('heures-fermeture-creche', GetHeureString(self.cotisation.heures_fermeture_creche)))
                    fields.append(('heures-accueil-non-facture', GetHeureString(self.cotisation.heures_accueil_non_facture)))
                    heures_brut_periode = self.cotisation.heures_periode + self.cotisation.heures_fermeture_creche + self.cotisation.heures_accueil_non_facture
                    fields.append(('heures-brut-periode', GetHeureString(heures_brut_periode)))
                    if self.cotisation.heures_semaine > 0:
                        fields.append(('semaines-brut-periode', "%.2f" % (heures_brut_periode / self.cotisation.heures_semaine)))
                    else:
                        fields.append(('semaines-brut-periode', "0"))

        dates_conges_creche = []
        for debut, fin in database.creche.liste_conges:
            if inscription.debut < fin and (not inscription.fin or inscription.fin > debut):
                if debut == fin:
                    dates_conges_creche.append(GetDateString(debut))
                else:
                    dates_conges_creche.append(GetDateString(debut) + ' - ' + GetDateString(fin))
        fields.append(('dates-conges-creche', ", ".join(dates_conges_creche)))
        
        for jour in range(inscription.duree_reference):
            jour_reference = inscription.get_day_from_index(jour)
            debut, fin = jour_reference.GetPlageHoraire()
            fields.append(('heure-debut[%d]' % jour, GetHeureString(float(debut) / 12 if debut else None)))
            fields.append(('heure-fin[%d]' % jour, GetHeureString(float(fin) / 12 if fin else None)))
            fields.append(('heures-jour[%d]' % jour, GetHeureString(jour_reference.get_duration())))

        for key in database.creche.activites:
            print("TODO tri par activite")
            fields.append(('liste-activites[%d]' % key, inscription.GetListeActivites()))

        fields += self.GetCustomFields(self.inscrit, self.inscrit.famille, inscription, self.cotisation)

        # print(fields)
        return fields

    def IsPresentDuringTranche(self, weekday, debut, fin):
        journee = self.inscrit.get_inscription(self.date).reference[weekday]
        if IsPresentDuringTranche(journee, debut, fin):
            return "X"
        else:
            return ""
    
    def GetPermanences(self, inscription):
        jours = inscription.get_days_per_week()
        heures = inscription.get_duration_per_week()
        if heures >= 11:
            result = 8
        elif heures >= 8:
            result = 6
        else:
            result = 4
        if inscription.inscrit.famille.GetEnfantsCount(inscription.debut)[1]:
            return 2 + result
        else:
            return result        


class OdtDocumentAccueilModifications(DocumentAccueilModifications):
    def __init__(self, who, date):
        DocumentAccueilModifications.__init__(self, who, date)
        self.inscription = who.get_inscription(date, preinscription=True)
        self.multi = False

    def execute(self, filename, dom):
        fields = self.GetFields()
        if filename == 'meta.xml':
            self.GetMetas(dom)
        if filename != 'content.xml':
            ReplaceTextFields(dom, fields)
            return None
        
        doc = dom.getElementsByTagName("office:text")[0]
        # print(doc.toprettyxml())

        for section in doc.getElementsByTagName("text:section"):
            section_name = section.getAttribute("text:name")
            index = ["parent1", "parent2"].index(section_name)
            if index >= 0 and self.inscrit.famille.parents[index] is None:
                doc.removeChild(section)

        for table in doc.getElementsByTagName("table:table"):
            table_name = table.getAttribute("table:name")
            if table_name in ("Tableau3", "Horaires"):
                rows = table.getElementsByTagName("table:table-row")
                for semaine in range(1, self.inscription.duree_reference // 7):
                    for row in rows[1:-1]:
                        clone = row.cloneNode(1)
                        for textNode in clone.getElementsByTagName("text:p"):
                            for child in textNode.childNodes:
                                text = child.wholeText
                                for i in range(7):
                                    text = text.replace("[%d]" % i, "[%d]" % (i + semaine * 7))
                                child.replaceWholeText(text)
                        table.insertBefore(clone, rows[-1])
                # print(table.toprettyxml())
            elif table_name == "Echeancier":
                rows = table.getElementsByTagName("table:table-row")
                template = rows[1]
                # print(template.toprettyxml())
                for date, valeur in self.cotisation.get_echeances():
                    clone = template.cloneNode(1)
                    table.insertBefore(clone, template)
                    fields_echeance = [
                        ("date-echeance", date),
                        ("valeur-echeance", valeur, FIELD_EUROS)
                    ]
                    ReplaceTextFields(clone, fields_echeance)
                table.removeChild(template)
        
        # print(doc.toprettyxml())
        ReplaceTextFields(doc, fields)
        return {}


class DevisAccueilModifications(OdtDocumentAccueilModifications):
    title = "Devis"
    template = "Devis accueil.odt"

    def __init__(self, who, date):
        OdtDocumentAccueilModifications.__init__(self, who, date)
        self.default_output = "Devis accueil %s - %s.odt" % (GetPrenomNom(who), GetDateString(date, weekday=False))


class ContratAccueilModifications(OdtDocumentAccueilModifications):
    title = "Contrat d'accueil"
    template = 'Contrat accueil.odt'

    def __init__(self, who, date):
        OdtDocumentAccueilModifications.__init__(self, who, date)
        if self.inscription.mode == MODE_TEMPS_PARTIEL and IsTemplateFile("Contrat accueil temps partiel.odt"):
            self.template = "Contrat accueil temps partiel.odt"
        elif self.inscription.mode == MODE_FORFAIT_MENSUEL and IsTemplateFile("Contrat accueil forfait mensuel.odt"):
            self.template = "Contrat accueil forfait mensuel.odt"
        elif self.inscription.mode == MODE_HALTE_GARDERIE and IsTemplateFile("Contrat accueil halte garderie.odt"):
            self.template = "Contrat accueil halte garderie.odt"
        self.default_output = "Contrat accueil %s - %s.odt" % (GetPrenomNom(who), GetDateString(date, weekday=False))


class AvenantContratAccueilModifications(OdtDocumentAccueilModifications):
    title = "Avenant au contrat d'accueil"
    template = "Avenant contrat accueil.odt"

    def __init__(self, who, date):
        OdtDocumentAccueilModifications.__init__(self, who, date)
        self.default_output = "Avenant contrat accueil %s - %s.odt" % (GetPrenomNom(who), GetDateString(date, weekday=False))


class FraisGardeModifications(DocumentAccueilModifications):
    title = "Frais de garde"
    template = "Frais de garde.ods"

    def __init__(self, who, date):
        DocumentAccueilModifications.__init__(self, who, date)
        self.multi = False
        self.default_output = "Frais de garde %s - %s.odt" % (GetPrenomNom(who), GetDateString(date, weekday=False))
        
    def execute(self, filename, dom):
        if filename != 'content.xml':
            return None
        
        spreadsheet = dom.getElementsByTagName('office:spreadsheet').item(0)
        table = spreadsheet.getElementsByTagName("table:table").item(0)       
        lignes = table.getElementsByTagName("table:table-row")

        fields = self.GetFields()
        ReplaceFields(lignes, fields)

        if len(self.cotisation.revenus_parents) < 2:
            RemoveNodesContaining(lignes, "parent2")
        elif not self.cotisation.revenus_parents[1][2]:
            RemoveNodesContaining(lignes, "abattement-parent2")
        if len(self.cotisation.revenus_parents) < 1:
            RemoveNodesContaining(lignes, "parent1")
        elif not self.cotisation.revenus_parents[0][2]:
            RemoveNodesContaining(lignes, "abattement-parent1")
            
        if database.creche.mode_facturation == FACTURATION_FORFAIT_MENSUEL:
            RemoveNodesContaining(lignes, "assiette-annuelle")
            RemoveNodesContaining(lignes, "assiette-mensuelle")
            RemoveNodesContaining(lignes, "taux-effort")
            RemoveNodesContaining(lignes, "heures-mois")
            RemoveNodesContaining(lignes, "montant-heure-garde")

        return {}


class DossierInscriptionModifications(DocumentAccueilModifications):
    title = "Dossier d'inscription"
    template = ""

    def __init__(self, who, date):
        DocumentAccueilModifications.__init__(self, who, date)
        self.multi = False
        self.default_output = ""
        self.email_to = list(set([parent.email for parent in who.famille.parents if parent and parent.email]))
        self.email_subject = "Dossier d'inscription pour %s" % GetPrenomNom(who)
        self.introduction_filename = "Dossier inscription.txt"

    def get_attachments(self):
        return glob.glob("templates/Dossier inscription/*.pdf")

    def GetIntroductionFields(self):
        fields = self.GetFields()
        for i, field in enumerate(fields):
            if len(field) > 2 and field[2] == FIELD_EUROS:
                fields[i] = (field[0], "%.2f" % field[1])
        return fields


class PremiereFactureModifications(DocumentAccueilModifications):
    title = "Première facture"
    template = ""

    def __init__(self, who, date):
        DocumentAccueilModifications.__init__(self, who, date)
        self.multi = False
        self.default_output = ""
        self.email_to = list(set([parent.email for parent in who.famille.parents if parent and parent.email]))
        self.email_subject = "Contrat d'accueil et première facture pour %s" % GetPrenomNom(who)
        self.introduction_filename = "Premiere facture.txt"
        self.contrat_accueil = ContratAccueilModifications(who, date)
        GenerateDocument(self.contrat_accueil, filename=self.contrat_accueil.default_output)
        inscription = who.get_inscription(date, preinscription=True)
        if inscription.preinscription:
            inscription.preinscription = False
            preinscription_changed = True
        self.facture = FactureModifications([who], date)
        GenerateDocument(self.facture, filename=self.facture.default_output)
        if preinscription_changed:
            inscription.preinscription = True

    def get_attachments(self):
        return [self.contrat_accueil.default_output, self.facture.default_output]

    def GetIntroductionFields(self):
        fields = self.GetFields()
        if self.facture.last_facture:
            fields.append(("total-premiere-facture", "%.2f" % self.facture.last_facture.total))
        for i, field in enumerate(fields):
            if len(field) > 2 and field[2] == FIELD_EUROS:
                fields[i] = (field[0], "%.2f" % field[1])
        return fields


if __name__ == '__main__':
    import random
    from document_dialog import StartLibreOffice
    database.init("databases/opagaio.db")
    database.load()
    inscrit = database.creche.GetInscrit(44)
    for modifications_class in (ContratAccueilModifications, DevisAccueilModifications, FraisGardeModifications):
        modifications = modifications_class(inscrit, datetime.date(2017, 9, 1))
        filename = "./test-%f.odt" % random.random()
        errors = GenerateOODocument(modifications, filename=filename, gauge=None)
    StartLibreOffice(filename)
