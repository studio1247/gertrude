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
import re

def evalFields(fields):
    for i, field in enumerate(fields[:]):
        if len(field) == 2:
            param, value = field
            if isinstance(value, basestring):
                text = value
            elif isinstance(value, datetime.date):
                text = '%.2d/%.2d/%.4d' % (value.day, value.month, value.year)
            else:
                text = str(value)
            fields[i] = (param, value, text)
        fields.append((param.upper(), value, text.upper()))
    return fields
            
def ReplaceTextFields(dom, fields):
    evalFields(fields)
#    print dom.toprettyxml()
    if dom.__class__ == xml.dom.minidom.Element and dom.nodeName in ["text:p", "text:span"]:
        nodes = [dom] + dom.getElementsByTagName("text:span")
    else:
        nodes = dom.getElementsByTagName("text:p") + dom.getElementsByTagName("text:span")
    for node in nodes:
        for child in node.childNodes:
            if child.nodeType == child.TEXT_NODE:
                try:
                    nodeText = child.wholeText
                    replace = False
                    for field, value, text in fields:
                        tag = '<%s>' % field
                        if tag in nodeText:
                            replace = True
                            nodeText = nodeText.replace(tag, text)
                    if replace:
                        child.replaceWholeText(nodeText)
                except Exception, e:
                    print e

def ReplaceFields(cellules, fields):
    evalFields(fields)
    
    # Si l'argument est une ligne ...
    if cellules.__class__ == xml.dom.minidom.Element:
        if cellules.nodeName == "table:table-cell":
            cellules = [cellule]
        else:
            cellules = cellules.getElementsByTagName("table:table-cell")
    elif len(cellules) > 0 and cellules[0].nodeName != "table:table-cell":
        nodes = cellules
        cellules = []
        for node in nodes:
            cellules.extend(node.getElementsByTagName("table:table-cell"))

    # Remplacement ...
    for cellule in cellules:
        for node in cellule.getElementsByTagName("text:p"):
            if node.firstChild and node.firstChild.nodeType == node.TEXT_NODE:
                nodeText = node.firstChild.wholeText
                if '<' in nodeText and '>' in nodeText:
                    for param, value, text in fields:
                        tag = '<%s>' % param
                        if tag in nodeText:
                            if value is None:
                                nodeText = nodeText.replace(tag, '')
                            elif isinstance(value, int) or isinstance(value, float):
                                if nodeText == tag:
                                    cellule.setAttribute("office:value-type", 'float')
                                    cellule.setAttribute("office:value", str(value))
                                nodeText = nodeText.replace(tag, text)
                            elif isinstance(value, datetime.date):
                                if nodeText == tag:
                                    cellule.setAttribute("office:value-type", 'date')
                                    cellule.setAttribute("office:date-value", '%d-%d-%d' % (value.year, value.month, value.day))
                                nodeText = nodeText.replace(tag, text)
                            else:
                                nodeText = nodeText.replace(tag, text)

                        if '<' not in nodeText or '>' not in nodeText:
                            break

                    # print node.firstChild.wholeText, '=>', text
                    node.firstChild.replaceWholeText(nodeText)

def IncrementFormulas(cellules, inc=1):
    formula_gure = re.compile("\[\.([A-Z]+)([0-9]+)\]")
    if cellules.__class__ == xml.dom.minidom.Element:
        cellules = cellules.getElementsByTagName("table:table-cell")
    for cellule in cellules:
        if cellule.hasAttribute("table:formula"):
            formula = cellule.getAttribute("table:formula")
            mo = True
            while mo is not None:
                mo = formula_gure.search(formula)
                if mo:
                    formula = formula.replace(mo.group(0), "[_.%s%d_]" % (mo.group(1), int(mo.group(2))+inc))
            formula = formula.replace('[_', '[').replace('_]', ']')
            cellule.setAttribute("table:formula", formula)
            

def GenerateDocument(src, dest, modifications):
    errors = []
    template = zipfile.ZipFile(src, 'r')
    files = []
    for filename in template.namelist():
        data = template.read(filename)
        if filename == 'content.xml':
            dom = xml.dom.minidom.parseString(data)
            errors.extend(modifications.execute(dom))
            data = dom.toxml('UTF-8')
        files.append((filename, data))
    template.close()
    oofile = zipfile.ZipFile(dest, 'w')
    for filename, data in files:
        oofile.writestr(filename, data)
    oofile.close()
    return errors
