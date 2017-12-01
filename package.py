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

from __future__ import unicode_literals
from __future__ import print_function
import glob
import os
import shutil
import sys
import fnmatch

from version import VERSION


def main():
    if sys.platform == "win32":
        import win32api

        for directory in ("./dist", "./build"):
            if os.path.isdir(directory):
                shutil.rmtree(directory)

        if 1:
            os.chdir("WinPython-32bit-2.7.13.1Zero")
            paths = ["notebooks", "scripts", "settings", "tools"] + glob.glob("*.exe") + glob.glob("python-2.7.13/Scripts/*.exe")
            paths += [("python-2.7.13/" + path) for path in ("NEWS.txt", "README.txt", "w9xpopen.exe", "Doc", "include", "Logs", "tcl", "Lib\site-packages\prompt_toolkit", "Lib\site-packages\pygments", "Lib\site-packages\setuptools", "Lib\ensurepip", "Lib\site-packages\win32\Demos", "Lib\site-packages\pip", "Lib\site-packages\jedi", "Lib/unittest", "Lib/test", "Lib/lib2to3", "Lib/lib-tk", "Lib/idlelib", "Lib/distutils", "Lib/ctypes", "Lib/compiler", "Lib/site-packages/wx/tools/Editra", "Lib/site-packages/wx/tools/XRCed")]

            for root, dirnames, filenames in os.walk('python-2.7.13'):
                for filename in fnmatch.filter(filenames, '*.pyc') + fnmatch.filter(filenames, '*.chm'):
                    paths.append(os.path.join(root, filename))

            # for filename in filenames:
            #     if os.stat(os.path.join(root, filename)).st_size > 10000:
            #         print(os.path.join(root, filename), os.stat(os.path.join(root, filename)).st_size)

            for path in paths:
                print("Remove %s" % path)
                if os.path.isdir(path):
                    shutil.rmtree(path)
                elif os.path.exists(path):
                    os.remove(path)
            os.chdir("..")

        issfile = "setup.iss"
        isscontents = open(issfile + ".template").read().decode("utf-8")
        isscontents = isscontents.replace("@VERSION@", VERSION)
        open(issfile, "w").write(isscontents.encode("windows-1252"))

        path, name = os.path.split(issfile)
        isspath = os.path.split(win32api.FindExecutable(name, path)[-1])[0]
        if not os.system('\"%s\ISCC.exe\" %s' % (isspath, issfile)):
            exe = "./Output/setup_%s.exe" % VERSION
            if os.path.isfile(exe):
                os.remove(exe)
            os.rename("./Output/setup.exe", exe)
            print("File %s generated (%d bytes)" % (exe, os.stat(exe).st_size))

    elif sys.platform == "darwin":
        from setuptools import setup

        APP = ["gertrude.pyw"]
        DATA_FILES = glob.glob("bitmaps_dist/*.png") + glob.glob("bitmaps_dist/*.ico") + glob.glob("templates_dist/*.html") + glob.glob("templates_dist/*.txt") + glob.glob("templates_dist/*.od?")
        OPTIONS = {"site_packages": True,
                   "arch": "i386",
                   "iconfile": "bitmaps_dist/gertrude.icns",
                   "argv_emulation": True,
                   "includes": ["bcrypt", "_cffi_backend", "requests", "sqlalchemy", "sqlalchemy_utils", "configparser", "future", "backports"],
                   "packages": ["requests", "backports"]
                   }
        setup(
            name="Gertrude",
            app=APP,
            data_files=DATA_FILES,
            options={"py2app": OPTIONS},
            setup_requires=["py2app", "requests", "configparser"],
            install_requires=["requests", "configparser"]
        )

    elif "linux" in sys.platform:
        if not os.path.exists("./gertrude.py"):
            os.symlink("./gertrude.pyw", "./gertrude.py")

        from py2deb import Py2deb

        p = Py2deb("gertrude")
        p.author = "Bertrand Songis"
        p.mail = "bsongis@gmail.com"
        p.description = "Logiciel de gestion de creches"
        p.url = "https://www.gertrude-logiciel.org"
        p.icon = "./bitmaps_dist/gertrude.png"
        p.depends = "bash, python, python-gtk2, python-bcrypt, python-wxgtk2.8 | python-wxgtk3.0, python-requests, python-sqlalchemy, python-sqlalchemy-utils, python-future, python-configparser"
        p.license = "gpl"
        p.section = "utils"
        p.arch = "all"

        p["/usr/share/applications"] = ["./linux/gertrude.desktop|gertrude.desktop"]
        p["/usr/share/gertrude"] = glob.glob("./*.py") + glob.glob("./generation/*.py") + glob.glob("./demo.db") + glob.glob("./bitmaps_dist/*.*") + glob.glob("./bitmaps_dist/pictos/*") + glob.glob("./templates_dist/*.html") + glob.glob("./templates_dist/*.txt") + glob.glob("./templates_dist/*.od?")
        p["/usr/bin"] = ["./linux/gertrude|gertrude"]
        p["/usr/share/doc/gertrude"] = ["COPYING"]
        p.generate(VERSION, "", rpm=True, src=True)
    else:
        print("Plateforme %s non supportée" % sys.platform)


if __name__ == '__main__':
    main()
