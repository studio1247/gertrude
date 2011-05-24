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
import datetime, time
from constants import *
from controls import getActivityColor
from functions import GetActivitiesSummary, GetBitmapFile
from sqlobjects import Day
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
CHECKBOX_WIDTH = 20 # px

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
        self.readonly = True

class PlanningGridWindow(BufferedWindow):
    def __init__(self, parent, activity_combobox, options):
        self.info = ""
        self.lines = []
        BufferedWindow.__init__(self, parent, size=((creche.affichage_max-creche.affichage_min) * 4 * COLUMN_WIDTH + 1, -1))
        self.SetBackgroundColour(wx.WHITE)
        self.activity_combobox = activity_combobox
        self.value, self.state = None, None
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

    def DrawLineGrid(self, dc):
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
            
    def Draw(self, dc):
        dc.BeginDrawing()
        dc.Clear()

        # le quadrillage
        self.DrawLineGrid(dc)

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
            keys = line.activites.keys()
            keys.sort(key=lambda key:key[-1])
            for start, end, activity in keys:
                r, g, b, t, s = getActivityColor(activity)
                try:
                    dc.SetPen(wx.Pen(wx.Colour(r, g, b, wx.ALPHA_OPAQUE)))
                    dc.SetBrush(wx.Brush(wx.Colour(r, g, b, t), s))
                except:
                    dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
                    dc.SetBrush(wx.Brush(wx.Colour(r, g, b), s))
                rect = wx.Rect(1+(start-int(creche.affichage_min*(60 / BASE_GRANULARITY)))*COLUMN_WIDTH, 1+index*LINE_HEIGHT, (end-start)*COLUMN_WIDTH-1, LINE_HEIGHT-1)
                dc.DrawRoundedRectangleRect(rect, 4)
        else:
            dc.SetPen(wx.Pen(wx.BLACK))
            dc.DrawText(line.info, 200, 7 + index * LINE_HEIGHT)
            
    def DrawNumbersLine(self, dc, index, line):
        if not isinstance(line, basestring):
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
            if not line.readonly:
                self.value = self.activity_combobox.activity.value
                if creche.presences_previsionnelles and line.reference and line.date > datetime.date.today():
                    self.value |= PREVISIONNEL
                for a, b, v in line.activites.keys():
                    if v == self.value and posX >= a and posX <= b:
                        self.state = -1
                        break
                else:
                    self.state = 1
                self.OnLeftButtonDragging(event)

    def OnLeftButtonDragging(self, event):
        if self.state is not None:
            posX, self.curEndY = self.__get_pos(event.GetX(), event.GetY())
            self.curEndX = (posX / (creche.granularite/BASE_GRANULARITY)) * (creche.granularite/BASE_GRANULARITY)
            start, end = min(self.curStartX, self.curEndX), max(self.curStartX, self.curEndX) + creche.granularite/BASE_GRANULARITY
            line = self.lines[self.curStartY]
            
            line_copy = Day()
            line_copy.Copy(line, False)
            if self.state > 0:
                line_copy.SetActivity(start, end, self.value)
            else:
                line_copy.ClearActivity(start, end, self.value)

            bmp = wx.EmptyBitmap((creche.affichage_max-creche.affichage_min)*(60 / BASE_GRANULARITY)*COLUMN_WIDTH+1, 3*LINE_HEIGHT)
            lineDC = wx.MemoryDC()
            lineDC.SelectObject(bmp)
            lineDC.Clear()
            self.DrawLineGrid(lineDC)
            try:
                lineGCDC = wx.GCDC(lineDC)
            except:
                lineGCDC = line2DC
            lineGCDC.BeginDrawing()
            if self.curStartY > 0:
                self.draw_line(lineGCDC, 0, self.lines[self.curStartY-1])
            self.draw_line(lineGCDC, 1, line_copy)
            if self.curStartY < len(self.lines) - 1:
                self.draw_line(lineGCDC, 2, self.lines[self.curStartY+1])
            lineGCDC.EndDrawing()
            wx.ClientDC(self).Blit(0, self.curStartY*LINE_HEIGHT, (creche.affichage_max-creche.affichage_min)*(60 / BASE_GRANULARITY)*COLUMN_WIDTH+1, LINE_HEIGHT+1, lineDC, 0, LINE_HEIGHT)

    def OnLeftButtonUp(self, event):
        if self.state is not None:
            start, end = min(self.curStartX, self.curEndX), max(self.curStartX, self.curEndX) + creche.granularite/BASE_GRANULARITY
            line = self.lines[self.curStartY]
            
            history.Append([Call(line.Restore, line.Backup())])
            
            if self.state > 0:
                line.SetActivity(start, end, self.value)
            else:
                line.ClearActivity(start, end, self.value)
            if line.insert is not None:
                line.insert[line.key] = line
                line.insert = None

            self.GetParent().UpdateLine(self.curStartY)
            self.state = None

class PlanningInternalPanel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, activity_combobox, options):
        width = (creche.affichage_max-creche.affichage_min) * (60 / BASE_GRANULARITY) * COLUMN_WIDTH + LABEL_WIDTH + 27
        if not options & NO_ICONS:
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
        self.activites_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.activites_sizers = []
        self.last_activites_observer = 0
#        for i, activite in enumerate(creche.GetActivitesSansHoraires()):
#            sizer = wx.BoxSizer(wx.VERTICAL)
#            sizer.activite = activite
#            self.activites_sizers.append(sizer)
#            sizer.SetMinSize((CHECKBOX_WIDTH, -1))
#            self.activites_sizer.Add(sizer, 0, wx.EXPAND|wx.LEFT, 5)
        self.sizer.Add(self.activites_sizer)
        self.labels_panel.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetSizer(self.sizer)
        self.SetupScrolling(scroll_x = False)

    def OnButtonPressed(self, event):
        button = event.GetEventObject()
        line = self.lines[button.line]
        if not line.readonly:
            history.Append([Call(line.Restore, line.Backup())])        
            state = line.get_state()
            if state == VACANCES:
                line.set_state(MALADE)
            elif state == MALADE:
                if line.HasPrevisionnelCloture():
                    line.RestorePrevisionnelCloture(creche.presences_previsionnelles and line.date > datetime.date.today())
                else:
                    line.Copy(line.reference, creche.presences_previsionnelles and line.date > datetime.date.today())
                    line.Save()
            elif line.date <= datetime.date.today() and state & PREVISIONNEL:
                line.Confirm()
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
        
    def OnActiviteCheckbox(self, event):
        button = event.GetEventObject()
        line = self.lines[button.line]
        if not line.readonly:
            if event.Checked():
                history.Append([])
                line.insert_activity(None, None, button.activite.value)
            else:
                history.Append([])
                line.remove_activity(None, None, button.activite.value)
            line.Save()
            if line.insert is not None:
                line.insert[line.key] = line
                line.insert = None

    def UpdateLine(self, index):
        options = self.GetParent().options
        if not options & NO_ICONS:
            self.UpdateButton(index)
        if not options & DRAW_NUMBERS:
            self.UpdateCheckboxes(index)
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
        
    def UpdateCheckboxes(self, index):
        line = self.lines[index]
        for activite_sizer in self.activites_sizers:
            checkbox = activite_sizer.GetItem(index).GetWindow()
            if isinstance(line, LigneConge):
                checkbox.Disable()
            elif not isinstance(line, basestring):
                checkbox.Enable()
                checkbox.SetValue(checkbox.activite.value in line.activites_sans_horaires)

    def SetInfo(self, info):
        self.grid_panel.SetInfo(info)
        
    def Disable(self, info):
        self.lines = []
        self.SetScrollPos(wx.VERTICAL, 0)
        if not self.GetParent().options & NO_ICONS:
            self.buttons_sizer.Clear(True)
            self.buttons_sizer.Layout()
        for activite_sizer in self.activites_sizers:
            activite_sizer.Clear(True)
            activite_sizer.Layout()
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
        count = len(self.lines)
        
        if not self.GetParent().options & DRAW_NUMBERS and (self.last_activites_observer == 0 or ('activites' in observers and observers['activites'] > self.last_activites_observer)):
            activites = creche.GetActivitesSansHoraires()
            activites_count = len(activites)
            previous_activites_count = len(self.activites_sizers)
            for i in range(previous_activites_count, activites_count, -1):
                self.activites_sizers[-1].DeleteWindows()
                del self.activites_sizers[-1]
            for i in range(previous_activites_count, activites_count):
                self.activites_sizers.append(wx.BoxSizer(wx.VERTICAL))
                self.activites_sizers[-1].SetMinSize((CHECKBOX_WIDTH, -1))
                self.activites_sizer.Add(self.activites_sizers[-1], 0, wx.EXPAND|wx.LEFT, 5)
                for i in range(previous_count):
                    checkbox = wx.CheckBox(self, -1, "", size=(CHECKBOX_WIDTH, LINE_HEIGHT))
                    self.activites_sizers[-1].Add(checkbox)
                    checkbox.line = i
                    self.Bind(wx.EVT_CHECKBOX, self.OnActiviteCheckbox, checkbox)
            for i, activite in enumerate(activites):
                sizer = self.activites_sizers[i] 
                sizer.activite = activite
                for child in sizer.GetChildren():
                    child.GetWindow().activite = activite
         
        self.grid_panel.SetLines(lines)        

        if count != previous_count:
            self.SetScrollPos(wx.VERTICAL, 0)
            
            for i in range(previous_count, count, -1):
                if not self.GetParent().options & NO_ICONS:
                    self.buttons_sizer.GetItem(i-1).DeleteWindows()
                    self.buttons_sizer.Detach(i-1)
                for sizer in self.activites_sizers:
                    sizer.GetItem(i-1).DeleteWindows()
                    sizer.Detach(i-1)
            for i in range(previous_count, count):
                if not self.GetParent().options & NO_ICONS:
                    panel = wx.Panel(self, style=wx.SUNKEN_BORDER)
                    self.buttons_sizer.Add(panel)
                    panel.button = wx.BitmapButton(panel, -1, BUTTON_BITMAPS[PRESENT], size=(26, 26), style=wx.NO_BORDER)
                    panel.button.line = i
                    self.Bind(wx.EVT_BUTTON, self.OnButtonPressed, panel.button)
                    sizer = wx.BoxSizer(wx.VERTICAL)
                    sizer.Add(panel.button)
                    panel.SetSizer(sizer)
                    # sizer.Layout()
                    # self.buttons_sizer.Layout()
                for sizer in self.activites_sizers:
                    checkbox = wx.CheckBox(self, -1, "", size=(CHECKBOX_WIDTH, LINE_HEIGHT))
                    sizer.Add(checkbox)
                    checkbox.activite = sizer.activite
                    checkbox.line = i
                    self.Bind(wx.EVT_CHECKBOX, self.OnActiviteCheckbox, checkbox)
               
            self.labels_panel.SetMinSize((LABEL_WIDTH, LINE_HEIGHT*count - 1))
            self.sizer.Layout()
            self.SetupScrolling(scroll_x=False)
            self.GetParent().sizer.Layout()
        
        options = self.GetParent().options 
        for i in range(count):
            if not options & NO_ICONS:
                self.UpdateButton(i)
            if not options & DRAW_NUMBERS:
                self.UpdateCheckboxes(i)
        
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
        self.summary = GetActivitiesSummary(creche, lines)
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
        self.Refresh()
        
    def UpdateLine(self, index):
        if self.summary_panel:
            self.summary_panel.UpdateContents()
        
    def GetSummaryLines(self):
        lines = []
        for line in self.lines:
            if not isinstance(line, LigneConge):
                lines.append(line)
        return lines

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
        
        # dessin de l'échelle
        affichage_min = int(creche.affichage_min * (60 / BASE_GRANULARITY))
        affichage_max = int(creche.affichage_max * (60 / BASE_GRANULARITY))
        if affichage_min % (creche.granularite / BASE_GRANULARITY):
            heure = affichage_min + (creche.granularite / BASE_GRANULARITY) - affichage_min % (creche.granularite / BASE_GRANULARITY)
        else:
            heure = affichage_min
        offset = 2 + LABEL_WIDTH
        if not self.options & NO_ICONS:
            offset += ICONS_WIDTH
        while heure <= affichage_max:
            x = offset + (heure - affichage_min) * COLUMN_WIDTH
            if heure % (60 / BASE_GRANULARITY) == 0:
                dc.DrawLine(x, 20, x, 12)
                dc.DrawText(str(int(round(heure/(60 / BASE_GRANULARITY))))+"h", x - 3, 0)
            else:
                dc.DrawLine(x, 20, x, 15)
            heure += creche.granularite / BASE_GRANULARITY
        dc.EndDrawing()
