from db import Database

def main():
    db = Database()
    db.push()
    db.close()

if __name__ == "__main__":
    main()