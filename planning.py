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

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

import collections
import wx
import wx.lib.scrolledpanel
from buffered_window import BufferedWindow
from controls import TextDialog
from database import Timeslot, Activite
from functions import *
from config import config
from planning_line import BasePlanningLine, BasePlanningSeparator
from history import Call


# Elements size
LABEL_WIDTH = 130  # px
ICONS_WIDTH = 50  # px
LINE_HEIGHT = 32  # px
CHECKBOX_WIDTH = 25  # px
COMMENT_BUTTON_WIDTH = 31  # px
RECAP_WIDTH = 100  # px

try:
    BUTTON_BITMAPS = {ABSENT: (wx.Bitmap(GetBitmapFile("icone_vacances.png"), wx.BITMAP_TYPE_PNG), "Absent"),
                      PRESENT: (wx.Bitmap(GetBitmapFile("icone_presence.png"), wx.BITMAP_TYPE_PNG), "Présent"),
                      VACANCES: (wx.Bitmap(GetBitmapFile("icone_vacances.png"), wx.BITMAP_TYPE_PNG), "Congés"),
                      CONGES_PAYES: (wx.Bitmap(GetBitmapFile("icone_conges_payes.png"), wx.BITMAP_TYPE_PNG), STATE_LABELS[CONGES_PAYES]),
                      MALADE: (wx.Bitmap(GetBitmapFile("icone_maladie.png"), wx.BITMAP_TYPE_PNG), STATE_LABELS[MALADE]),
                      HOPITAL: (wx.Bitmap(GetBitmapFile("icone_hopital.png"), wx.BITMAP_TYPE_PNG), STATE_LABELS[HOPITAL]),
                      MALADE_SANS_JUSTIFICATIF: (wx.Bitmap(GetBitmapFile("icone_maladie_sans_justificatif.png"), wx.BITMAP_TYPE_PNG), STATE_LABELS[MALADE_SANS_JUSTIFICATIF]),
                      ABSENCE_NON_PREVENUE: (wx.Bitmap(GetBitmapFile("icone_absence_non_prevenue.png"), wx.BITMAP_TYPE_PNG), STATE_LABELS[ABSENCE_NON_PREVENUE]),
                      ABSENCE_CONGE_SANS_PREAVIS: (wx.Bitmap(GetBitmapFile("icone_absence_sans_preavis.png"), wx.BITMAP_TYPE_PNG), STATE_LABELS[ABSENCE_CONGE_SANS_PREAVIS]),
                      CONGES_DEPASSEMENT: (wx.Bitmap(GetBitmapFile("icone_conges_depassement.png"), wx.BITMAP_TYPE_PNG), STATE_LABELS[CONGES_DEPASSEMENT]),
                      CONGES_SANS_SOLDE: (wx.Bitmap(GetBitmapFile("icone_conges_sans_solde.png"), wx.BITMAP_TYPE_PNG), STATE_LABELS[CONGES_SANS_SOLDE]),
                      }

    BULLE_BITMAP = wx.Bitmap(GetBitmapFile("bulle.png"))
except:
    # a cause des nonreg tests
    pass


def GetPlanningWidth():
    return (database.creche.affichage_max - database.creche.affichage_min) * (60 // BASE_GRANULARITY) * config.column_width


class BaseWxPythonLine:
    def clone(self):
        class Clone(BaseWxPythonLine, BasePlanningLine):
            pass
        clone = Clone(self.label, [timeslot for timeslot in self.timeslots], options=self.options)
        clone.reference = self.reference
        return clone

    def draw(self, dc):
        self.draw_grid(dc)
        if self.reference:
            for timeslot in self.reference.timeslots:
                if timeslot.activity.mode == 0:
                    r, g, b, t, s = database.creche.states[0].couleur
                    try:
                        dc.SetPen(wx.Pen(wx.Colour(r, g, b, wx.ALPHA_OPAQUE)))
                        dc.SetBrush(wx.Brush(wx.Colour(r, g, b, t), s))
                    except:
                        dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
                        dc.SetBrush(wx.Brush(wx.Colour(r, g, b), s))
                    rect = wx.Rect(1 + (timeslot.debut - int(database.creche.affichage_min*(60 // BASE_GRANULARITY))) * config.column_width, 0, (timeslot.fin-timeslot.debut) * config.column_width - 1, LINE_HEIGHT//3)
                    dc.DrawRectangleRect(rect)

        timeslots = self.timeslots[:]
        if not (self.options & DRAW_VALUES):
            timeslots.sort(key=lambda slot: slot.activity.mode)

        for timeslot in timeslots:
            if not timeslot.is_checkbox():
                if self.options & DRAW_VALUES:
                    r, g, b, t, s = database.creche.states[0].couleur
                else:
                    r, g, b, t, s = timeslot.activity.couleur
                try:
                    dc.SetPen(wx.Pen(wx.Colour(r, g, b, wx.ALPHA_OPAQUE)))
                    dc.SetBrush(wx.Brush(wx.Colour(r, g, b, t), s if s != 50 else 100))
                except:
                    dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
                    dc.SetBrush(wx.Brush(wx.Colour(r, g, b), s))
                rect = wx.Rect(1 + (
                timeslot.debut - int(database.creche.affichage_min * (60 // BASE_GRANULARITY))) * config.column_width, 0,
                               (timeslot.fin - timeslot.debut) * config.column_width - 1, LINE_HEIGHT - 1)
                dc.DrawRoundedRectangleRect(rect, 3)
                if self.options & DRAW_VALUES and timeslot.value is not None:
                    dc.DrawText(str(timeslot.value), rect.GetX() + rect.GetWidth() // 2 - 4 * len(str(timeslot.value)), 7)

        # Commentaire sur la ligne
        if self.commentaire:
            dc.SetPen(wx.BLACK_PEN)
            dc.DrawText(self.commentaire, 50, 7)

    def draw_grid(self, dc):
        dc.SetPen(wx.WHITE_PEN)
        dc.SetBrush(wx.WHITE_BRUSH)

        affichage_min = int(database.creche.affichage_min * 60 // BASE_GRANULARITY)
        affichage_max = int(database.creche.affichage_max * 60 // BASE_GRANULARITY)

        if affichage_min % (database.creche.granularite // BASE_GRANULARITY):
            heure = affichage_min + (database.creche.granularite // BASE_GRANULARITY) - affichage_min % (database.creche.granularite // BASE_GRANULARITY)
        else:
            heure = affichage_min

        while heure <= affichage_max:
            x = (heure - affichage_min) * config.column_width
            if heure % (60 // BASE_GRANULARITY) == 0:
                dc.SetPen(wx.GREY_PEN)
            else:
                dc.SetPen(wx.LIGHT_GREY_PEN)
            dc.DrawLine(x, 0, x, LINE_HEIGHT)
            heure += database.creche.granularite // BASE_GRANULARITY

        if self.widget.parent.plages_fermeture or self.widget.parent.plages_insecables:
            dc.SetPen(wx.LIGHT_GREY_PEN)
            dc.SetBrush(wx.LIGHT_GREY_BRUSH)
            for debut, fin in self.widget.parent.plages_fermeture:
                dc.DrawRectangle(1 + (debut - affichage_min) * config.column_width, 0, (fin - debut) * config.column_width - 1, LINE_HEIGHT)
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.SetBrush(wx.Brush(wx.Colour(250, 250, 0, 100)))
            for debut, fin in self.widget.parent.plages_insecables:
                dc.DrawRectangle(1 + (debut - affichage_min) * config.column_width, 0, (fin - debut) * config.column_width - 1, LINE_HEIGHT)

    def draw_label(self, dc):
        if self.sublabel is None:
            font = wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL)
            dc.SetFont(font)
            dc.DrawText(self.label, 5, 6)
        else:
            font = wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL)
            dc.SetFont(font)
            dc.DrawText(self.line.label, 5, 4)
            font = wx.Font(6, wx.SWISS, wx.NORMAL, wx.NORMAL)
            dc.SetFont(font)
            dc.DrawText(self.line.sublabel, 5, 16)

    def update_button(self, button):
        bitmap, tooltip = BUTTON_BITMAPS[self.state]
        button.SetBitmapLabel(bitmap)
        button.SetToolTip(wx.ToolTip(tooltip))
        button.Show(True)

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def get_states(self):
        return [PRESENT, ABSENT]


class WxPlanningSeparator(BasePlanningSeparator, BaseWxPythonLine):
    def draw_label(self, dc):
        try:
            dc.SetPen(wx.Pen(wx.Colour(0, 0, 0, wx.ALPHA_OPAQUE)))
            dc.SetBrush(wx.Brush(wx.Colour(128, 128, 128, 128), wx.SOLID))
        except:
            dc.SetPen(wx.Pen(wx.Colour(0, 0, 0)))
            dc.SetBrush(wx.Brush(wx.Colour(128, 128, 128), wx.SOLID))
        rect = wx.Rect(2, 4, 125, LINE_HEIGHT - 8)
        dc.DrawRectangleRect(rect)
        font = wx.Font(10, wx.SWISS, wx.BOLD, wx.BOLD)
        dc.SetFont(font)
        dc.DrawText(self.label, 5, 8)

    def update_button(self, button):
        button.Hide()

    def draw(self, dc):
        self.draw_grid(dc)


class NumberPlanningLine(BasePlanningLine, BaseWxPythonLine):
    def draw(self, dc):
        self.draw_grid(dc)
        pos = -2
        debut = int(database.creche.affichage_min * (60 // BASE_GRANULARITY))
        fin = int(database.creche.affichage_max * (60 // BASE_GRANULARITY))
        x = debut
        v = 0
        a = 0
        while x <= fin:
            if x == fin:
                nv = 0
            else:
                nv = self.array[x][0]
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
                    dc.DrawText(s, pos + 4 - 4*len(s) + (float(x+a)//2-debut)*config.column_width, 7)
                a = x
                if nv:
                    v = nv
                else:
                    v = 0
            x += 1


class PlanningLineGrid(BufferedWindow):
    def __init__(self, parent, line, pos):
        self.parent = parent
        self.line = line
        self.temp_line = None
        self.options = parent.parent.options
        self.activity_combobox = parent.parent.activity_combobox
        self.value, self.state = None, None
        self.width = GetPlanningWidth() + 1
        BufferedWindow.__init__(self, parent, pos=pos, size=(self.width, LINE_HEIGHT))
        self.SetBackgroundColour(wx.WHITE)
        if not (self.options & READ_ONLY or config.readonly):
            self.SetCursor(wx.StockCursor(wx.CURSOR_PENCIL))        
            self.Bind(wx.EVT_LEFT_DOWN, self.onLeftButtonDown)
            self.Bind(wx.EVT_LEFT_UP, self.OnLeftButtonUp)
            self.Bind(wx.EVT_MOTION, self.onLeftButtonDragging)

    def SetLine(self, line):
        self.line = line
        self.UpdateDrawing()
            
    def UpdateContents(self):
        self.UpdateDrawing()
            
    def Draw(self, dc):
        dc.BeginDrawing()
        dc.SetBackground(wx.Brush(wx.WHITE))
        dc.Clear()
        try:
            dc = wx.GCDC(dc)
        except:
            pass
        # les présences
        if self.temp_line:
            line = self.temp_line
        else:
            line = self.line            
        line.draw(dc)
        dc.EndDrawing()
        
    @staticmethod
    def __get_pos(x):
        if x > 0:
            x -= 1
        return int(database.creche.affichage_min * (60 // BASE_GRANULARITY) + (x // config.column_width))

    def onLeftButtonDown(self, event):
        posX = self.__get_pos(event.GetX())
        self.curStartX = (posX // (database.creche.granularite // BASE_GRANULARITY)) * (database.creche.granularite // BASE_GRANULARITY)
        # TODO config.readonly pourrait empecher l'evenement
        if not self.line.readonly and not config.readonly:
            # TODO plutôt notifier d'un changement dans la combo
            if self.activity_combobox:
                self.activity = self.activity_combobox.activity
            else:
                self.activity = database.creche.states[0]
            for timeslot in self.line.timeslots:
                if ((self.line.options & DRAW_VALUES) or timeslot.activity == self.activity) and timeslot.debut <= posX <= timeslot.fin:
                    self.state = -1
                    break
            else:
                self.state = 1
            self.onLeftButtonDragging(event)

    def GetPlagesSelectionnees(self):
        start, end = min(self.curStartX, self.curEndX), max(self.curStartX, self.curEndX) + database.creche.granularite // BASE_GRANULARITY
        
        affichage_min = int(database.creche.affichage_min * (60 // BASE_GRANULARITY))
        affichage_max = int(database.creche.affichage_max * (60 // BASE_GRANULARITY))
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

    def onLeftButtonDragging(self, event):
        if self.state is not None:
            posX = self.__get_pos(event.GetX())
            self.curEndX = (posX // (database.creche.granularite // BASE_GRANULARITY)) * (database.creche.granularite // BASE_GRANULARITY)
            
            clone = self.line.clone()
            clone.widget = self.parent
            for start, end in self.GetPlagesSelectionnees():                        
                if self.state > 0:
                    clone.set_activity(start, end, self.activity)
                else:
                    clone.clear_activity(start, end, self.activity)
            
            self.temp_line = clone
            self.UpdateDrawing()

    print("TODO Historique sur saisie planning")
    def OnLeftButtonUp(self, _):
        self.temp_line = None
        if self.state is not None:
            line = self.line
            history.Append(None)
            # history.Append([Call(line.Restore, line.Backup())])
            
            if self.state > 0:
                if self.activity_combobox:
                    for start, end in self.GetPlagesSelectionnees():
                        line.set_activity(start, end, self.activity)
                else:
                    dlg = TextDialog(self, "Capacité", "10")
                    response = dlg.ShowModal()
                    dlg.Destroy()
                    if not dlg.GetText().isdigit():
                        return
                    value = int(dlg.GetText())
                    if response != wx.ID_OK or value == 0:
                        self.parent.UpdateContents()
                        self.state = None
                        self.UpdateDrawing()
                        return
                    for start, end in self.GetPlagesSelectionnees():
                        line.set_activity(start, end, value)
            else:
                for start, end in self.GetPlagesSelectionnees():                        
                    line.clear_activity(start, end, self.activity)
            
            self.parent.OnLineChanged()
            self.state = None


class SaisieHoraireDialog(wx.Dialog):
    def __init__(self, parent, line):
        wx.Dialog.__init__(self, parent, -1, "Saisie horaire", wx.DefaultPosition, wx.DefaultSize)
        self.line = line
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.fields_sizer = wx.FlexGridSizer(0, 2, 5, 10)
        self.fields_sizer.AddGrowableCol(1, 1)
        self.debut_ctrl = wx.TextCtrl(self)
        # self.debut_ctrl.SetValue(periode.debut)
        self.fields_sizer.AddMany(
            [(wx.StaticText(self, -1, "Début :"), 0, wx.ALIGN_CENTRE_VERTICAL | wx.ALL - wx.BOTTOM, 5),
             (self.debut_ctrl, 0, wx.EXPAND | wx.ALIGN_CENTRE_VERTICAL | wx.ALL - wx.BOTTOM, 5)])
        self.fin_ctrl = wx.TextCtrl(self)
        # self.fin_ctrl.SetValue(periode.fin)
        self.fields_sizer.AddMany([(wx.StaticText(self, -1, "Fin :"), 0, wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 5),
                                   (self.fin_ctrl, 0, wx.EXPAND | wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 5)])
        self.sizer.Add(self.fields_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        self.btnsizer.AddButton(btn)
        btn = wx.Button(self, wx.ID_CANCEL)
        self.btnsizer.AddButton(btn)
        self.btnsizer.Realize()
        self.sizer.Add(self.btnsizer, 0, wx.ALL, 5)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)

    @staticmethod
    def get_index(text):
        if ":" in text:
            hours, minutes = map(lambda s: s.strip(), text.split(":", 1))
        else:
            hours, minutes = text.strip(), "0"
        if not hours.isdigit() or not minutes.isdigit():
            return None
        return 12 * int(hours) + int(minutes) // 5

    def get_interval(self):
        return self.get_index(self.debut_ctrl.GetValue()), self.get_index(self.fin_ctrl.GetValue())


class PlanningLineLabel(wx.Panel):
    def __init__(self, parent, line, pos):
        wx.Panel.__init__(self, parent, -1, pos=pos, size=(LABEL_WIDTH, LINE_HEIGHT-1), style=wx.NO_BORDER)
        self.parent = parent
        self.line = line
        self.Bind(wx.EVT_PAINT, self.onPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.onLeftButtonDown)
        
    def SetLine(self, line):
        self.line = line
    
    def onPaint(self, _):
        dc = wx.PaintDC(self)
        dc.BeginDrawing()
        dc.SetTextForeground("BLACK")
        self.line.draw_label(dc)
        dc.EndDrawing()

    def onLeftButtonDown(self, _):
        dialog = SaisieHoraireDialog(self, self.line)
        response = dialog.ShowModal()
        dialog.Destroy()
        if response == wx.ID_OK:
            start, end = dialog.get_interval()
            self.line.set_activity(start, end, database.creche.states[0])
            self.parent.OnLineChanged()


class PlanningLineIcon(wx.Window):
    def __init__(self, parent, line, pos):
        wx.Window.__init__(self, parent, -1, pos=pos, size=(ICONS_WIDTH, LINE_HEIGHT-1))
        self.SetBackgroundColour(wx.WHITE)
        self.button = wx.BitmapButton(self, -1, BUTTON_BITMAPS[PRESENT][0], size=(ICONS_WIDTH, LINE_HEIGHT-1), style=wx.NO_BORDER)
        self.button.SetBackgroundColour(wx.WHITE)
        if not config.readonly:
            self.Bind(wx.EVT_BUTTON, self.OnButtonPressed, self.button)
        self.parent = parent
        self.SetLine(line)
        
    def SetLine(self, line):
        self.line = line
        self.line.update_button(self.button)

    def OnButtonPressed(self, _):
        if not self.line.readonly:
            history.Append(None)
            # TODO history.Append([Call(self.line.Restore, self.line.Backup())])
            state = PRESENCE_CAROUSSEL[self.line.get_state()]
            states = self.line.get_states()
            if state in states:
                new_state = states[(states.index(state) + 1) % len(states)]
            else:
                new_state = PRESENT
            self.line.set_state(new_state)
            self.parent.OnLineChanged()


class PlanningLineComment(wx.StaticText):
    def __init__(self, parent, line, pos):
        wx.StaticText.__init__(self, parent, -1, pos=pos, style=wx.NO_BORDER)
        self.SetLine(line)
        
    def SetLine(self, line):
        text = line.get_badge_text()
        if text:
            self.SetWindowStyle(wx.BORDER)
            self.SetLabel(text)
        else:
            self.SetWindowStyle(wx.NO_BORDER)
            self.SetLabel("")


class PlanningLineWidget(wx.Window):
    def __init__(self, parent, line, pos, size):
        wx.Window.__init__(self, parent, pos=pos, size=size)
        self.SetBackgroundColour(wx.WHITE)
        self.parent = parent
        self.line = line
        self.line.widget = self
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
            self.status_icon = PlanningLineIcon(self, self.line, pos=(self.width, 0))
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
            checkbox.Enable(not config.readonly)
            checkbox.activite = activite
            self.Bind(wx.EVT_CHECKBOX, self.OnActiviteCheckbox, checkbox)
            self.width += CHECKBOX_WIDTH
            self.activites_checkboxes.append(checkbox)
        self.UpdateActivites()
        
    def OnLineChanged(self):
        self.parent.OnPlanningChanged(self.line)
        self.UpdateContents()
        if self.parent.parent.summary_panel:
            self.parent.parent.summary_panel.UpdateContents()

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
            if self.line is None or not self.line.options & ACTIVITES:
                checkbox.Hide()
            elif isinstance(self.line, BasePlanningSeparator):
                checkbox.Show()
                checkbox.Disable()
            else:
                checkbox.Show()
                checkbox.Enable(not config.readonly)
                checkbox.SetValue(self.line.is_timeslot_checked(checkbox.activite))

    def UpdateBulle(self):
        if self.line.commentaire is None:
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
        self.line.widget = self
        self.UpdateContents()
        
    def OnActiviteCheckbox(self, event):
        checkbox = event.GetEventObject()
        if not (self.line.readonly or config.readonly):
            if event.Checked():
                history.Append(None)
                self.line.set_checkbox(checkbox.activite)
            else:
                history.Append(None)
                self.line.clear_checkbox(checkbox.activite)
            self.OnLineChanged()

    def OnCommentButtonPressed(self, _):
        if not (self.line.readonly or config.readonly):
            dlg = TextDialog(self, "Commentaire", self.line.commentaire)
            response = dlg.ShowModal()
            dlg.Destroy()
            if response == wx.ID_OK:
                self.line.set_comment(dlg.GetText())
                self.UpdateContents()


class PlanningInternalPanel(wx.Window):
    def __init__(self, parent, activity_combobox, options):
        wx.Window.__init__(self, parent)
        self.parent = parent.parent
        self.activity_combobox = activity_combobox
        self.options = options
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

    def OnPlanningChanged(self, line):
        self.parent.OnPlanningChanged(line)

    def SetInfo(self, info):
        self.info = info
        
    def Disable(self, info):
        self.SetInfo(info)
        self.SetLines([])
        
    def SetLines(self, lines):
        self.activites = database.creche.get_activites_sans_horaires()
            
        if counters['plages'] > self.plages_observer:
            self.plages_observer = counters['plages']
            self.plages_fermeture = database.creche.GetPlagesArray(PLAGE_FERMETURE, conversion=True)
            self.plages_insecables = database.creche.GetPlagesArray(PLAGE_INSECABLE, conversion=True)
        
        previous_count = len(self.lines)
        self.lines = lines
        count = len(self.lines)

        if count > previous_count:
            for i in range(previous_count):
                self.line_widgets[i].SetLine(lines[i])
            for i in range(previous_count, count):
                widget = PlanningLineWidget(self, lines[i], pos=(0, i*LINE_HEIGHT), size=(-1, self.line_height))
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
        if self.tri_planning != database.creche.tri_planning:
            self.tri_planning = database.creche.tri_planning
            if database.creche.tri_planning & TRI_LIGNES_CAHIER:
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
            dc.DrawRotatedText(self.info, (width-700)//2, 350+(height-350)//2, 40)
            dc.EndDrawing()
        elif database.creche.tri_planning & TRI_LIGNES_CAHIER:
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
    def __init__(self, parent, activity_combobox, options):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, style=wx.SUNKEN_BORDER)
        self.parent = parent
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.internal_panel = PlanningInternalPanel(self, activity_combobox, options)
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
        
    def OnSize(self, _):
        self.internal_panel.UpdateSize()


class PlanningSummaryPanel(BufferedWindow):
    def __init__(self, parent, options):
        self.parent = parent
        self.options = options
        self.activities_count = 0
        self.activites = collections.OrderedDict()
        self.activites_sans_horaires = collections.OrderedDict()
        BufferedWindow.__init__(self, parent, size=(-1, 2+20*self.activities_count))

    def UpdateContents(self):
        self.activites, self.activites_sans_horaires = self.GetParent().get_summary()
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
            keys = self.activites.keys()
            index = 0
            for key in keys:
                if self.activites[key]:
                    dc.DrawText(key.label, 5, 6 + index * 20)
                    self.DrawLine(dc, index, key)
                    index += 1
            
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
                    dc.DrawText(text, rect.left + (rect.width - w) // 2, rect.top + (rect.height - h) // 2)
            
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
                rect = wx.Rect(x, 4, w + 6, 15)
                dc.DrawRectangleRect(rect)
                dc.DrawText(text, rect.left + (rect.width - w) // 2, rect.top + (rect.height - h) // 2)
            
        dc.EndDrawing()

    def DrawLine(self, dc, index, key):
        pos = LABEL_WIDTH
        if not self.options & NO_ICONS:
            pos += ICONS_WIDTH

        debut = int(database.creche.affichage_min * (60 // BASE_GRANULARITY))

        timeslots = self.activites[key]
        for timeslot in timeslots:
            if timeslot.debut is not None:
                if hasattr(timeslot, "overflow") and timeslot.overflow:
                    r, g, b, t, s = database.creche.states[0].couleur_supplement
                else:
                    r, g, b, t, s = database.creche.states[0].couleur if key == PRESENCE_SALARIE else key.couleur

                try:
                    dc.SetPen(wx.Pen(wx.Colour(r, g, b, wx.ALPHA_OPAQUE)))
                    dc.SetBrush(wx.Brush(wx.Colour(r, g, b, t), s))
                except:
                    dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
                    dc.SetBrush(wx.Brush(wx.Colour(r, g, b), s))

                rect = wx.Rect(pos + 3 + (timeslot.debut - debut) * config.column_width, 2 + index * 20, (timeslot.fin - timeslot.debut) * config.column_width - 1, 19)
                dc.DrawRoundedRectangleRect(rect, 3)
                text = str(timeslot.value)
                w, h = dc.GetTextExtent(text)
                dc.DrawText(text, rect.left + (rect.width - w) / 2, rect.top + (rect.height - h) / 2)


class PlanningWidget(wx.Panel):
    def __init__(self, parent, activity_combobox=None, options=0):
        wx.Panel.__init__(self, parent, id=-1, style=wx.LB_DEFAULT)
        self.options = options
        self.lines = []
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.scale_window = wx.Window(self, -1, size=(-1, 25))
        self.sizer.Add(self.scale_window, 0, wx.EXPAND)
        self.internal_panel = PlanningScrollPanel(self, activity_combobox, options)
        self.sizer.Add(self.internal_panel, 1, wx.EXPAND)
        if not (options & NO_BOTTOM_LINE):
            self.summary_panel = PlanningSummaryPanel(self, options)
            self.sizer.Add(self.summary_panel, 0, wx.EXPAND)
        else:
            self.summary_panel = None
        self.SetSizer(self.sizer)
        self.sizer.Layout()
        self.scale_window.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnPlanningChanged(self, line):
        pass

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

    def get_summary(self):
        return get_lines_summary(self.lines)

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
        affichage_min = int(database.creche.affichage_min * (60 // BASE_GRANULARITY))
        affichage_max = int(database.creche.affichage_max * (60 // BASE_GRANULARITY))
        if affichage_min % (database.creche.granularite // BASE_GRANULARITY):
            heure = affichage_min + (database.creche.granularite // BASE_GRANULARITY) - affichage_min % (database.creche.granularite // BASE_GRANULARITY)
        else:
            heure = affichage_min
        offset = 2
        if not self.options & NO_LABELS:
            offset += LABEL_WIDTH
        if not self.options & NO_ICONS:
            offset += ICONS_WIDTH
        while heure <= affichage_max:
            x = offset + (heure - affichage_min) * config.column_width
            if heure % (60 // BASE_GRANULARITY) == 0:
                dc.DrawLine(x, 20, x, 12)
                dc.DrawText(str(int(round(heure//(60 // BASE_GRANULARITY))))+"h", x - 3, 0)
            else:
                dc.DrawLine(x, 20, x, 15)
            heure += database.creche.granularite // BASE_GRANULARITY
        
        # les noms des activités en oblique
        if self.options & ACTIVITES:
            activites = database.creche.get_activites_sans_horaires()
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
