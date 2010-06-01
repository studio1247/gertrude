#!/usr/bin/env python
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

import __builtin__
import os, sys, imp, time, shutil, glob
import wx, wx.lib.wordwrap
from config import *
from startdialog import StartDialog
try:
  import winsound
except:
  pass

# Don't remove these 2 lines (mandatory for py2exe)
import controls, zipfile, xml.dom.minidom, wx.html, ooffice
sys.path.insert(0, ".")

VERSION = '0.76'

class HtmlListBox(wx.HtmlListBox):
    def __init__(self, parent, id, size, style):
        wx.HtmlListBox.__init__(self, parent, id, size=size, style=style)
        self.items = []

    def OnGetItem(self, n):
        return self.items[n]

    def Append(self, html):
        self.items.append(html)

    def Draw(self):
        self.SetItemCount(len(self.items))
        self.SetSelection(0)
        self.SetFocus()

class Listbook(wx.Panel):
    def __init__(self, parent, id, style, pos):
        wx.Panel.__init__(self, parent, id=id, pos=pos)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.list_box = HtmlListBox(self, -1, size=(155, 250), style=wx.BORDER_SUNKEN)
        self.sizer.Add(self.list_box, 0, wx.EXPAND)
        self.list_box.Bind(wx.EVT_LISTBOX, self.OnPageChanged)
        self.panels = []
        self.active_panel = None
        self.SetSizer(self.sizer)

    def AddPage(self, panel, bitmap):
        self.list_box.Append('<center><img src="%s"></center>' % bitmap)
        self.panels.append(panel)
        self.sizer.Add(panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        if len(self.panels) == 1:
            self.active_panel = panel
        else:
            self.sizer.Show(panel, False)

    def Draw(self):
        self.list_box.Draw()

    def OnPageChanged(self, event):
        if self.active_panel:
            self.sizer.Show(self.active_panel, False)
        self.active_panel = self.panels[event.GetSelection()]
        self.sizer.Show(self.active_panel, True)
        self.sizer.Layout()

    def GetPage(self, n):
        return self.panels[n]

class GertrudeListbook(Listbook):
    def __init__(self, parent, id=-1):
        Listbook.__init__(self, parent, id=-1, style=wx.LB_DEFAULT, pos=(10, 10))
        panels = []
        for filename in glob.glob('panel_*.py'):
            module_name = os.path.split(filename)[1][:-3]
            print 'Import de %s.py' % module_name
            f, filename, description = imp.find_module(module_name, [os.getcwd()])
            module = imp.load_module(module_name, f, filename, description)
            panels.extend([tmp(self) for tmp in module.panels])
        panels.sort(lambda a, b: a.index-b.index)
        for panel in panels:
            if panel.profil & profil:
                self.AddPage(panel, panel.bitmap)
        self.Draw()

    def OnPageChanged(self, event):
        Listbook.OnPageChanged(self, event)
        self.GetPage(event.GetSelection()).UpdateContents()
        event.Skip()

    def UpdateContents(self):
        self.GetPage(self.list_box.GetSelection()).UpdateContents()

class GertrudeFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Gertrude v%s" % VERSION, wx.DefaultPosition, (920, 600))

        # Icon
        icon = wx.Icon('./bitmaps/gertrude.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        # Statusbar
        self.CreateStatusBar()

        # MenuBar
        menuBar = wx.MenuBar()
        menu = wx.Menu()
        menu.Append(101, "&Enregistrer\tCtrl+S", u"Enregistre")
        self.Bind(wx.EVT_MENU, self.OnSave, id=101)
        menu.Append(102, "&Fermer\tAlt+F4", u"Ferme la fenêtre")
        self.Bind(wx.EVT_MENU, self.OnExit, id=102)
        menuBar.Append(menu, "&Fichier")
        menu = wx.Menu()
        menu.Append(201, "&Annuler\tCtrl+Z", u"Annule l'action précédente")
        self.Bind(wx.EVT_MENU, self.OnUndo, id=201)
        menuBar.Append(menu, "&Edition")
        menu = wx.Menu()
        menu.Append(301, "A &propos de Gertrude", u"A propos de Gertrude")
        self.Bind(wx.EVT_MENU, self.OnAbout, id=301)
        menuBar.Append(menu, "&?")
        self.SetMenuBar(menuBar)
        
        # Inside
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel = wx.Panel(self, -1)
        sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer)

        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.listbook = GertrudeListbook(panel)
        sizer2.Add(self.listbook, 1, wx.EXPAND)
        panel.SetSizer(sizer2)

        self.Bind(wx.EVT_CLOSE, self.OnExit)

    def OnSave(self, evt):
        self.SetStatusText("Enregistrement en cours ...")
        Save(ProgressHandler(self.SetStatusText))
        self.SetStatusText("")

    def OnExit(self, evt):
        self.SetStatusText("Fermeture en cours ...")
        if len(history) > 0:
            dlg = wx.MessageDialog(self, "Voulez-vous enregistrer les changements ?", "Gertrude", wx.YES_NO|wx.YES_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
        else:
            result = wx.ID_NO

        if result == wx.ID_CANCEL:
            self.SetStatusText("")
            return
        elif result == wx.ID_YES:
            Save(ProgressHandler(self.SetStatusText))
        else:
            Restore(ProgressHandler(self.SetStatusText))
        Exit(ProgressHandler(self.SetStatusText))
        self.Destroy()

    def OnUndo(self, event):
        if history.Undo():
            self.listbook.UpdateContents()
        else:
            try:
                winsound.MessageBeep()
            except:
                pass

    def OnAbout(self, event):
        info = wx.AboutDialogInfo()
        info.Name = "Gertrude"
        info.Version = VERSION
        info.Copyright = "(C) 2005-2009 Bertrand Songis"
        info.Description = wx.lib.wordwrap.wordwrap(
            u"Gertrude est un logiciel libre adapté aux besoins de gestion des crèches et haltes-garderies en France.\n\n"
            u"Développé pour une crèche parentale rennaise début 2005, il a été adapté de 2007 à 2009 pour d’autres crèches ; il est désormais accessible à tous.\n\n"
            u"Il permet l'édition de contrats, la gestion de planning, la facturation, les appels de cotisations, les attestations de paiement, les rapports de fréquentation, la synthèse des contributions familiales.\n\n",
            350, wx.ClientDC(self))
        info.WebSite = ("http://gertrude.creches.free.fr", "Gertrude")
        info.Contributors = [ "Mairie des Orres" ]
        info.License = wx.lib.wordwrap.wordwrap(
            "Gertrude is free software; you can redistribute it and/or modify "
            "it under the terms of the GNU General Public License as published by "
            "the Free Software Foundation; either version 2 of the License, or "
            "(at your option) any later version.\n\n"
        
            "Gertrude is distributed in the hope that it will be useful, "
            "but WITHOUT ANY WARRANTY; without even the implied warranty of "
            "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the "
            "GNU General Public License for more details.\n\n"
        
            "You should have received a copy of the GNU General Public License "
            "along with Gertrude; if not, write to the Free Software "
            "Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA",
            350, wx.ClientDC(self))

        wx.AboutBox(info)

class MyApp(wx.App):
    def OnInit(self):
        start_dialog = StartDialog(GertrudeFrame)
        start_dialog.Show(True)
        return True

if __name__ == '__main__':
    app = MyApp(False)
    app.MainLoop()

