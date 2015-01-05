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
import os, sys, imp, time, locale, shutil, glob, thread, urllib2
import wx, wx.lib.wordwrap
from wx.lib import masked
from startdialog import StartDialog
from config import Liste, Load, Update, Save, Restore, Exit, ProgressHandler
from functions import GetBitmapFile, today
from alertes import CheckAlertes
try:
    import winsound
except:
    pass

# Don't remove these 2 lines (mandatory for py2exe)
import controls, zipfile, xml.dom.minidom, wx.html, ooffice

VERSION = '0.97b'

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
            
    def ChangePage(self, position):
        self.list_box.SetSelection(position)
        class MyEvent(object):
            def __init__(self, selection):
                self.selection = selection
            def GetSelection(self):
                return self.selection
            def Skip(self):
                pass
        self.OnPageChanged(MyEvent(position))

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
    def __init__(self, parent, progress_handler):
        Listbook.__init__(self, parent, id=-1, style=wx.LB_DEFAULT, pos=(10, 10))
        panels = []
        import panel_inscriptions
        panels.append(panel_inscriptions.InscriptionsPanel)
        import panel_planning
        panels.append(panel_planning.PlanningPanel)
        import panel_facturation
        panels.append(panel_facturation.FacturationPanel)
        import panel_salaries
        panels.append(panel_salaries.SalariesPanel)
        import panel_tableaux_bord
        panels.append(panel_tableaux_bord.TableauxDeBordPanel)
        import panel_configuration
        panels.append(panel_configuration.ConfigurationPanel)
        for i, panel in enumerate(panels):
            if panel.profil & profil:
                progress_handler.set(10+80*i/len(panels))
                progress_handler.display(u"Chargement de l'outil %s ..." % panel.name)
                self.AddPage(panel(self), panel.bitmap)
        self.Draw()
 
    def OnPageChanged(self, event):
        Listbook.OnPageChanged(self, event)
        self.GetPage(event.GetSelection()).UpdateContents()
        event.Skip()

    def UpdateContents(self):
        self.GetPage(self.list_box.GetSelection()).UpdateContents()

class GertrudeFrame(wx.Frame):
    def __init__(self, progress_handler):
        wx.Frame.__init__(self, None, -1, "Gertrude v%s" % VERSION, wx.DefaultPosition, config.window_size)

        # Icon
        icon = wx.Icon(GetBitmapFile('gertrude.ico'), wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        # Statusbar
        self.CreateStatusBar()

        # MenuBar
        menuBar = wx.MenuBar()
        menu = wx.Menu()
        if len(config.sections) > 1:
            self.db_menu = wx.Menu()
            for i, key in enumerate(config.sections.keys()):
                self.db_menu.Append(1001+i, key)
                self.Bind(wx.EVT_MENU, self.OnChangementDatabase, id=1001+i)
            self.db_menu.FindItemByPosition(config.sections.keys().index(config.default_section)).Enable(False)
            self.db_menu.AppendSeparator()
            self.db_menu.Append(1099, "Rechercher...")
            self.Bind(wx.EVT_MENU, self.OnRechercher, id=1099)
            menu.AppendMenu(1000, "Changer de structure", self.db_menu)
        menu.Append(101, "&Enregistrer\tCtrl+S", u"Enregistre")
        self.Bind(wx.EVT_MENU, self.OnSave, id=101)
        menu.Append(102, u"&Copie de secours des données", u"Crée une copie de toutes les données")
        self.Bind(wx.EVT_MENU, self.OnBackup, id=102)
        menu.Append(103, "&Fermer\tAlt+F4", u"Ferme la fenêtre")
        self.Bind(wx.EVT_MENU, self.OnExit, id=103)
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
        self.listbook = GertrudeListbook(panel, progress_handler)
        sizer2.Add(self.listbook, 1, wx.EXPAND)
        panel.SetSizer(sizer2)
        
        self.UpdateEvent, EVT_UPDATE_AVAILABLE_EVENT = wx.lib.newevent.NewEvent()
        self.Bind(EVT_UPDATE_AVAILABLE_EVENT, self.OnUpdateAvailable)
        thread.start_new_thread(self.CheckForUpdates, ())
        
        self.AlertEvent, EVT_ALERT_EVENT = wx.lib.newevent.NewEvent()
        self.Bind(EVT_ALERT_EVENT, self.OnAlertAvailable)
        thread.start_new_thread(self.CheckAlertes, ())

        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        
        self.timer = wx.Timer(self, -1)  # message will be sent to the panel
        self.timer.Start(1000)  # x100 milliseconds
        self.Bind(wx.EVT_TIMER, self.onUpdateTimer, self.timer)  # call the on_timer function
    
    def onUpdateTimer(self, event):
        if readonly:
            _sql_connection, _creche = Update()
            if _sql_connection and _creche:
                __builtin__.sql_connection = _sql_connection
                __builtin__.creche = _creche
                self.listbook.UpdateContents()
        
    def CheckAlertes(self):
        if creche.gestion_alertes:
            new_alertes, alertes_non_acquittees = CheckAlertes()
            if new_alertes or alertes_non_acquittees:
                wx.PostEvent(self, self.AlertEvent(new_alertes=new_alertes, alertes_non_acquittees=alertes_non_acquittees))
            
    def OnAlertAvailable(self, event):
        if event.new_alertes:
            for alerte in event.new_alertes:
                alerte.create()
            history.append(None)
        if event.alertes_non_acquittees:
            texte = ""
            for alerte in event.alertes_non_acquittees:
                texte += alerte.texte + "\n"
            texte += "\n"
            dlg = wx.MessageDialog(self, texte + "Voulez-vous acquitter ces alertes ?", "Gertrude", wx.YES_NO|wx.YES_DEFAULT|wx.CANCEL|wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_YES:
                for alerte in event.alertes_non_acquittees:
                    alerte.acquittement = True
                history.append(None)
        
    def CheckForUpdates(self):
        try:
            url = u'http://gertrude.creches.free.fr/checkupdate.php?binary=%s&version=%s&creche=%s&ville=%s' % (os.path.splitext(os.path.basename(sys.argv[0]))[0], VERSION, urllib2.quote(creche.nom.encode("utf-8")), urllib2.quote(creche.ville.encode("utf-8")))
            req = urllib2.Request(url)
            result = urllib2.urlopen(req).read()
            if result:
                version, location = result.split()
                wx.PostEvent(self, self.UpdateEvent(version=version, location=location))
        except:
            return None
    
    def OnChangementDatabase(self, event):
        self.ChangeDatabase(config.sections.keys()[event.GetId()-1001])
        
    def ChangeDatabase(self, database):
        self.SetStatusText("Changement en cours ...")
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
        
        self.db_menu.FindItemByPosition(config.databases.keys().index(database)).Enable(False)
        self.db_menu.FindItemByPosition(config.databases.keys().index(config.default_database)).Enable(True)
        config.default_database = database
        config.connection = config.databases[database].connection
        history.Clear()
        Load(ProgressHandler(self.SetStatusText))
        self.listbook.UpdateContents() 
        self.SetStatusText("")
    
    def OnRechercher(self, event):
        class RechercherDialog(wx.Dialog):
            def __init__(self, parent):
                wx.Dialog.__init__(self, parent, -1, u"Rechercher un enfant", wx.DefaultPosition, wx.DefaultSize)
                self.sizer = wx.BoxSizer(wx.VERTICAL)
                self.fields_sizer = wx.FlexGridSizer(0, 2, 5, 10)
                self.fields_sizer.AddGrowableCol(1, 1)
                self.liste = Liste()
                self.choices = sorted(self.liste.keys())
                self.text = wx.TextCtrl(self)
                self.combo = wx.ListBox(self)
                self.combo.SetItems(self.choices)
                self.text.Bind(wx.EVT_TEXT, self.OnText)
                self.combo.Bind(wx.EVT_LEFT_DCLICK, self.OnOK)
                self.fields_sizer.AddMany([(wx.StaticText(self, -1, u"Recherche :"), 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALL-wx.BOTTOM, 5), (self.text, 0, wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL|wx.ALL-wx.BOTTOM, 5)])
                self.sizer.Add(self.fields_sizer, 0, wx.EXPAND|wx.ALL, 5)
                self.sizer.Add(self.combo, 0, wx.EXPAND|wx.ALL, 5)
                self.btnsizer = wx.StdDialogButtonSizer()
                self.ok = wx.Button(self, wx.ID_OK)
                self.btnsizer.AddButton(self.ok)
                btn = wx.Button(self, wx.ID_CANCEL)
                self.btnsizer.AddButton(btn)
                self.btnsizer.Realize()       
                self.sizer.Add(self.btnsizer, 0, wx.ALL, 5)
                self.SetSizer(self.sizer)
                self.sizer.Fit(self)
                
            def OnOK(self, event):
                self.EndModal(wx.ID_OK)
                
            def OnText(self, event):
                value = event.GetString().lower()
                items = [tmp for tmp in self.choices if value in tmp.lower()]
                self.combo.SetItems(items)
                if items:
                    self.combo.SetSelection(0)
                self.ok.Enable(len(items) > 0)

        dlg = RechercherDialog(self)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            selection = dlg.combo.GetStringSelection()
            db = dlg.liste[dlg.combo.GetStringSelection()]
            if db.section != config.default_database:
                self.ChangeDatabase(db.section)
            self.listbook.ChangePage(0)
            for inscrit in creche.inscrits:
                if selection == "%s %s" % (inscrit.prenom, inscrit.nom):
                    self.listbook.GetPage(0).SelectInscrit(inscrit)             
        
    def OnUpdateAvailable(self, event):
        if sys.platform == 'win32' and sys.argv[0].endswith("exe"):
            dlg = wx.MessageDialog(self, u'La version %s est disponible. Voulez-vous la télécharger maintenant ?' % event.version,
                                   'Nouvelle version disponible',
                                   wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result == wx.ID_YES:
                import webbrowser
                webbrowser.open(event.location)

    def OnSave(self, evt):
        self.SetStatusText("Enregistrement en cours ...")
        if readonly:
            dlg = wx.MessageDialog(self, u"Gertrude est en lecture seule !", 'Erreur', wx.OK|wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            Save(ProgressHandler(self.SetStatusText))
        self.SetStatusText("")

    def OnBackup(self, evt):
        self.SetStatusText("Copie de secours ...")
        Save(ProgressHandler(self.SetStatusText))
        wildcard = "ZIP files (*.zip)|*.zip"
        dlg = wx.FileDialog(self, style=wx.SAVE, wildcard=wildcard, defaultDir=config.backups_directory, defaultFile="gertrude-%d-%d-%d.zip" % (today.day, today.month, today.year))
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            filename = dlg.GetPath()
            config.backups_directory = os.path.dirname(filename)            
            zip = zipfile.ZipFile(filename, 'w')
            zip.write(config.connection.filename)
            for f in glob.glob("./templates/*"):
                zip.write(f)
        self.SetStatusText("")

    def OnResize(self, evt):
        config.window_size = evt.GetSize()
        evt.Skip()
        
    def OnExit(self, evt):
        self.SetStatusText("Fermeture en cours ...")
        if not readonly and len(history) > 0:
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
        info.Copyright = "(C) 2005-2013 Bertrand Songis"
        info.Description = wx.lib.wordwrap.wordwrap(
            u"Gertrude est un logiciel libre adapté aux besoins de gestion des crèches et haltes-garderies en France.\n\n"
            u"Développé pour une crèche parentale rennaise début 2005, il a été adapté de 2007 à 2010 pour d’autres crèches ; il est désormais accessible à tous.\n\n"
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
#     if sys.platform == 'win32':
#         locale.setlocale(locale.LC_ALL, 'fra_fra')
#     else:
#         locale.setlocale(locale.LC_ALL, 'fr_FR')
    app = MyApp(False)
    app.MainLoop()

