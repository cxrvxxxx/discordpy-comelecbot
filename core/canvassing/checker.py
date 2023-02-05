import sqlite3 as sql

db_path = r'./data/AppData.db'
conn = sql.connect(db_path)
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS checker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discord_id INTEGER,
    firstname VARCHAR(255),
    lastname VARCHAR(255),
    email VARCHAR(255)
    )"""
)
conn.commit()
conn.close()

class Checker:
    def __init__(self, id: int, discord_id: int, firstname: str, lastname: str, email: str):
        self.id = id
        self.discord_id = discord_id
        self.firstname = firstname
        self.lastname = lastname
        self.email = email

    @staticmethod
    def check_exists(discord_id: int):
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("SELECT * FROM checker WHERE discord_id=?", (discord_id,))
        data = c.fetchone()

        conn.close()

        if data: return True
        return False
    
    @staticmethod
    def get_checkers():
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("SELECT * FROM checker ORDER BY id ASC")
        data = c.fetchall()

        conn.close()

        return data
    
    @classmethod
    def create(cls, discord_id: int, firstname: str, lastname:str, email: str):
        if cls.check_exists(discord_id): return

        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("""
            INSERT INTO checker (discord_id, firstname, lastname, email)
            VALUES (:discord_id, :firstname, :lastname, :email)""",
            {
                "discord_id": discord_id,
                "firstname" : firstname,
                "lastname": lastname,
                "email": email
            }
        )
        conn.commit()
        c.execute("""
            SELECT * FROM checker
            WHERE discord_id=?""",
            (
                discord_id,
            )
        )

        checker = cls(*c.fetchone())
        conn.close()

        return checker

    @staticmethod
    def is_checker(discord_id: int):
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("SELECT * FROM checker WHERE discord_id=?", (discord_id,))
        data = c.fetchone()

        conn.close()

        if not data: return False
        return True

    @classmethod
    def get_checker_by_id(cls, discord_id):
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("SELECT * FROM checker WHERE discord_id=?", (discord_id,))
        fields = c.fetchone()

        if fields: return cls(*fields)

    @classmethod
    def update(cls, discord_id, field, value):
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute(f"""
            UPDATE checker
            SET {field}=:value
            WHERE discord_id=:discord_id""",
            {
                "discord_id": discord_id,
                "value": value
            }
        )

        conn.commit()
        conn.close()
