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
from controls import getActivityColor
from history import *

LABEL_WIDTH = 80 # px
ICONS_WIDTH = 34 # px
COLUMN_WIDTH = 12 # px
LINE_HEIGHT = 30 # px

BUTTON_BITMAPS = { PRESENT: wx.Bitmap("./bitmaps/icone_presence.png", wx.BITMAP_TYPE_PNG),
                   PRESENT+PREVISIONNEL: wx.Bitmap("./bitmaps/icone_presence_prev.png", wx.BITMAP_TYPE_PNG),
                   VACANCES: wx.Bitmap("./bitmaps/icone_vacances.png", wx.BITMAP_TYPE_PNG),
                   MALADE: wx.Bitmap("./bitmaps/icone_maladie.png", wx.BITMAP_TYPE_PNG),
                   }

class PlanningGridWindow(wx.Window):
    def __init__(self, parent, activity_combobox):
        wx.Window.__init__(self, parent, size=((creche.affichage_max-creche.affichage_min) * 4 * COLUMN_WIDTH + 1, -1))
        self.SetBackgroundColour(wx.WHITE)
        self.lines = []
        self.activity_combobox = activity_combobox
        self.state = -1
        self.Bind(wx.EVT_PAINT, self.OnPaint)

##        if (profil & PROFIL_SAISIE_PRESENCES) or date > datetime.date.today():
        self.SetCursor(wx.StockCursor(wx.CURSOR_PENCIL))        
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftButtonDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftButtonUp)
        self.Bind(wx.EVT_MOTION, self.OnLeftButtonDragging)

    def SetLines(self, lines):
        self.lines = lines
        self.SetMinSize((int((creche.affichage_max-creche.affichage_min) * 4 * COLUMN_WIDTH + 1), LINE_HEIGHT * len(self.lines) - 1))

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        self.PrepareDC(dc)
        dc.BeginDrawing()

        # le quadrillage
        dc.SetPen(wx.GREY_PEN)
        dc.SetBrush(wx.WHITE_BRUSH)
        affichage_min = int(creche.affichage_min * 4)
        affichage_max = int(creche.affichage_max * 4)
        heure = affichage_min
        height = dc.GetSize()[1]
        while heure <= affichage_max:
            x = (heure - affichage_min) * COLUMN_WIDTH
            if heure % 4 == 0:
                dc.SetPen(wx.GREY_PEN)
            else:
                dc.SetPen(wx.LIGHT_GREY_PEN)
            dc.DrawLine(x, 0,  x, height)
            heure += 1

        # les presences
        try:
            dc = wx.GCDC(dc)
        except:
            pass

        for i, line in enumerate(self.lines):
            self.DrawLine(dc, i, line)
        
        dc.EndDrawing()

    def DrawLine(self, dc, index, line):
        for start, end, activity in line.get_activities():
            # print debut, fin, valeur
            r, g, b, t, s = getActivityColor(activity)
            try:
              dc.SetPen(wx.Pen(wx.Colour(r, g, b, wx.ALPHA_OPAQUE)))
              dc.SetBrush(wx.Brush(wx.Colour(r, g, b, t), s))
            except:
              dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
              dc.SetBrush(wx.Brush(wx.Colour(r, g, b), s))
            rect = wx.Rect(1+(start-int(creche.affichage_min*4))*COLUMN_WIDTH, 1 + index*LINE_HEIGHT, (end-start)*COLUMN_WIDTH-1, LINE_HEIGHT-1)
            dc.DrawRoundedRectangleRect(rect, 4)
        
    def __get_pos(self, x, y):
        l = int(creche.affichage_min * BASE_GRANULARITY + (x / COLUMN_WIDTH))
        c = int(y / LINE_HEIGHT)
        return l, c

    def OnLeftButtonDown(self, event):
        posX, self.curStartY = self.__get_pos(event.GetX(), event.GetY())
        self.curStartX = (posX / (4 / creche.granularite)) * (4 / creche.granularite)
        line = self.lines[self.curStartY]
        line.original_values = line.values[:]
        if line.get_state() < 0 or not line.values[posX] & (1<<self.activity_combobox.activity.value):
            self.state = 1
        else:
            self.state = 0
        self.OnLeftButtonDragging(event)

    def OnLeftButtonDragging(self, event):
        if self.state != -1:
            posX, self.curEndY = self.__get_pos(event.GetX(), event.GetY())
            self.curEndX = (posX / (4 / creche.granularite)) * (4 / creche.granularite)
            start, end = min(self.curStartX, self.curEndX), max(self.curStartX, self.curEndX)
            line = self.lines[self.curStartY]
            line.values = line.original_values[:]
            for i in range(start, end+BASE_GRANULARITY/creche.granularite):
                if line.values[i] < 0:
                    if creche.presences_previsionnelles and line.date > datetime.date.today():
                        line.values[i] = PREVISIONNEL
                    else:
                        line.values[i] = 0
                if self.state:
                    line.values[i] |= 1 << self.activity_combobox.activity.value
                else:
                    line.values[i] &= ~(1 << self.activity_combobox.activity.value)
            self.Refresh(True, wx.Rect(0, self.curStartY*LINE_HEIGHT, (creche.affichage_max-creche.affichage_min)*4*COLUMN_WIDTH, LINE_HEIGHT))

    def OnLeftButtonUp(self, event):
         if self.state != -1:
            start, end = min(self.curStartX, self.curEndX), max(self.curStartX, self.curEndX)
            line = self.lines[self.curStartY]
            line.values = line.original_values[:]
            if line.get_state() < 0:
                if creche.presences_previsionnelles and line.date > datetime.date.today():
                    line.values = [PREVISIONNEL] * 96
                else:
                    line.values = [0] * 96
            for i in range(start, end+BASE_GRANULARITY/creche.granularite):
                if self.state:
                    if self.activity_combobox.activity.mode & MODE_LIBERE_PLACE:
                        line.values[i] = 1 << self.activity_combobox.activity.value
                    else:
                        line.values[i] |= 1 << self.activity_combobox.activity.value
                else:
                    line.values[i] &= ~(1 << self.activity_combobox.activity.value)

            line.save()
            history.Append([Change(line, 'values', line.original_values),
                            Call(line.save)])

            self.Refresh(True, wx.Rect(0, self.curStartY*LINE_HEIGHT, (creche.affichage_max-creche.affichage_min)*4*COLUMN_WIDTH, LINE_HEIGHT))
            self.state = -1
            self.GetParent().UpdateLine(self.curStartY)

class PlanningInternalPanel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, activity_combobox):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1, size=((creche.affichage_max-creche.affichage_min) * 4 * COLUMN_WIDTH + LABEL_WIDTH + 60, -1), style=wx.SUNKEN_BORDER)
        self.lines = []
        self.summary_panel = None
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.labels_panel = wx.Window(self, -1, size=(LABEL_WIDTH, -1))
        self.sizer.Add(self.labels_panel, 0, wx.EXPAND)
        self.buttons_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.buttons_sizer, 0, wx.EXPAND|wx.RIGHT, 2)
        self.grid_panel = PlanningGridWindow(self, activity_combobox)
        self.sizer.Add(self.grid_panel, 0, wx.EXPAND)
        self.labels_panel.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetSizer(self.sizer)
        self.SetupScrolling(scroll_x = False)

    def OnButtonPressed(self, event):
        button = event.GetEventObject()
        line = self.lines[button.line]

        history.Append([Change(line, 'values', line.values[:]),
                        Call(line.save)])

        state = line.get_state()
        if state == VACANCES:
            line.set_state(MALADE, line.reference)
        elif state == MALADE:
            # TODO dans ce cas plutôt recopier la référence que mettre PRESENT partout
            if not creche.presences_previsionnelles or line.date <= datetime.date.today():
                line.set_state(PRESENT, line.reference)
            else:
                line.set_state(PRESENT|PREVISIONNEL, line.reference)
        elif line.date <= datetime.date.today() and state == PREVISIONNEL:
            line.confirm()
        else:
            line.set_state(VACANCES, line.reference)

        self.grid_panel.Refresh() # TODO UpdateLine aussi !
        self.UpdateLine(button.line)

    def UpdateLine(self, index):
        self.UpdateButton(index)
        self.GetParent().UpdateLine(index)
            
    def UpdateButton(self, index):
        self.buttons_sizer.GetItem(index).GetWindow().button.SetBitmapLabel(BUTTON_BITMAPS[self.lines[index].get_state()])

# self.buttons_sizer.ShowItems(1)

    def SetLines(self, lines):
        previous_count = len(self.lines)
        self.lines = lines
        self.grid_panel.SetLines(lines)        
        count = len(self.lines)
        if count != previous_count:
            self.SetScrollPos(wx.VERTICAL, 0)
            for i in range(previous_count, count, -1):
                self.buttons_sizer.GetItem(i-1).DeleteWindows()
                self.buttons_sizer.Detach(i-1)
            for i in range(previous_count, count):
                panel = wx.Panel(self, style=wx.SUNKEN_BORDER)
                self.buttons_sizer.Add(panel)
                panel.button = wx.BitmapButton(panel, -1, BUTTON_BITMAPS[PRESENT], size=(26, 26), style=wx.NO_BORDER)
                panel.button.line = i
                sizer = wx.BoxSizer(wx.VERTICAL)
                sizer.Add(panel.button)
                panel.SetSizer(sizer)
                sizer.Layout()
##            if (self.profil & PROFIL_SAISIE_PRESENCES) or self.date > datetime.date.today():
                self.Bind(wx.EVT_BUTTON, self.OnButtonPressed, panel.button)
            self.buttons_sizer.Layout()
            self.labels_panel.SetMinSize((LABEL_WIDTH, LINE_HEIGHT*count - 1))
            self.sizer.Layout()
            self.SetupScrolling(scroll_x=False)
            self.GetParent().sizer.Layout()

        for i in range(count):
            self.UpdateButton(i)

        self.grid_panel.Refresh()
        self.labels_panel.Refresh()
            
    def OnPaint(self, event):
        dc = wx.PaintDC(self.labels_panel)
        self.labels_panel.PrepareDC(dc)
        dc.BeginDrawing()
        dc.SetTextForeground("BLACK")
        font = wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL)
        dc.SetFont(font)
        for i, line in enumerate(self.lines):
            dc.DrawText(line.label, 5, 5 + LINE_HEIGHT*i)
        dc.EndDrawing()


class PlanningSummaryPanel(wx.Window):
    def __init__(self, parent):
        self.activities_count = len(creche.activites)
        self.summary = {}
        wx.Window.__init__(self, parent, -1, size=(-1, 22+20*self.activities_count))
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def UpdateContents(self):
        if self.activities_count != len(creche.activites):
            self.activities_count = len(creche.activites)
            self.SetMinSize((-1, 22+20*self.activities_count))
            self.GetParent().sizer.Layout()
            
        lines = self.GetParent().GetSummaryLines()
        self.summary = {}
        for activity in [0] + creche.activites.keys():
            self.summary[activity] = [0] * 96
            for i in range(96):
                for line in lines:
                    if line[i] > 0 and line[i] & (1 << activity):
                        self.summary[activity][i] += 1
        self.Refresh()

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        self.PrepareDC(dc)

        try:
            dc = wx.GCDC(dc)
        except:
            pass
        
        for i, activity in enumerate(self.summary.keys()):
            if activity == 0:
                dc.DrawText(u"Présences", 5, 6 + i * 20)
            else:
                dc.DrawText(creche.activites[i].label, 5, 6 + i * 20)
            self.DrawLine(dc, i, activity)

    def DrawLine(self, dc, index, activity):
        line = self.summary[activity]
        r, g, b, t, s = getActivityColor(activity)
        try:
            dc.SetPen(wx.Pen(wx.Colour(r, g, b, wx.ALPHA_OPAQUE)))
            dc.SetBrush(wx.Brush(wx.Colour(r, g, b, t), s))
        except:
            dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
            dc.SetBrush(wx.Brush(wx.Colour(r, g, b), s))
        
        debut = int(creche.affichage_min*4)
        fin = int(creche.affichage_max*4)
        x = debut
        v = 0
        holes = []
        a = 0
        while x <= fin:
            if x == fin:
                nv = 0
            else:
                nv = line[x]
            if nv != v:
                if v != 0:
                    rect = wx.Rect(LABEL_WIDTH+35+(a-debut)*COLUMN_WIDTH, 2 + index * 20, (x-a)*COLUMN_WIDTH-1, 19)
                    dc.DrawRoundedRectangleRect(rect, 4)
                    dc.DrawText(str(v), LABEL_WIDTH - 4*len(str(v)) + 36 + (float(x+a)/2-debut)*COLUMN_WIDTH, 4 + index * 20)
                else:
                    holes.append((a, x))
                a = x    
                v = nv
            x += 1
        
        dc.SetPen(wx.GREY_PEN)
        for a, b in holes:
            if a == 0:
                a1 = 5
            else:
                a1 = LABEL_WIDTH + 36 + (a-debut)*COLUMN_WIDTH
            dc.DrawLine(a1, 20 + index * 20, LABEL_WIDTH+32+(b-debut)*COLUMN_WIDTH, 20 + 20*index)
            
        
class PlanningWidget(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, activity_combobox):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, id=-1, style=wx.LB_DEFAULT)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.scale_window = wx.Window(self, -1, size=(-1, 25))
        self.sizer.Add(self.scale_window, 0, wx.EXPAND)
        self.internal_panel = PlanningInternalPanel(self, activity_combobox)
        self.sizer.Add(self.internal_panel, 1, wx.EXPAND)
        self.summary_panel = PlanningSummaryPanel(self)
        self.sizer.Add(self.summary_panel, 0, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.SetupScrolling(scroll_y = False)
        self.sizer.Layout()
        self.scale_window.Bind(wx.EVT_PAINT, self.OnPaint)

    def SetLines(self, lines):
        self.lines = lines
        self.internal_panel.SetLines(lines)
        self.summary_panel.UpdateContents()
        
    def UpdateLine(self, index):
        self.summary_panel.UpdateContents()
        
    def GetSummaryLines(self):
        values = []
        for line in self.lines:
            values.append(line.values)
        return values

    def OnPaint(self, event):
        dc = wx.PaintDC(self.scale_window)
        self.scale_window.PrepareDC(dc)
        dc.BeginDrawing()
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
            x = LABEL_WIDTH + ICONS_WIDTH + (heure - affichage_min) * COLUMN_WIDTH
            if heure % 4 == 0:
                dc.DrawLine(x, 20, x, 12)
                dc.DrawText(str(int(round(heure/4)))+"h", x - 3, 0)
            else:
                dc.DrawLine(x, 20, x, 15)
            heure += 1
        dc.EndDrawing()
