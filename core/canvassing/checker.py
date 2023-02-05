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
        self.__id = id
        self.__discord_id = discord_id
        self.__firstname = firstname
        self.__lastname = lastname
        self.__email = email

    def get_id(self):
        return self.__id
    
    def get_discord_id(self):
        return self.__discord_id
    
    def get_firstname(self):
        return self.__firstname
    
    def get_lastname(self):
        return self.__lastname
    
    def get_email(self):
        return self.__email
    
    def set_firstname(self, firstname):
        self.__firstname = firstname
        self.update()

    def set_lastname(self, lastname):
        self.__lastname = lastname
        self.update()

    def set_email(self, email):
        self.__email = email
        self.update()

    @classmethod
    def get_by_id(cls, discord_id):
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("""
            SELECT * FROM checker
            WHERE discord_id=?""",
            (discord_id,)
        )

        fields = c.fetchone()

        checker = cls(*fields) if fields else None

        conn.close()

        return checker

    @classmethod
    def get_all(cls):
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("SELECT * FROM checker")
        fields = c.fetchall()

        checkers = []
        for row in fields:
            checkers.append(cls(*row))

        return checkers
    
    @classmethod
    def create(cls, discord_id, firstname, lastname, email):
        if cls.get_by_id(discord_id):
            return
        
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("""
            INSERT INTO checker (discord_id, firstname, lastname, email)
            VALUES (:discord_id, :firstname, :lastname, :email)""",
            {
                "discord_id": discord_id,
                "firstname": firstname,
                "lastname": lastname,
                "email": email
            }
        )

        conn.commit()
        conn.close()

        return cls.get_by_id(discord_id)

    def update(self):
        if not self.get_by_id(self.__discord_id):
            return
        
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("""
            UPDATE checker
            SET
                firstname=:firstname,
                lastname=:lastname,
                email=:email
            WHERE id=:id""",
            {
                "firstname": self.__firstname,
                "lastname": self.__lastname,
                "email": self.__email,
                "id": self.__id
            }
        )

        conn.commit()
        conn.close()

        return self.get_by_id(self.__discord_id)

    def delete(self):
        if not self.get_by_id(self.__discord_id):
            return
        
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("""
            DELETE FROM checker
            WHERE
                id=?""",
            (self.__id,)
        )

        conn.commit()
        conn.close()
