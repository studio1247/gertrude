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
from __future__ import division

from controls import *
import wx
from planning import PlanningWidget, BasePlanningLine, BaseWxPythonLine
from database import *

modes_facturation = [("Forfait 10h / jour", FACTURATION_FORFAIT_10H),
                     ("PSU", FACTURATION_PSU),
                     ("PSU avec taux d'effort personnalisés", FACTURATION_PSU_TAUX_PERSONNALISES),
                     ("PAJE (taux horaire spécifique)", FACTURATION_PAJE),
                     ("PAJE (taux horaire spécifique) avec forfait 10h / jour", FACTURATION_PAJE_10H),
                     ("Horaires réels", FACTURATION_HORAIRES_REELS),
                     ("Facturation personnalisée (forfait mensuel)", FACTURATION_FORFAIT_MENSUEL),
                     ]

modes_mensualisation = [("Avec mensualisation (sur 12 mois). Uniquement disponible si jours fériés non déduits", REPARTITION_MENSUALISATION_12MOIS),
                        ("Avec mensualisation (sur la période du contrat)", REPARTITION_MENSUALISATION_CONTRAT),
                        ("Sans mensualisation", REPARTITION_SANS_MENSUALISATION)
                        ]

modes_prorata = [
    ("Pas de prorata", PRORATA_NONE),
    ("Prorata sur le nombre de jours d'ouverture", PRORATA_JOURS_OUVRES),
    ("Prorata sur le nombre de jours du mois", PRORATA_MOIS_COMPLET)
]

modes_facturation_absences = [("En semaines (nombre de semaines entré à l'inscription)", ABSENCES_DEDUITES_EN_SEMAINES),
                              ("En jours (décompte précis des jours de présence sur l'ensemble du contrat)", ABSENCES_DEDUITES_EN_JOURS),
                              ("Sans limite", ABSENCES_DEDUITES_SANS_LIMITE),
                              ]

modes_arrondi_mensualisation = [("Pas d'arrondi", SANS_ARRONDI),
                                ("Arrondi à l'heure la plus proche", ARRONDI_HEURE_PLUS_PROCHE),
                                ]

modes_arrondi_horaires_enfants = [("Pas d'arrondi", SANS_ARRONDI),
                                  ("Arrondi à l'heure", ARRONDI_HEURE),
                                  ("Arrondi à l'heure avec marge d'1/2heure", ARRONDI_HEURE_MARGE_DEMI_HEURE),
                                  ("Arrondi à la demi heure", ARRONDI_DEMI_HEURE),
                                  ("Arrondi des heures d'arrivée et de départ", ARRONDI_HEURE_ARRIVEE_DEPART)
                                  ]

modes_arrondi_factures_enfants = [("Pas d'arrondi", SANS_ARRONDI),
                                  ("Arrondi à l'heure", ARRONDI_HEURE),
                                  ("Arrondi à la demi heure", ARRONDI_DEMI_HEURE),
                                  ("Arrondi des heures d'arrivée et de départ", ARRONDI_HEURE_ARRIVEE_DEPART)
                                  ]

modes_arrondi_horaires_salaries = [("Pas d'arrondi", SANS_ARRONDI),
                                   ("Arrondi à l'heure", ARRONDI_HEURE),
                                   ("Arrondi des heures d'arrivée et de départ", ARRONDI_HEURE_ARRIVEE_DEPART)
                                   ]

modes_arrondi_semaines_periodes = [("Arrondi à la semaine supérieure", ARRONDI_SEMAINE_SUPERIEURE),
                                   ("Arrondi à la semaine la plus proche", ARRONDI_SEMAINE_PLUS_PROCHE),
                                   ("Arrondi à la semaine supérieure avec limite à 52 semaines", ARRONDI_SEMAINE_AVEC_LIMITE_52_SEMAINES)
                                   ]

temps_facturation = [("Fin de mois", FACTURATION_FIN_MOIS),
                     ("Début de mois : contrat mois + réalisé mois-1", FACTURATION_DEBUT_MOIS_CONTRAT),
                     ("Début de mois : prévisionnel mois + réalisé mois-1", FACTURATION_DEBUT_MOIS_PREVISIONNEL),
                     ]

modes_saisie_planning = [("A partir de l'interface planning (recommandé)", SAISIE_HORAIRE),
                         ("En volume horaire par semaine", SAISIE_HEURES_SEMAINE),
                         ("En jours par semaine", SAISIE_JOURS_SEMAINE),
                         ]

modes_inscription = [("Plein-temps uniquement", MODE_TEMPS_PLEIN),
                     ("Temps partiel uniquement", MODE_TEMPS_PARTIEL),
                     ("Tous modes", TOUS_MODES_ACCUEIL),
                     ]

modes_gestion_standard = [("Géré", True),
                          ("Non géré", False)
                          ]


class StructureCapaciteLine(BasePlanningLine, BaseWxPythonLine):
    def __init__(self, index):
        BasePlanningLine.__init__(self, days[index], database.creche.tranches_capacite.get(index, Day()).timeslots, options=DRAW_VALUES)
        self.index = index
        self.update()

    def update(self):
        self.day = database.creche.tranches_capacite.get(self.index, Day())
        self.timeslots = self.day.timeslots

    def add_timeslot(self, debut, fin, value):
        timeslot = TrancheCapacite(creche=database.creche, jour=self.index, debut=debut, fin=fin, value=value)
        database.creche.tranches_capacite.add(timeslot)
        self.update()

    def delete_timeslot(self, i, check=True):
        timeslot = self.timeslots[i]
        database.creche.tranches_capacite.remove(timeslot)
        self.update()


class CrecheTab(AutoTab):
    def __init__(self, parent):
        global delbmp
        delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        grid_sizer = wx.FlexGridSizer(0, 2, 5, 5)
        grid_sizer.AddGrowableCol(1, 1)
        grid_sizer.AddMany([wx.StaticText(self, -1, "Nom de la structure :"), (AutoTextCtrl(self, database.creche, "nom"), 0, wx.EXPAND)])
        grid_sizer.AddMany([wx.StaticText(self, -1, "Adresse :"), (AutoTextCtrl(self, database.creche, "adresse"), 0, wx.EXPAND)])
        grid_sizer.AddMany([wx.StaticText(self, -1, "Code Postal :"), (AutoNumericCtrl(self, database.creche, "code_postal", precision=0), 0, wx.EXPAND)])
        grid_sizer.AddMany([wx.StaticText(self, -1, "Ville :"), (AutoTextCtrl(self, database.creche, "ville"), 0, wx.EXPAND)])
        grid_sizer.AddMany([wx.StaticText(self, -1, "Téléphone :"), (AutoPhoneCtrl(self, database.creche, "telephone"), 0, wx.EXPAND)])
        grid_sizer.AddMany([wx.StaticText(self, -1, "E-mail :"), (AutoTextCtrl(self, database.creche, "email"), 0, wx.EXPAND)])
        grid_sizer.AddMany([wx.StaticText(self, -1, "Serveur pour l'envoi d'emails :"), (AutoTextCtrl(self, database.creche, "smtp_server"), 0, wx.EXPAND)])
        grid_sizer.AddMany([wx.StaticText(self, -1, "Email de la CAF :"), (AutoTextCtrl(self, database.creche, "caf_email"), 0, wx.EXPAND)])
        type_structure_choice = AutoChoiceCtrl(self, database.creche, "type", items=TypesCreche)
        self.Bind(wx.EVT_CHOICE, self.OnChangementTypeStructure, type_structure_choice)
        grid_sizer.AddMany([wx.StaticText(self, -1, "Type :"), (type_structure_choice, 0, wx.EXPAND)])
        raz_permanences_label = wx.StaticText(self, -1, "Date de remise à zéro des permanences :")
        raz_permanences_ctrl = AutoDateCtrl(self, database.creche, "date_raz_permanences")
        grid_sizer.AddMany([raz_permanences_label, (raz_permanences_ctrl, 0, wx.EXPAND)])
        self.creche_parentale_widgets = (raz_permanences_label, raz_permanences_ctrl)
        if config.options & PRELEVEMENTS_AUTOMATIQUES:
            grid_sizer.AddMany([wx.StaticText(self, -1, "IBAN :"), (AutoTextCtrl(self, database.creche, "iban"), 0, wx.EXPAND)])
            grid_sizer.AddMany([wx.StaticText(self, -1, "BIC :"), (AutoTextCtrl(self, database.creche, "bic"), 0, wx.EXPAND)])
            grid_sizer.AddMany([wx.StaticText(self, -1, "Creditor ID :"), (AutoTextCtrl(self, database.creche, "creditor_id"), 0, wx.EXPAND)])
        grid_sizer.AddMany([wx.StaticText(self, -1, "SIRET :"), (AutoTextCtrl(self, database.creche, "siret"), 0, wx.EXPAND)])
        planning = PlanningWidget(self, None, NO_BOTTOM_LINE | NO_ICONS | DRAW_VALUES | NO_SCROLL)
        lines = []
        for i in range(7):
            if database.creche.is_jour_semaine_travaille(i):
                lines.append(StructureCapaciteLine(i))
        planning.SetLines(lines)
        grid_sizer.AddMany([wx.StaticText(self, -1, "Capacité :"), (planning, 1, wx.EXPAND)])
        self.sizer.Add(grid_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        self.sites_box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Sites"), wx.VERTICAL)
        self.sites_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, site in enumerate(database.creche.sites):
            self.AjouteLigneSite(i)
        self.sites_box_sizer.Add(self.sites_sizer, 0, wx.EXPAND | wx.ALL, 5)
        button_add = wx.Button(self, -1, "Nouveau site")
        if config.readonly:
            button_add.Disable()
        self.sites_box_sizer.Add(button_add, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutSite, button_add)
        self.sizer.Add(self.sites_box_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        self.groupes_box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Groupes"), wx.VERTICAL)
        self.groupes_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, groupe in enumerate(database.creche.groupes):
            self.AjouteLigneGroupe(i)
        self.groupes_box_sizer.Add(self.groupes_sizer, 0, wx.EXPAND | wx.ALL, 5)
        button_add = wx.Button(self, -1, "Nouveau groupe")
        if config.readonly:
            button_add.Disable()
        self.groupes_box_sizer.Add(button_add, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutGroupe, button_add)
        self.sizer.Add(self.groupes_box_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        if config.options & CATEGORIES:
            self.categories_box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Catégories"), wx.VERTICAL)
            self.categories_sizer = wx.BoxSizer(wx.VERTICAL)
            for i, categorie in enumerate(database.creche.categories):
                self.AjouteLigneCategorie(i)
            self.categories_box_sizer.Add(self.categories_sizer, 0, wx.EXPAND | wx.ALL, 5)
            button_add = wx.Button(self, -1, "Nouvelle catégorie")
            if config.readonly:
                button_add.Disable()
            self.categories_box_sizer.Add(button_add, 0, wx.ALL, 5)
            self.Bind(wx.EVT_BUTTON, self.OnAjoutCategorie, button_add)
            self.sizer.Add(self.categories_box_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(self.sizer)

    def UpdateContents(self):
        for i in range(len(self.sites_sizer.GetChildren()), len(database.creche.sites)):
            self.AjouteLigneSite(i)
        for i in range(len(database.creche.sites), len(self.sites_sizer.GetChildren())):
            self.SupprimeLigneSite()
        for i in range(len(self.groupes_sizer.GetChildren()), len(database.creche.groupes)):
            self.AjouteLigneGroupe(i)
        for i in range(len(database.creche.groupes), len(self.groupes_sizer.GetChildren())):
            self.SupprimeLigneGroupe()
        self.sizer.Layout()
        AutoTab.UpdateContents(self)

    def AjouteLigneSite(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, "Nom :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, database.creche, "sites[%d].nom" % index, observers=['sites']), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, "Adresse :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, database.creche, "sites[%d].adresse" % index), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, "Code Postal :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoNumericCtrl(self, database.creche, "sites[%d].code_postal" % index, precision=0), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, "Ville :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, database.creche, "sites[%d].ville" % index), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, "Téléphone"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoPhoneCtrl(self, database.creche, "sites[%d].telephone" % index), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, "Capacité"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoNumericCtrl(self, database.creche, "sites[%d].capacite" % index, precision=0), 1, wx.EXPAND)])                
        if config.options & GROUPES_SITES:
            sizer.AddMany([(wx.StaticText(self, -1, "Groupe"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoNumericCtrl(self, database.creche, "sites[%d].groupe" % index, precision=0), 1, wx.EXPAND)])                
        if not config.readonly:
            delbutton = wx.BitmapButton(self, -1, delbmp)
            delbutton.index = index
            sizer.Add(delbutton, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
            self.Bind(wx.EVT_BUTTON, self.OnSuppressionSite, delbutton)
        self.sites_sizer.Add(sizer, 0, wx.EXPAND | wx.BOTTOM, 5)

    def SupprimeLigneSite(self):
        index = len(self.sites_sizer.GetChildren()) - 1
        sizer = self.sites_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.sites_sizer.Detach(index)

    def OnAjoutSite(self, _):
        counters['sites'] += 1
        history.Append(Delete(database.creche.sites, -1))
        database.creche.sites.append(Site())
        self.AjouteLigneSite(len(database.creche.sites) - 1)
        self.sizer.Layout()

    def OnSuppressionSite(self, event):
        counters['sites'] += 1
        index = event.GetEventObject().index
        history.Append(Insert(database.creche.sites, index, database.creche.sites[index]))
        self.SupprimeLigneSite()
        del database.creche.sites[index]
        self.sizer.FitInside(self)
        self.UpdateContents()

    def AjouteLigneGroupe(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, "Nom :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, database.creche, "groupes[%d].nom" % index, observers=['groupes']), 1, wx.EXPAND)])
        if database.creche.changement_groupe_auto:
            sizer.AddMany([(wx.StaticText(self, -1, "Age maximum :"), 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoNumericCtrl(self, database.creche, "groupes[%d].age_maximum" % index, observers=['groupes'], precision=0), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, "Ordre :"), 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoNumericCtrl(self, database.creche, "groupes[%d].ordre" % index, observers=['groupes'], precision=0), 0, wx.EXPAND)])
        if not config.readonly:
            delbutton = wx.BitmapButton(self, -1, delbmp)
            delbutton.index = index
            sizer.Add(delbutton, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
            self.Bind(wx.EVT_BUTTON, self.OnSuppressionGroupe, delbutton)
        self.groupes_sizer.Add(sizer, 0, wx.EXPAND | wx.BOTTOM, 5)

    def SupprimeLigneGroupe(self):
        index = len(self.groupes_sizer.GetChildren()) - 1
        sizer = self.groupes_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.groupes_sizer.Detach(index)

    def OnAjoutGroupe(self, _):
        counters['groupes'] += 1
        history.Append(Delete(database.creche.groupes, -1))
        if len(database.creche.groupes) == 0:
            ordre = 0
        else:
            ordre = database.creche.groupes[-1].ordre + 1
        database.creche.groupes.append(Groupe(creche=database.creche, ordre=ordre))
        self.AjouteLigneGroupe(len(database.creche.groupes) - 1)
        self.sizer.FitInside(self)
        self.sizer.Layout()

    def OnSuppressionGroupe(self, event):
        counters['groupes'] += 1
        index = event.GetEventObject().index
        history.Append(Insert(database.creche.groupes, index, database.creche.groupes[index]))
        self.SupprimeLigneGroupe()
        del database.creche.groupes[index]
        self.sizer.FitInside(self)
        self.UpdateContents()
        
    def AjouteLigneCategorie(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, "Nom :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, database.creche, "categories[%d].nom" % index, observers=['categories']), 1, wx.EXPAND)])
        if not config.readonly:
            delbutton = wx.BitmapButton(self, -1, delbmp)
            delbutton.index = index
            sizer.Add(delbutton, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
            self.Bind(wx.EVT_BUTTON, self.OnSuppressionCategorie, delbutton)
        self.categories_sizer.Add(sizer, 0, wx.EXPAND | wx.BOTTOM, 5)

    def SupprimeLigneCategorie(self):
        index = len(self.categories_sizer.GetChildren()) - 1
        sizer = self.categories_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.categories_sizer.Detach(index)

    def OnAjoutCategorie(self, _):
        counters['categories'] += 1
        history.Append(Delete(database.creche.categories, -1))
        database.creche.categories.append(Categorie())
        self.AjouteLigneCategorie(len(database.creche.categories) - 1)
        self.sizer.FitInside(self)
        self.sizer.Layout()

    def OnSuppressionCategorie(self, event):
        counters['categories'] += 1
        index = event.GetEventObject().index
        history.Append(Insert(database.creche.categories, index, database.creche.categories[index]))
        self.SupprimeLigneCategorie()
        del database.creche.categories[index]
        self.sizer.FitInside(self)
        self.UpdateContents()
        
    def OnChangementTypeStructure(self, event):
        obj = event.GetEventObject()
        value = obj.GetClientData(obj.GetSelection())
        self.GetParent().DisplayProfesseursTab(value == TYPE_GARDERIE_PERISCOLAIRE)
        for widget in self.creche_parentale_widgets:
            widget.Show(value == TYPE_PARENTAL)
        event.Skip()


class ProfesseursTab(AutoTab):
    def __init__(self, parent):
        global delbmp
        delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.professeurs_sizer = wx.BoxSizer(wx.VERTICAL)
        for professeur in database.creche.professeurs:
            self.affiche_professeur(professeur)
        self.sizer.Add(self.professeurs_sizer, 0, wx.EXPAND | wx.ALL, 5)
        button_add = wx.Button(self, -1, "Nouveau professeur")
        self.sizer.Add(button_add, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutProfesseur, button_add)
        self.SetSizer(self.sizer)

    def UpdateContents(self):
        pass

    def affiche_professeur(self, professeur):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, "Prénom :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), (AutoTextCtrl(self, professeur, "prenom", observers=['professeurs']), 0, wx.ALIGN_CENTER_VERTICAL)])
        sizer.AddMany([(wx.StaticText(self, -1, "Nom :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), (AutoTextCtrl(self, professeur, "nom", observers=['professeurs']), 0, wx.ALIGN_CENTER_VERTICAL)])
        sizer.AddMany([(wx.StaticText(self, -1, "Entrée :", size=(50,-1)), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), AutoDateCtrl(self, professeur, "entree", observers=['professeurs'])])
        sizer.AddMany([(wx.StaticText(self, -1, "Sortie :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), AutoDateCtrl(self, professeur, "sortie", observers=['professeurs'])])
        if not config.readonly:
            delbutton = wx.BitmapButton(self, -1, delbmp, style=wx.NO_BORDER)
            delbutton.professeur, delbutton.sizer = professeur, sizer
            sizer.Add(delbutton, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
            self.Bind(wx.EVT_BUTTON, self.OnSuppressionProfesseur, delbutton)
        self.professeurs_sizer.Add(sizer)

    def OnAjoutProfesseur(self, _):
        counters['professeurs'] += 1
        history.Append(Delete(database.creche.professeurs, -1))
        professeur = Professeur()
        database.creche.professeurs.append(professeur)
        self.affiche_professeur(professeur)        
        self.sizer.FitInside(self)
        
    def OnSuppressionProfesseur(self, event):
        counters['professeurs'] += 1
        obj = event.GetEventObject()
        for i, professeur in enumerate(database.creche.professeurs):
            if professeur == obj.professeur:
                history.Append(Insert(database.creche.professeurs, i, professeur))
                sizer = self.professeurs_sizer.GetItem(i)
                sizer.DeleteWindows()
                self.professeurs_sizer.Detach(i)
                del database.creche.professeurs[i]
                self.sizer.FitInside(self)
                self.Refresh()
                break


class ResponsabilitesTab(AutoTab, PeriodeMixin):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        PeriodeMixin.__init__(self, "bureaux")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(PeriodeChoice(self, lambda obj: Bureau(creche=database.creche)), 0, wx.TOP, 5)
        sizer2 = wx.FlexGridSizer(0, 2, 5, 5)
        sizer2.AddGrowableCol(1, 1)
        self.responsables_ctrls = []
        if database.creche.type == TYPE_MULTI_ACCUEIL:
            self.gerant_ctrl = AutoComboBox(self, None, "gerant")
            sizer2.AddMany([(wx.StaticText(self, -1, "Gérant(e) :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.gerant_ctrl, 0, wx.EXPAND)])
            self.directeur_ctrl = AutoComboBox(self, None, "directeur")        
            sizer2.AddMany([(wx.StaticText(self, -1, "Directeur(trice) :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.directeur_ctrl, 0, wx.EXPAND)])
            self.directeur_adjoint_ctrl = AutoComboBox(self, None, "directeur_adjoint")        
            sizer2.AddMany([(wx.StaticText(self, -1, "Directeur(trice) adjoint(e) :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.directeur_adjoint_ctrl, 0, wx.EXPAND)])
            self.comptable_ctrl = AutoComboBox(self, None, "comptable")        
            sizer2.AddMany([(wx.StaticText(self, -1, "Comptable :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.comptable_ctrl, 0, wx.EXPAND)])
            self.secretaire_ctrl = AutoComboBox(self, None, "secretaire")        
            sizer2.AddMany([(wx.StaticText(self, -1, "Secrétaire :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.secretaire_ctrl, 0, wx.EXPAND)])
        else:
            self.gerant_ctrl = None
            self.responsables_ctrls.append(AutoComboBox(self, None, "president"))
            sizer2.AddMany([(wx.StaticText(self, -1, "Président(e) :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.responsables_ctrls[-1], 0, wx.EXPAND)])
            self.responsables_ctrls.append(AutoComboBox(self, None, "vice_president"))
            sizer2.AddMany([(wx.StaticText(self, -1, "Vice président(e) :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.responsables_ctrls[-1], 0, wx.EXPAND)])
            self.responsables_ctrls.append(AutoComboBox(self, None, "tresorier"))
            sizer2.AddMany([(wx.StaticText(self, -1, "Trésorier(ère) :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.responsables_ctrls[-1], 0, wx.EXPAND)])
            self.responsables_ctrls.append(AutoComboBox(self, None, "secretaire"))        
            sizer2.AddMany([(wx.StaticText(self, -1, "Secrétaire :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.responsables_ctrls[-1], 0, wx.EXPAND)])
            self.directeur_ctrl = AutoComboBox(self, None, "directeur")        
            sizer2.AddMany([(wx.StaticText(self, -1, "Directeur(trice) :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.directeur_ctrl, 0, wx.EXPAND)])
        sizer.Add(sizer2, 0, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)

    def UpdateContents(self):
        self.SetInstance(database.creche)

    def SetInstance(self, instance, periode=None):
        self.instance = instance
        if instance and len(instance.bureaux) > 0:
            if periode is None:
                current_periode = eval("self.instance.%s[-1]" % self.member)
            else:
                current_periode = eval("self.instance.%s[%d]" % (self.member, periode))
            
            salaries = self.GetNomsSalaries(current_periode)
            
            if self.gerant_ctrl:
                self.gerant_ctrl.SetItems(salaries)
                self.directeur_ctrl.SetItems(salaries)
                self.directeur_adjoint_ctrl.SetItems(salaries)
                self.comptable_ctrl.SetItems(salaries)                
                self.secretaire_ctrl.SetItems(salaries)
            else:
                parents = self.GetNomsParents(current_periode)
                for ctrl in self.responsables_ctrls:
                    ctrl.SetItems(parents)
                self.directeur_ctrl.SetItems(salaries)
        PeriodeMixin.SetInstance(self, instance, periode)

    def GetNomsParents(self, periode):
        noms = set()
        if periode.debut and periode.fin:
            for inscrit in database.creche.select_inscrits(periode.debut, periode.fin):
                for parent in inscrit.famille.parents:
                    noms.add(GetPrenomNom(parent))
        noms = list(noms)
        noms.sort(cmp=lambda x, y: cmp(x.lower(), y.lower()))
        return noms
    
    def GetNomsSalaries(self, periode):
        noms = []
        for salarie in database.creche.salaries:
            noms.append(GetPrenomNom(salarie))
        noms.sort(cmp=lambda x,y: cmp(x.lower(), y.lower()))
        return noms


activity_ownership = [
    ("Enfants et Salariés", ACTIVITY_OWNER_ALL),
    ("Enfants", ACTIVITY_OWNER_ENFANTS),
    ("Salariés", ACTIVITY_OWNER_SALARIES)
]


class ActivitesTab(AutoTab):
    def __init__(self, parent):
        global delbmp
        delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        AutoTab.__init__(self, parent)
        self.color_buttons = {}
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Temps de présence"), wx.VERTICAL)
        flex_sizer = wx.FlexGridSizer(0, 3, 3, 2)
        flex_sizer.AddGrowableCol(1, 1)
        flex_sizer.AddMany([(wx.StaticText(self, -1, "Libellé :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), wx.Size(10,10), (AutoTextCtrl(self, database.creche.states[MODE_PRESENCE], "label"), 1, wx.EXPAND)])

        for label, activite, field in (("présences", database.creche.states[0], "couleur"), ("présences supplémentaires", database.creche.states[0], "couleur_supplement"), ("absences pour congés", database.creche.states[VACANCES], "couleur"), ("absences non prévenues", database.creche.states[ABSENCE_NON_PREVENUE], "couleur"), ("absences pour maladie", database.creche.states[MALADE], "couleur")):
            color_button = wx.Button(self, -1, "", size=(20, 20))            
            r, g, b, a, h = couleur = getattr(activite, field)
            color_button.SetBackgroundColour(wx.Colour(r, g, b))
            self.Bind(wx.EVT_BUTTON, self.OnColorButton, color_button)
            color_button.hash_cb = HashComboBox(self)
            if config.readonly:
                color_button.Disable()
                color_button.hash_cb.Disable()
            color_button.activite = color_button.hash_cb.activite = activite
            color_button.field = color_button.hash_cb.field = [field]
            self.color_buttons[(activite.mode, field)] = color_button
            self.UpdateHash(color_button.hash_cb, couleur)
            self.Bind(wx.EVT_COMBOBOX, self.OnHashChange, color_button.hash_cb)
            flex_sizer.AddMany([(wx.StaticText(self, -1, "Couleur des %s :" % label), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (color_button, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (color_button.hash_cb, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)])
        box_sizer.Add(flex_sizer, 0, wx.BOTTOM, 5)
        button = wx.Button(self, -1, "Rétablir les couleurs par défaut")
        self.Bind(wx.EVT_BUTTON, self.OnCouleursDefaut, button)
        box_sizer.Add(button, 0, wx.ALL, 5)
        self.sizer.Add(box_sizer, 0, wx.ALL | wx.EXPAND, 5)

        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Activités"), wx.VERTICAL)
        self.activites_sizer = wx.BoxSizer(wx.VERTICAL)
        for activity in database.creche.activites:
            if activity.mode > 0:
                self.AjouteLigneActivite(activity)
        box_sizer.Add(self.activites_sizer, 0, wx.EXPAND | wx.ALL, 5)
        button_add = wx.Button(self, -1, "Nouvelle activité")
        box_sizer.Add(button_add, 0, wx.ALL, 5)
        if config.readonly:
            button.Disable()
            button_add.Disable()
        else:
            self.Bind(wx.EVT_BUTTON, self.OnAjoutActivite, button_add)
        self.sizer.Add(box_sizer, 0, wx.ALL | wx.EXPAND, 5)
        self.SetSizer(self.sizer)
        self.sizer.Layout()
        self.UpdateContents()

    def UpdateContents(self):
        self.color_buttons[(0, "couleur_supplement")].Enable(not config.readonly and database.creche.presences_supplementaires)
        self.color_buttons[(0, "couleur_supplement")].hash_cb.Enable(not config.readonly and database.creche.presences_supplementaires)
        self.activites_sizer.Clear(True)
        for activity in database.creche.activites:
            self.AjouteLigneActivite(activity)
        self.sizer.Layout()
        
    def OnCouleursDefaut(self, event):
        history.Append(None)
        counters['activites'] += 1
        database.creche.states[0].couleur = [5, 203, 28, 150, wx.SOLID]
        database.creche.states[0].couleur_supplement = [5, 203, 28, 250, wx.SOLID]
        database.creche.states[VACANCES].couleur = [0, 0, 255, 150, wx.SOLID]
        database.creche.states[ABSENCE_NON_PREVENUE].couleur = [0, 0, 255, 150, wx.SOLID]
        database.creche.states[MALADE].couleur = [190, 35, 29, 150, wx.SOLID]
        for activite, field in [(database.creche.states[0], "couleur"), (database.creche.states[0], "couleur_supplement")]:
            r, g, b, a, h = color = getattr(activite, field)
            self.color_buttons[(0, field)].SetBackgroundColour(wx.Colour(r, g, b))
            self.UpdateHash(self.color_buttons[(0, field)].hash_cb, color)        

    def AjouteLigneActivite(self, activity):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, "Libellé :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, activity, "label"), 1, wx.EXPAND)])
        mode_choice = AutoChoiceCtrl(self, activity, "mode", items=ActivityModes, observers=['activites'])
        self.Bind(wx.EVT_CHOICE, self.OnChangementMode, mode_choice)
        sizer.AddMany([(wx.StaticText(self, -1, "Mode :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (mode_choice, 0, 0)])
        color_button = mode_choice.color_button = wx.Button(self, -1, "", size=(20, 20))
        r, g, b, a, h = activity.couleur
        color_button.SetBackgroundColour(wx.Colour(r, g, b))
        self.Bind(wx.EVT_BUTTON, self.OnColorButton, color_button)
        color_button.static = wx.StaticText(self, -1, "Couleur :")
        color_button.hash_cb = HashComboBox(self)
        color_button.activite = color_button.hash_cb.activite = activity
        color_button.field = color_button.hash_cb.field = ["couleur", "couleur_supplement"]
        self.UpdateHash(color_button.hash_cb, activity.couleur)
        self.Bind(wx.EVT_COMBOBOX, self.OnHashChange, color_button.hash_cb)
        sizer.AddMany([(color_button.static, 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (color_button, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (color_button.hash_cb, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)])
        if database.creche.tarification_activites:
            sizer.AddMany([(wx.StaticText(self, -1, "Tarif :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, activity, "formule_tarif"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)])
        if not config.readonly:
            delbutton = wx.BitmapButton(self, -1, delbmp)
            delbutton.activity = activity
            sizer.Add(delbutton, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
            self.Bind(wx.EVT_BUTTON, self.OnSuppressionActivite, delbutton)      
        if config.readonly or activity.mode == MODE_SANS_HORAIRES:
            color_button.Disable()
            color_button.static.Disable()
            color_button.hash_cb.Disable()
        self.activites_sizer.Add(sizer, 0, wx.EXPAND | wx.BOTTOM, 5)

    def OnAjoutActivite(self, _):
        counters['activites'] += 1
        activity = Activite(creche=database.creche, mode=MODE_NORMAL)
        colors = [tmp.couleur for tmp in database.creche.activites]
        for h in (wx.BDIAGONAL_HATCH, wx.CROSSDIAG_HATCH, wx.FDIAGONAL_HATCH, wx.CROSS_HATCH, wx.HORIZONTAL_HATCH, wx.VERTICAL_HATCH, wx.TRANSPARENT, wx.SOLID):
            for color in (wx.RED, wx.BLUE, wx.CYAN, wx.GREEN, wx.LIGHT_GREY):
                r, g, b = color.Get()
                if (r, g, b, 150, h) not in colors:
                    couleur = (r, g, b, 150, h)
                    couleur_supplement = (r, g, b, 250, h)
                    break
            if couleur:
                break
        else:
            couleur = 0, 0, 0, 150, wx.SOLID
            couleur_supplement = 0, 0, 0, 250, wx.SOLID
        activity.set_color("couleur", couleur)
        activity.set_color("couleur_supplement", couleur_supplement)
        database.creche.add_activite(activity)
        history.Append(None)  # TODO Delete(database.creche.activites, activity.value))
        self.AjouteLigneActivite(activity)
        self.sizer.Layout()

    def OnSuppressionActivite(self, event):
        counters['activites'] += 1
        activity = event.GetEventObject().activity
        timeslots = database.query(TimeslotInscrit).filter(TimeslotInscrit.activity == activity).all()
        if len(timeslots) > 0:
            message = "Cette activité est utilisée par :\n"
            message += ", ".join(["%s le %s" % (GetPrenomNom(timeslot.inscrit), GetDateString(timeslot.date)) for timeslot in timeslots[:10]])
            if len(timeslots) > 10:
                message += ", etc."
            message += "\nVoulez-vous vraiment la supprimer ?"
            dlg = wx.MessageDialog(self, message, "Confirmation", wx.OK | wx.CANCEL | wx.ICON_WARNING)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_OK:
                return
        history.Append(None)
        for i, child in enumerate(self.activites_sizer.GetChildren()):
            sizer = child.GetSizer()
            if activity == sizer.GetItem(len(sizer.Children)-1).GetWindow().activity:
                sizer.DeleteWindows()
                self.activites_sizer.Detach(i)
        database.creche.delete_activite(activity)
        self.sizer.Layout()
        self.UpdateContents()

    def UpdateHash(self, hash_cb, color):
        r, g, b, a, h = color
        hash_cb.Clear()
        for i, hash in enumerate((wx.SOLID, wx.TRANSPARENT, wx.BDIAGONAL_HATCH, wx.CROSSDIAG_HATCH, wx.FDIAGONAL_HATCH, wx.CROSS_HATCH, wx.HORIZONTAL_HATCH, wx.VERTICAL_HATCH)):
            hash_cb.Append("", (r, g, b, a, hash))
            if hash == h:
                hash_cb.SetSelection(i)
    
    def OnChangementMode(self, event):
        obj = event.GetEventObject()
        color_button = obj.color_button
        value = obj.GetClientData(obj.GetSelection())
        color_button.Enable(value != MODE_SANS_HORAIRES)
        color_button.static.Enable(value != MODE_SANS_HORAIRES)
        color_button.hash_cb.Enable(value != MODE_SANS_HORAIRES)
        event.Skip()
        
    def OnColorButton(self, event):
        history.Append(None)
        counters['activites'] += 1
        obj = event.GetEventObject()
        r, g, b, a, h = getattr(obj.activite, obj.field[0])
        data = wx.ColourData()
        data.SetColour((r, g, b, a))
        try:
            import wx.lib.agw.cubecolourdialog as CCD
            dlg = CCD.CubeColourDialog(self, data)
            dlg.GetColourData().SetChooseFull(True)
            if dlg.ShowModal() == wx.ID_OK:
                data = dlg.GetColourData()
                colour = data.GetColour()
                r, g, b, a = colour.Red(), colour.Green(), colour.Blue(), colour.Alpha()
        except ImportError:
            dlg = wx.ColourDialog(self, data)
            if dlg.ShowModal() == wx.ID_OK:
                data = dlg.GetColourData()
                r, g, b = data.GetColour()
        couleur = r, g, b, a, h
        for field in obj.field:
            obj.activite.set_color(field, couleur)
        obj.SetBackgroundColour(wx.Colour(r, g, b))
        self.UpdateHash(obj.hash_cb, couleur)
    
    def OnHashChange(self, event):
        history.Append(None)
        counters['activites'] += 1
        obj = event.GetEventObject()
        for field in obj.field:
            obj.activite.set_color(field, obj.GetClientData(obj.GetSelection()))


class ChargesTab(AutoTab, PeriodeMixin):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        PeriodeMixin.__init__(self, "charges")
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.annee_choice = wx.Choice(self, -1)
        AddYearsToChoice(self.annee_choice)
        self.Bind(wx.EVT_CHOICE, self.OnAnneeChoice, self.annee_choice)
        sizer.Add(self.annee_choice, 0, wx.EXPAND | wx.ALL, 5)
        sizer2 = wx.FlexGridSizer(12, 2, 5, 5)
        self.charges_ctrls = []
        for m in range(12):
            ctrl = AutoNumericCtrl(self, None, "charges", precision=2)
            self.charges_ctrls.append(ctrl)
            sizer2.AddMany([wx.StaticText(self, -1, months[m] + " :"), ctrl])
        sizer.Add(sizer2, 0, wx.ALL, 5)
        self.OnAnneeChoice(None)
        sizer.Fit(self)
        self.SetSizer(sizer)

    def OnAnneeChoice(self, _):
        selected = self.annee_choice.GetSelection()
        annee = self.annee_choice.GetClientData(selected)
        for m in range(12):
            date = datetime.date(annee, m+1, 1)
            if date not in database.creche.charges:
                database.creche.charges[date] = Charge(creche=database.creche, date=date)
            self.charges_ctrls[m].SetInstance(database.creche.charges[date])
        

class CafTab(AutoTab, PeriodeMixin):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        PeriodeMixin.__init__(self, "baremes_caf")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(PeriodeChoice(self, lambda obj: BaremeCAF(creche=database.creche)), 0, wx.TOP, 5)
        sizer2 = wx.FlexGridSizer(4, 2, 5, 5)
        sizer2.AddMany([wx.StaticText(self, -1, "Plancher annuel :"), AutoNumericCtrl(self, None, "plancher", precision=2)])
        sizer2.AddMany([wx.StaticText(self, -1, "Plafond annuel :"), AutoNumericCtrl(self, None, "plafond", precision=2)])
        sizer.Add(sizer2, 0, wx.ALL, 5)
        sizer.Fit(self)
        self.SetSizer(sizer)

    def UpdateContents(self):
        self.SetInstance(database.creche)
        

class JoursFermeturePanel(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        labels_conges = [j[0] for j in jours_fermeture]
        self.jours_feries_sizer = wx.BoxSizer(wx.VERTICAL)
        for text in labels_conges:
            checkbox = wx.CheckBox(self, -1, text)
            if config.readonly:
                checkbox.Disable()
            if text in database.creche.feries:
                checkbox.SetValue(True)
            self.jours_feries_sizer.Add(checkbox, 0, wx.EXPAND)
            self.Bind(wx.EVT_CHECKBOX, self.feries_check, checkbox)
        self.conges_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, conge in enumerate(database.creche.conges):
            self.AjouteLigneConge(i)
        self.sizer.Add(self.jours_feries_sizer, 0, wx.ALL, 5)
        self.sizer.Add(self.conges_sizer, 0, wx.ALL, 5)
        button_add = wx.Button(self, -1, "Ajouter une période de fermeture")
        if config.readonly:
            button_add.Disable()
        self.sizer.Add(button_add, 0, wx.EXPAND | wx.TOP, 5)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutConge, button_add)
        self.SetSizer(self.sizer)
        self.Layout()

    def UpdateContents(self):
        for i in range(len(self.conges_sizer.GetChildren()), len(database.creche.conges)):
            self.AjouteLigneConge(i)
        for i in range(len(database.creche.conges), len(self.conges_sizer.GetChildren())):
            self.RemoveLine()
        self.sizer.Layout()
        AutoTab.UpdateContents(self)
        self.sizer.FitInside(self)

    def AjouteLigneConge(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, "Debut :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, database.creche, "conges[%d].debut" % index, mois=True, observers=['conges'])])
        sizer.AddMany([(wx.StaticText(self, -1, "Fin :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, database.creche, "conges[%d].fin" % index, mois=True, observers=['conges'])])
        sizer.AddMany([(wx.StaticText(self, -1, "Libellé :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, database.creche, "conges[%d].label" % index, observers=['conges'])])
        sizer.AddMany([(wx.StaticText(self, -1, "Options :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, database.creche, "conges[%d].options" % index, ModeCongeItems, observers=['conges']), 0, wx.EXPAND)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        if config.readonly:
            delbutton.Disable()
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.OnSuppressionConge, delbutton)
        self.conges_sizer.Add(sizer)

    def RemoveLine(self):
        index = len(self.conges_sizer.GetChildren()) - 1
        sizer = self.conges_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.conges_sizer.Detach(index)

    def OnAjoutConge(self, _):
        counters['conges'] += 1
        history.Append(Delete(database.creche.conges, -1))
        conge = CongeStructure(creche=database.creche, debut="", fin="", label="", options=0)
        database.creche.add_conge(conge)
        self.AjouteLigneConge(len(database.creche.conges) - 1)
        self.sizer.FitInside(self)
        self.sizer.Layout()

    def OnSuppressionConge(self, event):
        counters['conges'] += 1
        index = event.GetEventObject().index
        conge = database.creche.conges[index]
        history.Append(Insert(database.creche.conges, index, conge))
        self.RemoveLine()
        database.creche.delete_conge(conge)
        self.UpdateContents()

    def feries_check(self, event):
        label = event.GetEventObject().GetLabelText()
        if event.IsChecked():
            conge = CongeStructure(creche=database.creche, debut=label)
            database.creche.add_ferie(conge)
        else:
            conge = database.creche.feries[label]
            database.creche.delete_ferie(conge)
        history.Append(None)


class ReservatairesTab(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.reservataires_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, reservataire in enumerate(database.creche.reservataires):
            self.AjouteLigneReservataire(i)
        self.sizer.Add(self.reservataires_sizer, 0, wx.ALL, 5)
        button_add = wx.Button(self, -1, "Nouveau réservataire")
        if config.readonly:
            button_add.Disable()
        self.sizer.Add(button_add, 0, wx.EXPAND+wx.TOP, 5)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutReservataire, button_add)
        sizer.Add(self.sizer, 0, wx.EXPAND+wx.ALL, 5)
        self.SetSizer(sizer)

    def UpdateContents(self):
        for i in range(len(self.reservataires_sizer.GetChildren()), len(database.creche.reservataires)):
            self.AjouteLigneReservataire(i)
        for i in range(len(database.creche.reservataires), len(self.reservataires_sizer.GetChildren())):
            self.RemoveLine()
        self.sizer.Layout()
        AutoTab.UpdateContents(self)

    def AjouteLigneReservataire(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, "Debut :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, database.creche, "reservataires[%d].debut" % index, observers=['reservataires'])])
        sizer.AddMany([(wx.StaticText(self, -1, "Fin :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, database.creche, "reservataires[%d].fin" % index, observers=['reservataires'])])
        sizer.AddMany([(wx.StaticText(self, -1, "Nom :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, database.creche, "reservataires[%d].nom" % index, observers=['reservataires'])])
        sizer.AddMany([(wx.StaticText(self, -1, "Places :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), AutoNumericCtrl(self, database.creche, "reservataires[%d].places" % index, precision=0, observers=['reservataires'])])
        sizer.AddMany([(wx.StaticText(self, -1, "Adresse :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, database.creche, "reservataires[%d].adresse" % index, observers=['reservataires'])])
        sizer.AddMany([(wx.StaticText(self, -1, "Code Postal :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), AutoNumericCtrl(self, database.creche, "reservataires[%d].code_postal" % index, precision=0, observers=['reservataires'])])
        sizer.AddMany([(wx.StaticText(self, -1, "Ville :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, database.creche, "reservataires[%d].ville" % index, observers=['reservataires'])])
        sizer.AddMany([(wx.StaticText(self, -1, "Téléphone :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), AutoPhoneCtrl(self, database.creche, "reservataires[%d].telephone" % index, observers=['reservataires'])])
        sizer.AddMany([(wx.StaticText(self, -1, "E-mail :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, database.creche, "reservataires[%d].email" % index, observers=['reservataires'])])
        
        # sizer.AddMany([(wx.StaticText(self, -1, "Options :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, database.creche, "reservataires[%d].options" % index, [("Congé", 0), ("Accueil non facturé", ACCUEIL_NON_FACTURE), ("Pas de facture pendant ce mois", MOIS_SANS_FACTURE), ("Uniquement supplément/déduction", MOIS_FACTURE_UNIQUEMENT_HEURES_SUPP)], observers=['reservataires']), 0, wx.EXPAND)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        if config.readonly:
            delbutton.Disable()
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.OnSuppressionReservataire, delbutton)
        self.reservataires_sizer.Add(sizer)

    def RemoveLine(self):
        index = len(self.reservataires_sizer.GetChildren()) - 1
        sizer = self.reservataires_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.reservataires_sizer.Detach(index)

    def OnAjoutReservataire(self, _):
        counters['reservataires'] += 1
        history.Append(Delete(database.creche.reservataires, -1))
        database.creche.reservataires.append(Reservataire(creche=database.creche))
        self.AjouteLigneReservataire(len(database.creche.reservataires) - 1)
        self.sizer.FitInside(self)
        self.sizer.Layout()

    def OnSuppressionReservataire(self, event):
        counters['reservataires'] += 1
        index = event.GetEventObject().index
        reservataire = database.creche.reservataires[index]
        history.Append(Insert(database.creche.reservataires, index, reservataire))
        self.RemoveLine()
        database.creche.reservataires.remove(reservataire)
        self.sizer.FitInside(self)
        self.sizer.Layout()
        self.UpdateContents()


class ParametersPanel(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.FlexGridSizer(0, 2, 5, 5)
        sizer.AddGrowableCol(1, 1)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.ouverture_cb = AutoTimeCtrl(self, database.creche, "ouverture")
        self.fermeture_cb = AutoTimeCtrl(self, database.creche, "fermeture")
        self.ouverture_cb.check_function = self.ouverture_check
        self.fermeture_cb.check_function = self.fermeture_check
        # self.Bind(wx.EVT_CHOICE, self.onOuverture, self.ouverture_cb)
        # self.Bind(wx.EVT_CHOICE, self.onOuverture, self.fermeture_cb)
        sizer2.AddMany([(self.ouverture_cb, 1, wx.EXPAND), (self.ouverture_cb.spin, 0, wx.EXPAND), (wx.StaticText(self, -1, "-"), 0, wx.RIGHT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10), (self.fermeture_cb, 1, wx.EXPAND), (self.fermeture_cb.spin, 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, "Heures d'ouverture :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), (sizer2, 0, wx.EXPAND)])
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.affichage_min_cb = AutoTimeCtrl(self, database.creche, "affichage_min")
        self.affichage_max_cb = AutoTimeCtrl(self, database.creche, "affichage_max")
        self.Bind(wx.EVT_CHOICE, self.onAffichage, self.affichage_min_cb)
        self.Bind(wx.EVT_CHOICE, self.onAffichage, self.affichage_max_cb)
        sizer2.AddMany([(self.affichage_min_cb, 1, wx.EXPAND), (self.affichage_min_cb.spin, 0, wx.EXPAND), (wx.StaticText(self, -1, "-"), 0, wx.RIGHT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10), (self.affichage_max_cb, 1, wx.EXPAND), (self.affichage_max_cb.spin, 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, "Heures affichées sur le planning :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), (sizer2, 0, wx.EXPAND)])

        def CreateLabelTuple(text):
            return wx.StaticText(self, -1, text), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10

        def CreateRedemarrageSizer(widget):
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.AddMany([(widget, 1, wx.EXPAND), (wx.StaticText(self, -1, "(prise en compte après redémarrage)"), 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)])
            return sizer

        sizer.AddMany([CreateLabelTuple("Mode de saisie des présences :"), (CreateRedemarrageSizer(AutoChoiceCtrl(self, database.creche, "mode_saisie_planning", items=modes_saisie_planning)), 0, wx.EXPAND)])
        if database.creche.mode_saisie_planning == SAISIE_HORAIRE:
            sizer.AddMany([CreateLabelTuple("Granularité du planning :"), (AutoChoiceCtrl(self, database.creche, "granularite", [("5 minutes", 5), ("10 minutes", 10), ("1/4 heure", 15), ("1/2 heure", 30), ("1 heure", 60)]), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Ordre d'affichage dans les inscriptions :"),
                       (AutoChoiceCtrl(self, database.creche, "tri_inscriptions", [("Par prénom", TRI_PRENOM), ("Par nom", TRI_NOM), ("Par nom sans séparation des anciens", TRI_NOM | TRI_SANS_SEPARATION)]), 0, wx.EXPAND)])
        ordre_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ordre_sizer.AddMany([(AutoChoiceCtrl(self, database.creche, "tri_planning", items=[("Par prénom", TRI_PRENOM), ("Par nom", TRI_NOM)], mask=255), 1, wx.EXPAND),
                             (AutoCheckBox(self, database.creche, "tri_planning", value=TRI_GROUPE, label="Séparation par groupes"), 0, wx.EXPAND | wx.LEFT, 10),
                             (AutoCheckBox(self, database.creche, "tri_planning", value=TRI_LIGNES_CAHIER, label="Lignes horizontales"), 0, wx.EXPAND | wx.LEFT, 10),
                             ])
        sizer.AddMany([CreateLabelTuple("Ordre d'affichage sur le planning :"), (ordre_sizer, 1, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Préinscriptions :"),
                       (AutoChoiceCtrl(self, database.creche, "preinscriptions", items=modes_gestion_standard), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Présences supplémentaires :"),
                       (AutoChoiceCtrl(self, database.creche, "presences_supplementaires", items=modes_gestion_standard), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Modes d'inscription :"),
                       (AutoChoiceCtrl(self, database.creche, "modes_inscription", items=modes_inscription), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Mode d'accueil par défaut :"),
                       (AutoChoiceCtrl(self, database.creche, "mode_accueil_defaut", items=ModeAccueilItems), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Gestion des plannings des salariés :"),
                       (CreateRedemarrageSizer(AutoChoiceCtrl(self, database.creche, "gestion_plannings_salaries", items=modes_gestion_plannings_salaries)), 0, wx.EXPAND)])
        mode_facturation_choice = AutoChoiceCtrl(self, database.creche, "mode_facturation", modes_facturation)
        self.Bind(wx.EVT_CHOICE, self.onModeFacturationChoice, mode_facturation_choice)
        sizer.AddMany([CreateLabelTuple("Mode de facturation :"), (mode_facturation_choice, 1, wx.EXPAND)])
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.AddMany([
            (AutoChoiceCtrl(self, database.creche, "repartition", modes_mensualisation), 1, wx.EXPAND | wx.RIGHT, 5),
            CreateLabelTuple("Prorata en cas d'arrivée ou de départ en cours de mois"),
            (AutoChoiceCtrl(self, database.creche, "prorata", modes_prorata), 1, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(""), (sizer2, 1, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(""),
                       (AutoChoiceCtrl(self, database.creche, "temps_facturation", temps_facturation), 1, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Revenus pris en compte :"),
                       (AutoChoiceCtrl(self, database.creche, "periode_revenus", [("Année N-2", REVENUS_YM2), ("CAFPRO", REVENUS_CAFPRO)]), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Ordre des factures :"),
                       (AutoChoiceCtrl(self, database.creche, "tri_factures", [("Par prénom de l'enfant", TRI_PRENOM), ("Par nom de l'enfant", TRI_NOM), ("Par nom des parents", TRI_NOM_PARENTS)]), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Clôture des factures :"),
                       (AutoChoiceCtrl(self, database.creche, "cloture_facturation", [("Désactivée", CLOTURE_FACTURES_OFF), ("Activée", CLOTURE_FACTURES_SIMPLE), ("Activée avec contrôle des factures précédentes", CLOTURE_FACTURES_AVEC_CONTROLE)]), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Mode de facturation des périodes d'adaptation :"), (AutoChoiceCtrl(self, database.creche, "facturation_periode_adaptation", TypeModesFacturationItems), 1, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Mode d'arrondi des horaires des enfants :"), (AutoChoiceCtrl(self, database.creche, "arrondi_heures", modes_arrondi_horaires_enfants), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Mode d'arrondi de la facturation des enfants :"), (AutoChoiceCtrl(self, database.creche, "arrondi_facturation", modes_arrondi_factures_enfants), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Mode d'arrondi de la facturation des enfants pendant les périodes d'adaptation :"), (AutoChoiceCtrl(self, database.creche, "arrondi_facturation_periode_adaptation", modes_arrondi_factures_enfants), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Mode d'arrondi des horaires des salariés :"), (AutoChoiceCtrl(self, database.creche, "arrondi_heures_salaries", modes_arrondi_horaires_salaries), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Mode d'arrondi des semaines des contrats :"), (AutoChoiceCtrl(self, database.creche, "arrondi_semaines", modes_arrondi_semaines_periodes), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Mode d'arrondi de la mensualisation en heures :"), (AutoChoiceCtrl(self, database.creche, "arrondi_mensualisation", modes_arrondi_mensualisation), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Mode d'arrondi de la mensualisation en euros :"), (AutoChoiceCtrl(self, database.creche, "arrondi_mensualisation_euros", [("Pas d'arrondi", SANS_ARRONDI), ("Arrondi à l'euro le plus proche", ARRONDI_EURO_PLUS_PROCHE)]), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Gestion des absences prévues au contrat :"), (AutoChoiceCtrl(self, database.creche, "conges_inscription", modes_absences_prevues_au_contrat), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Déduction des jours fériés et absences prévues au contrat :"), (AutoChoiceCtrl(self, database.creche, "facturation_jours_feries", modes_facturation_absences), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Tarification des activités :"), (AutoChoiceCtrl(self, database.creche, "tarification_activites", [("Non géré", ACTIVITES_NON_FACTUREES), ("A la journée", ACTIVITES_FACTUREES_JOURNEE), ("Période d'adaptation, à la journée", ACTIVITES_FACTUREES_JOURNEE_PERIODE_ADAPTATION)]), 0, wx.EXPAND)])
        if database.creche.nom == "LA VOLIERE":
            sizer.AddMany([CreateLabelTuple("Coût journalier :"), (AutoNumericCtrl(self, database.creche, "cout_journalier", min=0, precision=2), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Traitement des absences pour maladie :"), (AutoChoiceCtrl(self, database.creche, "traitement_maladie", [("Avec carence en jours ouvrés", DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_OUVRES), ("Avec carence en jours calendaires", DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CALENDAIRES), ("Avec carence en jours consécutifs", DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CONSECUTIFS), ("Sans carence", DEDUCTION_MALADIE_SANS_CARENCE)]), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Durée de la carence :"), (AutoNumericCtrl(self, database.creche, "minimum_maladie", min=0, precision=0), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Traitement des absences pour hospitalisation :"), (AutoChoiceCtrl(self, database.creche, "gestion_maladie_hospitalisation", items=modes_gestion_standard), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Traitement des absences pour maladie sans justificatif :"), (AutoChoiceCtrl(self, database.creche, "gestion_maladie_sans_justificatif", items=modes_gestion_standard), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Traitement des absences non prévenues :"), (AutoChoiceCtrl(self, database.creche, "gestion_absences_non_prevenues", items=modes_gestion_standard), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Traitement des préavis de congés :"), (AutoChoiceCtrl(self, database.creche, "gestion_preavis_conges", items=modes_gestion_standard), 0, wx.EXPAND)])
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.AddMany([(AutoChoiceCtrl(self, database.creche, "gestion_depart_anticipe", items=modes_gestion_standard), 1, wx.EXPAND), (wx.StaticText(self, -1, "Régularisation de la facturation en fin de contrat :"), 0, wx.RIGHT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, database.creche, "regularisation_fin_contrat", [("Gérée", True), ("Non gérée", False)]), 1, wx.EXPAND), (wx.StaticText(self, -1, "Régularisation pour les congés non pris :"), 0, wx.RIGHT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, database.creche, "regularisation_conges_non_pris", [("Gérée", True), ("Non gérée", False)]), 1, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Traitement des départs anticipés :"), (sizer3, 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Changement de groupe :"), (AutoChoiceCtrl(self, database.creche, "changement_groupe_auto", [("Manuel", False), ("Automatique", True)]), 0, wx.EXPAND)])

        alertes_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for label, value in AlertesItems:
            alertes_sizer.Add(AutoCheckBox(self, database.creche, "masque_alertes", value=value, label=label), 0, wx.EXPAND | wx.RIGHT, 10)
        sizer.AddMany([CreateLabelTuple("Alertes :"), alertes_sizer])

        sizer.AddMany([CreateLabelTuple("Age maximum des enfants :"), (AutoNumericCtrl(self, database.creche, "age_maximum", min=0, max=5, precision=0), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Alerte dépassement capacité dans les plannings :"), (AutoChoiceCtrl(self, database.creche, "alerte_depassement_planning", [("Activée", True), ("Désactivée", False)]), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Seuil d'alerte dépassement capacité inscriptions (jours) :"), (AutoNumericCtrl(self, database.creche, "seuil_alerte_inscription", min=0, max=100, precision=0), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple("Allergies :"), (CreateRedemarrageSizer(AutoTextCtrl(self, database.creche, "allergies")), 0, wx.EXPAND)])
        self.sizer.Add(sizer, 0, wx.EXPAND | wx.ALL, 5)

        salaries_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Salariés"), wx.VERTICAL)
        salaries_sizer.AddMany([CreateLabelTuple("Nombre de jours de congés payés :"), (AutoNumericCtrl(self, database.creche, "conges_payes_salaries", min=0, precision=0), 0, wx.EXPAND)])
        salaries_sizer.AddMany([CreateLabelTuple("Nombre de jours de congés supplémentaires :"), (AutoNumericCtrl(self, database.creche, "conges_supplementaires_salaries", min=0, precision=0), 0, wx.EXPAND)])
        self.sizer.Add(salaries_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.plages_box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Plages horaires spéciales"), wx.VERTICAL)
        self.plages_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, plage in enumerate(database.creche.plages_horaires):
            self.AjouteLignePlageHoraire(i)
        self.plages_box_sizer.Add(self.plages_sizer, 0, wx.EXPAND | wx.ALL, 5)
        button_add = wx.Button(self, -1, "Nouvelle plage horaire")
        if config.readonly:
            button_add.Disable()        
        self.plages_box_sizer.Add(button_add, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutPlageHoraire, button_add)
        self.sizer.Add(self.plages_box_sizer, 0, wx.EXPAND | wx.ALL, 5)
                
        self.tarifs_box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Tarifs spéciaux"), wx.VERTICAL)
        self.tarifs_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, tarif in enumerate(database.creche.tarifs_speciaux):
            self.AjouteLigneTarif(i)
        self.tarifs_box_sizer.Add(self.tarifs_sizer, 0, wx.EXPAND | wx.ALL, 5)
        button_add = wx.Button(self, -1, "Nouveau tarif spécial")
        if config.readonly:
            button_add.Disable()        
        self.tarifs_box_sizer.Add(button_add, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutTarif, button_add)
        self.sizer.Add(self.tarifs_box_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(self.sizer)

    def AjouteLignePlageHoraire(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        debut_ctrl = AutoTimeCtrl(self, database.creche, "plages_horaires[%d].debut" % index, observers=['plages'])
        fin_ctrl = AutoTimeCtrl(self, database.creche, "plages_horaires[%d].fin" % index, observers=['plages']) 
        sizer.AddMany([(wx.StaticText(self, -1, "Plage horaire :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (debut_ctrl, 1, wx.EXPAND), (debut_ctrl.spin, 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, "-"), 0, wx.RIGHT | wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10), (fin_ctrl, 1, wx.EXPAND), (fin_ctrl.spin, 0, wx.EXPAND)])
        sizer.AddMany([(AutoChoiceCtrl(self, database.creche, "plages_horaires[%d].flags" % index, items=[("Fermeture", PLAGE_FERMETURE), ("Insécable", PLAGE_INSECABLE)], observers=['plages']), 1, wx.LEFT | wx.EXPAND, 5)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnSuppressionPlageHoraire, delbutton)
        self.plages_sizer.Add(sizer, 0, wx.EXPAND | wx.BOTTOM, 5)
        if config.readonly:
            delbutton.Disable()

    def SupprimeLignePlageHoraire(self):
        index = len(self.plages_sizer.GetChildren()) - 1
        sizer = self.plages_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.plages_sizer.Detach(index)

    def OnAjoutPlageHoraire(self, _):
        counters['plages'] += 1
        history.Append(Delete(database.creche.plages_horaires, -1))
        database.creche.plages_horaires.append(PlageHoraire())
        self.AjouteLignePlageHoraire(len(database.creche.plages_horaires) - 1)
        self.sizer.FitInside(self)

    def OnSuppressionPlageHoraire(self, event):
        counters['plages'] += 1
        index = event.GetEventObject().index
        history.Append(Insert(database.creche.plages_horaires, index, database.creche.plages_horaires[index]))
        self.SupprimeLignePlageHoraire()
        del database.creche.plages_horaires[index]
        self.sizer.FitInside(self)
        self.UpdateContents()
    
    def AjouteLigneTarif(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, "Libellé :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, database.creche, "tarifs_speciaux[%d].label" % index, observers=['tarifs']), 1, wx.RIGHT | wx.EXPAND, 5)])
        sizer.AddMany([(AutoChoiceCtrl(self, database.creche, "tarifs_speciaux[%d].type" % index, items=TypeTarifsSpeciauxItems), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, "Valeur :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoNumericCtrl(self, database.creche, "tarifs_speciaux[%d].valeur" % index, precision=2), 1, wx.RIGHT | wx.EXPAND, 5)])
        sizer.AddMany([(AutoChoiceCtrl(self, database.creche, "tarifs_speciaux[%d].unite" % index, items=UniteTarifsSpeciauxItems), 1, wx.RIGHT | wx.EXPAND, 5)])
        sizer.AddMany([(AutoChoiceCtrl(self, database.creche, "tarifs_speciaux[%d].portee" % index, items=PorteeTarifsSpeciauxItems), 1, wx.EXPAND)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnSuppressionTarif, delbutton)
        self.tarifs_sizer.Add(sizer, 0, wx.EXPAND | wx.BOTTOM, 5)
        if config.readonly:
            delbutton.Disable()

    def SupprimeLigneTarif(self):
        index = len(self.tarifs_sizer.GetChildren()) - 1
        sizer = self.tarifs_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.tarifs_sizer.Detach(index)

    def OnAjoutTarif(self, _):
        counters['tarifs'] += 1
        history.Append(Delete(database.creche.tarifs_speciaux, -1))
        database.creche.tarifs_speciaux.append(TarifSpecial(database.creche))
        self.AjouteLigneTarif(len(database.creche.tarifs_speciaux) - 1)
        self.sizer.FitInside(self)

    def OnSuppressionTarif(self, event):
        counters['tarifs'] += 1
        index = event.GetEventObject().index
        history.Append(Insert(database.creche.tarifs_speciaux, index, database.creche.tarifs_speciaux[index]))
        self.SupprimeLigneTarif()
        del database.creche.tarifs_speciaux[index]
        self.sizer.FitInside(self)
        self.UpdateContents()

    def onModeFacturationChoice(self, event):
        object = event.GetEventObject()
        value = object.GetClientData(object.GetSelection())
        self.GetParent().DisplayTarifHorairePanel(value in (FACTURATION_PAJE, FACTURATION_PAJE_10H, FACTURATION_HORAIRES_REELS))
        self.GetParent().DisplayTauxEffortPanel(value == FACTURATION_PSU_TAUX_PERSONNALISES)
        event.Skip()
            
    def ouverture_check(self, ouverture, a, b):
        return a >= ouverture * 4
    
    def fermeture_check(self, fermeture, a, b):
        return b <= fermeture * 4

    print("TODO Fonction retirée il y a un moment")
    def onOuverture(self, event):
        errors = []
        obj = event.GetEventObject()
        value = event.GetClientData()
        for inscrit in database.creche.inscrits:
            for inscription in inscrit.inscriptions:
                for j, jour in enumerate(inscription.reference):
                    for a, b, v in jour.activites.keys():
                        if not obj.check_function(value, a, b):
                            errors.append((inscrit, jour, " (%s)" % GetPeriodeString(inscription), days[j%7].lower()))
            for j in inscrit.journees.keys():
                jour = inscrit.journees[j]
                for a, b, v in jour.activites.keys():
                    if not obj.check_function(value, a, b):
                        errors.append((inscrit, jour, "", date2str(j)))
                
        if errors:
            message = "Diminuer la période d'ouverture changera les plannings des enfants suivants :\n"
            for inscrit, jour, info, date in errors:
                message += "  %s %s%s le %s\n" % (inscrit.prenom, inscrit.nom, info, date)
            message += "Confirmer ?"
            dlg = wx.MessageDialog(self, message, "Confirmation", wx.OK|wx.CANCEL | wx.ICON_WARNING)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_OK:
                obj.UpdateContents()
                return
        obj.AutoChange(value)
# TODO
#        for inscrit, jour, info, date in errors:
#            for i in range(0, int(database.creche.ouverture*4)) + range(int(database.creche.fermeture*4), TAILLE_TABLE_ACTIVITES):
#                jour.values[i] = 0
#            jour.save()
        if database.creche.affichage_min > database.creche.ouverture:
            database.creche.affichage_min = database.creche.ouverture
            self.affichage_min_cb.UpdateContents()
        if database.creche.affichage_max < database.creche.fermeture:
            database.creche.affichage_max = database.creche.fermeture
            self.affichage_max_cb.UpdateContents()
            
    def onAffichage(self, event):
        obj = event.GetEventObject()
        value = event.GetClientData()
        error = False
        if obj is self.affichage_min_cb:
            if value > database.creche.ouverture:
                error = True
        else:
            if value < database.creche.fermeture:
                error = True
        if error:
            dlg = wx.MessageDialog(self, "La période d'affichage doit couvrir au moins l'amplitude horaire de la structure !", "Erreur", wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            obj.UpdateContents()
        else:
            obj.AutoChange(value)

    def onPause(self, event):
        obj = event.GetEventObject()
        value = event.GetClientData()
        obj.AutoChange(value)


class TarifHorairePanel(AutoTab, PeriodeMixin):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        PeriodeMixin.__init__(self, "tarifs_horaires")
        self.delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(PeriodeChoice(self, lambda obj: TarifHoraire(database.creche)), 0, wx.TOP | wx.BOTTOM, 5)
        self.addbutton = wx.Button(self, -1, "Ajouter un cas")
        if config.readonly:
            self.addbutton.Disable()
        self.addbutton.index = 0
        self.Bind(wx.EVT_BUTTON, self.OnAdd, self.addbutton)
        self.sizer.Add(self.addbutton, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.LEFT, 5)
        self.controls = []
        self.tarifs_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.tarifs_sizer, 1, wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.LEFT | wx.EXPAND, 5)
        self.SetSizer(self.sizer)
        self.Layout()

    def InternalUpdate(self):
        if sys.platform == 'win32':
            self.Hide()
        self.tarifs_sizer.DeleteWindows()
        del self.controls[:]
        if self.periode is not None and self.periode >= 0:
            self.addbutton.Enable()
            for i, cas in enumerate(database.creche.tarifs_horaires[self.periode].formule):
                self.AjouteLigneTarifHoraire(i, cas[0], cas[1])
        else:
            self.addbutton.Disable()
        if sys.platform == 'win32':
            self.Show()

    def UpdateContents(self):
        self.SetInstance(database.creche)
        self.InternalUpdate()

    def SetPeriode(self, periode):
        PeriodeMixin.SetPeriode(self, periode)
        self.InternalUpdate()
        
    def AjouteLigneTarifHoraire(self, index, condition="", taux=0.0):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(10)
        cas = wx.StaticText(self, -1, "[Cas %d]" % (index+1))
        cas.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(cas, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        condition_ctrl = wx.TextCtrl(self, -1, condition)
        condition_ctrl.index = index
        sizer1.AddMany([(wx.StaticText(self, -1, "Condition :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (condition_ctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)])
        taux_ctrl = wx.TextCtrl(self, -1, str(taux), size=(200, -1))
        taux_ctrl.index = index
        sizer1.AddMany([(wx.StaticText(self, -1, "Tarif horaire :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (taux_ctrl, 0, wx.ALIGN_CENTER_VERTICAL, 5)])
        if not config.readonly:
            delbutton = wx.BitmapButton(self, -1, self.delbmp)
            delbutton.index = index
            sizer1.Add(delbutton, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
            self.Bind(wx.EVT_BUTTON, self.OnRemove, delbutton)
        sizer.Add(sizer1, 0, wx.EXPAND)
        if not config.readonly:
            addbutton = wx.Button(self, -1, "Ajouter un cas")
            addbutton.index = index+1
            sizer.Add(addbutton, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP, 5)
            self.Bind(wx.EVT_BUTTON, self.OnAdd, addbutton)
            self.controls.insert(index, (cas, condition_ctrl, taux_ctrl, delbutton, addbutton))
            self.Bind(wx.EVT_TEXT, self.OnConditionChange, condition_ctrl)
            self.Bind(wx.EVT_TEXT, self.OnTauxChange, taux_ctrl)
        else:
            condition_ctrl.Disable()
            taux_ctrl.Disable()
        self.tarifs_sizer.Insert(index, sizer, 0, wx.EXPAND | wx.BOTTOM, 5)
        self.sizer.FitInside(self)

    def OnAdd(self, event):
        object = event.GetEventObject()
        database.creche.tarifs_horaires[self.periode].formule.insert(object.index, ["", 0.0, TARIF_HORAIRE_UNITE_EUROS_PAR_HEURE])
        database.creche.tarifs_horaires[self.periode].UpdateFormule(changed=False)
        self.AjouteLigneTarifHoraire(object.index)
        for i in range(object.index+1, len(self.controls)):
            self.controls[i][0].SetLabel("[Cas %d]" % (i+1))
            for control in self.controls[i][1:]:
                control.index += 1
        self.sizer.FitInside(self)
        history.Append(None)
    
    def OnRemove(self, event):
        index = event.GetEventObject().index
        sizer = self.tarifs_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.tarifs_sizer.Detach(index)
        del self.controls[index]
        del database.creche.tarifs_horaires[self.periode].formule[index]
        database.creche.tarifs_horaires[self.periode].UpdateFormule()
        for i in range(index, len(self.controls)):
            self.controls[i][0].SetLabel("[Cas %d]" % (i+1))
            for control in self.controls[i][1:]:
                control.index -= 1
        self.sizer.FitInside(self)
        history.Append(None)
    
    def OnConditionChange(self, event):
        object = event.GetEventObject()
        database.creche.tarifs_horaires[self.periode].formule[object.index][0] = object.GetValue()
        database.creche.tarifs_horaires[self.periode].UpdateFormule()
        if database.creche.tarifs_horaires[self.periode].CheckFormule(object.index):
            object.SetBackgroundColour(wx.WHITE)
        else:
            object.SetBackgroundColour(wx.RED)
        object.Refresh()
        history.Append(None)
        
    def OnTauxChange(self, event):
        object = event.GetEventObject()
        database.creche.tarifs_horaires[self.periode].formule[object.index][1] = float(object.GetValue())
        database.creche.tarifs_horaires[self.periode].UpdateFormule()
        history.Append(None)


class TauxEffortPanel(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        self.delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        addbutton = wx.Button(self, -1, "Ajouter un cas")
        addbutton.index = 0
        self.Bind(wx.EVT_BUTTON, self.OnAdd, addbutton)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(addbutton, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP, 5)
        self.controls = []
        if database.creche.formule_taux_effort:
            for i, cas in enumerate(database.creche.formule_taux_effort):
                self.AjouteLigneTauxEffort(i, cas[0], cas[1])
        self.SetSizer(self.sizer)
        self.Layout()
        
    def AjouteLigneTauxEffort(self, index, condition="", taux=0.0):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(10)
        cas = wx.StaticText(self, -1, "[Cas %d]" % (index+1))
        cas.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(cas, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
        condition_ctrl = wx.TextCtrl(self, -1, condition)
        condition_ctrl.index = index
        sizer1.AddMany([(wx.StaticText(self, -1, "Condition :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (condition_ctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)])
        taux_ctrl = wx.TextCtrl(self, -1, str(taux))
        taux_ctrl.index = index
        sizer1.AddMany([(wx.StaticText(self, -1, "Taux d'effort :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (taux_ctrl, 0, wx.ALIGN_CENTER_VERTICAL, 5)])
        if not config.readonly:
            delbutton = wx.BitmapButton(self, -1, self.delbmp)
            delbutton.index = index
            sizer1.Add(delbutton, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
            self.Bind(wx.EVT_BUTTON, self.OnRemove, delbutton)
        sizer.Add(sizer1, 0, wx.EXPAND)
        if not config.readonly:
            addbutton = wx.Button(self, -1, "Ajouter un cas")
            addbutton.index = index+1
            sizer.Add(addbutton, 0, wx.ALIGN_CENTER_VERTICAL | wx.TOP, 5)
            self.Bind(wx.EVT_BUTTON, self.OnAdd, addbutton)
            self.controls.insert(index, (cas, condition_ctrl, taux_ctrl, delbutton, addbutton))
            self.Bind(wx.EVT_TEXT, self.OnConditionChange, condition_ctrl)
            self.Bind(wx.EVT_TEXT, self.OnTauxChange, taux_ctrl)
        self.sizer.Insert(index+1, sizer, 0, wx.EXPAND | wx.BOTTOM, 5)         

    def OnAdd(self, event):
        object = event.GetEventObject()
        self.AjouteLigneTauxEffort(object.index)
        if database.creche.formule_taux_effort is None:
            database.creche.formule_taux_effort = [["", 0.0]]
        else:
            database.creche.formule_taux_effort.insert(object.index, ["", 0.0])
        database.creche.UpdateFormuleTauxEffort()
        for i in range(object.index+1, len(self.controls)):
            self.controls[i][0].SetLabel("[Cas %d]" % (i+1))
            for control in self.controls[i][1:]:
                control.index += 1
        self.sizer.FitInside(self)
        history.Append(None)
    
    def OnRemove(self, event):
        index = event.GetEventObject().index
        sizer = self.sizer.GetItem(index+1)
        sizer.DeleteWindows()
        self.sizer.Detach(index+1)
        del self.controls[index]
        if len(database.creche.formule_taux_effort) == 1:
            database.creche.formule_taux_effort = None
        else:
            del database.creche.formule_taux_effort[index]
        database.creche.UpdateFormuleTauxEffort()
        for i in range(index, len(self.controls)):
            self.controls[i][0].SetLabel("[Cas %d]" % (i+1))
            for control in self.controls[i][1:]:
                control.index -= 1
        self.sizer.FitInside(self)
        history.Append(None)
    
    def OnConditionChange(self, event):
        object = event.GetEventObject()
        database.creche.formule_taux_effort[object.index][0] = object.GetValue()
        database.creche.UpdateFormuleTauxEffort()
        if database.creche.CheckFormuleTauxEffort(object.index):
            object.SetBackgroundColour(wx.WHITE)
        else:
            object.SetBackgroundColour(wx.RED)
        object.Refresh()
        history.Append(None)
        
    def OnTauxChange(self, event):
        object = event.GetEventObject()
        database.creche.formule_taux_effort[object.index][1] = float(object.GetValue())
        database.creche.UpdateFormuleTauxEffort()
        history.Append(None)    


class UsersTab(AutoTab):
    def __init__(self, parent):
        global delbmp
        delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.users_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, user in enumerate(database.creche.users):
            self.AjouteLigneUtilisateur(i)
        self.sizer.Add(self.users_sizer, 0, wx.EXPAND | wx.ALL, 5)
        button_add = wx.Button(self, -1, "Nouvel utilisateur")
        if config.readonly:
            button_add.Disable()      
        self.sizer.Add(button_add, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.AddUser, button_add)
        self.SetSizer(self.sizer)

    def UpdateContents(self):
        for i in range(len(self.users_sizer.GetChildren()), len(database.creche.users)):
            self.AjouteLigneUtilisateur(i)
        for i in range(len(database.creche.users), len(self.users_sizer.GetChildren())):
            self.RemoveLine()
        self.sizer.Layout()
        AutoTab.UpdateContents(self)

    def OnPasswordChange(self, event):
        obj = event.GetEventObject()
        user = database.creche.users[obj.user_index]
        history.Append(Change(user, "password", user.password))
        user.password = bcrypt.hashpw(obj.GetValue().encode("utf-8"), bcrypt.gensalt())

    def AjouteLigneUtilisateur(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, "Login :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), (AutoTextCtrl(self, database.creche, "users[%d].login" % index), 0, wx.ALIGN_CENTER_VERTICAL)])
        password_ctrl = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        password_ctrl.user_index = index
        self.Bind(wx.EVT_TEXT, self.OnPasswordChange, password_ctrl)
        sizer.AddMany([(wx.StaticText(self, -1, "Mot de passe :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), (password_ctrl, 0, wx.ALIGN_CENTER_VERTICAL)])
        profile_choice = AutoChoiceCtrl(self, database.creche, "users[%d].profile" % index, items=TypesProfil)
        profile_choice.index = index
        self.Bind(wx.EVT_CHOICE, self.OnUserProfileModified, profile_choice)
        sizer.AddMany([(wx.StaticText(self, -1, "Profil :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), profile_choice])
        delbutton = wx.BitmapButton(self, -1, delbmp, style=wx.NO_BORDER)
        if config.readonly:
            delbutton.Disable()              
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.RemoveUser, delbutton)
        self.users_sizer.Add(sizer)

    def RemoveLine(self):
        index = len(self.users_sizer.GetChildren()) - 1
        sizer = self.users_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.users_sizer.Detach(index)

    def AddUser(self, _):
        history.Append(Delete(database.creche.users, -1))
        database.creche.users.append(User(creche=database.creche))
        self.AjouteLigneUtilisateur(len(database.creche.users) - 1)
        self.sizer.Layout()

    def RemoveUser(self, event):
        index = event.GetEventObject().index
        nb_admins = len([user for i, user in enumerate(database.creche.users) if (i != index and (user.profile & PROFIL_ADMIN))])
        if len(database.creche.users) == 1 or nb_admins > 0:
            user = database.creche.users[index]
            history.Append(Insert(database.creche.users, index, user))
            self.RemoveLine()
            database.creche.users.remove(user)
            self.sizer.Layout()
            self.UpdateContents()
        else:
            dlg = wx.MessageDialog(self, "Il faut au moins un administrateur", "Message", wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

    def OnUserProfileModified(self, event):
        obj = event.GetEventObject()
        index = obj.index
        if (database.creche.users[index].profile & PROFIL_ADMIN) and not (event.GetClientData() & PROFIL_ADMIN):
            nb_admins = len([user for i, user in enumerate(database.creche.users) if (i != index and (user.profile & PROFIL_ADMIN))])
            if nb_admins == 0:
                dlg = wx.MessageDialog(self, "Il faut au moins un administrateur", "Message", wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                event.Skip(False)
                obj.SetSelection(0) # PROFIL_ALL
            else:
                event.Skip(True)
        else:
            event.Skip(True)


class ParametresNotebook(wx.Notebook):
    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, style=wx.LB_DEFAULT)
        self.AddPage(CrecheTab(self), "Structure")
        self.professeurs_tab = ProfesseursTab(self)
        if database.creche.type == TYPE_GARDERIE_PERISCOLAIRE:
            self.AddPage(self.professeurs_tab, "Professeurs")
            self.professeurs_tab_displayed = 1
        else:
            self.professeurs_tab.Show(False)
            self.professeurs_tab_displayed = 0
        self.AddPage(ResponsabilitesTab(self), "Responsabilités")
        if IsTemplateFile("Synthese financiere.ods"):
            self.AddPage(ChargesTab(self), "Charges")
            self.charges_tab_displayed = 1
        else:
            self.charges_tab_displayed = 0
        self.AddPage(CafTab(self), "C.A.F.")
        self.AddPage(JoursFermeturePanel(self), "Fermeture de l'établissement")
        self.AddPage(ActivitesTab(self), "Couleurs / Activités")
        self.AddPage(ParametersPanel(self), "Paramètres")
        self.tarif_horaire_panel = TarifHorairePanel(self)
        if database.creche.mode_facturation in (FACTURATION_PAJE, FACTURATION_PAJE_10H, FACTURATION_HORAIRES_REELS):
            self.AddPage(self.tarif_horaire_panel, "Tarif horaire")
            self.tarif_horaire_panel_displayed = 1
        else:
            self.tarif_horaire_panel.Show(False)
            self.tarif_horaire_panel_displayed = 0
        self.taux_effort_panel = TauxEffortPanel(self)
        if database.creche.mode_facturation == FACTURATION_PSU_TAUX_PERSONNALISES:
            self.AddPage(self.taux_effort_panel, "Taux d'effort")
            self.taux_effort_panel_displayed = 1
        else:
            self.taux_effort_panel.Show(False)
            self.taux_effort_panel_displayed = 0
        if not config.readonly:
            self.AddPage(UsersTab(self), "Utilisateurs et mots de passe")
        if config.options & RESERVATAIRES:
            self.AddPage(ReservatairesTab(self), "Réservataires")
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    def OnPageChanged(self, event):
        page = self.GetPage(event.GetSelection())
        page.UpdateContents()
        event.Skip()

    def UpdateContents(self):
        page = self.GetCurrentPage()
        page.UpdateContents()
        
    def DisplayTarifHorairePanel(self, enable):
        if enable == self.tarif_horaire_panel_displayed:
            return
        else:
            self.tarif_horaire_panel.Show(enable)
            tab_index = 7 + self.professeurs_tab_displayed + self.charges_tab_displayed
            if enable:
                self.InsertPage(tab_index, self.tarif_horaire_panel, "Tarif horaire")
            else:
                self.RemovePage(tab_index)

        self.tarif_horaire_panel_displayed = enable
        self.Layout()
        
    def DisplayTauxEffortPanel(self, enable):
        if enable == self.taux_effort_panel_displayed:
            return
        else:
            self.taux_effort_panel.Show(enable)
            tab_index = 7 + self.professeurs_tab_displayed + self.charges_tab_displayed + self.tarif_horaire_panel_displayed
            if enable:
                self.InsertPage(tab_index, self.taux_effort_panel, "Taux d'effort")
            else:
                self.RemovePage(tab_index)

        self.taux_effort_panel_displayed = enable
        self.Layout()
        
    def DisplayProfesseursTab(self, enable):
        if enable == self.professeurs_tab_displayed:
            return
        else:
            self.professeurs_tab.Show(enable)
            if enable:
                self.InsertPage(2, self.professeurs_tab, "Professeurs")
            else:
                self.RemovePage(2)

        self.professeurs_tab_displayed = enable
        self.Layout()


class ConfigurationPanel(GPanel):
    name = "Configuration"
    bitmap = GetBitmapFile("configuration.png")
    profil = PROFIL_ADMIN

    def __init__(self, parent):
        GPanel.__init__(self, parent, "Configuration")
        self.notebook = ParametresNotebook(self)
        self.sizer.Add(self.notebook, 1, wx.EXPAND)

    def UpdateContents(self):
        self.notebook.UpdateContents()

