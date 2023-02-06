import sqlite3 as sql

from . import db_path

class Vote:
    def __init__(self, id: int, vote_id: int, rep_col: int, checekr_id: int, is_valid: bool, reason: int):
        self.__id = id
        self.__vote_id = vote_id
        self.__rep_col = rep_col
        self.__checker_id = checekr_id
        self.__is_valid = is_valid
        self.__reason = reason

    def get_id(self):
        return self.__id

    def get_vote_id(self):
        return self.__vote_id
    
    def get_rep_col(self):
        return self.__rep_col

    def get_checker_id(self):
        return self.__checker_id

    def get_is_valid(self):
        return self.__is_valid

    def get_reason(self):
        return self.__reason

    @classmethod
    def get_by_id(cls, id):
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("""
            SELECT * FROM vote
            WHERE
                id=?""",
            (id,)
        )

        fields = c.fetchone()
        conn.close()

        if fields:
            return cls(*fields)

    @classmethod
    def get_by_vote_id(cls, vote_id):
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("""
            SELECT * FROM vote
            WHERE
                vote_id=?""",
            (vote_id,)
        )

        fields = c.fetchone()
        conn.close()

        if fields:
            return cls(*fields)
        
    @classmethod
    def get_all(cls):
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("SELECT * FROM vote")
        fields = c.fetchall()

        conn.close()

        votes = []
        for row in fields:
            votes.append(cls(*row))

        return votes
    
    @classmethod
    def get_validated(cls):
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("SELECT * FROM vote WHERE is_valid=1")
        fields = c.fetchall()

        conn.close()

        votes = []
        for row in fields:
            votes.append(cls(*row))

        return votes
    
    @classmethod
    def get_voided(cls):
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("SELECT * FROM vote WHERE is_valid=0")
        fields = c.fetchall()

        conn.close()

        votes = []
        for row in fields:
            votes.append(cls(*row))

        return votes
    
    @classmethod
    def create(cls, vote_id, rep_col, checker_id, is_valid, reason):
        if cls.get_by_id(vote_id):
            return
        
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("""
            INSERT INTO vote (vote_id, rep_col, checker_id, is_valid, reason)
            VALUES (:vote_id, :rep_col, :checker_id, :is_valid, :reason)""",
            {
                "vote_id": vote_id,
                "rep_col": rep_col,
                "checker_id": checker_id,
                "is_valid": is_valid,
                "reason": reason
            }
        )

        conn.commit()
        conn.close()

        return cls.get_by_id(vote_id)
    
    def update(self):
        if not self.get_by_id(self.__vote_id):
            return

        conn = sql.connect(db_path)
        c = conn.cursor()
        
        c.execute(""""
            UPDATE vote
            SET
                checker_id=:checker_id,
                is_valid=:is_valid,
                reason=:reason
            WHERE
                vote_id=:vote_id""",
            {
                "rep_col":  self.__rep_col,
                "checker_id": self.__checker_id,
                "is_valid": self.__is_valid,
                "reason": self.__reason,
                "vote_id": self.__vote_id
            }
        )

        conn.commit()
        conn.close()

        return self.get_by_id(self.__vote_id)

    def delete(self):
        if not self.get_by_id(self.__vote_id):
            return

        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("""
            DELETE FROM vote
            WHERE id=?""",
            (self.__id,)
        )

        conn.commit()
        conn.close()
