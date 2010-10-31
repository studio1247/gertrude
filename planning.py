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
from functions import getActivitiesSummary, GetBitmapFile
from history import *

# PlanningWidget options
NO_ICONS = 1
READ_ONLY = 2
PRESENCES_ONLY = 4
NO_BOTTOM_LINE = 8
DRAW_NUMBERS = 16

# Elements size
LABEL_WIDTH = 105 # px
ICONS_WIDTH = 33 # px
COLUMN_WIDTH = 48 / (60 / BASE_GRANULARITY) # px
LINE_HEIGHT = 30 # px

BUTTON_BITMAPS = { ABSENT: wx.Bitmap(GetBitmapFile("icone_vacances.png"), wx.BITMAP_TYPE_PNG),
                   ABSENT+PREVISIONNEL: wx.Bitmap(GetBitmapFile("icone_vacances.png"), wx.BITMAP_TYPE_PNG),
                   PRESENT: wx.Bitmap(GetBitmapFile("icone_presence.png"), wx.BITMAP_TYPE_PNG),
                   PRESENT+PREVISIONNEL: wx.Bitmap(GetBitmapFile("icone_presence_prev.png"), wx.BITMAP_TYPE_PNG),
                   VACANCES: wx.Bitmap(GetBitmapFile("icone_vacances.png"), wx.BITMAP_TYPE_PNG),
                   MALADE: wx.Bitmap(GetBitmapFile("icone_maladie.png"), wx.BITMAP_TYPE_PNG),
                   }

class LigneConge(object):
    def __init__(self, info):
        self.info = info

class PlanningGridWindow(BufferedWindow):
    def __init__(self, parent, activity_combobox, options):
        self.info = ""
        self.lines = []
        BufferedWindow.__init__(self, parent, size=((creche.affichage_max-creche.affichage_min) * 4 * COLUMN_WIDTH + 1, -1))
        self.SetBackgroundColour(wx.WHITE)
        self.activity_combobox = activity_combobox
        self.state = -1
        if options & DRAW_NUMBERS:
            self.draw_line = self.DrawNumbersLine
        else:
            self.draw_line = self.DrawActivitiesLine
        if not options & READ_ONLY:
            self.SetCursor(wx.StockCursor(wx.CURSOR_PENCIL))        
            self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftButtonDown)
            self.Bind(wx.EVT_LEFT_UP, self.OnLeftButtonUp)
            self.Bind(wx.EVT_MOTION, self.OnLeftButtonDragging)

    def SetInfo(self, info):
        self.info = info
        
    def Disable(self, info):
        self.SetInfo(info)
        self.lines = []
        self.SetMinSize((int((creche.affichage_max-creche.affichage_min) * (60 / BASE_GRANULARITY) * COLUMN_WIDTH + 1), 400))
        
    def SetLines(self, lines):
        self.lines = lines
        self.SetMinSize((int((creche.affichage_max-creche.affichage_min) * (60 / BASE_GRANULARITY) * COLUMN_WIDTH + 1), LINE_HEIGHT * len(self.lines) - 1))
       
    def UpdateLine(self, index):
        self.UpdateDrawing()

    def Draw(self, dc):
        dc.BeginDrawing()
        dc.Clear()

        # le quadrillage
        dc.SetPen(wx.GREY_PEN)
        dc.SetBrush(wx.WHITE_BRUSH)
        affichage_min = int(creche.affichage_min * 60 / BASE_GRANULARITY)
        affichage_max = int(creche.affichage_max * 60 / BASE_GRANULARITY)
        if affichage_min % (creche.granularite / BASE_GRANULARITY):
            heure = affichage_min + (creche.granularite / BASE_GRANULARITY) - affichage_min % (creche.granularite / BASE_GRANULARITY)
        else:
            heure = affichage_min
        height = dc.GetSize()[1]
        while heure <= affichage_max:
            x = (heure - affichage_min) * COLUMN_WIDTH
            if heure % (60 / BASE_GRANULARITY) == 0:
                dc.SetPen(wx.GREY_PEN)
            else:
                dc.SetPen(wx.LIGHT_GREY_PEN)
            dc.DrawLine(x, 0,  x, height)
            heure += creche.granularite / BASE_GRANULARITY

        if self.info:
            dc.SetTextForeground("LIGHT GREY")
            font = wx.Font(56, wx.SWISS, wx.NORMAL, wx.BOLD)
            dc.SetFont(font)
            dc.DrawRotatedText(self.info, 50, 340, 45)
        
        # les présences
        try:
            dc = wx.GCDC(dc)
        except:
            pass

        for i, line in enumerate(self.lines):
            self.draw_line(dc, i, line)
        
        dc.EndDrawing()

    def DrawActivitiesLine(self, dc, index, line):
        if not isinstance(line, LigneConge):
            for start, end, activity in line.get_activities(reference=line.reference):
                r, g, b, t, s = getActivityColor(activity)
                try:
                  dc.SetPen(wx.Pen(wx.Colour(r, g, b, wx.ALPHA_OPAQUE)))
                  dc.SetBrush(wx.Brush(wx.Colour(r, g, b, t), s))
                except:
                  dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
                  dc.SetBrush(wx.Brush(wx.Colour(r, g, b), s))
                rect = wx.Rect(1+(start-int(creche.affichage_min*(60 / BASE_GRANULARITY)))*COLUMN_WIDTH, 1 + index*LINE_HEIGHT, (end-start)*COLUMN_WIDTH-1, LINE_HEIGHT-1)
                dc.DrawRoundedRectangleRect(rect, 4)
        else:
            dc.SetPen(wx.Pen(wx.BLACK))
            dc.DrawText(line.info, 200, 7 + index * LINE_HEIGHT)
            
    def DrawNumbersLine(self, dc, index, line):
        if not isinstance(line, basestring):
            line = line.values    
            pos = -2
            if not self.GetParent().GetParent().options & NO_ICONS:
                pos += ICONS_WIDTH
            debut = int(creche.affichage_min * (60 / BASE_GRANULARITY))
            fin = int(creche.affichage_max * (60 / BASE_GRANULARITY))
            x = debut
            v = 0
            a = 0
            while x <= fin:
                if x == fin:
                    nv = 0
                else:
                    nv = line[x]
                if nv != v:
                    if v != 0:
                        rect = wx.Rect(pos+3+(a-debut)*COLUMN_WIDTH, 2 + index * LINE_HEIGHT, (x-a)*COLUMN_WIDTH-1, LINE_HEIGHT-1)
                        if v > 5:
                            r, g, b, t, s = 5, 203, 28, 150, wx.SOLID
                        elif v > 0:
                            r, g, b, t, s = 5, 203, 28, 30*v, wx.SOLID
                        else:
                            r, g, b, t, s = 190, 35, 29, 50, wx.SOLID
                        try:
                            dc.SetPen(wx.Pen(wx.Colour(r, g, b, wx.ALPHA_OPAQUE)))
                            dc.SetBrush(wx.Brush(wx.Colour(r, g, b, t), s))
                        except:
                            dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
                            dc.SetBrush(wx.Brush(wx.Colour(r, g, b), s))
                        dc.DrawRoundedRectangleRect(rect, 4)
                        dc.DrawText(str(v), pos + 4 - 4*len(str(v)) + (float(x+a)/2-debut)*COLUMN_WIDTH, 7 + index * LINE_HEIGHT)
                    a = x    
                    v = nv
                x += 1
        
    def __get_pos(self, x, y):
        l = int(creche.affichage_min * (60 / BASE_GRANULARITY) + (x / COLUMN_WIDTH))
        c = int(y / LINE_HEIGHT)
        return l, c

    def OnLeftButtonDown(self, event):
        posX, self.curStartY = self.__get_pos(event.GetX(), event.GetY())
        self.curStartX = (posX / (creche.granularite/BASE_GRANULARITY)) * (creche.granularite/BASE_GRANULARITY)
        if self.curStartY < len(self.lines):
            line = self.lines[self.curStartY]
            if not isinstance(line, LigneConge):
                line.original_values = line.values[:]
                if line.get_state() < 0 or not line.values[posX] & (1<<self.activity_combobox.activity.value):
                    self.state = 1
                else:
                    self.state = 0
                self.OnLeftButtonDragging(event)

    def OnLeftButtonDragging(self, event):
        if self.state != -1:
            posX, self.curEndY = self.__get_pos(event.GetX(), event.GetY())
            self.curEndX = (posX / (creche.granularite/BASE_GRANULARITY)) * (creche.granularite/BASE_GRANULARITY)
            start, end = min(self.curStartX, self.curEndX), max(self.curStartX, self.curEndX)
            line = self.lines[self.curStartY]
            line.values = line.original_values[:]
            
            for i in range(start, end + creche.granularite/BASE_GRANULARITY):
                if line.values[i] < 0:
                    line.values[i] = 0
                if creche.presences_previsionnelles and line.reference and line.date > datetime.date.today():
                    line.values[i] |= PREVISIONNEL
                else:
                    line.values[i] &= ~PREVISIONNEL
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
                line.values = [0] * 24 * (60 / BASE_GRANULARITY)
            if self.state:
                value = 1 << self.activity_combobox.activity.value
                clear_values = [1 << activity.value for activity in creche.activites.values() if (activity.mode & MODE_LIBERE_PLACE)]
            else:
                value = ~(1 << self.activity_combobox.activity.value)
                clear_values = [1 << activity.value for activity in creche.activites.values() if not (activity.mode & MODE_LIBERE_PLACE)]
                clear_values = ~sum(clear_values)
            
            for i in range(start, end + creche.granularite/BASE_GRANULARITY):
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
                if creche.presences_previsionnelles and line.reference and line.date > datetime.date.today():
                    line.values[i] |= PREVISIONNEL
                else:
                    line.values[i] &= ~PREVISIONNEL

            if not (self.GetParent().GetParent().options & PRESENCES_ONLY) and line.get_state() == ABSENT and line.reference.get_state() != ABSENT:
                line.set_state(VACANCES)
            else:
                line.save()

            if line.insert is not None:
                line.insert[line.key] = line
                line.insert = None

            history.Append([Change(line, 'values', line.original_values),
                            Call(line.save)])

            self.UpdateLine(self.curStartY)
            self.state = -1
            self.GetParent().UpdateLine(self.curStartY)

class PlanningInternalPanel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, activity_combobox, options):
        width = (creche.affichage_max-creche.affichage_min) * (60 / BASE_GRANULARITY) * COLUMN_WIDTH + LABEL_WIDTH + 27
        if not parent.options & NO_ICONS:
            width += ICONS_WIDTH
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1, size=(width, -1), style=wx.SUNKEN_BORDER)
        self.lines = []
        self.summary_panel = None
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.labels_panel = wx.Window(self, -1, size=(LABEL_WIDTH, -1))
        self.sizer.Add(self.labels_panel, 0, wx.EXPAND)
        if not options & NO_ICONS:
            self.buttons_sizer = wx.BoxSizer(wx.VERTICAL)
            self.buttons_sizer.SetMinSize((ICONS_WIDTH-2, -1))
            self.sizer.Add(self.buttons_sizer, 0, wx.EXPAND|wx.RIGHT, 2)
        self.grid_panel = PlanningGridWindow(self, activity_combobox, options)
        self.sizer.Add(self.grid_panel, 0, wx.EXPAND)
        self.labels_panel.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetSizer(self.sizer)
        self.SetupScrolling(scroll_x = False)

    def OnButtonPressed(self, event):
        button = event.GetEventObject()
        line = self.lines[button.line]
        if isinstance(line, LigneConge):
            return
        
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
            if line.reference.get_state() == ABSENT:
                line.set_state(MALADE)
            else:
                line.set_state(VACANCES)

        if line.insert is not None:
            line.insert[line.key] = line
            line.insert = None

        self.grid_panel.UpdateLine(button.line)
        self.UpdateLine(button.line)

    def UpdateLine(self, index):
        if not self.GetParent().options & NO_ICONS:
            self.UpdateButton(index)
        self.GetParent().UpdateLine(index)
            
    def UpdateButton(self, index):
        line = self.lines[index]
        if isinstance(line, LigneConge):
            state = VACANCES
        else:
            state = line.get_state()
            if state > 0:
                activities_state = state & ~(PRESENT|PREVISIONNEL)
                if activities_state:
                    state &= ~activities_state
                    state |= PRESENT
        self.buttons_sizer.GetItem(index).GetWindow().button.SetBitmapLabel(BUTTON_BITMAPS[state])

    def SetInfo(self, info):
        self.grid_panel.SetInfo(info)
        
    def Disable(self, info):
        self.lines = []
        self.SetScrollPos(wx.VERTICAL, 0)
        if not self.GetParent().options & NO_ICONS:
            self.buttons_sizer.Clear(True)
            self.buttons_sizer.Layout()
        self.labels_panel.SetMinSize((LABEL_WIDTH, 1))
        self.grid_panel.Disable(info)
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
        self.Layout()
            
    def OnPaint(self, event):
        dc = wx.PaintDC(self.labels_panel)
        self.labels_panel.PrepareDC(dc)
        dc.BeginDrawing()
        dc.SetTextForeground("BLACK")
        font = wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL)
        dc.SetFont(font)
        for i, line in enumerate(self.lines):
            if isinstance(line, basestring):
                rect = wx.Rect(0, 5 + i * LINE_HEIGHT, 75, LINE_HEIGHT-8)
                try:
                    dc.SetPen(wx.Pen(wx.Colour(0, 0, 0, wx.ALPHA_OPAQUE)))
                    dc.SetBrush(wx.Brush(wx.Colour(128, 128, 128, 128), wx.SOLID))
                except:
                    dc.SetPen(wx.Pen(wx.Colour(0, 0, 0)))
                    dc.SetBrush(wx.Brush(wx.Colour(128, 128, 128), wx.SOLID))
                dc.DrawRoundedRectangleRect(rect, 4)
                dc.DrawText(line, 5, 8 + i * LINE_HEIGHT)
            else:
                dc.DrawText(line.label, 5, 6 + LINE_HEIGHT*i)
        dc.EndDrawing()


class PlanningSummaryPanel(BufferedWindow):
    def __init__(self, parent):
        self.activities_count = len(creche.activites)
        self.summary = {}
        BufferedWindow.__init__(self, parent, size=(-1, 2+20*self.activities_count))

    def UpdateContents(self):
        if self.activities_count != len(creche.activites):
            self.activities_count = len(creche.activites)
            self.SetMinSize((-1, 2+20*self.activities_count))
            self.GetParent().sizer.Layout()
            
        lines = self.GetParent().GetSummaryLines()
        self.summary = getActivitiesSummary(creche, lines)
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
            dc.DrawText(self.summary[activity].label, 5, 6 + i * 20)
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
        debut = int(creche.affichage_min * (60 / BASE_GRANULARITY))
        fin = int(creche.affichage_max * (60 / BASE_GRANULARITY))
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
    def __init__(self, parent, activity_combobox=None, options=0):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, id=-1, style=wx.LB_DEFAULT)
        self.options = options
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.scale_window = wx.Window(self, -1, size=(-1, 25))
        self.sizer.Add(self.scale_window, 0, wx.EXPAND)
        self.internal_panel = PlanningInternalPanel(self, activity_combobox, options)
        self.sizer.Add(self.internal_panel, 1, wx.EXPAND)
        if not (options & NO_BOTTOM_LINE):
            self.summary_panel = PlanningSummaryPanel(self)
            self.sizer.Add(self.summary_panel, 0, wx.EXPAND)
        else:
            self.summary_panel = None
        self.SetSizer(self.sizer)
        self.SetupScrolling(scroll_y = False)
        self.sizer.Layout()
        self.scale_window.Bind(wx.EVT_PAINT, self.OnPaint)

    def SetInfo(self, info):
        self.internal_panel.SetInfo(info)
        
    def Disable(self, info):
        self.lines = []
        self.internal_panel.Disable(info)
        if self.summary_panel:
            self.summary_panel.UpdateContents()
        
    def SetLines(self, lines):
        self.lines = lines
        self.internal_panel.SetLines(lines)
        if self.summary_panel:
            self.summary_panel.UpdateContents()
        
    def UpdateLine(self, index):
        if self.summary_panel:
            self.summary_panel.UpdateContents()
        
    def GetSummaryLines(self):
        values = []
        for line in self.lines:
            if not isinstance(line, LigneConge):
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
        
        affichage_min = int(creche.affichage_min * (60 / BASE_GRANULARITY))
        affichage_max = int(creche.affichage_max * (60 / BASE_GRANULARITY))
        if affichage_min % (creche.granularite / BASE_GRANULARITY):
            heure = affichage_min + (creche.granularite / BASE_GRANULARITY) - affichage_min % (creche.granularite / BASE_GRANULARITY)
        else:
            heure = affichage_min
        while heure <= affichage_max:
            x = 2 + LABEL_WIDTH + (heure - affichage_min) * COLUMN_WIDTH
            if not self.options & NO_ICONS:
                x += ICONS_WIDTH
            if heure % (60 / BASE_GRANULARITY) == 0:
                dc.DrawLine(x, 20, x, 12)
                dc.DrawText(str(int(round(heure/(60 / BASE_GRANULARITY))))+"h", x - 3, 0)
            else:
                dc.DrawLine(x, 20, x, 15)
            heure += creche.granularite / BASE_GRANULARITY
        dc.EndDrawing()
