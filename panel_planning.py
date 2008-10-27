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

import wx, wx.lib.scrolledpanel
import datetime
from constants import *
from parameters import *
from functions import *
from sqlobjects import *
from history import *
from controls import *

PRENOMS_WIDTH = 80 # px
BUTTONS_WIDTH = 34 # px
BASE_WIDTH = 12 # px
LINE_HEIGHT = 30 # px
        
class DayTabWindow(wx.Window):
    def __init__(self, parent, inscrits, date, *args, **kwargs):
        wx.Window.__init__(self, parent, size=((creche.affichage_max-creche.affichage_min) * 4 * BASE_WIDTH + 1, LINE_HEIGHT * len(inscrits) + 1), *args, **kwargs)
        self.parent = parent
        self.inscrits = inscrits
        self.SetBackgroundColour(wx.WHITE)
        self.valeur_selection = -1
        self.date = date
        self.green_brush = [ wx.Brush(wx.Color(5, 203, 28)), wx.Brush(wx.Color(150, 229, 139)) ]
        self.red_brush = [ wx.Brush(wx.Color(203, 5, 28)), wx.Brush(wx.Color(229, 150, 139)) ]

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

    def DrawLine(self, ligne, journee, dc):
        for debut, fin, valeur in journee.get_activities():
            r, g, b, t, s = getActivityColor(valeur)
            try:
              dc.SetPen(wx.Pen(wx.Colour(r, g, b, wx.ALPHA_OPAQUE)))
              dc.SetBrush(wx.Brush(wx.Colour(r, g, b, t), s))
            except:
              dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
              dc.SetBrush(wx.Brush(wx.Colour(r, g, b), s))
            rect = wx.Rect(1+(debut-int(creche.affichage_min*4))*BASE_WIDTH, 1 + ligne * LINE_HEIGHT, (fin-debut)*BASE_WIDTH-1, LINE_HEIGHT-1)
            dc.DrawRoundedRectangleRect(rect, 4)

    def DrawPresence(self, index, dc):
        inscrit = self.inscrits[index]
        if self.date in inscrit.journees:
            journee = inscrit.journees[self.date]
        else:
            journee = inscrit.getJourneeFromSemaineType(self.date)
        self.DrawLine(index, journee, dc)

    def DoDrawing(self, dc, printing=False):
        dc.BeginDrawing()

        # le quadrillage
        dc.SetPen(wx.GREY_PEN)
        dc.SetBrush(wx.WHITE_BRUSH)
        affichage_min = int(creche.affichage_min * 4)
        affichage_max = int(creche.affichage_max * 4)
        heure = affichage_min
        while heure <= affichage_max:
            x = (heure - affichage_min) * BASE_WIDTH
            if heure % 4 == 0:
                dc.SetPen(wx.GREY_PEN)
            else:
                dc.SetPen(wx.LIGHT_GREY_PEN)
            dc.DrawLine(x, 0,  x, dc.GetSize()[1])
            heure += 1

        # les presences
        try:
            dc = wx.GCDC(dc)
        except:
            pass
        for i, inscrit in enumerate(self.inscrits):
            self.DrawPresence(i, dc)

        dc.EndDrawing()

    def __get_pos(self, x, y):
        posX = int(creche.affichage_min * BASE_GRANULARITY + (x / BASE_WIDTH))
        posY = int(y / LINE_HEIGHT)
        return posX, posY

    def OnLeftButtonDown(self, event):
        posX, self.curStartY = self.__get_pos(event.GetX(), event.GetY())
        self.curStartX = (posX / (4 / creche.granularite)) * (4 / creche.granularite)

        inscrit = self.inscrits[self.curStartY]
        if self.date not in inscrit.journees:
            journee = inscrit.getJourneeFromSemaineType(self.date, creation=True)
            inscrit.journees[self.date] = journee
        else:
            journee = inscrit.journees[self.date]

        journee.original_values = journee.values[:]
        if journee.get_state() < 0 or not journee.values[posX] & (PRESENT<<self.parent.parent.panel.activity.value) or (datetime.date.today() >= self.date and creche.presences_previsionnelles and (journee.values[posX] & PREVISIONNEL)):
            self.valeur_selection = 1
        else:
            self.valeur_selection = 0

        if datetime.date.today() < self.date and creche.presences_previsionnelles:
            self.valeur_selection |= PREVISIONNEL

        self.parent.UpdateButton(self.curStartY) # TODO pas toujours
        self.OnLeftButtonDragging(event)

    def OnLeftButtonDragging(self, event):
        if self.valeur_selection != -1:
            inscrit = self.inscrits[self.curStartY]
            journee = inscrit.journees[self.date]
            posX, self.curEndY = self.__get_pos(event.GetX(), event.GetY())
            self.curEndX = (posX / (4 / creche.granularite)) * (4 / creche.granularite)
            start, end = min(self.curStartX, self.curEndX), max(self.curStartX, self.curEndX)
            journee.values = journee.original_values[:]
            for i in range(start, end+BASE_GRANULARITY/creche.granularite):
                if journee.values[i] < 0:
                    journee.values[i] = 0
                if self.valeur_selection:
                    journee.values[i] |= PRESENT << self.parent.parent.panel.activity.value
                else:
                    journee.values[i] &= ~(PRESENT << self.parent.parent.panel.activity.value)
            self.Refresh(True, wx.Rect(0, self.curStartY*LINE_HEIGHT, (creche.affichage_max-creche.affichage_min)*4*BASE_WIDTH, LINE_HEIGHT))

    def OnLeftButtonUp(self, event):
         if self.valeur_selection != -1:
            start, end = min(self.curStartX, self.curEndX), max(self.curStartX, self.curEndX)
            inscrit = self.inscrits[self.curStartY]
            journee = inscrit.journees[self.date]
            journee.values = journee.original_values[:]
            state = journee.get_state()
            if state < 0:
                journee.set_state(ABSENT, inscrit.getJourneeFromSemaineType(self.date))
            activity = self.parent.parent.panel.activity
            for i in range(start, end+BASE_GRANULARITY/creche.granularite):
                if self.valeur_selection:
                    if activity.mode & MODE_LIBERE_PLACE:
                        journee.values[i] = PRESENT << activity.value
                    else:
                        journee.values[i] |= PRESENT << activity.value
                else:
                    journee.values[i] &= ~(PRESENT << activity.value)
            journee.save()
            history.Append([Change(journee, 'values', journee.original_values),
                            Call(journee.save)])

            self.Refresh(True, wx.Rect(0, self.curStartY*LINE_HEIGHT, (creche.affichage_max-creche.affichage_min)*4*BASE_WIDTH, LINE_HEIGHT))
            self.valeur_selection = -1
            self.parent.UpdateButton(self.curStartY)

class PresencesPanel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, date = datetime.date.today()):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1, size=((creche.affichage_max-creche.affichage_min) * 4 * BASE_WIDTH + PRENOMS_WIDTH + 60, -1), style=wx.SUNKEN_BORDER)
        self.parent = parent
        self.profil = profil
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.prenoms = wx.Window(self, -1, size=(PRENOMS_WIDTH, 0))
        self.sizer.Add(self.prenoms, 0, wx.EXPAND)
        self.buttons_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.buttons_sizer, 0, wx.EXPAND|wx.RIGHT, 2)
        self.inscrits = []
        self.tab_window = DayTabWindow(self, self.inscrits, date=date)
        self.sizer.Add(self.tab_window, 0, wx.EXPAND)
        self.date = date
        self.bmp = range(6)
        self.bmp[0] = wx.Bitmap("./bitmaps/icone_presence.png", wx.BITMAP_TYPE_PNG)
        self.bmp[1] = wx.Bitmap("./bitmaps/icone_presence_prev.png", wx.BITMAP_TYPE_PNG)
        self.bmp[2] = wx.Bitmap("./bitmaps/icone_vacances.png", wx.BITMAP_TYPE_PNG)
        self.bmp[3] = wx.Bitmap("./bitmaps/icone_maladie.png", wx.BITMAP_TYPE_PNG)
        self.UpdateContents()
        self.prenoms.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetSizer(self.sizer)
        self.SetupScrolling(scroll_x = False)
        self.SetAutoLayout(1)

    def OnButtonPressed(self, event):
        button = event.GetEventObject()
        inscrit = self.inscrits[button.inscrit]
        if self.date not in inscrit.journees:
            inscrit.journees[self.date] = journee = inscrit.getJourneeFromSemaineType(self.date)
        else:
            journee = inscrit.journees[self.date]

        history.Append([Change(journee, 'values', journee.values[:]),
                        Call(journee.save)])

        state = journee.get_state()
        if state == VACANCES:
            journee.set_state(MALADE, inscrit.getJourneeFromSemaineType(self.date))
        elif state == MALADE:
            if self.date <= datetime.date.today():
                journee.set_state(PRESENT, inscrit.getJourneeFromSemaineType(self.date))
            else:
                journee.set_state(PRESENT|PREVISIONNEL, inscrit.getJourneeFromSemaineType(self.date))
        elif self.date <= datetime.date.today() and state == PRESENT+PREVISIONNEL:
            journee.confirm()
        else:
            journee.set_state(VACANCES, inscrit.getJourneeFromSemaineType(self.date))


        self.UpdateButton(button.inscrit)
        self.tab_window.Refresh()

    def UpdateButton(self, index):
        inscrit = self.inscrits[index]
        if self.date in inscrit.journees:
            journee = inscrit.journees[self.date]
        else:
            journee = inscrit.getJourneeFromSemaineType(self.date)

        state = journee.get_state()
        if state == MALADE:
            bmp_index = 3
        elif state == VACANCES:
            bmp_index = 2
        elif state & PREVISIONNEL:
            bmp_index = 1
        else:
            bmp_index = 0

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
            self.prenoms.SetMinSize((PRENOMS_WIDTH, LINE_HEIGHT * len(self.inscrits) - 1))
            self.tab_window.SetMinSize((int((creche.affichage_max-creche.affichage_min) * 4 * BASE_WIDTH + 1), LINE_HEIGHT * len(self.inscrits) - 1))
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

        # les prénoms des inscrits
        dc.SetTextForeground("BLACK")
        font = wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL)
        dc.SetFont(font)

        for i, inscrit in enumerate(self.inscrits):
            if inscrit.getInscription(self.date) is not None:
                dc.DrawText(GetInscritId(inscrit, self.inscrits), 5, 5 + i * LINE_HEIGHT)

        dc.SetPen(wx.GREY_PEN)
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.EndDrawing()

    def SetDate(self, date):
        self.date = date
        self.tab_window.date = date
        self.UpdateContents()

class ActivitiesPanel(wx.Window):
    def __init__(self, parent):
        wx.Window.__init__(self, parent, -1, size=(-1, 50))
        
class DayPanel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, panel, date):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, id=-1, style=wx.LB_DEFAULT)
        self.panel = panel
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.echelle = wx.Window(self, -1, size=(-1, 25))
        self.sizer.Add(self.echelle, 0, wx.EXPAND)
        self.presences_panel = PresencesPanel(self, date)
        self.sizer.Add(self.presences_panel, 1, wx.EXPAND)
        self.activities_panel = ActivitiesPanel(self)
        self.sizer.Add(self.activities_panel, 0, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.SetupScrolling(scroll_y = False)
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
        affichage_min = int(creche.affichage_min * 4)
        affichage_max = int(creche.affichage_max * 4)
        heure = affichage_min
        while heure <= affichage_max:
            x = PRENOMS_WIDTH + BUTTONS_WIDTH + (heure - affichage_min) * BASE_WIDTH
            if heure % 4 == 0:
                dc.DrawLine(x, 20, x, 12)
                dc.DrawText(str(int(round(heure/4)))+"h", x - 3, 0)
            else:
                dc.DrawLine(x, 20, x, 15)
            heure += 1

        dc.EndDrawing()

class PlanningPanel(GPanel):
    bitmap = './bitmaps/presences.png'
    index = 20
    profil = PROFIL_ALL

    def __init__(self, parent):
        GPanel.__init__(self, parent, u'Présences enfants')
        self.activity = Activite(creation=False, value=0)

        # La combobox pour la selection de la semaine
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.week_choice = wx.Choice(self, -1)
        sizer.Add(self.week_choice, 1, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND)
        day = first_monday = getfirstmonday()
        semaine = getNumeroSemaine(day)
        while day < last_date:
            string = 'Semaine %d (%d %s %d)' % (semaine, day.day, months[day.month - 1], day.year)
            self.week_choice.Append(string, day)
            if day.year == (day + datetime.timedelta(7)).year:
                semaine += 1
            else:
                semaine = 1
            day += datetime.timedelta(7)
        delta = datetime.date.today() - first_monday
        semaine = int(delta.days / 7)
        self.week_choice.SetSelection(semaine)
        self.Bind(wx.EVT_CHOICE, self.EvtChoice, self.week_choice)
        
        # La combobox pour la selection de l'outil (si activités)
        self.activity_choice = ActivityComboBox(self, -1, style=wx.CB_READONLY, size=(100, -1))
        sizer.Add(self.activity_choice, 0, wx.ALIGN_CENTER_VERTICAL)
        self.Bind(wx.EVT_COMBOBOX, self.changeTool, self.activity_choice)
        self.sizer.Add(sizer, 0, wx.EXPAND)
        
        # le notebook pour les jours de la semaine
        self.notebook = wx.Notebook(self, style=wx.LB_DEFAULT)
        self.sizer.Add(self.notebook, 1, wx.EXPAND|wx.TOP, 5)
        for week_day in range(5):
            day = first_monday + datetime.timedelta(semaine * 7 + week_day)
            title = days[week_day] + " " + str(day.day) + " " + months[day.month - 1] + " " + str(day.year)
            self.notebook.AddPage(DayPanel(self.notebook, self, day), title)

        self.sizer.Layout()

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

    def changeTool(self, evt):
        cb = evt.GetEventObject()
        self.activity = cb.GetClientData(cb.GetSelection())

    def UpdateContents(self):
        self.activity_choice.Clear()
        tmp = Activite(creation=False)
        tmp.value = 0
        self.activity_choice.Append(u'Présences', tmp)
        selected = 0
        if len(creche.activites) > 0:
            self.activity_choice.Enable()
            for i, activity in enumerate(creche.activites.values()):
                self.activity_choice.Append(activity.label, activity)
                if self.activity.value == activity.value:
                    selected = i+1
        else:
            self.activity_choice.Disable()
        self.activity_choice.SetSelection(selected)
        for week_day in range(5):
            note = self.notebook.GetPage(week_day)
            note.presences_panel.UpdateContents()
        self.sizer.Layout()

panels = [PlanningPanel]
