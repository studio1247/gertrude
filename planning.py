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
from controls import GetActivityColor, TextDialog
from functions import GetActivitiesSummary, GetBitmapFile, GetHeureString
from sqlobjects import Day, JourneeCapacite
from history import *

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
LABEL_WIDTH = 130 # px
ICONS_WIDTH = 50 # px
LINE_HEIGHT = 32 # px
CHECKBOX_WIDTH = 20 # px

BUTTON_BITMAPS = { ABSENT: (wx.Bitmap(GetBitmapFile("icone_vacances.png"), wx.BITMAP_TYPE_PNG), u'Absent'),
                   ABSENT+PREVISIONNEL: (wx.Bitmap(GetBitmapFile("icone_vacances.png"), wx.BITMAP_TYPE_PNG), u'Congés'),
                   PRESENT: (wx.Bitmap(GetBitmapFile("icone_presence.png"), wx.BITMAP_TYPE_PNG), u'Présent'),
                   PRESENT+PREVISIONNEL: (wx.Bitmap(GetBitmapFile("icone_presence_prev.png"), wx.BITMAP_TYPE_PNG), u'Présent'),
                   VACANCES: (wx.Bitmap(GetBitmapFile("icone_vacances.png"), wx.BITMAP_TYPE_PNG), u'Congés'),
                   MALADE: (wx.Bitmap(GetBitmapFile("icone_maladie.png"), wx.BITMAP_TYPE_PNG), u'Malade'),
                   HOPITAL: (wx.Bitmap(GetBitmapFile("icone_hopital.png"), wx.BITMAP_TYPE_PNG), u'Maladie avec hospitalisation'),
                   MALADE_SANS_JUSTIFICATIF: (wx.Bitmap(GetBitmapFile("icone_maladie_sans_justificatif.png"), wx.BITMAP_TYPE_PNG), u'Maladie sans justificatif'),
                   ABSENCE_NON_PREVENUE: (wx.Bitmap(GetBitmapFile("icone_absence_non_prevenue.png"), wx.BITMAP_TYPE_PNG), u'Absence non prévenue'),
                   ABSENCE_CONGE_SANS_PREAVIS: (wx.Bitmap(GetBitmapFile("icone_absence_sans_preavis.png"), wx.BITMAP_TYPE_PNG), u'Congés sans préavis'),
                   CONGES_DEPASSEMENT: (wx.Bitmap(GetBitmapFile("icone_conges_depassement.png"), wx.BITMAP_TYPE_PNG), u'Absence non déductible (dépassement)'),
                   }

def getPlanningWidth():
    return (creche.affichage_max - creche.affichage_min) * (60 / BASE_GRANULARITY) * config.column_width

class LigneConge(object):
    def __init__(self, info):
        self.info = info
        self.readonly = True
        self.reference = None
        self.options = 0
    
    def GetNombreHeures(self):
        return 0.0

class PlanningGridWindow(BufferedWindow):
    def __init__(self, parent, activity_combobox, options, check_line=None, on_modify=None):
        self.options = options
        self.check_line = check_line
        self.on_modify = on_modify
        self.info = ""
        self.plages_fermeture = creche.GetPlagesArray(PLAGE_FERMETURE, conversion=True)
        self.plages_insecables = creche.GetPlagesArray(PLAGE_INSECABLE, conversion=True)
        self.last_plages_observer = None 
        self.lines = []
        BufferedWindow.__init__(self, parent, size=((creche.affichage_max-creche.affichage_min) * 4 * config.column_width + 1, -1))
        # self.SetBackgroundColour(wx.WHITE)
        self.activity_combobox = activity_combobox
        self.value, self.state = None, None
        if options & DRAW_NUMBERS:
            self.draw_line = self.DrawNumbersLine
        else:
            self.draw_line = self.DrawActivitiesLine
        if not (options & READ_ONLY or readonly):
            self.SetCursor(wx.StockCursor(wx.CURSOR_PENCIL))        
            self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftButtonDown)
            self.Bind(wx.EVT_LEFT_UP, self.OnLeftButtonUp)
            self.Bind(wx.EVT_MOTION, self.OnLeftButtonDragging)

    def SetInfo(self, info):
        self.info = info
        
    def Disable(self, info):
        self.SetInfo(info)
        self.SetLines([])
        
    def SetLines(self, lines):
        self.lines = lines
        self.SetMinSize((int((creche.affichage_max-creche.affichage_min) * (60 / BASE_GRANULARITY) * config.column_width + 1), LINE_HEIGHT * len(self.lines) - 1))
        if self.last_plages_observer is None or ('plages' in observers and observers['plages'] > self.last_plages_observer):
            self.plages_fermeture = creche.GetPlagesArray(PLAGE_FERMETURE, conversion=True)
            self.plages_insecables = creche.GetPlagesArray(PLAGE_INSECABLE, conversion=True)
            if 'plages' in observers:
                self.last_plages_observer = observers['plages']
            
    def UpdateLine(self, index):
        self.UpdateDrawing()

    def DrawLineGrid(self, dc):
        dc.SetPen(wx.WHITE_PEN)
        dc.SetBrush(wx.WHITE_BRUSH)

        height = dc.GetSize()[1]
        
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
            dc.DrawLine(x, 0,  x, height)
            heure += creche.granularite / BASE_GRANULARITY

        try:
            dc = wx.GCDC(dc)
        except:
            pass
        
        dc.SetPen(wx.LIGHT_GREY_PEN)
        dc.SetBrush(wx.LIGHT_GREY_BRUSH)
        for debut, fin in self.plages_fermeture:
            dc.DrawRectangle(1 + (debut-affichage_min) * config.column_width, 0, (fin-debut) * config.column_width - 1, height)
        dc.SetPen(wx.TRANSPARENT_PEN)            
        dc.SetBrush(wx.Brush(wx.Colour(250, 250, 0, 100)))
        for debut, fin in self.plages_insecables:
            dc.DrawRectangle(1 + (debut-affichage_min) * config.column_width, 0, (fin-debut) * config.column_width - 1, height)
            
            
    def Draw(self, dc):
        dc.BeginDrawing()
        dc.SetBackground(wx.ClientDC(self).GetBackground())
        dc.Clear()

        # le quadrillage
        self.DrawLineGrid(dc)

        # les plages de fermeture
        height = dc.GetSize()[1]
        dc.SetPen(wx.LIGHT_GREY_PEN)
        dc.SetBrush(wx.LIGHT_GREY_BRUSH)
        affichage_min = int(creche.affichage_min * 60 / BASE_GRANULARITY)
        for debut, fin in self.plages_fermeture:
            dc.DrawRectangle(1 + (debut-affichage_min) * config.column_width, 0, (fin-debut) * config.column_width - 1, height)

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
        if line is None:
            dc.SetBrush(wx.WHITE_BRUSH)
            dc.SetPen(wx.TRANSPARENT_PEN)
            width = getPlanningWidth()
            y = 14+index*LINE_HEIGHT
            dc.DrawRectangle(1, index*LINE_HEIGHT, width-3, 30)
            dc.SetPen(wx.BLACK_PEN)
            dc.DrawLine(50, y, width-50, y)
        elif isinstance(line, LigneConge):
            dc.SetPen(wx.BLACK_PEN)
            dc.DrawText(line.info, 100, 7 + index * LINE_HEIGHT)
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
                        rect = wx.Rect(1+(start-int(creche.affichage_min*(60 / BASE_GRANULARITY)))*config.column_width, 1+index*LINE_HEIGHT, (end-start)*config.column_width-1, LINE_HEIGHT/3)
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
                rect = wx.Rect(1+(start-int(creche.affichage_min*(60 / BASE_GRANULARITY)))*config.column_width, 1+index*LINE_HEIGHT, (end-start)*config.column_width-1, LINE_HEIGHT-1)
                dc.DrawRoundedRectangleRect(rect, 3)
                if self.options & DRAW_VALUES and val != 0:
                    dc.DrawText(str(val), rect.GetX() + rect.GetWidth()/2 - 4*len(str(val)), 7 + index * LINE_HEIGHT)
            # Commentaire sur la ligne
            if self.options & COMMENTS:
                dc.SetPen(wx.BLACK_PEN)
                dc.DrawText(line.commentaire, 50, 7 + index * LINE_HEIGHT)
            
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
                    nv = line[x][0]
                if nv != v:
                    if v != 0:
                        rect = wx.Rect(pos+3+(a-debut)*config.column_width, 2 + index * LINE_HEIGHT, (x-a)*config.column_width-1, LINE_HEIGHT-1)
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
                        dc.DrawText(s, pos + 4 - 4*len(s) + (float(x+a)/2-debut)*config.column_width, 7 + index * LINE_HEIGHT)
                    a = x    
                    if nv:
                        v = nv
                    else:
                        v = 0
                x += 1
        
    def __get_pos(self, x, y):
        p = -1
        if x > 0:
            x -= 1
        l = int(creche.affichage_min * (60 / BASE_GRANULARITY) + (x / config.column_width))               
        c = int(y / LINE_HEIGHT)
        return l, c, p

    def OnLeftButtonDown(self, event):
        posX, self.curStartY, self.curStartPos = self.__get_pos(event.GetX(), event.GetY())
        self.curStartX = (posX / (creche.granularite/BASE_GRANULARITY)) * (creche.granularite/BASE_GRANULARITY)
        if self.curStartPos != 0 and self.curStartY < len(self.lines):
            line = self.lines[self.curStartY]
            if not (isinstance(line, basestring) or line is None or line.readonly or readonly):
                if self.activity_combobox:
                    self.value = self.activity_combobox.activity.value
                else:
                    self.value = 0
                if creche.presences_previsionnelles and line.reference and line.date > datetime.date.today():
                    self.value |= PREVISIONNEL
                for a, b, v in line.activites.keys():
                    if (line.exclusive or v == self.value) and posX >= a and posX <= b:
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
        
        for debut, fin in self.plages_insecables:
            if (start >= debut and start < fin) or (end > debut and end < fin) or (start <= debut and end > fin): 
                if debut < start:
                    start = debut
                if fin > end:
                    end = fin

        result = [(start, end)]        
        for start, end in self.plages_fermeture:
            for i, (debut, fin) in enumerate(result):
                if debut >= start and fin <= end:
                    del result[i]
                elif start > debut and end < fin:
                    result[i] = (debut, start)
                    result.insert(i+1, (end, fin))
                    break
                elif start >= debut and start <= fin and end >= fin:
                    result[i] = (debut, start)
                elif start <= debut and end >= debut and end <= fin:
                    result[i] = (end, fin)
        
        return result

    def OnLeftButtonDragging(self, event):
        if self.state is not None:
            posX, self.curEndY, curEndPos = self.__get_pos(event.GetX(), event.GetY())
            self.curEndX = (posX / (creche.granularite/BASE_GRANULARITY)) * (creche.granularite/BASE_GRANULARITY)
            line = self.lines[self.curStartY]
            
            line_copy = Day()
            line_copy.Copy(line, False)

            for start, end in self.GetPlagesSelectionnees():                        
                if self.state > 0:
                    line_copy.SetActivity(start, end, self.value)
                else:
                    line_copy.ClearActivity(start, end, self.value)

            bmp = wx.EmptyBitmap(getPlanningWidth()+1, 3*LINE_HEIGHT)
            lineDC = wx.MemoryDC()
            lineDC.SelectObject(bmp)
            lineDC.SetBackground(wx.ClientDC(self).GetBackground())
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
            wx.ClientDC(self).Blit(0, self.curStartY*LINE_HEIGHT, getPlanningWidth()+1, LINE_HEIGHT+1, lineDC, 0, LINE_HEIGHT)

    def OnLeftButtonUp(self, event):
        if self.state is not None:
            line = self.lines[self.curStartY]
            
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
                        self.GetParent().UpdateLine(self.curStartY)
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

            self.GetParent().UpdateLine(self.curStartY)
            self.UpdateDrawing()
            
            if self.options & DEPASSEMENT_CAPACITE and self.state > 0 and self.value == 0 and creche.alerte_depassement_planning and self.check_line:
                self.check_line(line, self.GetPlagesSelectionnees())
                
            if self.on_modify:
                self.on_modify(line)
                    
            self.state = None

class PlanningInternalPanel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, activity_combobox, options, check_line=None, on_modify=None):
        self.options = options
        self.activites_count = 0
        self.bulle_bitmap = wx.Bitmap(GetBitmapFile("bulle.png"))
        width = getPlanningWidth() + 27
        if not options & NO_LABELS:
            width += LABEL_WIDTH
        if not options & NO_ICONS:
            width += ICONS_WIDTH
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1, size=(width, -1), style=wx.SUNKEN_BORDER)
        self.lines = []
        self.summary_panel = None
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        if not options & NO_LABELS:
            self.labels_panel = wx.Window(self, -1, size=(LABEL_WIDTH, -1))
            self.labels_panel.Bind(wx.EVT_PAINT, self.OnPaint)
            self.sizer.Add(self.labels_panel, 0, wx.EXPAND)
        if not options & NO_ICONS:
            self.buttons_sizer = wx.BoxSizer(wx.VERTICAL)
            self.buttons_sizer.SetMinSize((ICONS_WIDTH-2, -1))
            self.sizer.Add(self.buttons_sizer, 0, wx.EXPAND|wx.RIGHT, 2)
        self.grid_panel = PlanningGridWindow(self, activity_combobox, options, check_line, on_modify)
        self.sizer.Add(self.grid_panel, 0, wx.EXPAND)
        self.last_activites_observer = None
        self.right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.right_sizer)
        self.activites_sizers = []      
        self.SetSizer(self.sizer)
        self.SetupScrolling(scroll_x=False, scroll_y=not(options & NO_SCROLL))

    def OnCommentButtonPressed(self, event):
        button = event.GetEventObject()
        line = self.lines[button.line]
        if not (line.readonly or readonly):
            state = line.GetState()
            dlg = TextDialog(self, "Commentaire", line.commentaire)
            response = dlg.ShowModal()
            dlg.Destroy()
            if response == wx.ID_OK:
                line.SetCommentaire(dlg.GetText())
                line.Save()
                history.Append(None)
                if line.insert is not None:
                    line.insert[line.key] = line
                    line.insert = None
        
                self.grid_panel.UpdateLine(button.line)
                self.UpdateLine(button.line)

    def OnButtonPressed(self, event):
        button = event.GetEventObject()
        line = self.lines[button.line]
        if not (line.readonly or readonly):
            history.Append([Call(line.Restore, line.Backup())])        
            state = line.GetState()
            
            if state < 0:
                order = [VACANCES, ABSENCE_CONGE_SANS_PREAVIS, ABSENCE_NON_PREVENUE, MALADE, HOPITAL, MALADE_SANS_JUSTIFICATIF, PRESENT]
                if not creche.gestion_preavis_conges:
                    order.remove(ABSENCE_CONGE_SANS_PREAVIS)
                if not creche.gestion_absences_non_prevenues:
                    order.remove(ABSENCE_NON_PREVENUE)
                if not creche.gestion_maladie_hospitalisation:
                    order.remove(HOPITAL)
                if not creche.gestion_maladie_sans_justificatif:
                    order.remove(MALADE_SANS_JUSTIFICATIF)

                index = order.index(state)
                newstate = order[(index+1) % len(order)]
                if newstate == PRESENT:
                    if line.HasPrevisionnelCloture():
                        line.RestorePrevisionnelCloture(creche.presences_previsionnelles and line.date > datetime.date.today())
                    else:
                        reference = line.reference
                        line.Copy(reference, creche.presences_previsionnelles and line.date > datetime.date.today())
                        line.Save()
                        line.reference = reference
                else:
                    line.SetState(newstate)
            elif line.date <= datetime.date.today() and state & PREVISIONNEL:
                line.Confirm()
            else:
                if line.reference.GetState() == ABSENT:
                    line.SetState(MALADE)
                else:
                    line.SetState(VACANCES)
    
            if line.insert is not None:
                line.insert[line.key] = line
                line.insert = None
    
            self.grid_panel.UpdateLine(button.line)
            self.UpdateLine(button.line)
        
    def OnActiviteCheckbox(self, event):
        button = event.GetEventObject()
        line = self.lines[button.line]
        if not (line.readonly or readonly):
            if event.Checked():
                history.Append(None)
                line.InsertActivity(None, None, button.activite.value)
            else:
                history.Append(None)
                line.RemoveActivity(None, None, button.activite.value)
            line.Save()
            if line.insert is not None:
                line.insert[line.key] = line
                line.insert = None
            if self.GetParent().summary_panel:
                self.GetParent().summary_panel.UpdateContents()

    def UpdateLine(self, index):
        line = self.lines[index]
        right_sizer = self.right_sizer.GetItem(index).GetSizer()
        if not self.options & NO_ICONS:
            self.UpdateIcon(index)
        ctrl_index = 0
        if self.options & ACTIVITES:
            self.UpdateActivites(index)
            ctrl_index += 1
        if self.options & COMMENTS:
            bulle_button = right_sizer.GetItem(ctrl_index).GetWindow()
            ctrl_index += 1
            if line is None or isinstance(line, basestring) or not line.options & COMMENTS:
                bulle_button.Show(False)
            else:
                bulle_button.Show(True)
                bulle_button.Enable()
                bulle_button.SetBitmapLabel(self.bulle_bitmap)
        text_ctrl = right_sizer.GetItem(ctrl_index).GetWindow()
        if line is None or isinstance(line, basestring) or not line.GetDynamicText:
            text = None
        else:
            text = line.GetDynamicText(line)
        if text:
            text_ctrl.SetWindowStyle(wx.BORDER)
            text_ctrl.SetLabel(line.GetDynamicText(line))
        else:
            text_ctrl.SetWindowStyle(wx.NO_BORDER)
            text_ctrl.SetLabel("")
        
        self.GetParent().UpdateLine(index)
    
    def UpdateIcon(self, index):
        line = self.lines[index]
        button = self.buttons_sizer.GetItem(index).GetWindow().button
        right_sizer = self.right_sizer.GetItem(index).GetSizer()
        text_ctrl = right_sizer.GetItem(2).GetWindow()
        activites_sizer = self.activites_sizers[index]
        if line is None or isinstance(line, basestring):
            button.Hide()
        else:
            if isinstance(line, LigneConge):
                state = VACANCES
            else:
                state = line.GetState()
                if state > 0:
                    activities_state = state & ~(PRESENT|PREVISIONNEL)
                    if activities_state:
                        state &= ~activities_state
                        state |= PRESENT
                elif state == VACANCES and creche.repartition == REPARTITION_SANS_MENSUALISATION:
                    try:
                        if line.inscription.IsNombreSemainesCongesAtteint(line.key):
                            state = CONGES_DEPASSEMENT
                    except:
                        pass
                    
            bitmap, tooltip = BUTTON_BITMAPS[state]
            button.SetBitmapLabel(bitmap)
            button.SetToolTip(wx.ToolTip(tooltip))
            button.Show(True)
            
    def UpdateActivites(self, index):
        line = self.lines[index]
        activites_sizer = self.activites_sizers[index]
        for item in activites_sizer.GetChildren():
            checkbox = item.GetWindow()
            if line is None or isinstance(line, basestring) or not line.options & ACTIVITES:
                checkbox.Hide()
            elif isinstance(line, LigneConge):
                checkbox.Show()
                checkbox.Disable()
            else:
                checkbox.Show()
                checkbox.Enable(not readonly)
                checkbox.SetValue(checkbox.activite.value in line.activites_sans_horaires)

    def SetInfo(self, info):
        self.grid_panel.SetInfo(info)
        
    def Disable(self, info):
        self.lines = []
        self.SetScrollPos(wx.VERTICAL, 0)
        if not self.options & NO_ICONS:
            self.buttons_sizer.Clear(True)
        self.right_sizer.Clear(True)
        self.activites_sizers = []
        if not self.options & NO_LABELS:
            self.labels_panel.SetMinSize((LABEL_WIDTH, 1))
            self.labels_panel.Refresh()
        self.grid_panel.Disable(info)
        self.sizer.Layout()
        self.SetupScrolling(scroll_x=False, scroll_y=not(self.options & NO_SCROLL))
        self.GetParent().sizer.Layout()
        self.grid_panel.UpdateDrawing()
        
    def SetLines(self, lines):
        previous_count = len(self.lines)
        self.lines = lines
        count = len(self.lines)
        
        activites = creche.GetActivitesSansHoraires()
        activites_count = len(activites)
        
        if self.options & ACTIVITES and (self.last_activites_observer is None or ('activites' in observers and observers['activites'] > self.last_activites_observer)):
            if 'activites' in observers:
                self.last_activites_observer = observers['activites']
            for j, sizer in enumerate(self.activites_sizers):
                for i in range(self.activites_count, activites_count, -1):
                    sizer.GetItem(i-1).DeleteWindows()
                    sizer.Detach(i-1)
                for i in range(self.activites_count, activites_count):
                    checkbox = wx.CheckBox(self, -1, "", size=(CHECKBOX_WIDTH, LINE_HEIGHT))
                    checkbox.Enable(not readonly)
                    sizer.Add(checkbox, 0, wx.EXPAND|wx.LEFT, 5)
                    checkbox.line = i
                    self.Bind(wx.EVT_CHECKBOX, self.OnActiviteCheckbox, checkbox)
                for i, activite in enumerate(activites):
                    sizer.GetItem(i).GetWindow().activite = activite      
            self.activites_count = activites_count
         
        self.grid_panel.SetLines(lines)        

        if count != previous_count:
            self.SetScrollPos(wx.VERTICAL, 0)
            
            for i in range(previous_count, count, -1):
                if not self.options & NO_ICONS:
                    self.buttons_sizer.GetItem(i-1).DeleteWindows()
                    self.buttons_sizer.Detach(i-1)
                right_sizer = self.right_sizer.GetItem(i-1)
                right_sizer.DeleteWindows()
                self.right_sizer.Detach(i-1)
                if self.options & ACTIVITES:
                    del self.activites_sizers[-1]
            for i in range(previous_count, count):
                if not self.options & NO_ICONS:
                    panel = wx.Panel(self)
                    panel.SetMinSize((48, LINE_HEIGHT))
                    self.buttons_sizer.Add(panel)
                    panel.button = wx.BitmapButton(panel, -1, BUTTON_BITMAPS[PRESENT][0], size=(47, LINE_HEIGHT), style=wx.NO_BORDER)
                    panel.button.line = i
                    self.Bind(wx.EVT_BUTTON, self.OnButtonPressed, panel.button)
                    sizer = wx.BoxSizer(wx.VERTICAL)
                    sizer.Add(panel.button, 0, wx.LEFT, 2)
                    panel.SetSizer(sizer)
                    
                line_sizer = wx.BoxSizer(wx.HORIZONTAL)
                line_sizer.SetMinSize((-1, LINE_HEIGHT))
                
                if self.options & ACTIVITES:
                    activites_sizer = wx.BoxSizer(wx.HORIZONTAL)
                    for activite in activites: 
                        checkbox = wx.CheckBox(self, -1, "", size=(CHECKBOX_WIDTH, LINE_HEIGHT))
                        checkbox.Enable(not readonly)
                        activites_sizer.Add(checkbox, 0, wx.EXPAND|wx.LEFT, 5)
                        checkbox.activite = activite
                        checkbox.line = i
                        self.Bind(wx.EVT_CHECKBOX, self.OnActiviteCheckbox, checkbox)
                    line_sizer.Add(activites_sizer, 0, wx.LEFT, 5)
                    self.activites_sizers.append(activites_sizer)

                if self.options & COMMENTS:
                    comment_button = wx.BitmapButton(self, -1, self.bulle_bitmap, style=wx.NO_BORDER)
                    comment_button.SetMinSize((-1, LINE_HEIGHT))
                    comment_button.line = i
                    self.Bind(wx.EVT_BUTTON, self.OnCommentButtonPressed, comment_button)
                    line_sizer.Add(comment_button)
                
                text_ctrl = wx.StaticText(self, -1, style=wx.NO_BORDER)
                line_sizer.Add(text_ctrl, 0, wx.LEFT|wx.TOP, 7)
                
                self.right_sizer.Add(line_sizer)
                   
            if not self.options & NO_LABELS:
                self.labels_panel.SetMinSize((LABEL_WIDTH, LINE_HEIGHT*count - 1))
            self.sizer.Layout()
            self.SetupScrolling(scroll_x=False, scroll_y=not(self.options & NO_SCROLL))
            self.GetParent().sizer.Layout()

        for i in range(count):
            self.UpdateLine(i)
        
        self.grid_panel.UpdateDrawing()
        if not self.options & NO_LABELS:
            self.labels_panel.Refresh()
        self.Layout()
            
    def OnPaint(self, event):
        dc = wx.PaintDC(self.labels_panel)
        dc.BeginDrawing()
        dc.SetTextForeground("BLACK")
        labelfont = wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL)
        sublabelfont = wx.Font(6, wx.SWISS, wx.NORMAL, wx.NORMAL)
        dc.SetFont(labelfont)
        for i, line in enumerate(self.lines):
            if line is None:
                pass
            elif isinstance(line, basestring):
                rect = wx.Rect(1, 5 + i * LINE_HEIGHT, 125, LINE_HEIGHT-8)
                try:
                    dc.SetPen(wx.Pen(wx.Colour(0, 0, 0, wx.ALPHA_OPAQUE)))
                    dc.SetBrush(wx.Brush(wx.Colour(128, 128, 128, 128), wx.SOLID))
                except:
                    dc.SetPen(wx.Pen(wx.Colour(0, 0, 0)))
                    dc.SetBrush(wx.Brush(wx.Colour(128, 128, 128), wx.SOLID))
                dc.DrawRoundedRectangleRect(rect, 3)
                dc.DrawText(line, 5, 8 + i * LINE_HEIGHT)
            else:
                if line.sublabel:
                    dc.DrawText(line.label, 5, 4 + LINE_HEIGHT*i)
                    dc.SetFont(sublabelfont)
                    dc.DrawText(line.sublabel, 5, 16 + LINE_HEIGHT*i)
                    dc.SetFont(labelfont)
                else:
                    dc.DrawText(line.label, 5, 6 + LINE_HEIGHT*i)
        dc.EndDrawing()


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
            self.SetMinSize((-1, 2+20*new_activitites_count))
            self.GetParent().sizer.Layout()

        self.UpdateDrawing()

    def Draw(self, dc):
        dc.BeginDrawing()
        dc.SetBackground(wx.ClientDC(self).GetBackground())
        dc.Clear()
        
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
                x = getPlanningWidth() + LABEL_WIDTH + i*25 + 10
                if not (self.options & NO_ICONS):
                    x += ICONS_WIDTH
                rect = wx.Rect(x, 2, 20, 19)
                dc.DrawRoundedRectangleRect(rect, 3)
                dc.DrawText(str(count), x + 4, 5)
        
        # total horaire + pourcentage remplissage
        text = self.parent.GetSummaryDynamicText()
        if text: 
            x = getPlanningWidth() + LABEL_WIDTH + 10 + 6
            if not self.options & NO_ICONS:
                x += ICONS_WIDTH
            if self.options & ACTIVITES:
                x += len(self.activites_sans_horaires) * 25
            if self.options & COMMENTS:
                x += 15
            dc.SetPen(wx.BLACK_PEN)
            dc.SetBrush(wx.WHITE_BRUSH)
            w, h = dc.GetTextExtent(text)
            dc.DrawRectangle(x, 4, w+5, 15)
            dc.DrawText(text, x+2, 4 + (15-h)/2)
            
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

            if (self.options & TWO_PARTS) and activity == 0 and (nw == 0 or nv > creche.GetCapacite() or float(nv)/nw > 6.5):
                nw = activity|SUPPLEMENT
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
        
class PlanningWidget(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, activity_combobox=None, options=0, check_line=None, on_modify=None):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, id=-1, style=wx.LB_DEFAULT)
        self.options = options
        self.lines = []
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.scale_window = wx.Window(self, -1, size=(-1, 25))
        self.sizer.Add(self.scale_window, 0, wx.EXPAND)
        self.internal_panel = PlanningInternalPanel(self, activity_combobox, options, check_line, on_modify)
        self.sizer.Add(self.internal_panel, 1, wx.EXPAND)
        if not (options & NO_BOTTOM_LINE):
            self.summary_panel = PlanningSummaryPanel(self, options)
            self.sizer.Add(self.summary_panel, 0, wx.EXPAND)
        else:
            self.summary_panel = None
        self.SetSizer(self.sizer)
        self.SetupScrolling(scroll_x=False, scroll_y=not(options & NO_SCROLL))
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
        self.internal_panel.SetLines(lines)
        if self.summary_panel:
            self.summary_panel.UpdateContents()
        if self.options & NO_SCROLL:
            self.SetMinSize((-1, 25+5+LINE_HEIGHT*len(lines)))
        self.Refresh()
    
    def UpdateDrawing(self):
        for i in range(len(self.lines)):
            self.internal_panel.UpdateLine(i)
        
    def UpdateLine(self, index):
        if self.summary_panel:
            self.summary_panel.UpdateContents()
        
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
        
