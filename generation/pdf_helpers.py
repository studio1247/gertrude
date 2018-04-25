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

import os
import sys
import urllib
import shutil

try:
    import uno
    import unohelper
    from com.sun.star.beans import PropertyValue
except ImportError:
    uno = None


class LibreOfficeContext:
    def __init__(self):
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
        context = resolver.resolve("uno:socket,host=localhost,port=2000;urp;StarOffice.ComponentContext")
        self.desktop = context.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", context)
        self.pdf_export_property = (PropertyValue("FilterName", 0, "writer_pdf_Export", 0), )

    def convert_to_pdf(self, filename, pdf_filename):
        # TODO reinit context in case of error
        input_filename = unohelper.systemPathToFileUrl(os.path.abspath(filename))
        output_filename = unohelper.systemPathToFileUrl(os.path.abspath(pdf_filename))
        document = self.desktop.loadComponentFromURL(input_filename, "_blank", 0, ())
        document.storeToURL(output_filename, self.pdf_export_property)
        document.dispose()
        return pdf_filename


def fallback_convert_to_pdf(filename, pdf_filename):
    command = "libreoffice --headless --convert-to pdf '%s' --outdir '%s'" % (filename, os.path.dirname(pdf_filename))
    print(command)
    os.system(command)
    shutil.move(os.path.splitext(filename)[0] + ".pdf", pdf_filename)


def windows_convert_to_pdf(filename, pdf_filename):
    # print filename, pdf_filename
    if filename.endswith(".ods"):
        filter_name = "calc_pdf_Export"
    else:
        filter_name = "writer_pdf_Export"
    filename = ''.join(["file:", urllib.pathname2url(os.path.abspath(filename).encode("utf8"))])
    pdf_filename = ''.join(["file:", urllib.pathname2url(os.path.abspath(pdf_filename).encode("utf8"))])
    StarDesktop, objServiceManager, core_reflection = get_libreoffice_context()
    document = StarDesktop.LoadComponentFromURL(
        filename,
        "_blank",
        0,
        make_property_values(
            objServiceManager,
            [["ReadOnly", True],
             ["Hidden", True]]))
    document.storeToUrl(
        pdf_filename,
        make_property_values(
            objServiceManager,
            [["CompressMode", 1],
             ["FilterName", filter_name]]))
    document.close(False)


libreoffice_context = None

if uno:
    try:
        libreoffice_context = LibreOfficeContext()
    except: # uno.NoConnectException:
        print("Connection à LibreOffice impossible!")
        uno = None

if libreoffice_context:
    convert_to_pdf = libreoffice_context.convert_to_pdf
elif sys.platform == "win32":
    from libreoffice_helpers import *
    convert_to_pdf = windows_convert_to_pdf
else:
    convert_to_pdf = fallback_convert_to_pdf
