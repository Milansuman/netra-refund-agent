from db.connections import db

def main():
    db.push()
    db.setup_checkpointer()
    db.close()

if __name__ == "__main__":
    main()