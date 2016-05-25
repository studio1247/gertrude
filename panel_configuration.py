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

import os.path
import datetime, time
from constants import *
from controls import *
from sqlobjects import *
import wx
from planning import PlanningWidget, NO_BOTTOM_LINE, NO_ICONS, DRAW_VALUES, NO_SCROLL

types_creche = [(u"Parental", TYPE_PARENTAL),
                (u"Familial", TYPE_FAMILIAL),
                (u"Associatif", TYPE_ASSOCIATIF),
                (u"Municipal", TYPE_MUNICIPAL),
                (u"Micro-crèche", TYPE_MICRO_CRECHE),
                (u"Multi-accueil", TYPE_MULTI_ACCUEIL),
                (u"Assistante maternelle", TYPE_ASSISTANTE_MATERNELLE),
                (u"Garderie périscolaire", TYPE_GARDERIE_PERISCOLAIRE)
                ]

modes_facturation = [(u"Forfait 10h / jour", FACTURATION_FORFAIT_10H),
                     (u"PSU", FACTURATION_PSU),
                     (u"PSU avec taux d'effort personnalisés", FACTURATION_PSU_TAUX_PERSONNALISES),
                     (u"PAJE (taux horaire spécifique)", FACTURATION_PAJE),
                     (u"Horaires réels", FACTURATION_HORAIRES_REELS),
                     (u"Facturation personnalisée (forfait mensuel)", FACTURATION_FORFAIT_MENSUEL)
                     ]

modes_mensualisation = [(u'Avec mensualisation (sur 12 mois). Uniquement disponible si jours fériés non déduits', REPARTITION_MENSUALISATION_12MOIS),
                        (u'Avec mensualisation (sur la période du contrat)', REPARTITION_MENSUALISATION_CONTRAT),
                        (u'Avec mensualisation (sur la période du contrat), mois incomplets au même tarif', REPARTITION_MENSUALISATION_CONTRAT_DEBUT_FIN_INCLUS),
                        (u'Sans mensualisation', REPARTITION_SANS_MENSUALISATION)
                        ]

modes_facturation_jours_feries = [(u"En semaines (nombre de semaines entré à l'inscription)", JOURS_FERIES_NON_DEDUITS),
                                  (u"En jours (décompte précis des jours de présence sur l'ensemble du contrat)", JOURS_FERIES_DEDUITS_ANNUELLEMENT)
                                  ]

modes_facturation_adaptation = [(u'Facturation normale', PERIODE_ADAPTATION_FACTUREE_NORMALEMENT),
                                (u"Facturation aux horaires réels", PERIODE_ADAPTATION_HORAIRES_REELS),
                                (u"Période d'adaptation gratuite", PERIODE_ADAPTATION_GRATUITE)
                                ]

modes_arrondi_horaires_enfants = [(u"Pas d'arrondi", SANS_ARRONDI),
                                  (u"Arrondi à l'heure", ARRONDI_HEURE),
                                  (u"Arrondi à l'heure avec marge d'1/2heure", ARRONDI_HEURE_MARGE_DEMI_HEURE),
                                  (u"Arrondi à la demi heure", ARRONDI_DEMI_HEURE),
                                  (u"Arrondi des heures d'arrivée et de départ", ARRONDI_HEURE_ARRIVEE_DEPART)
                                  ]

modes_arrondi_factures_enfants = [(u"Pas d'arrondi", SANS_ARRONDI),
                                  (u"Arrondi à l'heure", ARRONDI_HEURE),
                                  (u"Arrondi à la demi heure", ARRONDI_DEMI_HEURE),
                                  (u"Arrondi des heures d'arrivée et de départ", ARRONDI_HEURE_ARRIVEE_DEPART)
                                  ]

modes_arrondi_horaires_salaries = [(u"Pas d'arrondi", SANS_ARRONDI),
                                   (u"Arrondi à l'heure", ARRONDI_HEURE),
                                   (u"Arrondi des heures d'arrivée et de départ", ARRONDI_HEURE_ARRIVEE_DEPART)
                                   ]

temps_facturation = [(u"Fin de mois", FACTURATION_FIN_MOIS),
                     (u"Début de mois : contrat mois + réalisé mois-1", FACTURATION_DEBUT_MOIS_CONTRAT),
                     (u"Début de mois : prévisionnel mois + réalisé mois-1", FACTURATION_DEBUT_MOIS_PREVISIONNEL),
                     ]

modes_saisie_planning = [(u"A partir de l'interface planning (recommandé)", SAISIE_HORAIRE),
                         (u"En volume horaire par semaine", SAISIE_HEURES_SEMAINE),
                         (u"En jours par semaine", SAISIE_JOURS_SEMAINE),
                         ]

modes_inscription = [(u'Crèche à plein-temps uniquement', MODE_5_5),
                     (u'Tous modes', MODE_5_5+MODE_4_5 | MODE_3_5 | MODE_HALTE_GARDERIE),
                     ]

modes_gestion_standard = [(u'Géré', True),
                          (u'Non géré', False)
                          ]


class CrecheTab(AutoTab):
    def __init__(self, parent):
        global delbmp
        delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        grid_sizer = wx.FlexGridSizer(0, 2, 5, 5)
        grid_sizer.AddGrowableCol(1, 1)
        grid_sizer.AddMany([wx.StaticText(self, -1, u"Nom de la structure :"), (AutoTextCtrl(self, creche, 'nom'), 0, wx.EXPAND)])
        grid_sizer.AddMany([wx.StaticText(self, -1, u"Adresse :"), (AutoTextCtrl(self, creche, 'adresse'), 0, wx.EXPAND)])
        grid_sizer.AddMany([wx.StaticText(self, -1, u"Code Postal :"), (AutoNumericCtrl(self, creche, 'code_postal', precision=0), 0, wx.EXPAND)])
        grid_sizer.AddMany([wx.StaticText(self, -1, u"Ville :"), (AutoTextCtrl(self, creche, 'ville'), 0, wx.EXPAND)])
        grid_sizer.AddMany([wx.StaticText(self, -1, u"Téléphone :"), (AutoPhoneCtrl(self, creche, 'telephone'), 0, wx.EXPAND)])
        grid_sizer.AddMany([wx.StaticText(self, -1, u"E-mail :"), (AutoTextCtrl(self, creche, 'email'), 0, wx.EXPAND)])
        grid_sizer.AddMany([wx.StaticText(self, -1, u"Serveur pour l'envoi d'emails :"), (AutoTextCtrl(self, creche, 'smtp_server'), 0, wx.EXPAND)])
        grid_sizer.AddMany([wx.StaticText(self, -1, u"Email de la CAF :"), (AutoTextCtrl(self, creche, 'caf_email'), 0, wx.EXPAND)])
        type_structure_choice = AutoChoiceCtrl(self, creche, 'type', items=types_creche)
        self.Bind(wx.EVT_CHOICE, self.OnChangementTypeStructure, type_structure_choice)
        grid_sizer.AddMany([wx.StaticText(self, -1, u"Type :"), (type_structure_choice, 0, wx.EXPAND)])
        raz_permanences_label = wx.StaticText(self, -1, u"Date remise à zéro des permanences :")
        raz_permanences_ctrl = AutoDateCtrl(self, creche, 'date_raz_permanences')
        self.creche_parentale_widgets = (raz_permanences_label, raz_permanences_ctrl)
        grid_sizer.AddMany([raz_permanences_label, (raz_permanences_ctrl, 0, wx.EXPAND)])
        planning = PlanningWidget(self, None, NO_BOTTOM_LINE | NO_ICONS | DRAW_VALUES | NO_SCROLL)
        planning.SetLines([line for line in creche.tranches_capacite if IsJourSemaineTravaille(line.jour)])
        grid_sizer.AddMany([wx.StaticText(self, -1, u"Capacité :"), (planning, 1, wx.EXPAND)])
        self.sizer.Add(grid_sizer, 0, wx.EXPAND|wx.ALL, 5)
        
        self.sites_box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Sites"), wx.VERTICAL)
        self.sites_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, site in enumerate(creche.sites):
            self.AjouteLigneSite(i)
        self.sites_box_sizer.Add(self.sites_sizer, 0, wx.EXPAND|wx.ALL, 5)
        button_add = wx.Button(self, -1, u"Nouveau site")
        if readonly:
            button_add.Disable()
        self.sites_box_sizer.Add(button_add, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutSite, button_add)
        self.sizer.Add(self.sites_box_sizer, 0, wx.EXPAND|wx.ALL, 5)
        
        self.groupes_box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u"Groupes"), wx.VERTICAL)
        self.groupes_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, groupe in enumerate(creche.groupes):
            self.AjouteLigneGroupe(i)
        self.groupes_box_sizer.Add(self.groupes_sizer, 0, wx.EXPAND|wx.ALL, 5)
        button_add = wx.Button(self, -1, u'Nouveau groupe')
        if readonly:
            button_add.Disable()
        self.groupes_box_sizer.Add(button_add, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutGroupe, button_add)
        self.sizer.Add(self.groupes_box_sizer, 0, wx.EXPAND|wx.ALL, 5)
        
        if config.options & CATEGORIES:
            self.categories_box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u"Catégories"), wx.VERTICAL)
            self.categories_sizer = wx.BoxSizer(wx.VERTICAL)
            for i, categorie in enumerate(creche.categories):
                self.AjouteLigneCategorie(i)
            self.categories_box_sizer.Add(self.categories_sizer, 0, wx.EXPAND|wx.ALL, 5)
            button_add = wx.Button(self, -1, u'Nouvelle catégorie')
            if readonly:
                button_add.Disable()
            self.categories_box_sizer.Add(button_add, 0, wx.ALL, 5)
            self.Bind(wx.EVT_BUTTON, self.OnAjoutCategorie, button_add)
            self.sizer.Add(self.categories_box_sizer, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(self.sizer)

    def UpdateContents(self):
        for i in range(len(self.sites_sizer.GetChildren()), len(creche.sites)):
            self.AjouteLigneSite(i)
        for i in range(len(creche.sites), len(self.sites_sizer.GetChildren())):
            self.SupprimeLigneSite()
        for i in range(len(self.groupes_sizer.GetChildren()), len(creche.groupes)):
            self.AjouteLigneGroupe(i)
        for i in range(len(creche.groupes), len(self.groupes_sizer.GetChildren())):
            self.SupprimeLigneGroupe()
        self.sizer.Layout()
        AutoTab.UpdateContents(self)

    def AjouteLigneSite(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, u'Nom :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, creche, 'sites[%d].nom' % index, observers=['sites']), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Adresse :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, creche, 'sites[%d].adresse' % index), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Code Postal :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoNumericCtrl(self, creche, 'sites[%d].code_postal' % index, precision=0), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Ville :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, creche, 'sites[%d].ville' % index), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Téléphone'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoPhoneCtrl(self, creche, 'sites[%d].telephone' % index), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Capacité'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoNumericCtrl(self, creche, 'sites[%d].capacite' % index, precision=0), 1, wx.EXPAND)])                
        if config.options & GROUPES_SITES:
            sizer.AddMany([(wx.StaticText(self, -1, u'Groupe'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoNumericCtrl(self, creche, 'sites[%d].groupe' % index, precision=0), 1, wx.EXPAND)])                
        if not readonly:
            delbutton = wx.BitmapButton(self, -1, delbmp)
            delbutton.index = index
            sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
            self.Bind(wx.EVT_BUTTON, self.OnSuppressionSite, delbutton)
        self.sites_sizer.Add(sizer, 0, wx.EXPAND|wx.BOTTOM, 5)

    def SupprimeLigneSite(self):
        index = len(self.sites_sizer.GetChildren()) - 1
        sizer = self.sites_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.sites_sizer.Detach(index)

    def OnAjoutSite(self, event):
        counters['sites'] += 1
        history.Append(Delete(creche.sites, -1))
        creche.sites.append(Site())
        self.AjouteLigneSite(len(creche.sites) - 1)
        self.sizer.Layout()

    def OnSuppressionSite(self, event):
        counters['sites'] += 1
        index = event.GetEventObject().index
        history.Append(Insert(creche.sites, index, creche.sites[index]))
        self.SupprimeLigneSite()
        creche.sites[index].delete()
        del creche.sites[index]
        self.sizer.FitInside(self)
        self.UpdateContents()

    def AjouteLigneGroupe(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, u'Nom :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, creche, 'groupes[%d].nom' % index, observers=['groupes']), 1, wx.EXPAND)])
        if creche.changement_groupe_auto:
            sizer.AddMany([(wx.StaticText(self, -1, u'Age maximum :'), 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoNumericCtrl(self, creche, 'groupes[%d].age_maximum' % index, observers=['groupes'], precision=0), 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Ordre :'), 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoNumericCtrl(self, creche, 'groupes[%d].ordre' % index, observers=['groupes'], precision=0), 0, wx.EXPAND)])
        if not readonly:
            delbutton = wx.BitmapButton(self, -1, delbmp)
            delbutton.index = index
            sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
            self.Bind(wx.EVT_BUTTON, self.OnSuppressionGroupe, delbutton)
        self.groupes_sizer.Add(sizer, 0, wx.EXPAND|wx.BOTTOM, 5)

    def SupprimeLigneGroupe(self):
        index = len(self.groupes_sizer.GetChildren()) - 1
        sizer = self.groupes_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.groupes_sizer.Detach(index)

    def OnAjoutGroupe(self, event):
        counters['groupes'] += 1
        history.Append(Delete(creche.groupes, -1))
        if len(creche.groupes) == 0:
            ordre = 0
        else:
            ordre = creche.groupes[-1].ordre + 1
        creche.groupes.append(Groupe(ordre))
        self.AjouteLigneGroupe(len(creche.groupes) - 1)
        self.sizer.FitInside(self)
        self.sizer.Layout()

    def OnSuppressionGroupe(self, event):
        counters['groupes'] += 1
        index = event.GetEventObject().index
        history.Append(Insert(creche.groupes, index, creche.groupes[index]))
        self.SupprimeLigneGroupe()
        creche.groupes[index].delete()
        del creche.groupes[index]
        self.sizer.FitInside(self)
        self.UpdateContents()
        
    def AjouteLigneCategorie(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, u'Nom :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, creche, 'categories[%d].nom' % index, observers=['categories']), 1, wx.EXPAND)])
        if not readonly:
            delbutton = wx.BitmapButton(self, -1, delbmp)
            delbutton.index = index
            sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
            self.Bind(wx.EVT_BUTTON, self.OnSuppressionCategorie, delbutton)
        self.categories_sizer.Add(sizer, 0, wx.EXPAND|wx.BOTTOM, 5)

    def SupprimeLigneCategorie(self):
        index = len(self.categories_sizer.GetChildren()) - 1
        sizer = self.categories_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.categories_sizer.Detach(index)

    def OnAjoutCategorie(self, event):
        counters['categories'] += 1
        history.Append(Delete(creche.categories, -1))
        creche.categories.append(Categorie())
        self.AjouteLigneCategorie(len(creche.categories) - 1)
        self.sizer.FitInside(self)
        self.sizer.Layout()

    def OnSuppressionCategorie(self, event):
        counters['categories'] += 1
        index = event.GetEventObject().index
        history.Append(Insert(creche.categories, index, creche.categories[index]))
        self.SupprimeLigneCategorie()
        creche.categories[index].delete()
        del creche.categories[index]
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
        for professeur in creche.professeurs:
            self.affiche_professeur(professeur)
        self.sizer.Add(self.professeurs_sizer, 0, wx.EXPAND|wx.ALL, 5)
        button_add = wx.Button(self, -1, u'Nouveau professeur')
        self.sizer.Add(button_add, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutProfesseur, button_add)
        self.SetSizer(self.sizer)

    def UpdateContents(self):
        pass

    def affiche_professeur(self, professeur):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, u'Prénom :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoTextCtrl(self, professeur, 'prenom', observers=['professeurs']), 0, wx.ALIGN_CENTER_VERTICAL)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Nom :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoTextCtrl(self, professeur, 'nom', observers=['professeurs']), 0, wx.ALIGN_CENTER_VERTICAL)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Entrée :', size=(50,-1)), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), AutoDateCtrl(self, professeur, 'entree', observers=['professeurs'])])
        sizer.AddMany([(wx.StaticText(self, -1, u'Sortie :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), AutoDateCtrl(self, professeur, 'sortie', observers=['professeurs'])])
        if not readonly:
            delbutton = wx.BitmapButton(self, -1, delbmp, style=wx.NO_BORDER)
            delbutton.professeur, delbutton.sizer = professeur, sizer
            sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
            self.Bind(wx.EVT_BUTTON, self.OnSuppressionProfesseur, delbutton)
        self.professeurs_sizer.Add(sizer)

    def OnAjoutProfesseur(self, event):
        counters['professeurs'] += 1
        history.Append(Delete(creche.professeurs, -1))
        professeur = Professeur()
        creche.professeurs.append(professeur)
        self.affiche_professeur(professeur)        
        self.sizer.FitInside(self)
        
    def OnSuppressionProfesseur(self, event):
        counters['professeurs'] += 1
        obj = event.GetEventObject()
        for i, professeur in enumerate(creche.professeurs):
            if professeur == obj.professeur:
                history.Append(Insert(creche.professeurs, i, professeur))
                sizer = self.professeurs_sizer.GetItem(i)
                sizer.DeleteWindows()
                self.professeurs_sizer.Detach(i)
                professeur.delete()
                del creche.professeurs[i]
                self.sizer.FitInside(self)
                self.Refresh()
                break


class ResponsabilitesTab(AutoTab, PeriodeMixin):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        PeriodeMixin.__init__(self, 'bureaux')
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(PeriodeChoice(self, Bureau), 0, wx.TOP, 5)
        sizer2 = wx.FlexGridSizer(0, 2, 5, 5)
        sizer2.AddGrowableCol(1, 1)
        self.responsables_ctrls = []
        if creche.type == TYPE_MULTI_ACCUEIL:
            self.gerant_ctrl = AutoComboBox(self, None, 'gerant')
            sizer2.AddMany([(wx.StaticText(self, -1, u'Gérant(e) :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.gerant_ctrl, 0, wx.EXPAND)])
            self.directeur_ctrl = AutoComboBox(self, None, 'directeur')        
            sizer2.AddMany([(wx.StaticText(self, -1, u'Directeur(trice) :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.directeur_ctrl, 0, wx.EXPAND)])
            self.directeur_adjoint_ctrl = AutoComboBox(self, None, 'directeur_adjoint')        
            sizer2.AddMany([(wx.StaticText(self, -1, u'Directeur(trice) adjoint(e) :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.directeur_adjoint_ctrl, 0, wx.EXPAND)])
            self.comptable_ctrl = AutoComboBox(self, None, 'comptable')        
            sizer2.AddMany([(wx.StaticText(self, -1, u'Comptable :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.comptable_ctrl, 0, wx.EXPAND)])
            self.secretaire_ctrl = AutoComboBox(self, None, 'secretaire')        
            sizer2.AddMany([(wx.StaticText(self, -1, u'Secrétaire :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.secretaire_ctrl, 0, wx.EXPAND)])
        else:
            self.gerant_ctrl = None
            self.responsables_ctrls.append(AutoComboBox(self, None, 'president'))
            sizer2.AddMany([(wx.StaticText(self, -1, u'Président(e) :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.responsables_ctrls[-1], 0, wx.EXPAND)])
            self.responsables_ctrls.append(AutoComboBox(self, None, 'vice_president'))
            sizer2.AddMany([(wx.StaticText(self, -1, u'Vice président(e) :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.responsables_ctrls[-1], 0, wx.EXPAND)])
            self.responsables_ctrls.append(AutoComboBox(self, None, 'tresorier'))
            sizer2.AddMany([(wx.StaticText(self, -1, u'Trésorier(ère) :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.responsables_ctrls[-1], 0, wx.EXPAND)])
            self.responsables_ctrls.append(AutoComboBox(self, None, 'secretaire'))        
            sizer2.AddMany([(wx.StaticText(self, -1, u'Secrétaire :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.responsables_ctrls[-1], 0, wx.EXPAND)])
            self.directeur_ctrl = AutoComboBox(self, None, 'directeur')        
            sizer2.AddMany([(wx.StaticText(self, -1, u'Directeur(trice) :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.directeur_ctrl, 0, wx.EXPAND)])
        sizer.Add(sizer2, 0, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(sizer)

    def UpdateContents(self):
        self.SetInstance(creche)

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
        for inscrit in GetInscrits(periode.debut, periode.fin):
            for parent in inscrit.famille.parents.values():
                noms.add(GetPrenomNom(parent))
        noms = list(noms)
        noms.sort(cmp=lambda x, y: cmp(x.lower(), y.lower()))
        return noms
    
    def GetNomsSalaries(self, periode):
        noms = []
        for salarie in creche.salaries:
            noms.append(GetPrenomNom(salarie))
        noms.sort(cmp=lambda x,y: cmp(x.lower(), y.lower()))
        return noms

activity_modes = [(u"Normal", 0),
                  (u"Libère une place", MODE_LIBERE_PLACE),
                  (u"Sans horaires", MODE_SANS_HORAIRES),
                  (u"Présence non facturée", MODE_PRESENCE_NON_FACTUREE),
                  (u"Sans horaire, systématique", MODE_SYSTEMATIQUE_SANS_HORAIRES),
                  (u"Permanence", MODE_PERMANENCE)
                  ]

activity_ownership = [(u"Enfants et Salariés", ACTIVITY_OWNER_ALL),
                      (u"Enfants", ACTIVITY_OWNER_ENFANTS),
                      (u"Salariés", ACTIVITY_OWNER_SALARIES)
                      ]


class ActivitesTab(AutoTab):
    def __init__(self, parent):
        global delbmp
        delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        AutoTab.__init__(self, parent)
        self.color_buttons = {}
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u"Temps de présence"), wx.VERTICAL)
        flex_sizer = wx.FlexGridSizer(0, 3, 3, 2)
        flex_sizer.AddGrowableCol(1, 1)
        flex_sizer.AddMany([(wx.StaticText(self, -1, u'Libellé :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), wx.Size(10,10), (AutoTextCtrl(self, creche, 'activites[0].label'), 1, wx.EXPAND)])

        for label, activite, field in ((u"présences", creche.activites[0], "couleur"), (u"présences supplémentaires", creche.activites[0], "couleur_supplement"), (u"présences prévisionnelles", creche.activites[0], "couleur_previsionnel"), (u"absences pour congés", creche.couleurs[VACANCES], "couleur"), (u"absences non prévenues", creche.couleurs[ABSENCE_NON_PREVENUE], "couleur"), (u"absences pour maladie", creche.couleurs[MALADE], "couleur")):
            color_button = wx.Button(self, -1, "", size=(20, 20))            
            r, g, b, a, h = couleur = getattr(activite, field)
            color_button.SetBackgroundColour(wx.Colour(r, g, b))
            self.Bind(wx.EVT_BUTTON, self.OnColorButton, color_button)
            color_button.hash_cb = HashComboBox(self)
            if readonly:
                color_button.Disable()
                color_button.hash_cb.Disable()
            color_button.activite = color_button.hash_cb.activite = activite
            color_button.field = color_button.hash_cb.field = [field]
            self.color_buttons[(activite.value, field)] = color_button
            self.UpdateHash(color_button.hash_cb, couleur)
            self.Bind(wx.EVT_COMBOBOX, self.OnHashChange, color_button.hash_cb)
            flex_sizer.AddMany([(wx.StaticText(self, -1, u'Couleur des %s :' % label), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (color_button, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (color_button.hash_cb, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)])
        box_sizer.Add(flex_sizer, 0, wx.BOTTOM, 5)
        button = wx.Button(self, -1, u'Rétablir les couleurs par défaut')
        self.Bind(wx.EVT_BUTTON, self.OnCouleursDefaut, button)
        box_sizer.Add(button, 0, wx.ALL, 5)
        self.sizer.Add(box_sizer, 0, wx.ALL|wx.EXPAND, 5)

        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Activités'), wx.VERTICAL)
        self.activites_sizer = wx.BoxSizer(wx.VERTICAL)
        for activity in creche.activites.values():
            if activity.value > 0:
                self.AjouteLigneActivite(activity)
        box_sizer.Add(self.activites_sizer, 0, wx.EXPAND|wx.ALL, 5)
        button_add = wx.Button(self, -1, u'Nouvelle activité')
        box_sizer.Add(button_add, 0, wx.ALL, 5)
        if readonly:
            button.Disable()
            button_add.Disable()
        self.Bind(wx.EVT_BUTTON, self.OnAjoutActivite, button_add)
        self.sizer.Add(box_sizer, 0, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(self.sizer)
        self.sizer.Layout()
        self.UpdateContents()

    def UpdateContents(self):
        self.color_buttons[(0, "couleur_supplement")].Enable(not readonly and creche.presences_supplementaires)
        self.color_buttons[(0, "couleur_supplement")].hash_cb.Enable(not readonly and creche.presences_supplementaires)
        self.color_buttons[(0, "couleur_previsionnel")].Enable(not readonly)
        self.color_buttons[(0, "couleur_previsionnel")].hash_cb.Enable(not readonly)
        self.activites_sizer.Clear(True)
        for activity in creche.activites.values():
            if activity.value > 0:
                self.AjouteLigneActivite(activity)
        self.sizer.Layout()
        
    def OnCouleursDefaut(self, event):
        history.Append(None)
        counters['activites'] += 1
        creche.activites[0].couleur = [5, 203, 28, 150, wx.SOLID]
        creche.activites[0].couleur_supplement = [5, 203, 28, 250, wx.SOLID]
        creche.activites[0].couleur_previsionnel = [5, 203, 28, 50, wx.SOLID]
        creche.couleurs[VACANCES].couleur = [0, 0, 255, 150, wx.SOLID]
        creche.couleurs[ABSENCE_NON_PREVENUE].couleur = [0, 0, 255, 150, wx.SOLID]
        creche.couleurs[MALADE].couleur = [190, 35, 29, 150, wx.SOLID]
        for activite, field in [(creche.activites[0], "couleur"), (creche.activites[0], "couleur_supplement"), (creche.activites[0], "couleur_previsionnel")]:
            r, g, b, a, h = color = getattr(activite, field)
            self.color_buttons[(0, field)].SetBackgroundColour(wx.Colour(r, g, b))
            self.UpdateHash(self.color_buttons[(0, field)].hash_cb, color)        

    def AjouteLigneActivite(self, activity):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, u'Libellé :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, creche, 'activites[%d].label' % activity.value), 1, wx.EXPAND)])
        mode_choice = AutoChoiceCtrl(self, creche, 'activites[%d].mode' % activity.value, items=activity_modes, observers=['activites'])
        self.Bind(wx.EVT_CHOICE, self.OnChangementMode, mode_choice)
        sizer.AddMany([(wx.StaticText(self, -1, u'Mode :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (mode_choice, 0, 0)])
        color_button = mode_choice.color_button = wx.Button(self, -1, "", size=(20, 20))
        r, g, b, a, h = activity.couleur
        color_button.SetBackgroundColour(wx.Colour(r, g, b))
        self.Bind(wx.EVT_BUTTON, self.OnColorButton, color_button)
        color_button.static = wx.StaticText(self, -1, u'Couleur :')
        color_button.hash_cb = HashComboBox(self)
        color_button.activite = color_button.hash_cb.activite = activity
        color_button.field = color_button.hash_cb.field = ["couleur", "couleur_supplement", "couleur_previsionnel"]
        self.UpdateHash(color_button.hash_cb, activity.couleur)
        self.Bind(wx.EVT_COMBOBOX, self.OnHashChange, color_button.hash_cb)
        sizer.AddMany([(color_button.static, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (color_button, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (color_button.hash_cb, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)])
        if creche.tarification_activites:
            sizer.AddMany([(wx.StaticText(self, -1, u'Tarif :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, creche, 'activites[%d].formule_tarif' % activity.value), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5)])
        if not readonly:
            delbutton = wx.BitmapButton(self, -1, delbmp)
            delbutton.index = activity.value
            sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
            self.Bind(wx.EVT_BUTTON, self.OnSuppressionActivite, delbutton)      
        if readonly or activity.mode == MODE_SANS_HORAIRES:
            color_button.Disable()
            color_button.static.Disable()
            color_button.hash_cb.Disable()
        self.activites_sizer.Add(sizer, 0, wx.EXPAND|wx.BOTTOM, 5)

    def OnAjoutActivite(self, event):
        counters['activites'] += 1
        activity = Activite()
        colors = [tmp.couleur for tmp in creche.activites.values()]
        for h in (wx.BDIAGONAL_HATCH, wx.CROSSDIAG_HATCH, wx.FDIAGONAL_HATCH, wx.CROSS_HATCH, wx.HORIZONTAL_HATCH, wx.VERTICAL_HATCH, wx.TRANSPARENT, wx.SOLID):
            for color in (wx.RED, wx.BLUE, wx.CYAN, wx.GREEN, wx.LIGHT_GREY):
                r, g, b = color.Get()
                if (r, g, b, 150, h) not in colors:
                    activity.couleur = (r, g, b, 150, h)
                    activity.couleur_supplement = (r, g, b, 250, h)
                    activity.couleur_previsionnel = (r, g, b, 50, h)
                    break
            if activity.couleur:
                break
        else:
            activity.couleur = 0, 0, 0, 150, wx.SOLID
            activity.couleur_supplement = 0, 0, 0, 250, wx.SOLID
            activity.couleur_previsionnel = 0, 0, 0, 50, wx.SOLID
        creche.activites[activity.value] = activity
        history.Append(Delete(creche.activites, activity.value))
        self.AjouteLigneActivite(activity)
        self.sizer.Layout()

    def OnSuppressionActivite(self, event):
        counters['activites'] += 1
        index = event.GetEventObject().index
        entrees = []
        for inscrit in creche.inscrits:
            for date in inscrit.journees:
                journee = inscrit.journees[date]
                for start, end, activity in journee.activites:
                    if activity == index:
                        entrees.append((inscrit, date))
                        break
        if len(entrees) > 0:
            message = u'Cette activité est utilisée par :\n'
            for inscrit, date in entrees:
                message += u'%s %s le %s, ' % (inscrit.prenom, inscrit.nom, GetDateString(date))
            message += u'\nVoulez-vous vraiment la supprimer ?'
            dlg = wx.MessageDialog(self, message, u'Confirmation', wx.OK|wx.CANCEL|wx.ICON_WARNING)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_OK:
                return
        for inscrit, date in entrees:
            journee = inscrit.journees[date]
            journee.RemoveActivities(index)
        history.Append(Insert(creche.activites, index, creche.activites[index]))
        for i, child in enumerate(self.activites_sizer.GetChildren()):
            sizer = child.GetSizer()
            if index == sizer.GetItem(len(sizer.Children)-1).GetWindow().index:
                sizer.DeleteWindows()
                self.activites_sizer.Detach(i)
        creche.activites[index].delete()
        del creche.activites[index]
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
        object = event.GetEventObject()
        color_button = object.color_button
        value = object.GetClientData(object.GetSelection())
        color_button.Enable(value != MODE_SANS_HORAIRES)
        color_button.static.Enable(value != MODE_SANS_HORAIRES)
        color_button.hash_cb.Enable(value != MODE_SANS_HORAIRES)
        event.Skip()
        
    def OnColorButton(self, event):
        history.Append(None)
        counters['activites'] += 1
        obj = event.GetEventObject()
        r, g, b, a, h = couleur = getattr(obj.activite, obj.field[0])
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
            setattr(obj.activite, field, couleur)
            if obj.activite.idx is None:
                obj.activite.create() 
        obj.SetBackgroundColour(wx.Colour(r, g, b))
        self.UpdateHash(obj.hash_cb, couleur)
    
    def OnHashChange(self, event):
        history.Append(None)
        counters['activites'] += 1
        obj = event.GetEventObject()
        for field in obj.field:
            setattr(obj.activite, field, obj.GetClientData(obj.GetSelection()))
            if obj.activite.idx is None:
                obj.activite.create()


class ChargesTab(AutoTab, PeriodeMixin):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        PeriodeMixin.__init__(self, 'charges')
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.annee_choice = wx.Choice(self, -1)
        AddYearsToChoice(self.annee_choice)
        self.Bind(wx.EVT_CHOICE, self.OnAnneeChoice, self.annee_choice)
        sizer.Add(self.annee_choice, 0, wx.EXPAND | wx.ALL, 5)
        sizer2 = wx.FlexGridSizer(12, 2, 5, 5)
        self.charges_ctrls = []
        for m in range(12):
            ctrl = AutoNumericCtrl(self, None, 'charges', precision=2)
            self.charges_ctrls.append(ctrl)
            sizer2.AddMany([wx.StaticText(self, -1, months[m] + ' :'), ctrl])
        sizer.Add(sizer2, 0, wx.ALL, 5)
        self.OnAnneeChoice(None)
        sizer.Fit(self)
        self.SetSizer(sizer)

    def OnAnneeChoice(self, evt):
        selected = self.annee_choice.GetSelection()
        annee = self.annee_choice.GetClientData(selected)
        for m in range(12):
            date = datetime.date(annee, m+1, 1)
            if not date in creche.charges:
                creche.charges[date] = Charges(date)
            self.charges_ctrls[m].SetInstance(creche.charges[date])
        

class CafTab(AutoTab, PeriodeMixin):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        PeriodeMixin.__init__(self, 'baremes_caf')
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(PeriodeChoice(self, BaremeCAF), 0, wx.TOP, 5)
        sizer2 = wx.FlexGridSizer(4, 2, 5, 5)
        sizer2.AddMany([wx.StaticText(self, -1, 'Plancher annuel :'), AutoNumericCtrl(self, None, 'plancher', precision=2)])
        sizer2.AddMany([wx.StaticText(self, -1, 'Plafond annuel :'), AutoNumericCtrl(self, None, 'plafond', precision=2)])
        sizer.Add(sizer2, 0, wx.ALL, 5)
        sizer.Fit(self)
        self.SetSizer(sizer)

    def UpdateContents(self):
        self.SetInstance(creche)
        

class JoursFermeturePanel(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        labels_conges = [j[0] for j in jours_fermeture]
        for text in labels_conges:
            checkbox = wx.CheckBox(self, -1, text)
            if readonly:
                checkbox.Disable()
            if text in creche.feries:
                checkbox.SetValue(True)
            self.sizer.Add(checkbox, 0, wx.EXPAND)
            self.Bind(wx.EVT_CHECKBOX, self.feries_check, checkbox)
        self.conges_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, conge in enumerate(creche.conges):
            self.AjouteLigneConge(i)
        self.sizer.Add(self.conges_sizer, 0, wx.ALL, 5)
        button_add = wx.Button(self, -1, u"Ajouter une période de fermeture")
        if readonly:
            button_add.Disable()
        self.sizer.Add(button_add, 0, wx.EXPAND | wx.TOP, 5)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutConge, button_add)
        sizer.Add(self.sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)

    def UpdateContents(self):
        for i in range(len(self.conges_sizer.GetChildren()), len(creche.conges)):
            self.AjouteLigneConge(i)
        for i in range(len(creche.conges), len(self.conges_sizer.GetChildren())):
            self.RemoveLine()
        self.GetSizer().Layout()
        AutoTab.UpdateContents(self)

    def AjouteLigneConge(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, u'Debut :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, creche, 'conges[%d].debut' % index, mois=True, observers=['conges'])])
        sizer.AddMany([(wx.StaticText(self, -1, u'Fin :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, creche, 'conges[%d].fin' % index, mois=True, observers=['conges'])])
        sizer.AddMany([(wx.StaticText(self, -1, u'Libellé :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, creche, 'conges[%d].label' % index, observers=['conges'])])
        sizer.AddMany([(wx.StaticText(self, -1, u'Options :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'conges[%d].options' % index, [(u'Congé', 0), (u'Accueil non facturé', ACCUEIL_NON_FACTURE), (u'Pas de facture pendant ce mois', MOIS_SANS_FACTURE), (u'Uniquement supplément/déduction', MOIS_FACTURE_UNIQUEMENT_HEURES_SUPP)], observers=['conges']), 0, wx.EXPAND)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        if readonly:
            delbutton.Disable()
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.OnSuppressionConge, delbutton)
        self.conges_sizer.Add(sizer)

    def RemoveLine(self):
        index = len(self.conges_sizer.GetChildren()) - 1
        sizer = self.conges_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.conges_sizer.Detach(index)

    def OnAjoutConge(self, event):
        counters['conges'] += 1
        history.Append(Delete(creche.conges, -1))
        creche.AddConge(Conge(creche))
        self.AjouteLigneConge(len(creche.conges) - 1)
        self.GetSizer().Layout()

    def OnSuppressionConge(self, event):
        counters['conges'] += 1
        index = event.GetEventObject().index
        history.Append(Insert(creche.conges, index, creche.conges[index]))
        self.RemoveLine()
        creche.conges[index].delete()
        del creche.conges[index]
        self.UpdateContents()

    def feries_check(self, event):
        label = event.GetEventObject().GetLabelText()
        if event.IsChecked():
            conge = Conge(creche, creation=False)
            conge.debut = label
            conge.create()
            creche.AddConge(conge)
        else:
            conge = creche.feries[label]
            del creche.feries[label]
            conge.delete()            
        history.Append(None)

class ReservatairesTab(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.reservataires_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, reservataire in enumerate(creche.reservataires):
            self.AjouteLigneReservataire(i)
        self.sizer.Add(self.reservataires_sizer, 0, wx.ALL, 5)
        button_add = wx.Button(self, -1, u'Nouveau réservataire')
        if readonly:
            button_add.Disable()
        self.sizer.Add(button_add, 0, wx.EXPAND+wx.TOP, 5)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutReservataire, button_add)
        sizer.Add(self.sizer, 0, wx.EXPAND+wx.ALL, 5)
        self.SetSizer(sizer)

    def UpdateContents(self):
        for i in range(len(self.reservataires_sizer.GetChildren()), len(creche.reservataires)):
            self.AjouteLigneReservataire(i)
        for i in range(len(creche.reservataires), len(self.reservataires_sizer.GetChildren())):
            self.RemoveLine()
        self.sizer.Layout()
        AutoTab.UpdateContents(self)

    def AjouteLigneReservataire(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, u'Debut :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, creche, 'reservataires[%d].debut' % index, mois=True, observers=['reservataires'])])
        sizer.AddMany([(wx.StaticText(self, -1, u'Fin :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, creche, 'reservataires[%d].fin' % index, mois=True, observers=['reservataires'])])
        sizer.AddMany([(wx.StaticText(self, -1, u'Nom :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, creche, 'reservataires[%d].nom' % index, observers=['reservataires'])])
        sizer.AddMany([(wx.StaticText(self, -1, u'Places :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoNumericCtrl(self, creche, 'reservataires[%d].places' % index, precision=0, observers=['reservataires'])])
        sizer.AddMany([(wx.StaticText(self, -1, u'Adresse :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, creche, 'reservataires[%d].adresse' % index, observers=['reservataires'])])
        sizer.AddMany([(wx.StaticText(self, -1, u'Code Postal :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoNumericCtrl(self, creche, 'reservataires[%d].code_postal' % index, precision=0, observers=['reservataires'])])
        sizer.AddMany([(wx.StaticText(self, -1, u'Ville :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, creche, 'reservataires[%d].ville' % index, observers=['reservataires'])])
        sizer.AddMany([(wx.StaticText(self, -1, u'Téléphone :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoPhoneCtrl(self, creche, 'reservataires[%d].telephone' % index, observers=['reservataires'])])
        sizer.AddMany([(wx.StaticText(self, -1, u'E-mail :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, creche, 'reservataires[%d].email' % index, observers=['reservataires'])])
        
        # sizer.AddMany([(wx.StaticText(self, -1, u'Options :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'reservataires[%d].options' % index, [(u'Congé', 0), (u'Accueil non facturé', ACCUEIL_NON_FACTURE), (u'Pas de facture pendant ce mois', MOIS_SANS_FACTURE), (u'Uniquement supplément/déduction', MOIS_FACTURE_UNIQUEMENT_HEURES_SUPP)], observers=['reservataires']), 0, wx.EXPAND)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        if readonly:
            delbutton.Disable()
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.OnSuppressionReservataire, delbutton)
        self.reservataires_sizer.Add(sizer)

    def RemoveLine(self):
        index = len(self.reservataires_sizer.GetChildren()) - 1
        sizer = self.reservataires_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.reservataires_sizer.Detach(index)

    def OnAjoutReservataire(self, event):
        counters['reservataires'] += 1
        history.Append(Delete(creche.reservataires, -1))
        creche.reservataires.append(Reservataire())
        self.AjouteLigneReservataire(len(creche.reservataires) - 1)
        self.sizer.FitInside(self)
        self.sizer.Layout()

    def OnSuppressionReservataire(self, event):
        counters['reservataires'] += 1
        index = event.GetEventObject().index
        history.Append(Insert(creche.reservataires, index, creche.reservataires[index]))
        self.RemoveLine()
        creche.reservataires[index].delete()
        del creche.reservataires[index]
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
        self.ouverture_cb = AutoTimeCtrl(self, creche, "ouverture")
        self.fermeture_cb = AutoTimeCtrl(self, creche, "fermeture")
        self.ouverture_cb.check_function = self.ouverture_check
        self.fermeture_cb.check_function = self.fermeture_check
        self.Bind(wx.EVT_CHOICE, self.onOuverture, self.ouverture_cb)
        self.Bind(wx.EVT_CHOICE, self.onOuverture, self.fermeture_cb)
        sizer2.AddMany([(self.ouverture_cb, 1, wx.EXPAND), (self.ouverture_cb.spin, 0, wx.EXPAND), (wx.StaticText(self, -1, '-'), 0, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10), (self.fermeture_cb, 1, wx.EXPAND), (self.fermeture_cb.spin, 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u"Heures d'ouverture :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), (sizer2, 0, wx.EXPAND)])
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.affichage_min_cb = AutoTimeCtrl(self, creche, "affichage_min")
        self.affichage_max_cb = AutoTimeCtrl(self, creche, "affichage_max")
        self.Bind(wx.EVT_CHOICE, self.onAffichage, self.affichage_min_cb)
        self.Bind(wx.EVT_CHOICE, self.onAffichage, self.affichage_max_cb)
        sizer2.AddMany([(self.affichage_min_cb, 1, wx.EXPAND), (self.affichage_min_cb.spin, 0, wx.EXPAND), (wx.StaticText(self, -1, '-'), 0, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10), (self.affichage_max_cb, 1, wx.EXPAND), (self.affichage_max_cb.spin, 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u"Heures affichées sur le planning :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), (sizer2, 0, wx.EXPAND)])

        def CreateLabelTuple(text):
            return wx.StaticText(self, -1, text), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10

        def CreateRedemarrageSizer(widget):
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.AddMany([(widget, 1, wx.EXPAND), (wx.StaticText(self, -1, u"(prise en compte après redémarrage)"), 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)])
            return sizer

        sizer.AddMany([CreateLabelTuple(u"Mode de saisie des présences :"), (CreateRedemarrageSizer(AutoChoiceCtrl(self, creche, 'mode_saisie_planning', items=modes_saisie_planning)), 0, wx.EXPAND)])
        if creche.mode_saisie_planning == SAISIE_HORAIRE:
            sizer.AddMany([CreateLabelTuple(u"Granularité du planning :"), (AutoChoiceCtrl(self, creche, 'granularite', [('5 minutes', 5), ('10 minutes', 10), ('1/4 heure', 15), ('1/2 heure', 30), ('1 heure', 60)]), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Ordre d'affichage dans les inscriptions :"),
                       (AutoChoiceCtrl(self, creche, 'tri_inscriptions', [(u'Par prénom', TRI_PRENOM), (u'Par nom', TRI_NOM), (u'Par nom sans séparation des anciens', TRI_NOM | TRI_SANS_SEPARATION)]), 0, wx.EXPAND)])
        ordre_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ordre_sizer.AddMany([(AutoChoiceCtrl(self, creche, 'tri_planning', items=[(u'Par prénom', TRI_PRENOM), (u'Par nom', TRI_NOM)], mask=255), 1, wx.EXPAND),
                             (AutoCheckBox(self, creche, 'tri_planning', value=TRI_GROUPE, label=u"Séparation par groupes"), 0, wx.EXPAND|wx.LEFT, 10),
                             (AutoCheckBox(self, creche, 'tri_planning', value=TRI_LIGNES_CAHIER, label=u"Lignes horizontales"), 0, wx.EXPAND|wx.LEFT, 10),
                             ])
        sizer.AddMany([CreateLabelTuple(u"Ordre d'affichage sur le planning :"), (ordre_sizer, 1, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Préinscriptions :"),
                       (AutoChoiceCtrl(self, creche, 'preinscriptions', items=modes_gestion_standard), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Présences prévisionnelles :"),
                       (AutoChoiceCtrl(self, creche, 'presences_previsionnelles', items=modes_gestion_standard), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Présences supplémentaires :"),
                       (AutoChoiceCtrl(self, creche, 'presences_supplementaires', items=modes_gestion_standard), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Modes d'inscription :"),
                       (AutoChoiceCtrl(self, creche, 'modes_inscription', items=modes_inscription), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Mode d'accueil par défaut :"),
                       (AutoChoiceCtrl(self, creche, 'mode_accueil_defaut', items=ModeAccueilItems), 0, wx.EXPAND)])
        mode_facturation_choice = AutoChoiceCtrl(self, creche, 'mode_facturation', modes_facturation)
        self.Bind(wx.EVT_CHOICE, self.onModeFacturationChoice, mode_facturation_choice)
        sizer.AddMany([CreateLabelTuple(u"Mode de facturation :"), (mode_facturation_choice, 1, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(""),
                       (AutoChoiceCtrl(self, creche, 'repartition', modes_mensualisation), 1, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(""),
                       (AutoChoiceCtrl(self, creche, 'temps_facturation', temps_facturation), 1, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Revenus pris en compte :"),
                       (AutoChoiceCtrl(self, creche, 'periode_revenus', [(u'Année N-2', REVENUS_YM2), (u'CAFPRO', REVENUS_CAFPRO)]), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Ordre des factures :"),
                       (AutoChoiceCtrl(self, creche, 'tri_factures', [(u"Par prénom de l'enfant", TRI_PRENOM), (u"Par nom de l'enfant", TRI_NOM), ('Par nom des parents', TRI_NOM_PARENTS)]), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Clôture des factures :"),
                       (AutoChoiceCtrl(self, creche, 'cloture_factures', [(u'Activée', True), (u'Désactivée', False)]), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Mode de facturation des périodes d'adaptation :"), (AutoChoiceCtrl(self, creche, 'facturation_periode_adaptation', modes_facturation_adaptation), 1, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Mode d'arrondi des horaires des enfants :"), (AutoChoiceCtrl(self, creche, 'arrondi_heures', modes_arrondi_horaires_enfants), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Mode d'arrondi de la facturation des enfants :"), (AutoChoiceCtrl(self, creche, 'arrondi_facturation', modes_arrondi_factures_enfants), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Mode d'arrondi de la facturation des enfants pendant les périodes d'adaptation :"), (AutoChoiceCtrl(self, creche, 'arrondi_facturation_periode_adaptation', modes_arrondi_factures_enfants), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Mode d'arrondi des horaires des salariés :"), (AutoChoiceCtrl(self, creche, 'arrondi_heures_salaries', modes_arrondi_horaires_salaries), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Mode d'arrondi des semaines des contrats :"), (AutoChoiceCtrl(self, creche, 'arrondi_semaines', [(u"Arrondi à la semaine supérieure", ARRONDI_SEMAINE_SUPERIEURE), (u"Arrondi à la semaine la plus proche", ARRONDI_SEMAINE_PLUS_PROCHE)]), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Mode d'arrondi des mensualisations en Euros :"), (AutoChoiceCtrl(self, creche, 'arrondi_mensualisation_euros', [(u"Pas d'arrondi", SANS_ARRONDI), (u"Arrondi à l'euro le plus proche", ARRONDI_EURO_PLUS_PROCHE)]), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Gestion des absences prévues au contrat :"), (AutoChoiceCtrl(self, creche, 'conges_inscription', [('Non', 0), (u'Oui', 1), (u"Oui, avec gestion d'heures supplémentaires", 2)]), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Déduction des jours fériés et absences prévues au contrat :"), (AutoChoiceCtrl(self, creche, 'facturation_jours_feries', modes_facturation_jours_feries), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Tarification des activités :"), (AutoChoiceCtrl(self, creche, 'tarification_activites', [(u'Non géré', ACTIVITES_NON_FACTUREES), (u'A la journée', ACTIVITES_FACTUREES_JOURNEE), (u"Période d'adaptation, à la journée", ACTIVITES_FACTUREES_JOURNEE_PERIODE_ADAPTATION)]), 0, wx.EXPAND)])
        if creche.nom == u"LA VOLIERE":
            sizer.AddMany([CreateLabelTuple(u"Coût journalier :"), (AutoNumericCtrl(self, creche, 'cout_journalier', min=0, precision=2), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Traitement des absences pour maladie :"), (AutoChoiceCtrl(self, creche, 'traitement_maladie', [(u"Avec carence en jours ouvrés", DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_OUVRES), (u"Avec carence en jours calendaires", DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CALENDAIRES), (u"Avec carence en jours consécutifs", DEDUCTION_MALADIE_AVEC_CARENCE_JOURS_CONSECUTIFS), ("Sans carence", DEDUCTION_MALADIE_SANS_CARENCE)]), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Durée de la carence :"), (AutoNumericCtrl(self, creche, 'minimum_maladie', min=0, precision=0), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Traitement des absences pour hospitalisation :"), (AutoChoiceCtrl(self, creche, 'gestion_maladie_hospitalisation', items=modes_gestion_standard), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Traitement des absences pour maladie sans justificatif :"), (AutoChoiceCtrl(self, creche, 'gestion_maladie_sans_justificatif', items=modes_gestion_standard), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Traitement des absences non prévenues :"), (AutoChoiceCtrl(self, creche, 'gestion_absences_non_prevenues', items=modes_gestion_standard), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Traitement des préavis de congés :"), (AutoChoiceCtrl(self, creche, 'gestion_preavis_conges', items=modes_gestion_standard), 0, wx.EXPAND)])
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.AddMany([(AutoChoiceCtrl(self, creche, 'gestion_depart_anticipe', items=modes_gestion_standard), 1, wx.EXPAND), (wx.StaticText(self, -1, u'Régularisation de la facturation en fin de contrat :'), 0, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoChoiceCtrl(self, creche, 'regularisation_fin_contrat', [(u"Gérée", True), (u"Non gérée", False)]), 1, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Traitement des départs anticipés :"), (sizer2, 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Changement de groupe :"), (AutoChoiceCtrl(self, creche, 'changement_groupe_auto', [(u"Manuel", False), (u"Automatique", True)]), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Gestion d'alertes :"), (AutoChoiceCtrl(self, creche, 'gestion_alertes', [(u'Activée', True), (u'Désactivée', False)]), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Age maximum des enfants :"), (AutoNumericCtrl(self, creche, 'age_maximum', min=0, max=5, precision=0), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Alerte dépassement capacité dans les plannings :"), (AutoChoiceCtrl(self, creche, 'alerte_depassement_planning', [(u"Activée", True), (u"Désactivée", False)]), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Seuil d'alerte dépassement capacité inscriptions (jours) :"), (AutoNumericCtrl(self, creche, 'seuil_alerte_inscription', min=0, max=100, precision=0), 0, wx.EXPAND)])
        sizer.AddMany([CreateLabelTuple(u"Allergies :"), (CreateRedemarrageSizer(AutoTextCtrl(self, creche, 'allergies')), 0, wx.EXPAND)])
        self.sizer.Add(sizer, 0, wx.EXPAND | wx.ALL, 5)

        salaries_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u"Salariés"), wx.VERTICAL)
        salaries_sizer.AddMany([CreateLabelTuple(u"Nombre de jours de congés payés :"), (AutoNumericCtrl(self, creche, 'conges_payes_salaries', min=0, precision=0), 0, wx.EXPAND)])
        salaries_sizer.AddMany([CreateLabelTuple(u"Nombre de jours de congés supplémentaires :"), (AutoNumericCtrl(self, creche, 'conges_supplementaires_salaries', min=0, precision=0), 0, wx.EXPAND)])
        self.sizer.Add(salaries_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.plages_box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u"Plages horaires spéciales"), wx.VERTICAL)
        self.plages_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, plage in enumerate(creche.plages_horaires):
            self.AjouteLignePlageHoraire(i)
        self.plages_box_sizer.Add(self.plages_sizer, 0, wx.EXPAND|wx.ALL, 5)
        button_add = wx.Button(self, -1, u"Nouvelle plage horaire")
        if readonly:
            button_add.Disable()        
        self.plages_box_sizer.Add(button_add, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutPlageHoraire, button_add)
        self.sizer.Add(self.plages_box_sizer, 0, wx.EXPAND|wx.ALL, 5)
                
        self.tarifs_box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u"Tarifs spéciaux"), wx.VERTICAL)
        self.tarifs_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, tarif in enumerate(creche.tarifs_speciaux):
            self.AjouteLigneTarif(i)
        self.tarifs_box_sizer.Add(self.tarifs_sizer, 0, wx.EXPAND|wx.ALL, 5)
        button_add = wx.Button(self, -1, u'Nouveau tarif spécial')
        if readonly:
            button_add.Disable()        
        self.tarifs_box_sizer.Add(button_add, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutTarif, button_add)
        self.sizer.Add(self.tarifs_box_sizer, 0, wx.EXPAND|wx.ALL, 5)
        
        self.SetSizer(self.sizer)

    def AjouteLignePlageHoraire(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        debut_ctrl = AutoTimeCtrl(self, creche, 'plages_horaires[%d].debut' % index, observers=['plages'])
        fin_ctrl = AutoTimeCtrl(self, creche, 'plages_horaires[%d].fin' % index, observers=['plages']) 
        sizer.AddMany([(wx.StaticText(self, -1, u'Plage horaire :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (debut_ctrl, 1, wx.EXPAND), (debut_ctrl.spin, 0, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'-'), 0, wx.RIGHT|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10), (fin_ctrl, 1, wx.EXPAND), (fin_ctrl.spin, 0, wx.EXPAND)])
        sizer.AddMany([(AutoChoiceCtrl(self, creche, 'plages_horaires[%d].flags' % index, items=[("Fermeture", PLAGE_FERMETURE), (u"Insécable", PLAGE_INSECABLE)], observers=['plages']), 1, wx.LEFT|wx.EXPAND, 5)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnSuppressionPlageHoraire, delbutton)
        self.plages_sizer.Add(sizer, 0, wx.EXPAND|wx.BOTTOM, 5)
        if readonly:
            delbutton.Disable()

    def SupprimeLignePlageHoraire(self):
        index = len(self.plages_sizer.GetChildren()) - 1
        sizer = self.plages_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.plages_sizer.Detach(index)

    def OnAjoutPlageHoraire(self, event):
        counters['plages'] += 1
        history.Append(Delete(creche.plages_horaires, -1))
        creche.plages_horaires.append(PlageHoraire())
        self.AjouteLignePlageHoraire(len(creche.plages_horaires) - 1)
        self.sizer.FitInside(self)

    def OnSuppressionPlageHoraire(self, event):
        counters['plages'] += 1
        index = event.GetEventObject().index
        history.Append(Insert(creche.plages_horaires, index, creche.plages_horaires[index]))
        self.SupprimeLignePlageHoraire()
        creche.plages_horaires[index].delete()
        del creche.plages_horaires[index]
        self.sizer.FitInside(self)
        self.UpdateContents()
    
    def AjouteLigneTarif(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, u'Libellé :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, creche, 'tarifs_speciaux[%d].label' % index, observers=['tarifs']), 1, wx.RIGHT|wx.EXPAND, 5)])
        sizer.AddMany([(AutoChoiceCtrl(self, creche, 'tarifs_speciaux[%d].type' % index, items=[(u"Majoration", TARIF_SPECIAL_MAJORATION), (u"Réduction", TARIF_SPECIAL_REDUCTION), (u"Tarif de remplacement", TARIF_SPECIAL_REMPLACEMENT)]), 1, wx.EXPAND)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Valeur :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoNumericCtrl(self, creche, 'tarifs_speciaux[%d].valeur' % index, precision=2), 1, wx.RIGHT|wx.EXPAND, 5)])
        sizer.AddMany([(AutoChoiceCtrl(self, creche, 'tarifs_speciaux[%d].unite' % index, items=[(u"€", TARIF_SPECIAL_UNITE_EUROS), (u"%", TARIF_SPECIAL_UNITE_POURCENTAGE), (u"€/heure", TARIF_SPECIAL_UNITE_EUROS_PAR_HEURE), (u"€/jour de présence", TARIF_SPECIAL_UNITE_EUROS_PAR_JOUR)]), 1, wx.EXPAND)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnSuppressionTarif, delbutton)
        self.tarifs_sizer.Add(sizer, 0, wx.EXPAND|wx.BOTTOM, 5)
        if readonly:
            delbutton.Disable()

    def SupprimeLigneTarif(self):
        index = len(self.tarifs_sizer.GetChildren()) - 1
        sizer = self.tarifs_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.tarifs_sizer.Detach(index)

    def OnAjoutTarif(self, event):
        counters['tarifs'] += 1
        history.Append(Delete(creche.tarifs_speciaux, -1))
        creche.tarifs_speciaux.append(TarifSpecial())
        self.AjouteLigneTarif(len(creche.tarifs_speciaux) - 1)
        self.sizer.FitInside(self)

    def OnSuppressionTarif(self, event):
        counters['tarifs'] += 1
        index = event.GetEventObject().index
        history.Append(Insert(creche.tarifs_speciaux, index, creche.tarifs_speciaux[index]))
        self.SupprimeLigneTarif()
        creche.tarifs_speciaux[index].delete()
        del creche.tarifs_speciaux[index]
        self.sizer.FitInside(self)
        self.UpdateContents()

    def onModeFacturationChoice(self, event):
        object = event.GetEventObject()
        value = object.GetClientData(object.GetSelection())
        self.GetParent().DisplayTarifHorairePanel(value in (FACTURATION_PAJE, FACTURATION_HORAIRES_REELS))
        self.GetParent().DisplayTauxEffortPanel(value == FACTURATION_PSU_TAUX_PERSONNALISES)
        event.Skip()
            
    def ouverture_check(self, ouverture, a, b):
        return a >= ouverture * 4
    
    def fermeture_check(self, fermeture, a, b):
        return b <= fermeture * 4
    
    def onOuverture(self, event):
        errors = []
        obj = event.GetEventObject()
        value = event.GetClientData()
        for inscrit in creche.inscrits:
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
            message = u"Diminuer la période d'ouverture changera les plannings des enfants suivants :\n"
            for inscrit, jour, info, date in errors:
                message += '  %s %s%s le %s\n' % (inscrit.prenom, inscrit.nom, info, date)
            message += 'Confirmer ?'
            dlg = wx.MessageDialog(self, message, 'Confirmation', wx.OK|wx.CANCEL|wx.ICON_WARNING)
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_OK:
                obj.UpdateContents()
                return
        obj.AutoChange(value)
# TODO
#        for inscrit, jour, info, date in errors:
#            for i in range(0, int(creche.ouverture*4)) + range(int(creche.fermeture*4), TAILLE_TABLE_ACTIVITES):
#                jour.values[i] = 0
#            jour.save()
        if creche.affichage_min > creche.ouverture:
            creche.affichage_min = creche.ouverture
            self.affichage_min_cb.UpdateContents()
        if creche.affichage_max < creche.fermeture:
            creche.affichage_max = creche.fermeture
            self.affichage_max_cb.UpdateContents()
            
    def onAffichage(self, event):
        obj = event.GetEventObject()
        value = event.GetClientData()
        error = False
        if obj is self.affichage_min_cb:
            if value > creche.ouverture:
                error = True
        else:
            if value < creche.fermeture:
                error = True
        if error:
            dlg = wx.MessageDialog(self, u"La période d'affichage doit couvrir au moins l'amplitude horaire de la structure !", "Erreur", wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            obj.UpdateContents()
        else:
            obj.AutoChange(value)

    def onPause(self, event):
        obj = event.GetEventObject()
        value = event.GetClientData()
        obj.AutoChange(value)


class TarifHorairePanel(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        self.delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        addbutton = wx.Button(self, -1, u"Ajouter un cas")
        if readonly:
            addbutton.Disable()
        addbutton.index = 0
        self.Bind(wx.EVT_BUTTON, self.OnAdd, addbutton)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(addbutton, 0, wx.ALIGN_CENTER_VERTICAL|wx.TOP, 5)
        self.controls = []
        if creche.formule_taux_horaire:
            for i, cas in enumerate(creche.formule_taux_horaire):
                self.AjouteLigneTarifHoraire(i, cas[0], cas[1])
        self.SetSizer(self.sizer)
        self.Layout()
        
    def AjouteLigneTarifHoraire(self, index, condition="", taux=0.0):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(10)
        cas = wx.StaticText(self, -1, u"[Cas %d]" % (index+1))
        cas.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(cas, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
        condition_ctrl = wx.TextCtrl(self, -1, condition)
        condition_ctrl.index = index
        sizer1.AddMany([(wx.StaticText(self, -1, 'Condition :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (condition_ctrl, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)])
        taux_ctrl = wx.TextCtrl(self, -1, str(taux))
        taux_ctrl.index = index
        sizer1.AddMany([(wx.StaticText(self, -1, 'Tarif horaire :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (taux_ctrl, 0, wx.ALIGN_CENTER_VERTICAL, 5)])
        if not readonly:
            delbutton = wx.BitmapButton(self, -1, self.delbmp)
            delbutton.index = index
            sizer1.Add(delbutton, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 5)
            self.Bind(wx.EVT_BUTTON, self.OnRemove, delbutton)
        sizer.Add(sizer1, 0, wx.EXPAND)
        if not readonly:
            addbutton = wx.Button(self, -1, "Ajouter un cas")
            addbutton.index = index+1
            sizer.Add(addbutton, 0, wx.ALIGN_CENTER_VERTICAL|wx.TOP, 5)
            self.Bind(wx.EVT_BUTTON, self.OnAdd, addbutton)
            self.controls.insert(index, (cas, condition_ctrl, taux_ctrl, delbutton, addbutton))
            self.Bind(wx.EVT_TEXT, self.OnConditionChange, condition_ctrl)
            self.Bind(wx.EVT_TEXT, self.OnTauxChange, taux_ctrl)
        else:
            condition_ctrl.Disable()
            taux_ctrl.Disable()
        self.sizer.Insert(index+1, sizer, 0, wx.EXPAND|wx.BOTTOM, 5)            

    def OnAdd(self, event):
        object = event.GetEventObject()
        self.AjouteLigneTarifHoraire(object.index)
        if creche.formule_taux_horaire is None:
            creche.formule_taux_horaire = [["", 0.0]]
        else:
            creche.formule_taux_horaire.insert(object.index, ["", 0.0])
        creche.UpdateFormuleTauxHoraire()
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
        if len(creche.formule_taux_horaire) == 1:
            creche.formule_taux_horaire = None
        else:
            del creche.formule_taux_horaire[index]
        creche.UpdateFormuleTauxHoraire()
        for i in range(index, len(self.controls)):
            self.controls[i][0].SetLabel("[Cas %d]" % (i+1))
            for control in self.controls[i][1:]:
                control.index -= 1
        self.sizer.FitInside(self)
        history.Append(None)
    
    def OnConditionChange(self, event):
        object = event.GetEventObject()
        creche.formule_taux_horaire[object.index][0] = object.GetValue()
        creche.UpdateFormuleTauxHoraire()
        if creche.CheckFormuleTauxHoraire(object.index):
            object.SetBackgroundColour(wx.WHITE)
        else:
            object.SetBackgroundColour(wx.RED)
        object.Refresh()
        history.Append(None)
        
    def OnTauxChange(self, event):
        object = event.GetEventObject()
        creche.formule_taux_horaire[object.index][1] = float(object.GetValue())
        creche.UpdateFormuleTauxHoraire()
        history.Append(None)


class TauxEffortPanel(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        self.delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        addbutton = wx.Button(self, -1, "Ajouter un cas")
        addbutton.index = 0
        self.Bind(wx.EVT_BUTTON, self.OnAdd, addbutton)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(addbutton, 0, wx.ALIGN_CENTER_VERTICAL|wx.TOP, 5)
        self.controls = []
        if creche.formule_taux_effort:
            for i, cas in enumerate(creche.formule_taux_effort):
                self.AjouteLigneTauxEffort(i, cas[0], cas[1])
        self.SetSizer(self.sizer)
        self.Layout()
        
    def AjouteLigneTauxEffort(self, index, condition="", taux=0.0):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(10)
        cas = wx.StaticText(self, -1, "[Cas %d]" % (index+1))
        cas.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD))
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(cas, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)
        condition_ctrl = wx.TextCtrl(self, -1, condition)
        condition_ctrl.index = index
        sizer1.AddMany([(wx.StaticText(self, -1, 'Condition :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (condition_ctrl, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)])
        taux_ctrl = wx.TextCtrl(self, -1, str(taux))
        taux_ctrl.index = index
        sizer1.AddMany([(wx.StaticText(self, -1, "Taux d'effort :"), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (taux_ctrl, 0, wx.ALIGN_CENTER_VERTICAL, 5)])
        if not readonly:
            delbutton = wx.BitmapButton(self, -1, self.delbmp)
            delbutton.index = index
            sizer1.Add(delbutton, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 5)
            self.Bind(wx.EVT_BUTTON, self.OnRemove, delbutton)
        sizer.Add(sizer1, 0, wx.EXPAND)
        if not readonly:
            addbutton = wx.Button(self, -1, "Ajouter un cas")
            addbutton.index = index+1
            sizer.Add(addbutton, 0, wx.ALIGN_CENTER_VERTICAL|wx.TOP, 5)
            self.Bind(wx.EVT_BUTTON, self.OnAdd, addbutton)
            self.controls.insert(index, (cas, condition_ctrl, taux_ctrl, delbutton, addbutton))
            self.Bind(wx.EVT_TEXT, self.OnConditionChange, condition_ctrl)
            self.Bind(wx.EVT_TEXT, self.OnTauxChange, taux_ctrl)
        self.sizer.Insert(index+1, sizer, 0, wx.EXPAND|wx.BOTTOM, 5)         

    def OnAdd(self, event):
        object = event.GetEventObject()
        self.AjouteLigneTauxEffort(object.index)
        if creche.formule_taux_effort is None:
            creche.formule_taux_effort = [["", 0.0]]
        else:
            creche.formule_taux_effort.insert(object.index, ["", 0.0])
        creche.UpdateFormuleTauxEffort()
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
        if len(creche.formule_taux_effort) == 1:
            creche.formule_taux_effort = None
        else:
            del creche.formule_taux_effort[index]
        creche.UpdateFormuleTauxEffort()
        for i in range(index, len(self.controls)):
            self.controls[i][0].SetLabel("[Cas %d]" % (i+1))
            for control in self.controls[i][1:]:
                control.index -= 1
        self.sizer.FitInside(self)
        history.Append(None)
    
    def OnConditionChange(self, event):
        object = event.GetEventObject()
        creche.formule_taux_effort[object.index][0] = object.GetValue()
        creche.UpdateFormuleTauxEffort()
        if creche.CheckFormuleTauxEffort(object.index):
            object.SetBackgroundColour(wx.WHITE)
        else:
            object.SetBackgroundColour(wx.RED)
        object.Refresh()
        history.Append(None)
        
    def OnTauxChange(self, event):
        object = event.GetEventObject()
        creche.formule_taux_effort[object.index][1] = float(object.GetValue())
        creche.UpdateFormuleTauxEffort()
        history.Append(None)    

profiles = [(u"Administrateur", PROFIL_ALL),
            (u"Equipe", PROFIL_ALL-PROFIL_ADMIN),
            (u"Bureau", PROFIL_BUREAU),
            (u"Trésorier", PROFIL_TRESORIER),
            (u"Inscriptions", PROFIL_INSCRIPTIONS),
            (u"Saisie présences", PROFIL_SAISIE_PRESENCES),
            (u"Utilisateur lecture seule", PROFIL_LECTURE_SEULE),
            ]


class UsersTab(AutoTab):
    def __init__(self, parent):
        global delbmp
        delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        AutoTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.users_sizer = wx.BoxSizer(wx.VERTICAL)
        for i, user in enumerate(creche.users):
            self.AjouteLigneUtilisateur(i)
        self.sizer.Add(self.users_sizer, 0, wx.EXPAND|wx.ALL, 5)
        button_add = wx.Button(self, -1, u'Nouvel utilisateur')
        if readonly:
            button_add.Disable()      
        self.sizer.Add(button_add, 0, wx.ALL, 5)
        self.Bind(wx.EVT_BUTTON, self.AddUser, button_add)
        self.SetSizer(self.sizer)

    def UpdateContents(self):
        for i in range(len(self.users_sizer.GetChildren()), len(creche.users)):
            self.AjouteLigneUtilisateur(i)
        for i in range(len(creche.users), len(self.users_sizer.GetChildren())):
            self.RemoveLine()
        self.sizer.Layout()
        AutoTab.UpdateContents(self)

    def AjouteLigneUtilisateur(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, u'Login :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoTextCtrl(self, creche, 'users[%d].login' % index), 0, wx.ALIGN_CENTER_VERTICAL)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Mot de passe :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoTextCtrl(self, creche, 'users[%d].password' % index, style=wx.TE_PASSWORD), 0, wx.ALIGN_CENTER_VERTICAL)])
        profile_choice = AutoChoiceCtrl(self, creche, 'users[%d].profile' % index, items=profiles)
        profile_choice.index = index
        self.Bind(wx.EVT_CHOICE, self.OnUserProfileModified, profile_choice)
        sizer.AddMany([(wx.StaticText(self, -1, u'Profil :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), profile_choice])
        delbutton = wx.BitmapButton(self, -1, delbmp, style=wx.NO_BORDER)
        if readonly:
            delbutton.Disable()              
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.RemoveUser, delbutton)
        self.users_sizer.Add(sizer)

    def RemoveLine(self):
        index = len(self.users_sizer.GetChildren()) - 1
        sizer = self.users_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.users_sizer.Detach(index)

    def AddUser(self, event):
        history.Append(Delete(creche.users, -1))
        creche.users.append(User())
        self.AjouteLigneUtilisateur(len(creche.users) - 1)
        self.sizer.Layout()

    def RemoveUser(self, event):
        index = event.GetEventObject().index
        nb_admins = len([user for i, user in enumerate(creche.users) if (i != index and user.profile == PROFIL_ALL)])
        if len(creche.users) == 1 or nb_admins > 0:
            history.Append(Insert(creche.users, index, creche.users[index]))
            self.RemoveLine()
            creche.users[index].delete()
            del creche.users[index]
            self.sizer.Layout()
            self.UpdateContents()
        else:
            dlg = wx.MessageDialog(self, "Il faut au moins un administrateur", 'Message', wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()

    def OnUserProfileModified(self, event):
        obj = event.GetEventObject()
        index = obj.index
        if creche.users[index].profile == PROFIL_ALL and event.GetClientData() != PROFIL_ALL:
            nb_admins = len([user for i, user in enumerate(creche.users) if (i != index and user.profile == PROFIL_ALL)])
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
        self.AddPage(CrecheTab(self), 'Structure')
        self.professeurs_tab = ProfesseursTab(self)
        if creche.type == TYPE_GARDERIE_PERISCOLAIRE:
            self.AddPage(self.professeurs_tab, 'Professeurs')
            self.professeurs_tab_displayed = 1
        else:
            self.professeurs_tab.Show(False)
            self.professeurs_tab_displayed = 0
        self.AddPage(ResponsabilitesTab(self), u'Responsabilités')
        if IsTemplateFile("Synthese financiere.ods"):
            self.AddPage(ChargesTab(self), u'Charges')
            self.charges_tab_displayed = 1
        else:
            self.charges_tab_displayed = 0
        self.AddPage(CafTab(self), 'C.A.F.')
        self.AddPage(JoursFermeturePanel(self), u"Fermeture de l'établissement")
        self.AddPage(ActivitesTab(self), u'Couleurs / Activités')
        self.AddPage(ParametersPanel(self), u'Paramètres')
        self.tarif_horaire_panel = TarifHorairePanel(self)
        if creche.mode_facturation in (FACTURATION_PAJE, FACTURATION_HORAIRES_REELS):
            self.AddPage(self.tarif_horaire_panel, u'Tarif horaire')
            self.tarif_horaire_panel_displayed = 1
        else:
            self.tarif_horaire_panel.Show(False)
            self.tarif_horaire_panel_displayed = 0
        self.taux_effort_panel = TauxEffortPanel(self)
        if creche.mode_facturation == FACTURATION_PSU_TAUX_PERSONNALISES:
            self.AddPage(self.taux_effort_panel, u"Taux d'effort")
            self.taux_effort_panel_displayed = 1
        else:
            self.taux_effort_panel.Show(False)
            self.taux_effort_panel_displayed = 0
        if not readonly:
            self.AddPage(UsersTab(self), u'Utilisateurs et mots de passe')
        if config.options & RESERVATAIRES:
            self.AddPage(ReservatairesTab(self), u'Réservataires')
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
                self.InsertPage(tab_index, self.tarif_horaire_panel, u'Tarif horaire')
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
                self.InsertPage(tab_index, self.taux_effort_panel, u"Taux d'effort")
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
                self.InsertPage(2, self.professeurs_tab, 'Professeurs')
            else:
                self.RemovePage(2)

        self.professeurs_tab_displayed = enable
        self.Layout()


class ConfigurationPanel(GPanel):
    name = "Configuration"
    bitmap = GetBitmapFile("configuration.png")
    profil = PROFIL_ADMIN

    def __init__(self, parent):
        GPanel.__init__(self, parent, 'Configuration')
        self.notebook = ParametresNotebook(self)
        self.sizer.Add(self.notebook, 1, wx.EXPAND)

    def UpdateContents(self):
        self.notebook.UpdateContents()

