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

import os.path
import sys
import string
import datetime
import wx
import wx.lib.scrolledpanel
import wx.html
from constants import *
from controls import *
from cotisation import CotisationException
from planning_presences import GenerePlanningPresences
from coordonnees_parents import GenereCoordonneesParents
from etats_trimestriels import GenereEtatsTrimestriels
from planning_detaille import GenerePlanningDetaille

class RelevesPanel(GPanel):
    bitmap = './bitmaps/releves.png'
    index = 40
    profil = PROFIL_ALL
    def __init__(self, parent):
        GPanel.__init__(self, parent, u'Relevés')

        today = datetime.date.today()
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Les coordonnees des parents
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Coordonnées des parents'), wx.HORIZONTAL)
        self.coords_date = wx.TextCtrl(self)
        self.coords_date.SetValue("Aujourd'hui")
        button = wx.Button(self, -1, u'Génération')
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationCoordonnees, button)
        box_sizer.AddMany([(self.coords_date, 1, wx.EXPAND|wx.ALL, 5), (button, 0, wx.ALL, 5)])
        sizer.Add(box_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)
        
        # Les releves trimestriels
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Relevés trimestriels'), wx.HORIZONTAL)
        self.choice = wx.Choice(self)
        button = wx.Button(self, -1, u'Génération')
        for year in range(first_date.year, last_date.year + 1):
            self.choice.Append(u'Année %d' % year, year)
        self.choice.SetSelection(today.year - first_date.year)
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationEtatsTrimestriels, button)
        box_sizer.AddMany([(self.choice, 1, wx.ALL|wx.EXPAND, 5), (button, 0, wx.ALL, 5)])
        sizer.Add(box_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)

        # Les plannings de presence enfants
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Planning des présences'), wx.HORIZONTAL)
        self.weekchoice = wx.Choice(self)
        day = getFirstMonday()
        semaine = 1
        while day < last_date:
            string = 'Semaines %d et %d (%d %s %d)' % (semaine, semaine+1, day.day, months[day.month - 1], day.year)
            self.weekchoice.Append(string, day)
            if (day.year == (day + datetime.timedelta(14)).year):
                semaine += 2
            else:
                semaine = 1
            day += datetime.timedelta(14)
        self.weekchoice.SetSelection((today - getFirstMonday()).days / 14 + 1)
        button = wx.Button(self, -1, u'Génération')
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationPlanningPresences, button)
        box_sizer.AddMany([(self.weekchoice, 1, wx.ALL|wx.EXPAND, 5), (button, 0, wx.ALL, 5)])
        sizer.Add(box_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)

        # Les plannings détaillés
        box_sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'Planning détaillé'), wx.HORIZONTAL)
        self.detail_start_date = DateCtrl(self)
        self.detail_end_date = DateCtrl(self)
        self.detail_start_date.SetValue(today)
        button = wx.Button(self, -1, u'Génération')
        self.Bind(wx.EVT_BUTTON, self.EvtGenerationPlanningDetaille, button)
        box_sizer.AddMany([(self.detail_start_date, 1, wx.ALL|wx.EXPAND, 5), (wx.StaticText(self, -1, "-"), 0, wx.ALL|wx.EXPAND, 5), (self.detail_end_date, 1, wx.ALL|wx.EXPAND, 5), (button, 0, wx.ALL, 5)])
        sizer.Add(box_sizer, 0, wx.EXPAND|wx.BOTTOM, 10)
        
        self.sizer.Add(sizer, 1, wx.EXPAND)

    def EvtGenerationCoordonnees(self, evt):
        date = str2date(self.coords_date.GetValue())
        if not date:
            date = today
        wildcard = "OpenDocument (*.ods)|*.ods"
        oodefaultfilename = u"Coordonnées parents %s.ods" % getDateStr(date, weekday=False)
        old_path = os.getcwd()
        dlg = wx.FileDialog(self, message=u'Générer un document OpenOffice', defaultDir=os.getcwd(), defaultFile=oodefaultfilename, wildcard=wildcard, style=wx.SAVE | wx.CHANGE_DIR)
        response = dlg.ShowModal()
        os.chdir(old_path)

        if response == wx.ID_OK:
            oofilename = dlg.GetPath()
            try:
                GenereCoordonneesParents(date, oofilename)
                dlg = wx.MessageDialog(self, u"Document %s généré" % oofilename, 'Message', wx.OK)
            except Exception, e:
                dlg = wx.MessageDialog(self, str(e), 'Erreur', wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()

    def EvtGenerationEtatsTrimestriels(self, evt):
        annee = self.choice.GetClientData(self.choice.GetSelection())

        wildcard = "OpenDocument (*.ods)|*.ods"
        oodefaultfilename = "Etats trimestriels %d.ods" % annee
        old_path = os.getcwd()
        dlg = wx.FileDialog(self, message=u'Générer un document OpenOffice', defaultDir=os.getcwd(), defaultFile=oodefaultfilename, wildcard=wildcard, style=wx.SAVE | wx.CHANGE_DIR)
        response = dlg.ShowModal()
        os.chdir(old_path)

        if response == wx.ID_OK:
            oofilename = dlg.GetPath()
            try:
                GenereEtatsTrimestriels(annee, oofilename)
                dlg = wx.MessageDialog(self, u"Document %s généré" % oofilename, 'Message', wx.OK)
            except CotisationException, e:
                message = '\n'.join(['%s %s :\n%s' % (tmp[0], tmp[1], '\n'.join(list(e.errors[tmp]))) for tmp in e.errors])
                dlg = wx.MessageDialog(self, message, 'Erreur', wx.OK | wx.ICON_WARNING)
            except Exception, e:
                dlg = wx.MessageDialog(self, str(e), 'Exception', wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()

    def EvtGenerationPlanningPresences(self, evt):
        date = self.weekchoice.GetClientData(self.weekchoice.GetSelection())

        wildcard = "OpenDocument (*.ods)|*.ods"
        oodefaultfilename = "Planning presences %s.ods" % str(date)
        old_path = os.getcwd()
        dlg = wx.FileDialog(self, message=u'Générer un document OpenOffice', defaultDir=os.getcwd(), defaultFile=oodefaultfilename, wildcard=wildcard, style=wx.SAVE | wx.CHANGE_DIR)
        response = dlg.ShowModal()
        os.chdir(old_path)

        if response == wx.ID_OK:
            oofilename = dlg.GetPath()
            GenerePlanningPresences(date, oofilename)
            dlg = wx.MessageDialog(self, u"Document %s généré" % oofilename, 'Message', wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            
    def EvtGenerationPlanningDetaille(self, evt):
        start = self.detail_start_date.GetValue()
        end = self.detail_end_date.GetValue()
        if end is None:
            end = start
            oodefaultfilename = "Planning presences %s.odg" % getDateStr(start, weekday=False)
        else:
            oodefaultfilename = "Planning presences %s-%s.odg" % (getDateStr(start, weekday=False), getDateStr(end, weekday=False))
        wildcard = "OpenDocument (*.odg)|*.odg"
        old_path = os.getcwd()
        dlg = wx.FileDialog(self, message=u'Générer un document OpenOffice', defaultDir=os.getcwd(), defaultFile=oodefaultfilename, wildcard=wildcard, style=wx.SAVE | wx.CHANGE_DIR)
        response = dlg.ShowModal()
        os.chdir(old_path)

        if response == wx.ID_OK:
            oofilename = dlg.GetPath()
            GenerePlanningDetaille((start, end), oofilename)
            dlg = wx.MessageDialog(self, u"Document %s généré" % oofilename, 'Message', wx.OK)
            dlg.ShowModal()
            dlg.Destroy()

panels = [RelevesPanel]

if __name__ == '__main__':
    import os
    from config import *
    from data import *
    LoadConfig()
    Load()
            
    today = datetime.date.today()

    #GenereCoordonneesParents("coordonnees.odt")
    #sys.exit(0)    
    filename = 'etats_trimestriels_%d.ods' % (today.year - 1)
    try:
        GenereEtatsTrimestriels(today.year - 1, filename)
        print u'Fichier %s généré' % filename
    except CotisationException, e:
        print e.errors

    #filename = 'planning_presences_%s.ods' % first_date
    #GenerePlanningPresences(getfirstmonday(), filename)
    #print u'Fichier %s généré' % filename
