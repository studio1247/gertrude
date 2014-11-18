#!/usr/bin/env python
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

import glob, shutil, os, sys

if sys.platform == 'win32':
    from gertrude import VERSION
    import win32api
    
    for directory in ("./dist", "./build"):
        if os.path.isdir(directory):
            shutil.rmtree(directory)
            
    os.system("C:\Python27\Scripts\pyi-build gertrude.spec")
    
    issfile = "setup.iss"
    path, name = os.path.split(issfile)
    isspath = os.path.split(win32api.FindExecutable(name, path)[-1])[0]
    if not os.system('\"%s\ISCC.exe\" %s' % (isspath, issfile)):
        exe = "./Output/setup_%s.exe" % VERSION
        if os.path.isfile(exe):
            os.remove(exe)
        os.rename("./Output/setup.exe", exe)
        print u"File %s generated!" % exe
        
elif "linux" in sys.platform:
    if not os.path.exists("./gertrude.py"):
        os.symlink("./gertrude.pyw", "./gertrude.py")
    
    from gertrude import VERSION
    from py2deb import Py2deb

    p = Py2deb("gertrude")
    p.author = "Bertrand Songis"
    p.mail = "bsongis@gmail.com"
    p.description = u"Logiciel pour les creches"
    p.url = "http://www.gertrude-logiciel.org"
    p.depends = "bash, python-gtk2, python"
    p.license = "gpl"
    p.section = "utils"
    p.arch = "all"

    p["/usr/share/applications"] =["./linux/gertrude.desktop|gertrude.desktop"]
    p["/usr/share/gertrude"] = glob.glob("./*.py") + glob.glob("./demo.db") + glob.glob("./bitmaps_dist/*") + glob.glob("./templates_dist/*.html") + glob.glob("./templates_dist/*.txt") + glob.glob("./templates_dist/*.od?")
    p["/usr/bin"]=["./linux/gertrude|gertrude"]
    p["/usr/share/doc/gertrude"]=["COPYING"]
    p.generate(VERSION, "", rpm=True, src=True)
else:
    print u"Plateforme %s non supportée" % sys.platform
