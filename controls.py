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

import wx
import wx.lib
import wx.lib.scrolledpanel
import wx.lib.masked
import wx.lib.stattext
import wx.combo
from wx.lib.masked import Field
from helpers import *
from functions import *
from config import config
from history import Change, Insert, Delete


class GPanel(wx.Panel):
    def __init__(self, parent, title):
        wx.Panel.__init__(self, parent, style=wx.LB_DEFAULT)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        if sys.platform == 'win32':
            st = wx.StaticText(self, -1, title, size=(-1, 24), style=wx.BORDER_SUNKEN | wx.ST_NO_AUTORESIZE)
            font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
        else:
            st = wx.lib.stattext.GenStaticText(self, -1, ' ' + title, size=(-1, 28),
                                               style=wx.BORDER_SUNKEN | wx.ST_NO_AUTORESIZE)
            font = st.GetFont()
            font.SetPointSize(14)
        st.SetFont(font)
        st.SetBackgroundColour(wx.Colour(10, 36, 106))
        st.SetBackgroundStyle(wx.BG_STYLE_COLOUR)
        st.SetForegroundColour(wx.Colour(255, 255, 255))
        sizer.Add(st, 1, wx.EXPAND)
        self.sizer.Add(sizer, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL | wx.BOTTOM, 5)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)

    def UpdateContents(self):
        pass


class NumericCtrl(wx.TextCtrl):
    def __init__(self, parent, id=-1, value="", min=None, max=None, precision=3, action_kw={}, *args, **kwargs):
        self.__digits = '0123456789.-'
        self.__prec = precision
        self.format = '%.' + str(self.__prec) + 'f'
        self.__val = 0
        self.__min, self.__max = None, None
        if max is not None:
            self.__max = float(max)
        if min is not None:
            self.__min = float(min)

        wx.TextCtrl.__init__(self, parent, id, value=value, *args, **kwargs)

        self.Bind(wx.EVT_CHAR, self.onChar)

    def SetPrecision(self, p):
        self.__prec = p
        self.format = '%.' + str(self.__prec) + 'f'

    def onChar(self, event):
        """ on Character event"""
        key = event.KeyCode
        entry = wx.TextCtrl.GetValue(self).strip()

        # 2. other non-text characters are passed without change
        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()
            return

        # 3. check for multiple '.' and out of place '-' signs and ignore these
        #    note that chr(key) will now work due to return at #2
        pos = wx.TextCtrl.GetSelection(self)[0]
        has_minus = '-' in entry
        if ((chr(key) == '.' and (self.__prec == 0 or '.' in entry)) or
                (chr(key) == '-' and (has_minus or pos != 0 or (self.__min is not None and self.__min >= 0))) or
                (chr(key) != '-' and has_minus and pos == 0)):
            return
        # 4. allow digits, but not other characters
        if chr(key) in self.__digits:
            event.Skip()
            return

    def GetValue(self):
        if wx.TextCtrl.GetValue(self) == "":
            return None
        elif self.__prec > 0:
            return float(wx.TextCtrl.GetValue(self))
        else:
            return int(wx.TextCtrl.GetValue(self))

        #    def __Text_SetValue(self,value):

    def SetValue(self, value):
        if value != "":
            wx.TextCtrl.SetValue(self, self.format % float(value))
        else:
            wx.TextCtrl.SetValue(self, "")
        self.Refresh()

    def GetMin(self):
        return self.__min

    def GetMax(self):
        return self.__max

    def SetMin(self, min):
        try:
            self.__min = float(min)
        except:
            pass
        return self.__min

    def SetMax(self, max):
        try:
            self.__max = float(max)
        except:
            pass
        return self.__max


PHONECTRL_WIDTH = 0


class PhoneCtrl(wx.TextCtrl):
    def __init__(self, parent, id, value=None, action_kw={}, *args, **kwargs):
        global PHONECTRL_WIDTH

        self.__digits = '0123456789'

        # this_sty = wx.TAB_TRAVERSAL| wx.TE_PROCESS_ENTER
        kw = kwargs

        wx.TextCtrl.__init__(self, parent.GetWindow(), id, size=(-1, -1), *args, **kw)
        self.SetMaxLength(14)
        if PHONECTRL_WIDTH == 0:
            dc = wx.WindowDC(self)
            PHONECTRL_WIDTH = dc.GetMultiLineTextExtent("00 00 00 00 00", self.GetFont())[0]
        self.SetMinSize((PHONECTRL_WIDTH + 15, -1))

        wx.EVT_CHAR(self, self.onChar)
        wx.EVT_TEXT(self, -1, self.checkSyntax)
        wx.EVT_LEFT_DOWN(self, self.OnLeftDown)

    def onChar(self, event):
        """ on Character event"""
        ip = self.GetInsertionPoint()
        lp = self.GetLastPosition()
        key = event.KeyCode

        # 2. other non-text characters are passed without change
        if key == wx.WXK_BACK:
            if ip > 0:
                self.RemoveChar(ip - 1)
            return

        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()
            wx.CallAfter(self.Arrange, key)
            return

        # 4. allow digits, but not other characters
        if chr(key) in self.__digits:
            event.Skip()
            wx.CallAfter(self.Arrange, key)

    def checkSyntax(self, event=None):
        value = self.GetValue()
        if value != "" and len(value) != 14:
            self.SetBackgroundColour(wx.RED)
        else:
            self.SetBackgroundColour(wx.WHITE)
        self.Refresh()
        event.Skip()

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
                if len(arranged) < 14 and len(arranged) % 3 == 2:
                    arranged += " "
            else:
                ip -= 1

        if arranged != value:
            self.SetValue(arranged)

        if sel == (ip, ip) or arranged != value:
            if (ip == len(arranged) or arranged[ip] != " "):
                self.SetInsertionPoint(ip)
            elif key == wx.WXK_LEFT:
                self.SetInsertionPoint(ip - 1)
            else:
                self.SetInsertionPoint(ip + 1)

    def RemoveChar(self, index):
        value = self.GetValue()
        if value[index] == " ":
            value = value[:index - 1] + value[index + 1:]
            index -= 1
        else:
            value = value[:index] + value[index + 1:]

        self.SetValue(value)
        self.SetInsertionPoint(index)
        self.Arrange(wx.WXK_BACK)

    def OnLeftDown(self, event):
        if event.LeftDown():
            event.Skip()
            wx.CallAfter(self.OnCursorMoved, event)

    def OnCursorMoved(self, event):
        ip = self.GetInsertionPoint()
        if ip < 14 and ip % 3 == 2:
            self.SetInsertionPoint(ip + 1)


if 0:  # sys.platform == 'win32':
    class DateCtrl(wx.GenericDatePickerCtrl):
        def SetValue(self, date):
            if date is None:
                date = wx.DefaultDateTime
            if isinstance(date, (datetime.datetime, datetime.date)):
                tt = date.timetuple()
                dmy = (tt[2], tt[1] - 1, tt[0])
                date = wx.DateTimeFromDMY(*dmy)
            wx.GenericDatePickerCtrl.SetValue(self, date)

        def GetValue(self):
            date = wx.GenericDatePickerCtrl.GetValue(self)
            if date.IsValid():
                ymd = map(int, date.FormatISODate().split('-'))
                return datetime.date(*ymd)
            else:
                return None
else:
    DATECTRL_WIDTH = 0


    class DateCtrl(wx.TextCtrl):
        def __init__(self, parent, id=-1, value=None, mois=False, *args, **kwargs):
            global DATECTRL_WIDTH
            self.mois = mois
            wx.TextCtrl.__init__(self, parent, id=-1, *args, **kwargs)
            if DATECTRL_WIDTH == 0:
                dc = wx.WindowDC(self)
                DATECTRL_WIDTH = dc.GetMultiLineTextExtent("00/00/0000 ", self.GetFont())[0]
            self.SetMinSize((DATECTRL_WIDTH + 10, -1))
            wx.EVT_TEXT(self, -1, self.checkSyntax)
            if value is not None:
                self.SetValue(value)

        def checkSyntax(self, event=None):
            str = wx.TextCtrl.GetValue(self)
            if str == "":
                self.SetBackgroundColour(wx.WHITE)
            elif self.mois and (
                    str.lower() in [m.lower() for m in months] or (str.isdigit() and int(str) in range(1, 13))):
                self.SetBackgroundColour(wx.WHITE)
            else:
                if self.mois:
                    r = str2date(str, day=1)
                else:
                    r = str2date(str)
                if r:
                    self.SetBackgroundColour(wx.WHITE)
                else:
                    self.SetBackgroundColour(wx.RED)
            self.Refresh()
            event.Skip()

        def GetValue(self):
            if self.mois:
                return wx.TextCtrl.GetValue(self)
            elif wx.TextCtrl.GetValue(self) == "":
                return None
            else:
                return str2date(wx.TextCtrl.GetValue(self))

        def SetValue(self, value):
            if value is None:
                wx.TextCtrl.SetValue(self, '')
            elif self.mois:
                wx.TextCtrl.SetValue(self, value)
            else:
                wx.TextCtrl.SetValue(self, '%.02d/%.02d/%.04d' % (value.day, value.month, value.year))
            self.Refresh()


class TimeCtrl(wx.lib.masked.TimeCtrl):
    def __init__(self, parent):
        self.spin = wx.SpinButton(parent, -1, wx.DefaultPosition, (-1, 10), wx.SP_VERTICAL)
        self.spin.SetRange(-100000, +100000)
        self.spin.SetValue(0)
        wx.lib.masked.TimeCtrl.__init__(self, parent, id=-1, fmt24hr=True, display_seconds=False, spinButton=self.spin)

    def SetParameters(self, **kwargs):
        """
        Function providing access to the parameters governing TimeCtrl display and bounds.
        """
        maskededit_kwargs = {}
        reset_format = False

        if kwargs.has_key('display_seconds'):
            kwargs['displaySeconds'] = kwargs['display_seconds']
            del kwargs['display_seconds']
        if kwargs.has_key('format') and kwargs.has_key('displaySeconds'):
            del kwargs['displaySeconds']  # always apply format if specified

        # assign keyword args as appropriate:
        for key, param_value in kwargs.items():
            if key not in TimeCtrl.valid_ctrl_params.keys():
                raise AttributeError('invalid keyword argument "%s"' % key)

            if key == 'format':
                wxdt = wx.DateTimeFromDMY(1, 0, 1970)
                try:
                    if wxdt.Format('%p') != 'AM':
                        require24hr = True
                    else:
                        require24hr = False
                except:
                    require24hr = True

                # handle both local or generic 'maskededit' autoformat codes:
                if param_value == 'HHMMSS' or param_value == 'TIMEHHMMSS':
                    self.__displaySeconds = True
                    self.__fmt24hr = False
                elif param_value == 'HHMM' or param_value == 'TIMEHHMM':
                    self.__displaySeconds = False
                    self.__fmt24hr = False
                elif param_value == '24HHMMSS' or param_value == '24HRTIMEHHMMSS':
                    self.__displaySeconds = True
                    self.__fmt24hr = True
                elif param_value == '24HHMM' or param_value == '24HRTIMEHHMM':
                    self.__displaySeconds = False
                    self.__fmt24hr = True
                else:
                    raise AttributeError('"%s" is not a valid format' % param_value)

                if require24hr and not self.__fmt24hr:
                    raise AttributeError('"%s" is an unsupported time format for the current locale' % param_value)

                reset_format = True

            elif key in ("displaySeconds", "display_seconds") and not kwargs.has_key('format'):
                self.__displaySeconds = param_value
                reset_format = True

            elif key == "min":
                min = param_value
            elif key == "max":
                max = param_value
            elif key == "limited":
                limited = param_value

            elif key == "useFixedWidthFont":
                maskededit_kwargs[key] = param_value

            elif key == "oob_color":
                maskededit_kwargs['invalidBackgroundColor'] = param_value

        if reset_format:
            if self.__fmt24hr:
                if self.__displaySeconds:
                    maskededit_kwargs['autoformat'] = '24HRTIMEHHMMSS'
                else:
                    maskededit_kwargs['autoformat'] = '24HRTIMEHHMM'

                # Set hour field to zero-pad, right-insert, require explicit field change,
                # select entire field on entry, and require a resultant valid entry
                # to allow character entry:
                hourfield = Field(formatcodes='0r<SV', validRegex='0\d|1\d|2[0123]', validRequired=True)
            else:
                if self.__displaySeconds:
                    maskededit_kwargs['autoformat'] = 'TIMEHHMMSS'
                else:
                    maskededit_kwargs['autoformat'] = 'TIMEHHMM'

                # Set hour field to allow spaces (at start), right-insert,
                # require explicit field change, select entire field on entry,
                # and require a resultant valid entry to allow character entry:
                hourfield = Field(formatcodes='_0<rSV', validRegex='0[1-9]| [1-9]|1[012]', validRequired=True)
                ampmfield = Field(formatcodes='S', emptyInvalid=True, validRequired=True)

            # Field 1 is always a zero-padded right-insert minute field,
            # similarly configured as above:
            minutefield = Field(formatcodes='0r<SV', validRegex='[0-5][0|5]', validRequired=True)

            fields = [hourfield, minutefield]
            if self.__displaySeconds:
                fields.append(copy.copy(minutefield))  # second field has same constraints as field 1

            if not self.__fmt24hr:
                fields.append(ampmfield)

            # set fields argument:
            maskededit_kwargs['fields'] = fields

            # This allows range validation if set
            maskededit_kwargs['validFunc'] = self.IsInBounds

            # This allows range limits to affect insertion into control or not
            # dynamically without affecting individual field constraint validation
            maskededit_kwargs['retainFieldValidation'] = True

        if hasattr(self, 'controlInitialized') and self.controlInitialized:
            self.SetCtrlParameters(**maskededit_kwargs)  # set appropriate parameters
            # self.SetBounds("00:00", "23:55")
            # Validate initial value and set if appropriate
            try:
                self.SetBounds(min, max)
                self.SetLimited(limited)
                self.SetValue(value)
            except:
                self.SetValue('00:00:00')
            return {}  # no arguments to return
        else:
            return maskededit_kwargs

    def __IncrementValue(self, key, pos):
        text = self.GetValue()
        field = self._FindField(pos)
        start, end = field._extent
        slice = text[start:end]
        if key == wx.WXK_UP:
            increment = 1
        else:
            increment = -1

        if slice in ('A', 'P'):
            if slice == 'A':
                newslice = 'P'
            elif slice == 'P':
                newslice = 'A'
            newvalue = text[:start] + newslice + text[end:]

        elif field._index == 0:
            # adjusting this field is trickier, as its value can affect the
            # am/pm setting.  So, we use wxDateTime to generate a new value for us:
            # (Use a fixed date not subject to DST variations:)
            converter = wx.DateTimeFromDMY(1, 0, 1970)
            converter.ParseTime(text.strip())
            currenthour = converter.GetHour()
            newhour = (currenthour + increment) % 24
            converter.SetHour(newhour)
            newvalue = converter  # take advantage of auto-conversion for am/pm in .SetValue()

        else:  # minute or second field; handled the same way:
            increment *= 5
            newslice = "%02d" % ((int(slice) + increment) % 60)
            newvalue = text[:start] + newslice + text[end:]

        try:
            self.SetValue(newvalue)

        except ValueError:  # must not be in bounds:
            if not wx.Validator_IsSilent():
                wx.Bell()


class AutoMixin:
    default = None

    def __init__(self, parent, instance, member, fixed_instance=False, observers=[], mask=None):
        self.__ontext = True
        self.parent = parent
        self.fixed_instance = fixed_instance
        self.observers = observers
        self.mask = mask
        if not fixed_instance:
            parent.ctrls.append(self)
        self.SetInstance(instance, member)
        self.Bind(wx.EVT_TEXT, self.onText)

    def __del__(self):
        if not self.fixed_instance:
            self.parent.ctrls.remove(self)

    def SetInstance(self, instance, member=None):
        self.instance = instance
        if member:
            self.member = member
        self.UpdateContents()

    def GetCurrentValue(self):
        if self.mask:
            return eval('self.instance.%s & self.mask' % self.member)
        else:
            return eval('self.instance.%s' % self.member)

    def UpdateContents(self):
        if not self.instance:
            self.Disable()
        else:
            self.__ontext = False
            try:
                value = self.GetCurrentValue()
                self.SetValue(self.default if value is None else value)
            except Exception as e:
                print("Erreur lors de l'evaluation de self.instance.%s" % self.member, e)
            self.__ontext = True
            self.Enable(not config.readonly)

    def onText(self, event):
        obj = event.GetEventObject()
        if self.__ontext:
            self.AutoChange(obj.GetValue())
        event.Skip()

    def AutoChange(self, new_value):
        old_value = eval('self.instance.%s' % self.member)
        if self.mask is not None:
            new_value |= old_value & ~self.mask
        if old_value != new_value:
            last = history.Last()
            if last is not None and len(last) == 1 and isinstance(last[-1], Change):
                if last[-1].instance is not self.instance or last[-1].member != self.member:
                    history.Append(Change(self.instance, self.member, old_value))
            else:
                history.Append(Change(self.instance, self.member, old_value))
            exec ('self.instance.%s = new_value' % self.member)
            for o in self.observers:
                counters[o] += 1


class AutoTextCtrl(wx.TextCtrl, AutoMixin):
    default = ""

    def __init__(self, parent, instance, member, fixed_instance=False, observers=[], *args, **kwargs):
        wx.TextCtrl.__init__(self, parent.GetWindow(), -1, *args, **kwargs)
        AutoMixin.__init__(self, parent, instance, member, fixed_instance, observers)

    def __del__(self):
        AutoMixin.__del__(self)


class AutoComboBox(wx.ComboBox, AutoMixin):
    def __init__(self, parent, instance, member, fixed_instance=False, observers=[], *args, **kwargs):
        wx.ComboBox.__init__(self, parent.GetWindow(), -1, *args, **kwargs)
        AutoMixin.__init__(self, parent, instance, member, fixed_instance, observers)

    def __del__(self):
        AutoMixin.__del__(self)


class AutoDateCtrl(DateCtrl, AutoMixin):
    default = None

    def __init__(self, parent, instance, member, fixed_instance=False, observers=[], *args, **kwargs):
        DateCtrl.__init__(self, parent.GetWindow(), id=-1,
                          style=wx.DP_DEFAULT | wx.DP_DROPDOWN | wx.DP_SHOWCENTURY | wx.DP_ALLOWNONE, *args, **kwargs)
        AutoMixin.__init__(self, parent, instance, member, fixed_instance, observers)
        # self.Bind(wx.EVT_DATE_CHANGED, self.onText, self)
        # DateCtrl.__init__(self, parent, -1, *args, **kwargs)
        # AutoMixin.__init__(self, parent, instance, member)

    def __del__(self):
        AutoMixin.__del__(self)


class AutoTimeCtrl(TimeCtrl, AutoMixin):
    def __init__(self, parent, instance, member, fixed_instance=False, observers=[], *args, **kwargs):
        TimeCtrl.__init__(self, parent)
        AutoMixin.__init__(self, parent, instance, member, fixed_instance, observers)
        self.SetMin("05:00")

    def __del__(self):
        AutoMixin.__del__(self)

    def SetValue(self, value):
        if isinstance(value, float):
            wx.lib.masked.TimeCtrl.SetValue(self, "%02d:%02d" % (int(value), round((value - int(value)) * 60)))
        else:
            wx.lib.masked.TimeCtrl.SetValue(self, value)

    def onText(self, event):
        value = self.GetValue()
        try:
            self.AutoChange(float(value[:2]) + float(value[3:5]) / 60)
        except:
            pass
        event.Skip()


class AutoNumericCtrl(NumericCtrl, AutoMixin):
    default = ""

    def __init__(self, parent, instance, member, fixed_instance=False, observers=[], *args, **kwargs):
        NumericCtrl.__init__(self, parent.GetWindow(), *args, **kwargs)
        AutoMixin.__init__(self, parent, instance, member, fixed_instance, observers)

    def __del__(self):
        AutoMixin.__del__(self)


class AutoPhoneCtrl(PhoneCtrl, AutoMixin):
    default = ""

    def __init__(self, parent, instance, member, fixed_instance=False, observers=[], *args, **kwargs):
        PhoneCtrl.__init__(self, parent, -1, *args, **kwargs)
        AutoMixin.__init__(self, parent, instance, member, fixed_instance, observers)

    def __del__(self):
        AutoMixin.__del__(self)


if sys.platform == "win32":
    class ChoiceWithoutScroll(wx.Choice):
        def onMouseWheel(self, event):
            pass

        def __init__(self, *args, **kwargs):
            wx.Choice.__init__(self, *args, **kwargs)
            self.Bind(wx.EVT_MOUSEWHEEL, self.onMouseWheel)
else:
    ChoiceWithoutScroll = wx.Choice


class ChoiceCtrl(ChoiceWithoutScroll):
    def __init__(self, parent, items=None):
        ChoiceWithoutScroll.__init__(self, parent, -1)
        if items:
            self.SetItems(items)

    def SetItems(self, items):
        ChoiceWithoutScroll.Clear(self)
        for item in items:
            if isinstance(item, tuple):
                self.Append(item[0], item[1])
            else:
                self.Append(item, item)

    def GetValue(self):
        selected = self.GetSelection()
        return self.GetClientData(selected)


class AutoChoiceCtrl(ChoiceWithoutScroll, AutoMixin):
    def __init__(self, parent, instance, member, items=None, fixed_instance=False, observers=[], mask=None, *args, **kwargs):
        ChoiceWithoutScroll.__init__(self, parent, -1, *args, **kwargs)
        self.values = {}
        if items:
            self.SetItems(items)
        AutoMixin.__init__(self, parent, instance, member, fixed_instance, observers, mask)
        parent.Bind(wx.EVT_CHOICE, self.onChoice, self)

    def __del__(self):
        AutoMixin.__del__(self)

    def Append(self, item, clientData):
        index = ChoiceWithoutScroll.Append(self, item, clientData)
        self.values[clientData] = index

    def onChoice(self, event):
        self.AutoChange(event.GetClientData())
        event.Skip()

    def SetValue(self, value):
        if self.GetCurrentValue() != value:
            exec ('self.instance.%s = value' % self.member)
            self.UpdateContents()

    def UpdateContents(self):
        if not self.instance:
            self.Disable()
        else:
            value = self.GetCurrentValue()
            if value in self.values:
                self.SetSelection(self.values[value])
            else:
                self.SetSelection(-1)
            self.Enable(not config.readonly)

    def SetItems(self, items):
        ChoiceWithoutScroll.Clear(self)
        self.values.clear()
        for item in items:
            if isinstance(item, tuple):
                self.Append(item[0], item[1])
            else:
                self.Append(item, item)
        try:
            self.UpdateContents()
        except:
            pass


class AutoCheckBox(wx.CheckBox, AutoMixin):
    def __init__(self, parent, instance, member, label="", value=1, fixed_instance=False, observers=[], *args,
                 **kwargs):
        wx.CheckBox.__init__(self, parent, -1, label, *args, **kwargs)
        self.value = value
        AutoMixin.__init__(self, parent, instance, member, fixed_instance, observers)
        parent.Bind(wx.EVT_CHECKBOX, self.EvtCheckbox, self)

    def __del__(self):
        AutoMixin.__del__(self)

    def EvtCheckbox(self, event):
        previous_value = eval('self.instance.%s' % self.member)
        if event.Checked():
            self.AutoChange(previous_value | self.value)
        else:
            self.AutoChange(previous_value & ~self.value)

    def SetValue(self, value):
        wx.CheckBox.SetValue(self, value & self.value)


class AutoBinaryChoiceCtrl(ChoiceWithoutScroll, AutoMixin):
    def __init__(self, parent, instance, member, items=None, fixed_instance=False, observers=[], *args, **kwargs):
        ChoiceWithoutScroll.__init__(self, parent, -1, *args, **kwargs)
        self.values = {}
        if items:
            self.SetItems(items)
        AutoMixin.__init__(self, parent, instance, member, fixed_instance, observers)
        parent.Bind(wx.EVT_CHOICE, self.onChoice, self)

    def __del__(self):
        AutoMixin.__del__(self)

    def Append(self, item, clientData):
        index = ChoiceWithoutScroll.Append(self, item, clientData)
        self.values[clientData] = index

    def onChoice(self, event):
        previous_value = eval('self.instance.%s' % self.member)
        value = event.GetClientData()
        if value:
            self.AutoChange(previous_value | self.value)
        else:
            self.AutoChange(previous_value & ~self.value)
        event.Skip()

    def SetValue(self, value):
        self.UpdateContents()

    def UpdateContents(self):
        if not self.instance:
            self.Disable()
        else:
            value = eval('self.instance.%s & self.value' % self.member)
            if value in self.values:
                self.SetSelection(self.values[value])
            else:
                self.SetSelection(-1)
            self.Enable(not config.readonly)

    def SetItems(self, items):
        ChoiceWithoutScroll.Clear(self)
        self.values.clear()
        for item, clientData in items:
            self.Append(item, clientData)
            if clientData:
                self.value = clientData


class AutoRadioBox(wx.RadioBox, AutoMixin):
    def __init__(self, parent, instance, member, label, choices, fixed_instance=False, observers=[], *args, **kwargs):
        wx.RadioBox.__init__(self, parent, -1, label=label, choices=choices, *args, **kwargs)
        AutoMixin.__init__(self, parent, instance, member, fixed_instance, observers)
        parent.Bind(wx.EVT_RADIOBOX, self.EvtRadiobox, self)

    def __del__(self):
        AutoMixin.__del__(self)

    def EvtRadiobox(self, event):
        self.AutoChange(event.GetInt())

    def SetValue(self, value):
        self.SetSelection(value)


class DatePickerCtrl(wx.DatePickerCtrl):
    _GetValue = wx.DatePickerCtrl.GetValue
    _SetValue = wx.DatePickerCtrl.SetValue

    def GetValue(self):
        if self._GetValue().IsValid():
            return datetime.date(self._GetValue().GetYear(), self._GetValue().GetMonth() + 1, self._GetValue().GetDay())
        else:
            return None

    def SetValue(self, dt):
        if dt is None:
            self._SetValue(wx.DateTime())
        else:
            self._SetValue(wx.DateTimeFromDMY(dt.day, dt.month - 1, dt.year))


class TextDialog(wx.Dialog):
    def __init__(self, parent, titre, text):
        wx.Dialog.__init__(self, parent, -1, titre, wx.DefaultPosition, wx.DefaultSize)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.textctrl = wx.TextCtrl(self, -1, text, style=wx.TAB_TRAVERSAL | wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnter, self.textctrl)
        self.sizer.Add(self.textctrl, 0, wx.EXPAND | wx.ALL, 5)
        self.btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        self.btnsizer.AddButton(btn)
        btn = wx.Button(self, wx.ID_CANCEL)
        self.btnsizer.AddButton(btn)
        self.btnsizer.Realize()
        self.sizer.Add(self.btnsizer, 0, wx.ALL, 5)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)

    def GetText(self):
        return self.textctrl.GetValue()

    def OnEnter(self, _):
        self.EndModal(wx.ID_OK)


class PeriodeDialog(wx.Dialog):
    def __init__(self, parent, periode):
        wx.Dialog.__init__(self, parent, -1, "Modifier une période", wx.DefaultPosition, wx.DefaultSize)
        self.periode = periode
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.fields_sizer = wx.FlexGridSizer(0, 2, 5, 10)
        self.fields_sizer.AddGrowableCol(1, 1)
        self.debut_ctrl = DateCtrl(self)
        self.debut_ctrl.SetValue(periode.debut)
        self.fields_sizer.AddMany(
            [(wx.StaticText(self, -1, "Début :"), 0, wx.ALIGN_CENTRE_VERTICAL | wx.ALL - wx.BOTTOM, 5),
             (self.debut_ctrl, 0, wx.EXPAND | wx.ALIGN_CENTRE_VERTICAL | wx.ALL - wx.BOTTOM, 5)])
        self.fin_ctrl = DateCtrl(self)
        self.fin_ctrl.SetValue(periode.fin)
        self.fields_sizer.AddMany([(wx.StaticText(self, -1, "Fin :"), 0, wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 5),
                                   (self.fin_ctrl, 0, wx.EXPAND | wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 5)])
        self.sizer.Add(self.fields_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        self.btnsizer.AddButton(btn)
        btn = wx.Button(self, wx.ID_CANCEL)
        self.btnsizer.AddButton(btn)
        self.btnsizer.Realize()
        self.sizer.Add(self.btnsizer, 0, wx.ALL, 5)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)


if sys.platform == "darwin":
    SIMPLE_BUTTONS_SIZE = (30, 30)
else:
    SIMPLE_BUTTONS_SIZE = (-1, -1)


class PeriodeChoice(wx.BoxSizer):
    def __init__(self, parent, constructor, default=None, onModify=None):
        wx.BoxSizer.__init__(self, wx.HORIZONTAL)
        self.parent = parent
        self.constructor = constructor
        self.onModify = onModify  # TODO rather raise events
        self.defaultPeriode = default
        self.instance = None
        self.readonly = False

        self.periodechoice = wx.Choice(parent, size=(220, -1))
        parent.Bind(wx.EVT_CHOICE, self.EvtPeriodeChoice, self.periodechoice)
        delbmp = wx.Bitmap(GetBitmapFile("remove.png"), wx.BITMAP_TYPE_PNG)
        plusbmp = wx.Bitmap(GetBitmapFile("plus.png"), wx.BITMAP_TYPE_PNG)
        settingsbmp = wx.Bitmap(GetBitmapFile("settings.png"), wx.BITMAP_TYPE_PNG)
        self.periodeaddbutton = wx.BitmapButton(parent, -1, plusbmp, size=SIMPLE_BUTTONS_SIZE)
        self.periodeaddbutton.SetToolTipString("Ajouter une période")
        self.periodedelbutton = wx.BitmapButton(parent, -1, delbmp, size=SIMPLE_BUTTONS_SIZE)
        self.periodedelbutton.SetToolTipString("Supprimer la période")
        self.periodesettingsbutton = wx.BitmapButton(parent, -1, settingsbmp, size=SIMPLE_BUTTONS_SIZE)
        self.periodesettingsbutton.SetToolTipString("Modifier la période")

        self.Add(self.periodechoice, 1, wx.EXPAND | wx.LEFT, 5)
        self.Add(self.periodeaddbutton, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
        self.Add(self.periodedelbutton, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.Add(self.periodesettingsbutton, 0, wx.ALIGN_CENTER_VERTICAL)
        parent.Bind(wx.EVT_BUTTON, self.EvtPeriodeAddButton, self.periodeaddbutton)
        parent.Bind(wx.EVT_BUTTON, self.EvtPeriodeDelButton, self.periodedelbutton)
        parent.Bind(wx.EVT_BUTTON, self.EvtPeriodeSettingsButton, self.periodesettingsbutton)
        parent.periodechoice = self

    def SetInstance(self, instance, periode=None):
        self.instance = instance
        self.periode = periode
        if instance is not None:
            self.periodechoice.Clear()
            for item in instance:
                self.periodechoice.Append(GetPeriodeString(item))
            self.Enable()
            if periode is not None:
                self.periodechoice.SetSelection(periode)
        else:
            self.Disable()

    def EvtPeriodeChoice(self, evt):
        ctrl = evt.GetEventObject()
        self.periode = ctrl.GetSelection()
        self.parent.SetPeriode(self.periode)
        self.Enable()

    def EvtPeriodeAddButton(self, _):
        self.periode = len(self.instance)
        new_periode = self.constructor()
        if len(self.instance) > 0:
            last_periode = self.instance[-1]
            new_periode.debut = last_periode.fin + datetime.timedelta(1)
            if last_periode.debut.day == new_periode.debut.day and last_periode.debut.month == new_periode.debut.month:
                new_periode.fin = datetime.date(
                    last_periode.fin.year + new_periode.debut.year - last_periode.debut.year, last_periode.fin.month,
                    last_periode.fin.day)
        elif self.defaultPeriode:
            new_periode.debut = datetime.date(self.defaultPeriode, 1, 1)
            new_periode.fin = datetime.date(self.defaultPeriode, 12, 31)

        self.instance.append(new_periode)
        self.periodechoice.Append(GetPeriodeString(new_periode))
        self.periodechoice.SetSelection(self.periode)
        self.parent.SetPeriode(self.periode)
        history.Append(Delete(self.instance, -1))
        self.Enable()

    def EvtPeriodeDelButton(self, evt):
        dlg = wx.MessageDialog(self.parent,
                               "Cette période va être supprimée, confirmer ?",
                               "Confirmation",
                               wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
        if dlg.ShowModal() == wx.ID_YES:
            index = self.periodechoice.GetSelection()
            periode = self.instance[index]
            history.Append(Insert(self.instance, index, periode))
            del self.instance[index]
            self.periodechoice.Delete(index)
            self.periode = len(self.instance) - 1
            self.periodechoice.SetSelection(self.periode)
            self.parent.SetPeriode(self.periode)
            self.Enable()

    def EvtPeriodeSettingsButton(self, _):
        periode = self.instance[self.periode]
        dlg = PeriodeDialog(self.parent, periode)
        response = dlg.ShowModal()
        dlg.Destroy()
        if response == wx.ID_OK:
            history.Append([Change(periode, "debut", periode.debut), Change(periode, "fin", periode.fin)])
            periode.debut, periode.fin = dlg.debut_ctrl.GetValue(), dlg.fin_ctrl.GetValue()
            if self.onModify:
                self.onModify()
            self.periodechoice.SetString(self.periode, GetPeriodeString(periode))
            self.periodechoice.SetSelection(self.periode)
            self.Enable()

    def set_readonly(self, readonly):
        self.readonly = readonly

    def Enable(self, enable=True):
        self.periodechoice.Enable(enable and len(self.instance) > 0)
        self.periodesettingsbutton.Enable(enable and len(self.instance) > 0 and not config.readonly and not self.readonly)
        self.periodeaddbutton.Enable(enable and self.instance is not None and (len(self.instance) == 0 or self.instance[-1].fin is not None) and not config.readonly and not self.readonly)
        self.periodedelbutton.Enable(enable and self.instance is not None and len(self.instance) > 0 and not config.readonly and not self.readonly)

    def Disable(self):
        self.Enable(False)


class ControlsGroup(object):
    def __init__(self, parent):
        self.ctrls = []
        self.parent = parent
        self.window = None

    def UpdateContents(self):
        for ctrl in self.ctrls:
            ctrl.UpdateContents()

    def GetWindow(self):
        return self.parent


class AutoTab(wx.lib.scrolledpanel.ScrolledPanel, ControlsGroup):
    def __init__(self, parent):
        ControlsGroup.__init__(self, parent)
        wx.lib.scrolledpanel.ScrolledPanel.__init__(self, parent)
        self.window = self
        self.SetAutoLayout(1)
        self.SetupScrolling()

    def GetWindow(self):
        return self


class PeriodeMixin(object):
    def __init__(self, member):
        self.instance = None
        self.member = member
        self.periode = None
        self.current_periode = None
        self.ctrls = []
        self.periodechoice = None

    def UpdateContents(self):
        for ctrl in self.ctrls:
            ctrl.UpdateContents()

    def SetInstance(self, instance, periode=None):
        self.instance = instance
        self.periode = periode

        if instance:
            periodes = eval("instance.%s" % self.member)
            if len(periodes) > 0:
                if periode is None:
                    self.periode = len(periodes) - 1
                    if self.periodechoice:
                        self.periodechoice.SetInstance(periodes, self.periode)
                self.current_periode = periodes[self.periode]
            else:
                self.current_periode = None
                if self.periodechoice:
                    self.periodechoice.SetInstance(periodes)
            for ctrl in self.ctrls:
                ctrl.SetInstance(self.current_periode)
        else:
            self.current_periode = None
            if self.periodechoice:
                self.periodechoice.SetInstance(None)
            for ctrl in self.ctrls:
                ctrl.SetInstance(None)

    def SetPeriode(self, periode):
        self.SetInstance(self.instance, periode)


class PeriodePanel(wx.Panel, PeriodeMixin):
    def __init__(self, parent, member, *args, **kwargs):
        wx.Panel.__init__(self, parent, -1, *args, **kwargs)
        PeriodeMixin.__init__(self, member)
        parent.ctrls.append(self)

    def GetWindow(self):
        return self


class HashComboBox(wx.combo.OwnerDrawnComboBox):
    def __init__(self, parent, id=-1):
        wx.combo.OwnerDrawnComboBox.__init__(self, parent, id, style=wx.CB_READONLY, size=(150, -1))

    def OnDrawItem(self, dc, rect, item, flags):
        if item == wx.NOT_FOUND:
            return

        rr = wx.Rect(*rect)  # make a copy
        rr.Deflate(3, 5)

        data = self.GetClientData(item)
        if isinstance(data, tuple):
            r, g, b, t, s = data
        else:
            r, g, b, t, s = data.couleur

        dc = wx.GCDC(dc)
        dc.SetPen(wx.Pen(wx.Colour(r, g, b)))
        dc.SetBrush(wx.Brush(wx.Colour(r, g, b, t), s))
        dc.DrawRoundedRectangleRect(wx.Rect(rr.x, rr.y - 3, rr.width, rr.height + 6), 3)

        if flags & wx.combo.ODCB_PAINTING_CONTROL:
            rr.y -= 2
        dc.DrawText(self.GetString(item), rr.x + 10, rr.y - 1)

    def OnMeasureItem(self, item):
        return 24

    def OnDrawBackground(self, dc, rect, item, flags):
        if flags & wx.combo.ODCB_PAINTING_SELECTED:
            bgCol = wx.Colour(160, 160, 160)
            dc.SetBrush(wx.Brush(bgCol))
            dc.SetPen(wx.Pen(bgCol))
            dc.DrawRectangleRect(rect);


class ActivityComboBox(HashComboBox):
    def __init__(self, parent, id=-1):
        HashComboBox.__init__(self, parent, id)
        self.Bind(wx.EVT_COMBOBOX, self.OnChangeActivity, self)
        self.activity = None

    def SetSelection(self, item):
        wx.combo.OwnerDrawnComboBox.SetSelection(self, item)
        self.activity = self.GetClientData(item)

    def OnChangeActivity(self, evt):
        self.activity = self.GetClientData(self.GetSelection())
        evt.Skip()

    def add_activity(self, activity):
        self.Append(activity.label, activity)

    def Update(self):
        self.Clear()
        selected = 0
        self.add_activity(database.creche.states[0])
        if database.creche.has_activites_avec_horaires():
            self.Show(True)
            for i, activity in enumerate(database.creche.activites):
                if activity.has_horaires():
                    self.add_activity(activity)
                    if self.activity == activity:
                        selected = i + 1
        else:
            self.Show(False)
        self.SetSelection(selected)


def GetPictoBitmap(index, size=64):
    if isinstance(index, int):
        index = chr(ord('a') + index)
    bitmap = wx.Bitmap(GetBitmapFile("pictos/%c.png" % index), wx.BITMAP_TYPE_PNG)
    image = wx.ImageFromBitmap(bitmap)
    image = image.Scale(size, size, wx.IMAGE_QUALITY_HIGH)
    return wx.BitmapFromImage(image)


class CombinaisonDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "Nouvelle combinaison", wx.DefaultPosition, wx.DefaultSize)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        gridSizer = wx.FlexGridSizer(5, 4, 5, 5)
        self.combinaison = []
        for i in range(20):
            picto = wx.BitmapButton(self, -1, GetPictoBitmap(i), style=wx.BU_EXACTFIT)
            picto.picto = chr(ord('a') + i)
            self.Bind(wx.EVT_BUTTON, self.OnPressPicto, picto)
            gridSizer.Add(picto)
        self.sizer.Add(gridSizer, 0, wx.EXPAND | wx.ALL, 5)

        self.combinaisonPanel = wx.Panel(self, style=wx.SUNKEN_BORDER)
        self.combinaisonPanel.SetMinSize((-1, 36))
        self.combinaisonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.combinaisonPanel.SetSizer(self.combinaisonSizer)
        self.sizer.Add(self.combinaisonPanel, 0, wx.EXPAND)

        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        btnsizer.AddButton(btn)
        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        self.sizer.Add(btnsizer, 0, wx.ALL, 5)
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)

    def OnPressPicto(self, event):
        sender = event.GetEventObject()
        picto = sender.picto
        self.combinaison.append(picto)
        bmp = GetPictoBitmap(picto, size=32)
        button = wx.StaticBitmap(self.combinaisonPanel, -1, bmp)
        self.combinaisonSizer.Add(button, 0, wx.LEFT, 5)
        self.combinaisonSizer.Layout()

    def GetCombinaison(self):
        return "".join(self.combinaison)


class TabletteSizer(wx.StaticBoxSizer):
    def __init__(self, parent, object):
        wx.StaticBoxSizer.__init__(self, wx.StaticBox(parent, -1, u'Tablette'), wx.VERTICAL)
        self.parent = parent
        self.object = object
        internalSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.combinaisonSizer = wx.BoxSizer(wx.HORIZONTAL)
        internalSizer.Add(self.combinaisonSizer)
        settingsbmp = wx.Bitmap(GetBitmapFile("settings.png"), wx.BITMAP_TYPE_PNG)
        self.button = wx.BitmapButton(parent, -1, settingsbmp)
        self.button.Enable(not config.readonly)
        parent.Bind(wx.EVT_BUTTON, self.OnModifyCombinaison, self.button)
        internalSizer.Add(self.button, 0, wx.LEFT, 10)
        self.Add(internalSizer, 0, wx.TOP | wx.BOTTOM, 10)

    def OnModifyCombinaison(self, _):
        dlg = CombinaisonDialog(self.parent)
        res = dlg.ShowModal()
        if res == wx.ID_OK:
            self.object.combinaison = dlg.GetCombinaison()
            self.UpdateCombinaison()
            history.Append(None)
        dlg.Destroy()

    def UpdateCombinaison(self):
        self.combinaisonSizer.DeleteWindows()
        if self.object:
            self.button.Enable(not config.readonly)
            if self.object.combinaison:
                for letter in self.object.combinaison:
                    bitmap = GetPictoBitmap(letter, size=32)
                    picto = wx.StaticBitmap(self.parent, -1, bitmap)
                    self.combinaisonSizer.Add(picto, 0, wx.LEFT, 10)
        else:
            self.button.Disable()
        self.combinaisonSizer.Layout()
        self.parent.sizer.Layout()

    def SetObject(self, object):
        self.object = object


if sys.platform == "darwin":
    MACOS_MARGIN = 1
else:
    MACOS_MARGIN = 0
