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

import wx, wx.lib.scrolledpanel
from buffered_window import BufferedWindow
import datetime, time
from constants import *
from controls import GetActivityColor, TextDialog
from functions import GetActivitiesSummary, GetBitmapFile, GetHeureString, GetPlanningStates
from sqlobjects import Day, JourneeCapacite
from globals import *

# PlanningWidget options
NO_ICONS = 1
READ_ONLY = 2
PRESENCES_ONLY = 4
NO_BOTTOM_LINE = 8
DRAW_NUMBERS = 16
COMMENTS = 32
TWO_PARTS = 64
ACTIVITES = 128
NO_LABELS = 256
DRAW_VALUES = 512
DEPASSEMENT_CAPACITE = 1024
NO_SCROLL = 2048

# Elements size
LABEL_WIDTH = 130  # px
ICONS_WIDTH = 50  # px
LINE_HEIGHT = 32 # px
CHECKBOX_WIDTH = 25  # px
COMMENT_BUTTON_WIDTH = 31  # px
RECAP_WIDTH = 100  # px

BUTTON_BITMAPS = { ABSENT: (wx.Bitmap(GetBitmapFile("icone_vacances.png"), wx.BITMAP_TYPE_PNG), u'Absent'),
                   ABSENT+PREVISIONNEL: (wx.Bitmap(GetBitmapFile("icone_vacances.png"), wx.BITMAP_TYPE_PNG), u'Congés'),
                   PRESENT: (wx.Bitmap(GetBitmapFile("icone_presence.png"), wx.BITMAP_TYPE_PNG), u'Présent'),
                   PRESENT+PREVISIONNEL: (wx.Bitmap(GetBitmapFile("icone_presence_prev.png"), wx.BITMAP_TYPE_PNG), u'Présent'),
                   VACANCES: (wx.Bitmap(GetBitmapFile("icone_vacances.png"), wx.BITMAP_TYPE_PNG), u'Congés'),
                   CONGES_PAYES: (wx.Bitmap(GetBitmapFile("icone_conges_payes.png"), wx.BITMAP_TYPE_PNG), u'Congés payés'),
                   MALADE: (wx.Bitmap(GetBitmapFile("icone_maladie.png"), wx.BITMAP_TYPE_PNG), u'Malade'),
                   HOPITAL: (wx.Bitmap(GetBitmapFile("icone_hopital.png"), wx.BITMAP_TYPE_PNG), u'Maladie avec hospitalisation'),
                   MALADE_SANS_JUSTIFICATIF: (wx.Bitmap(GetBitmapFile("icone_maladie_sans_justificatif.png"), wx.BITMAP_TYPE_PNG), u'Maladie sans justificatif'),
                   ABSENCE_NON_PREVENUE: (wx.Bitmap(GetBitmapFile("icone_absence_non_prevenue.png"), wx.BITMAP_TYPE_PNG), u'Absence non prévenue'),
                   ABSENCE_CONGE_SANS_PREAVIS: (wx.Bitmap(GetBitmapFile("icone_absence_sans_preavis.png"), wx.BITMAP_TYPE_PNG), u'Congés sans préavis'),
                   CONGES_DEPASSEMENT: (wx.Bitmap(GetBitmapFile("icone_conges_depassement.png"), wx.BITMAP_TYPE_PNG), u'Absence non déductible (dépassement)'),
                   }

BULLE_BITMAP = wx.Bitmap(GetBitmapFile("bulle.png"))


def GetPlanningWidth():
    return (creche.affichage_max - creche.affichage_min) * (60 / BASE_GRANULARITY) * config.column_width


class LigneConge(object):
    def __init__(self, state, info):
        self.state = state
        self.info = info
        self.readonly = True
        self.reference = None
        self.options = 0
    
    def GetNombreHeures(self):
        return 0.0

    def GetDynamicText(self):
        return None

    def GetStateIcon(self):
        return self.state


class PlanningLineGrid(BufferedWindow):
    def __init__(self, parent, line, pos):
        self.parent = parent
        self.line = line
        self.temp_line = None
        self.options = parent.parent.options
        self.check_line = parent.parent.check_line
        self.activity_combobox = parent.parent.activity_combobox
        self.value, self.state = None, None
        if self.options & DRAW_NUMBERS:
            self.draw_line = self.DrawNumbersLine
        else:
            self.draw_line = self.DrawActivitiesLine
        self.width = GetPlanningWidth() + 1
        BufferedWindow.__init__(self, parent, pos=pos, size=(self.width, LINE_HEIGHT))
        self.SetBackgroundColour(wx.WHITE)
        if not (self.options & READ_ONLY or readonly):
            self.SetCursor(wx.StockCursor(wx.CURSOR_PENCIL))        
            self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftButtonDown)
            self.Bind(wx.EVT_LEFT_UP, self.OnLeftButtonUp)
            self.Bind(wx.EVT_MOTION, self.OnLeftButtonDragging)

    def SetLine(self, line):
        self.line = line
        self.UpdateDrawing()
            
    def UpdateContents(self):
        self.UpdateDrawing()

    def DrawLineGrid(self, dc):
        dc.SetPen(wx.WHITE_PEN)
        dc.SetBrush(wx.WHITE_BRUSH)
        
        affichage_min = int(creche.affichage_min * 60 / BASE_GRANULARITY)
        affichage_max = int(creche.affichage_max * 60 / BASE_GRANULARITY)
        
        if affichage_min % (creche.granularite / BASE_GRANULARITY):
            heure = affichage_min + (creche.granularite / BASE_GRANULARITY) - affichage_min % (creche.granularite / BASE_GRANULARITY)
        else:
            heure = affichage_min
        
        while heure <= affichage_max:
            x = (heure - affichage_min) * config.column_width
            if heure % (60 / BASE_GRANULARITY) == 0:
                dc.SetPen(wx.GREY_PEN)
            else:
                dc.SetPen(wx.LIGHT_GREY_PEN)
            dc.DrawLine(x, 0, x, LINE_HEIGHT)
            heure += creche.granularite / BASE_GRANULARITY
        
        if self.parent.parent.plages_fermeture or self.parent.parent.plages_insecables:
            dc.SetPen(wx.LIGHT_GREY_PEN)
            dc.SetBrush(wx.LIGHT_GREY_BRUSH)
            for debut, fin in self.parent.parent.plages_fermeture:
                dc.DrawRectangle(1 + (debut - affichage_min) * config.column_width, 0, (fin - debut) * config.column_width - 1, LINE_HEIGHT)
            dc.SetPen(wx.TRANSPARENT_PEN)            
            dc.SetBrush(wx.Brush(wx.Colour(250, 250, 0, 100)))
            for debut, fin in self.parent.parent.plages_insecables:
                dc.DrawRectangle(1 + (debut - affichage_min) * config.column_width, 0, (fin - debut) * config.column_width - 1, LINE_HEIGHT)
            
    def Draw(self, dc):
        dc.BeginDrawing()
        dc.SetBackground(wx.Brush(wx.WHITE))
        dc.Clear()

        try:
            dc = wx.GCDC(dc)
        except:
            pass

        # le quadrillage
        if self.line is not None and not isinstance(self.line, basestring):
            self.DrawLineGrid(dc)
        
        # les présences
        if self.temp_line:
            line = self.temp_line
        else:
            line = self.line            
        self.draw_line(dc, line)

        dc.EndDrawing()

    def DrawActivitiesLine(self, dc, line):
        if isinstance(line, LigneConge):
            dc.SetPen(wx.BLACK_PEN)
            dc.DrawText(line.info, 100, 7)
        elif not isinstance(line, basestring):
            keys = line.activites.keys()
            # Affichage du contrat de référence en arrière plan
            if line.reference:
                for start, end, value in line.reference.activites:
                    if value == 0:
                        r, g, b, t, s = GetActivityColor(value|PREVISIONNEL)
                        try:
                            dc.SetPen(wx.Pen(wx.Colour(r, g, b, wx.ALPHA_OPAQUE)))
                            dc.SetBrush(wx.Brush(wx.Colour(r, g, b, t), s))
                        except:
                            dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
                            dc.SetBrush(wx.Brush(wx.Colour(r, g, b), s))
                        rect = wx.Rect(1 + (start - int(creche.affichage_min*(60 / BASE_GRANULARITY))) * config.column_width, 0, (end-start) * config.column_width - 1, LINE_HEIGHT/3)
                        dc.DrawRectangleRect(rect)
                
            for start, end, activity in keys[:]:
                if activity == 0 and line.reference:
                    keys.remove((start, end, activity))
                    splitted = [(start, end, activity)]
                    i = 0
                    while i < len(splitted):
                        start, end, activity = splitted[i]
                        for s, e, v in line.reference.activites:
                            if v == 0:
                                a = max(s, start)
                                b = min(e, end)
                                if a < b:
                                    splitted.pop(i)
                                    keys.append((a, b, activity))
                                    if start < a:
                                        splitted.append((start, a, activity))
                                    if end > b:
                                        splitted.append((b, end, activity))
                                    break
                        else:
                            i += 1
                    for start, end, activity in splitted:
                        keys.append((start, end, activity|SUPPLEMENT))                                
            keys.sort(key=lambda key:key[-1]&(~SUPPLEMENT))
            for start, end, val in keys:
                activity = val
                if self.options & DRAW_VALUES:
                    activity = 0
                r, g, b, t, s = GetActivityColor(activity)
                try:
                    dc.SetPen(wx.Pen(wx.Colour(r, g, b, wx.ALPHA_OPAQUE)))
                    dc.SetBrush(wx.Brush(wx.Colour(r, g, b, t), s))
                except:
                    dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
                    dc.SetBrush(wx.Brush(wx.Colour(r, g, b), s))
                rect = wx.Rect(1+(start-int(creche.affichage_min*(60 / BASE_GRANULARITY)))*config.column_width, 0, (end-start)*config.column_width-1, LINE_HEIGHT-1)
                dc.DrawRoundedRectangleRect(rect, 3)
                if self.options & DRAW_VALUES and val != 0:
                    dc.DrawText(str(val), rect.GetX() + rect.GetWidth()/2 - 4*len(str(val)), 7)
            # Commentaire sur la ligne
            if self.options & COMMENTS:
                dc.SetPen(wx.BLACK_PEN)
                dc.DrawText(line.commentaire, 50, 7)
            
    def DrawNumbersLine(self, dc, line):
        if not isinstance(line, basestring):
            pos = -2
            if not self.options & NO_ICONS:
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
                    nv = line[x][0]
                if nv != v:
                    if v != 0:
                        rect = wx.Rect(pos+3+(a-debut)*config.column_width, 0, (x-a)*config.column_width-1, LINE_HEIGHT-1)
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
                        dc.DrawRoundedRectangleRect(rect, 3)
                        s = str(int(v))
                        dc.DrawText(s, pos + 4 - 4*len(s) + (float(x+a)/2-debut)*config.column_width, 7)
                    a = x    
                    if nv:
                        v = nv
                    else:
                        v = 0
                x += 1
        
    def __get_pos(self, x):
        if x > 0:
            x -= 1
        l = int(creche.affichage_min * (60 / BASE_GRANULARITY) + (x / config.column_width))               
        return l

    def OnLeftButtonDown(self, event):
        posX = self.__get_pos(event.GetX())
        self.curStartX = (posX / (creche.granularite/BASE_GRANULARITY)) * (creche.granularite/BASE_GRANULARITY)
        if not (isinstance(self.line, basestring) or self.line is None or self.line.readonly or readonly):
            if self.activity_combobox:
                self.value = self.activity_combobox.activity.value
            else:
                self.value = 0
            if creche.presences_previsionnelles and self.line.reference and self.line.date > datetime.date.today():
                self.value |= PREVISIONNEL
            for a, b, v in self.line.activites.keys():
                if (self.line.exclusive or v == self.value) and a <= posX <= b:
                    self.state = -1
                    break
            else:
                self.state = 1
            self.OnLeftButtonDragging(event)

    def GetPlagesSelectionnees(self):
        start, end = min(self.curStartX, self.curEndX), max(self.curStartX, self.curEndX) + creche.granularite/BASE_GRANULARITY
        
        affichage_min = int(creche.affichage_min * (60 / BASE_GRANULARITY))
        affichage_max = int(creche.affichage_max * (60 / BASE_GRANULARITY))
        if start < affichage_min:
            start = affichage_min
        if end > affichage_max:
            end = affichage_max
        
        for debut, fin in self.parent.parent.plages_insecables:
            if (debut <= start < fin) or (debut < end < fin) or (start <= debut and end > fin):
                if debut < start:
                    start = debut
                if fin > end:
                    end = fin

        result = [(start, end)]        
        for start, end in self.parent.parent.plages_fermeture:
            for i, (debut, fin) in enumerate(result):
                if debut >= start and fin <= end:
                    del result[i]
                elif start > debut and end < fin:
                    result[i] = (debut, start)
                    result.insert(i+1, (end, fin))
                    break
                elif debut <= start <= fin <= end:
                    result[i] = (debut, start)
                elif start <= debut <= end <= fin:
                    result[i] = (end, fin)
        
        return result

    def OnLeftButtonDragging(self, event):
        if self.state is not None:
            posX = self.__get_pos(event.GetX())
            self.curEndX = (posX / (creche.granularite/BASE_GRANULARITY)) * (creche.granularite/BASE_GRANULARITY)
            
            line_copy = Day()
            line_copy.Copy(self.line, False)

            for start, end in self.GetPlagesSelectionnees():                        
                if self.state > 0:
                    line_copy.SetActivity(start, end, self.value)
                else:
                    line_copy.ClearActivity(start, end, self.value)
            
            self.temp_line = line_copy
            self.UpdateDrawing()

    def OnLeftButtonUp(self, _):
        self.temp_line = None
        if self.state is not None:
            line = self.line
            
            history.Append([Call(line.Restore, line.Backup())])
            
            if self.state > 0:
                if not self.activity_combobox:
                    dlg = TextDialog(self, u"Capacité", "10")
                    response = dlg.ShowModal()
                    dlg.Destroy()
                    try:
                        self.value = int(dlg.GetText())
                    except:
                        pass
                    if response != wx.ID_OK or self.value == 0:
                        self.parent.UpdateContents()
                        self.state = None
                        self.UpdateDrawing()
                        return
                for start, end in self.GetPlagesSelectionnees():                        
                    line.SetActivity(start, end, self.value)
            else:
                for start, end in self.GetPlagesSelectionnees():                        
                    line.ClearActivity(start, end, self.value)
                
            if not (self.options & PRESENCES_ONLY) and len(line.activites) == 0 and line.reference and len(line.reference.activites) > 0:
                line.SetState(VACANCES)
                
            if line.insert is not None:
                line.insert[line.key] = line
                line.insert = None
            
            if self.options & DEPASSEMENT_CAPACITE and self.state > 0 and self.value == 0 and creche.alerte_depassement_planning and self.check_line:
                self.check_line(line, self.GetPlagesSelectionnees())
            
            self.parent.OnLineChanged()
                    
            self.state = None


class PlanningLineLabel(wx.Panel):
    def __init__(self, parent, line, pos):
        wx.Panel.__init__(self, parent, -1, pos=pos, size=(LABEL_WIDTH, LINE_HEIGHT-1), style=wx.NO_BORDER)
        self.line = line
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        
    def SetLine(self, line):
        self.line = line
    
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.BeginDrawing()
        dc.SetTextForeground("BLACK")
        categoryfont = wx.Font(10, wx.SWISS, wx.BOLD, wx.BOLD)
        labelfont = wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL)
        sublabelfont = wx.Font(6, wx.SWISS, wx.NORMAL, wx.NORMAL)
        dc.SetFont(labelfont)
        
        if isinstance(self.line, basestring):
            rect = wx.Rect(2, 4, 125, LINE_HEIGHT - 8)
            try:
                dc.SetPen(wx.Pen(wx.Colour(0, 0, 0, wx.ALPHA_OPAQUE)))
                dc.SetBrush(wx.Brush(wx.Colour(128, 128, 128, 128), wx.SOLID))
            except:
                dc.SetPen(wx.Pen(wx.Colour(0, 0, 0)))
                dc.SetBrush(wx.Brush(wx.Colour(128, 128, 128), wx.SOLID))
            dc.DrawRectangleRect(rect)
            dc.SetFont(categoryfont)
            dc.DrawText(self.line, 5, 8)
            dc.SetFont(labelfont)
        else:
            if self.line.sublabel:
                dc.DrawText(self.line.label, 5, 4)
                dc.SetFont(sublabelfont)
                dc.DrawText(self.line.sublabel, 5, 16)
                dc.SetFont(labelfont)
            else:
                dc.DrawText(self.line.label, 5, 6)

        dc.EndDrawing()


class PlanningLineStatusIcon(wx.Window):
    def __init__(self, parent, line, pos):
        wx.Window.__init__(self, parent, -1, pos=pos, size=(ICONS_WIDTH, LINE_HEIGHT-1))
        self.SetBackgroundColour(wx.WHITE)
        self.button = wx.BitmapButton(self, -1, BUTTON_BITMAPS[PRESENT][0], size=(ICONS_WIDTH, LINE_HEIGHT-1), style=wx.NO_BORDER)
        self.button.SetBackgroundColour(wx.WHITE)
        self.Bind(wx.EVT_BUTTON, self.OnButtonPressed, self.button)
        self.parent = parent
        self.SetLine(line)
        
    def SetLine(self, line):
        self.line = line
        if isinstance(line, basestring):
            self.button.Hide()
        else:
            if isinstance(line, LigneConge):
                state = line.state
            else:
                state = line.GetStateIcon()
            bitmap, tooltip = BUTTON_BITMAPS[state]
            self.button.SetBitmapLabel(bitmap)
            self.button.SetToolTip(wx.ToolTip(tooltip))
            self.button.Show(True)
            
    def OnButtonPressed(self, _):
        if not (self.line.readonly or readonly):
            history.Append([Call(self.line.Restore, self.line.Backup())])        
            state = self.line.GetState()
            
            if state < 0:
                states = GetPlanningStates()
                index = states.index(state)
                newstate = states[(index + 1) % len(states)]
                if newstate == PRESENT:
                    if self.line.HasPrevisionnelCloture():
                        self.line.RestorePrevisionnelCloture(creche.presences_previsionnelles and self.line.date > datetime.date.today())
                    else:
                        reference = self.line.reference
                        self.line.Copy(reference, creche.presences_previsionnelles and self.line.date > datetime.date.today())
                        self.line.Save()
                        self.line.reference = reference
                else:
                    self.line.SetState(newstate)
            elif self.line.date <= datetime.date.today() and state & PREVISIONNEL:
                self.line.Confirm()
            else:
                if self.line.reference.GetState() == ABSENT:
                    self.line.SetState(MALADE)
                else:
                    self.line.SetState(VACANCES)
    
            if self.line.insert is not None:
                self.line.insert[self.line.key] = self.line
                self.line.insert = None
    
            self.parent.OnLineChanged()


class PlanningLineComment(wx.StaticText):
    def __init__(self, parent, line, pos):
        wx.StaticText.__init__(self, parent, -1, pos=pos, style=wx.NO_BORDER)
        self.SetLine(line)
        
    def SetLine(self, line):
        if isinstance(line, basestring) or not line.GetDynamicText:
            text = None
        else:
            text = line.GetDynamicText(line)
        if text:
            self.SetWindowStyle(wx.BORDER)
            self.SetLabel(line.GetDynamicText(line))
        else:
            self.SetWindowStyle(wx.NO_BORDER)
            self.SetLabel("")


class PlanningLine(wx.Window):
    def __init__(self, parent, line, pos, size):
        wx.Window.__init__(self, parent, pos=pos, size=size)
        self.SetBackgroundColour(wx.WHITE)
        self.parent = parent
        self.line = line
        self.width, self.height = size
        self.label_panel = None
        self.status_icon = None
        self.bulle_button = None
        self.Create()
    
    def Create(self):
        self.width = 0
        if not self.parent.options & NO_LABELS:
            self.label_panel = PlanningLineLabel(self, self.line, pos=(0, 0))
            self.width += LABEL_WIDTH
        if not self.parent.options & NO_ICONS:
            self.status_icon = PlanningLineStatusIcon(self, self.line, pos=(self.width, 0))
            self.width += ICONS_WIDTH
        self.grid = PlanningLineGrid(self, self.line, (self.width, 0))
        self.planning_width = GetPlanningWidth()
        self.width += self.planning_width + 5
        if self.parent.options & ACTIVITES:
            self.CreateActivitesCheckboxes()
        if self.parent.options & COMMENTS:
            self.bulle_button = wx.BitmapButton(self, -1, BULLE_BITMAP, pos=(self.width + 5, 7), style=wx.NO_BORDER)
            self.Bind(wx.EVT_BUTTON, self.OnCommentButtonPressed, self.bulle_button)
            self.width += COMMENT_BUTTON_WIDTH
            self.UpdateBulle()
        self.comment_panel = PlanningLineComment(self, self.line, pos=(self.width, 7))
        self.width += RECAP_WIDTH
        self.SetSize((max(self.width, self.parent.GetSize()[0]), self.height))
        
    def CreateActivitesCheckboxes(self):
        self.activites_checkboxes = []
        for activite in self.parent.activites: 
            checkbox = wx.CheckBox(self, -1, "", pos=(self.width+5, 0), size=(CHECKBOX_WIDTH-5, LINE_HEIGHT-1))
            checkbox.Enable(not readonly)
            checkbox.activite = activite
            self.Bind(wx.EVT_CHECKBOX, self.OnActiviteCheckbox, checkbox)
            self.width += CHECKBOX_WIDTH
            self.activites_checkboxes.append(checkbox)
        self.UpdateActivites()
        
    def OnLineChanged(self):
        self.UpdateContents()
        if self.parent.parent.summary_panel:
            self.parent.parent.summary_panel.UpdateContents()
        if self.parent.on_modify:
            self.parent.on_modify(self.line)
                
    def UpdateContents(self):
        if self.label_panel:
            self.label_panel.SetLine(self.line)
        if self.status_icon:
            self.status_icon.SetLine(self.line)
        self.grid.SetLine(self.line)
        if self.comment_panel:
            self.comment_panel.SetLine(self.line)
        if self.parent.options & ACTIVITES:
            self.UpdateActivites()
        if self.parent.options & COMMENTS:
            self.UpdateBulle()

    def UpdateActivites(self):
        for checkbox in self.activites_checkboxes:
            if self.line is None or isinstance(self.line, basestring) or not self.line.options & ACTIVITES:
                checkbox.Hide()
            elif isinstance(self.line, LigneConge):
                checkbox.Show()
                checkbox.Disable()
            else:
                checkbox.Show()
                checkbox.Enable(not readonly)
                checkbox.SetValue(checkbox.activite.value in self.line.activites_sans_horaires)

    def UpdateBulle(self):
        if self.line is None or isinstance(self.line, basestring) or not self.line.options & COMMENTS:
            self.bulle_button.Show(False)
        else:
            self.bulle_button.Show(True)
            self.bulle_button.Enable()
            self.bulle_button.SetBitmapLabel(BULLE_BITMAP)  

    def SetLineHeight(self, height):
        self.height = height
        self.SetSize((max(self.width, self.parent.GetSize()[0]), height))
    
    def Recreate(self):
        self.DestroyChildren()
        self.Create()
            
    def SetLine(self, line):
        self.line = line
        self.UpdateContents()
        
    def OnActiviteCheckbox(self, event):
        button = event.GetEventObject()
        if not (self.line.readonly or readonly):
            if event.Checked():
                history.Append(None)
                self.line.InsertActivity(None, None, button.activite.value)
            else:
                history.Append(None)
                self.line.RemoveActivity(None, None, button.activite.value)
            self.line.Save()
            if self.line.insert is not None:
                self.line.insert[self.line.key] = self.line
                self.line.insert = None
            self.OnLineChanged()

    def OnCommentButtonPressed(self, _):
        if not (self.line.readonly or readonly):
            dlg = TextDialog(self, u"Commentaire", self.line.commentaire)
            response = dlg.ShowModal()
            dlg.Destroy()
            if response == wx.ID_OK:
                self.line.SetCommentaire(dlg.GetText())
                self.line.Save()
                history.Append(None)
                if self.line.insert is not None:
                    self.line.insert[self.line.key] = self.line
                    self.line.insert = None
                self.UpdateContents()


class PlanningInternalPanel(wx.Window):
    def __init__(self, parent, activity_combobox, options, check_line=None, on_modify=None):
        wx.Window.__init__(self, parent)
        self.parent = parent.parent
        self.activity_combobox = activity_combobox
        self.options = options
        self.check_line = check_line
        self.on_modify = on_modify
        self.plages_observer = -1
        self.activites_observer = -1
        self.width = 0
        self.info = ""        
        self.lines = []
        self.summary_panel = None
        self.line_widgets = []
        self.tri_planning = None
        self.planning_width = 0
        self.CheckLinesHeight()
        self.CheckLinesWidth()
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def SetInfo(self, info):
        self.info = info
        
    def Disable(self, info):
        self.SetInfo(info)
        self.SetLines([])
        
    def SetLines(self, lines):
        self.activites = creche.GetActivitesSansHoraires()
            
        if counters['plages'] > self.plages_observer:
            self.plages_observer = counters['plages']
            self.plages_fermeture = creche.GetPlagesArray(PLAGE_FERMETURE, conversion=True)
            self.plages_insecables = creche.GetPlagesArray(PLAGE_INSECABLE, conversion=True)
        
        previous_count = len(self.lines)
        self.lines = lines
        count = len(self.lines)

        if count > previous_count:
            for i in range(previous_count):
                self.line_widgets[i].SetLine(lines[i])
            for i in range(previous_count, count):
                widget = PlanningLine(self, lines[i], pos=(0, i*LINE_HEIGHT), size=(-1, self.line_height))
                self.line_widgets.append(widget)         
        else:
            for i in range(count):
                self.line_widgets[i].SetLine(lines[i])
            for i in range(count, previous_count):
                self.line_widgets[-1].Destroy()
                del self.line_widgets[-1]
        
        self.width = GetPlanningWidth() + 5
        if not self.options & NO_LABELS:
            self.width += LABEL_WIDTH
        if not self.options & NO_ICONS:
            self.width += ICONS_WIDTH
        self.width += len(self.activites) * CHECKBOX_WIDTH
        if self.options & COMMENTS:
            self.width += COMMENT_BUTTON_WIDTH
        self.width += RECAP_WIDTH
        self.UpdateSize(update_children=False)
        self.CheckLinesHeight()
        self.CheckLinesWidth()
        
    def CheckLinesHeight(self):
        if self.tri_planning != creche.tri_planning:
            self.tri_planning = creche.tri_planning
            if creche.tri_planning & TRI_LIGNES_CAHIER:
                self.line_height = LINE_HEIGHT - 1
            else:
                self.line_height = LINE_HEIGHT
            for widget in self.line_widgets:
                widget.SetLineHeight(self.line_height)
    
    def CheckLinesWidth(self):
        if GetPlanningWidth() != self.planning_width or (self.options & ACTIVITES and counters['activites'] > self.activites_observer):
            self.planning_width = GetPlanningWidth()
            self.activites_observer = counters['activites']
            for widget in self.line_widgets:
                widget.Recreate()
    
    def UpdateSize(self, update_children=True):
        width = max(self.width, self.GetParent().GetSize()[0])
        count = len(self.lines)
        if count > 0:
            self.SetMinSize((width, count*LINE_HEIGHT))
        else:
            self.SetSize(self.parent.GetSize())
            self.Refresh()
        if update_children:
            for widget in self.line_widgets:
                widget.SetLineHeight(self.line_height)

    def OnPaint(self, event):
        if self.info:
            width, height = self.parent.GetSize()
            dc = wx.PaintDC(self)
            dc.BeginDrawing()
            dc.Clear()
            dc.SetTextForeground("LIGHT GREY")
            font = wx.Font(64, wx.SWISS, wx.NORMAL, wx.BOLD)
            dc.SetFont(font)
            dc.DrawRotatedText(self.info, (width-700)/2, 350+(height-350)/2, 40)
            dc.EndDrawing()
        elif creche.tri_planning & TRI_LIGNES_CAHIER:
            # Dessin des lignes horizontales pour ceux qui ont besoin d'une séparation
            dc = wx.PaintDC(self)
            dc.BeginDrawing()
            dc.SetBackground(wx.Brush(wx.WHITE))
            dc.Clear()
            dc.SetPen(wx.LIGHT_GREY_PEN)
            width = max(self.width, self.GetParent().GetSize()[0])
            height = LINE_HEIGHT-1
            for line in self.lines:
                dc.DrawLine(0, height, width, height)
                height += LINE_HEIGHT
            dc.EndDrawing()


class PlanningScrollPanel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, activity_combobox, options, check_line=None, on_modify=None):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, style=wx.SUNKEN_BORDER)
        self.parent = parent
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.internal_panel = PlanningInternalPanel(self, activity_combobox, options, check_line, on_modify)
        sizer.Add(self.internal_panel, 0, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetupScrolling(scroll_x=False, scroll_y=not(options & NO_SCROLL))
        self.Bind(wx.EVT_SIZE, self.OnSize)
        
    def SetLines(self, lines):
        self.internal_panel.SetLines(lines)
        self.SetScrollbars(0, LINE_HEIGHT, 0, len(lines), 0, 0)
        
    def Disable(self, info):
        self.SetScrollbars(0, 0, 0, 0, 0, 0)
        self.internal_panel.Disable(info)
        
    def SetInfo(self, info):
        self.internal_panel.SetInfo(info)
        
    def OnSize(self, event):
        self.internal_panel.UpdateSize()


class PlanningSummaryPanel(BufferedWindow):
    def __init__(self, parent, options):
        self.parent = parent
        self.options = options
        self.activities_count = 0
        self.activites = {}
        self.activites_sans_horaires = {}
        BufferedWindow.__init__(self, parent, size=(-1, 2+20*self.activities_count))

    def UpdateContents(self):
        lines = self.GetParent().GetSummaryLines()
        self.activites, self.activites_sans_horaires = GetActivitiesSummary(creche, lines)
        
        new_activitites_count = len(self.activites)
        if self.activities_count != new_activitites_count:
            self.activities_count = new_activitites_count
            self.SetMinSize((-1, 2 + 20 * new_activitites_count))
            self.GetParent().sizer.Layout()

        self.ForceRefresh()

    def Draw(self, dc):
        dc.BeginDrawing()
        dc.SetBackground(wx.ClientDC(self).GetBackground())
        dc.Clear()
        
        if self.parent.lines:        
            try:
                dc = wx.GCDC(dc)
            except:
                pass
            
            # summary pour les activités avec horaire 
            for i, activity in enumerate(self.activites.keys()):
                dc.DrawText(self.activites[activity].label, 5, 6 + i * 20)
                self.DrawLine(dc, i, activity)
            
            # summary pour les activités sans horaire
            if self.options & ACTIVITES:
                dc.SetPen(wx.BLACK_PEN)
                dc.SetBrush(wx.GREY_BRUSH)
                for i, count in enumerate(self.activites_sans_horaires.values()):
                    x = GetPlanningWidth() + LABEL_WIDTH + i*CHECKBOX_WIDTH + 10
                    if not (self.options & NO_ICONS):
                        x += ICONS_WIDTH
                    rect = wx.Rect(x, 2, 20, 19)
                    dc.DrawRoundedRectangleRect(rect, 3)
                    text = str(count)
                    w, h = dc.GetTextExtent(text)
                    dc.DrawText(text, x + (20-w)/2, 4 + (15-h)/2)
            
            # total horaire + pourcentage remplissage
            text = self.parent.GetSummaryDynamicText()
            if text: 
                x = GetPlanningWidth()
                if not self.options & NO_LABELS:
                    x += LABEL_WIDTH
                if not self.options & NO_ICONS:
                    x += ICONS_WIDTH
                if self.options & ACTIVITES:
                    x += len(self.activites_sans_horaires) * CHECKBOX_WIDTH
                if self.options & COMMENTS:
                    x += COMMENT_BUTTON_WIDTH
                x += 7
                dc.SetPen(wx.BLACK_PEN)
                dc.SetBrush(wx.WHITE_BRUSH)
                w, h = dc.GetTextExtent(text)
                dc.DrawRectangle(x, 4, w + 5, 15)
                dc.DrawText(text, x + 2, 4 + (15 - h) / 2)
            
        dc.EndDrawing()

    def DrawLine(self, dc, index, activity):
        line = self.activites[activity]

        pos = LABEL_WIDTH
        if not self.options & NO_ICONS:
            pos += ICONS_WIDTH

        debut = int(creche.affichage_min * (60 / BASE_GRANULARITY))
        fin = int(creche.affichage_max * (60 / BASE_GRANULARITY))
        x = debut
        v, w = 0, 0
        a = 0
        while x <= fin:
            if x == fin:
                nv, nw = 0, 0
            else:
                nv, nw = line[x]

            if (self.options & TWO_PARTS) and activity == 0 and (nw == 0 or nv > creche.GetCapacite() or float(nv) / nw > 6.5):
                nw = activity | SUPPLEMENT
            else:
                nw = activity
                
            if nv != v or nw != w:
                if v != 0:
                    rect = wx.Rect(pos+3+(a-debut)*config.column_width, 2 + index * 20, (x-a)*config.column_width-1, 19)
                    if w == PRESENCE_SALARIE:
                        w = 0
                    r, g, b, t, s = GetActivityColor(w)
                    
                    text = str(v)
                    try:
                        dc.SetPen(wx.Pen(wx.Colour(r, g, b, wx.ALPHA_OPAQUE)))
                        dc.SetBrush(wx.Brush(wx.Colour(r, g, b, t), s))
                    except:
                        dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
                        dc.SetBrush(wx.Brush(wx.Colour(r, g, b), s))
                    w, h = dc.GetTextExtent(text)
                    dc.DrawRoundedRectangleRect(rect, 3)
                    dc.DrawText(text, pos + 4 - 4*len(text) + (float(x+a)/2-debut)*config.column_width, 4 + (15-h)/2 + index * 20)
                a = x
                v, w = nv, nw
            x += 1


class PlanningWidget(wx.Panel):
    def __init__(self, parent, activity_combobox=None, options=0, check_line=None, on_modify=None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.LB_DEFAULT)
        self.options = options
        self.lines = []
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.scale_window = wx.Window(self, -1, size=(-1, 25))
        self.sizer.Add(self.scale_window, 0, wx.EXPAND)
        self.internal_panel = PlanningScrollPanel(self, activity_combobox, options, check_line, on_modify)
        self.sizer.Add(self.internal_panel, 1, wx.EXPAND)
        if not (options & NO_BOTTOM_LINE):
            self.summary_panel = PlanningSummaryPanel(self, options)
            self.sizer.Add(self.summary_panel, 0, wx.EXPAND)
        else:
            self.summary_panel = None
        self.SetSizer(self.sizer)
        self.sizer.Layout()
        self.scale_window.Bind(wx.EVT_PAINT, self.OnPaint)

    def GetSummaryDynamicText(self):
        return None
    
    def SetInfo(self, info):
        self.internal_panel.SetInfo(info)
        
    def Disable(self, info):
        self.lines = []
        self.internal_panel.Disable(info)
        if self.summary_panel:
            self.summary_panel.UpdateContents()
        
    def SetLines(self, lines):
        self.lines = lines
        self.UpdateDrawing()
    
    def UpdateDrawing(self):
        self.internal_panel.SetLines(self.lines)
        if self.summary_panel:
            self.summary_panel.UpdateContents()
        if self.options & NO_SCROLL:
            self.SetMinSize((-1, 25+5+LINE_HEIGHT*len(self.lines)))
        self.Refresh()
        
    def GetSummaryLines(self):
        lines = []
        for line in self.lines:
            if line is not None and not isinstance(line, LigneConge) and not isinstance(line, basestring) and line.summary:
                lines.append(line)
        return lines

    def OnPaint(self, event):
        dc = wx.PaintDC(self.scale_window)
        # seems removed in wxPython 2.9 self.scale_window.PrepareDC(dc)
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
        offset = 2
        if not self.options & NO_LABELS:
            offset += LABEL_WIDTH
        if not self.options & NO_ICONS:
            offset += ICONS_WIDTH
        while heure <= affichage_max:
            x = offset + (heure - affichage_min) * config.column_width
            if heure % (60 / BASE_GRANULARITY) == 0:
                dc.DrawLine(x, 20, x, 12)
                dc.DrawText(str(int(round(heure/(60 / BASE_GRANULARITY))))+"h", x - 3, 0)
            else:
                dc.DrawLine(x, 20, x, 15)
            heure += creche.granularite / BASE_GRANULARITY
        
        # les noms des activités en oblique
        if self.options & ACTIVITES:
            activites = creche.GetActivitesSansHoraires()
            font = wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL)
            dc.SetFont(font)
            for i, activite in enumerate(activites):
                dc.DrawRotatedText(activite.label, i*25 + 10 + offset + (affichage_max - affichage_min) * config.column_width, 12, 18)
            
        dc.EndDrawing()


class LinePlanningWidget(PlanningWidget):
    def __init__(self, parent, line, options=0):
        PlanningWidget.__init__(self, parent, None, options|NO_BOTTOM_LINE|NO_LABELS|NO_ICONS|DRAW_VALUES)
        self.line = line
        self.SetLines([self.line])
        self.SetMinSize((-1, 60))
