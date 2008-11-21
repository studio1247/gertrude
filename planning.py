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
from buffered_window import BufferedWindow
import datetime
from constants import *
from controls import getActivityColor
from history import *

# PlanningWidget options
NO_ICONS = 1
READ_ONLY = 2
PRESENCES_ONLY = 4

# Elements size
LABEL_WIDTH = 80 # px
ICONS_WIDTH = 33 # px
COLUMN_WIDTH = 12 # px
LINE_HEIGHT = 30 # px

BUTTON_BITMAPS = { ABSENT: wx.Bitmap("./bitmaps/icone_vacances.png", wx.BITMAP_TYPE_PNG),
                   ABSENT+PREVISIONNEL: wx.Bitmap("./bitmaps/icone_vacances.png", wx.BITMAP_TYPE_PNG),
                   PRESENT: wx.Bitmap("./bitmaps/icone_presence.png", wx.BITMAP_TYPE_PNG),
                   PRESENT+PREVISIONNEL: wx.Bitmap("./bitmaps/icone_presence_prev.png", wx.BITMAP_TYPE_PNG),
                   VACANCES: wx.Bitmap("./bitmaps/icone_vacances.png", wx.BITMAP_TYPE_PNG),
                   MALADE: wx.Bitmap("./bitmaps/icone_maladie.png", wx.BITMAP_TYPE_PNG),
                   }

class PlanningGridWindow(BufferedWindow):
    def __init__(self, parent, activity_combobox):
        self.disable_cause = None
        self.lines = []
        BufferedWindow.__init__(self, parent, size=((creche.affichage_max-creche.affichage_min) * 4 * COLUMN_WIDTH + 1, -1))
        self.SetBackgroundColour(wx.WHITE)
        self.activity_combobox = activity_combobox
        self.state = -1
##        if (profil & PROFIL_SAISIE_PRESENCES) or date > datetime.date.today():
        self.SetCursor(wx.StockCursor(wx.CURSOR_PENCIL))        
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftButtonDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftButtonUp)
        self.Bind(wx.EVT_MOTION, self.OnLeftButtonDragging)

    def Disable(self, cause):
        self.disable_cause = cause
        self.lines = []
        self.SetMinSize((int((creche.affichage_max-creche.affichage_min) * 4 * COLUMN_WIDTH + 1), 400))
        
    def SetLines(self, lines):
        self.disable_cause = None
        self.lines = lines
        self.SetMinSize((int((creche.affichage_max-creche.affichage_min) * 4 * COLUMN_WIDTH + 1), LINE_HEIGHT * len(self.lines) - 1))
       
    def UpdateLine(self, index):
        self.UpdateDrawing()

    def Draw(self, dc):
        dc.BeginDrawing()
        dc.Clear()

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

        if self.disable_cause:
            dc.SetTextForeground("LIGHT GREY")
            font = wx.Font(56, wx.SWISS, wx.NORMAL, wx.BOLD)
            dc.SetFont(font)
            dc.DrawRotatedText(self.disable_cause, 50, 340, 45)
        else: 
            # les présences
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
        if self.curStartY < len(self.lines):
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
            self.UpdateLine(self.curStartY)

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
            if self.state:
                value = 1 << self.activity_combobox.activity.value
                clear_values = [1 << activity.value for activity in creche.activites.values() if (activity.mode & MODE_LIBERE_PLACE)]
            else:
                value = ~(1 << self.activity_combobox.activity.value)
                clear_values = [1 << activity.value for activity in creche.activites.values() if not (activity.mode & MODE_LIBERE_PLACE)]
                clear_values = ~(1 + sum(clear_values))
            
            for i in range(start, end+BASE_GRANULARITY/creche.granularite):
                if self.state:
                    if self.activity_combobox.activity.mode & MODE_LIBERE_PLACE:
                        line.values[i] = value
                    elif line.values[i] in clear_values:
                        line.values[i] = (value | 1)
                    else:
                        line.values[i] |= (value | 1)
                else:
                    if self.activity_combobox.activity.value == 0:
                        line.values[i] &= clear_values
                    else:
                        line.values[i] &= value

            if not (self.GetParent().GetParent().options & PRESENCES_ONLY) and line.get_state() == ABSENT:
                line.set_state(VACANCES)
            else:
                line.save()
                
            history.Append([Change(line, 'values', line.original_values),
                            Call(line.save)])

            self.UpdateLine(self.curStartY)
            self.state = -1
            self.GetParent().UpdateLine(self.curStartY)

class PlanningInternalPanel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, activity_combobox):
        width = (creche.affichage_max-creche.affichage_min) * 4 * COLUMN_WIDTH + LABEL_WIDTH + 27
        if not parent.options & NO_ICONS:
            width += ICONS_WIDTH
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1, size=(width, -1), style=wx.SUNKEN_BORDER)
        self.lines = []
        self.summary_panel = None
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.labels_panel = wx.Window(self, -1, size=(LABEL_WIDTH, -1))
        self.sizer.Add(self.labels_panel, 0, wx.EXPAND)
        if not parent.options & NO_ICONS:
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
            line.set_state(MALADE)
        elif state == MALADE:
            line.copy(line.reference, creche.presences_previsionnelles and (line.date > datetime.date.today()))
            line.save()
        elif line.date <= datetime.date.today() and state & PREVISIONNEL:
            line.confirm()
        else:
            line.set_state(VACANCES)

        self.grid_panel.UpdateLine(button.line)
        self.UpdateLine(button.line)

    def UpdateLine(self, index):
        if not self.GetParent().options & NO_ICONS:
            self.UpdateButton(index)
        self.GetParent().UpdateLine(index)
            
    def UpdateButton(self, index):
        state = self.lines[index].get_state()
        if state > 0:
            activities_state = state & ~(PRESENT|PREVISIONNEL)
            if activities_state:
                state &= ~activities_state
                state |= PRESENT
        self.buttons_sizer.GetItem(index).GetWindow().button.SetBitmapLabel(BUTTON_BITMAPS[state])

# self.buttons_sizer.ShowItems(1)
    def Disable(self, cause):
        self.lines = []
        self.SetScrollPos(wx.VERTICAL, 0)
        if not self.GetParent().options & NO_ICONS:
            self.buttons_sizer.Clear(True)
            self.buttons_sizer.Layout()
        self.labels_panel.SetMinSize((LABEL_WIDTH, 1))
        self.grid_panel.Disable(cause)
        self.sizer.Layout()
        self.SetupScrolling(scroll_x=False)
        self.GetParent().sizer.Layout()
        self.grid_panel.UpdateDrawing()
        self.labels_panel.Refresh()
        
    def SetLines(self, lines):
        previous_count = len(self.lines)
        self.lines = lines
        self.grid_panel.SetLines(lines)        
        count = len(self.lines)
        if count != previous_count:
            self.SetScrollPos(wx.VERTICAL, 0)
            if not self.GetParent().options & NO_ICONS:
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

        if not self.GetParent().options & NO_ICONS:
            for i in range(count):
                self.UpdateButton(i)

        self.grid_panel.UpdateDrawing()
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


class PlanningSummaryPanel(BufferedWindow):
    def __init__(self, parent):
        self.activities_count = len(creche.activites)
        self.summary = {}
        BufferedWindow.__init__(self, parent, size=(-1, 22+20*self.activities_count))

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
        self.UpdateDrawing()

    def Draw(self, dc):
        dc.BeginDrawing()
        dc.SetBackground(wx.ClientDC(self).GetBackground())
        dc.Clear()
        
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

        dc.EndDrawing()

    def DrawLine(self, dc, index, activity):
        line = self.summary[activity]
        r, g, b, t, s = getActivityColor(activity)
        try:
            dc.SetPen(wx.Pen(wx.Colour(r, g, b, wx.ALPHA_OPAQUE)))
            dc.SetBrush(wx.Brush(wx.Colour(r, g, b, t), s))
        except:
            dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
            dc.SetBrush(wx.Brush(wx.Colour(r, g, b), s))

        pos = LABEL_WIDTH
        if not self.GetParent().options & NO_ICONS:
            pos += ICONS_WIDTH
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
                    rect = wx.Rect(pos+3+(a-debut)*COLUMN_WIDTH, 2 + index * 20, (x-a)*COLUMN_WIDTH-1, 19)
                    dc.DrawRoundedRectangleRect(rect, 4)
                    dc.DrawText(str(v), pos + 4 - 4*len(str(v)) + (float(x+a)/2-debut)*COLUMN_WIDTH, 4 + index * 20)
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
                a1 = pos + 4 + (a-debut)*COLUMN_WIDTH
            dc.DrawLine(a1, 20 + index * 20, pos+(b-debut)*COLUMN_WIDTH, 20 + 20*index)
            
        
class PlanningWidget(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, activity_combobox, options=0):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, id=-1, style=wx.LB_DEFAULT)
        self.options = options
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

    def Disable(self, cause):
        self.lines = []
        self.internal_panel.Disable(cause)
        self.summary_panel.UpdateContents()
        
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
            x = 2 + LABEL_WIDTH + (heure - affichage_min) * COLUMN_WIDTH
            if not self.options & NO_ICONS:
                x += ICONS_WIDTH
            if heure % 4 == 0:
                dc.DrawLine(x, 20, x, 12)
                dc.DrawText(str(int(round(heure/4)))+"h", x - 3, 0)
            else:
                dc.DrawLine(x, 20, x, 15)
            heure += 1
        dc.EndDrawing()
