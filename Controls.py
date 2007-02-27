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

import wx
import fpformat
import datetime
from common import *
              
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

        # set up action
##        self.__action = Closure.Closure()
##        if callable(action):  self.__action.func = action
##        if len(action_kw.keys())>0:  self.__action.kw = action_kw

        this_sty = wx.TAB_TRAVERSAL| wx.TE_PROCESS_ENTER
        kw = kwargs

        if kw.has_key('style'): this_sty = this_sty | kw['style']
        kw['style'] = this_sty
            
        wx.TextCtrl.__init__(self, parent, id, value=value, *args, **kw)
        
        #self.__CheckValid(self.__val)
        #self.SetValue(self.__val)
              
        wx.EVT_CHAR(self, self.onChar)
        #wx.EVT_TEXT(self, -1,self.onText)
        #wx.EVT_SET_FOCUS(self, self.onSetFocus)
        #wx.EVT_KILL_FOCUS(self, self.onKillFocus)
        #wx.EVT_SIZE(self, self.onResize)
        #self.__GetMark()

##    def SetAction(self,action,action_kw={}):
##        self.__action = Closure.Closure()
##        if callable(action):         self.__action.func = action
##        if len(action_kw.keys())>0:  self.__action.kw = action_kw
        
    def SetPrecision(self,p):
        self.__prec = p
        self.format = '%.'+str(self.__prec)+'f'
        
##    def __GetMark(self):
##        " keep track of cursor position within text"
##        try:
##            self.__mark = min(wx.TextCtrl.GetSelection(self)[0],
##                              len(wx.TextCtrl.GetValue(self).strip()))
##        except:
##            self.__mark = 0
##
##    def __SetMark(self,m=None):
##        " "
##        if m==None: m = self.__mark
##        self.SetSelection(m,m)
##
##    def SetValue(self,value,act=True):
##        " main method to set value "
##        if value == None: value = wx.TextCtrl.GetValue(self).strip()
##        self.__CheckValid(value)
##        self.__GetMark()
##        if self.__valid:
##            self.__Text_SetValue(self.__val)
##            self.SetForegroundColour(self.__fgcol_valid)
##            self.SetBackgroundColour(self.__bgcol_valid)
##            if  callable(self.__action) and act:  self.__action(value=self.__val)
##        else:
##            self.__val = self.__bound_val
##            self.__Text_SetValue(self.__val)
##            self.__CheckValid(self.__val)
##            self.SetForegroundColour(self.__fgcol_invalid)
##            self.SetBackgroundColour(self.__bgcol_invalid)
##            wx.Bell()
##        self.__SetMark()
##
##    def onKillFocus(self, event):
##        self.__GetMark()
##        event.Skip()
##
##    def onResize(self, event):
##        event.Skip()
##
##    def onSetFocus(self, event):
##        self.__SetMark()
##        event.Skip()
        
    def onChar(self, event):
        """ on Character event"""
        key   = event.KeyCode()
        entry = wx.TextCtrl.GetValue(self).strip()
        # really, the order here is important:
        # 1. return sends to ValidateEntry
##        if (key == wx.WXK_RETURN):
##            self.SetValue(entry)
##            return

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

##    def onText(self, event=None):
##        try:
##            if event.GetString() != '':
##                self.__CheckValid(event.GetString())
##        except:
##            pass
##        event.Skip()

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

        wx.TextCtrl.__init__(self, parent, id, size=(90, 21), *args, **kw)
        self.SetMaxLength(14)

        wx.EVT_CHAR(self, self.onChar)
#        wx.EVT_TEXT(self, -1, self.onText)
        wx.EVT_LEFT_DOWN(self, self.OnLeftDown)
       
    def onChar(self, event):
        """ on Character event"""
        ip = self.GetInsertionPoint()
        lp = self.GetLastPosition()
        key   = event.KeyCode()

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
    def __init__(self, parent, id, value=None, *args, **kwargs):
        wx.TextCtrl.__init__(self, parent, id, *args, **kwargs)
        
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

    def getdate(self, str):
        day = str.strip()
        try:
            (jour, mois, annee) = map(lambda x: int(x), day.split('/'))
            if annee < 2000:
                return None
            else:
                return datetime.date(annee, mois, jour)
        except:
            return None
    
    def GetValue(self):
        if (wx.TextCtrl.GetValue(self) == ""):
            return None
        else:
            return self.getdate(wx.TextCtrl.GetValue(self))

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
            value = obj.GetValue()
            if eval('self.instance.%s' % self.member) != value:
                exec('self.instance.%s = value' % self.member)
        event.Skip()
        
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
        if eval('self.instance.%s' % self.member) != value:
            exec('self.instance.%s = value' % self.member)
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
        value = event.Checked()
        exec("self.instance." + self.member + " = value")
        
class AutoRadioBox(wx.RadioBox, AutoMixin):
    def __init__(self, parent, instance, member, label, choices, *args, **kwargs):
        wx.RadioBox.__init__(self, parent, -1, label=label, choices=choices)
        AutoMixin.__init__(self, parent, instance, member)
        parent.Bind(wx.EVT_RADIOBOX, self.EvtRadiobox, self)

    def EvtRadiobox(self, event):
        value = event.GetInt()
        exec('self.instance.%s = value' % self.member)
        
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
      
class PeriodeChoice(wx.BoxSizer):
    def __init__(self, parent, instance, member, constructor):
        wx.BoxSizer.__init__(self, wx.VERTICAL)
        self.parent = parent
        self.parent.periode = 0
        self.constructor = constructor
        
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.periodechoice = wx.Choice(parent, -1)
        sizer1.AddMany([(wx.StaticText(parent, -1, u'Période :'), 0, wx.ALIGN_CENTER_VERTICAL), (self.periodechoice, 0, wx.EXPAND)])
        parent.Bind(wx.EVT_CHOICE, self.EvtPeriodeChoice, self.periodechoice)
        self.periodeaddbutton = wx.Button(parent, -1, "Ajout")
        self.periodedelbutton = wx.Button(parent, -1, "Suppression")
        sizer1.AddMany([self.periodeaddbutton, self.periodedelbutton])
        parent.Bind(wx.EVT_BUTTON, self.EvtPeriodeAddButton, self.periodeaddbutton)
        parent.Bind(wx.EVT_BUTTON, self.EvtPeriodeDelButton, self.periodedelbutton)
        parent.ctrls.append(self)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)

        date_debut = AutoDateCtrl(parent, instance, member+'[self.parent.periode].debut')
        sizer2.AddMany([(wx.StaticText(parent, -1, u'Début :'), 0, wx.ALIGN_CENTER_VERTICAL), date_debut])
        date_fin = AutoDateCtrl(parent, instance, member+'[self.parent.periode].fin', style=wx.DP_ALLOWNONE)
        sizer2.AddMany([(wx.StaticText(parent, -1, 'Fin :'), 0, wx.ALIGN_CENTER_VERTICAL), date_fin])
        #parent.Bind(wx.EVT_DATE_CHANGED, self.EvtChangementPeriode, date_debut)
        #parent.Bind(wx.EVT_DATE_CHANGED, self.EvtChangementPeriode, date_fin)
        parent.Bind(wx.EVT_TEXT, self.EvtChangementPeriode, date_debut)
        parent.Bind(wx.EVT_TEXT, self.EvtChangementPeriode, date_fin)
        
        self.AddMany([sizer1, sizer2])
        self.SetInstance(instance, member)
        
    def SetInstance(self, instance, member=None):
        self.instance = instance
        if member:
            self.member = member
        if not self.instance:
            self.Disable()
            self.parent.periode = 0
        else:
            self.Enable()        
            self.parent.periode = eval('len(instance.%s) - 1' % self.member)
            self.periodechoice.Clear()
            for item in eval('instance.%s' % self.member):
                self.periodechoice.Append(periodestr(item))

            count = self.periodechoice.GetCount()
            if count > 1 and self.parent.periode == count - 1:
                self.periodedelbutton.Enable()
            else:
                self.periodedelbutton.Disable()
            if count > 1:
                self.periodechoice.Enable()
            else:
                self.periodechoice.Disable()
            self.periodechoice.SetSelection(self.parent.periode)
            
    def UpdateContents(self):
        pass
      
    def EvtPeriodeChoice(self, evt):
        ctrl = evt.GetEventObject()
        self.parent.periode = ctrl.GetSelection()
        self.parent.UpdateContents()
  
    def EvtPeriodeAddButton(self, evt):
        periode_nb = eval('len(self.instance.%s)' % self.member)
        exec('self.instance.%s.append(self.constructor())' % self.member)
        periode = eval('self.instance.'+self.member+'[periode_nb]')
        self.periodechoice.Append(periodestr(periode))
        self.periodechoice.Enable()
        self.periodedelbutton.Enable()
        self.parent.periode = periode_nb
        self.parent.UpdateContents()
  
    def EvtPeriodeDelButton(self, evt):
        periode = self.periodechoice.GetSelection()
        exec('self.instance.'+self.member+'[periode].delete()')
        exec('del self.instance.'+self.member+'[periode]')
        self.periodechoice.Delete(periode)
        last_periode = eval('len(self.instance.'+self.member+') - 1')
        self.periodechoice.SetSelection(last_periode)
        if last_periode == 0:
          self.periodechoice.Disable()
          self.periodedelbutton.Disable()
        self.parent.periode = last_periode
        self.parent.UpdateContents()

    def EvtChangementPeriode(self, event):
        obj = event.GetEventObject()
        obj.onText(event)
        value = obj.GetValue()
        periode = eval('self.instance.'+self.member+'[self.parent.periode]')            
        self.periodechoice.SetString(self.parent.periode, periodestr(periode))
        self.periodechoice.SetSelection(self.parent.periode)
        event.Skip()    

    def Enable(self, value=True):
        self.periodechoice.Enable(value)
        self.periodeaddbutton.Enable(value)
        self.periodedelbutton.Enable(value)
        count = self.periodechoice.GetCount()
        if count <= 1 or self.parent.periode != count - 1:
            self.periodedelbutton.Disable()
    
    def Disable(self):
        self.Enable(False)

class AutoTab(wx.lib.scrolledpanel.ScrolledPanel):
    def __init__(self, parent):
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent)
        self.parent = parent
        self.ctrls = []
           
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
        
        
