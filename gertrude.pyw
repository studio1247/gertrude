#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#    This file is part of Gertrude.
#
#    Gertrude is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Gertrude is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Gertrude; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from __future__ import unicode_literals

import codecs
import os
import sys
import wx
import __builtin__

if sys.executable.endswith("pythonw.exe"):
    logfile = file("gertrude.log", "a")
    sys.stdout = codecs.getwriter('utf8')(logfile)
    sys.stderr = codecs.getwriter('utf8')(logfile)


from startdialog import StartDialog

try:
    import winsound
except:
    pass

if sys.platform != "win32":
    from functions import GERTRUDE_DIRECTORY
    if not os.path.exists(GERTRUDE_DIRECTORY):
        os.mkdir(GERTRUDE_DIRECTORY)
    try:
        print "Démarrage de Gertrude ..."
    except:
        sys.stdout = codecs.open(GERTRUDE_DIRECTORY + "/gertrude.log", "w", "utf-8")


class GertrudeApp(wx.App):
    def OnInit(self):
        self.SetAssertMode(wx.PYAPP_ASSERT_SUPPRESS)
        self.locale = wx.Locale(wx.LANGUAGE_DEFAULT)
        __builtin__.readonly = False
        self.instance = wx.SingleInstanceChecker("Gertrude")
        if self.instance.IsAnotherRunning():
            dlg = wx.MessageDialog(
                None,
                "Gertrude est déjà lancée. Les données seront accessibles en lecture seule !",
                "Confirmation",
                wx.OK | wx.ICON_WARNING | wx.CANCEL
            )
            response = dlg.ShowModal()
            dlg.Destroy()
            if response == wx.ID_OK:
                __builtin__.readonly = True
            else:
                return False
        dialog = StartDialog()
        dialog.Show(True)
        return True

if __name__ == '__main__':
    app = GertrudeApp(False)
    app.MainLoop()
