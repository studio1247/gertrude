# -*- coding: cp1252 -*-

import wx
import wx.lib.scrolledpanel
import datetime
from common import *

PRENOMS_WIDTH = 80 # px
BUTTONS_WIDTH = 34 # px

class GPanel(wx.Panel):
    def __init__(self, parent, title):
        wx.Panel.__init__(self, parent, id=-1, style=wx.LB_DEFAULT)
	self.sizer = wx.BoxSizer(wx.VERTICAL)
	sizer = wx.BoxSizer(wx.HORIZONTAL)
        st = wx.StaticText(self, -1, title, size=(100, 28), style=wx.BORDER_SUNKEN)
        st.SetBackgroundColour(wx.Colour(10, 36, 106))
        st.SetBackgroundStyle(wx.BG_STYLE_COLOUR)
        st.SetForegroundColour(wx.Colour(255, 255, 255))
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        st.SetFont(font)
	sizer.Add(st, 1, wx.EXPAND)
	self.sizer.Add(sizer, 0, wx.EXPAND | wx.BOTTOM, 5)
	self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        
    def UpdateContents(self):
        pass

class DayTabWindow(wx.Window):
    pxHeure = 40
    pxBebe = 30
    def __init__(self, parent, profil, inscrits, date, *args, **kwargs):
        wx.Window.__init__(self, parent, size=((heureMaximum-heureOuverture) * self.pxHeure + 1,self.pxBebe * len(inscrits) + 1), *args, **kwargs)
        self.parent = parent
        self.profil = profil
        self.inscrits = inscrits
        self.SetBackgroundColour(wx.WHITE)
        self.valeur_selection = -1
        self.date = date

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        if (self.profil & PROFIL_SAISIE_PRESENCES) or date > datetime.date.today():
            self.SetCursor(wx.StockCursor(wx.CURSOR_PENCIL))        
            self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftButtonEvent)
            self.Bind(wx.EVT_LEFT_UP, self.OnLeftButtonEvent)
            self.Bind(wx.EVT_MOTION, self.OnLeftButtonEvent)
        
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        self.PrepareDC(dc)
        self.DoDrawing(dc)

    def DrawPresence(self, ligne, presence, dc = None):
        if not dc:
            dc = wx.ClientDC(self)
            self.PrepareDC(dc)
            
        dc.SetPen(wx.TRANSPARENT_PEN)
        green_brush = [ wx.Brush(wx.Color(5, 203, 28)), wx.Brush(wx.Color(150, 229, 139)) ]
        red_brush = [ wx.Brush(wx.Color(203, 5, 28)), wx.Brush(wx.Color(229, 150, 139)) ]
        for i in range(int((heureMaximum - heureOuverture) * 4)):
            if presence.value == PRESENT and presence.details[i]:
                if presence.details[i] == 2:
                    previsionnel = 1
                else:
                    previsionnel = presence.previsionnel
                if i < (heureFermeture - heureOuverture) * 4:
                    brush = green_brush[previsionnel]
                else:
                    brush = red_brush[previsionnel]
                dc.SetBrush(brush)
            else:
                dc.SetBrush(wx.WHITE_BRUSH)
            dc.DrawRectangle(1 + i * self.pxHeure / 4, 1 + ligne * self.pxBebe, (self.pxHeure / 4) - 1, self.pxBebe - 1)

    def DoDrawing(self, dc, printing=False):
        dc.BeginDrawing()
       
        # le quadrillage
        dc.SetPen(wx.GREY_PEN)
        dc.SetBrush(wx.WHITE_BRUSH)
        for i in range(len(self.inscrits)+1):
            dc.DrawLine(0, i*self.pxBebe, (heureMaximum-heureOuverture) * self.pxHeure + 1, i*self.pxBebe)

        heure = heureOuverture
        while heure <= heureMaximum:
            x = (heure - heureOuverture ) * self.pxHeure
            if heure == int(heure):
                dc.SetPen(wx.GREY_PEN)
            else:
                dc.SetPen(wx.LIGHT_GREY_PEN)
            dc.DrawLine(x, 0,  x, self.pxBebe * len(self.inscrits))
            heure += 0.25

        # les presences
        for i, inscrit in enumerate(self.inscrits):
            if self.date in inscrit.presences:
                presence = inscrit.presences[self.date]
            else:
                presence = inscrit.getPresenceFromSemaineType(self.date)
            self.DrawPresence(i, presence, dc)
            
        dc.EndDrawing()
    
    def __get_pos(self, x, y):
        posX = int(4 * x / self.pxHeure)
        posY = int(y / self.pxBebe)
        return posX, posY

    def OnLeftButtonEvent(self, event):            
        x = event.GetX()
        y = event.GetY()
# tests au cas ou ...            if self.curStartX < 4 * (heureMaximum-heureOuverture) and self.curStartY < len(self.inscrits):

        if event.LeftDown():
            self.curStartX, self.curStartY = self.__get_pos(x, y)
            inscrit = self.inscrits[self.curStartY]
            if self.date not in inscrit.presences:
                presence = inscrit.getPresenceFromSemaineType(self.date)
                presence.create()
                inscrit.presences[self.date] = presence
            else:
                presence = inscrit.presences[self.date]

            if presence.value != PRESENT:
                presence.value = PRESENT
                presence.details = [0] * int((heureMaximum-heureOuverture) * 4)
            self.presence = Presence(inscrit, self.date, presence.previsionnel, presence.value, creation=False)
            self.presence.original = presence
            if self.date <= datetime.date.today() and presence.previsionnel:
                presence.previsionnel = self.presence.previsionnel = 0
                self.presence.sel_details = [tmp * 2 for tmp in presence.details]
            else:
                self.presence.sel_details = presence.details[:]
            if self.presence.sel_details[self.curStartX] == 1:
                self.valeur_selection = 0
            else:
                self.valeur_selection = 1

            self.parent.UpdateButton(self.curStartY) # TODO pas toujours

        if (event.LeftDown() or event.Dragging()) and self.valeur_selection != -1:
            self.curEndX, self.curEndY = self.__get_pos(x, y)
            if self.curEndY == self.curStartY:
                start, end = min(self.curStartX, self.curEndX), max(self.curStartX, self.curEndX)
                self.presence.details = self.presence.sel_details[:]
                self.presence.details[start:end+1] = [self.valeur_selection] * (end - start + 1)
                self.DrawPresence(self.curStartY, self.presence)

        elif event.LeftUp() and self.valeur_selection != -1:
            if self.curStartY == self.curEndY:
                start, end = min(self.curStartX, self.curEndX), max(self.curStartX, self.curEndX)
                presence = self.presence.original
                self.presence.details = self.presence.sel_details[:]
                self.presence.details[start:end+1] = [self.valeur_selection] * (end - start + 1)
                for i in range(len(self.presence.details)):
                    if self.presence.details[i] == 2:
                        self.presence.details[i] = 0
                           
                if self.presence.Total() == 0:
                    presence.value = VACANCES
                    presence.details = None
                    self.parent.UpdateButton(self.curStartY)
                else:
                    presence.details = self.presence.details
            else:
                presence = self.presence.original
            self.valeur_selection = -1
            self.DrawPresence(self.curStartY, presence)

class PresencesPanel(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent, profil, inscrits, date = datetime.date.today()):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent, -1, style=wx.SUNKEN_BORDER)
        self.profil = profil
        self.all_inscrits = inscrits
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
	self.prenoms = wx.Window(self, -1, size=(PRENOMS_WIDTH, 0))
	self.sizer.Add(self.prenoms)
	self.buttons_sizer = wx.BoxSizer(wx.VERTICAL)
	self.sizer.Add(self.buttons_sizer, 0, wx.RIGHT, 2)
        self.tab_window = DayTabWindow(self, profil, inscrits, date=date)
	self.sizer.Add(self.tab_window)
        self.date = date
        self.bmp = range(6)
        self.bmp[0] = wx.Bitmap("./bitmaps/icone_presence.png", wx.BITMAP_TYPE_PNG)
        self.bmp[1] = wx.Bitmap("./bitmaps/icone_presence_prev.png", wx.BITMAP_TYPE_PNG)
        self.bmp[2] = wx.Bitmap("./bitmaps/icone_vacances.png", wx.BITMAP_TYPE_PNG)
        self.bmp[3] = wx.Bitmap("./bitmaps/icone_vacances.png", wx.BITMAP_TYPE_PNG) # pas utilise pour le moment
        self.bmp[4] = wx.Bitmap("./bitmaps/icone_maladie.png", wx.BITMAP_TYPE_PNG)
        self.bmp[5] = wx.Bitmap("./bitmaps/icone_maladie.png", wx.BITMAP_TYPE_PNG) # pas utilise pour le moment
	self.inscrits = []
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
        if presence.previsionnel and presence.value == 0 and self.date <= datetime.date.today():
            presence.previsionnel = 0
        elif presence.value == PRESENT or presence.value == VACANCES:
            presence.value += 1
        elif presence.value == MALADE:
            new_presence = inscrit.getPresenceFromSemaineType(self.date)
            presence.value, presence.details = new_presence.value, new_presence.details
            if self.date <= datetime.date.today():
              presence.previsionnel = 0
            else:
              presence.previsionnel = 1

        self.UpdateButton(button.inscrit)
        self.tab_window.DrawPresence(button.inscrit, presence)

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
        for inscrit in self.all_inscrits:
            if inscrit.getInscription(self.date) is not None:
                self.inscrits.append(inscrit)
        new = len(self.inscrits)
        self.tab_window.inscrits = self.inscrits
        if self.date in jours_feries:
            self.prenoms.SetMinSize((0, 0))
            self.tab_window.SetMinSize((0, 0))
            self.buttons_sizer.ShowItems(0)
        else:
            self.prenoms.SetMinSize((PRENOMS_WIDTH, self.tab_window.pxBebe * len(self.inscrits) + 1))
            self.tab_window.SetMinSize((int((heureMaximum-heureOuverture) * self.tab_window.pxHeure + 1), self.tab_window.pxBebe * len(self.inscrits) + 1))
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
                dc.DrawText(GetInscritId(inscrit, self.inscrits), 10, 5 + i * self.tab_window.pxBebe)
        
        dc.EndDrawing()

    def SetDate(self, date):
        self.date = date
        self.tab_window.date = date
        self.UpdateContents()

class DayPanel(wx.Panel):
    def __init__(self, parent, profil, inscrits, date):
        wx.Panel.__init__(self, parent, id=-1, style=wx.LB_DEFAULT)
	self.sizer = wx.BoxSizer(wx.VERTICAL)
	self.echelle = wx.Window(self, -1, size=(0, 25))
	self.sizer.Add(self.echelle, 0, wx.EXPAND)
        self.presences_panel = PresencesPanel(self, profil, inscrits, date)
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
        heure = heureOuverture
        while heure <= heureMaximum:
            x = PRENOMS_WIDTH + BUTTONS_WIDTH + (heure - heureOuverture ) * self.presences_panel.tab_window.pxHeure
            if heure == int(heure):
                dc.DrawLine(x, 20, x, 12)
                dc.DrawText(str(int(heure))+"h", x - 3, 0)
            else:
                dc.DrawLine(x, 20, x, 15)
            heure += 0.25
            
        dc.EndDrawing()

class PlanningPanel(GPanel):
    def __init__(self, parent, profil, inscrits):
        GPanel.__init__(self, parent, u'Présences enfants')
        self.inscrits = inscrits
        
        # La combobox pour la selection de la semaine
        self.combobox = wx.Choice(self, -1)
	self.sizer.Add(self.combobox)
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
	self.sizer.Add(self.notebook, 1, wx.EXPAND)
        for week_day in range(5):
            day = first_monday + datetime.timedelta(semaine * 7 + week_day)
            title = days[week_day] + " " + str(day.day) + " " + months[day.month - 1] + " " + str(day.year)
            self.notebook.AddPage(DayPanel(self.notebook, profil, inscrits, day), title)
        
        self.Bind(wx.EVT_CHOICE, self.EvtChoice, self.combobox)

    def EvtChoice(self, evt):
        cb = evt.GetEventObject()
        monday = cb.GetClientData(cb.GetSelection())
        for week_day in range(5):
            day = monday + datetime.timedelta(week_day)
	    note = self.notebook.GetPage(week_day)
            self.notebook.SetPageText(week_day, days[week_day] + " " + str(day.day) + " " + months[day.month - 1] + " " + str(day.year))
            note = self.notebook.GetPage(week_day)
            if day in jours_feries:
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
