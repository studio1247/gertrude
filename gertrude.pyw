#!/usr/bin/python
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

import os, sys, codecs, locale
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
        print u"Démarrage de Gertrude ..."
    except:
        sys.stdout = codecs.open(GERTRUDE_DIRECTORY + "/gertrude.log", "w", "utf-8")

# Don't remove these 2 lines (mandatory for py2exe)
import controls, zipfile, xml.dom.minidom, wx.html, ooffice

class GertrudeApp(wx.App):
    def OnInit(self):
        self.locale = wx.Locale(wx.LANGUAGE_DEFAULT)
        dialog = StartDialog()
        
        dialog.Show(True)
        return True

if __name__ == '__main__':
    app = GertrudeApp(False)
    app.MainLoop()
