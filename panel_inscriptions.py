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

import xml.dom.minidom
import wx.html
from sqlobjects import *
from controls import *
from planning import *
from cotisation import *
from ooffice import *
from doc_contrat_accueil import ContratAccueilModifications, DevisAccueilModifications, FraisGardeModifications


def ParseHtml(filename, context):
    locals().update(context.__dict__)
    data = file(filename, 'r').read()

    # remplacement des <if>
    while 1:
        start = data.find('<if ')
        if start == -1:
            break
        end = data.find('</if>', start) + 5
        text = data[start:end]
        dom = xml.dom.minidom.parseString(text[:text.index('>')+1] + '</if>')
        test = dom.getElementsByTagName('if')[0].getAttribute('value')
        try:
            if eval(test):
                replacement = text[text.index('>')+1:-5]
            else:
                replacement = ''
            
        except:
            print 'TODO', text
            replacement = '' # TODO la période de référence du contrat est cassée
        data = data.replace(text, replacement)

    # remplacement des <var>
    while 1:
        start = data.find('<var ')
        if start == -1:
            break
        end = data.find('/>', start) + 2
        text = data[start:end]
        dom = xml.dom.minidom.parseString(text)
        try:
            replacement = eval(dom.getElementsByTagName('var')[0].getAttribute('value'))
        except:
            replacement = "<erreur (%s)>" % dom.getElementsByTagName('var')[0].getAttribute('value')
        if type(replacement) == datetime.date:
            replacement = date2str(replacement)
        elif type(replacement) != str and type(replacement) != unicode:
            replacement = str(replacement)
        data = data.replace(text, replacement)

    return data


class FraisGardePanel(wx.Panel):
    def __init__(self, parent):
        self.parent = parent
        wx.Panel.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.periodechoice = wx.Choice(self, size=(150,-1))
        self.Bind(wx.EVT_CHOICE, self.EvtPeriodeChoice, self.periodechoice)
        sizer1.Add(self.periodechoice, 0, wx.ALIGN_CENTER_VERTICAL)
        self.frais_accueil_button = wx.Button(self, -1, u"Exporter")
        sizer1.Add(self.frais_accueil_button, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationFraisAccueil, self.frais_accueil_button)
        if IsTemplateFile("Devis accueil.odt"):
            devis_button = wx.Button(self, -1, u"Générer un devis")
            sizer1.Add(devis_button, 0, wx.LEFT, 5)
            self.Bind(wx.EVT_BUTTON, self.EvtGenerationDevis, devis_button)
        self.contrat_button = wx.Button(self, -1, u"Générer le contrat")
        sizer1.Add(self.contrat_button, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationContrat, self.contrat_button)
        if IsTemplateFile("Avenant contrat accueil.odt"):
            avenant_button = wx.Button(self, -1, u"Générer un avenant")
            sizer1.Add(avenant_button, 0, wx.LEFT, 5)
            self.Bind(wx.EVT_BUTTON, self.EvtGenerationAvenant, avenant_button)
        self.sizer.Add(sizer1, 0, wx.ALL, 5)
        self.html_window = wx.html.HtmlWindow(self, style=wx.SUNKEN_BORDER)
        self.sizer.Add(self.html_window, 1, wx.EXPAND|wx.ALL-wx.TOP, 5)
        self.SetSizer(self.sizer)

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
                self.html = u"<html><body><b>Les frais de garde ne peuvent être calcul&eacute;s pour la (les) raison(s) suivante(s) :</b><br>" + error + "</body></html>"
                self.frais_accueil_button.Disable()
                self.contrat_button.Disable()
            else:
                if creche.mode_facturation == FACTURATION_FORFAIT_MENSUEL:
                    filename = "Frais garde forfait.html"
                elif creche.mode_facturation == FACTURATION_HORAIRES_REELS:
                    filename = "Frais garde reel.html"
                elif creche.mode_facturation == FACTURATION_PAJE:
                    filename = "Frais garde paje.html"
                else:
                    filename = "Frais garde defaut.html"   
                self.html = ParseHtml(GetTemplateFile(filename), context)
                self.frais_accueil_button.Enable()
                self.contrat_button.Enable()
        self.html_window.SetPage(self.html)
        
    def SetInscrit(self, inscrit):
        self.inscrit = inscrit
        self.UpdateContents()

    def GetCotisations(self):
        self.cotisations = []
        for inscription in self.inscrit.inscriptions:
            date = inscription.debut
            while date and date.year < today.year + 2:
                try:
                    cotisation = Cotisation(self.inscrit, date, TRACES)
                    self.cotisations.append((cotisation.debut, cotisation.fin, cotisation))
                    if cotisation.fin and (not inscription.fin or cotisation.fin < inscription.fin):
                        date = cotisation.fin + datetime.timedelta(1)
                    else:
                        date = None
                except CotisationException, e:
                    self.cotisations.append((date, inscription.fin, e))
                    date = None
    
    def UpdateContents(self):
        self.periodechoice.Clear()
        if self.inscrit:
            self.GetCotisations()
            if len(self.cotisations) > 0:
                index = len(self.cotisations) - 1
                self.current_cotisation = self.cotisations[index]
                for i, cotisation in enumerate(self.cotisations):
                    if cotisation[0] and cotisation[0] <= today and (not cotisation[1] or today <= cotisation[1]):
                        self.current_cotisation = cotisation
                        index = i
                        break
                self.periodechoice.Enable()
                self.frais_accueil_button.Enable()
                self.contrat_button.Enable()
                for c in self.cotisations:
                    self.periodechoice.Append(date2str(c[0]) + ' - ' + date2str(c[1]))
                self.periodechoice.SetSelection(index)
            else:
                self.current_cotisation = None
                self.periodechoice.Disable()
                self.frais_accueil_button.Disable()
                self.contrat_button.Disable()
        else:
            self.current_cotisation = None
            self.periodechoice.Disable()
            self.frais_accueil_button.Disable()
            self.contrat_button.Disable()
        self.UpdatePage()
        
    def EvtPeriodeChoice(self, evt):
        ctrl = evt.GetEventObject()
        self.current_cotisation = self.cotisations[ctrl.GetSelection()]
        self.UpdatePage()
        
    def EvtGenerationFraisAccueil(self, evt):
        DocumentDialog(self, FraisGardeModifications(self.inscrit, self.current_cotisation[0])).ShowModal()

    def EvtGenerationDevis(self, evt):
        DocumentDialog(self, DevisAccueilModifications(self.inscrit, self.current_cotisation[0])).ShowModal()

    def EvtGenerationContrat(self, evt):
        DocumentDialog(self, ContratAccueilModifications(self.inscrit, self.current_cotisation[0])).ShowModal()

    def EvtGenerationAvenant(self, evt):
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
        grid_sizer.AddMany([(wx.StaticText(self, -1, u'Prénom :'), 0, wx.ALIGN_CENTER_VERTICAL), (prenom_ctrl, 0, wx.EXPAND)])
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.famille_button = wx.ToggleButton(self, -1, u"Rattachement")
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnRattachementFamille, self.famille_button)           
        sizer.AddMany([(nom_ctrl, 1, wx.EXPAND), (self.famille_button, 0, wx.EXPAND)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, u'Nom :'), 0, wx.ALIGN_CENTER_VERTICAL), (sizer, 0, wx.EXPAND)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, u'Sexe :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoChoiceCtrl(self, None, 'sexe', items=[(u"Garçon", 1), ("Fille", 2)]), 0, wx.EXPAND)])
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.age_ctrl = wx.TextCtrl(self, -1)
        self.age_ctrl.Disable()
        self.date_naissance_ctrl = AutoDateCtrl(self, None, 'naissance')
        self.Bind(wx.EVT_TEXT, self.OnChangementDateNaissance, self.date_naissance_ctrl)
        sizer.AddMany([(self.date_naissance_ctrl, 1, wx.EXPAND), (self.age_ctrl, 1, wx.EXPAND|wx.LEFT, 5)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, u'Date de naissance :'), 0, wx.ALIGN_CENTER_VERTICAL), (sizer, 0, wx.EXPAND)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, u'Adresse :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoTextCtrl(self, None, 'famille.adresse'), 0, wx.EXPAND)])
        self.ville_ctrl = AutoTextCtrl(self, None, 'famille.ville') # A laisser avant le code postal !
        self.code_postal_ctrl = AutoNumericCtrl(self, None, 'famille.code_postal', min=0, precision=0)
        self.Bind(wx.EVT_TEXT, self.OnChangementCodePostal, self.code_postal_ctrl)
        grid_sizer.AddMany([(wx.StaticText(self, -1, u'Code Postal :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.code_postal_ctrl, 0, wx.EXPAND)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, u'Ville :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.ville_ctrl, 0, wx.EXPAND)])
        if config.codeclient == "custom":
            grid_sizer.AddMany([(wx.StaticText(self, -1, u'Code client :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoTextCtrl(self, None, 'famille.code_client'), 0, wx.EXPAND)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, u'Numéro de sécurité sociale :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoTextCtrl(self, None, 'famille.numero_securite_sociale'), 0, wx.EXPAND)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, u"Numéro d'allocataire CAF :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoTextCtrl(self, None, 'famille.numero_allocataire_caf'), 0, wx.EXPAND)])
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(AutoTextCtrl(self, None, 'famille.medecin_traitant'), 1, wx.EXPAND), (AutoPhoneCtrl(self, None, 'famille.telephone_medecin_traitant'), 1, wx.EXPAND|wx.LEFT, 5)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, u"Médecin traitant :"), 0, wx.ALIGN_CENTER_VERTICAL), (sizer, 0, wx.EXPAND)])
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(AutoTextCtrl(self, None, 'famille.assureur'), 1, wx.EXPAND), (AutoTextCtrl(self, None, 'famille.numero_police_assurance'), 1, wx.EXPAND|wx.LEFT, 5)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, u"Assurance :"), 0, wx.ALIGN_CENTER_VERTICAL), (sizer, 0, wx.EXPAND)])
        if creche.type == TYPE_PARENTAL:
            self.permanences_dues_widget = wx.TextCtrl(self, -1)
            self.permanences_dues_widget.Disable()
            grid_sizer.AddMany([(wx.StaticText(self, -1, u"Permanences :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.permanences_dues_widget, 0, wx.EXPAND)])
        self.allergies_checkboxes = []
        allergies = creche.GetAllergies()
        if allergies:
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            for allergie in allergies:
                checkbox = wx.CheckBox(self, -1, allergie)
                if readonly:
                    checkbox.Disable()
                self.allergies_checkboxes.append(checkbox)
                self.Bind(wx.EVT_CHECKBOX, self.OnToggleAllergie, checkbox)
                sizer.Add(checkbox)
            grid_sizer.AddMany([(wx.StaticText(self, -1, u"Allergies :"), 0, wx.ALIGN_CENTER_VERTICAL), (sizer, 0, wx.EXPAND)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, u"Enfant handicapé :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoCheckBox(self, None, 'handicap'), 0, wx.EXPAND)])
        self.sizer.Add(grid_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.tarifs_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.tarifs_sizer, 0, wx.EXPAND | wx.LEFT, 5)

        if config.options & CATEGORIES:
            self.categorie_items = wx.StaticText(self, -1, u"Catégorie :"), AutoChoiceCtrl(self, None, 'categorie')
            grid_sizer.AddMany([(self.categorie_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.categorie_items[1], 0, wx.EXPAND)])
            self.UpdateCategorieItems()

        # Le chapitre frères et soeurs
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Frères et sœurs'), wx.VERTICAL)
        self.inscrits_fratrie_sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer.Add(self.inscrits_fratrie_sizer, 0, wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP, 10)
        self.fratrie_sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer.Add(self.fratrie_sizer, 0, wx.EXPAND | wx.RIGHT | wx.LEFT | wx.TOP, 10)
        self.nouveau_frere = wx.Button(self, -1, u'Ajouter un frère ou une sœur')
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

    def OnToggleAllergie(self, event):
        if self.inscrit:
            allergies = []
            for checkbox in self.allergies_checkboxes:
                if checkbox.GetValue():
                    allergies.append(checkbox.GetLabel())
            self.inscrit.allergies = ','.join(allergies)
            history.Append(None)                    

    def UpdateCategorieItems(self):
        if len(creche.categories) > 0:
            categories = [("----", None)] + [(categorie.nom, categorie) for categorie in creche.categories]
            self.categorie_items[1].SetItems(categories)
            for item in self.categorie_items:
                item.Show(True)
        else:
            for item in self.categorie_items:
                item.Show(False)
        self.categories_observer = counters['categories']
            
    def UpdateAllergies(self):
        if self.inscrit and self.allergies_checkboxes:
            allergies = self.inscrit.GetAllergies()
            for checkbox in self.allergies_checkboxes:
                checkbox.SetValue(checkbox.GetLabel() in allergies)                    
    
    def UpdateLignesInscritsFratrie(self):
        self.inscrits_fratrie_sizer.DeleteWindows()
        if self.inscrit:        
            for inscrit in creche.inscrits:
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
        sizer.AddMany([(wx.StaticText(self, -1, u"Prénom :"), 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (prenom_ctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, u"Naissance :"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (naissance_ctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, u"En crèche du"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (debut_ctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, u"au"), 0, wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 5), (fin_ctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND, 5)])
        del_button = wx.BitmapButton(self, -1, self.delbmp)
        del_button.Disable()
        sizer.Add(del_button, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        self.inscrits_fratrie_sizer.Add(sizer, 0, wx.EXPAND|wx.BOTTOM, 5)

    def AjouteLigneFrere(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, u'Prénom :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, self.inscrit, 'famille.freres_soeurs[%d].prenom' % index), 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Naissance :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoDateCtrl(self, self.inscrit, 'famille.freres_soeurs[%d].naissance' % index), 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, u'En crèche du'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoDateCtrl(self, self.inscrit, 'famille.freres_soeurs[%d].entree' % index), 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, u'au'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoDateCtrl(self, self.inscrit, 'famille.freres_soeurs[%d].sortie' % index), 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)])
        delbutton = wx.BitmapButton(self, -1, self.delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnSuppressionFrere, delbutton)
        self.fratrie_sizer.Add(sizer, 0, wx.EXPAND|wx.BOTTOM, 5)

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
            for inscrit in creche.inscrits:
                if inscrit is not self.inscrit and inscrit.nom == self.inscrit.nom:
                    self.famille_button.SetLabel(u"Rattachement à la famille de %s" % GetPrenomNom(inscrit))
                    self.famille_button.SetValue(inscrit.famille == self.inscrit.famille)
                    self.famille_button.Show()
                    self.sizer.Layout()
                    break
                    
    def OnRattachementFamille(self, event):
        if not self.famille_button.GetValue():
            self.inscrit.famille = Famille()
        else:
            for inscrit in creche.inscrits:
                if inscrit is not self.inscrit and inscrit.nom == self.inscrit.nom:
                    self.inscrit.famille = inscrit.famille
                    break
        self.UpdateContents()
                        
    def OnChangementDateNaissance(self, event):
        date_naissance = self.date_naissance_ctrl.GetValue()
        self.age_ctrl.SetValue(GetAgeString(date_naissance))

    def OnChangementCodePostal(self, event):
        code_postal = self.code_postal_ctrl.GetValue()
        if code_postal and not self.ville_ctrl.GetValue():
            for famille in creche.familles:
                if famille.code_postal == code_postal and famille.ville:
                    self.ville_ctrl.SetValue(famille.ville)
                    break

    def OnAjoutFrere(self, event):
        history.Append(Delete(self.inscrit.famille.freres_soeurs, -1))
        self.inscrit.famille.freres_soeurs.append(Frere_Soeur(self.inscrit.famille))
        self.AjouteLigneFrere(len(self.inscrit.famille.freres_soeurs) - 1)
        self.sizer.FitInside(self)

    def OnSuppressionFrere(self, event):
        index = event.GetEventObject().index
        history.Append(Insert(self.inscrit.famille.freres_soeurs, index, self.inscrit.famille.freres_soeurs[index]))
        self.SupprimeLigneFrere()
        self.inscrit.famille.freres_soeurs[index].delete()
        del self.inscrit.famille.freres_soeurs[index]
        self.UpdateContents()
        self.sizer.FitInside(self)

    def UpdatePermanencesDues(self):
        if self.inscrit:
            total, effectue = self.inscrit.GetDecomptePermanences()
            solde = effectue - total
            self.permanences_dues_widget.SetValue(u"Au %s : Total %s - Effectué %s - Solde %s" % (GetDateString(today), GetHeureString(total), GetHeureString(effectue), GetHeureString(solde)))
        else:
            self.permanences_dues_widget.SetValue("")

    def UpdateContents(self):
        if counters['tarifs'] > self.tarifs_observer:
            while len(self.tarifs_sizer.GetChildren()):
                sizer = self.tarifs_sizer.GetItem(0)
                sizer.DeleteWindows()
                self.tarifs_sizer.Detach(0)
            w = self.sizer2.GetColWidths()[0] + 10
            for tarif in creche.tarifs_speciaux:
                sizer = wx.BoxSizer(wx.HORIZONTAL)
                sizer.AddMany([(wx.StaticText(self, -1, u'%s :' % tarif.label, size=(w, -1)), 0, wx.ALIGN_CENTER_VERTICAL), (AutoCheckBox(self, self.inscrit, 'famille.tarifs', value=1 << tarif.idx), 0, wx.EXPAND)])
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
        if creche.type == TYPE_PARENTAL:
            self.UpdatePermanencesDues()

        AutoTab.UpdateContents(self)
        self.sizer.FitInside(self)
        
    def SetInscrit(self, inscrit):
        self.inscrit = inscrit
        if config.options & TABLETTE:
            self.tabletteSizer.SetObject(inscrit)
        self.UpdateContents()
        InscriptionsTab.SetInscrit(self, inscrit)
        self.nouveau_frere.Enable(self.inscrit is not None and not readonly)


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
        self.sizer.Add(sizer1, 1, wx.EXPAND|wx.ALL, 5)
        self.relations_items = []
        for index in range(2):
            self.parents_items.append([])
            sizer2 = wx.FlexGridSizer(0, 2, 5, 5)
            sizer2.AddGrowableCol(1, 1)
            self.relations_items.append(wx.Choice(self, -1))
            for item, value in (('Papa', 'papa'), ('Maman', 'maman'), ('Parent manquant', None)):
                self.relations_items[-1].Append(item, value)
            self.relations_items[-1].index = index
            if readonly:
                self.relations_items[-1].Disable()
            self.Bind(wx.EVT_CHOICE, self.OnParentRelationChoice, self.relations_items[-1])
            sizer2.AddMany([(wx.StaticText(self, -1, u'Relation :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.relations_items[-1], 0, wx.EXPAND)])           
            self.parents_items[-1].extend([wx.StaticText(self, -1, u'Prénom :'), AutoTextCtrl(self, None, 'prenom')])           
            sizer2.AddMany([(self.parents_items[-1][-2], 0, wx.ALIGN_CENTER_VERTICAL), (self.parents_items[-1][-1], 0, wx.EXPAND)])
            self.parents_items[-1].extend([wx.StaticText(self, -1, u'Nom :'), AutoTextCtrl(self, None, 'nom')])
            sizer2.AddMany([(self.parents_items[-1][-2], 0, wx.ALIGN_CENTER_VERTICAL), (self.parents_items[-1][-1], 0, wx.EXPAND)])
            for label, field in (u"Téléphone domicile", "telephone_domicile"), (u"Téléphone portable", "telephone_portable"), (u"Téléphone travail", "telephone_travail"):
                sizer3 = wx.BoxSizer(wx.HORIZONTAL)
                self.parents_items[-1].extend([wx.StaticText(self, -1, label+' :'), AutoPhoneCtrl(self, None, field), AutoTextCtrl(self, None, field+'_notes')])
                sizer3.AddMany([self.parents_items[-1][-2], (self.parents_items[-1][-1], 1, wx.LEFT|wx.EXPAND, 5)])
                sizer2.AddMany([(self.parents_items[-1][-3], 0, wx.ALIGN_CENTER_VERTICAL), (sizer3, 0, wx.EXPAND)])
            self.parents_items[-1].extend([wx.StaticText(self, -1, 'E-mail :'), AutoTextCtrl(self, None, 'email')])
            sizer2.AddMany([(self.parents_items[-1][-2], 0, wx.ALIGN_CENTER_VERTICAL), (self.parents_items[-1][-1], 0, wx.EXPAND)])
            sizer11.Add(sizer2, 0, wx.EXPAND|wx.ALL, 5)
            if profil & PROFIL_TRESORIER:
                panel = PeriodePanel(self, 'revenus')
                self.parents_items[-1].append(panel)
                if not creche.AreRevenusNeeded():
                    titre = u"Régime d'appartenance"
                    defaultPeriode = today.year
                elif creche.periode_revenus == REVENUS_CAFPRO:
                    titre = u"Revenus CAFPRO et régime d'appartenance"
                    defaultPeriode = today.year
                else:
                    titre = u"Revenus et régime d'appartenance"
                    defaultPeriode = today.year-2
                revenus_sizer = wx.StaticBoxSizer(wx.StaticBox(panel, -1, titre), wx.VERTICAL)
                revenus_sizer.Add(PeriodeChoice(panel, Revenu, default=defaultPeriode), 0, wx.EXPAND|wx.ALL, 5)
                revenus_gridsizer = wx.FlexGridSizer(0, 2, 5, 10)
                revenus_gridsizer.AddGrowableCol(1, 1)
                revenus_gridsizer.AddMany([(wx.StaticText(panel, -1, u'Revenus annuels bruts :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoNumericCtrl(panel, None, 'revenu', precision=2), 0, wx.EXPAND)])
                revenus_gridsizer.AddMany([(0, 0), (AutoCheckBox(panel, None, 'chomage', u'Chômage'), 0, wx.EXPAND)])
                revenus_gridsizer.AddMany([(0, 0), (AutoCheckBox(panel, None, 'conge_parental', u'Congé parental'), 0, wx.EXPAND)])
                self.revenus_items.extend([revenus_gridsizer.GetItem(0), revenus_gridsizer.GetItem(1), revenus_gridsizer.GetItem(2)])
                if not creche.AreRevenusNeeded():
                    for item in self.revenus_items:
                        item.Show(False)
                choice = AutoChoiceCtrl(panel, None, 'regime')
                self.regimes_choices.append(choice)
                for i, regime in enumerate(Regimes):
                    choice.Append(regime, i)
                revenus_gridsizer.AddMany([wx.StaticText(panel, -1, u"Régime d'appartenance :"), (choice, 0, wx.EXPAND)])
                revenus_sizer.Add(revenus_gridsizer, 0, wx.ALL|wx.EXPAND, 5)
                panel.SetSizer(revenus_sizer)
                sizer11.Add(panel, 0, wx.ALL|wx.EXPAND, 5)
            if index != 1:
                sizer11.Add(wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL), 0, wx.EXPAND|wx.ALL, 5)

        sizer4 = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Référents'), wx.VERTICAL)
        self.referents_sizer = wx.BoxSizer(wx.VERTICAL)
        sizer4.Add(self.referents_sizer, 0, wx.EXPAND+wx.RIGHT+wx.LEFT+wx.TOP, 10)
        self.nouveau_referent = wx.Button(self, -1, u'Nouveau référent')
        self.nouveau_referent.Disable()
        sizer4.Add(self.nouveau_referent, 0, wx.RIGHT+wx.LEFT+wx.BOTTOM, 10)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutReferent, self.nouveau_referent)
        self.sizer.Add(sizer4, 0, wx.EXPAND|wx.ALL, 5)
        
        sizer5 = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Notes'), wx.VERTICAL)
        self.notes_parents_ctrl = AutoTextCtrl(self, None, 'famille.notes', style=wx.TE_MULTILINE)
        sizer5.Add(self.notes_parents_ctrl, 0, wx.EXPAND+wx.RIGHT+wx.LEFT+wx.TOP, 10)
        self.sizer.Add(sizer5, 0, wx.EXPAND|wx.ALL, 5)
        
        self.SetSizer(self.sizer)

    def OnParentRelationChoice(self, event):
        object = event.GetEventObject()
        value = object.GetClientData(object.GetSelection())
        if value is None:
            self.inscrit.famille.parents[object.instance.relation] = None
            object.instance.delete()
            for item in self.parents_items[object.index]:
                item.Show(False)
            self.sizer.FitInside(self)
        elif not self.inscrit.famille.parents[value]:
            self.inscrit.famille.parents[value] = parent = Parent(self.inscrit.famille, value)
            for item in self.parents_items[object.index]:
                try:
                    item.SetInstance(parent)
                except:
                    pass
                item.Show(True)
            self.UpdateContents()
            self.sizer.FitInside(self)
        else:
            event.Skip()
    
    def UpdateContents(self):
        if self.inscrit:
            for index, key in enumerate(self.inscrit.famille.parents.keys()):
                parent = self.inscrit.famille.parents[key]
                if parent:
                    self.relations_items[index].SetStringSelection(key.capitalize())
                else:
                    self.relations_items[index].SetSelection(2)
                self.relations_items[index].instance = parent
                for i, item in enumerate(self.parents_items[index]):
                    item.Show(parent is not None)
                    try:
                        item.SetInstance(parent)
                    except:
                        pass
            referents_count = len(self.inscrit.famille.referents)
            for i in range(len(self.referents_sizer.GetChildren()), referents_count):
                self.AjoutLigneReferent(i)
        else:
            referents_count = 0
        for i in range(referents_count, len(self.referents_sizer.GetChildren())):
            self.SupprimeLigneReferent()
        for item in self.revenus_items:
            item.Show(creche.AreRevenusNeeded())
        AutoTab.UpdateContents(self)
        self.sizer.FitInside(self)

    def SetInscrit(self, inscrit):
        self.inscrit = inscrit
        self.notes_parents_ctrl.SetInstance(inscrit)
        self.UpdateContents()
        self.nouveau_referent.Enable(self.inscrit is not None and not readonly)

    def AjoutLigneReferent(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, u'Prénom :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, self.inscrit, 'famille.referents[%d].prenom' % index), 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Nom :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, self.inscrit, 'famille.referents[%d].nom' % index), 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Téléphone :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoPhoneCtrl(self, self.inscrit, 'famille.referents[%d].telephone' % index), 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)])
        delbutton = wx.BitmapButton(self, -1, self.delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        self.Bind(wx.EVT_BUTTON, self.OnSuppressionReferent, delbutton)
        self.referents_sizer.Add(sizer, 0, wx.EXPAND|wx.BOTTOM, 5)            

    def SupprimeLigneReferent(self):
        index = len(self.referents_sizer.GetChildren()) - 1
        sizer = self.referents_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.referents_sizer.Detach(index)
    
    def OnAjoutReferent(self, event):
        history.Append(Delete(self.inscrit.famille.referents, -1))
        self.inscrit.famille.referents.append(Referent(self.inscrit.famille))
        self.AjoutLigneReferent(len(self.inscrit.famille.referents) - 1)
        self.sizer.FitInside(self)

    def OnSuppressionReferent(self, event):
        index = event.GetEventObject().index
        history.Append(Insert(self.inscrit.famille.referents, index, self.inscrit.famille.referents[index]))
        self.SupprimeLigneReferent()
        self.inscrit.famille.referents[index].delete()
        del self.inscrit.famille.referents[index]
        self.UpdateContents()
        self.sizer.FitInside(self)


class ReferencePlanningPanel(PlanningWidget):
    def __init__(self, parent, activity_choice):
        PlanningWidget.__init__(self, parent, activity_choice, options=NO_ICONS|PRESENCES_ONLY|ACTIVITES|DEPASSEMENT_CAPACITE, check_line=self.CheckLine, on_modify=self.OnPlanningChanged)
        self.parent = parent
        
    def CheckLine(self, line, plages):
        if creche.seuil_alerte_inscription > 0:
            dates_depassement = []
            for date in self.inscription.GetDatesFromReference(line.day):
                if not self.CheckDate(date, plages):
                    dates_depassement.append(date)
                    if len(dates_depassement) == creche.seuil_alerte_inscription:
                        dlg = wx.MessageDialog(None, u"Dépassement de la capacité sur ce créneau horaire les:\n" + "\n".join([(" - " + GetDateString(date)) for date in dates_depassement]), "Attention", wx.OK|wx.ICON_WARNING)
                        dlg.ShowModal()
                        dlg.Destroy()
                        self.state = None
                        return
    
    def OnPlanningChanged(self, line):
        self.parent.UpdateDecompteConges()
               
    def CheckDate(self, date, plages):
        capacite = creche.GetCapacite(date.weekday())
        lines = GetLines(date, creche.inscrits)
        activites, activites_sans_horaires = GetActivitiesSummary(creche, lines)
        for start, end in plages:                        
            for i in range(start, end):
                if activites[0][i][0] > capacite:
                    return False
        return True
   
    def UpdateContents(self):
        lines = []
        if self.inscription:
            for day in range(self.inscription.duree_reference):
                if JourSemaineAffichable(day):
                    line = self.inscription.reference[day]
                    line.insert = None
                    line.day = day
                    line.label = days[day % 7]
                    line.sublabel = ""
                    line.reference = None
                    line.summary = SUMMARY_ENFANT
                    line.options |= ACTIVITES
                    lines.append(line)
        self.SetLines(lines)

    def SetInscription(self, inscription):
        self.inscription = inscription
        self.UpdateContents()


class ModeAccueilPanel(InscriptionsTab, PeriodeMixin):
    def __init__(self, parent):
        InscriptionsTab.__init__(self, parent)
        PeriodeMixin.__init__(self, 'inscriptions')
        sizer = wx.BoxSizer(wx.VERTICAL)
        ligne_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ligne_sizer.Add(PeriodeChoice(self, self.nouvelleInscription))
        self.validation_button = wx.ToggleButton(self, -1, u"Invalider l'inscription")
        ligne_sizer.Add(self.validation_button, 0, wx.LEFT, 10)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnValidationInscription, self.validation_button)    
        sizer.Add(ligne_sizer, 0, wx.TOP, 5)
        grid_sizer = wx.FlexGridSizer(0, 2, 5, 10)
        grid_sizer.AddGrowableCol(1, 1)
        
        self.sites_items = wx.StaticText(self, -1, u"Site :"), AutoChoiceCtrl(self, None, 'site'), wx.StaticText(self, -1, u"Sites de préinscription :"), wx.CheckListBox(self, -1)
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckPreinscriptionSite, self.sites_items[3])
        self.UpdateSiteItems()
        grid_sizer.AddMany([(self.sites_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.sites_items[1], 0, wx.EXPAND)])
        grid_sizer.AddMany([(self.sites_items[2], 0, wx.ALIGN_CENTER_VERTICAL), (self.sites_items[3], 0, wx.EXPAND)])
        
        if config.options & RESERVATAIRES:
            self.reservataire_items = wx.StaticText(self, -1, u"Réservataire :"), AutoChoiceCtrl(self, None, 'reservataire')
            self.UpdateReservataireItems()
            grid_sizer.AddMany([(self.reservataire_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.reservataire_items[1], 0, wx.EXPAND)])
            
        self.groupe_items = wx.StaticText(self, -1, u"Groupe :"), AutoChoiceCtrl(self, None, 'groupe')
        self.UpdateGroupeItems()
        grid_sizer.AddMany([(self.groupe_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.groupe_items[1], 0, wx.EXPAND)])
        
        self.professeur_items = wx.StaticText(self, -1, u"Professeur :"), AutoChoiceCtrl(self, None, 'professeur')
        self.UpdateProfesseurItems()
        grid_sizer.AddMany([(self.professeur_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.professeur_items[1], 0, wx.EXPAND)])
        
        self.mode_accueil_choice = AutoChoiceCtrl(self, None, 'mode', items=ModeAccueilItems)
        self.Bind(wx.EVT_CHOICE, self.OnModeAccueilChoice, self.mode_accueil_choice)
        grid_sizer.AddMany([(wx.StaticText(self, -1, u"Mode d'accueil :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.mode_accueil_choice, 0, wx.EXPAND)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, u"Frais d'inscription :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoNumericCtrl(self, None, 'frais_inscription', min=0, precision=2), 0, wx.EXPAND)])
        if creche.mode_facturation == FACTURATION_PAJE:
            grid_sizer.AddMany([(wx.StaticText(self, -1, u"Allocation mensuelle CAF :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoNumericCtrl(self, None, 'allocation_mensuelle_caf', min=0, precision=2), 0, wx.EXPAND)])
        label_conges = wx.StaticText(self, -1, u"Nombre de semaines d'absence prévu au contrat :")
        semaines_conges = AutoNumericCtrl(self, None, 'semaines_conges', min=0, precision=0)
        self.jours_poses = wx.TextCtrl(self, -1)
        self.jours_poses.Disable()
        self.semaines_conges_items = label_conges, semaines_conges, self.jours_poses
        self.heures_and_jours_reference = wx.TextCtrl(self, -1)
        self.heures_and_jours_reference.Disable()
        self.Bind(wx.EVT_TEXT, self.UpdateDecompteConges, self.semaines_conges_items[1])
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.AddMany([(semaines_conges, 0, wx.EXPAND), (self.jours_poses, 1, wx.EXPAND|wx.LEFT, 5)])
        grid_sizer.AddMany([(label_conges, 0, wx.ALIGN_CENTER_VERTICAL), (sizer3, 0, wx.EXPAND)])
        if creche.type == TYPE_PARENTAL:
            grid_sizer.AddMany([(wx.StaticText(self, -1, u"Heures de permanences à effectuer :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoNumericCtrl(self, None, 'heures_permanences', min=0, precision=2), 0, wx.EXPAND)])
        self.facturation_items = wx.StaticText(self, -1, u"Forfait mensuel :"), AutoNumericCtrl(self, None, 'forfait_mensuel', min=0, precision=2)
        grid_sizer.AddMany([(self.facturation_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.facturation_items[1], 0, wx.EXPAND)])
        grid_sizer.AddMany([(wx.StaticText(self, -1, u"Date de fin de la période d'adaptation :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoDateCtrl(self, None, 'fin_periode_adaptation'), 0, wx.EXPAND)])
        if creche.gestion_depart_anticipe:
            grid_sizer.AddMany([(wx.StaticText(self, -1, u"Date de départ anticipé :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoDateCtrl(self, None, 'depart'), 0, wx.EXPAND)])
        self.duree_reference_choice = wx.Choice(self)
        for item, data in [("1 semaine", 7)] + [("%d semaines" % (i + 2), 7 * (i + 2)) for i in range(MAX_SEMAINES_REFERENCE-1)]:
            self.duree_reference_choice.Append(item, data)
        self.Bind(wx.EVT_CHOICE, self.OnDureeReferenceChoice, self.duree_reference_choice)
        grid_sizer.AddMany([(wx.StaticText(self, -1, u"Durée de la période de référence :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.duree_reference_choice, 0, wx.EXPAND)])
        self.forfait_mensuel_heures_static = wx.StaticText(self, -1, u"Forfait mensuel en heures :")
        self.forfait_mensuel_heures_ctrl = AutoNumericCtrl(self, None, 'forfait_mensuel_heures', min=0, precision=2)
        grid_sizer.AddMany([(self.forfait_mensuel_heures_static, 0, wx.ALIGN_CENTER_VERTICAL), (self.forfait_mensuel_heures_ctrl, 0, wx.EXPAND)])
        sizer.Add(grid_sizer, 0, wx.ALL|wx.EXPAND, 5)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.heures_and_jours_reference, 1, wx.ALIGN_CENTER_VERTICAL)
        self.button_5_5 = wx.Button(self, -1, u"Plein temps")
        self.Bind(wx.EVT_BUTTON, self.OnMode_5_5, self.button_5_5)
        self.button_copy = wx.Button(self, -1, u"Recopier lundi sur toute la période")
        sizer2.AddMany([(self.button_5_5, 0, wx.ALIGN_CENTER_VERTICAL), (self.button_copy, 0, wx.ALIGN_CENTER_VERTICAL)])
        self.Bind(wx.EVT_BUTTON, self.OnMondayCopy, self.button_copy)
        self.activity_choice = ActivityComboBox(self)        
        sizer2.Add(self.activity_choice, 0, wx.ALIGN_RIGHT)
        grid_sizer.AddMany([(wx.StaticText(self, -1, u"Temps de présence :"), 0, wx.ALIGN_CENTER_VERTICAL), (sizer2, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)])
        self.planning_panel = ReferencePlanningPanel(self, self.activity_choice)
        sizer.Add(self.planning_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.UpdateContents()
        
    def nouvelleInscription(self):  # TODO les autres pareil ...
        inscription = Inscription(self.inscrit)
        inscription.preinscription = creche.preinscriptions
        if len(creche.groupes) > 0 and self.inscrit.inscriptions:
            inscription.groupe = self.inscrit.inscriptions[-1].groupe
        return inscription

    def SetInscrit(self, inscrit):
        self.inscrit = inscrit
        self.SetInstance(inscrit)
        self.UpdateContents()
    
    def OnValidationInscription(self, event):
        obj = event.GetEventObject()
        inscription = self.inscrit.inscriptions[self.periode]
        if len(creche.sites) > 1:
            if obj.GetValue():
                if len(inscription.sites_preinscription) != 1:
                    if not inscription.sites_preinscription:
                        dlg = wx.MessageDialog(self, u"Avant de valider une inscription, il faut choisir un site de préinscription", 'Erreur', wx.OK|wx.ICON_WARNING)
                    else:
                        dlg = wx.MessageDialog(self, u"Avant de valider une inscription, il ne faut garder qu'un seul site de préinscription", 'Erreur', wx.OK|wx.ICON_WARNING)
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
        self.UpdateContents()
    
    def OnModeAccueilChoice(self, event):
        history.Append(None)
        self.inscrit.inscriptions[self.periode].mode = self.mode_accueil_choice.GetClientData(self.mode_accueil_choice.GetSelection())
        self.UpdateContents()        
        
    def OnDureeReferenceChoice(self, event):
        history.Append(None)
        duration = self.duree_reference_choice.GetClientData(self.duree_reference_choice.GetSelection())
        self.inscrit.inscriptions[self.periode].SetReferenceDuration(duration)
        self.UpdateContents()
        
    def OnMode_5_5(self, event):
        history.Append(None)
        inscription = self.inscrit.inscriptions[self.periode]
        inscription.mode = MODE_5_5
        for i, day in enumerate(inscription.reference):
            if JourSemaineAffichable(i):
                day.SetState(0)
        self.UpdateContents()
    
    def OnMondayCopy(self, event):
        history.Append(None)
        inscription = self.inscrit.inscriptions[self.periode]
        for i, day in enumerate(inscription.reference):
            if i > 0 and JourSemaineAffichable(i):
                day.Copy(inscription.reference[0], False)
                day.Save()
        self.UpdateContents()
            
    def OnCheckPreinscriptionSite(self, event):
        index = event.GetSelection()
        obj = event.GetEventObject()
        site = creche.sites[index]
        inscription = self.inscrit.inscriptions[self.periode]
        history.Append(Change(inscription, "sites_preinscription", inscription.sites_preinscription[:]))
        if obj.IsChecked(index):
            inscription.sites_preinscription.append(site)
        else:
            inscription.sites_preinscription.remove(site)
        inscription.sites_preinscription = inscription.sites_preinscription

    def UpdateSiteItems(self):
        if len(creche.sites) > 1:
            items = [(site.nom, site) for site in creche.sites]
            self.sites_items[1].SetItems(items)
            for nom, site in items:
                self.sites_items[3].Append(nom)
        else:
            for item in self.sites_items:
                item.Show(False)
        self.sites_observer = counters['sites']
    
    def UpdateReservataireItems(self):
        if len(creche.reservataires) > 0:
            reservataires = [("----", None)] + [(reservataire.nom, reservataire) for reservataire in creche.reservataires]
            self.reservataire_items[1].SetItems(reservataires)
            for item in self.reservataire_items:
                item.Show(True)
        else:
            for item in self.reservataire_items:
                item.Show(False)
        self.reservataires_observer = counters['reservataires']

    def UpdateGroupeItems(self):
        if len(creche.groupes) > 0:
            groupes = [("----", None)] + [(groupe.nom, groupe) for groupe in creche.groupes]
            self.groupe_items[1].SetItems(groupes)
            for item in self.groupe_items:
                item.Show(True)
        else:
            for item in self.groupe_items:
                item.Show(False)
        self.groupes_observer = counters["groupes"]

    def UpdateProfesseurItems(self):
        if creche.type == TYPE_GARDERIE_PERISCOLAIRE and len(creche.professeurs) > 0:
            professeurs = [("%s %s" % (professeur.prenom, professeur.nom), professeur) for professeur in creche.professeurs]
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
        if inscription:
            self.jours_poses.SetValue(u"%d jours posés / %d jours" % (inscription.GetNombreJoursCongesPoses(), inscription.GetNombreJoursCongesPeriode()))
            self.heures_and_jours_reference.SetValue(u"%s heures / %s jours" % (Number2String(inscription.GetNombreHeuresPresenceSemaine()), Number2String(inscription.GetNombreJoursPresenceSemaine())))
        else:
            self.jours_poses.SetValue("")
            self.heures_and_jours_reference.SetValue("")
        
    def UpdateContents(self):
        if counters['sites'] > self.sites_observer:
            self.UpdateSiteItems()
        if counters['groupes'] > self.groupes_observer:
            self.UpdateGroupeItems()
        if config.options & RESERVATAIRES and counters['reservataires'] > self.reservataires_observer:
            self.UpdateReservataireItems()
        if counters['professeurs'] > self.professeurs_observer:
            self.UpdateProfesseurItems()

        InscriptionsTab.UpdateContents(self)
        self.mode_accueil_choice.Enable(creche.modes_inscription != MODE_5_5)
        self.validation_button.Show(creche.preinscriptions)

        self.InternalUpdate()
        self.activity_choice.Update()

        for item in self.semaines_conges_items:
            item.Show(creche.mode_facturation in (FACTURATION_PAJE, FACTURATION_PSU))
            
        for item in self.facturation_items:
            item.Show(creche.mode_facturation == FACTURATION_FORFAIT_MENSUEL)
                            
        self.Layout()

    def SetPeriode(self, periode):
        PeriodeMixin.SetPeriode(self, periode)
        self.InternalUpdate()
    
    def InternalUpdate(self):
        if self.inscrit and self.periode is not None and self.periode != -1 and self.periode < len(self.inscrit.inscriptions):
            inscription = self.inscrit.inscriptions[self.periode]
            for obj in [self.duree_reference_choice, self.mode_accueil_choice, self.button_5_5, self.button_copy, self.validation_button]:
                obj.Enable(not readonly)
            if creche.preinscriptions:
                if inscription.preinscription:
                    self.validation_button.SetValue(False)
                    self.validation_button.SetLabel("Valider l'inscription")
                    if len(creche.sites) > 1:
                        for item in self.sites_items[0:2]:
                            item.Show(False)
                        for item in self.sites_items[2:4]:
                            item.Show(True)
                        self.sites_items[3].SetCheckedStrings([site.nom for site in inscription.sites_preinscription])
                else:
                    self.validation_button.SetValue(True)
                    self.validation_button.SetLabel("Invalider l'inscription")
                    if len(creche.sites) > 1:
                        for item in self.sites_items[0:2]:
                            item.Show(True)
                        for item in self.sites_items[2:4]:
                            item.Show(False)
            elif len(creche.sites) > 1:
                for item in self.sites_items[0:2]:
                    item.Show(True)
                for item in self.sites_items[2:4]:
                    item.Show(False)
                    
            self.forfait_mensuel_heures_ctrl.Show(inscription.mode == MODE_FORFAIT_HORAIRE)
            self.forfait_mensuel_heures_static.Show(inscription.mode == MODE_FORFAIT_HORAIRE)
            self.duree_reference_choice.SetSelection(inscription.duree_reference / 7 - 1)
            self.planning_panel.SetInscription(inscription)
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
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.conges_creche_sizer = wx.BoxSizer(wx.VERTICAL)
        self.AfficheCongesCreche()
        self.sizer.Add(self.conges_creche_sizer, 0, wx.ALL, 5)
        
        self.conges_inscrit_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.conges_inscrit_sizer, 0, wx.ALL, 5)
        
        self.nouveau_conge_button = wx.Button(self, -1, u"Ajouter une période d'absence")
        self.sizer.Add(self.nouveau_conge_button, 0, wx.EXPAND+wx.TOP, 5)
        self.Bind(wx.EVT_BUTTON, self.OnAjoutConge, self.nouveau_conge_button)

#        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
#        sizer2.AddMany([(wx.StaticText(self, -1, u'Nombre de semaines de congés déduites :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoNumericCtrl(self, creche, 'semaines_conges', min=0, precision=0), 0, wx.EXPAND)])
#        self.sizer.Add(sizer2, 0, wx.EXPAND+wx.TOP, 5)

        self.SetSizer(self.sizer)

    def UpdateContents(self):
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
        self.sizer.Layout()
        AutoTab.UpdateContents(self)
        
    def SetInscrit(self, inscrit):
        self.inscrit = inscrit
        self.UpdateContents()
        InscriptionsTab.SetInscrit(self, inscrit)
        self.nouveau_conge_button.Enable(self.inscrit is not None and not readonly)

    def AfficheCongesCreche(self):
        self.conges_creche_sizer.DeleteWindows()
        labels_conges = [j[0] for j in jours_fermeture]
        for text in labels_conges:
            checkbox = wx.CheckBox(self, -1, text)
            checkbox.Disable()
            if text in creche.feries:
                checkbox.SetValue(True)
            self.conges_creche_sizer.Add(checkbox, 0, wx.EXPAND)
        for conge in creche.conges:
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.AddMany([(wx.StaticText(self, -1, 'Debut :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, conge, 'debut', mois=True, fixed_instance=True)])
            sizer.AddMany([(wx.StaticText(self, -1, 'Fin :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, conge, 'fin', mois=True, fixed_instance=True)])
            sizer.AddMany([(wx.StaticText(self, -1, u'Libellé :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, conge, 'label', fixed_instance=True)])
            for child in sizer.GetChildren():
                child.GetWindow().Disable()
            self.conges_creche_sizer.Add(sizer)
        self.conges_observer = counters['conges']

    def AjouteLigneConge(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, 'Debut :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, self.inscrit, 'conges[%d].debut' % index, mois=True)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Fin :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, self.inscrit, 'conges[%d].fin' % index, mois=True)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Libellé :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, self.inscrit, 'conges[%d].label' % index)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.OnSuppressionConge, delbutton)
        self.conges_inscrit_sizer.Add(sizer)
        
    def SupprimeLigneConge(self):
        index = len(self.conges_inscrit_sizer.GetChildren()) - 1
        sizer = self.conges_inscrit_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.conges_inscrit_sizer.Detach(index)

    def OnAjoutConge(self, event):
        history.Append(Delete(self.inscrit.conges, -1))
        self.inscrit.AddConge(CongeInscrit(self.inscrit))
        self.AjouteLigneConge(len(self.inscrit.conges) - 1)
        self.sizer.Layout()

    def OnSuppressionConge(self, event):
        index = event.GetEventObject().index
        history.Append(Insert(self.inscrit.conges, index, self.inscrit.conges[index]))
        self.SupprimeLigneConge()
        conge = self.inscrit.conges[index]
        del self.inscrit.conges[index]
        conge.delete()
        self.sizer.Layout()
        self.UpdateContents()
        
class NotesPanel(InscriptionsTab):
    def __init__(self, parent):        
        InscriptionsTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(AutoTextCtrl(self, None, 'notes', style=wx.TE_MULTILINE), 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(self.sizer)
        
class InscriptionsNotebook(wx.Notebook):
    def __init__(self, parent, *args, **kwargs):
        wx.Notebook.__init__(self, parent, style=wx.LB_DEFAULT, *args, **kwargs)      
        self.parent = parent
        self.inscrit = None

        self.AddPage(IdentitePanel(self), u'Identité')
        self.AddPage(ParentsPanel(self), u'Parents et référents')
        self.AddPage(ModeAccueilPanel(self), "Mode d'accueil")
        if creche.conges_inscription:
            self.conges_panel = CongesPanel(self)
            self.AddPage(self.conges_panel, u"Absences prévues au contrat")
        else:
            self.conges_panel = None
        self.AddPage(NotesPanel(self), "Notes")
        if profil & PROFIL_TRESORIER:
            self.AddPage(FraisGardePanel(self), 'Frais de garde')

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)  
            
    def OnChangementPrenomNom(self, event):
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
        if creche.conges_inscription and not self.conges_panel:
            self.conges_panel = CongesPanel(self)
            self.conges_panel.SetInscrit(self.inscrit)
            self.InsertPage(3, self.conges_panel, u"Absences prévues au contrat")
        elif self.conges_panel and not creche.conges_inscription:
            self.RemovePage(3)
            self.conges_panel.Destroy()
            self.conges_panel = None
        self.GetCurrentPage().UpdateContents()
            
class InscriptionsPanel(GPanel):
    name = "Inscriptions"
    bitmap = GetBitmapFile("inscriptions.png")
    profil = PROFIL_ALL
    
    def __init__(self, parent):
        GPanel.__init__(self, parent, "Inscriptions")

        # Le control pour la selection de l'enfant
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.choice = wx.Choice(self)
        self.Bind(wx.EVT_CHOICE, self.OnInscritChoice, self.choice)
        plusbmp = wx.Bitmap(GetBitmapFile("plus.png"), wx.BITMAP_TYPE_PNG)
        delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        self.addbutton = wx.BitmapButton(self, -1, plusbmp)
        self.delbutton = wx.BitmapButton(self, -1, delbmp)
        self.addbutton.SetToolTipString(u"Ajouter un enfant")
        self.delbutton.SetToolTipString(u"Supprimer cet enfant")
        self.Bind(wx.EVT_BUTTON, self.OnAjoutInscrit, self.addbutton)
        self.Bind(wx.EVT_BUTTON, self.OnSuppressionInscrit, self.delbutton)
        sizer.AddMany([(self.choice, 1, wx.EXPAND|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (self.addbutton, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (self.delbutton, 0, wx.ALIGN_CENTER_VERTICAL)])
        self.sizer.Add(sizer, 0, wx.EXPAND|wx.LEFT, MACOS_MARGIN)
        # le notebook pour la fiche d'inscription
        self.notebook = InscriptionsNotebook(self)
        self.sizer.Add(self.notebook, 1, wx.EXPAND|wx.TOP, 5)
        self.InitInscrits()

    def UpdateContents(self):
        self.notebook.UpdateContents()
            
    def InitInscrits(self, selected=None):
        AddInscritsToChoice(self.choice)
        if len(creche.inscrits) > 0 and selected != None and selected in creche.inscrits:
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

    def OnAjoutInscrit(self, evt):
        history.Append(Delete(creche.inscrits, -1))
        inscrit = Inscrit()
        creche.inscrits.append(inscrit)
        self.InitInscrits(inscrit)
        self.notebook.SetInscrit(inscrit)
        self.notebook.SetSelection(0) # Selectionne la page identite

    def OnSuppressionInscrit(self, evt):
        selected = self.choice.GetSelection()
        inscrit = self.choice.GetClientData(selected)
        if inscrit:
            dlg = wx.MessageDialog(self,
                                   u'Cette inscription va être supprimée, êtes-vous sûr de vouloir continuer ?',
                                   'Confirmation',
                                   wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION )
            if dlg.ShowModal() == wx.ID_YES:
                index = creche.inscrits.index(inscrit)
                history.Append(Insert(creche.inscrits, index, inscrit))
                inscrit.delete()
                del creche.inscrits[index]
                self.choice.Delete(selected)
                self.choice.SetSelection(-1)
                self.notebook.SetInscrit(None)
                self.delbutton.Disable()
            dlg.Destroy()
        
    def ChangePrenom(self, inscrit):
        if creche and inscrit:
            inscritId = GetPrenomNom(inscrit)
            if inscritId.isspace():
                inscritId = 'Nouvelle inscription'
            selection = self.choice.GetSelection()
            self.choice.SetString(selection, '  ' + inscritId)
            self.choice.SetSelection(selection)
                                