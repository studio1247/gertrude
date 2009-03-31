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

import datetime, time
import sys, os, zipfile
import xml.dom.minidom
import re, urllib
import wx, wx.lib.filebrowsebutton
import traceback

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
    #print dom.toprettyxml()

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
        nodes = cellule.getElementsByTagName("text:p")
        for node in nodes:
            if node.firstChild and node.firstChild.nodeType == node.TEXT_NODE:
                nodeText = node.firstChild.wholeText
                if '<' in nodeText and '>' in nodeText:
                    for param, value, text in fields:
                        tag = '<%s>' % param
                        if tag in nodeText:
                            if value is None:
                                nodeText = nodeText.replace(tag, '')
                            elif isinstance(value, int) or isinstance(value, float):
                                if len(nodes) == 1 and nodeText == tag:
                                    cellule.setAttribute("office:value-type", 'float')
                                    cellule.setAttribute("office:value", str(value))
                                nodeText = nodeText.replace(tag, text)
                            elif isinstance(value, datetime.date):
                                if len(nodes) == 1 and nodeText == tag:
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
            
def getNamedShapes(dom):
    shapes = {}
    for tag in ("draw:line", "draw:frame", "draw:custom-shape"):
        nodes = dom.getElementsByTagName(tag)
        for node in nodes:
            name = node.getAttribute("draw:name")
            if name:
                shapes[name] = node
    return shapes

def GenerateDocument(modifications, filename=None, gauge=None):
    if gauge:
        gauge.SetValue(0)
    if not filename:
        filename = modification.default_output.replace(u"é", "e")
    if os.path.exists("./templates/%s" % modifications.template):
        template = "./templates/%s" % modifications.template
    else:
        template = "./templates_dist/%s" % modifications.template
    errors = {}
    zip = zipfile.ZipFile(template, 'r')
    files = []
    if gauge:
        modifications.gauge = gauge
        gauge.SetValue(5)
    for f in zip.namelist():
        data = zip.read(f)
        if f in ('content.xml', 'styles.xml'):
            dom = xml.dom.minidom.parseString(data)
            #print dom.toprettyxml()
            new_errors = modifications.execute(f, dom)
            if new_errors:
                errors.update(new_errors)
            data = dom.toxml('UTF-8')
        files.append((f, data))
    zip.close()
    zip = zipfile.ZipFile(filename, 'w')
    if gauge:
        gauge.SetValue(95)
    for f, data in files:
        zip.writestr(f, data)
    zip.close()
    if gauge:
        gauge.SetValue(100)
    return errors

def getOOoContext():
    import win32com.client
    objServiceManager = win32com.client.dynamic.Dispatch("com.sun.star.ServiceManager")
    objServiceManager._FlagAsMethod("CreateInstance")
    objServiceManager._FlagAsMethod("Bridge_GetStruct")
    corereflection = objServiceManager.CreateInstance("com.sun.star.reflection.CoreReflection")
    return objServiceManager.createInstance("com.sun.star.frame.Desktop"), objServiceManager, corereflection

def MakePropertyValue(oServiceManager, Name, Value):
    oStruct = oServiceManager.Bridge_GetStruct("com.sun.star.beans.PropertyValue")
    oStruct.Name = Name
    oStruct.Value = Value
    return oStruct

def MakePropertyValues(oServiceManager, values):
    return [MakePropertyValue(oServiceManager, value[0], value[1]) for value in values]

def oo_open(filename):
    filename = ''.join(["file:", urllib.pathname2url(unicode(os.path.abspath(filename)).encode("latin-1"))])
    # print filename
    StarDesktop, objServiceManager, corereflection = getOOoContext()
    document = StarDesktop.LoadComponentFromURL(filename, "_blank", 0,
        MakePropertyValues(objServiceManager,
                    [["ReadOnly", False],
                    ["Hidden", False]]))
    
def convert_to_pdf(filename, pdffilename):
    filename = ''.join(["file:", urllib.pathname2url(unicode(os.path.abspath(filename)).encode("latin-1"))])
    pdffilename = ''.join(["file:", urllib.pathname2url(unicode(os.path.abspath(pdffilename)).encode("latin-1"))])
    StarDesktop, objServiceManager, corereflection = getOOoContext()
    document = StarDesktop.LoadComponentFromURL(filename, "_blank", 0,
        MakePropertyValues(objServiceManager,
                    [["ReadOnly", True],
                    ["Hidden", True]]))
    document.storeToUrl( pdffilename,
        MakePropertyValues(objServiceManager,
                    [["CompressMode", 1],
                    ["FilterName", "writer_pdf_Export"]]))
    document.close(False)

def pdf_open(filename):    
    import win32ui, win32api
    import dde, time
    from os import spawnl,P_NOWAIT,startfile
    
    filename = unicode(os.path.abspath(filename))
    path, name = os.path.split(filename)
    readerexe = win32api.FindExecutable(name, path)
    os.spawnl(os.P_NOWAIT, readerexe[1], " ")
    time.sleep(5)
    s = dde.CreateServer()
    s.Create('')
    c = dde.CreateConversation(s)
    c.ConnectTo('acroview', 'control')
    c.Exec('[DocOpen("%s")]' % (filename,))

class DocumentDialog(wx.Dialog):
    def __init__(self, parent, modifications):
        self.modifications = modifications

        # Instead of calling wx.Dialog.__init__ we precreate the dialog
        # so we can set an extra style that must be set before
        # creation, and then we create the GUI object using the Create
        # method.
        pre = wx.PreDialog()
        pre.SetExtraStyle(wx.DIALOG_EX_CONTEXTHELP)
        pre.Create(parent, -1, u"Génération de document")

        # This next step is the most important, it turns this Python
        # object into the real wrapper of the dialog (instead of pre)
        # as far as the wxPython extension is concerned.
        self.PostCreate(pre)

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(self, -1, "Format :"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.format = wx.Choice(self, -1, choices=["OpenOffice", "PDF"])
        self.format.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.onFormat, self.format)
        sizer.Add(self.format, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        default_output = modifications.default_output.replace(u"é", "e")
        self.extension = os.path.splitext(default_output)[-1]
        wildcard = "OpenDocument (*%s)|*%s|PDF files (*.pdf)|*.pdf" % (self.extension, self.extension)
        self.fbb = wx.lib.filebrowsebutton.FileBrowseButton(self, -1,
                                                            size=(600, -1),
                                                            labelText="Nom de fichier :",
                                                            startDirectory=config.documents_directory,
                                                            initialValue=os.path.join(config.documents_directory, default_output),
                                                            fileMask=wildcard,
                                                            fileMode=wx.SAVE)
        sizer.Add(self.fbb, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 5)
        self.sizer.Add(sizer, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        
        self.gauge = wx.Gauge(self, -1, size=(-1,10))
        self.gauge.SetRange(100)
        self.sizer.Add(self.gauge, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.LEFT|wx.TOP, 5)
        
        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        self.sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.TOP|wx.BOTTOM, 5)
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        if sys.platform == 'win32':
            self.sauver_ouvrir = wx.Button(self, -1, u"Sauver et ouvrir")
            self.sauver_ouvrir.SetDefault()
            self.Bind(wx.EVT_BUTTON, self.onSauverOuvrir, self.sauver_ouvrir)
            sizer.Add(self.sauver_ouvrir, 0, wx.LEFT|wx.RIGHT, 5)
        else:
            self.sauver_ouvrir = None
#        self.ok = wx.Button(self, wx.ID_OK)
        self.sauver = wx.Button(self, -1, u"Sauver")
        self.Bind(wx.EVT_BUTTON, self.onSauver, self.sauver)
        sizer.Add(self.sauver, 0, wx.RIGHT, 5)
        #btnsizer.Add(self.ok)
        btn = wx.Button(self, wx.ID_CANCEL)
        sizer.Add(btn, 0, wx.RIGHT, 5)
        self.sizer.Add(sizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        self.CenterOnScreen()
    
    def onFormat(self, event):
        filename = os.path.splitext(self.fbb.GetValue())[0]
        if self.format.GetSelection() == 0:
            self.fbb.SetValue(filename+self.extension, None)
        else:
            self.fbb.SetValue(filename+".pdf", None)
            
    def onSauver(self, event):
        self.fbb.Disable()
        self.sauver.Disable()
        if self.sauver_ouvrir:
            self.sauver_ouvrir.Disable()
        self.filename = self.fbb.GetValue()
        f, e = os.path.splitext(self.fbb.GetValue())
        if e == ".pdf":
            pdf = True
            self.oo_filename = f + self.extension
        else:
            pdf = False
            self.oo_filename = self.filename
            
        config.documents_directory = os.path.dirname(self.filename)
        dlg = None
        try:
            errors = GenerateDocument(self.modifications, filename=self.oo_filename, gauge=self.gauge)
            if pdf:
                convert_to_pdf(self.oo_filename, self.filename)
                os.remove(self.oo_filename)
            self.document_generated = True
            if errors:
                message = u"Document %s généré avec des erreurs :\n" % self.filename
                for label in errors.keys():
                    message += '\n' + label + ' :\n  '
                    message += '\n  '.join(errors[label])
                dlg = wx.MessageDialog(self, message, 'Message', wx.OK|wx.ICON_WARNING)
        except Exception, e:
            info = sys.exc_info()
            message = ' [type: %s value: %s traceback: %s]' % (info[0], info[1], traceback.extract_tb(info[2]))
            dlg = wx.MessageDialog(self, message, 'Erreur', wx.OK|wx.ICON_WARNING)
        if dlg:
            dlg.ShowModal()
            dlg.Destroy()
        self.Destroy()
        
    def onSauverOuvrir(self, event):
        self.onSauver(event)
        if self.document_generated:
            if self.filename.endswith("pdf"):
                pdf_open(self.filename)
            else:
                oo_open(self.filename)
    
if __name__ == '__main__':   
    filename = '.\\templates_dist\\Appel cotisations.ods'
    oo_open(filename)
    
    pdffilename = ''.join([os.path.splitext(filename)[0], ".pdf"])
    convert_to_pdf(filename, pdffilename)
    pdf_open(pdffilename)
