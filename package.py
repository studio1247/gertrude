#!/usr/bin/env python
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

import glob
import os
import shutil
import sys

from version import VERSION

if sys.platform == 'win32':
    import win32api
    
    for directory in ("./dist", "./build"):
        if os.path.isdir(directory):
            shutil.rmtree(directory)
            
    os.system("C:\Python27\Scripts\pyinstaller.exe gertrude.spec")

    issfile = "setup.iss"
    path, name = os.path.split(issfile)
    isspath = os.path.split(win32api.FindExecutable(name, path)[-1])[0]
    if not os.system('\"%s\ISCC.exe\" %s' % (isspath, issfile)):
        exe = "./Output/setup_%s.exe" % VERSION
        if os.path.isfile(exe):
            os.remove(exe)
        os.rename("./Output/setup.exe", exe)
        print u"File %s generated!" % exe

elif sys.platform == 'darwin':
    from setuptools import setup

    APP = ["gertrude.pyw"]
    DATA_FILES = glob.glob("bitmaps_dist/*.png") + glob.glob("bitmaps_dist/*.ico") + glob.glob("templates_dist/*.html") + glob.glob("templates_dist/*.txt") + glob.glob("templates_dist/*.od?")
    OPTIONS = {'site_packages': True,
               'arch': 'i386',
               'iconfile': 'bitmaps_dist/gertrude.icns',
               'argv_emulation': True,
               'includes': ['bcrypt', "_cffi_backend"]
               }
    setup(
        name="Gertrude",
        app=APP,
        data_files=DATA_FILES,
        options={'py2app': OPTIONS},
        setup_requires=['py2app'],
    )
        
elif "linux" in sys.platform:
    if not os.path.exists("./gertrude.py"):
        os.symlink("./gertrude.pyw", "./gertrude.py")
    
    from py2deb import Py2deb

    p = Py2deb("gertrude")
    p.author = "Bertrand Songis"
    p.mail = "bsongis@gmail.com"
    p.description = u"Logiciel de gestion de creches"
    p.url = "http://www.gertrude-logiciel.org"
    p.icon = "./bitmaps_dist/gertrude.png"
    p.depends = "bash, python, python-gtk2, python-bcrypt, python-wxgtk2.8 | python-wxgtk3.0"
    p.license = "gpl"
    p.section = "utils"
    p.arch = "all"

    p["/usr/share/applications"] =["./linux/gertrude.desktop|gertrude.desktop"]
    p["/usr/share/gertrude"] = glob.glob("./*.py") + glob.glob("./demo.db") + glob.glob("./bitmaps_dist/*.*") + glob.glob("./bitmaps_dist/pictos/*") + glob.glob("./templates_dist/*.html") + glob.glob("./templates_dist/*.txt") + glob.glob("./templates_dist/*.od?")
    p["/usr/bin"] = ["./linux/gertrude|gertrude"]
    p["/usr/share/doc/gertrude"] = ["COPYING"]
    p.generate(VERSION, u"", rpm=True, src=True)
else:
    print u"Plateforme %s non supportée" % sys.platform
