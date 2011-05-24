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

import __builtin__

class Change:
    def __init__(self, instance, member, value):
        self.instance, self.member, self.value = instance, member, value

    def Undo(self):
        exec('self.instance.%s = self.value' % self.member)

class Delete:
    def __init__(self, instance, index):
        self.instance, self.index = instance, index

    def Undo(self):
        self.instance[self.index].delete()
        del self.instance[self.index]

class Insert:
    def __init__(self, instance, index, value):
        self.instance, self.index, self.value = instance, index, value

    def Undo(self):
        if isinstance(self.instance, list):
            self.instance.insert(self.index, self.value)
        else:
            self.instance[self.index] = self.value
        self.value.create()

class Call:
    def __init__(self, function, args=None):
        self.function = function
        self.args = args

    def Undo(self):
        if self.args is None:
            self.function()
        else:
            self.function(self.args)
       
class History(list):
    def __init__(self):
        list.__init__(self)

    def Undo(self, count=1):
        result = 0
        for i in range(count):
            if len(self) > 0:
                for action in self.pop(-1):
                    action.Undo()
                    result += 1
        return result

    def Append(self, actions):
        if not isinstance(actions, list):
            actions = [actions]
        self.append(actions)

    def Last(self):
        if len(self) > 0:
            return self[-1]
        else:
            return None
        
    def Clear(self):
        del self[:]

__builtin__.history = History()
