from database import Database


if __name__ == '__main__':
    database = Database("../databases/...")
    database.load()
    database.delete_all_inscriptions()
