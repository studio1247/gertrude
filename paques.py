import datetime

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
