from db import Database

def main():
    db = Database()
    db.push(all=True)

if __name__ == "__main__":
    main()