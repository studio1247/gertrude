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


# a executer avec le parametre "py2exe"

from distutils.core import setup
import py2exe
import glob

setup(
	windows = [{"script" : "gertrude.pyw", "icon_resources" : [(1000, "bitmaps\\gertrude.ico")]}],
	data_files=[(".", glob.glob("*.dist") + glob.glob("panel_*.py") + ["facture.py", "cotisation.py"]),
	            ("bitmaps", glob.glob("bitmaps\\*.png") + glob.glob("bitmaps\\*.ico")),
                ("templates", glob.glob("templates\\*.html") + glob.glob("templates\\*.ods")  + glob.glob("templates\\*.odt"))],
	options = {"py2exe": {"packages": ["encodings"]}},
)
