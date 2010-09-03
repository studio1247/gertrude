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

import os, datetime, xml.dom.minidom, cStringIO
import wx, wx.lib.scrolledpanel, wx.html
from constants import *
from sqlobjects import *
from controls import *
from planning import *
from cotisation import *

def isPresentDuringTranche(journee, tranche):
    # Tranches horaires
    tranches = [(creche.ouverture, 12), (12, 14), (14, creche.fermeture)]
    
    debut, fin = tranches[tranche]
    for i in range(int(debut * (60 / BASE_GRANULARITY)), int(fin * (60 / BASE_GRANULARITY))):
        if journee.values[i]:
            return True
    return False

def HeuresTranche(journee, tranche):
    # Tranches horaires
    tranches = [(creche.ouverture, 12), (12, 14), (14, creche.fermeture)]
    
    debut, fin = tranches[tranche]
    result = 0
    for i in range(int(debut * (60 / BASE_GRANULARITY)), int(fin * (60 / BASE_GRANULARITY))):
        if journee.values[i]:
            result += BASE_GRANULARITY
    return float(result) / 60

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

class ContextPanel(wx.Panel):
    def __init__(self, parent):
        self.parent = parent
        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.periodechoice = wx.Choice(self)
        self.Bind(wx.EVT_CHOICE, self.EvtPeriodeChoice, self.periodechoice)
        self.html_window = wx.html.HtmlWindow(self, style=wx.SUNKEN_BORDER)
        sizer.AddMany([(self.periodechoice, 0, wx.EXPAND|wx.ALL, 5), (self.html_window, 1, wx.EXPAND|wx.ALL-wx.TOP, 5)])
        self.SetSizer(sizer)

    def SetInscrit(self, inscrit):
        self.inscrit = inscrit
        self.UpdateContents()

    def UpdateContents(self):
        if self.inscrit and self.inscrit.inscriptions and self.inscrit.inscriptions[0].debut:
            self.periodechoice.Clear()   
            self.periodes = self.GetPeriodes()
            for p in self.periodes:
                self.periodechoice.Append(date2str(p[0]) + ' - ' + date2str(p[1]))
            if len(self.periodes) > 1:
                self.periodechoice.Enable()
            else:
                self.periodechoice.Disable()

            self.periode = self.periodes[-1]
            self.periodechoice.SetSelection(self.periodechoice.GetCount() - 1)
        else:
            self.periode = None
            self.periodechoice.Clear()
            self.periodechoice.Disable()
        self.UpdatePage()

    def EvtPeriodeChoice(self, evt):
        ctrl = evt.GetEventObject()
        self.periode = self.periodes[ctrl.GetSelection()]
        self.UpdatePage()

class ContratPanel(ContextPanel):
    def __init__(self, parent):
        ContextPanel.__init__(self, parent)

    def GetPeriodes(self):
        return [(inscription.debut, inscription.fin) for inscription in self.inscrit.inscriptions]

    def UpdatePage(self):
        if self.inscrit is None:
            self.html = '<html><body>Aucun inscrit s&eacute;lectionn&eacute; !</body></html>'
            self.periodechoice.Disable()
        elif self.periode is None:
            self.html = '<html><body>Aucune inscription !</body></html>'
            self.periodechoice.Disable()
        else:
            try:
                context = Cotisation(self.inscrit, self.periode)
                if creche.mode_facturation == FACTURATION_PAJE:
                    str_facturation = "_paje"
                else:
                    str_facturation = ""
                if os.path.exists("./templates/contrat_accueil%s.html" % str_facturation):
                    self.html = ParseHtml("./templates/contrat_accueil%s.html" % str_facturation, context)
                else:
                    self.html = ParseHtml("./templates_dist/contrat_accueil%s.html" % str_facturation, context)
            except CotisationException, e:
                error = '<br>'.join(e.errors)
                self.html = u"<html><body><b>Le contrat d'accueil de l'enfant ne peut être édit&eacute; pour la (les) raison(s) suivante(s) :</b><br>" + error + "</body></html>"

        self.html_window.SetPage(self.html)

class ForfaitPanel(ContextPanel):
    def __init__(self, parent):
        ContextPanel.__init__(self, parent)

    def GetPeriodes(self):
        periodes = []
        for inscription in self.inscrit.inscriptions:
            separators = self.get_separators(inscription.debut, inscription.fin)
            all_periodes = [(separators[i], separators[i+1] - datetime.timedelta(1)) for i in range(len(separators)-1)]
            previous_context = None
            previous_periode = None
            for periode in all_periodes:
                try:
                    context = Cotisation(self.inscrit, periode, options=NO_ADDRESS+NO_PARENTS)                    
                    if not previous_periode or context != previous_context:
                        periodes.append(periode)           
                        previous_periode = periode
                        previous_context = context
                    else:
                        periodes[-1] = (previous_periode[0], periode[1])
                except CotisationException, e:
                    periodes.append(periode)           
                    previous_periode = periode
                    previous_context = None
        return periodes

    def get_separators(self, debut, fin):
        if debut is None:
            return []

        if fin is None:
            fin = datetime.date(day=1, month=1, year=datetime.date.today().year+1)
        else:
            fin = fin + datetime.timedelta(1)

        separators = [debut, fin]

        def addseparator(separator, end=0):
            if separator is None:
                return
            if end == 1:
                separator = separator + datetime.timedelta(1)
            if separator >= debut and separator <= fin and not separator in separators:
                separators.append(separator)

        for parent in [self.inscrit.papa, self.inscrit.maman]:
            for revenu in parent.revenus:
                addseparator(revenu.debut)
                addseparator(revenu.fin, 1)
        for frere_soeur in self.inscrit.freres_soeurs:
            addseparator(frere_soeur.naissance)
            addseparator(frere_soeur.entree)
            addseparator(frere_soeur.sortie, 1)
        for year in range(debut.year, fin.year+1):
            addseparator(datetime.date(day=1, month=9, year=year))
            addseparator(datetime.date(day=1, month=1, year=year))

        separators.sort()
        return separators

    def UpdatePage(self):      
        if self.inscrit is None:
            self.html = '<html><body>Aucun inscrit s&eacute;lectionn&eacute; !</body></html>'
            self.periodechoice.Disable()
        elif self.periode is None:
            self.html = '<html><body>Aucune inscription !</body></html>'
            self.periodechoice.Disable()
        else:
            try:
                context = Cotisation(self.inscrit, self.periode, options=NO_ADDRESS+NO_PARENTS)
                if context.mode_inscription == MODE_CRECHE:
                    str_inscription = "_creche"
                else:
                    str_inscription = "_hg"
                if creche.mode_facturation == FACTURATION_PAJE:
                    str_facturation = "_paje"
                else:
                    str_facturation = ""
                if os.path.exists("./templates/frais_de_garde%s%s.html" % (str_inscription, str_facturation)):
                    self.html = ParseHtml("./templates/frais_de_garde%s%s.html" % (str_inscription, str_facturation), context)
                else:
                    self.html = ParseHtml("./templates_dist/frais_de_garde%s%s.html" % (str_inscription, str_facturation), context)
            except CotisationException, e:
                error = '<br>'.join(e.errors)
                self.html = u"<html><body><b>Les frais de garde mensuels ne peuvent être calcul&eacute;s pour la (les) raison(s) suivante(s) :</b><br>" + error  + "</body></html>"
                
        self.html_window.SetPage(self.html)

            
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

        self.delbmp = wx.Bitmap("bitmaps/remove.png", wx.BITMAP_TYPE_PNG)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        sizer2 = wx.FlexGridSizer(0, 2, 5, 10)
        sizer2.AddGrowableCol(1, 1)
        ctrl = AutoTextCtrl(self, None, 'prenom')
        self.Bind(wx.EVT_TEXT, self.EvtChangementPrenom, ctrl)
        sizer2.AddMany([(wx.StaticText(self, -1, u'Prénom :'), 0, wx.ALIGN_CENTER_VERTICAL), (ctrl, 0, wx.EXPAND)])
        sizer2.AddMany([(wx.StaticText(self, -1, 'Nom :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoTextCtrl(self, None, 'nom'), 0, wx.EXPAND)])
        sizer2.AddMany([(wx.StaticText(self, -1, 'Sexe :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoChoiceCtrl(self, None, 'sexe', items=[(u"Garçon", 1), ("Fille", 2)]), 0, wx.EXPAND)])
        sizer2.AddMany([(wx.StaticText(self, -1, 'Date de naissance :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoDateCtrl(self, None, 'naissance'), 0, wx.EXPAND)])
        sizer2.AddMany([(wx.StaticText(self, -1, 'Adresse :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoTextCtrl(self, None, 'adresse'), 0, wx.EXPAND)])
        self.ville_ctrl = AutoTextCtrl(self, None, 'ville') # A laisser avant le code postal !
        self.code_postal_ctrl = AutoNumericCtrl(self, None, 'code_postal', min=0, precision=0)
        self.Bind(wx.EVT_TEXT, self.EvtChangementCodePostal, self.code_postal_ctrl)
        sizer2.AddMany([(wx.StaticText(self, -1, 'Code Postal :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.code_postal_ctrl, 0, wx.EXPAND)])
        sizer2.AddMany([(wx.StaticText(self, -1, 'Ville :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.ville_ctrl, 0, wx.EXPAND)])
        if creche.majoration_localite:
            sizer2.AddMany([(wx.StaticText(self, -1, u'Majoration (enfant hors localité) :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoCheckBox(self, None, 'majoration', ''), 0, wx.EXPAND)])
##        sizer2.AddMany([(wx.StaticText(self, -1, 'Date de marche :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoDateCtrl(self, None, 'marche'), 0, wx.EXPAND)])
        sizer3 = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Frères et soeurs'), wx.VERTICAL)
        self.fratries_sizer = wx.BoxSizer(wx.VERTICAL)
        sizer3.Add(self.fratries_sizer, 0, wx.EXPAND+wx.RIGHT+wx.LEFT+wx.TOP, 10)
        self.nouveau_frere = wx.Button(self, -1, u'Nouveau frère ou nouvelle soeur')
        self.nouveau_frere.Disable()
        sizer3.Add(self.nouveau_frere, 0, wx.RIGHT+wx.LEFT+wx.BOTTOM, 10)
        self.Bind(wx.EVT_BUTTON, self.EvtNouveauFrere, self.nouveau_frere)
        
        self.sizer.Add(sizer2, 0, wx.EXPAND|wx.ALL, 5)
        self.sizer.Add(sizer3, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(self.sizer)

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
        
    def EvtChangementPrenom(self, event):
        event.GetEventObject().onText(event)
        self.parent.EvtChangementPrenom(event)

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
        if self.inscrit:
            freres_count = len(self.inscrit.freres_soeurs)
            for i in range(len(self.fratries_sizer.GetChildren()), freres_count):
                self.frere_line_add(i)
        else:
            freres_count = 0
        for i in range(freres_count, len(self.fratries_sizer.GetChildren())):
            self.frere_line_del()
        AutoTab.UpdateContents(self)
        self.sizer.FitInside(self)
        
    def SetInscrit(self, inscrit):
        self.inscrit = inscrit
        self.UpdateContents()
        InscriptionsTab.SetInscrit(self, inscrit)
        self.nouveau_frere.Enable(self.inscrit is not None)

class ParentsPanel(InscriptionsTab):
    def __init__(self, parent):
        InscriptionsTab.__init__(self, parent)
        self.delbmp = wx.Bitmap("bitmaps/remove.png", wx.BITMAP_TYPE_PNG)
        self.regimes_choices = []
        self.revenus_items = []
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        for parent in ['papa', 'maman']:
            sizer1 = wx.StaticBoxSizer(wx.StaticBox(self, -1, parent.capitalize()), wx.VERTICAL)
            sizer11 = wx.BoxSizer(wx.VERTICAL)
            sizer1.Add(sizer11, 0, wx.EXPAND)
            sizer2 = wx.FlexGridSizer(0, 2, 5, 5)
            sizer2.AddGrowableCol(1, 1)
            sizer2.AddMany([(wx.StaticText(self, -1, u'Prénom :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoTextCtrl(self, None, '%s.prenom' % parent), 0, wx.EXPAND)])
            sizer2.AddMany([(wx.StaticText(self, -1, 'Nom :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoTextCtrl(self, None, '%s.nom' % parent), 0, wx.EXPAND)])
            sizer3 = wx.BoxSizer(wx.HORIZONTAL)
            sizer3.AddMany([AutoPhoneCtrl(self, None, '%s.telephone_domicile' % parent), (AutoTextCtrl(self, None, '%s.telephone_domicile_notes' % parent), 1, wx.LEFT|wx.EXPAND, 5)])
            sizer2.AddMany([(wx.StaticText(self, -1, u'Téléphone domicile :'), 0, wx.ALIGN_CENTER_VERTICAL), (sizer3, 0, wx.EXPAND)])
            sizer3 = wx.BoxSizer(wx.HORIZONTAL)
            sizer3.AddMany([AutoPhoneCtrl(self, None, '%s.telephone_portable' % parent), (AutoTextCtrl(self, None, '%s.telephone_portable_notes' % parent), 1, wx.LEFT|wx.EXPAND, 5)])        
            sizer2.AddMany([(wx.StaticText(self, -1, u'Téléphone portable :'), 0, wx.ALIGN_CENTER_VERTICAL), (sizer3, 0, wx.EXPAND)])
            sizer3 = wx.BoxSizer(wx.HORIZONTAL)
            sizer3.AddMany([AutoPhoneCtrl(self, None, '%s.telephone_travail' % parent), (AutoTextCtrl(self, None, '%s.telephone_travail_notes' % parent), 1, wx.LEFT|wx.EXPAND, 5)])        
            sizer2.AddMany([(wx.StaticText(self, -1, u'Téléphone travail :'), 0, wx.ALIGN_CENTER_VERTICAL), (sizer3, 0, wx.EXPAND)])
            sizer2.AddMany([(wx.StaticText(self, -1, 'E-mail :'), 0, wx.ALIGN_CENTER_VERTICAL), (AutoTextCtrl(self, None, '%s.email' % parent), 0, wx.EXPAND)])
            sizer11.Add(sizer2, 0, wx.EXPAND|wx.ALL, 5)
            
            if profil & PROFIL_TRESORIER:
                panel = PeriodePanel(self, parent+'.revenus')
                revenus_sizer = wx.StaticBoxSizer(wx.StaticBox(panel, -1, u"Revenus et régime d'appartenance"), wx.VERTICAL)
                revenus_sizer.Add(PeriodeChoice(panel, eval('self.nouveau_revenu_%s' % parent)), 0, wx.EXPAND|wx.ALL, 5)
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
                for i, regime in enumerate([u'Pas de sélection', u'Régime général', u'Régime de la fonction publique', u'Régime MSA', u'Régime EDF-GDF', u'Régime RATP', u'Régime Pêche maritime', u'Régime Marins du Commerce']):
                    choice.Append(regime, i)
                revenus_gridsizer.AddMany([wx.StaticText(panel, -1, u"Régime d'appartenance :"), (choice, 0, wx.EXPAND)])
                revenus_sizer.Add(revenus_gridsizer, 0, wx.ALL|wx.EXPAND, 5)
                panel.SetSizer(revenus_sizer)
                sizer11.Add(panel, 0, wx.ALL|wx.EXPAND, 5)

            self.sizer.Add(sizer1, 1, wx.EXPAND|wx.ALL, 5)

        sizer4 = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Référents'), wx.VERTICAL)
        self.referents_sizer = wx.BoxSizer(wx.VERTICAL)
        sizer4.Add(self.referents_sizer, 0, wx.EXPAND+wx.RIGHT+wx.LEFT+wx.TOP, 10)
        self.nouveau_referent = wx.Button(self, -1, u'Nouveau référent')
        self.nouveau_referent.Disable()
        sizer4.Add(self.nouveau_referent, 0, wx.RIGHT+wx.LEFT+wx.BOTTOM, 10)
        self.Bind(wx.EVT_BUTTON, self.EvtNouveauReferent, self.nouveau_referent)
        self.sizer.Add(sizer4, 0, wx.EXPAND|wx.ALL, 5)

        self.SetSizer(self.sizer)

    def nouveau_revenu_papa(self):
        return Revenu(self.inscrit.papa)
    
    def nouveau_revenu_maman(self):
        return Revenu(self.inscrit.maman)

    def UpdateContents(self):
        if self.inscrit:
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
        self.UpdateContents()
        InscriptionsTab.SetInscrit(self, inscrit)
        self.nouveau_referent.Enable(self.inscrit is not None)

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
        PlanningWidget.__init__(self, parent, activity_choice, options=NO_ICONS|PRESENCES_ONLY)
        
    def UpdateContents(self):
        lines = []
        if self.inscription:
            for day in range(self.inscription.duree_reference):
                if day % 7 < 5 or not "Week-end" in creche.feries:
                    line = self.inscription.reference[day]
                    line.insert = None
                    line.label = days[day % 7]
                    line.reference = None
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
        sizer.Add(PeriodeChoice(self, self.nouvelleInscription), 0, wx.TOP|wx.BOTTOM, 5)               
        sizer1 = wx.FlexGridSizer(0, 2, 5, 10)
        sizer1.AddGrowableCol(1, 1)
        self.sites_items = wx.StaticText(self, -1, u"Site :"), AutoChoiceCtrl(self, None, 'site')
        if len(creche.sites) > 1:
            items = [(site.nom, site) for site in creche.sites]
            self.sites_items[1].SetItems(items)
        else:
            for item in self.sites_items:
                item.Show(False)
        sizer1.AddMany([(self.sites_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.sites_items[1], 0, wx.EXPAND)])
        self.mode_accueil_choice = AutoChoiceCtrl(self, None, 'mode', items=[("Plein temps", MODE_5_5), (u"4/5èmes", MODE_4_5), (u"3/5èmes", MODE_3_5), ("Halte-garderie", MODE_HALTE_GARDERIE)])
        sizer1.AddMany([(wx.StaticText(self, -1, u"Mode d'accueil :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.mode_accueil_choice, 0, wx.EXPAND)])
        self.semaines_conges_items = wx.StaticText(self, -1, u"Nombre de semaines de congés :"), AutoNumericCtrl(self, None, 'semaines_conges', min=0, precision=0)
        sizer1.AddMany([(self.semaines_conges_items[0], 0, wx.ALIGN_CENTER_VERTICAL), (self.semaines_conges_items[1], 0, wx.EXPAND)])
        if creche.mode_facturation != FACTURATION_PAJE:
            for item in self.semaines_conges_items:
                item.Show(False)
        sizer1.AddMany([(wx.StaticText(self, -1, u"Date de fin de la période d'adaptation :"), 0, wx.ALIGN_CENTER_VERTICAL), (AutoDateCtrl(self, None, 'fin_periode_essai'), 0, wx.EXPAND)])
        self.duree_reference_choice = wx.Choice(self)
        for item, data in [("1 semaine", 7), (u"2 semaines", 14), (u"3 semaines", 21), ("4 semaines", 28)]:
            self.duree_reference_choice.Append(item, data)
        self.Bind(wx.EVT_CHOICE, self.onDureeReferenceChoice, self.duree_reference_choice)
        sizer1.AddMany([(wx.StaticText(self, -1, u"Durée de la période de référence :"), 0, wx.ALIGN_CENTER_VERTICAL), (self.duree_reference_choice, 0, wx.EXPAND)])
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
        return Inscription(self.inscrit)

    def SetInscrit(self, inscrit):
        self.inscrit = inscrit
        self.SetInstance(inscrit)
        self.UpdateContents()
    
    def onDureeReferenceChoice(self, event):
        duration = self.duree_reference_choice.GetClientData(self.duree_reference_choice.GetSelection())
        self.inscrit.inscriptions[self.periode].setReferenceDuration(duration)
        self.UpdateContents()
        
    def onMode_5_5(self, event):
        inscription = self.inscrit.inscriptions[self.periode]
        inscription.mode = MODE_5_5
        for i, day in enumerate(inscription.reference):
            if (i % 7 < 5) or "Week-end" not in creche.feries:
                day.set_state(PRESENT)
        self.UpdateContents()
    
    def onMondayCopy(self, event):
        inscription = self.inscrit.inscriptions[self.periode]
        for i, day in enumerate(inscription.reference):
            if i > 0 and ((i % 7 < 5) or "Week-end" not in creche.feries):
                day.copy(inscription.reference[0], False)
                day.save()
        self.UpdateContents()
            
    def UpdateContents(self):
        if len(creche.sites) > 1:
            items = [(site.nom, site) for site in creche.sites]
            self.sites_items[1].SetItems(items)
            for item in self.sites_items:
                item.Show(True)
        else:
            for item in self.sites_items:
                item.Show(False)

        InscriptionsTab.UpdateContents(self)
        self.mode_accueil_choice.Enable(creche.modes_inscription != MODE_5_5)
        
        if self.inscrit and self.periode is not None and self.periode != -1 and self.periode < len(self.inscrit.inscriptions):
            for obj in [self.duree_reference_choice, self.mode_accueil_choice, self.button_5_5, self.button_copy]:
                obj.Enable()
            self.duree_reference_choice.SetSelection(self.inscrit.inscriptions[self.periode].duree_reference / 7 - 1)
            self.planning_panel.SetInscription(self.inscrit.inscriptions[self.periode])
        else:
            self.planning_panel.SetInscription(None)
            for obj in [self.duree_reference_choice, self.mode_accueil_choice, self.button_5_5, self.button_copy]:
                obj.Disable()
            
        self.activity_choice.Clear()
        selected = 0
        if len(creche.activites) > 1:
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
            item.Show(creche.mode_facturation == FACTURATION_PAJE)
                            
        self.Layout()

    def SetPeriode(self, periode):
        PeriodeMixin.SetPeriode(self, periode)
        if self.inscrit and self.periode is not None and self.periode != -1 and self.periode < len(self.inscrit.inscriptions):
            inscription = self.inscrit.inscriptions[self.periode]
            self.planning_panel.SetInscription(inscription)
            for obj in [self.duree_reference_choice, self.mode_accueil_choice, self.button_5_5, self.button_copy]:
                obj.Enable()
            self.duree_reference_choice.SetSelection(inscription.duree_reference / 7 - 1)
        else:
            for obj in [self.duree_reference_choice, self.mode_accueil_choice, self.button_5_5, self.button_copy]:
                obj.Disable()
                
class CongesPanel(InscriptionsTab):
    def __init__(self, parent):
        global delbmp
        delbmp = wx.Bitmap("bitmaps/remove.png", wx.BITMAP_TYPE_PNG)
        self.last_creche_observer = 0
        
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
        self.nouveau_conge_button.Enable(self.inscrit is not None)

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
        if 'conges' in observers:
            self.last_creche_observer = observers['conges']

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
        self.inscrit.conges[index].delete()
        del self.inscrit.conges[index]
        self.sizer.Layout()
        self.UpdateContents()
        
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

        if profil & PROFIL_TRESORIER:
            self.contrat_panel = ContratPanel(self)
            self.forfait_panel = ForfaitPanel(self)
            self.AddPage(self.contrat_panel, "Contrat d'accueil")
            self.AddPage(self.forfait_panel, 'Frais de garde mensuels')
        else:
            self.contrat_panel = self.forfait_panel = None

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChanged)  
            
    def EvtChangementPrenom(self, event):
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
    bitmap = './bitmaps/inscriptions.png'
    profil = PROFIL_ALL
    def __init__(self, parent):
        GPanel.__init__(self, parent, "Inscriptions")

        # Le control pour la selection du bebe
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.choice = wx.Choice(self)
        self.Bind(wx.EVT_CHOICE, self.EvtInscritChoice, self.choice)
        plusbmp = wx.Bitmap("bitmaps/plus.png", wx.BITMAP_TYPE_PNG)
        delbmp = wx.Bitmap("bitmaps/remove.png", wx.BITMAP_TYPE_PNG)
        self.addbutton = wx.BitmapButton(self, -1, plusbmp, style=wx.BU_EXACTFIT)
        self.delbutton = wx.BitmapButton(self, -1, delbmp, style=wx.BU_EXACTFIT)
        self.addbutton.SetToolTipString(u"Ajouter un enfant")
        self.delbutton.SetToolTipString(u"Supprimer cet enfant")
        self.Bind(wx.EVT_BUTTON, self.EvtInscritAddButton, self.addbutton)
        self.Bind(wx.EVT_BUTTON, self.EvtInscritDelButton, self.delbutton)
        sizer.AddMany([(self.choice, 1, wx.EXPAND|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (self.addbutton, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5), (self.delbutton, 0, wx.ALIGN_CENTER_VERTICAL)])
        self.sizer.Add(sizer, 0, wx.EXPAND)
        # le notebook pour la fiche d'inscription
        self.notebook = InscriptionsNotebook(self)
        self.sizer.Add(self.notebook, 1, wx.EXPAND|wx.TOP, 5)
        self.InitInscrits()

    def UpdateContents(self):
        self.notebook.UpdateContents()

    def InitInscrits(self, selected=None):
        self.choice.Clear()
        # Ceux qui sont presents
        for inscrit in creche.inscrits:
            if inscrit.getInscription(datetime.date.today()) != None:
                self.choice.Append(GetInscritId(inscrit, creche.inscrits), inscrit)
        # Les autres
        separator = False
        for inscrit in creche.inscrits:
            if inscrit.getInscription(datetime.date.today()) == None:
                if not separator:
                    self.choice.Append(150 * '-', None)
                    separator = True
                self.choice.Append(GetInscritId(inscrit, creche.inscrits), inscrit)

        if len(creche.inscrits) > 0 and selected != None and selected in creche.inscrits:
            self.SelectInscrit(selected)
        elif len(creche.inscrits) > 0:
            self.SelectInscrit(self.choice.GetClientData(0))
        else:
            self.SelectInscrit(None)

    def EvtInscritChoice(self, evt):
        ctrl = evt.GetEventObject()
        selected = ctrl.GetSelection()
        inscrit = ctrl.GetClientData(selected)
        if inscrit:
            self.delbutton.Enable()
            self.SelectInscrit(inscrit)
        else:
            ctrl.SetSelection(0)
            self.EvtInscritChoice(evt)

    def SelectInscrit(self, inscrit):
        if inscrit:
            for i in range(self.choice.GetCount()):
                if self.choice.GetClientData(i) == inscrit:
                    self.choice.SetSelection(i)
                    break
        else:
            self.choice.SetSelection(-1)
        self.notebook.SetInscrit(inscrit)

    def EvtInscritAddButton(self, evt):
        history.Append(Delete(creche.inscrits, -1))
        inscrit = Inscrit()
        self.choice.Insert('Nouvelle inscription', 0, inscrit)
        self.choice.SetSelection(0)
        creche.inscrits.append(inscrit)
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
            inscritId = GetInscritId(inscrit, creche.inscrits)
            if inscritId == '':
                inscritId = 'Nouvelle inscription'
            self.choice.SetString(self.choice.GetSelection(), inscritId)
            self.choice.SetStringSelection(inscritId)
                                