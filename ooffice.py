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

def ReplaceFields(cellules, values):
    # Si l'argument est une ligne ...
    if cellules.__class__ == xml.dom.minidom.Element:
        cellules = cellules.getElementsByTagName("table:table-cell")
    # Fonction ...
    for cellule in cellules:
        for tag in cellule.getElementsByTagName("text:p"):
            text = tag.firstChild.wholeText
            if '[' in text and ']' in text:
                for key in values.keys():
                    if '[%s]' % key in text:
                        if values[key] is None:
                            text = text.replace('[%s]' % key, '')
                        elif type(values[key]) == int:
                            if text == '[%s]' % key:
                                cellule.setAttribute("office:value-type", 'float')
                                cellule.setAttribute("office:value", '%d' % values[key])
                            text = text.replace('[%s]' % key, str(values[key]))
                        elif type(values[key]) == datetime.date:
                            date = values[key]
                            if text == '[%s]' % key:
                                cellule.setAttribute("office:value-type", 'date')
                                cellule.setAttribute("office:date-value", '%d-%d-%d' % (date.year, date.month, date.day))
                            text = text.replace('[%s]' % key, '%.2d/%.2d/%.4d' % (date.day, date.month, date.year))
                        else:
                            text = text.replace('[%s]' % key, values[key])

                    if '[' not in text or ']' not in text:
                        break
                else:
                    text = ''

                # print tag.firstChild.wholeText, '=>', text
                tag.firstChild.replaceWholeText(text)

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
