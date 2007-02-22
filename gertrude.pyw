# -*- coding: cp1252 -*-

import wx, wx.lib.scrolledpanel, wx.html
import datetime
import sys, shutil
from planning import GPanel, PlanningPanel
from inscriptions import InscriptionsPanel
from cotisations import CotisationsPanel
from releves import RelevesPanel
from general import GeneralPanel
from admin import AdminPanel
from common import *
from datafiles import *

version = '0.32'

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
        self.AddPage(InscriptionsPanel(self, profil, creche, creche.inscrits), './bitmaps/inscriptions.png')
        self.AddPage(PlanningPanel(self, profil, creche.inscrits), './bitmaps/presences.png')
        if profil & PROFIL_TRESORIER:
            self.AddPage(CotisationsPanel(self, profil, creche, creche.inscrits), './bitmaps/facturation.png')
        self.AddPage(RelevesPanel(self, profil, creche, creche.inscrits), './bitmaps/releves.png')
        if profil & PROFIL_BUREAU:
            self.AddPage(GeneralPanel(self, creche, creche.inscrits), './bitmaps/creche.png')
        if profil & PROFIL_ADMIN:
            self.AddPage(AdminPanel(self, creche), './bitmaps/administration.png')
        self.Draw()

    def OnPageChanged(self, event):
        Listbook.OnPageChanged(self, event)
        self.GetPage(event.GetSelection()).UpdateContents()
        event.Skip()

    def Update(self):
        self.GetPage(self.list_box.GetSelection()).Update()


class GertrudeFrame(wx.Frame):
    def __init__(self, parent, ID, title):
        wx.Frame.__init__(self, parent, ID, title, wx.DefaultPosition, wx.Size(900, 700))

        # Icone
        icon = wx.Icon('./bitmaps/gertrude.ico', wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        # Statusbar
        self.CreateStatusBar()
        self.SetStatusText("This is the statusbar")

        # Toolbar
        tb = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)
        tb.SetToolBitmapSize(wx.Size(24, 24))
        tb.AddSimpleTool(20, wx.BitmapFromImage(wx.Image("./bitmaps/Reload File.png", wx.BITMAP_TYPE_PNG)), "Synchroniser")
        self.Bind(wx.EVT_TOOL, self.onSynchroButton)
        tb.Realize()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel = wx.Panel(self, -1)
        sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer)

        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.listbook = GertrudeListbook(panel)
        sizer2.Add(self.listbook, 1, wx.EXPAND)
        panel.SetSizer(sizer2)

    def onSynchroButton(self, event):
        global creche
        dlg = SynchroDialog(self)
        dlg.CenterOnScreen()

        # this does not return until the dialog is closed.
        val = dlg.ShowModal()
        dlg.Destroy()
        if val == ID_SYNCHRO:
            # TODO crade ...
            _creche = Load()
            creche.nom = _creche.nom
            creche.adresse = _creche.adresse
            creche.code_postal = _creche.code_postal
            creche.ville = _creche.ville
            creche.baremes_caf[:] = _creche.baremes_caf
            creche.bureaux[:] = _creche.bureaux
            creche.inscrits[:] = _creche.inscrits
            creche.users[:] = _creche.users
            self.listbook.Update()

class LoginDialog(wx.Dialog):
    def __init__(self):
        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI dialog using the Create
        # method.

        pre = wx.PreDialog()
        #pre.SetExtraStyle(DIALOG_EX_CONTEXTHELP)
        pre.Create(None, -1, "Identification", wx.DefaultPosition, wx.DefaultSize)

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.PostCreate(pre)

        # Icone
        icon = wx.Icon('./bitmaps/gertrude.ico', wx.BITMAP_TYPE_ICO )
        self.SetIcon(icon)

        # Now continue with the normal construction of the dialog
        # contents
        sizer = wx.BoxSizer(wx.VERTICAL)

        bmp = wx.Bitmap("./bitmaps/splash_gertrude.png", wx.BITMAP_TYPE_PNG)
        bmp32 = wx.StaticBitmap(self, -1, bmp, style=wx.SUNKEN_BORDER)
        #label = wx.StaticText(self, -1, "This is a wx.Dialog")
        #label.SetHelpText("This is the help text for the label")
        sizer.Add(bmp32, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, "Identifiant :     ")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.login_ctrl = wx.TextCtrl(self, -1, "", size=(80,-1))
        self.login_ctrl.SetHelpText("Entrez votre identifiant")
        box.Add(self.login_ctrl, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, "Mot de passe :")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        self.passwd_ctrl = wx.TextCtrl(self, -1, "", size=(80,-1), style=wx.TE_PASSWORD)
        self.passwd_ctrl.SetHelpText("Entrez votre mot de passe")
        box.Add(self.passwd_ctrl, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)
        self.Bind(wx.EVT_BUTTON, self.onOkButton, btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        self.Bind(wx.EVT_BUTTON, self.OnExit, btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)

        self.Bind(wx.EVT_CLOSE, self.OnExit)

    def onOkButton(self, evt):
        global profil
        login = self.login_ctrl.GetValue()
        password = self.passwd_ctrl.GetValue()

        for user in creche.users:
            if login == user.login and password == user.password:
                self.Destroy()
                profil = user.profile
                frame = GertrudeFrame(None, -1, "Gertrude v%s" % version)
                frame.Show()
                return

        self.login_ctrl.Clear()
        self.passwd_ctrl.Clear()
        self.login_ctrl.SetFocus()

    def OnExit(self, evt):
        self.Destroy()
        evt.Skip()

class MyApp(wx.App):
    def OnInit(self):
        login_dialog = LoginDialog()
        login_dialog.Show(True)
        return True

creche = Load()
profil = 0
Backup()
app = MyApp(0)
app.MainLoop()
connection.close()
