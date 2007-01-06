# -*- coding: cp1252 -*-

# pysetup.py

# a executer avec le parametre "py2exe"

from distutils.core import setup
import py2exe
import glob

setup(
	windows = [{"script" : "gertrude.pyw", "icon_resources" : [(1000, "bitmaps\\gertrude.ico")]}],
	data_files=[("bitmaps", glob.glob("bitmaps\\*.png") + glob.glob("bitmaps\\*.ico")),
                    ("templates", glob.glob("templates\\*.html") + glob.glob("templates\\*.ods")  + glob.glob("templates\\*.odt"))],
	options = {"py2exe": {"packages": ["encodings"]}},
)
