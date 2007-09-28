# -*- coding: utf-8 -*-

##    This file is part of Gertrude.
##
##    Gertrude is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 2 of the License, or
##    (at your option) any later version.
##
##    Gertrude is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with Gertrude; if not, write to the Free Software
##    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import wx
import wx.lib.scrolledpanel
import datetime
from constants import *
from parameters import *
from functions import *
from gpanel import GPanel

PRENOMS_WIDTH = 80 # px
BUTTONS_WIDTH = 34 # px
HEURE_WIDTH = 48 # px
BEBE_HEIGHT = 30 # px

class DayTabWindow(wx.Window):
    def __init__(self, parent, inscrits, date, *args, **kwargs):
        wx.Window.__init__(self, parent, size=((heureAffichageMax-heureAffichageMin) * HEURE_WIDTH + 1, BEBE_HEIGHT * len(inscrits) + 1), *args, **kwargs)
        self.parent = parent
        self.inscrits = inscrits
        self.SetBackgroundColour(wx.WHITE)
        self.valeur_selection = -1
        self.date = date

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        if (profil & PROFIL_SAISIE_PRESENCES) or date > datetime.date.today():
            self.SetCursor(wx.StockCursor(wx.CURSOR_PENCIL))        
            self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftButtonDown)
            self.Bind(wx.EVT_LEFT_UP, self.OnLeftButtonUp)
            self.Bind(wx.EVT_MOTION, self.OnLeftButtonDragging)
        
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        self.PrepareDC(dc)
        self.DoDrawing(dc)

    def DrawLine(self, ligne, presence, dc=None):
        if not dc:
            dc = wx.ClientDC(self)
            self.PrepareDC(dc)
            
        dc.SetPen(wx.TRANSPARENT_PEN)
        green_brush = [ wx.Brush(wx.Color(5, 203, 28)), wx.Brush(wx.Color(150, 229, 139)) ]
        red_brush = [ wx.Brush(wx.Color(203, 5, 28)), wx.Brush(wx.Color(229, 150, 139)) ]
        heure = heureAffichageMin
        while heure < heureAffichageMax:
            i = int((heure-BASE_MIN_HOUR) * BASE_GRANULARITY)
            if presence.value == PRESENT and presence.details[i]:
                if not creche.presences_previsionnelles:
                    previsionnel = 0
                elif presence.details[i] == 2:
                    previsionnel = 1
                else:
                    previsionnel = presence.previsionnel
                if heure >= heureOuverture and heure <= heureFermeture:
                    brush = green_brush[previsionnel]
                else:
                    brush = red_brush[previsionnel]
                dc.SetBrush(brush)
            else:
                dc.SetBrush(wx.WHITE_BRUSH)
            dc.DrawRectangle(1 + (heure - heureAffichageMin) * HEURE_WIDTH, 1 + ligne * BEBE_HEIGHT, (1.0/heureGranularite) * HEURE_WIDTH - 1, BEBE_HEIGHT - 1)
            heure += 1.0 / heureGranularite

    def DrawPresence(self, index, dc=None):
        inscrit = self.inscrits[index]
        if self.date in inscrit.presences:
            presence = inscrit.presences[self.date]
        else:
            presence = inscrit.getPresenceFromSemaineType(self.date)
        self.DrawLine(index, presence, dc)
        
    def DoDrawing(self, dc, printing=False):
        dc.BeginDrawing()
       
        # le quadrillage
        dc.SetPen(wx.GREY_PEN)
        dc.SetBrush(wx.WHITE_BRUSH)
        for i in range(len(self.inscrits)+1):
            dc.DrawLine(0, i*BEBE_HEIGHT, (heureAffichageMax-heureAffichageMin) * HEURE_WIDTH + 1, i*BEBE_HEIGHT)

        heure = heureAffichageMin
        while heure <= heureAffichageMax:
            x = (heure - heureAffichageMin) * HEURE_WIDTH
            if heure == int(heure):
                dc.SetPen(wx.GREY_PEN)
            else:
                dc.SetPen(wx.LIGHT_GREY_PEN)
            dc.DrawLine(x, 0,  x, BEBE_HEIGHT * len(self.inscrits))
            heure += 1.0 / heureGranularite

        # les presences
        for i, inscrit in enumerate(self.inscrits):
            self.DrawPresence(i, dc)
            
        dc.EndDrawing()
    
    def __get_pos(self, x, y):
        posX = int((heureAffichageMin - BASE_MIN_HOUR + float(x * heureGranularite / HEURE_WIDTH) / heureGranularite) * BASE_GRANULARITY)
        posY = int(y / BEBE_HEIGHT)
        return posX, posY

    def OnLeftButtonDown(self, event):            
        # tests au cas ou ...  if self.curStartX < 4 * (heureAffichageMax-heureOuverture) and self.curStartY < len(self.inscrits):
        self.curStartX, self.curStartY = self.__get_pos(event.GetX(), event.GetY())
        inscrit = self.inscrits[self.curStartY]
        if self.date not in inscrit.presences:
            self.original_presence = None
            presence = inscrit.getPresenceFromSemaineType(self.date)
        else:
            self.original_presence = inscrit.presences[self.date]
            presence = Presence(inscrit, self.date, self.original_presence.previsionnel, self.original_presence.value, creation=False)
            if presence.value == PRESENT:
                presence.details = self.original_presence.details[:]

        inscrit.presences[self.date] = presence
        if presence.value != PRESENT:
            presence.set_value(PRESENT)
        if self.date <= datetime.date.today() and presence.previsionnel:
            presence.previsionnel = 0
            presence.details = [tmp * 2 for tmp in presence.details]
        presence.original_details = presence.details[:]
        if presence.details[self.curStartX] == 1:
            self.valeur_selection = 0
        else:
            self.valeur_selection = 1

        self.parent.UpdateButton(self.curStartY) # TODO pas toujours
        self.OnLeftButtonDragging(event)

    def OnLeftButtonDragging(self, event):            
        if self.valeur_selection != -1:
            inscrit = self.inscrits[self.curStartY]
            presence = inscrit.presences[self.date]
            self.curEndX, self.curEndY = self.__get_pos(event.GetX(), event.GetY())
            start, end = min(self.curStartX, self.curEndX), max(self.curStartX, self.curEndX)
            presence.details = presence.original_details[:]
            presence.details[start:end+BASE_GRANULARITY/heureGranularite] = [self.valeur_selection] * (end - start + BASE_GRANULARITY/heureGranularite)
            self.DrawLine(self.curStartY, presence)

    def OnLeftButtonUp(self, event):            
         if self.valeur_selection != -1:
            inscrit = self.inscrits[self.curStartY]            
            presence = inscrit.presences[self.date]
            start, end = min(self.curStartX, self.curEndX), max(self.curStartX, self.curEndX)
            presence.details = presence.original_details[:]
            presence.details[start:end+BASE_GRANULARITY/heureGranularite] = [self.valeur_selection] * (end - start + BASE_GRANULARITY/heureGranularite)
            for i in range(len(presence.details)):
                if presence.details[i] == 2:
                    presence.details[i] = 0           
            if not 1 in presence.details:
                presence.value = VACANCES
                presence.details = None
            if self.original_presence:
                obj = self.original_presence
                original_presence = self.original_presence
            else:
                obj = inscrit.presences[self.date]
                original_presence = inscrit.getPresenceFromSemaineType(self.date)
            if original_presence.value == PRESENT:
                history.append([(obj, 'value', original_presence.value),
                                (obj, 'previsionnel', original_presence.previsionnel),
                                (obj, 'details', original_presence.details[:])])
            else:
                history.append([(obj, 'value', original_presence.value),
                                (obj, 'previsionnel', original_presence.previsionnel),
                                (obj, 'details', None)])
            if self.original_presence:
                self.original_presence.value = presence.value
                self.original_presence.previsionnel = presence.previsionnel
                self.original_presence.details = presence.details
                inscrit.presences[self.date] = self.original_presence
            else:
                presence.create()
            self.valeur_selection = -1
            self.parent.UpdateButton(self.curStartY)
            self.DrawPresence(self.curStartY)

class PresencesPanel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, date = datetime.date.today()):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1, style=wx.SUNKEN_BORDER)
        self.profil = profil
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
	self.prenoms = wx.Window(self, -1, size=(PRENOMS_WIDTH, 0))
	self.sizer.Add(self.prenoms)
	self.buttons_sizer = wx.BoxSizer(wx.VERTICAL)
	self.sizer.Add(self.buttons_sizer, 0, wx.RIGHT, 2)
	self.inscrits = []
        self.tab_window = DayTabWindow(self, self.inscrits, date=date)
	self.sizer.Add(self.tab_window)
        self.date = date
        self.bmp = range(6)
        self.bmp[0] = wx.Bitmap("./bitmaps/icone_presence.png", wx.BITMAP_TYPE_PNG)
        self.bmp[1] = wx.Bitmap("./bitmaps/icone_presence_prev.png", wx.BITMAP_TYPE_PNG)
        self.bmp[2] = wx.Bitmap("./bitmaps/icone_vacances.png", wx.BITMAP_TYPE_PNG)
        self.bmp[3] = wx.Bitmap("./bitmaps/icone_vacances.png", wx.BITMAP_TYPE_PNG) # pas utilise pour le moment
        self.bmp[4] = wx.Bitmap("./bitmaps/icone_maladie.png", wx.BITMAP_TYPE_PNG)
        self.bmp[5] = wx.Bitmap("./bitmaps/icone_maladie.png", wx.BITMAP_TYPE_PNG) # pas utilise pour le moment
        self.UpdateContents()
        self.prenoms.Bind(wx.EVT_PAINT, self.OnPaint)
	self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.SetupScrolling()

    def OnButtonPressed(self, event):
        button = event.GetEventObject()
        inscrit = self.inscrits[button.inscrit]               
        if self.date not in inscrit.presences:
            inscrit.presences[self.date] = presence = inscrit.getPresenceFromSemaineType(self.date)
            presence.create()
        else:
            presence = inscrit.presences[self.date]
        if presence.previsionnel and presence.value == PRESENT and self.date <= datetime.date.today():
            history.append([(presence, 'previsionnel', 1)])
            presence.previsionnel = 0
        elif presence.value == PRESENT:
            history.append([(presence, 'value', PRESENT),
                            (presence, 'details', presence.details[:])])
            presence.value = VACANCES
        elif presence.value == VACANCES:
            history.append([(presence, 'value', VACANCES)])
            presence.value = MALADE
        elif presence.value == MALADE:
            history.append([(presence, 'value', MALADE),
                            (presence, 'details', None),
                            (presence, 'previsionnel', presence.previsionnel)])
            new_presence = inscrit.getPresenceFromSemaineType(self.date)
            presence.value, presence.details = new_presence.value, new_presence.details
            if creche.presences_previsionnelles and self.date > datetime.date.today():
              presence.previsionnel = 1
            else:
              presence.previsionnel = 0

        self.UpdateButton(button.inscrit)
        self.tab_window.DrawLine(button.inscrit, presence)

    def UpdateButton(self, index):
        inscrit = self.inscrits[index]
        if self.date in inscrit.presences:
            presence = inscrit.presences[self.date]
        else:
            presence = inscrit.getPresenceFromSemaineType(self.date)

        bmp_index = 2 * presence.value + presence.previsionnel
        self.buttons_sizer.GetItem(index).GetWindow().button.SetBitmapLabel(self.bmp[bmp_index])
        
    def UpdateContents(self):       
        old = len(self.inscrits)
        self.inscrits = []
        for inscrit in creche.inscrits:
            if inscrit.getInscription(self.date) is not None:
                self.inscrits.append(inscrit)
        new = len(self.inscrits)
        self.tab_window.inscrits = self.inscrits
        if self.date in creche.jours_fermeture:
            self.prenoms.SetMinSize((0, 0))
            self.tab_window.SetMinSize((0, 0))
            self.buttons_sizer.ShowItems(0)
        else:
            self.prenoms.SetMinSize((PRENOMS_WIDTH, BEBE_HEIGHT * len(self.inscrits) + 1))
            self.tab_window.SetMinSize((int((heureAffichageMax-heureOuverture) * HEURE_WIDTH + 1), BEBE_HEIGHT * len(self.inscrits) + 1))
            self.buttons_sizer.ShowItems(1)

        for i in range(old, new, -1):
            self.buttons_sizer.GetItem(i-1).DeleteWindows()
            self.buttons_sizer.Detach(i-1)
        for i in range(old, new):
	    panel = wx.Panel(self, style=wx.SUNKEN_BORDER)
            self.buttons_sizer.Add(panel)
            panel.button = wx.BitmapButton(panel, -1, self.bmp[0], size=(26, 26), style=wx.NO_BORDER)
            panel.button.inscrit = i
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(panel.button)
            panel.SetSizer(sizer)
            if (self.profil & PROFIL_SAISIE_PRESENCES) or self.date > datetime.date.today():
                self.Bind(wx.EVT_BUTTON, self.OnButtonPressed, panel.button)
        self.sizer.Layout()
        for i in range(len(self.inscrits)):
            self.UpdateButton(i)
        
        self.Refresh()
        self.tab_window.Refresh()

        
    def OnPaint(self, event):
        dc = wx.PaintDC(self.prenoms)
        self.prenoms.PrepareDC(dc)
        # since we're not buffering in this case, we have to
        # paint the whole window, potentially very time consuming.
        self.DoDrawing(dc)

    def DoDrawing(self, dc, printing=False):
        dc.BeginDrawing()
       
        # les bebes
        dc.SetTextForeground("BLACK")
        font = wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL)
        dc.SetFont(font)

        for i, inscrit in enumerate(self.inscrits):
            if inscrit.getInscription(self.date) is not None:
                dc.DrawText(GetInscritId(inscrit, self.inscrits), 10, 5 + i * BEBE_HEIGHT)
        
        dc.EndDrawing()

    def SetDate(self, date):
        self.date = date
        self.tab_window.date = date
        self.UpdateContents()

class DayPanel(wx.Panel):
    def __init__(self, parent, date):
        wx.Panel.__init__(self, parent, id=-1, style=wx.LB_DEFAULT)
	self.sizer = wx.BoxSizer(wx.VERTICAL)
	self.echelle = wx.Window(self, -1, size=(0, 25))
	self.sizer.Add(self.echelle, 0, wx.EXPAND)
        self.presences_panel = PresencesPanel(self, date)
	self.sizer.Add(self.presences_panel, 1, wx.EXPAND)
	self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.echelle.Bind(wx.EVT_PAINT, self.OnPaint)

    def SetDate(self, date):
        self.presences_panel.SetDate(date)
	self.sizer.Layout()
        
    def OnPaint(self, event):
        dc = wx.PaintDC(self.echelle)
        self.echelle.PrepareDC(dc)
        dc.BeginDrawing()
        
        # l'echelle
        dc.SetBrush(wx.GREY_BRUSH)
        dc.SetPen(wx.GREY_PEN)
        dc.DrawRectangle(0, 1, dc.GetSize()[0], 25)
        dc.SetPen(wx.WHITE_PEN)
	font = wx.Font(7, wx.SWISS, wx.NORMAL, wx.NORMAL)
        dc.SetFont(font)
        dc.SetTextForeground("WHITE")
        heure = heureAffichageMin
        while heure <= heureAffichageMax:
            x = PRENOMS_WIDTH + BUTTONS_WIDTH + (heure - heureAffichageMin) * HEURE_WIDTH
            if abs(heure - round(heure)) < 0.01:
                dc.DrawLine(x, 20, x, 12)
                dc.DrawText(str(int(round(heure)))+"h", x - 3, 0)
            else:
                dc.DrawLine(x, 20, x, 15)
            heure += 1.0 / heureGranularite
            
        dc.EndDrawing()

class PlanningPanel(GPanel):
    bitmap = './bitmaps/presences.png'
    index = 20
    profil = PROFIL_ALL
    def __init__(self, parent):
        GPanel.__init__(self, parent, u'Présences enfants')
        
        # La combobox pour la selection de la semaine
        self.combobox = wx.Choice(self, -1)
	self.sizer.Add(self.combobox, 0, wx.EXPAND, 0)
        day = first_monday = getfirstmonday()
        semaine = getNumeroSemaine(day)
        while day < last_date:
            string = 'Semaine %d (%d %s %d)' % (semaine, day.day, months[day.month - 1], day.year)
            self.combobox.Append(string, day)
            if day.year == (day + datetime.timedelta(7)).year:
                semaine += 1
            else:
                semaine = 1
            day += datetime.timedelta(7)

        delta = datetime.date.today() - first_monday
        semaine = int(delta.days / 7)
        self.combobox.SetSelection(semaine)

        # le notebook pour les jours de la semaine
        self.notebook = wx.Notebook(self, style=wx.LB_DEFAULT)
	self.sizer.Add(self.notebook, 1, wx.EXPAND|wx.TOP, 5)
        for week_day in range(5):
            day = first_monday + datetime.timedelta(semaine * 7 + week_day)
            title = days[week_day] + " " + str(day.day) + " " + months[day.month - 1] + " " + str(day.year)
            self.notebook.AddPage(DayPanel(self.notebook, day), title)
        
        self.Bind(wx.EVT_CHOICE, self.EvtChoice, self.combobox)

    def EvtChoice(self, evt):
        cb = evt.GetEventObject()
        monday = cb.GetClientData(cb.GetSelection())
        for week_day in range(5):
            day = monday + datetime.timedelta(week_day)
	    note = self.notebook.GetPage(week_day)
            self.notebook.SetPageText(week_day, days[week_day] + " " + str(day.day) + " " + months[day.month - 1] + " " + str(day.year))
            note = self.notebook.GetPage(week_day)
            if day in creche.jours_fermeture:
                pass
            else:
                pass
            note.SetDate(day)
            note.presences_panel.UpdateContents()
            self.notebook.SetSelection(0)
        self.sizer.Layout()

    def UpdateContents(self):
        for week_day in range(5):
            note = self.notebook.GetPage(week_day)
            note.presences_panel.UpdateContents()
        self.sizer.Layout()

panels = [PlanningPanel]
