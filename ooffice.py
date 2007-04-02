# -*- coding: cp1252 -*-

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

import datetime
import zipfile
import xml.dom.minidom

def ReplaceTextFields(dom, fields):
    for node in dom.getElementsByTagName("text:p"):
        try:
            text = node.firstChild.wholeText
            replace = False
            for field, value in fields:
                field = '<%s>' % field
                if field in text:
                    replace = True
                    text = text.replace(field, value)
            if replace:
                node.firstChild.replaceWholeText(text)
        except:
            pass

def ReplaceFields(cellules, fields):
    # print fields
    # Si l'argument est une ligne ...
    if cellules.__class__ == xml.dom.minidom.Element:
        cellules = cellules.getElementsByTagName("table:table-cell")
    # Fonction ...
    for cellule in cellules:
        for node in cellule.getElementsByTagName("text:p"):
            text = node.firstChild.wholeText
            if '<' in text and '>' in text:
                for field, value in fields:
                    field = '<%s>' % field
                    if field in text:
                        if value is None:
                            text = text.replace(field, '')
                        elif type(value) == int:
                            if text == field:
                                cellule.setAttribute("office:value-type", 'float')
                                cellule.setAttribute("office:value", '%d' % value)
                            text = text.replace(field, str(value))
                        elif type(value) == datetime.date:
                            if text == field:
                                cellule.setAttribute("office:value-type", 'date')
                                cellule.setAttribute("office:date-value", '%d-%d-%d' % (value.year, value.month, value.day))
                            text = text.replace(field, '%.2d/%.2d/%.4d' % (value.day, value.month, value.year))
                        else:
                            text = text.replace(field, value)

                    if '<' not in text or '>' not in text:
                        break
                else:
                    text = ''

                # print node.firstChild.wholeText, '=>', text
                node.firstChild.replaceWholeText(text)

def GenerateDocument(src, dest, modifications):
    template = zipfile.ZipFile(src, 'r')
    files = []
    for filename in template.namelist():
        data = template.read(filename)
        if filename == 'content.xml':
            dom = xml.dom.minidom.parseString(data)
            modifications.execute(dom)
            data = dom.toxml('UTF-8')
        files.append((filename, data))
    template.close()
    oofile = zipfile.ZipFile(dest, 'w')
    for filename, data in files:
        oofile.writestr(filename, data)
    oofile.close()
