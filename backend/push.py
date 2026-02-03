from db import Database

def main():
    db = Database()
    db.push()
    db.setup_checkpointer()
    db.close()

if __name__ == "__main__":
    main()