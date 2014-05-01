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

import os, datetime, time, xml.dom.minidom, cStringIO
import wx, wx.lib.scrolledpanel, wx.html
from constants import *
from sqlobjects import *
from controls import *
from planning import *
from cotisation import *
from ooffice import *
from contrat_accueil import ContratAccueilModifications, FraisGardeModifications

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
    
class FraisAccueilPanel(wx.Panel):
    def __init__(self, parent):
        self.parent = parent
        wx.Panel.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.periodechoice = wx.Choice(self, size=(150,-1))
        self.Bind(wx.EVT_CHOICE, self.EvtPeriodeChoice, self.periodechoice)
        sizer1.Add(self.periodechoice, 0)
        self.frais_accueil_button = wx.Button(self, -1, u"Exporter")
        sizer1.Add(self.frais_accueil_button, 0, wx.LEFT, 5)
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationFraisAccueil, self.frais_accueil_button)
        self.contrat_button = wx.Button(self, -1, u"Générer le contrat")
        sizer1.Add(self.contrat_button, 0, wx.LEFT, 5)
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationContrat, self.contrat_button)
        if IsTemplateFile("Avenant contrat accueil.odt"):
            self.avenant_button = wx.Button(self, -1, u"Générer un avenant")
            sizer1.Add(self.avenant_button, 0, wx.LEFT, 5)
            self.Bind(wx.EVT_BUTTON, self.EvtGenerationAvenant, self.avenant_button)
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
                self.html = u"<html><body><b>Les frais de garde ne peuvent être calcul&eacute;s pour la (les) raison(s) suivante(s) :</b><br>" + error  + "</body></html>"
                self.frais_accueil_button.Disable()
                self.contrat_button.Disable()
            else:
                if creche.mode_facturation == FACTURATION_FORFAIT_MENSUEL:
                    filename = "Frais accueil forfait.html"
                elif creche.mode_facturation == FACTURATION_HORAIRES_REELS:
                    filename = "Frais accueil reel.html"
                elif creche.mode_facturation == FACTURATION_PAJE:
                    filename = "Frais accueil paje.html"
                else:
                    filename = "Frais accueil defaut.html"   
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
                self.current_cotisation = self.cotisations[-1]
                self.periodechoice.Enable()
                self.frais_accueil_button.Enable()
                self.contrat_button.Enable()
                for c in self.cotisations:
                    self.periodechoice.Append(date2str(c[0]) + ' - ' + date2str(c[1]))
                self.periodechoice.SetSelection(self.periodechoice.GetCount() - 1)
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

    def EvtGenerationContrat(self, evt):
        DocumentDialog(self, ContratAccueilModifications(self.inscrit, self.current_cotisation[0])).ShowModal()

    def EvtGenerationAvenant(self, evt):
        DocumentDialog(self, ContratAccueilModifications(self.inscrit, self.current_cotisation[0], avenant=True)).ShowModal()
            
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

def getPictoBitmap(index, size=64):
    if isinstance(index, int):
        index = chr(ord('a')+index)
    bitmap = wx.Bitmap(GetBitmapFile("pictos/%c.png" % index), wx.BITMAP_TYPE_PNG)
    image = wx.ImageFromBitmap(bitmap)
    image = image.Scale(size, size, wx.IMAGE_QUALITY_HIGH)
    return wx.BitmapFromImage(image)
    
class CombinaisonDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "Nouvelle combinaison", wx.DefaultPosition, wx.DefaultSize)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        gridSizer = wx.FlexGridSizer(5, 4, 5, 5)
        self.combinaison= []
        for i in range(20):
            picto = wx.BitmapButton(self, -1, getPictoBitmap(i), style=wx.BU_EXACTFIT)
            picto.picto = chr(ord('a')+i)
            self.Bind(wx.EVT_BUTTON, self.onPressPicto, picto)
            gridSizer.Add(picto)            
        self.sizer.Add(gridSizer, 0, wx.EXPAND|wx.ALL, 5)

        self.combinaisonPanel = wx.Panel(self, style=wx.SUNKEN_BORDER)
        self.combinaisonPanel.SetMinSize((-1, 36))
        self.combinaisonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.combinaisonPanel.SetSizer(self.combinaisonSizer)
        self.sizer.Add(self.combinaisonPanel, 0, wx.EXPAND)
        
        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        btnsizer.AddButton(btn)
        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()       
        self.sizer.Add(btnsizer, 0, wx.ALL, 5)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
    
    def onPressPicto(self, event):
        sender = event.GetEventObject()
        picto = sender.picto
        self.combinaison.append(picto)       
        bmp = getPictoBitmap(picto, size=32)
        button = wx.StaticBitmap(self.combinaisonPanel, -1, bmp)
        self.combinaisonSizer.Add(button, 0, wx.LEFT, 5)
        self.combinaisonSizer.Layout()
    
    def getCombinaison(self):
        return "".join(self.combinaison)

class IdentitePanel(InscriptionsTab):
    def __init__(self, parent):
        InscriptionsTab.__init__(self, parent)
        self.last_tarifs_observer = -1
        self.inscrit = None
        self.delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.FlexGridSizer(0, 2, 5, 10)
        self.sizer2 = sizer2
        sizer2.AddGrowableCol(1, 1)
        prenom_ctrl = AutoTextCtrl(self, None, 'prenom')
        self.Bind(wx.EVT_TEXT, self.EvtChangementPrenomNom, prenom_ctrl)
        nom_ctrl = AutoTextCtrl(self, None, 'nom')
        self.Bind(wx.EVT_TEXT, self.EvtChangementPrenomNom, nom_ctrl)
        sizer2.AddMany([(wx.StaticText(self, -1, u'Prénom :'), 0, wx.ALIGN_CENTER_VERTICAL), (prenom_ctrl, 0, wx.EXPAND)])
        sizer2.AddMany([(wx.StaticText(self, -1, 'Nom :'), 0, wx.ALIGN_CENTER_VERTICAL), (nom_ctrl, 0, wx.EXPAND)])
        sizer2.AddMany([(wx.StaticText(self, -1, 'Sexe :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoChoiceCtrl(self, None, 'sexe', items=[(u"Garçon", 1), ("Fille", 2)]), 0, wx.EXPAND)])
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.age_ctrl = wx.TextCtrl(self, -1)
        self.age_ctrl.Disable()
        self.date_naissance_ctrl = AutoDateCtrl(self, None, 'naissance')
        self.Bind(wx.EVT_TEXT, self.EvtChangementDateNaissance, self.date_naissance_ctrl)
        sizer3.AddMany([(self.date_naissance_ctrl, 1, wx.EXPAND), (self.age_ctrl, 1, wx.EXPAND|wx.LEFT, 5)])
        sizer2.AddMany([(wx.StaticText(self, -1, 'Date de naissance :'), 0, wx.ALIGN_CENTER_VERTICAL), (sizer3, 0, wx.EXPAND)])
        sizer2.AddMany([(wx.StaticText(self, -1, 'Adresse :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoTextCtrl(self, None, 'adresse'), 0, wx.EXPAND)])
        self.ville_ctrl = AutoTextCtrl(self, None, 'ville') # A laisser avant le code postal !
        self.code_postal_ctrl = AutoNumericCtrl(self, None, 'code_postal', min=0, precision=0)
        self.Bind(wx.EVT_TEXT, self.EvtChangementCodePostal, self.code_postal_ctrl)
        sizer2.AddMany([(wx.StaticText(self, -1, 'Code Postal :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.code_postal_ctrl, 0, wx.EXPAND)])
        sizer2.AddMany([(wx.StaticText(self, -1, 'Ville :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.ville_ctrl, 0, wx.EXPAND)])
        sizer2.AddMany([(wx.StaticText(self, -1, u'Numéro de sécurité sociale :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoTextCtrl(self, None, 'numero_securite_sociale'), 0, wx.EXPAND)])
        sizer2.AddMany([(wx.StaticText(self, -1, u"Numéro d'allocataire CAF :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoTextCtrl(self, None, 'numero_allocataire_caf'), 0, wx.EXPAND)])

        if config.options & CATEGORIES:
            self.categorie_items = wx.StaticText(self, -1, u"Catégorie :"), AutoChoiceCtrl(self, None, 'categorie')  
            sizer2.AddMany([(self.categorie_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.categorie_items[1], 0, wx.EXPAND)])
            self.UpdateCategorieItems()

        sizer2.AddMany([(wx.StaticText(self, -1, u"Enfant handicapé :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoCheckBox(self, None, 'handicap'), 0, wx.EXPAND)])
##        sizer2.AddMany([(wx.StaticText(self, -1, 'Date de marche :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoDateCtrl(self, None, 'marche'), 0, wx.EXPAND)])
        self.sizer.Add(sizer2, 0, wx.EXPAND|wx.ALL, 5)
        
        self.tarifs_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.tarifs_sizer, 0, wx.EXPAND|wx.ALL, 5)
        
        sizer3 = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Frères et soeurs'), wx.VERTICAL)
        self.fratries_sizer = wx.BoxSizer(wx.VERTICAL)
        sizer3.Add(self.fratries_sizer, 0, wx.EXPAND+wx.RIGHT+wx.LEFT+wx.TOP, 10)
        self.nouveau_frere = wx.Button(self, -1, u'Nouveau frère ou nouvelle soeur')
        self.nouveau_frere.Disable()
        sizer3.Add(self.nouveau_frere, 0, wx.RIGHT+wx.LEFT+wx.BOTTOM, 10)
        self.Bind(wx.EVT_BUTTON, self.EvtNouveauFrere, self.nouveau_frere)
        self.sizer.Add(sizer3, 0, wx.EXPAND|wx.ALL, 5)

        if config.options & TABLETTE: 
            tabletteSizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Tablette'), wx.VERTICAL)
            internalSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.combinaisonSizer = wx.BoxSizer(wx.HORIZONTAL)
            internalSizer.Add(self.combinaisonSizer)
            settingsbmp = wx.Bitmap(GetBitmapFile("settings.png"), wx.BITMAP_TYPE_PNG)
            button = wx.BitmapButton(self, -1, settingsbmp)
            self.Bind(wx.EVT_BUTTON, self.onModifyCombinaison, button)           
            internalSizer.Add(button, 0, wx.LEFT, 10)
            tabletteSizer.Add(internalSizer, 0, wx.TOP|wx.BOTTOM, 10)
            self.sizer.Add(tabletteSizer, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(self.sizer)
        self.sizer.FitInside(self)

    def onModifyCombinaison(self, event):
        dlg = CombinaisonDialog(self)
        res = dlg.ShowModal()
        if res == wx.ID_OK:
            self.inscrit.combinaison = dlg.getCombinaison()
            self.UpdateCombinaison()
        dlg.Destroy()        

    def UpdateCategorieItems(self):
        if len(creche.categories) > 0:
            categories = [("----", None)] + [(categorie.nom, categorie) for categorie in creche.categories]
            self.categorie_items[1].SetItems(categories)
            for item in self.categorie_items:
                item.Show(True)
        else:
            for item in self.categorie_items:
                item.Show(False)
        self.last_categorie_observer = time.time()
        
    def UpdateCombinaison(self):
        if self.inscrit and config.options & TABLETTE: 
            self.combinaisonSizer.DeleteWindows()
            if self.inscrit.combinaison:
                for letter in self.inscrit.combinaison:
                    bitmap = getPictoBitmap(letter, size=32)
                    picto = wx.StaticBitmap(self, -1, bitmap)
                    self.combinaisonSizer.Add(picto, 0, wx.LEFT, 10)
            self.combinaisonSizer.Layout()
            self.sizer.Layout()
        
    def frere_line_add(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, u'Prénom :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, self.inscrit, 'freres_soeurs[%d].prenom' % index), 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Naissance :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoDateCtrl(self, self.inscrit, 'freres_soeurs[%d].naissance' % index), 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, u'En crèche du'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoDateCtrl(self, self.inscrit, 'freres_soeurs[%d].entree' % index), 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, 'au'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoDateCtrl(self, self.inscrit, 'freres_soeurs[%d].sortie' % index), 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)])
        delbutton = wx.BitmapButton(self, -1, self.delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        self.Bind(wx.EVT_BUTTON, self.EvtSuppressionFrere, delbutton)
        self.fratries_sizer.Add(sizer, 0, wx.EXPAND|wx.BOTTOM, 5)

    def frere_line_del(self):
        index = len(self.fratries_sizer.GetChildren()) - 1
        sizer = self.fratries_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.fratries_sizer.Detach(index)
        
    def EvtChangementPrenomNom(self, event):
        event.GetEventObject().onText(event)
        self.parent.EvtChangementPrenomNom(event)

    def EvtChangementDateNaissance(self, event):
        date_naissance = self.date_naissance_ctrl.GetValue()
        self.age_ctrl.SetValue(GetAgeString(date_naissance))

    def EvtChangementCodePostal(self, event):
        code_postal = self.code_postal_ctrl.GetValue()
        if code_postal and not self.ville_ctrl.GetValue():
            for inscrit in creche.inscrits:
                if inscrit.code_postal == code_postal and inscrit.ville:
                    self.ville_ctrl.SetValue(inscrit.ville)
                    break

    def EvtNouveauFrere(self, event):
        history.Append(Delete(self.inscrit.freres_soeurs, -1))
        self.inscrit.freres_soeurs.append(Frere_Soeur(self.inscrit))
        self.frere_line_add(len(self.inscrit.freres_soeurs) - 1)
        self.sizer.FitInside(self)

    def EvtSuppressionFrere(self, event):
        index = event.GetEventObject().index
        history.Append(Insert(self.inscrit.freres_soeurs, index, self.inscrit.freres_soeurs[index]))
        self.frere_line_del()
        self.inscrit.freres_soeurs[index].delete()
        del self.inscrit.freres_soeurs[index]
        self.UpdateContents()
        self.sizer.FitInside(self)
        
    def UpdateContents(self):
        if self.last_tarifs_observer < 0 or ('tarifs' in observers and observers['tarifs'] > self.last_tarifs_observer):
            while len(self.tarifs_sizer.GetChildren()):
                sizer = self.tarifs_sizer.GetItem(0)
                sizer.DeleteWindows()
                self.tarifs_sizer.Detach(0)
            w = self.sizer2.GetColWidths()[0] + 10
            for tarif in creche.tarifs_speciaux:
                sizer = wx.BoxSizer(wx.HORIZONTAL)
                sizer.AddMany([(wx.StaticText(self, -1, u'%s :' % tarif.label, size=(w, -1)), 0, wx.ALIGN_CENTER_VERTICAL), (AutoCheckBox(self, self.inscrit, 'tarifs', value=1<<tarif.idx), 0, wx.EXPAND)])
                self.tarifs_sizer.Add(sizer, 0, wx.EXPAND|wx.BOTTOM, 10)
            self.last_tarifs_observer = time.time()
        if self.inscrit:
            freres_count = len(self.inscrit.freres_soeurs)
            for i in range(len(self.fratries_sizer.GetChildren()), freres_count):
                self.frere_line_add(i)
        else:
            freres_count = 0
        for i in range(freres_count, len(self.fratries_sizer.GetChildren())):
            self.frere_line_del()
        self.UpdateCombinaison()
        if 'categories' in observers and observers['categories'] > self.last_categorie_observer:
            self.UpdateCategorieItems()

        AutoTab.UpdateContents(self)
        self.sizer.FitInside(self)
        
    def SetInscrit(self, inscrit):
        self.inscrit = inscrit
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
            sizer2.AddMany([(wx.StaticText(self, -1, 'Relation :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.relations_items[-1], 0, wx.EXPAND)])           
            self.parents_items[-1].extend([wx.StaticText(self, -1, u'Prénom :'), AutoTextCtrl(self, None, 'prenom')])           
            sizer2.AddMany([(self.parents_items[-1][-2], 0, wx.ALIGN_CENTER_VERTICAL), (self.parents_items[-1][-1], 0, wx.EXPAND)])
            self.parents_items[-1].extend([wx.StaticText(self, -1, 'Nom :'), AutoTextCtrl(self, None, 'nom')])
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
                if not creche.formule_taux_horaire_needs_revenus():
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
                revenus_gridsizer.AddMany([(wx.StaticText(panel, -1, 'Revenus annuels bruts :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoNumericCtrl(panel, None, 'revenu', precision=2), 0, wx.EXPAND)])
                revenus_gridsizer.AddMany([(0, 0), (AutoCheckBox(panel, None, 'chomage', u'Chômage'), 0, wx.EXPAND)])
                self.revenus_items.extend([revenus_gridsizer.GetItem(0), revenus_gridsizer.GetItem(1), revenus_gridsizer.GetItem(2), revenus_gridsizer.GetItem(3)])
                if not creche.formule_taux_horaire_needs_revenus():
                    for item in self.revenus_items:
                        item.Show(False)
                choice = AutoChoiceCtrl(panel, None, 'regime')
                self.regimes_choices.append(choice)
                for i, regime in enumerate([u'Pas de sélection', u'Régime général', u'Régime de la fonction publique', u'Régime MSA', u'Régime EDF-GDF', u'Régime RATP', u'Régime Pêche maritime', u'Régime Marins du Commerce', u'Régime RSI']):
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
        self.Bind(wx.EVT_BUTTON, self.EvtNouveauReferent, self.nouveau_referent)
        self.sizer.Add(sizer4, 0, wx.EXPAND|wx.ALL, 5)
        
        sizer5 = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Notes'), wx.VERTICAL)
        self.notes_parents_ctrl = AutoTextCtrl(self, None, 'notes_parents', style=wx.TE_MULTILINE)
        sizer5.Add(self.notes_parents_ctrl, 0, wx.EXPAND+wx.RIGHT+wx.LEFT+wx.TOP, 10)
        self.sizer.Add(sizer5, 0, wx.EXPAND|wx.ALL, 5)
        
        self.SetSizer(self.sizer)

    def OnParentRelationChoice(self, event):
        object = event.GetEventObject()
        value = object.GetClientData(object.GetSelection())
        if value == None:
            self.inscrit.parents[object.instance.relation] = None
            object.instance.delete()
            for item in self.parents_items[object.index]:
                item.Show(False)
            self.sizer.FitInside(self)
        elif not self.inscrit.parents[value]:
            self.inscrit.parents[value] = parent = Parent(self.inscrit, value)
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
            for index, key in enumerate(self.inscrit.parents.keys()):
                parent = self.inscrit.parents[key]
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
            referents_count = len(self.inscrit.referents)
            for i in range(len(self.referents_sizer.GetChildren()), referents_count):
                self.referent_line_add(i)
        else:
            referents_count = 0
        for i in range(referents_count, len(self.referents_sizer.GetChildren())):
            self.referent_line_del()
        for item in self.revenus_items:
            item.Show(creche.formule_taux_horaire_needs_revenus())
        AutoTab.UpdateContents(self)
        self.sizer.FitInside(self)

    def SetInscrit(self, inscrit):
        self.inscrit = inscrit
        self.notes_parents_ctrl.SetInstance(inscrit)
        self.UpdateContents()
        self.nouveau_referent.Enable(self.inscrit is not None and not readonly)

    def referent_line_add(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, u'Prénom :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, self.inscrit, 'referents[%d].prenom' % index), 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Nom :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoTextCtrl(self, self.inscrit, 'referents[%d].nom' % index), 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Téléphone :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (AutoPhoneCtrl(self, self.inscrit, 'referents[%d].telephone' % index), 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 5)])
        delbutton = wx.BitmapButton(self, -1, self.delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
        self.Bind(wx.EVT_BUTTON, self.EvtSuppressionReferent, delbutton)
        self.referents_sizer.Add(sizer, 0, wx.EXPAND|wx.BOTTOM, 5)            

    def referent_line_del(self):
        index = len(self.referents_sizer.GetChildren()) - 1
        sizer = self.referents_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.referents_sizer.Detach(index)
    
    def EvtNouveauReferent(self, event):
        history.Append(Delete(self.inscrit.referents, -1))
        self.inscrit.referents.append(Referent(self.inscrit))
        self.referent_line_add(len(self.inscrit.referents) - 1)
        self.sizer.FitInside(self)

    def EvtSuppressionReferent(self, event):
        index = event.GetEventObject().index
        history.Append(Insert(self.inscrit.referents, index, self.inscrit.referents[index]))
        self.referent_line_del()
        self.inscrit.referents[index].delete()
        del self.inscrit.referents[index]
        self.UpdateContents()
        self.sizer.FitInside(self)

class ReferencePlanningPanel(PlanningWidget):
    def __init__(self, parent, activity_choice):
        PlanningWidget.__init__(self, parent, activity_choice, options=NO_ICONS|PRESENCES_ONLY|ACTIVITES)
        
    def UpdateContents(self):
        lines = []
        if self.inscription:
            for day in range(self.inscription.duree_reference):
                if JourSemaineAffichable(day):
                    line = self.inscription.reference[day]
                    line.insert = None
                    line.label = days[day % 7]
                    line.reference = None
                    line.summary = SUMMARY_NUM
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
        self.validation_button = wx.ToggleButton(self, -1, "Invalider l'inscription")
        ligne_sizer.Add(self.validation_button, 0, wx.LEFT, 10)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnValidationInscription, self.validation_button)    
        sizer.Add(ligne_sizer, 0, wx.TOP, 5)
        sizer1 = wx.FlexGridSizer(0, 2, 5, 10)
        sizer1.AddGrowableCol(1, 1)
        
        self.sites_items = wx.StaticText(self, -1, u"Site :"), AutoChoiceCtrl(self, None, 'site'), wx.StaticText(self, -1, u"Sites de préinscription :"), wx.CheckListBox(self, -1)
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheckPreinscriptionSite, self.sites_items[3])
        self.UpdateSiteItems()
        sizer1.AddMany([(self.sites_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.sites_items[1], 0, wx.EXPAND)])
        sizer1.AddMany([(self.sites_items[2], 0, wx.ALIGN_CENTER_VERTICAL), (self.sites_items[3], 0, wx.EXPAND)])
        
        if config.options & RESERVATAIRES:
            self.reservataire_items = wx.StaticText(self, -1, u"Réservataire :"), AutoChoiceCtrl(self, None, 'reservataire')
            self.UpdateReservataireItems()
            sizer1.AddMany([(self.reservataire_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.reservataire_items[1], 0, wx.EXPAND)])
            
        self.groupe_items = wx.StaticText(self, -1, u"Groupe :"), AutoChoiceCtrl(self, None, 'groupe')
        self.UpdateGroupeItems()
        sizer1.AddMany([(self.groupe_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.groupe_items[1], 0, wx.EXPAND)])
        
        self.professeur_items = wx.StaticText(self, -1, u"Professeur :"), AutoChoiceCtrl(self, None, 'professeur')
        self.UpdateProfesseurItems()
        sizer1.AddMany([(self.professeur_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.professeur_items[1], 0, wx.EXPAND)])
        
        self.mode_accueil_choice = AutoChoiceCtrl(self, None, 'mode', items=ModeAccueilItems)
        self.Bind(wx.EVT_CHOICE, self.onModeAccueilChoice, self.mode_accueil_choice)
        sizer1.AddMany([(wx.StaticText(self, -1, u"Mode d'accueil :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.mode_accueil_choice, 0, wx.EXPAND)])
        sizer1.AddMany([(wx.StaticText(self, -1, u"Frais d'inscription :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoNumericCtrl(self, None, 'frais_inscription', min=0, precision=2), 0, wx.EXPAND)])
        self.semaines_conges_items = wx.StaticText(self, -1, u"Nombre de semaines de congés :"), AutoNumericCtrl(self, None, 'semaines_conges', min=0, precision=0)
        sizer1.AddMany([(self.semaines_conges_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.semaines_conges_items[1], 0, wx.EXPAND)])
        self.facturation_items = wx.StaticText(self, -1, u"Forfait mensuel :"), AutoNumericCtrl(self, None, 'forfait_mensuel', min=0, precision=2)
        sizer1.AddMany([(self.facturation_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.facturation_items[1], 0, wx.EXPAND)])
        sizer1.AddMany([(wx.StaticText(self, -1, u"Date de fin de la période d'adaptation :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoDateCtrl(self, None, 'fin_periode_adaptation'), 0, wx.EXPAND)])
        if creche.gestion_depart_anticipe:
            sizer1.AddMany([(wx.StaticText(self, -1, u"Date de départ anticipé :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoDateCtrl(self, None, 'depart'), 0, wx.EXPAND)])
        self.duree_reference_choice = wx.Choice(self)
        for item, data in [("1 semaine", 7)] + [("%d semaines" % (i+2), 7*(i+2)) for i in range(MAX_SEMAINES_REFERENCE-1)]:
            self.duree_reference_choice.Append(item, data)
        self.Bind(wx.EVT_CHOICE, self.onDureeReferenceChoice, self.duree_reference_choice)
        sizer1.AddMany([(wx.StaticText(self, -1, u"Durée de la période de référence :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.duree_reference_choice, 0, wx.EXPAND)])
        self.forfait_heures_presences_static = wx.StaticText(self, -1, u"Forfait mensuel en heures :")
        self.forfait_heures_presences_ctrl = AutoNumericCtrl(self, None, 'forfait_heures_presence', min=0, precision=0)
        sizer1.AddMany([(self.forfait_heures_presences_static, 0, wx.ALIGN_CENTER_VERTICAL), (self.forfait_heures_presences_ctrl, 0, wx.EXPAND)])
        sizer.Add(sizer1, 0, wx.ALL|wx.EXPAND, 5)
       
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.button_5_5 = wx.Button(self, -1, "Plein temps")
        sizer2.Add(self.button_5_5)
        self.Bind(wx.EVT_BUTTON, self.onMode_5_5, self.button_5_5)
        self.button_copy = wx.Button(self, -1, u"Recopier lundi sur toute la période")
        sizer2.Add(self.button_copy)
        self.Bind(wx.EVT_BUTTON, self.onMondayCopy, self.button_copy)
        
        self.activity_choice = ActivityComboBox(self)        
        sizer2.Add(self.activity_choice, 0, wx.ALIGN_RIGHT)
        sizer.Add(sizer2, 0, wx.EXPAND)
        
        self.planning_panel = ReferencePlanningPanel(self, self.activity_choice)
        sizer.Add(self.planning_panel, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.UpdateContents()
        
    def nouvelleInscription(self): # TODO les autres pareil ...
        inscription = Inscription(self.inscrit)
        inscription.preinscription = creche.preinscriptions 
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
    
    def onModeAccueilChoice(self, event):
        history.Append(None)
        self.inscrit.inscriptions[self.periode].mode = self.mode_accueil_choice.GetClientData(self.mode_accueil_choice.GetSelection())
        self.UpdateContents()        
        
    def onDureeReferenceChoice(self, event):
        history.Append(None)
        duration = self.duree_reference_choice.GetClientData(self.duree_reference_choice.GetSelection())
        self.inscrit.inscriptions[self.periode].setReferenceDuration(duration)
        self.UpdateContents()
        
    def onMode_5_5(self, event):
        history.Append(None)
        inscription = self.inscrit.inscriptions[self.periode]
        inscription.mode = MODE_5_5
        for i, day in enumerate(inscription.reference):
            if JourSemaineAffichable(i):
                day.set_state(0)
        self.UpdateContents()
    
    def onMondayCopy(self, event):
        history.Append(None)
        inscription = self.inscrit.inscriptions[self.periode]
        for i, day in enumerate(inscription.reference):
            if i > 0 and JourSemaineAffichable(i):
                day.Copy(inscription.reference[0], False)
                day.Save()
        self.UpdateContents()
            
    def OnCheckPreinscriptionSite(self, event):
        index = event.GetSelection()
        object = event.GetEventObject()
        site = creche.sites[index]
        inscription = self.inscrit.inscriptions[self.periode]
        history.Append(Change(inscription, "sites_preinscription", inscription.sites_preinscription[:]))
        if object.IsChecked(index):
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
        self.last_site_observer = time.time()
    
    def UpdateReservataireItems(self):
        if len(creche.reservataires) > 0:
            reservataires = [("----", None)] + [(reservataire.nom, reservataire) for reservataire in creche.reservataires]
            self.reservataire_items[1].SetItems(reservataires)
            for item in self.reservataire_items:
                item.Show(True)
        else:
            for item in self.reservataire_items:
                item.Show(False)
        self.last_reservataire_observer = time.time()

    def UpdateGroupeItems(self):
        if len(creche.groupes) > 0:
            groupes = [("----", None)] + [(groupe.nom, groupe) for groupe in creche.groupes]
            self.groupe_items[1].SetItems(groupes)
            for item in self.groupe_items:
                item.Show(True)
        else:
            for item in self.groupe_items:
                item.Show(False)
        self.last_groupe_observer = time.time()

    def UpdateProfesseurItems(self):
        if creche.type == TYPE_GARDERIE_PERISCOLAIRE and len(creche.professeurs) > 0:
            professeurs = [("%s %s" % (professeur.prenom, professeur.nom), professeur) for professeur in creche.professeurs]
            self.professeur_items[1].SetItems(professeurs)
            for item in self.professeur_items:
                item.Show(True)
        else:
            for item in self.professeur_items:
                item.Show(False)
        self.last_professeur_observer = time.time()
                
    def UpdateContents(self):
        if 'sites' in observers and observers['sites'] > self.last_site_observer:
            self.UpdateSiteItems()
        if 'groupes' in observers and observers['groupes'] > self.last_groupe_observer:
            self.UpdateGroupeItems()
        if 'reservataires' in observers and observers['reservataires'] > self.last_reservataire_observer:
            self.UpdateReservataireItems()
        if 'professeurs' in observers and observers['professeurs'] > self.last_professeur_observer:
            self.UpdateProfesseurItems()

        InscriptionsTab.UpdateContents(self)
        self.mode_accueil_choice.Enable(creche.modes_inscription != MODE_5_5)
        self.validation_button.Show(creche.preinscriptions)

        self.InternalUpdate()
            
        self.activity_choice.Clear()
        selected = 0
        if creche.HasActivitesAvecHoraires():
            self.activity_choice.Show(True)
            for i, activity in enumerate(creche.activites.values()):
                self.activity_choice.Append(activity.label, activity)
                try:
                    if self.activity_choice.activity.value == activity.value:
                        selected = i
                except:
                    pass
        else:
            self.activity_choice.Show(False)
            self.activity_choice.Append(creche.activites[0].label, creche.activites[0])
        self.activity_choice.SetSelection(selected)
        
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
                    
            self.forfait_heures_presences_ctrl.Show(inscription.mode == MODE_FORFAIT_HORAIRE)
            self.forfait_heures_presences_static.Show(inscription.mode == MODE_FORFAIT_HORAIRE)
            self.duree_reference_choice.SetSelection(inscription.duree_reference / 7 - 1)
            self.planning_panel.SetInscription(inscription)
        else:
            self.planning_panel.SetInscription(None)
            for obj in [self.duree_reference_choice, self.mode_accueil_choice, self.button_5_5, self.button_copy, self.validation_button]:
                obj.Disable()
                
class CongesPanel(InscriptionsTab):
    def __init__(self, parent):
        global delbmp
        delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        self.last_creche_observer = -1
        
        InscriptionsTab.__init__(self, parent)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.conges_creche_sizer = wx.BoxSizer(wx.VERTICAL)
        self.affiche_conges_creche()
        self.sizer.Add(self.conges_creche_sizer, 0, wx.ALL, 5)
        
        self.conges_inscrit_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.conges_inscrit_sizer, 0, wx.ALL, 5)
        
        self.nouveau_conge_button = wx.Button(self, -1, u'Nouvelle période de congés')
        self.sizer.Add(self.nouveau_conge_button, 0, wx.EXPAND+wx.TOP, 5)
        self.Bind(wx.EVT_BUTTON, self.evt_conge_add, self.nouveau_conge_button)

#        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
#        sizer2.AddMany([(wx.StaticText(self, -1, u'Nombre de semaines de congés déduites :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), (AutoNumericCtrl(self, creche, 'semaines_conges', min=0, precision=0), 0, wx.EXPAND)])
#        self.sizer.Add(sizer2, 0, wx.EXPAND+wx.TOP, 5)

        self.SetSizer(self.sizer)

    def UpdateContents(self):
        if 'conges' in observers and observers['conges'] > self.last_creche_observer:
            self.affiche_conges_creche()
        if self.inscrit:
            for i in range(len(self.conges_inscrit_sizer.GetChildren()), len(self.inscrit.conges)):
                self.line_add(i)
            for i in range(len(self.inscrit.conges), len(self.conges_inscrit_sizer.GetChildren())):
                self.line_del()
        else:
            for i in range(len(self.conges_inscrit_sizer.GetChildren())):
                self.line_del()
        self.sizer.Layout()
        AutoTab.UpdateContents(self)
        
    def SetInscrit(self, inscrit):
        self.inscrit = inscrit
        self.UpdateContents()
        InscriptionsTab.SetInscrit(self, inscrit)
        self.nouveau_conge_button.Enable(self.inscrit is not None and not readonly)

    def affiche_conges_creche(self):
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
        self.last_creche_observer = time.time()

    def line_add(self, index):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddMany([(wx.StaticText(self, -1, 'Debut :'), 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, self.inscrit, 'conges[%d].debut' % index, mois=True)])
        sizer.AddMany([(wx.StaticText(self, -1, 'Fin :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoDateCtrl(self, self.inscrit, 'conges[%d].fin' % index, mois=True)])
        sizer.AddMany([(wx.StaticText(self, -1, u'Libellé :'), 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 10), AutoTextCtrl(self, self.inscrit, 'conges[%d].label' % index)])
        delbutton = wx.BitmapButton(self, -1, delbmp)
        delbutton.index = index
        sizer.Add(delbutton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 10)
        self.Bind(wx.EVT_BUTTON, self.evt_conge_del, delbutton)
        self.conges_inscrit_sizer.Add(sizer)
        
    def line_del(self):
        index = len(self.conges_inscrit_sizer.GetChildren()) - 1
        sizer = self.conges_inscrit_sizer.GetItem(index)
        sizer.DeleteWindows()
        self.conges_inscrit_sizer.Detach(index)

    def evt_conge_add(self, event):
        history.Append(Delete(self.inscrit.conges, -1))
        self.inscrit.add_conge(CongeInscrit(self.inscrit))
        self.line_add(len(self.inscrit.conges) - 1)
        self.sizer.Layout()

    def evt_conge_del(self, event):
        index = event.GetEventObject().index
        history.Append(Insert(self.inscrit.conges, index, self.inscrit.conges[index]))
        self.line_del()
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
            self.AddPage(self.conges_panel, u"Congés")
        else:
            self.conges_panel = None
        self.AddPage(NotesPanel(self), "Notes")
        if profil & PROFIL_TRESORIER:
            self.forfait_panel = FraisAccueilPanel(self)
            self.AddPage(self.forfait_panel, 'Frais de garde')
        else:
            self.forfait_panel = None

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChanged)  
            
    def EvtChangementPrenomNom(self, event):
        self.parent.ChangePrenom(self.inscrit)

    def onPageChanged(self, event):
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
            self.InsertPage(3, self.conges_panel, u"Congés")
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

        # Le control pour la selection du bebe
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.choice = wx.Choice(self)
        self.Bind(wx.EVT_CHOICE, self.EvtInscritChoice, self.choice)
        plusbmp = wx.Bitmap(GetBitmapFile("plus.png"), wx.BITMAP_TYPE_PNG)
        delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        self.addbutton = wx.BitmapButton(self, -1, plusbmp)
        self.delbutton = wx.BitmapButton(self, -1, delbmp)
        self.addbutton.SetToolTipString(u"Ajouter un enfant")
        self.delbutton.SetToolTipString(u"Supprimer cet enfant")
        self.Bind(wx.EVT_BUTTON, self.EvtInscritAddButton, self.addbutton)
        self.Bind(wx.EVT_BUTTON, self.EvtInscritDelButton, self.delbutton)
        sizer.AddMany([(self.choice, 1, wx.EXPAND|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (self.addbutton, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (self.delbutton, 0, wx.ALIGN_CENTER_VERTICAL)])
        self.sizer.Add(sizer, 0, wx.EXPAND|wx.LEFT, MACOS_MARGIN)
        # le notebook pour la fiche d'inscription
        self.notebook = InscriptionsNotebook(self)
        self.sizer.Add(self.notebook, 1, wx.EXPAND|wx.TOP, 5)
        self.InitInscrits()

    def UpdateContents(self):
        self.notebook.UpdateContents()

    def __add_in_array(self, array, cell):
        if isinstance(cell, basestring):
            return '[%s]' % cell

        key = GetPrenomNom(cell)
        if key.isspace():
            key = 'Nouvelle inscription'
        count = array.count(key)
        array.append(key)
        if count > 0:
            key = key + " (%d)" % count
        return '  ' + key 

    def __add_in_inscrits_choice(self, inscrits):
        array = []
        for inscrit in inscrits:
            key = self.__add_in_array(array, inscrit)
            self.choice.Append(key, inscrit)
            
    def InitInscrits(self, selected=None):
        self.choice.Clear()

        inscrits = []
        autres = []
        for inscrit in creche.inscrits:
            if inscrit.GetInscription(datetime.date.today(), preinscription=True) != None:
                inscrits.append(inscrit)
            else:
                autres.append(inscrit)
        
        if (config.options & RESERVATAIRES) and len(creche.reservataires):
            inscrits = TrieParReservataires(inscrits)
        else:
            if len(inscrits) > 0 and len(autres) > 0:
                self.choice.Append("[Inscrits]", None)
            inscrits.sort(key=lambda inscrit: GetPrenomNom(inscrit))

        self.__add_in_inscrits_choice(inscrits)        
        
        if len(inscrits) > 0 and len(autres) > 0:
            self.choice.Append("[Anciens]", None)

        autres.sort(key=lambda inscrit: GetPrenomNom(inscrit))

        self.__add_in_inscrits_choice(autres)        

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

    def EvtInscritChoice(self, evt):
        ctrl = evt.GetEventObject()
        selected = ctrl.GetSelection()
        inscrit = ctrl.GetClientData(selected)
        if isinstance(inscrit, Inscrit):
            self.inscrit_selected = selected
            self.delbutton.Enable()
            self.notebook.SetInscrit(inscrit)
        else:
            ctrl.SetSelection(self.inscrit_selected)
            self.EvtInscritChoice(evt)

    def SelectInscrit(self, inscrit):
        if inscrit:
            for i in range(self.choice.GetCount()):
                if self.choice.GetClientData(i) == inscrit:
                    self.inscrit_selected = i
                    self.choice.SetSelection(i)
                    break
        else:
            self.choice.SetSelection(-1)
        self.notebook.SetInscrit(inscrit)

    def EvtInscritAddButton(self, evt):
        history.Append(Delete(creche.inscrits, -1))
        inscrit = Inscrit()
        creche.inscrits.append(inscrit)
        self.InitInscrits(inscrit)
        self.notebook.SetInscrit(inscrit)
        self.notebook.SetSelection(0) # Selectionne la page identite

    def EvtInscritDelButton(self, evt):
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
                                