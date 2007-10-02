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

import wx, wx.lib, wx.lib.scrolledpanel
import fpformat
import datetime
from functions import *
from history import Change, Delete, Append
              
class NumericCtrl(wx.TextCtrl):
##    __fgcol_valid   ="Black"
##    __bgcol_valid   ="White"
##    __fgcol_invalid ="Red"
##    __bgcol_invalid =(254,254,120)

    def __init__(self, parent, id=-1, value="", min=None, max=None,
##                 action=None,
                 precision=3, action_kw={}, *args, **kwargs):

        self.__digits = '0123456789.-'
        self.__prec   = precision
        self.format   = '%.'+str(self.__prec)+'f'
        self.__val    = 0
        #if (value != None): self.__val = float(value)
        if (max != None): self.__max = float(max)
        if (min != None): self.__min = float(min)
      
        wx.TextCtrl.__init__(self, parent, id, value=value, *args, **kwargs)
                     
        self.Bind(wx.EVT_CHAR, self.onChar)
        
    def SetPrecision(self,p):
        self.__prec = p
        self.format = '%.'+str(self.__prec)+'f'
        
    def onChar(self, event):
        """ on Character event"""
        key  = event.KeyCode
        entry = wx.TextCtrl.GetValue(self).strip()

        # 2. other non-text characters are passed without change
        if (key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255):
            event.Skip()
            return
        
        # 3. check for multiple '.' and out of place '-' signs and ignore these
        #    note that chr(key) will now work due to return at #2
        pos = wx.TextCtrl.GetSelection(self)[0]
        has_minus = '-' in entry
        if ((chr(key) == '.' and (self.__prec == 0 or '.' in entry)) or
            (chr(key) == '-' and (has_minus or  pos != 0 or min >= 0)) or
            (chr(key) != '-' and  has_minus and pos == 0)):
            return
        # 4. allow digits, but not other characters
        if (chr(key) in self.__digits):
            event.Skip()
            return

    def GetValue(self):
        if (wx.TextCtrl.GetValue(self) == ""):
            return ""
        elif self.__prec > 0:
#            return float(fpformat.fix(self.__val, self.__prec))
            return float(wx.TextCtrl.GetValue(self))
        else:
#            return int(self.__val)
            return int(wx.TextCtrl.GetValue(self))

#    def __Text_SetValue(self,value):
    def SetValue(self,value):
        if (value != ""):
            wx.TextCtrl.SetValue(self, self.format % float(value))
        else:
            wx.TextCtrl.SetValue(self, "")
        self.Refresh()
    
    def GetMin(self):
        return self.__min
    
    def GetMax(self):
        return self.__max

    def SetMin(self,min):
        try:
            self.__min = float(min)
        except:
            pass
        return self.__min
    
    def SetMax(self,max):
        try:
            self.__max = float(max)
        except:
            pass
        return self.__max
    
##    def __CheckValid(self,value):
##        v = self.__val
##        try:
##            self.__valid = True
##            v = float(value)
##            if self.__min != None and (v < self.__min):
##                self.__valid = False
##                v = self.__min
##            if self.__max != None and (v > self.__max):
##                self.__valid = False
##                v = self.__max
##        except:
##            self.__valid = False
##        self.__bound_val = v
##        if self.__valid:
##            self.__bound_val = self.__val = v
##            self.SetForegroundColour(self.__fgcol_valid)
##            self.SetBackgroundColour(self.__bgcol_valid)
##        else:
##            self.SetForegroundColour(self.__fgcol_invalid)
##            self.SetBackgroundColour(self.__bgcol_invalid)
##        self.Refresh()


class PhoneCtrl(wx.TextCtrl):
    def __init__(self, parent, id, value=None, action_kw={}, *args, **kwargs):

        self.__digits = '0123456789'

        this_sty = wx.TAB_TRAVERSAL| wx.TE_PROCESS_ENTER
        kw = kwargs

#        if kw.has_key('style'): this_sty = this_sty | kw['style']
#        kw['style'] = this_sty

        wx.TextCtrl.__init__(self, parent, id, size=(-1, -1), *args, **kw)
        self.SetMaxLength(14)

        wx.EVT_CHAR(self, self.onChar)
#        wx.EVT_TEXT(self, -1, self.onText)
        wx.EVT_LEFT_DOWN(self, self.OnLeftDown)
       
    def onChar(self, event):
        """ on Character event"""
        ip = self.GetInsertionPoint()
        lp = self.GetLastPosition()
        key = event.KeyCode

        # 2. other non-text characters are passed without change
        if (key == wx.WXK_BACK):
            if (ip > 0): self.RemoveChar(ip - 1)
            return

        if (key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255):
            event.Skip()
            wx.CallAfter(self.Arrange, key)
            return

        # 4. allow digits, but not other characters
        if (chr(key) in self.__digits):
            event.Skip()
            wx.CallAfter(self.Arrange, key)

    def Arrange(self, key):
        ip = self.GetInsertionPoint()
        lp = self.GetLastPosition()
        sel = self.GetSelection()
        value = self.GetValue()
        
        tmp = self.GetValue().replace(" ", "")
        arranged = ""
        for c in tmp:
            if c in self.__digits:
                arranged += c
                if (len(arranged) < 14 and len(arranged) % 3 == 2):
                    arranged += " "
            else:
                ip -= 1
                
        if (arranged != value):
            self.SetValue(arranged)

        if (sel == (ip, ip) or arranged != value):
            if (ip == len(arranged) or arranged[ip] != " "):
                self.SetInsertionPoint(ip)
            elif key == wx.WXK_LEFT:
                self.SetInsertionPoint(ip - 1)
            else:
                self.SetInsertionPoint(ip + 1)
 
    def RemoveChar(self, index):
        value = self.GetValue()
        if (value[index] == " "):
            value = value[:index-1] + value[index+1:]
            index -= 1
        else:
            value = value[:index] + value[index+1:]

        self.SetValue(value)
        self.SetInsertionPoint(index)
        self.Arrange(wx.WXK_BACK)

    def OnLeftDown(self, event):
        if event.LeftDown():
            event.Skip()
            wx.CallAfter(self.OnCursorMoved, event)

    def OnCursorMoved(self, event):
        ip = self.GetInsertionPoint()
        if (ip < 14 and ip % 3 == 2):
            self.SetInsertionPoint(ip + 1)

class DateCtrl(wx.TextCtrl):
    def __init__(self, parent, id=-1, value=None, *args, **kwargs):
        wx.TextCtrl.__init__(self, parent, id=-1, *args, **kwargs)
        
        #self.__CheckValid(self.__val)
        #self.SetValue(self.__val)
              
        #wx.EVT_CHAR(self, self.onChar)
        #wx.EVT_TEXT(self, -1,self.onText)
        #wx.EVT_SET_FOCUS(self, self.onSetFocus)
        #wx.EVT_KILL_FOCUS(self, self.onKillFocus)
        #wx.EVT_SIZE(self, self.onResize)
        #self.__GetMark()

        
        
#    def onChar(self, event):
#        """ on Character event"""
#        key   = event.KeyCode()
#        entry = wx.TextCtrl.GetValue(self).strip()
#        # really, the order here is important:
#        # 1. return sends to ValidateEntry
###        if (key == wx.WXK_RETURN):
###            self.SetValue(entry)
###            return
#
#        # 2. other non-text characters are passed without change
#        if (key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255):
#            event.Skip()
#            return
#        
#        # 3. check for multiple '.' and out of place '-' signs and ignore these
#        #    note that chr(key) will now work due to return at #2
#        pos = wx.TextCtrl.GetSelection(self)[0]
#        has_minus = '-' in entry
#        if ((chr(key) == '.' and (self.__prec == 0 or '.' in entry)) or
#            (chr(key) == '-' and (has_minus or  pos != 0 or min >= 0)) or
#            (chr(key) != '-' and  has_minus and pos == 0)):
#            return
#        # 4. allow digits, but not other characters
#        if (chr(key) in self.__digits):
#            event.Skip()
#            return

##    def onText(self, event=None):
##        try:
##            if event.GetString() != '':
##                self.__CheckValid(event.GetString())
##        except:
##            pass
##        event.Skip()

    def GetValue(self):
        if (wx.TextCtrl.GetValue(self) == ""):
            return None
        else:
            return str2date(wx.TextCtrl.GetValue(self))

    def SetValue(self, value):
        if value is None:
            wx.TextCtrl.SetValue(self, '')
        else:
            wx.TextCtrl.SetValue(self, '%.02d/%.02d/%.04d' % (value.day, value.month, value.year))
        self.Refresh()

class AutoMixin:
    def __init__(self, parent, instance, member):
        self.__ontext = True
        self.parent = parent
        parent.ctrls.append(self)
        self.SetInstance(instance, member) 
        self.Bind(wx.EVT_TEXT, self.onText)

    def __del__(self):
        self.parent.ctrls.remove(self)
        
    def SetInstance(self, instance, member=None):
        self.instance = instance
        if member:
            self.member = member
        self.UpdateContents()
        
    def UpdateContents(self):
        if not self.instance:
            self.Disable()
        else:
            self.__ontext = False
            self.SetValue(eval('self.instance.%s' % self.member))
            self.__ontext = True
            self.Enable()
            
    def onText(self, event):
        obj = event.GetEventObject()
        if self.__ontext:
            self.AutoChange(obj.GetValue())
        event.Skip()

    def AutoChange(self, new_value):
        old_value = eval('self.instance.%s' % self.member)
        if old_value != new_value:
            last = history.Last()                
            if last is not None and len(last) == 1 and isinstance(last[-1], Change):
                if last[-1].instance != self.instance or last[-1].member != self.member:
                    history.Append(Change(self.instance, self.member, old_value))
            else:
                history.Append(Change(self.instance, self.member, old_value))
            exec('self.instance.%s = new_value' % self.member)
        
class AutoTextCtrl(wx.TextCtrl, AutoMixin):
    def __init__(self, parent, instance, member, *args, **kwargs):
        wx.TextCtrl.__init__(self, parent, -1, *args, **kwargs)
        AutoMixin.__init__(self, parent, instance, member)        

class AutoDateCtrl(DateCtrl, AutoMixin):
    def __init__(self, parent, instance, member, *args, **kwargs):
        DateCtrl.__init__(self, parent, -1, *args, **kwargs)
        AutoMixin.__init__(self, parent, instance, member)
        #ctrl = DatePickerCtrl(parent, -1, pos=(xpos + xspace, ypos), size=(xsize, -1), style=wx.DP_DROPDOWN | wx.DP_ALLOWNONE | style)
        #self.Bind(wx.EVT_DATE_CHANGED, self.onText, ctrl)

class AutoNumericCtrl(NumericCtrl, AutoMixin):
    def __init__(self, parent, instance, member, *args, **kwargs):
        NumericCtrl.__init__(self, parent, *args, **kwargs)
        AutoMixin.__init__(self, parent, instance, member)

class AutoPhoneCtrl(PhoneCtrl, AutoMixin):
    def __init__(self, parent, instance, member, *args, **kwargs):
        PhoneCtrl.__init__(self, parent, -1, *args, **kwargs)
        AutoMixin.__init__(self, parent, instance, member)

class AutoChoiceCtrl(wx.Choice, AutoMixin):
    def __init__(self, parent, instance, member, items=None, *args, **kwargs):
        wx.Choice.__init__(self, parent, -1, *args, **kwargs) # style=wxCB_SORT        
        self.values = {}
        if items:
            self.SetItems(items)
        AutoMixin.__init__(self, parent, instance, member)
        parent.Bind(wx.EVT_CHOICE, self.onChoice, self)

    def Append(self, item, clientData):
        index = wx.Choice.Append(self, item, clientData)
        self.values[clientData] = index
        
    def onChoice(self, event):
        value = event.GetClientData()
        self.AutoChange(event.GetClientData())
        event.Skip()
    
    def SetValue(self, value):
        if eval('self.instance.%s' % self.member) != value:
            exec('self.instance.%s = value' % self.member)
            self.UpdateContents()
    
    def UpdateContents(self):
        if not self.instance:
            self.Disable()
        else:
            self.Enable()
            value = eval('self.instance.%s' % self.member)
            if value in self.values:
                self.SetSelection(self.values[value])
            else:
                self.SetSelection(-1)

    def SetItems(self, items):
        wx.Choice.Clear(self)
        self.values.clear()
        for item, clientData in items:
            self.Append(item, clientData)

class AutoCheckBox(wx.CheckBox, AutoMixin):
    def __init__(self, parent, instance, member, label, *args, **kwargs):
        wx.CheckBox.__init__(self, parent, -1, label)
        AutoMixin.__init__(self, parent, instance, member)
        parent.Bind(wx.EVT_CHECKBOX, self.EvtCheckbox, self)

    def EvtCheckbox(self, event):
        box = event.GetEventObject()
        self.AutoChange(event.Checked())
        
class AutoRadioBox(wx.RadioBox, AutoMixin):
    def __init__(self, parent, instance, member, label, choices, *args, **kwargs):
        wx.RadioBox.__init__(self, parent, -1, label=label, choices=choices)
        AutoMixin.__init__(self, parent, instance, member)
        parent.Bind(wx.EVT_RADIOBOX, self.EvtRadiobox, self)

    def EvtRadiobox(self, event):
        self.AutoChange(event.GetInt())
        
    def SetValue(self, value):
        self.SetSelection(value)

class DatePickerCtrl(wx.DatePickerCtrl):
  _GetValue = wx.DatePickerCtrl.GetValue
  _SetValue = wx.DatePickerCtrl.SetValue

  def GetValue(self):
    if self._GetValue().IsValid():
      return datetime.date(self._GetValue().GetYear(), self._GetValue().GetMonth()+1, self._GetValue().GetDay())
    else:
      return None

  def SetValue(self, dt):
    if dt is None:
      self._SetValue(wx.DateTime())
    else:
      self._SetValue(wx.DateTimeFromDMY(dt.day, dt.month-1, dt.year))

class PeriodeDialog(wx.Dialog):
    def __init__(self, parent, periode):
        wx.Dialog.__init__(self, parent, -1, u"Modifier une période", wx.DefaultPosition, wx.DefaultSize)
        self.periode = periode
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.fields_sizer = wx.FlexGridSizer(0, 2, 5, 10)
        self.fields_sizer.AddGrowableCol(1, 1)
        self.debut_ctrl = DateCtrl(self)
        self.debut_ctrl.SetValue(periode.debut)
        self.fields_sizer.AddMany([(wx.StaticText(self, -1, u"Début :"), 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALL-wx.BOTTOM, 5), (self.debut_ctrl, 0, wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL|wx.ALL-wx.BOTTOM, 5)])
        self.fin_ctrl = DateCtrl(self)
        self.fin_ctrl.SetValue(periode.fin)
        self.fields_sizer.AddMany([(wx.StaticText(self, -1, "Fin :"), 0, wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5), (self.fin_ctrl, 0, wx.EXPAND|wx.ALIGN_CENTRE_VERTICAL|wx.ALL, 5)])
        self.sizer.Add(self.fields_sizer, 0, wx.EXPAND|wx.ALL, 5)
        self.btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        self.btnsizer.AddButton(btn)
        btn = wx.Button(self, wx.ID_CANCEL)
        self.btnsizer.AddButton(btn)
        self.btnsizer.Realize()       
        self.sizer.Add(self.btnsizer, 0, wx.ALL, 5)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        
class PeriodeChoice(wx.BoxSizer):
    def __init__(self, parent, instance, member, constructor):
        wx.BoxSizer.__init__(self, wx.HORIZONTAL)
        self.parent = parent
        self.parent.periode = 0
        self.constructor = constructor

        self.periodechoice = wx.Choice(parent, size=(200,-1))
        parent.Bind(wx.EVT_CHOICE, self.EvtPeriodeChoice, self.periodechoice)
        delbmp = wx.Bitmap("bitmaps/remove.png", wx.BITMAP_TYPE_PNG)
        plusbmp = wx.Bitmap("bitmaps/plus.png", wx.BITMAP_TYPE_PNG)
        settingsbmp = wx.Bitmap("bitmaps/settings.png", wx.BITMAP_TYPE_PNG)
        self.periodeaddbutton = wx.BitmapButton(parent, -1, plusbmp, style=wx.BU_EXACTFIT)
        self.periodeaddbutton.SetToolTipString(u"Ajouter une période")
        self.periodedelbutton = wx.BitmapButton(parent, -1, delbmp, style=wx.BU_EXACTFIT)
        self.periodedelbutton.SetToolTipString(u"Supprimer la période")
        self.periodesettingsbutton = wx.BitmapButton(parent, -1, settingsbmp, style=wx.BU_EXACTFIT)
        self.periodesettingsbutton.SetToolTipString(u"Modifier la période")
        
        self.Add(self.periodechoice, 1, wx.EXPAND)
        self.Add(self.periodeaddbutton, 0, wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, 5)
        self.Add(self.periodedelbutton, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 5)
        self.Add(self.periodesettingsbutton, 0, wx.ALIGN_CENTER_VERTICAL)
        parent.Bind(wx.EVT_BUTTON, self.EvtPeriodeAddButton, self.periodeaddbutton)
        parent.Bind(wx.EVT_BUTTON, self.EvtPeriodeDelButton, self.periodedelbutton)
        parent.Bind(wx.EVT_BUTTON, self.EvtPeriodeSettingsButton, self.periodesettingsbutton)
        parent.ctrls.append(self)
        self.SetInstance(instance, member)
        
    def SetInstance(self, instance, member=None):
        self.instance = instance
        if member:
            self.member = member
        if not self.instance:
            self.Disable()
            self.parent.periode = 0
        else:
            self.parent.periode = eval('len(instance.%s) - 1' % self.member)
            self.periodechoice.Clear()
            for item in eval('instance.%s' % self.member):
                self.periodechoice.Append(periodestr(item))

            self.Enable()
            self.periodechoice.SetSelection(self.parent.periode)
            
    def UpdateContents(self):
        pass
      
    def EvtPeriodeChoice(self, evt):
        ctrl = evt.GetEventObject()
        self.parent.periode = ctrl.GetSelection()
        self.parent.UpdateContents()
        self.Enable()
  
    def EvtPeriodeAddButton(self, evt):
        last_periode = eval('self.instance.'+self.member+'[-1]')       
        periode_nb = eval('len(self.instance.%s)' % self.member)
        new_periode = self.constructor()
        new_periode.debut = last_periode.fin + datetime.timedelta(1)
        if last_periode.debut.day == new_periode.debut.day and last_periode.debut.month == new_periode.debut.month:
            new_periode.fin = datetime.date(last_periode.fin.year+new_periode.debut.year-last_periode.debut.year, last_periode.fin.month, last_periode.fin.day)
        exec('self.instance.%s.append(new_periode)' % self.member)
        self.periodechoice.Append(periodestr(new_periode))
        self.periodechoice.SetSelection(periode_nb)
        self.parent.periode = periode_nb
        self.parent.UpdateContents()
        self.Enable()
        history.Append(Delete(self.instance, self.member+'[-1]'))

    def EvtPeriodeDelButton(self, evt):
        index = self.periodechoice.GetSelection()
        periode = eval('self.instance.'+self.member+'[index]')
        history.Append(Append(self.instance, self.member, self.constructor))
        # TODO pas fini
        #for ctrl in self.parent.ctrls:
        #    print ctrl.member
        exec('self.instance.'+self.member+'[index].delete()')
        exec('del self.instance.'+self.member+'[index]')
        self.periodechoice.Delete(index)
        last_periode = eval('len(self.instance.'+self.member+') - 1')
        self.periodechoice.SetSelection(last_periode)
        self.parent.periode = last_periode
        self.parent.UpdateContents()
        self.Enable()

    def EvtPeriodeSettingsButton(self, evt):
        periode = eval('self.instance.'+self.member+'[self.parent.periode]')
        dlg = PeriodeDialog(self.parent, periode)
        response = dlg.ShowModal()
	dlg.Destroy()
        if response == wx.ID_OK:
            history.Append([Change(self.instance, self.member+'[%d].debut' % self.parent.periode, periode.debut), Change(self.instance, self.member+'[%d].fin' % self.parent.periode, periode.fin)])
            periode.debut, periode.fin = dlg.debut_ctrl.GetValue(), dlg.fin_ctrl.GetValue()
            self.periodechoice.SetString(self.parent.periode, periodestr(periode))
            self.periodechoice.SetSelection(self.parent.periode)
            self.Enable()

    def Enable(self, value=True):
        self.periodechoice.Enable(value)
        if self.instance and eval('self.instance.'+self.member+'[-1]').fin:
            self.periodeaddbutton.Enable(value)
        else:
            self.periodeaddbutton.Disable()
        count = self.periodechoice.GetCount()
        if count <= 1 or self.parent.periode != count - 1:
            self.periodedelbutton.Disable()
        else:
            self.periodedelbutton.Enable(value)
    
    def Disable(self):
        self.Enable(False)

class AutoTab(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent)
        self.parent = parent
        self.ctrls = []
        self.SetAutoLayout(1)
        self.SetupScrolling()
           
    def UpdateContents(self):
        for ctrl in self.ctrls:
            ctrl.UpdateContents()
            
class PeriodePanel(wx.Panel):
    def __init__(self, parent, *args, **kwargs):
        wx.Panel.__init__(self, parent, -1, *args, **kwargs)
        self.ctrls = []
        parent.ctrls.append(self)
    
    def UpdateContents(self):
        for ctrl in self.ctrls:
            ctrl.UpdateContents()
    
    def SetInstance(self, instance):
        for ctrl in self.ctrls:
            ctrl.SetInstance(instance)
        
        
