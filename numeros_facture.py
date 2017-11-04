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

import os
import collections
from helpers import date2str, str2date


class NumerotationFactureBase:
    def get(self, id, date):
        raise NotImplementedError


class NumerotationMerEtTerre(NumerotationFactureBase):
    def __init__(self, filename="numeros_facture.txt"):
        self.numeros_facture = collections.OrderedDict()
        self.filename = filename
        self.read()

    def read(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r") as f:
                lines = f.readlines()
                for line in lines:
                    id, date, number = line.split()
                    date = str2date(date)
                    number = int(number)
                    self.numeros_facture[(id, date)] = number

    def register(self, id, date, number):
        self.numeros_facture[(id, date)] = number
        with open(self.filename, "a") as f:
            f.write("%s %s %d\n" % (id, date2str(date), number))

    def get(self, id, date):
        result = self.numeros_facture.get((id, date), None)
        if result is None:
            if self.numeros_facture:
                key, result = list(self.numeros_facture.items())[-1]
                result += 1
            else:
                result = 1619
            self.register(id, date, result)
        return result
