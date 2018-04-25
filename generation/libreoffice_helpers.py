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


def get_libreoffice_context():
    import win32com.client
    objServiceManager = win32com.client.Dispatch("com.sun.star.ServiceManager")
    objServiceManager._FlagAsMethod("CreateInstance")
    objServiceManager._FlagAsMethod("Bridge_GetStruct")
    core_reflection = objServiceManager.CreateInstance("com.sun.star.reflection.CoreReflection")
    return objServiceManager.createInstance("com.sun.star.frame.Desktop"), objServiceManager, core_reflection


def make_property_value(manager, Name, Value):
    struct = manager.Bridge_GetStruct("com.sun.star.beans.PropertyValue")
    struct.Name = Name
    struct.Value = Value
    return struct


def make_property_values(manager, values):
    return [make_property_value(manager, value[0], value[1]) for value in values]
