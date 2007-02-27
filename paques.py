import datetime

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

def getPaquesDate(year):
    if year < 1583:
        m, n = 16, 6
    else:
        m, n = 24, 5
    a, b, c = year % 19, year % 4, year % 7
    d = (19 * a + m) % 30
    e = (2 * b + 4 * c + 6 * d + n) % 7
    if d + e < 10:
        return datetime.date(year, 3, d + e + 22)
    else:
        return datetime.date(year, 4, d + e - 9)

if __name__ == '__main__':
    for year in range(2000, 2050):
        print getPaquesDate(year)
