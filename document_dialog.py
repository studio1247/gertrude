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
from builtins import str as text
import traceback
import subprocess
import wx
import wx.lib.filebrowsebutton
from ooffice import *


class DocumentDialog(wx.Dialog):
    def __init__(self, parent, modifications):
        self.modifications = modifications
        self.document_generated = False

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI object using the Create
        # method.
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        pre.Create(parent, -1, "Génération de document")

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.PostCreate(pre)

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, -1, "Format :"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        if not IsOODocument(modifications.template):
            self.format = wx.Choice(self, -1, choices=["Texte"])
        elif sys.platform == 'win32':
            self.format = wx.Choice(self, -1, choices=["LibreOffice", "PDF"])
        else:
            self.format = wx.Choice(self, -1, choices=["LibreOffice"])
        self.format.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.onFormat, self.format)
        sizer.Add(self.format, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        default_output = normalize_filename(modifications.default_output)

        self.extension = os.path.splitext(default_output)[-1]
        wildcard = "OpenDocument (*%s)|*%s|PDF files (*.pdf)|*.pdf" % (self.extension, self.extension)
        self.fbb = wx.lib.filebrowsebutton.FileBrowseButton(self, -1,
                                                            size=(600, -1),
                                                            labelText="Nom de fichier :",
                                                            startDirectory=config.documents_directory,
                                                            initialValue=os.path.join(config.documents_directory, default_output),
                                                            fileMask=wildcard,
                                                            fileMode=wx.SAVE)
        sizer.Add(self.fbb, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        self.sizer.Add(sizer, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.gauge = wx.Gauge(self, -1, size=(-1, 10))
        self.gauge.SetRange(100)
        self.sizer.Add(self.gauge, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.LEFT | wx.TOP, 5)

        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        self.sizer.Add(line, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM, 5)

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.sauver_ouvrir = wx.Button(self, -1, "Sauver et ouvrir")
        self.sauver_ouvrir.SetDefault()
        self.Bind(wx.EVT_BUTTON, self.OnSauverOuvrir, self.sauver_ouvrir)
        sizer.Add(self.sauver_ouvrir, 0, wx.LEFT | wx.RIGHT, 5)

        self.sauver = wx.Button(self, -1, "Sauver")
        self.Bind(wx.EVT_BUTTON, self.OnSauver, self.sauver)
        sizer.Add(self.sauver, 0, wx.RIGHT, 5)

        if modifications.multi:
            button = wx.Button(self, -1, "Sauver individuellement")
            self.Bind(wx.EVT_BUTTON, self.OnSauverUnitaire, button)
            sizer.Add(button, 0, wx.RIGHT, 5)

        if modifications.email:
            self.sauver_envoyer = wx.Button(self, -1, "Sauver et envoyer par email")
            self.Bind(wx.EVT_BUTTON, self.OnSauverEnvoyer, self.sauver_envoyer)
            sizer.Add(self.sauver_envoyer, 0, wx.RIGHT, 5)
            if modifications.multi is False and not modifications.email_to:
                self.sauver_envoyer.Disable()

            if database.creche.caf_email:
                self.sauver_envoyer = wx.Button(self, -1, "Sauver et envoyer par email à la CAF")
                self.Bind(wx.EVT_BUTTON, self.OnSauverEnvoyerCAF, self.sauver_envoyer)
                sizer.Add(self.sauver_envoyer, 0, wx.LEFT | wx.RIGHT, 5)

        # btnsizer.Add(self.ok)
        btn = wx.Button(self, wx.ID_CANCEL)
        sizer.Add(btn, 0, wx.RIGHT, 5)
        self.sizer.Add(sizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        self.CenterOnScreen()

    def onFormat(self, _):
        filename = os.path.splitext(self.fbb.GetValue())[0]
        if self.format.GetSelection() == 0:
            self.fbb.SetValue(filename + self.extension, None)
        else:
            self.fbb.SetValue(filename + ".pdf", None)

    def Sauver(self):
        self.fbb.Disable()
        self.sauver.Disable()
        if self.sauver_ouvrir:
            self.sauver_ouvrir.Disable()
        self.filename = self.fbb.GetValue()
        f, e = os.path.splitext(self.filename)
        if e == ".pdf":
            self.pdf = True
            self.oo_filename = f + self.extension
        else:
            self.pdf = False
            self.oo_filename = self.filename

        config.documents_directory = os.path.dirname(self.filename)
        dlg = None
        try:
            if self.modifications.multi is not False:
                errors = {}
                simple_modifications = self.modifications.get_simple_modifications(self.oo_filename)
                for i, (filename, modifs) in enumerate(simple_modifications):
                    self.gauge.SetValue((100 * i) / len(simple_modifications))
                    errors.update(GenerateDocument(modifs, filename=filename))
                    if self.pdf:
                        f, e = os.path.splitext(filename)
                        convert_to_pdf(filename, f + ".pdf")
                        os.remove(filename)
            else:
                self.filename = self.filename.replace(" <prenom> <nom>", "")
                self.oo_filename = self.oo_filename.replace(" <prenom> <nom>", "")
                errors = GenerateDocument(self.modifications, filename=self.oo_filename, gauge=self.gauge)
                if self.pdf:
                    convert_to_pdf(self.oo_filename, self.filename)
                    os.remove(self.oo_filename)
            self.document_generated = True
            if errors:
                message = "Document %s généré avec des erreurs :\n" % self.filename
                for label in errors.keys():
                    message += '\n' + label + ' :\n  '
                    message += '\n  '.join(errors[label])
                dlg = wx.MessageDialog(self, message, 'Message', wx.OK | wx.ICON_WARNING)
        except IOError:
            print(sys.exc_info())
            dlg = wx.MessageDialog(self, "Impossible de sauver le document. Peut-être est-il déjà ouvert ?", 'Erreur',
                                   wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
            return
        except Exception as e:
            info = sys.exc_info()
            message = ' [type: %s value: %s traceback: %s]' % (info[0], info[1], traceback.extract_tb(info[2]))
            dlg = wx.MessageDialog(self, message, 'Erreur', wx.OK | wx.ICON_WARNING)
        if dlg:
            dlg.ShowModal()
            dlg.Destroy()
        self.EndModal(wx.ID_OK)

    def OnSauver(self, _):
        self.modifications.multi = False
        self.Sauver()

    def OnSauverOuvrir(self, event):
        self.OnSauver(event)
        if self.document_generated:
            if self.filename.endswith(".pdf"):
                StartAcrobatReader(self.filename)
            else:
                StartLibreOffice(self.filename)

    def OnSauverUnitaire(self, _):
        self.Sauver()

    def OnSauverEnvoyer(self, event):
        self.OnSauverUnitaire(event)
        if self.document_generated:
            if self.modifications.multi is not False:
                simple_modifications = self.modifications.get_simple_modifications(self.oo_filename)
                emails = '\n'.join(
                    [" - %s (%s)" % (modifs.email_subject, ", ".join(modifs.email_to)) for filename, modifs in
                     simple_modifications])
                if len(emails) > 1000:
                    emails = emails[:1000] + "\n..."
                dlg = wx.MessageDialog(self, "Ces emails seront envoyés :\n" + emails, 'Confirmation',
                                       wx.OK | wx.CANCEL | wx.ICON_WARNING)
                response = dlg.ShowModal()
                dlg.Destroy()
                if response != wx.ID_OK:
                    return

                for filename, modifs in simple_modifications:
                    if self.pdf:
                        oo_filename = filename
                        filename, e = os.path.splitext(oo_filename)
                        filename += ".pdf"
                    try:
                        SendDocument(filename, modifs)
                    except Exception as e:
                        dlg = wx.MessageDialog(self, "Impossible d'envoyer le document %s\n%r" % (filename, e),
                                               'Erreur', wx.OK | wx.ICON_WARNING)
                        dlg.ShowModal()
                        dlg.Destroy()
            else:
                try:
                    SendDocument(self.filename, self.modifications)
                except Exception as e:
                    dlg = wx.MessageDialog(self, "Impossible d'envoyer le document %s\n%r" % (self.filename, e),
                                           'Erreur', wx.OK | wx.ICON_WARNING)
                    dlg.ShowModal()
                    dlg.Destroy()

    def OnSauverEnvoyerCAF(self, event):
        self.OnSauver(event)
        if self.document_generated:
            try:
                root, ext = os.path.splitext(self.modifications.introduction_filename)
                introduction_filename = root + " CAF" + ext
                SendDocument(self.filename, self.modifications, to=[database.creche.caf_email], introduction_filename=GetTemplateFile(introduction_filename))
            except Exception as e:
                dlg = wx.MessageDialog(self, "Impossible d'envoyer le document %s\n%r" % (self.filename, e), "Erreur", wx.OK | wx.ICON_WARNING)
                dlg.ShowModal()
                dlg.Destroy()


def StartLibreOffice(filename):
    if sys.platform == 'win32':
        filename = "".join(["file:", urllib.pathname2url(os.path.abspath(filename.encode("utf-8")))])
        # print filename
        try:
            StarDesktop, objServiceManager, core_reflection = getOOoContext()
            StarDesktop.LoadComponentFromURL(filename, "_blank", 0, MakePropertyValues(objServiceManager, [
                ["ReadOnly", False],
                ["Hidden", False]]))
        except Exception as e:
            print("Exception ouverture LibreOffice", e)
            dlg = wx.MessageDialog(None, "Impossible d'ouvrir le document\n%r" % e, "Erreur", wx.OK|wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
    else:
        paths = []
        if sys.platform == "darwin":
            paths.append("/Applications/LibreOffice.app/Contents/MacOS/soffice")
            paths.append("/Applications/OpenOffice.app/Contents/MacOS/soffice")
        else:
            paths.append("/usr/bin/libreoffice")
            paths.append("ooffice")
        for path in paths:
            try:
                print(path, filename)
                subprocess.Popen([path, filename])
                return
            except Exception as e:
                print(e)
                pass
        dlg = wx.MessageDialog(None, "Impossible de lancer OpenOffice / LibreOffice", 'Erreur', wx.OK|wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()


DDE_ACROBAT_STRINGS = ["AcroviewR15", "AcroviewA15", "AcroviewR12", "AcroviewA12", "AcroviewR11", "AcroviewA11",
                       "AcroviewR10", "AcroviewA10", "acroview"]
dde_server = None


def StartAcrobatReader(filename):
    global dde_server
    import win32api
    import win32ui
    import dde

    filename = str(os.path.abspath(filename))
    path, name = os.path.split(filename)
    reader = win32api.FindExecutable(name, path)
    os.spawnl(os.P_NOWAIT, reader[1], " ")

    for t in range(10):
        time.sleep(1)
        for acrobat in DDE_ACROBAT_STRINGS:
            try:
                if not dde_server:
                    dde_server = dde.CreateServer()
                    dde_server.Create('Gertrude')
                c = dde.CreateConversation(dde_server)
                c.ConnectTo(acrobat, 'control')
                c.Exec('[DocOpen("%s")]' % (filename,))
                return
            except Exception as e:
                pass
        print("Impossible de lancer acrobat reader ; prochain essai dans 1s ...", e)

    dlg = wx.MessageDialog(None, "Impossible d'ouvrir le document", 'Erreur', wx.OK | wx.ICON_WARNING)
    dlg.ShowModal()
    dlg.Destroy()

