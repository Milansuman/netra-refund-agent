from db import Database

def main():
    db = Database()
    db.push(all=True)
    db.close()

if __name__ == "__main__":
    main()