import sqlite3 as sql

from . import db_path

class Checker:
    def __init__(self, discord_id: int, firstname: str, lastname: str, email: str):
        self.__id = discord_id
        self.__discord_id = discord_id
        self.__firstname = firstname
        self.__lastname = lastname
        self.__email = email

    def get_id(self):
        return self.__id
    
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
            SELECT * FROM checkers
            WHERE
                id=?""",
            (discord_id,)
        )

        fields = c.fetchone()
        conn.close()

        checker = cls(*fields) if fields else None

        return checker

    @classmethod
    def get_all(cls):
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("SELECT * FROM checkers")
        fields = c.fetchall()

        conn.close()

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
            INSERT INTO checkers (id, firstname, lastname, email)
            VALUES (:id, :firstname, :lastname, :email)""",
            {
                "id": discord_id,
                "firstname": firstname,
                "lastname": lastname,
                "email": email
            }
        )

        conn.commit()
        conn.close()

        return cls.get_by_id(discord_id)

    def update(self):
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("""
            UPDATE checkers
            SET
                firstname=:firstname,
                lastname=:lastname,
                email=:email
            WHERE
                id=:id""",
            {
                "firstname": self.get_firstname(),
                "lastname": self.get_lastname(),
                "email": self.get_email(),
                "id": self.get_id()
            }
        )

        conn.commit()
        conn.close()

        return self.get_by_id(self.get_id())

    def delete(self):
        if not self.get_by_id(self.get_id()):
            return
        
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("""
            DELETE FROM checkers
            WHERE
                id=?""",
            (self.get_id(),)
        )

        conn.commit()
        conn.close()
