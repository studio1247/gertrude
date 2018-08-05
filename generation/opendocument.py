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
from __future__ import division

import os
import datetime
import locale
import xml.dom.minidom
import zipfile
import codecs
import chardet
import imageio
import re
import math
from builtins import str as typetext
from simpleeval import simple_eval
from collections import OrderedDict

from constants import FIELD_DATE, FIELD_EUROS, FIELD_HEURES, FIELD_SIGN
from helpers import GetHeureString, normalize_filename, date2str
from functions import GetTemplateFile
from generation.pdf_helpers import convert_to_pdf


FLAG_SUM_MAX = 1


class OpenDocument(object):
    format = "OpenDocument"

    def __init__(self):
        self.metas = {}
        self.expanded_fields = {}
        self.errors = {}
        self.destination_emails = OrderedDict()
        self.inserted_bitmaps = set()
        self.default_output = None
        self.output = None
        self.pdf_output = None
        self.last_field_value = None
        self.last_field_type = None
        self.site = None

    @classmethod
    def available(cls):
        return GetTemplateFile(cls.template)

    def set_default_output(self, value):
        self.default_output = value.replace("/", "").replace("'", "") if value else None

    @staticmethod
    def remove_nodes_containing(nodes, needle):
        if not isinstance(nodes, list):
            nodes = [nodes]
        for node in nodes:
            if needle in node.toprettyxml():
                node.parentNode.removeChild(node)

    @staticmethod
    def get_dimension(node, what):
        attribute = node.getAttribute(what)
        if attribute.endswith("cm"):
            return float(attribute[:-2]) * 10
        elif attribute.endswith("mm"):
            return float(attribute[:-2])
        elif attribute.endswith("in"):
            return float(attribute[:-2]) * 25.4
        else:
            return 0

    @staticmethod
    def set_dimension(node, what, value):
        node.setAttribute(what, "%.3smm" % value)

    def change_content_bitmap(self, dom, name, bitmap):
        im = imageio.imread(bitmap)
        bitmap_height, bitmap_width = im.shape[:2]
        for frame in dom.getElementsByTagName("draw:frame"):
            if frame.getAttribute("draw:name").startswith(name):
                max_width = OpenDocument.get_dimension(frame, "svg:width")
                max_height = OpenDocument.get_dimension(frame, "svg:height")
                if max_width > 0 and max_width > 0:
                    ratio = min(max_width / bitmap_width, max_height / bitmap_height)
                    OpenDocument.set_dimension(frame, "svg:width", bitmap_width * ratio)
                    OpenDocument.set_dimension(frame, "svg:height", bitmap_height * ratio)
                    images = frame.getElementsByTagName("draw:image")
                    if images:
                        images[0].setAttribute("xlink:href", self.get_bitmap_hash(bitmap))
                        self.inserted_bitmaps.add(bitmap)

    @staticmethod
    def convert_to_text(value, field_type=0):
        if value is None:
            return ""
        elif isinstance(value, typetext):
            return value
        elif field_type == FIELD_DATE:
            return date2str(value)
        elif field_type == FIELD_HEURES:
            return GetHeureString(value)
        elif isinstance(value, float):
            if field_type & FIELD_SIGN:
                return locale.format("%+0.2f", value)
            else:
                return locale.format("%0.2f", value)
        else:
            return str(value)

    def set_fields(self, fields):
        # fields are tuple (name, value, [type])
        self.expanded_fields = {}
        for field in fields:
            param, value = field[0:2]
            field_type = field[2] if len(field) == 3 else FIELD_DATE if isinstance(value, datetime.date) else 0
            text = OpenDocument.convert_to_text(value, field_type)
            if param in self.expanded_fields:
                print("Champ '%s' déjà présent : %r / %r" % (param, self.expanded_fields[param], (text, value, field_type)))
            else:
                self.expanded_fields[param] = (text, value, field_type)
                self.expanded_fields[param.upper()] = (text.upper(), value, field_type)

    def replace_fields(self, text, delimiters=(("<", ">"), ), node=None):
        self.last_field_value = None
        self.last_field_type = None

        for start, end in delimiters:
            matches = re.finditer(r"%s(.+?)%s" % (start, end), text)
            for match in reversed(list(matches)):
                field_replacement, field_value, field_type = self.expanded_fields.get(match.group(1), (match.group(0), match.group(0), 0))
                (self.last_field_value, self.last_field_type) = (field_value, field_type) if self.last_field_type is None else (None, 0)
                text = text[:match.start(0)] + field_replacement + text[match.end(0):]
        return text

    def replace_text_fields(self, dom, fields=None):
        # print dom.toprettyxml()
        if fields:
            backup_expanded_fields = self.expanded_fields
            self.set_fields(fields)

        nodes = dom.getElementsByTagName("text:a")
        for node in nodes:
            href = node.getAttribute("xlink:href")
            href = self.replace_fields(href, [("%%3C", "%%3E")])
            node.setAttribute("xlink:href", href)

        if dom.__class__ == xml.dom.minidom.Element and dom.nodeName in ["text:p", "text:h", "text:span"]:
            nodes = [dom] + dom.getElementsByTagName("text:span")
        else:
            nodes = dom.getElementsByTagName("text:p") + dom.getElementsByTagName("text:h") + dom.getElementsByTagName("text:span")

        for node in nodes:
            for child in node.childNodes:
                if child.nodeType == child.TEXT_NODE:
                    text = self.replace_fields(child.wholeText)
                    if text != child.wholeText:
                        child.replaceWholeText(text)

                    # if isinstance(text, typetext) and callable(value):
                    #     start_tag, end_tag = "<%s(" % field, ")>"
                    #     if start_tag in node_text and end_tag in node_text:
                    #         if isinstance(text, list):
                    #             print(child.toprettyxml())
                    #         else:
                    #             tag = node_text[node_text.find(start_tag):node_text.find(end_tag) + 2]
                    #             parameters = tag[len(field) + 2:-2]
                    #             try:
                    #                 replace = True
                    #                 node_text = node_text.replace(tag, eval("value(%s)" % parameters))
                    #             except Exception as e:
                    #                 print("erreur :", tag, parameters, e)

                    # if isinstance(text, list):
                    #     for t in text:
                    #         duplicate = node.cloneNode(1)
                    #         node.parentNode.insertBefore(duplicate, node)
                    #         for c in duplicate.childNodes:
                    #             if c.nodeType == child.TEXT_NODE:
                    #                 nt = c.wholeText.replace(tag, t)
                    #                 c.replaceWholeText(nt)
                    #     node.parentNode.removeChild(node)
        if fields:
            self.expanded_fields = backup_expanded_fields

    def get_template(self):
        return GetTemplateFile(self.template, self.site)

    @staticmethod
    def get_ordered_namelist(template_zip):
        namelist = template_zip.namelist()
        head = ("meta.xml", "content.xml")
        tail = ("META-INF/manifest.xml", )
        result = [f for f in head if f in namelist]
        result += [f for f in namelist if (f not in head and f not in tail)]
        result += [f for f in tail if f in namelist]
        return result

    def generate_xml(self, f, data):
        dom = xml.dom.minidom.parseString(data)
        if self.modify_dom(f, dom):
            return dom.toxml("UTF-8")
        else:
            return None

    def parse_meta(self, dom):
        metas = dom.getElementsByTagName("meta:user-defined")
        for meta in metas:
            # print(meta.toprettyxml())
            name = meta.getAttribute("meta:name").lower()
            if len(meta.childNodes) > 0:
                value = meta.childNodes[0].wholeText
                value_type = meta.getAttribute('meta:value-type')
                if value_type == "float":
                    self.metas[name] = float(value)
                elif value_type == "boolean":
                    self.metas[name] = True if value == "true" else False
                else:
                    self.metas[name] = value
        return True

    def get_fields_from_meta(self, names, functions={"ceil": math.ceil}):
        fields = []
        for key in self.metas:
            if key.lower().startswith("formule "):
                label = key[8:]
                try:
                    value = simple_eval(self.metas[key], names=names, functions=functions)
                except Exception as e:
                    print("Exception formule:", label, self.metas[key], e)
                    continue
                if isinstance(value, tuple):
                    field = label, value[0], value[1]
                else:
                    field = label, value
                fields.append(field)
        return fields

    def modify_content_bitmaps(self, dom, site=None):
        for name in ["logo", "signature"]:
            filename = GetTemplateFile(name + ".png", site)
            if filename:
                self.change_content_bitmap(dom, name, filename)

    def modify_content(self, dom):
        self.modify_content_bitmaps(dom)
        return True

    def modify_styles(self, dom):
        self.modify_content_bitmaps(dom)
        self.replace_text_fields(dom)
        return True

    @staticmethod
    def get_bitmap_hash(bitmap):
        return "Pictures/%X.png" % hash(bitmap)

    def modify_manifest(self, dom):
        manifests = dom.getElementsByTagName("manifest:manifest")
        if manifests:
            manifest = manifests[0]
            for bitmap in self.inserted_bitmaps:
                node = dom.createElement("manifest:file-entry")
                node.setAttribute("manifest:full-path", self.get_bitmap_hash(bitmap))
                node.setAttribute("manifest:media-type", "image/png")
                manifest.appendChild(node)
        return True

    def modify_dom(self, f, dom):
        if f == "meta.xml":
            return self.parse_meta(dom)
        elif f == "content.xml":
            return self.modify_content(dom)
        elif f == "styles.xml":
            return self.modify_styles(dom)
        elif f == "META-INF/manifest.xml":
            return self.modify_manifest(dom)
        else:
            # TODO ? ReplaceTextFields(dom, fields)
            return True

    def generate(self, filename=None, progress=None):
        if self.errors:
            return False

        if progress:
            progress.SetValue(0)
        self.output = normalize_filename(filename if filename else os.path.join("doc", os.path.basename(self.default_output)))
        template = self.get_template()
        print("Template : %s" % template)
        template_zip = zipfile.ZipFile(template, "r")
        output_zip = zipfile.ZipFile(self.output, "w")

        if progress:
            progress.SetValue(5)

        for f in self.get_ordered_namelist(template_zip):
            data = template_zip.read(f)
            if f.endswith(".xml") and len(data) > 0:
                data = self.generate_xml(f, data)
                if data is None:
                    return False
            output_zip.writestr(f, data)

        for f in self.inserted_bitmaps:
            output_zip.writestr(self.get_bitmap_hash(f), open(f, "rb").read())

        template_zip.close()
        output_zip.close()

        if progress:
            progress.SetValue(100)

        return True

    def generate_introduction(self, filename):
        filename = GetTemplateFile(filename)
        if not filename:
            return None
        with open(filename, "rb") as f:
            text = f.read()
            encoding = chardet.detect(text)["encoding"]
            text = codecs.decode(text, encoding)
            return self.replace_fields(text)

    def get_default_pdf_output(self):
        return os.path.splitext(self.output)[0] + ".pdf"

    def convert_to_pdf(self, pdf_filename=None):
        self.pdf_output = pdf_filename if pdf_filename else self.get_default_pdf_output()
        convert_to_pdf(self.output, self.pdf_output)
        return True


class OpenDocumentText(OpenDocument):
    def __init__(self):
        OpenDocument.__init__(self)


class OpenDocumentDraw(OpenDocument):
    def __init__(self):
        OpenDocument.__init__(self)

    @staticmethod
    def get_named_shapes(dom):
        shapes = {}
        for tag in ("draw:line", "draw:frame", "draw:custom-shape"):
            nodes = dom.getElementsByTagName(tag)
            for node in nodes:
                name = node.getAttribute("draw:name")
                if name:
                    shapes[name] = node
        return shapes


class OpenDocumentSpreadsheet(OpenDocument):
    def __init__(self):
        OpenDocument.__init__(self)

    @staticmethod
    def get_column_name(index):
        if index < 26:
            return chr(65 + index)
        else:
            return chr(64 + (index // 26)) + chr(65 + (index % 26))

    @staticmethod
    def get_column_index(name):
        if len(name) == 1:
            return ord(name) - 65
        elif len(name) == 2:
            return (ord(name[0]) - 64) * 26 + (ord(name[1]) - 65)

    @staticmethod
    def get_cell_text(node):
        result = ""
        text_nodes = node.getElementsByTagName("text:p") + node.getElementsByTagName("text:a")
        for text_node in text_nodes:
            for child in text_node.childNodes:
                if child.nodeType == child.TEXT_NODE:
                    result += child.wholeText
        return result

    @staticmethod
    def set_cell_value(node, value):
        if node.nodeName == "table:table-cell":
            node.setAttribute("office:value", str(value))
        text_nodes = node.getElementsByTagName("text:p") + node.getElementsByTagName("text:a")
        for text_node in text_nodes:
            for child in text_node.childNodes:
                if child.nodeType == child.TEXT_NODE:
                    child.replaceWholeText(str(value))
                    break

    @staticmethod
    def get_repeat(node):
        if node.hasAttribute("table:number-columns-repeated"):
            return int(node.getAttribute("table:number-columns-repeated"))
        elif node.hasAttribute("table:number-rows-repeated"):
            return int(node.getAttribute("table:number-rows-repeated"))
        else:
            return 1

    @staticmethod
    def get_row(table, index):
        rows = table.getElementsByTagName("table:table-row")
        i = 0
        for row in rows:
            repeat = OpenDocumentSpreadsheet.get_repeat(row)
            i += repeat
            if i >= index:
                return row
        return None

    @staticmethod
    def get_cells_count(row):
        count = 0
        for child in row.childNodes:
            if child.nodeName in ("table:table-cell", "table:covered-table-cell"):
                count += OpenDocumentSpreadsheet.get_repeat(child)
        return count

    @staticmethod
    def get_cell(row, index):
        i = 0
        for child in row.childNodes:
            if child.nodeName in ("table:table-cell", "table:covered-table-cell"):
                repeat = OpenDocumentSpreadsheet.get_repeat(child)
                if i <= index < i + repeat:
                    return child
                i += repeat
        return None

    @staticmethod
    def split_cell_repeat(cell):
        repeat = OpenDocumentSpreadsheet.get_repeat(cell)
        if repeat > 1:
            for i in range(1, repeat):
                clone = cell.cloneNode(1)
                clone.setAttribute("table:number-columns-repeated", "1")
                cell.parentNode.insertBefore(clone, cell)
            cell.setAttribute("table:number-columns-repeated", "1")

    @staticmethod
    def get_values(row):
        result = []
        cells = row.getElementsByTagName("table:table-cell")
        for cell in cells:
            # print cell.toprettyxml()
            # print GetRepeat(cell), GetValue(cell)
            result.extend([OpenDocumentSpreadsheet.get_cell_text(cell)] * OpenDocumentSpreadsheet.get_repeat(cell))
        return result

    @staticmethod
    def remove_column(rows, index):
        for row in rows:
            cells = row.getElementsByTagName("table:table-cell")
            count = 0
            for cell in cells:
                repeat = OpenDocumentSpreadsheet.get_repeat(cell)
                count += repeat
                if count > index:
                    if repeat == 1:
                        row.removeChild(cell)
                    else:
                        cell.setAttribute("table:number-columns-repeated", str(repeat - 1))
                    break

    def replace_cell_fields(self, cellules, fields=None):
        if fields:
            backup_expanded_fields = self.expanded_fields
            self.set_fields(fields)

        # Si l'argument est une ligne ...
        if cellules is None:
            return
        elif cellules.__class__ in (xml.dom.minidom.Element, xml.dom.minidom.Document):
            if cellules.nodeName == "table:table-cell":
                cellules = [cellules]
            else:
                cellules = cellules.getElementsByTagName("table:table-cell")
        elif len(cellules) > 0 and cellules[0].nodeName != "table:table-cell":
            nodes = cellules
            cellules = []
            for node in nodes:
                cellules.extend(node.getElementsByTagName("table:table-cell"))

        result = False

        # Remplacement ...
        for cellule in cellules:
            formula = cellule.getAttribute("table:formula")
            cellule.setAttribute("table:formula", self.replace_fields(formula))
            nodes = cellule.getElementsByTagName("text:p") + cellule.getElementsByTagName("text:h")
            for node in nodes:
                for child in node.childNodes:
                    if child.nodeType == node.TEXT_NODE:
                        text = self.replace_fields(child.wholeText, [("<", ">")])
                        child.replaceWholeText(text)
                        if self.last_field_type == FIELD_DATE:
                            value = self.last_field_value
                            cellule.setAttribute("office:value-type", "date")
                            if value:
                                cellule.setAttribute("office:date-value", "%04d-%02d-%02d" % (value.year, value.month, value.day))
                        elif isinstance(self.last_field_value, int) or isinstance(self.last_field_value, float):
                            cellule.setAttribute("office:value-type", "float")
                            cellule.setAttribute("office:value", str(self.last_field_value))

                        # if "<" in node_text and ">" in node_text:
                        #     for field, value, text in self.expanded_fields:
                        #         if isinstance(text, typetext) and callable(value):
                        #             start_tag, end_tag = "<%s(" % field, ")>"
                        #             if start_tag in node_text and end_tag in node_text:
                        #                 if isinstance(text, list):
                        #                     print(child.toprettyxml())
                        #                 else:
                        #                     tag = node_text[node_text.find(start_tag):node_text.find(end_tag) + 2]
                        #                     parameters = tag[len(field) + 2:-2]
                        #                     try:
                        #                         cellule.setAttribute("office:value-type", "float")
                        #                         val = eval("value(%s)" % parameters)
                        #                         cellule.setAttribute("office:value", val)
                        #                         node_text = node_text.replace(tag, val)
                        #                     except Exception as e:
                        #                         print("erreur :", tag, parameters, e)
                        #         else:
                        #             tag = "<%s>" % field
                        #             if tag in node_text:
                        #                 result = True
                        #                 if value is None:
                        #                     node_text = node_text.replace(tag, "")
                        #                 elif isinstance(value, int) or isinstance(value, float):
                        #                     if len(nodes) == 1 and node_text == tag:
                        #                         cellule.setAttribute("office:value-type", "float")
                        #                         cellule.setAttribute("office:value", str(value))
                        #                     node_text = node_text.replace(tag, text)
                        #                 elif isinstance(value, datetime.date):
                        #                     if len(nodes) == 1 and node_text == tag:
                        #                         cellule.setAttribute("office:value-type", "date")
                        #                         cellule.setAttribute("office:date-value", "%04d-%02d-%02d" % (value.year, value.month, value.day))
                        #                     node_text = node_text.replace(tag, text)
                        #                 else:
                        #                     node_text = node_text.replace(tag, text)
                        #
                        #             if "<" not in node_text or ">" not in node_text:
                        #                 break
                        #
                        #     # print child.wholeText, "=>", text
                        #     child.replaceWholeText(node_text)

        if fields:
            self.expanded_fields = backup_expanded_fields

        return result

    @staticmethod
    def replace_formulas(cellules, old, new):
        if cellules.__class__ == xml.dom.minidom.Element:
            cellules = cellules.getElementsByTagName("table:table-cell")
        for cellule in cellules:
            if cellule.hasAttribute("table:formula"):
                formula = cellule.getAttribute("table:formula")
                formula = formula.replace(old, new)
                cellule.setAttribute("table:formula", formula)

    @staticmethod
    def increment_formulas(cellules, row=0, column=0, flags=0):
        if flags & FLAG_SUM_MAX:
            prefix = ":"
        else:
            prefix = ""
        formula_gure = re.compile("%s\.([A-Z]+)([0-9]+)" % prefix)
        if cellules.__class__ == xml.dom.minidom.Element:
            cellules = cellules.getElementsByTagName("table:table-cell")
        for cellule in cellules:
            if cellule.hasAttribute("table:formula"):
                formula = cellule.getAttribute("table:formula")
                mo = True
                while mo is not None:
                    mo = formula_gure.search(formula)
                    if mo:
                        formula = formula.replace(mo.group(0), "%s.___%s%d" % (prefix, OpenDocumentSpreadsheet.get_column_name(OpenDocumentSpreadsheet.get_column_index(mo.group(1)) + column), int(mo.group(2)) + row))
                formula = formula.replace(".___", ".")
                cellule.setAttribute("table:formula", formula)

    @staticmethod
    def set_cell_formula(cell, formula):
        cell.setAttribute("table:formula", formula)

    @staticmethod
    def set_cell_formula_reference(cell, table, other):
        OpenDocumentSpreadsheet.set_cell_formula(cell, "of:=['%s'.%s]" % (table.getAttribute("table:name"), other))

    @staticmethod
    def hide_line(line):
        line.setAttribute("table:visibility", "collapse")


def choose_document(*args):
    for arg in args:
        if arg.available():
            return arg
