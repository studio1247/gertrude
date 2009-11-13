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

# a executer avec le parametre "py2exe"

from distutils.core import setup
import py2exe
import glob, shutil, os
from gertrude import VERSION

shutil.rmtree("./dist")

setup(
	name="Gertrude",
    version=VERSION,
    description=u"Logiciel pour les crèches",
    author="Bertrand Songis",
	windows=[{"script" : "gertrude.pyw", "icon_resources" : [(1000, "bitmaps\\gertrude.ico")]}],
	data_files=[(".", glob.glob("*.dist") + glob.glob("*.py")),
	            ("bitmaps", glob.glob("bitmaps\\*.png") + glob.glob("bitmaps\\*.ico")),
                ("templates_dist", glob.glob("templates_dist\\*.html") + glob.glob("templates_dist\\*.od?")),
                ("doc", glob.glob("doc\\*"))],
	options={"py2exe": {"packages": ["encodings", "wx.lib.agw.cubecolourdialog", "win32com.client", "win32ui", "win32api"]}},
)

chemin='\"C:/Program Files/Inno Setup 5/ISCC.exe\" setup.iss'
os.system(chemin)

os.rename("./Output/setup.exe", "./Output/setup_%s.exe" % VERSION)

