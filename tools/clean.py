import sys
from database import Database


def clean(filename):
    database = Database(filename)
    database.load()

    for site in database.creche.sites:
        print(site.idx, site.nom)

    # database.delete_all_inscriptions()
    database.delete_users()
    database.delete_site(2)


if __name__ == '__main__':
    clean(sys.argv[1])
