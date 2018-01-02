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

import wx.html
from history import *
from controls import *
from planning import *
from cotisation import *
from document_dialog import *
from generation.contrat_accueil import ContratAccueilModifications, DevisAccueilModifications, FraisGardeModifications, AvenantContratAccueilModifications
from config import config
from database import Inscrit, TimeslotInscription, Fratrie, Referent, Parent, CongeInscrit, Inscription, Revenu


class FraisGardePanel(wx.Panel):
    def __init__(self, parent):
        self.parent = parent
        self.inscrit = None
        wx.Panel.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.periodechoice = wx.Choice(self, size=(150, -1))
        self.Bind(wx.EVT_CHOICE, self.onPeriodeChoice, self.periodechoice)
        sizer1.Add(self.periodechoice, 0, wx.ALIGN_CENTER_VERTICAL)
        self.frais_accueil_button = wx.Button(self, -1, "Exporter")
        sizer1.Add(self.frais_accueil_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationFraisAccueil, self.frais_accueil_button)
        if IsTemplateFile("Devis accueil.odt"):
            self.devis_button = wx.Button(self, -1, "Générer un devis")
            sizer1.Add(self.devis_button, 0, wx.LEFT, 5)
            self.Bind(wx.EVT_BUTTON, self.EvtGenerationDevis, self.devis_button)
        else:
            self.devis_button = None
        self.contrat_button = wx.Button(self, -1, "Générer le contrat")
        sizer1.Add(self.contrat_button, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationContrat, self.contrat_button)
        if IsTemplateFile("Avenant contrat accueil.odt"):
            self.avenant_button = wx.Button(self, -1, "Générer un avenant")
            sizer1.Add(self.avenant_button, 0, wx.LEFT, 5)
            self.Bind(wx.EVT_BUTTON, self.EvtGenerationAvenant, self.avenant_button)
        else:
            self.avenant_button = None
        self.sizer.Add(sizer1, 0, wx.ALL, 5)
        self.html_window = wx.html.HtmlWindow(self, style=wx.SUNKEN_BORDER)
        self.sizer.Add(self.html_window, 1, wx.EXPAND | wx.ALL-wx.TOP, 5)
        self.SetSizer(self.sizer)

    def EnableButtons(self, state):
        for button in (self.contrat_button, self.devis_button, self.avenant_button, self.frais_accueil_button):
            if button:
                button.Enable(state)

    def UpdatePage(self):
        if self.inscrit is None:
            self.html = '<html><body>Aucun inscrit s&eacute;lectionn&eacute; !</body></html>'
            self.periodechoice.Disable()
        elif not self.current_cotisation:
            self.html = '<html><body>Aucune inscription !</body></html>'
            self.periodechoice.Disable()
        else:
            context = self.current_cotisation[-1]
            if isinstance(context, CotisationException):
                error = '<br>'.join(context.errors)
                self.html = "<html><body><b>Les frais de garde ne peuvent être calcul&eacute;s pour la (les) raison(s) suivante(s) :</b><br>" + error + "</body></html>"
                self.EnableButtons(False)
            else:
                self.html = generateFraisGardeHtml(context)
                self.EnableButtons(True)
        self.html_window.SetPage(self.html)
        
    def SetInscrit(self, inscrit):
        self.inscrit = inscrit
        self.UpdateContents()
    
    def UpdateContents(self):
        self.periodechoice.Clear()
        if self.inscrit:
            self.cotisations = GetCotisations(self.inscrit)
            if len(self.cotisations) > 0:
                index = len(self.cotisations) - 1
                self.current_cotisation = self.cotisations[index]
                for i, cotisation in enumerate(self.cotisations):
                    if cotisation[0] and cotisation[0] <= today and (not cotisation[1] or today <= cotisation[1]):
                        self.current_cotisation = cotisation
                        index = i
                        break
                self.periodechoice.Enable()
                self.EnableButtons(True)
                for c in self.cotisations:
                    self.periodechoice.Append(date2str(c[0]) + ' - ' + date2str(c[1]))
                self.periodechoice.SetSelection(index)
            else:
                self.current_cotisation = None
                self.periodechoice.Disable()
                self.EnableButtons(False)
        else:
            self.current_cotisation = None
            self.periodechoice.Disable()
            self.EnableButtons(False)
        self.UpdatePage()
        
    def onPeriodeChoice(self, evt):
        ctrl = evt.GetEventObject()
        self.current_cotisation = self.cotisations[ctrl.GetSelection()]
        self.UpdatePage()
        
    def EvtGenerationFraisAccueil(self, _):
        DocumentDialog(self, FraisGardeModifications(self.inscrit, self.current_cotisation[0])).ShowModal()

    def EvtGenerationDevis(self, _):
        DocumentDialog(self, DevisAccueilModifications(self.inscrit, self.current_cotisation[0])).ShowModal()

    def EvtGenerationContrat(self, _):
        DocumentDialog(self, ContratAccueilModifications(self.inscrit, self.current_cotisation[0])).ShowModal()

    def EvtGenerationAvenant(self, _):
        DocumentDialog(self, AvenantContratAccueilModifications(self.inscrit, self.current_cotisation[0])).ShowModal()

            
wildcard = "PNG (*.png)|*.png|"     \
           "BMP (*.pmp)|*.bmp|"     \
           "All files (*.*)|*.*"


class InscriptionsTab(AutoTab):
    def __init__(self, parent):
        AutoTab.__init__(self, parent)
        self.inscrit = None

    def SetInscrit(self, inscrit):
        self.inscrit = inscrit
        for ctrl in self.ctrls:
            ctrl.SetInstance(inscrit)


class IdentitePanel(InscriptionsTab):
    def __init__(self, parent):
        InscriptionsTab.__init__(self, parent)
        self.tarifs_observer = -1
        self.categories_observer = -1
        self.inscrit = None
        self.delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        grid_sizer = wx.FlexGridSizer(0, 2, 5, 10)
        self.sizer2 = grid_sizer
        grid_sizer.AddGrowableCol(1, 1)
        prenom_ctrl = AutoTextCtrl(self, None, 'prenom')
        self.Bind(wx.EVT_TEXT, self.OnChangementPrenom, prenom_ctrl)
        nom_ctrl = AutoTextCtrl(self, None, 'nom')
        self.Bind(wx.EVT_TEXT, self.OnChangementNom, nom_ctrl)
        grid_sizer.AddMany([(wx.StaticText(self, -1, 'Prénom :'), 0, wx.ALIGN_CENTER_VERTICAL),
                            (prenom_ctrl, 0, wx.EXPAND)])
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.famille_button = wx.ToggleButton(self, -1, "Rattachement")
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnRattachementFamille, self.famille_button)           
        sizer.AddMany([(nom_ctrl, 1, wx.EXPAND),
                       (self.famille_button, 0, wx.EXPAND)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, 'Nom :'), 0, wx.ALIGN_CENTER_VERTICAL),
                            (sizer, 0, wx.EXPAND)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, 'Sexe :'), 0, wx.ALIGN_CENTER_VERTICAL),
                            (AutoChoiceCtrl(self, None, 'sexe', items=[("Garçon", MASCULIN), ("Fille", FEMININ)]), 0, wx.EXPAND)])
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.age_ctrl = wx.TextCtrl(self, -1)
        self.age_ctrl.Disable()
        self.date_naissance_ctrl = AutoDateCtrl(self, None, 'naissance')
        self.Bind(wx.EVT_TEXT, self.OnChangementDateNaissance, self.date_naissance_ctrl)
        sizer.AddMany([(self.date_naissance_ctrl, 1, wx.EXPAND),
                       (self.age_ctrl, 1, wx.EXPAND | wx.LEFT, 5)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, 'Date de naissance :'), 0, wx.ALIGN_CENTER_VERTICAL),
                            (sizer, 0, wx.EXPAND)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, 'Adresse :'), 0, wx.ALIGN_CENTER_VERTICAL),
                            (AutoTextCtrl(self, None, 'famille.adresse'), 0, wx.EXPAND)])
        self.ville_ctrl = None  # Pour éviter une exception sur changement de code postal
        self.code_postal_ctrl = AutoNumericCtrl(self, None, 'famille.code_postal', min=0, precision=0)
        self.Bind(wx.EVT_TEXT, self.OnChangementCodePostal, self.code_postal_ctrl)
        self.ville_ctrl = AutoTextCtrl(self, None, 'famille.ville')
        grid_sizer.AddMany([(wx.StaticText(self, -1, 'Code postal :'), 0, wx.ALIGN_CENTER_VERTICAL),
                            (self.code_postal_ctrl, 0, wx.EXPAND)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, 'Ville :'), 0, wx.ALIGN_CENTER_VERTICAL),
                            (self.ville_ctrl, 0, wx.EXPAND)])
        if config.codeclient == "custom":
            grid_sizer.AddMany([(wx.StaticText(self, -1, 'Code client :'), 0, wx.ALIGN_CENTER_VERTICAL),
                                (AutoTextCtrl(self, None, 'famille.code_client'), 0, wx.EXPAND)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, 'Numéro de sécurité sociale :'), 0, wx.ALIGN_CENTER_VERTICAL),
                            (AutoTextCtrl(self, None, 'famille.numero_securite_sociale'), 0, wx.EXPAND)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, "Numéro d'allocataire CAF :"), 0, wx.ALIGN_CENTER_VERTICAL),
                            (AutoTextCtrl(self, None, 'famille.numero_allocataire_caf'), 0, wx.EXPAND)])
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(AutoTextCtrl(self, None, 'famille.medecin_traitant'), 1, wx.EXPAND),
                       (AutoPhoneCtrl(self, None, 'famille.telephone_medecin_traitant'), 1, wx.EXPAND | wx.LEFT, 5)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, "Médecin traitant :"), 0, wx.ALIGN_CENTER_VERTICAL),
                            (sizer, 0, wx.EXPAND)])
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(AutoTextCtrl(self, None, 'famille.assureur'), 1, wx.EXPAND),
                       (AutoTextCtrl(self, None, 'famille.numero_police_assurance'), 1, wx.EXPAND | wx.LEFT, 5)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, "Assurance :"), 0, wx.ALIGN_CENTER_VERTICAL), (sizer, 0, wx.EXPAND)])
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        if config.options & PRELEVEMENTS_AUTOMATIQUES:
            sizer.AddMany([(wx.StaticText(self, -1, "IBAN"), 0, wx.ALIGN_CENTER_VERTICAL),
                           (AutoTextCtrl(self, None, 'famille.iban'), 1, wx.EXPAND | wx.LEFT, 5),
                           (wx.StaticText(self, -1, "BIC"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5),
                           (AutoTextCtrl(self, None, 'famille.bic'), 1, wx.EXPAND | wx.LEFT, 5),
                           (wx.StaticText(self, -1, "ID Mandat"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5),
                           (AutoTextCtrl(self, None, 'famille.mandate_id'), 1, wx.EXPAND | wx.LEFT, 5),
                           (wx.StaticText(self, -1, "X du mois"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5),
                           (AutoNumericCtrl(self, None, 'famille.jour_prelevement_automatique', min=1, precision=0), 1, wx.EXPAND | wx.LEFT, 5),
                           (wx.StaticText(self, -1, "Date 1er prélèvement"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5),
                           (AutoDateCtrl(self, None, 'famille.date_premier_prelevement_automatique'), 1, wx.EXPAND | wx.LEFT, 5)])
            grid_sizer.AddMany([(wx.StaticText(self, -1, "Prélèvements automatiques :"), 0, wx.ALIGN_CENTER_VERTICAL),
                                (sizer, 0, wx.EXPAND)])
        if database.creche.mode_facturation == FACTURATION_PAJE:
            grid_sizer.AddMany([(wx.StaticText(self, -1, "Autorisation attestation PAJE :"), 0, wx.ALIGN_CENTER_VERTICAL),
                                (AutoCheckBox(self, None, "famille.autorisation_attestation_paje"), 0, wx.EXPAND)])
        if database.creche.type == TYPE_PARENTAL:
            self.permanences_dues_widget = wx.TextCtrl(self, -1)
            self.permanences_dues_widget.Disable()
            grid_sizer.AddMany([(wx.StaticText(self, -1, "Permanences :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.permanences_dues_widget, 0, wx.EXPAND)])
        self.allergies_checkboxes = []
        allergies = database.creche.get_allergies()
        if allergies:
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            for allergie in allergies:
                checkbox = wx.CheckBox(self, -1, allergie)
                if config.readonly:
                    checkbox.Disable()
                self.allergies_checkboxes.append(checkbox)
                self.Bind(wx.EVT_CHECKBOX, self.OnToggleAllergie, checkbox)
                sizer.Add(checkbox)
            grid_sizer.AddMany([(wx.StaticText(self, -1, "Allergies :"), 0, wx.ALIGN_CENTER_VERTICAL), (sizer, 0, wx.EXPAND)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, "Enfant handicapé :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoCheckBox(self, None, 'handicap'), 0, wx.EXPAND)])
        self.sizer.Add(grid_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.tarifs_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.tarifs_sizer, 0, wx.EXPAND | wx.LEFT, 5)

        if config.options & CATEGORIES:
            self.categorie_items = wx.StaticText(self, -1, "Catégorie :"), AutoChoiceCtrl(self, None, 'categorie')
            grid_sizer.AddMany([(self.categorie_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.categorie_items[1], 0, wx.EXPAND)])
            self.UpdateCategorieItems()

        # Le chapitre frères et soeurs
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Frères et sœurs'), wx.VERTICAL)
        self.inscrits_fratrie_sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer.Add(self.inscrits_fratrie_sizer, 0, wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP, 10)
        self.fratrie_sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer.Add(self.fratrie_sizer, 0, wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP, 10)
        self.nouveau_frere = wx.Button(self, -1, 'Ajouter un frère ou une sœur')
        self.nouveau_frere.Disable()
        box_sizer.Add(self.nouveau_frere, 0, wx.RIGHT | wx.LEFT | wx.BOTTOM, 10)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutFrere, self.nouveau_frere)
        self.sizer.Add(box_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Le chapitre tablette
        if config.options & TABLETTE:
            self.tabletteSizer = TabletteSizer(self, self.inscrit)
            self.sizer.Add(self.tabletteSizer, 0, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(self.sizer)
        self.sizer.FitInside(self)

    def OnToggleAllergie(self, _):
        if self.inscrit:
            allergies = []
            for checkbox in self.allergies_checkboxes:
                if checkbox.GetValue():
                    allergies.append(checkbox.GetLabel())
            self.inscrit.allergies = ','.join(allergies)
            history.Append(None)                    

    def UpdateCategorieItems(self):
        if len(database.creche.categories) > 0:
            categories = [("----", None)] + [(categorie.nom, categorie) for categorie in database.creche.categories]
            self.categorie_items[1].SetItems(categories)
            for item in self.categorie_items:
                item.Show(True)
        else:
            for item in self.categorie_items:
                item.Show(False)
        self.categories_observer = counters['categories']
            
    def UpdateAllergies(self):
        if self.inscrit and self.allergies_checkboxes:
            allergies = self.inscrit.get_allergies()
            for checkbox in self.allergies_checkboxes:
                checkbox.SetValue(checkbox.GetLabel() in allergies)                    
    
    def UpdateLignesInscritsFratrie(self):
        self.inscrits_fratrie_sizer.DeleteWindows()
        if self.inscrit:        
            for inscrit in database.creche.inscrits:
                if inscrit != self.inscrit and inscrit.famille == self.inscrit.famille:
                    self.AjouteLigneInscritFratrie(inscrit)

    def AjouteLigneInscritFratrie(self, inscrit):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        prenom_ctrl = wx.TextCtrl(self, -1, inscrit.prenom)
        naissance_ctrl = DateCtrl(self, -1, inscrit.naissance)
        debut, fin = inscrit.GetPeriodeInscriptions()
        debut_ctrl = DateCtrl(self, -1, debut)
        fin_ctrl = DateCtrl(self, -1, fin)
        prenom_ctrl.Disable()
        naissance_ctrl.Disable()
        debut_ctrl.Disable()
        fin_ctrl.Disable()
        sizer.AddMany([(wx.StaticText(self, -1, "Prénom :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (prenom_ctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, "Naissance :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (naissance_ctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, "En crèche du"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (debut_ctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, "au"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (fin_ctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)])
        del_button = wx.BitmapButton(self, -1, self.delbmp)
        del_button.Disable()
        sizer.Add(del_button, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        self.inscrits_fratrie_sizer.Add(sizer, 0, wx.EXPAND | wx.BOTTOM, 5)

    def AjouteLigneFrere(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, 'Prénom :'), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, self.inscrit, 'famille.freres_soeurs[%d].prenom' % index), 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Naissance :'), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoDateCtrl(self, self.inscrit, 'famille.freres_soeurs[%d].naissance' % index), 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, 'En crèche du'), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoDateCtrl(self, self.inscrit, 'famille.freres_soeurs[%d].entree' % index), 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, 'au'), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoDateCtrl(self, self.inscrit, 'famille.freres_soeurs[%d].sortie' % index), 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)])
        delbutton = wx.BitmapButton(self, -1, self.delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnSuppressionFrere, delbutton)
        self.fratrie_sizer.Add(sizer, 0, wx.EXPAND | wx.BOTTOM, 5)

    def SupprimeLigneFrere(self):
        index = len(self.fratrie_sizer.GetChildren()) - 1
        sizer = self.fratrie_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.fratrie_sizer.Detach(index)
        
    def OnChangementPrenom(self, event):
        event.GetEventObject().onText(event)
        self.parent.OnChangementPrenomNom(event)

    def OnChangementNom(self, event):
        event.GetEventObject().onText(event)
        self.parent.OnChangementPrenomNom(event)
        self.famille_button.Hide()
        self.famille_button.SetValue(False)
        if self.inscrit:
            for inscrit in database.creche.inscrits:
                if inscrit is not self.inscrit and inscrit.nom == self.inscrit.nom:
                    self.famille_button.SetLabel("Rattachement à la famille de %s" % GetPrenomNom(inscrit))
                    self.famille_button.SetValue(inscrit.famille == self.inscrit.famille)
                    self.famille_button.Show()
                    self.sizer.Layout()
                    break
                    
    def OnRattachementFamille(self, _):
        self.inscrit.ChangeRattachement(self.famille_button.GetValue())
        self.UpdateContents()
                        
    def OnChangementDateNaissance(self, _):
        date_naissance = self.date_naissance_ctrl.GetValue()
        self.age_ctrl.SetValue(GetAgeString(date_naissance))

    def OnChangementCodePostal(self, _):
        if self.ville_ctrl and self.ville_ctrl.instance:
            code_postal = self.code_postal_ctrl.GetValue()
            if code_postal and not self.ville_ctrl.GetValue():
                for famille in database.creche.familles:
                    if famille.code_postal == code_postal and famille.ville:
                        self.ville_ctrl.SetValue(famille.ville)
                        break

    def OnAjoutFrere(self, _):
        history.Append(Delete(self.inscrit.famille.freres_soeurs, -1))
        self.inscrit.famille.freres_soeurs.append(Fratrie(famille=self.inscrit.famille))
        self.AjouteLigneFrere(len(self.inscrit.famille.freres_soeurs) - 1)
        self.sizer.FitInside(self)

    def OnSuppressionFrere(self, event):
        index = event.GetEventObject().index
        history.Append(Insert(self.inscrit.famille.freres_soeurs, index, self.inscrit.famille.freres_soeurs[index]))
        self.SupprimeLigneFrere()
        del self.inscrit.famille.freres_soeurs[index]
        self.UpdateContents()
        self.sizer.FitInside(self)

    def UpdatePermanencesDues(self):
        if self.inscrit:
            if database.creche.date_raz_permanences:
                total, effectue = self.inscrit.GetDecomptePermanences()
                solde = effectue - total
                self.permanences_dues_widget.SetValue("Au %s : Total %s - Effectué %s - Solde %s" % (GetDateString(today), GetHeureString(total), GetHeureString(effectue), GetHeureString(solde)))
            else:
                self.permanences_dues_widget.SetValue("Veuillez saisir une date de remise à zéro du décompte (outil Configuration / Structure)")
        else:
            self.permanences_dues_widget.SetValue("")

    def UpdateContents(self):
        if counters['tarifs'] > self.tarifs_observer:
            while len(self.tarifs_sizer.GetChildren()):
                sizer = self.tarifs_sizer.GetItem(0)
                sizer.DeleteWindows()
                self.tarifs_sizer.Detach(0)
            w = self.sizer2.GetColWidths()[0] + 10
            for tarif in database.creche.tarifs_speciaux:
                if tarif.portee == PORTEE_INSCRIPTION:
                    sizer = wx.BoxSizer(wx.HORIZONTAL)
                    sizer.AddMany([(wx.StaticText(self, -1, '%s :' % tarif.label, size=(w, -1)), 0, wx.ALIGN_CENTER_VERTICAL), (AutoCheckBox(self, self.inscrit, 'famille.tarifs', value=1 << tarif.idx), 0, wx.EXPAND)])
                    self.tarifs_sizer.Add(sizer, 0, wx.EXPAND | wx.BOTTOM, 10)
            self.tarifs_observer = counters['tarifs']
        self.UpdateLignesInscritsFratrie()
        if self.inscrit:
            freres_count = len(self.inscrit.famille.freres_soeurs)
            for i in range(len(self.fratrie_sizer.GetChildren()), freres_count):
                self.AjouteLigneFrere(i)
        else:
            freres_count = 0
        for i in range(freres_count, len(self.fratrie_sizer.GetChildren())):
            self.SupprimeLigneFrere()
        self.UpdateAllergies()
        if config.options & TABLETTE:
            self.tabletteSizer.UpdateCombinaison()
        if config.options & CATEGORIES and counters['categories'] > self.categories_observer:
            self.UpdateCategorieItems()
        if database.creche.type == TYPE_PARENTAL:
            self.UpdatePermanencesDues()

        AutoTab.UpdateContents(self)
        self.sizer.FitInside(self)
        
    def SetInscrit(self, inscrit):
        self.inscrit = inscrit
        if config.options & TABLETTE:
            self.tabletteSizer.SetObject(inscrit)
        self.UpdateContents()
        InscriptionsTab.SetInscrit(self, inscrit)
        self.nouveau_frere.Enable(self.inscrit is not None and not config.readonly)


class ParentsPanel(InscriptionsTab):
    def __init__(self, parent):
        InscriptionsTab.__init__(self, parent)
        self.delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        self.regimes_choices = []
        self.revenus_items = []
        self.parents_items = []
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        sizer1 = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Parents"), wx.VERTICAL)
        sizer11 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(sizer11, 0, wx.EXPAND)
        self.sizer.Add(sizer1, 1, wx.EXPAND | wx.ALL, 5)
        self.relations_items = []
        for index in range(2):
            self.parents_items.append([])
            sizer2 = wx.FlexGridSizer(0, 2, 5, 5)
            sizer2.AddGrowableCol(1, 1)
            relation_item = ChoiceWithoutScroll(self, -1)
            relation_item.index = index
            self.relations_items.append(relation_item)
            for item, value in RelationsItems:
                relation_item.Append(item, value)
            if config.readonly:
                relation_item.Disable()
            self.Bind(wx.EVT_CHOICE, self.OnParentRelationChoice, relation_item)
            sizer2.AddMany([(wx.StaticText(self, -1, 'Relation :'), 0, wx.ALIGN_CENTER_VERTICAL), (relation_item, 0, wx.EXPAND)])
            self.parents_items[-1].extend([wx.StaticText(self, -1, 'Prénom :'), AutoTextCtrl(self, None, 'prenom')])           
            sizer2.AddMany([(self.parents_items[-1][-2], 0, wx.ALIGN_CENTER_VERTICAL), (self.parents_items[-1][-1], 0, wx.EXPAND)])
            self.parents_items[-1].extend([wx.StaticText(self, -1, 'Nom :'), AutoTextCtrl(self, None, 'nom')])
            sizer2.AddMany([(self.parents_items[-1][-2], 0, wx.ALIGN_CENTER_VERTICAL), (self.parents_items[-1][-1], 0, wx.EXPAND)])
            self.parents_items[-1].extend([wx.StaticText(self, -1, 'Adresse :'), AutoTextCtrl(self, None, 'adresse')])
            sizer2.AddMany([(self.parents_items[-1][-2], 0, wx.ALIGN_CENTER_VERTICAL), (self.parents_items[-1][-1], 0, wx.EXPAND)])
            self.parents_items[-1].extend([wx.StaticText(self, -1, 'Code postal :'), AutoNumericCtrl(self, None, 'code_postal', min=0, precision=0)])
            sizer2.AddMany([(self.parents_items[-1][-2], 0, wx.ALIGN_CENTER_VERTICAL), (self.parents_items[-1][-1], 0, wx.EXPAND)])
            self.parents_items[-1].extend([wx.StaticText(self, -1, 'Ville :'), AutoTextCtrl(self, None, 'ville')])
            sizer2.AddMany([(self.parents_items[-1][-2], 0, wx.ALIGN_CENTER_VERTICAL), (self.parents_items[-1][-1], 0, wx.EXPAND)])
            for label, field in ("Téléphone domicile", "telephone_domicile"), ("Téléphone portable", "telephone_portable"), ("Téléphone travail", "telephone_travail"):
                sizer3 = wx.BoxSizer(wx.HORIZONTAL)
                self.parents_items[-1].extend([wx.StaticText(self, -1, label+' :'), AutoPhoneCtrl(self, None, field), AutoTextCtrl(self, None, field+'_notes')])
                sizer3.AddMany([self.parents_items[-1][-2], (self.parents_items[-1][-1], 1, wx.LEFT | wx.EXPAND, 5)])
                sizer2.AddMany([(self.parents_items[-1][-3], 0, wx.ALIGN_CENTER_VERTICAL), (sizer3, 0, wx.EXPAND)])
            self.parents_items[-1].extend([wx.StaticText(self, -1, 'Profession :'), AutoTextCtrl(self, None, 'profession')])
            sizer2.AddMany([(self.parents_items[-1][-2], 0, wx.ALIGN_CENTER_VERTICAL), (self.parents_items[-1][-1], 0, wx.EXPAND)])
            self.parents_items[-1].extend([wx.StaticText(self, -1, 'E-mail :'), AutoTextCtrl(self, None, 'email')])
            sizer2.AddMany([(self.parents_items[-1][-2], 0, wx.ALIGN_CENTER_VERTICAL), (self.parents_items[-1][-1], 0, wx.EXPAND)])
            sizer11.Add(sizer2, 0, wx.EXPAND | wx.ALL, 5)
            if config.profil & PROFIL_FACTURATION:
                panel = PeriodePanel(self, "revenus")
                self.parents_items[-1].append(panel)
                if not database.creche.are_revenus_needed():
                    titre = "Régime d'appartenance"
                    defaultPeriode = today.year
                elif database.creche.periode_revenus == REVENUS_CAFPRO:
                    titre = "Revenus CAFPRO et régime d'appartenance"
                    defaultPeriode = today.year
                else:
                    titre = "Revenus et régime d'appartenance"
                    defaultPeriode = today.year-2
                revenus_sizer = wx.StaticBoxSizer(wx.StaticBox(panel, -1, titre), wx.VERTICAL)
                revenus_sizer.Add(PeriodeChoice(panel, lambda: Revenu(self.inscrit.famille.parents[index]), default=defaultPeriode), 0, wx.EXPAND | wx.ALL, 5)
                revenus_gridsizer = wx.FlexGridSizer(0, 2, 5, 10)
                revenus_gridsizer.AddGrowableCol(1, 1)
                revenus_gridsizer.AddMany([(wx.StaticText(panel, -1, 'Revenus annuels bruts :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoNumericCtrl(panel, None, 'revenu', precision=2), 0, wx.EXPAND)])
                revenus_gridsizer.AddMany([(0, 0), (AutoCheckBox(panel, None, 'chomage', 'Chômage'), 0, wx.EXPAND)])
                revenus_gridsizer.AddMany([(0, 0), (AutoCheckBox(panel, None, 'conge_parental', 'Congé parental'), 0, wx.EXPAND)])
                self.revenus_items.extend([revenus_gridsizer.GetItem(0), revenus_gridsizer.GetItem(1), revenus_gridsizer.GetItem(2)])
                if not database.creche.are_revenus_needed():
                    for item in self.revenus_items:
                        item.Show(False)
                choice = AutoChoiceCtrl(panel, None, 'regime')
                self.regimes_choices.append(choice)
                for i, regime in enumerate(RegimesCAF):
                    choice.Append(regime, i)
                revenus_gridsizer.AddMany([wx.StaticText(panel, -1, "Régime d'appartenance :"), (choice, 0, wx.EXPAND)])
                revenus_sizer.Add(revenus_gridsizer, 0, wx.ALL | wx.EXPAND, 5)
                panel.SetSizer(revenus_sizer)
                sizer11.Add(panel, 0, wx.ALL | wx.EXPAND, 5)
            if index != 1:
                sizer11.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.ALL, 5)

        sizer4 = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Référents'), wx.VERTICAL)
        self.referents_sizer = wx.BoxSizer(wx.VERTICAL)
        sizer4.Add(self.referents_sizer, 0, wx.EXPAND+wx.RIGHT+wx.LEFT+wx.TOP, 10)
        self.nouveau_referent = wx.Button(self, -1, 'Nouveau référent')
        self.nouveau_referent.Disable()
        sizer4.Add(self.nouveau_referent, 0, wx.RIGHT+wx.LEFT+wx.BOTTOM, 10)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutReferent, self.nouveau_referent)
        self.sizer.Add(sizer4, 0, wx.EXPAND | wx.ALL, 5)
        
        sizer5 = wx.StaticBoxSizer(wx.StaticBox(self, -1, 'Notes'), wx.VERTICAL)
        self.notes_parents_ctrl = AutoTextCtrl(self, None, 'famille.notes', style=wx.TE_MULTILINE)
        sizer5.Add(self.notes_parents_ctrl, 0, wx.EXPAND+wx.RIGHT+wx.LEFT+wx.TOP, 10)
        self.sizer.Add(sizer5, 0, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(self.sizer)

    def OnParentRelationChoice(self, event):
        obj = event.GetEventObject()
        sexe = obj.GetClientData(obj.GetSelection())
        index = obj.index
        if sexe is None:
            del self.inscrit.famille.parents[index]
            self.UpdateContents()
        elif index >= len(self.inscrit.famille.parents):
            parent = Parent(self.inscrit.famille, sexe)
            self.inscrit.famille.parents.append(parent)
            self.UpdateContents()
        else:
            self.inscrit.famille.parents[index].sexe = sexe
            event.Skip()
    
    def UpdateContents(self):
        for i in range(0, len(self.referents_sizer.GetChildren())):
            self.SupprimeLigneReferent()
        if self.inscrit:
            for index in range(2):
                parent = self.inscrit.famille.parents[index] if index < len(self.inscrit.famille.parents) else None
                if parent is None:
                    self.relations_items[index].SetSelection(0)
                else:
                    self.relations_items[index].SetSelection(parent.sexe)
                for i, item in enumerate(self.parents_items[index]):
                    item.Show(parent is not None)
                    try:
                        item.SetInstance(parent)
                    except Exception as e:
                        print(e)
            for i in range(0, len(self.inscrit.famille.referents)):
                self.AjoutLigneReferent(i)
        for item in self.revenus_items:
            item.Show(database.creche.are_revenus_needed())
        AutoTab.UpdateContents(self)
        self.sizer.FitInside(self)

    def SetInscrit(self, inscrit):
        self.inscrit = inscrit
        self.notes_parents_ctrl.SetInstance(inscrit)
        self.UpdateContents()
        self.nouveau_referent.Enable(self.inscrit is not None and not config.readonly)

    def AjoutLigneReferent(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, 'Prénom :'), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, self.inscrit, 'famille.referents[%d].prenom' % index), 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Nom :'), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, self.inscrit, 'famille.referents[%d].nom' % index), 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Téléphone :'), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (AutoPhoneCtrl(self, self.inscrit, 'famille.referents[%d].telephone' % index), 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)])
        delbutton = wx.BitmapButton(self, -1, self.delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnSuppressionReferent, delbutton)
        self.referents_sizer.Add(sizer, 0, wx.EXPAND | wx.BOTTOM, 5)            

    def SupprimeLigneReferent(self):
        index = len(self.referents_sizer.GetChildren()) - 1
        sizer = self.referents_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.referents_sizer.Detach(index)
    
    def OnAjoutReferent(self, _):
        history.Append(Delete(self.inscrit.famille.referents, -1))
        self.inscrit.famille.referents.append(Referent(famille=self.inscrit.famille))
        self.AjoutLigneReferent(len(self.inscrit.famille.referents) - 1)
        self.sizer.FitInside(self)

    def OnSuppressionReferent(self, event):
        index = event.GetEventObject().index
        history.Append(Insert(self.inscrit.famille.referents, index, self.inscrit.famille.referents[index]))
        self.SupprimeLigneReferent()
        del self.inscrit.famille.referents[index]
        self.UpdateContents()
        self.sizer.FitInside(self)


class WxInscriptionPlanningLine(BasePlanningLine, BaseWxPythonLine):
    def __init__(self, inscription, index):
        BasePlanningLine.__init__(self, days[index % 7])
        self.inscription = inscription
        self.index = index
        self.day = inscription.get_day_from_index(index)
        self.timeslots = self.day.timeslots

    def update(self):
        self.day = self.inscription.get_day_from_index(self.index)
        self.timeslots = self.day.timeslots

    print("TODO call CheckLine here pour dépassement capacité")
    # if self.options & DEPASSEMENT_CAPACITE and self.state > 0 and self.value == 0 and database.creche.alerte_depassement_planning:
    #     self.check_line(line, self.GetPlagesSelectionnees())

    def add_timeslot(self, debut, fin, activity):
        timeslot = TimeslotInscription(day=self.index, debut=debut, fin=fin, activity=activity)
        self.inscription.days.add(timeslot)
        self.update()

    def delete_timeslot(self, i, check=True):
        timeslot = self.timeslots[i]
        self.inscription.days.remove(timeslot)
        self.update()


class ReferencePlanningPanel(PlanningWidget):
    def __init__(self, parent, activity_choice):
        self.parent = parent
        self.inscription = None
        self.state = None
        PlanningWidget.__init__(self, parent, activity_choice, options=NO_ICONS | PRESENCES_ONLY | ACTIVITES | DEPASSEMENT_CAPACITE | NO_SALARIES)
        
    def CheckLine(self, line, plages):
        if database.creche.seuil_alerte_inscription > 0:
            dates_depassement = []
            for date in self.inscription.GetDatesFromReference(line.day):
                if not self.CheckDate(date, plages):
                    dates_depassement.append(date)
                    if len(dates_depassement) == database.creche.seuil_alerte_inscription:
                        dlg = wx.MessageDialog(None, "Dépassement de la capacité sur ce créneau horaire les:\n" + "\n".join([(" - " + GetDateString(date)) for date in dates_depassement]), "Attention", wx.OK | wx.ICON_WARNING)
                        dlg.ShowModal()
                        dlg.Destroy()
                        self.state = None
                        return

    def OnPlanningChanged(self, line):
        self.parent.UpdateDecompteConges()
               
    @staticmethod
    def CheckDate(date, plages):
        capacite = database.creche.get_capacite(date.weekday())
        lines = GetLines(date, database.creche.inscrits)
        activites, activites_sans_horaires = GetActivitiesSummary(lines)
        for start, end in plages:                        
            for i in range(start, end):
                if activites[0][i][0] > capacite:
                    return False
        return True
   
    def UpdateContents(self):
        lines = []
        if self.inscription:
            for index in range(self.inscription.duree_reference):
                if database.creche.is_jour_semaine_travaille(index):
                    lines.append(WxInscriptionPlanningLine(self.inscription, index))
        self.SetLines(lines)

    def SetInscription(self, inscription):
        self.inscription = inscription
        self.UpdateContents()


class ModeAccueilPanel(InscriptionsTab, PeriodeMixin):
    def __init__(self, parent):
        InscriptionsTab.__init__(self, parent)
        PeriodeMixin.__init__(self, 'inscriptions')
        self.reservataires_observer = None
        self.groupes_observer = None
        sizer = wx.BoxSizer(wx.VERTICAL)
        ligne_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ligne_sizer.Add(PeriodeChoice(self, self.nouvelleInscription))
        self.validation_button = wx.ToggleButton(self, -1, "Invalider l'inscription")
        ligne_sizer.Add(self.validation_button, 0, wx.LEFT, 10)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnValidationInscription, self.validation_button)    
        sizer.Add(ligne_sizer, 0, wx.TOP, 5)
        grid_sizer = wx.FlexGridSizer(0, 2, 5, 10)
        grid_sizer.AddGrowableCol(1, 1)
        
        self.sites_items = wx.StaticText(self, -1, "Site :"), AutoChoiceCtrl(self, None, 'site'), wx.StaticText(self, -1, "Sites de préinscription :"), wx.CheckListBox(self, -1)
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckPreinscriptionSite, self.sites_items[3])
        self.UpdateSiteItems()
        grid_sizer.AddMany([(self.sites_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.sites_items[1], 0, wx.EXPAND)])
        grid_sizer.AddMany([(self.sites_items[2], 0, wx.ALIGN_CENTER_VERTICAL), (self.sites_items[3], 0, wx.EXPAND)])
        
        if config.options & RESERVATAIRES:
            self.reservataire_items = wx.StaticText(self, -1, "Réservataire :"), AutoChoiceCtrl(self, None, 'reservataire')
            self.UpdateReservataireItems()
            grid_sizer.AddMany([(self.reservataire_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.reservataire_items[1], 0, wx.EXPAND)])
            
        self.groupe_items = wx.StaticText(self, -1, "Groupe :"), AutoChoiceCtrl(self, None, 'groupe')
        self.UpdateGroupeItems()
        grid_sizer.AddMany([(self.groupe_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.groupe_items[1], 0, wx.EXPAND)])
        
        self.professeur_items = wx.StaticText(self, -1, "Professeur :"), AutoChoiceCtrl(self, None, 'professeur')
        self.UpdateProfesseurItems()
        grid_sizer.AddMany([(self.professeur_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.professeur_items[1], 0, wx.EXPAND)])
        
        self.mode_accueil_choice = AutoChoiceCtrl(self, None, 'mode', items=ModeAccueilItems)
        self.Bind(wx.EVT_CHOICE, self.OnModeAccueilChoice, self.mode_accueil_choice)
        grid_sizer.AddMany([(wx.StaticText(self, -1, "Mode d'accueil :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.mode_accueil_choice, 0, wx.EXPAND)])
        self.forfait_heures_items = wx.StaticText(self, -1, "Forfait en heures :"), AutoNumericCtrl(self, None, 'forfait_mensuel_heures', min=0, precision=2)
        grid_sizer.AddMany([(self.forfait_heures_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.forfait_heures_items[1], 0, wx.EXPAND)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, "Frais d'inscription :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoNumericCtrl(self, None, 'frais_inscription', min=0, precision=2), 0, wx.EXPAND)])
        if database.creche.mode_facturation in (FACTURATION_PAJE, FACTURATION_PAJE_10H):
            grid_sizer.AddMany([(wx.StaticText(self, -1, "Allocation mensuelle CAF :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoNumericCtrl(self, None, 'allocation_mensuelle_caf', min=0, precision=2), 0, wx.EXPAND)])
        self.tarifs_sizer = wx.BoxSizer(wx.VERTICAL)
        grid_sizer.AddMany([(wx.StaticText(self, -1, "Tarifs spéciaux :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.tarifs_sizer, 0, wx.EXPAND | wx.LEFT, 5)])
        self.UpdateTarifsSpeciaux()
        label_conges = wx.StaticText(self, -1, "Nombre de semaines d'absence prévu au contrat :")
        semaines_conges = AutoNumericCtrl(self, None, 'semaines_conges', min=0, precision=0)
        self.jours_poses = wx.TextCtrl(self, -1)
        self.jours_poses.Disable()
        self.semaines_conges_items = label_conges, semaines_conges, self.jours_poses
        self.heures_and_jours_reference = wx.TextCtrl(self, -1)
        self.heures_and_jours_reference.Disable()
        self.Bind(wx.EVT_TEXT, self.UpdateDecompteConges, semaines_conges)
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.AddMany([(semaines_conges, 0, wx.EXPAND), (self.jours_poses, 1, wx.EXPAND | wx.LEFT, 5)])
        grid_sizer.AddMany([(label_conges, 0, wx.ALIGN_CENTER_VERTICAL), (sizer3, 0, wx.EXPAND)])
        if database.creche.type == TYPE_PARENTAL:
            grid_sizer.AddMany([(wx.StaticText(self, -1, "Heures de permanences à effectuer :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoNumericCtrl(self, None, 'heures_permanences', min=0, precision=2), 0, wx.EXPAND)])
        self.forfait_mensuel_items = wx.StaticText(self, -1, "Forfait mensuel :"), AutoNumericCtrl(self, None, 'forfait_mensuel', min=0, precision=2)
        grid_sizer.AddMany([(self.forfait_mensuel_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.forfait_mensuel_items[1], 0, wx.EXPAND)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, "Date de fin de la période d'adaptation :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoDateCtrl(self, None, 'fin_periode_adaptation'), 0, wx.EXPAND)])
        if database.creche.gestion_depart_anticipe:
            grid_sizer.AddMany([(wx.StaticText(self, -1, "Date de départ anticipé :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoDateCtrl(self, None, 'depart'), 0, wx.EXPAND)])
        self.duree_reference_choice = ChoiceWithoutScroll(self)
        for item, data in [("1 semaine", 7)] + [("%d semaines" % (i + 2), 7 * (i + 2)) for i in range(MAX_SEMAINES_REFERENCE-1)]:
            self.duree_reference_choice.Append(item, data)
        self.Bind(wx.EVT_CHOICE, self.OnDureeReferenceChoice, self.duree_reference_choice)
        grid_sizer.AddMany([(wx.StaticText(self, -1, "Durée de la période de référence :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.duree_reference_choice, 0, wx.EXPAND)])
        sizer.Add(grid_sizer, 0, wx.ALL | wx.EXPAND, 5)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.heures_and_jours_reference, 1, wx.ALIGN_CENTER_VERTICAL)
        self.button_5_5 = wx.Button(self, -1, "Plein temps")
        self.Bind(wx.EVT_BUTTON, self.OnMode_5_5, self.button_5_5)
        self.button_copy = wx.Button(self, -1, "Recopier lundi sur toute la période")
        sizer2.AddMany([(self.button_5_5, 0, wx.ALIGN_CENTER_VERTICAL), (self.button_copy, 0, wx.ALIGN_CENTER_VERTICAL)])
        self.Bind(wx.EVT_BUTTON, self.OnMondayCopy, self.button_copy)
        self.activity_choice = ActivityComboBox(self)        
        sizer2.Add(self.activity_choice, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
        grid_sizer.AddMany([(wx.StaticText(self, -1, "Temps de présence :"), 0, wx.ALIGN_CENTER_VERTICAL), (sizer2, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)])
        self.planning_panel = ReferencePlanningPanel(self, self.activity_choice)
        sizer.Add(self.planning_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.UpdateContents()
        
    def nouvelleInscription(self):
        inscription = Inscription(inscrit=self.inscrit, mode=MODE_TEMPS_PARTIEL, preinscription=database.creche.preinscriptions)
        if len(self.inscrit.inscriptions) > 0:
            previous_inscription = self.inscrit.inscriptions[self.periode]
            inscription.mode = previous_inscription.mode
            inscription.duree_reference = previous_inscription.duree_reference
            for timeslot in previous_inscription.days:
                inscription.days.add(TimeslotInscription(day=timeslot.day, debut=timeslot.debut, fin=timeslot.fin, activity=timeslot.activity))
            if len(database.creche.groupes) > 0:
                inscription.groupe = previous_inscription.groupe
        return inscription

    def SetInscrit(self, inscrit):
        self.inscrit = inscrit
        self.SetInstance(inscrit)
        self.UpdateContents()
    
    def OnValidationInscription(self, event):
        obj = event.GetEventObject()
        inscription = self.inscrit.inscriptions[self.periode]
        if len(database.creche.sites) > 1:
            if obj.GetValue():
                if len(inscription.sites_preinscription) != 1:
                    if not inscription.sites_preinscription:
                        dlg = wx.MessageDialog(self, "Avant de valider une inscription, il faut choisir un site de préinscription", 'Erreur', wx.OK|wx.ICON_WARNING)
                    else:
                        dlg = wx.MessageDialog(self, "Avant de valider une inscription, il ne faut garder qu'un seul site de préinscription", 'Erreur', wx.OK|wx.ICON_WARNING)
                    dlg.ShowModal()
                    dlg.Destroy()
                    self.UpdateContents()
                    event.Skip()
                    return
                else:
                    inscription.site = inscription.sites_preinscription[0]
            else:
                inscription.sites_preinscription = [inscription.site]
        inscription.preinscription = not obj.GetValue()
        history.Append(None)
        self.UpdateContents()
    
    def OnModeAccueilChoice(self, _):
        history.Append(None)
        self.inscrit.inscriptions[self.periode].mode = self.mode_accueil_choice.GetClientData(self.mode_accueil_choice.GetSelection())
        self.UpdateContents()        
        
    def OnDureeReferenceChoice(self, _):
        history.Append(None)
        duration = self.duree_reference_choice.GetClientData(self.duree_reference_choice.GetSelection())
        self.inscrit.inscriptions[self.periode].duree_reference = duration
        self.UpdateContents()
        
    def OnMode_5_5(self, _):
        history.Append(None)
        for line in self.planning_panel.lines:
            for debut, fin in database.creche.GetPlagesOuvertureArray():
                line.set_activity(debut, fin, 0)
        self.UpdateContents()
    
    def OnMondayCopy(self, _):
        history.Append(None)
        for line in self.planning_panel.lines[1:]:
            for i in range(len(line.timeslots)):
                line.delete_timeslot(0)
            for timeslot in self.planning_panel.lines[0].timeslots:
                line.add_timeslot(timeslot.debut, timeslot.fin, timeslot.activity)
        self.UpdateContents()
            
    def OnCheckPreinscriptionSite(self, event):
        index = event.GetSelection()
        obj = event.GetEventObject()
        site = database.creche.sites[index]
        inscription = self.inscrit.inscriptions[self.periode]
        history.Append(Change(inscription, "sites_preinscription", inscription.sites_preinscription[:]))
        if obj.IsChecked(index):
            inscription.sites_preinscription.append(site)
        else:
            inscription.sites_preinscription.remove(site)
        inscription.sites_preinscription = inscription.sites_preinscription

    def UpdateSiteItems(self):
        if len(database.creche.sites) > 1:
            items = [(site.get_name(), site) for site in database.creche.sites]
            self.sites_items[1].SetItems(items)
            for nom, site in items:
                self.sites_items[3].Append(nom)
        else:
            for item in self.sites_items:
                item.Show(False)
        self.sites_observer = counters['sites']
    
    def UpdateReservataireItems(self):
        if len(database.creche.reservataires) > 0:
            reservataires = [("----", None)] + [(reservataire.nom, reservataire) for reservataire in database.creche.reservataires]
            self.reservataire_items[1].SetItems(reservataires)
            for item in self.reservataire_items:
                item.Show(True)
        else:
            for item in self.reservataire_items:
                item.Show(False)
        self.reservataires_observer = counters['reservataires']

    def UpdateGroupeItems(self):
        if len(database.creche.groupes) > 0:
            groupes = [("----", None)] + [(groupe.nom, groupe) for groupe in database.creche.groupes]
            self.groupe_items[1].SetItems(groupes)
            for item in self.groupe_items:
                item.Show(True)
        else:
            for item in self.groupe_items:
                item.Show(False)
        self.groupes_observer = counters["groupes"]

    def UpdateProfesseurItems(self):
        if database.creche.type == TYPE_GARDERIE_PERISCOLAIRE and len(database.creche.professeurs) > 0:
            professeurs = [("%s %s" % (professeur.prenom, professeur.nom), professeur) for professeur in database.professeurs]
            self.professeur_items[1].SetItems(professeurs)
            for item in self.professeur_items:
                item.Show(True)
        else:
            for item in self.professeur_items:
                item.Show(False)
        self.professeurs_observer = counters["professeurs"]
    
    def UpdateDecompteConges(self, event=None, inscription=None):
        if inscription is None and self.inscrit and self.periode is not None and self.periode != -1 and self.periode < len(self.inscrit.inscriptions):
            inscription = self.inscrit.inscriptions[self.periode]
        if inscription and not inscription.preinscription:
            self.jours_poses.SetValue("%d jours posés / %d jours" % (inscription.GetNombreJoursCongesPoses(), inscription.GetNombreJoursCongesPeriode()))
            days, duration = inscription.get_days_per_week(), inscription.get_duration_per_week()
            print("TODO arrondi")
            self.heures_and_jours_reference.SetValue("%s heures / %s jours" % (Number2String(duration), Number2String(days)))
        else:
            self.jours_poses.SetValue("")
            self.heures_and_jours_reference.SetValue("")

    def UpdateTarifsSpeciaux(self):
        while len(self.tarifs_sizer.GetChildren()):
            sizer = self.tarifs_sizer.GetItem(0)
            sizer.DeleteWindows()
            self.tarifs_sizer.Detach(0)
        w = 200  # self.sizer2.GetColWidths()[0] + 10
        for tarif in database.creche.tarifs_speciaux:
            if tarif.portee == PORTEE_CONTRAT:
                sizer = wx.BoxSizer(wx.HORIZONTAL)
                sizer.AddMany([(wx.StaticText(self, -1, '%s :' % tarif.label, size=(w, -1)), 0, wx.ALIGN_CENTER_VERTICAL), (AutoCheckBox(self, None, 'tarifs', value=1 << tarif.idx), 0, wx.EXPAND)])
                self.tarifs_sizer.Add(sizer, 0, wx.EXPAND | wx.BOTTOM, 10)
        self.tarifs_observer = counters['tarifs']

    def UpdateContents(self):
        if counters['sites'] > self.sites_observer:
            self.UpdateSiteItems()
        if counters['groupes'] > self.groupes_observer:
            self.UpdateGroupeItems()
        if config.options & RESERVATAIRES and counters['reservataires'] > self.reservataires_observer:
            self.UpdateReservataireItems()
        if counters['professeurs'] > self.professeurs_observer:
            self.UpdateProfesseurItems()
        if counters['tarifs'] > self.tarifs_observer:
            self.UpdateTarifsSpeciaux()

        InscriptionsTab.UpdateContents(self)
        self.mode_accueil_choice.Enable(not is_power_of_two(database.creche.modes_inscription))
        self.validation_button.Show(database.creche.preinscriptions)

        self.InternalUpdate()
        self.activity_choice.Update()

        for item in self.semaines_conges_items:
            item.Show(database.creche.facturation_jours_feries != ABSENCES_DEDUITES_SANS_LIMITE and database.creche.mode_facturation in (FACTURATION_PAJE, FACTURATION_PAJE_10H, FACTURATION_PSU, FACTURATION_FORFAIT_10H))
            
        for item in self.forfait_mensuel_items:
            item.Show(database.creche.mode_facturation == FACTURATION_FORFAIT_MENSUEL)
                            
        self.Layout()

    def SetPeriode(self, periode):
        PeriodeMixin.SetPeriode(self, periode)
        self.InternalUpdate()
    
    def InternalUpdate(self):
        if self.inscrit and self.periode is not None and self.periode != -1 and self.periode < len(self.inscrit.inscriptions):
            inscription = self.inscrit.inscriptions[self.periode]
            for obj in [self.duree_reference_choice, self.mode_accueil_choice, self.button_5_5, self.button_copy, self.validation_button]:
                obj.Enable(not config.readonly)
            if database.creche.preinscriptions:
                if inscription.preinscription:
                    self.validation_button.SetValue(False)
                    self.validation_button.SetLabel("Valider l'inscription")
                    if len(database.creche.sites) > 1:
                        for item in self.sites_items[0:2]:
                            item.Show(False)
                        for item in self.sites_items[2:4]:
                            item.Show(True)
                        self.sites_items[3].SetCheckedStrings([site.nom for site in inscription.sites_preinscription])
                else:
                    self.validation_button.SetValue(True)
                    self.validation_button.SetLabel("Invalider l'inscription")
                    if len(database.creche.sites) > 1:
                        for item in self.sites_items[0:2]:
                            item.Show(True)
                        for item in self.sites_items[2:4]:
                            item.Show(False)
            elif len(database.creche.sites) > 1:
                for item in self.sites_items[0:2]:
                    item.Show(True)
                for item in self.sites_items[2:4]:
                    item.Show(False)
            self.duree_reference_choice.SetSelection(inscription.duree_reference // 7 - 1)
            self.planning_panel.SetInscription(inscription)
            for item in self.forfait_heures_items:
                item.Show(inscription.mode in (MODE_FORFAIT_MENSUEL, MODE_FORFAIT_HEBDOMADAIRE, MODE_FORFAIT_GLOBAL_CONTRAT))
            self.UpdateDecompteConges(inscription=inscription)
        else:
            self.planning_panel.SetInscription(None)
            for obj in [self.duree_reference_choice, self.mode_accueil_choice, self.button_5_5, self.button_copy, self.validation_button]:
                obj.Disable()


class CongesPanel(InscriptionsTab):
    def __init__(self, parent):
        global delbmp
        delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        
        InscriptionsTab.__init__(self, parent)
        self.label = "Absences déduites sans mensualisation" if database.creche.conges_inscription == GESTION_CONGES_INSCRIPTION_NON_MENSUALISES else "Absences prévues au contrat"
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.conges_creche_sizer = wx.BoxSizer(wx.VERTICAL)
        self.AfficheCongesCreche()
        self.sizer.Add(self.conges_creche_sizer, 0, wx.ALL, 5)
        
        self.conges_inscrit_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.conges_inscrit_sizer, 0, wx.ALL, 5)
        
        self.nouveau_conge_button = wx.Button(self, -1, "Ajouter une période d'absence")
        self.sizer.Add(self.nouveau_conge_button, 0, wx.EXPAND+wx.TOP, 5)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutConge, self.nouveau_conge_button)

#        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
#        sizer2.AddMany([(wx.StaticText(self, -1, 'Nombre de semaines de congés déduites :'), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), (AutoNumericCtrl(self, creche, 'semaines_conges', min=0, precision=0), 0, wx.EXPAND)])
#        self.sizer.Add(sizer2, 0, wx.EXPAND+wx.TOP, 5)

        self.SetSizer(self.sizer)

    def UpdateContents(self):
        # if sys.platform == 'win32':
        #     self.Hide()
        if counters['conges'] > self.conges_observer:
            self.AfficheCongesCreche()
        if self.inscrit:
            for i in range(len(self.conges_inscrit_sizer.GetChildren()), len(self.inscrit.conges)):
                self.AjouteLigneConge(i)
            for i in range(len(self.inscrit.conges), len(self.conges_inscrit_sizer.GetChildren())):
                self.SupprimeLigneConge()
        else:
            for i in range(len(self.conges_inscrit_sizer.GetChildren())):
                self.SupprimeLigneConge()
        AutoTab.UpdateContents(self)
        self.sizer.Layout()
        self.sizer.FitInside(self)
        # if sys.platform == 'win32':
        #     self.Show()
        
    def SetInscrit(self, inscrit):
        self.inscrit = inscrit
        self.UpdateContents()
        InscriptionsTab.SetInscrit(self, inscrit)
        self.nouveau_conge_button.Enable(self.inscrit is not None and not config.readonly)

    def AfficheCongesCreche(self):
        self.conges_creche_sizer.DeleteWindows()
        if database.creche.conges_inscription != GESTION_CONGES_INSCRIPTION_NON_MENSUALISES:
            labels_conges = [j[0] for j in jours_fermeture]
            for label in labels_conges:
                checkbox = wx.CheckBox(self, -1, label)
                checkbox.Disable()
                if label in database.creche.feries:
                    checkbox.SetValue(True)
                self.conges_creche_sizer.Add(checkbox, 0, wx.EXPAND)
            for conge in database.creche.conges:
                sizer = wx.BoxSizer(wx.HORIZONTAL)
                sizer.AddMany([(wx.StaticText(self, -1, 'Debut :'), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, conge, 'debut', mois=True, fixed_instance=True)])
                sizer.AddMany([(wx.StaticText(self, -1, 'Fin :'), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, conge, 'fin', mois=True, fixed_instance=True)])
                sizer.AddMany([(wx.StaticText(self, -1, 'Libellé :'), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, conge, 'label', fixed_instance=True)])
                for child in sizer.GetChildren():
                    child.GetWindow().Disable()
                self.conges_creche_sizer.Add(sizer)
        self.conges_observer = counters['conges']

    def AjouteLigneConge(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, 'Debut :'), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, self.inscrit, 'conges[%d].debut' % index, mois=True)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Fin :'), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, self.inscrit, 'conges[%d].fin' % index, mois=True)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Libellé :'), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, self.inscrit, 'conges[%d].label' % index)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.OnSuppressionConge, delbutton)
        self.conges_inscrit_sizer.Add(sizer)
        
    def SupprimeLigneConge(self):
        index = len(self.conges_inscrit_sizer.GetChildren()) - 1
        sizer = self.conges_inscrit_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.conges_inscrit_sizer.Detach(index)

    def OnAjoutConge(self, _):
        history.Append(Delete(self.inscrit.conges, -1))
        self.inscrit.add_conge(CongeInscrit(inscrit=self.inscrit))
        self.AjouteLigneConge(len(self.inscrit.conges) - 1)
        self.sizer.FitInside(self)
        self.sizer.Layout()

    def OnSuppressionConge(self, event):
        index = event.GetEventObject().index
        conge = self.inscrit.conges[index]
        history.Append(Insert(self.inscrit.conges, index, conge))
        self.SupprimeLigneConge()
        self.inscrit.delete_conge(conge)
        self.sizer.Layout()
        self.UpdateContents()


class NotesPanel(InscriptionsTab):
    def __init__(self, parent):        
        InscriptionsTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(AutoTextCtrl(self, None, 'notes', style=wx.TE_MULTILINE), 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(self.sizer)


class InscriptionsNotebook(wx.Notebook):
    def __init__(self, parent, *args, **kwargs):
        wx.Notebook.__init__(self, parent, style=wx.LB_DEFAULT, *args, **kwargs)      
        self.parent = parent
        self.inscrit = None

        self.AddPage(IdentitePanel(self), 'Identité')
        self.AddPage(ParentsPanel(self), 'Parents et référents')
        self.AddPage(ModeAccueilPanel(self), "Mode d'accueil")
        if database.creche.conges_inscription:
            self.conges_panel = CongesPanel(self)
            self.AddPage(self.conges_panel, self.conges_panel.label)
        else:
            self.conges_panel = None
        self.AddPage(NotesPanel(self), "Notes")
        if config.profil & PROFIL_FACTURATION:
            self.AddPage(FraisGardePanel(self), 'Frais de garde')

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)  
            
    def OnChangementPrenomNom(self, _):
        self.parent.ChangePrenom(self.inscrit)

    def OnPageChanged(self, event):
        self.GetPage(event.GetSelection()).UpdateContents()
        event.Skip()

    def SetInscrit(self, inscrit):
        self.inscrit = inscrit
        for i in range(self.GetPageCount()):
            page = self.GetPage(i)
            page.SetInscrit(inscrit)
            
    def UpdateContents(self):
        if database.creche.conges_inscription and not self.conges_panel:
            self.conges_panel = CongesPanel(self)
            self.conges_panel.SetInscrit(self.inscrit)
            self.InsertPage(3, self.conges_panel, self.conges_panel.label)
        elif self.conges_panel and not database.creche.conges_inscription:
            self.RemovePage(3)
            self.conges_panel.Destroy()
            self.conges_panel = None
        self.GetCurrentPage().UpdateContents()


print("TODO import inscrit")

class InscritImportDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "Import d'une fiche d'inscription", wx.DefaultPosition, wx.DefaultSize)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.creche_import = None  # sqlinterface.SQLConnection(config.import_database).Load(None)
        self.combo = wx.ListBox(self, style=wx.LB_SORT)
        for child in self.creche_import.inscrits:
            label = GetPrenomNom(child)
            if label.strip() != "":
                self.combo.Append(label, child)
        self.sizer.Add(self.combo, 0, wx.ALL, 5)
        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        btnsizer.AddButton(btn)
        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        self.sizer.Add(btnsizer, 0, wx.ALL, 5)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)

    def GetInscritSelected(self):
        return self.combo.GetClientData(self.combo.GetSelection())


class InscriptionsPanel(GPanel):
    name = "Inscriptions"
    bitmap = GetBitmapFile("inscriptions.png")
    profil = PROFIL_INSCRIPTIONS
    
    def __init__(self, parent):
        GPanel.__init__(self, parent, "Inscriptions")

        # Le control pour la selection de l'enfant
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.choice = wx.Choice(self)
        self.Bind(wx.EVT_CHOICE, self.OnInscritChoice, self.choice)
        plusbmp = wx.Bitmap(GetBitmapFile("plus.png"), wx.BITMAP_TYPE_PNG)
        self.addbutton = wx.BitmapButton(self, -1, plusbmp)
        self.addbutton.SetToolTipString("Ajouter un enfant")
        self.Bind(wx.EVT_BUTTON, self.OnAjoutInscrit, self.addbutton)
        delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        self.delbutton = wx.BitmapButton(self, -1, delbmp)
        self.delbutton.SetToolTipString("Supprimer cet enfant")
        self.Bind(wx.EVT_BUTTON, self.OnSuppressionInscrit, self.delbutton)
        sizer.AddMany([(self.choice, 1, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL),
                       (self.addbutton, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5),
                       (self.delbutton, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)])
        if config.import_database:
            importbmp = wx.Bitmap(GetBitmapFile("import.png"), wx.BITMAP_TYPE_PNG)
            self.importbutton = wx.BitmapButton(self, -1, importbmp)
            self.importbutton.SetToolTipString("Importer un enfant")
            self.Bind(wx.EVT_BUTTON, self.OnImportInscrit, self.importbutton)
            sizer.Add(self.importbutton, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
        self.sizer.Add(sizer, 0, wx.EXPAND | wx.LEFT, MACOS_MARGIN)
        # le notebook pour la fiche d'inscription
        self.notebook = InscriptionsNotebook(self)
        self.sizer.Add(self.notebook, 1, wx.EXPAND | wx.TOP, 5)
        self.InitInscrits()

    def UpdateContents(self):
        self.notebook.UpdateContents()
            
    def InitInscrits(self, selected=None):
        AddInscritsToChoice(self.choice)
        if len(database.creche.inscrits) > 0 and selected is not None and selected in database.creche.inscrits:
            self.SelectInscrit(selected)
        else:
            for i in range(self.choice.GetCount()):
                inscrit = self.choice.GetClientData(i)
                if isinstance(inscrit, Inscrit):
                    self.SelectInscrit(inscrit)
                    break
            else:
                self.SelectInscrit(None)

    def OnInscritChoice(self, evt):
        ctrl = evt.GetEventObject()
        selected = ctrl.GetSelection()
        inscrit = ctrl.GetClientData(selected)
        if isinstance(inscrit, Inscrit):
            self.inscrit_selected = selected
            self.delbutton.Enable()
            self.notebook.SetInscrit(inscrit)
        else:
            ctrl.SetSelection(self.inscrit_selected)
            self.OnInscritChoice(evt)

    def SelectInscrit(self, inscrit):
        if inscrit:
            self.inscrit_selected = SelectValueInChoice(self.choice, inscrit)
        else:
            self.choice.SetSelection(-1)
        self.notebook.SetInscrit(inscrit)

    def AjouteInscrit(self, inscrit):
        database.creche.inscrits.append(inscrit)
        self.InitInscrits(inscrit)
        self.notebook.SetInscrit(inscrit)
        self.notebook.SetSelection(0)  # Selectionne la page identite

    print("TODO Import Inscrit")

    def OnImportInscrit(self, _):
        dlg = InscritImportDialog(self)
        res = dlg.ShowModal()
        if res == wx.ID_OK:
            history.Append(Delete(database.creche.inscrits, -1))
            inscrit = dlg.GetInscritSelected()
            inscrit.idx = None
            if 0:
                inscrit.famille.create()
                inscrit.create()
                for inscription in inscrit.inscriptions:
                    if inscription.site:
                        inscription.site = database.creche.GetSite(inscription.site.idx)
                    for reference in inscription.reference:
                        reference.Save(force=True)
                for date in inscrit.journees:
                    inscrit.journees[date].Save(force=True)
                if inscrit.jours_conges:
                    print("Not imported: jours_conges" % inscrit.jours_conges)
                if inscrit.clotures:
                    print("Not imported: clotures" % inscrit.clotures)
                if inscrit.corrections:
                    print("Not imported: clotures" % inscrit.corrections)
            else:
                inscrit.inscriptions[:] = [Inscription(inscrit)]
                inscrit.journees = {}
                inscrit.semaines = {}
                inscrit.clotures = {}
                inscrit.corrections = {}
                inscrit.famille.create()
                inscrit.create()
            self.AjouteInscrit(inscrit)
        dlg.Destroy()

    def OnAjoutInscrit(self, _):
        history.Append(Delete(database.creche.inscrits, -1))
        inscrit = Inscrit(creche=database.creche)
        self.AjouteInscrit(inscrit)

    def OnSuppressionInscrit(self, _):
        selected = self.choice.GetSelection()
        inscrit = self.choice.GetClientData(selected)
        if inscrit:
            dlg = wx.MessageDialog(self,
                                   "Cette inscription va être supprimée, êtes-vous sûr de vouloir continuer ?",
                                   "Confirmation",
                                   wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION )
            if dlg.ShowModal() == wx.ID_YES:
                index = database.creche.inscrits.index(inscrit)
                history.Append(Insert(database.creche.inscrits, index, inscrit))
                del database.creche.inscrits[index]
                self.choice.Delete(selected)
                self.choice.SetSelection(-1)
                self.notebook.SetInscrit(None)
                self.delbutton.Disable()
            dlg.Destroy()
        
    def ChangePrenom(self, inscrit):
        if database.creche and inscrit:
            inscritId = GetPrenomNom(inscrit, tri=database.creche.tri_inscriptions)
            if inscritId.isspace():
                inscritId = "Nouvelle inscription"
            selection = self.choice.GetSelection()
            self.choice.SetString(selection, '  ' + inscritId)
            self.choice.SetSelection(selection)
