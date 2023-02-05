import sqlite3 as sql

db_path = r'./data/AppData.db'

conn = sql.connect(db_path)
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS vote (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vote_id INTEGER,
    checker_id INTEGER,
    is_valid INTEGER,
    reason INTEGER,
    FOREIGN KEY (checker_id) REFERENCES checker (id)
    )"""
)
conn.commit()
conn.close()

class Vote:
    def __init__(self, id: int, vote_id: int, checekr_id: int, is_valid: bool, reason: int):
        self.__id = id
        self.__vote_id = vote_id
        self.__checker_id = checekr_id
        self.__is_valid = is_valid
        self.__reason = reason

    @classmethod
    def get_by_id(cls, vote_id):
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
    def create(cls, vote_id, checker_id, is_valid, reason):
        if cls.get_by_id(vote_id):
            return
        
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("""
            INSERT INTO vote (vote_id, checker_id, is_valid, reason)
            VALUES (:vote_id, :checker_id, :is_valid, :reason)""",
            {
                "vote_id": vote_id,
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
        
        c.execute(""""
            UPDATE vote
            SET
                checker_id=:checker_id,
                is_valid=:is_valid,
                reason=:reason
            WHERE
                vote_id=:vote_id""",
            {
                "checker_id": self.__checker_id,
                "is_valid": self.__is_valid,
                "reason": self.__reason,
                "vote_id": self.__vote_id
            }
        )

        conn.commit()
        conn.close()

        return self.get_by_id(self.__vote_id)

    @staticmethod
    def check_exists(vote_id):
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("SELECT * FROM vote WHERE vote_id=?", (vote_id,))
        fields = c.fetchone()

        conn.close()

        if not fields: return False
        return True

    def save(self):
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("""
            INSERT INTO vote (vote_id, checker_id, is_valid, reason)
            VALUES (:vote_id, :checker_id, :is_valid, :reason)""",
            {
                "vote_id": self.vote_id,
                "checker_id": self.checker_id,
                "is_valid": self.is_valid,
                "reason": self.reason
            }
        )

        conn.commit()
        conn.close()

    @staticmethod
    def fetch_valid_votes():
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("""
            SELECT vote.vote_id, checker.lastname || ', ' || checker.firstname AS name
            FROM vote
            INNER JOIN checker
            ON vote.checker_id = checker.id
            WHERE is_valid=1
        """)

        fields = c.fetchall()

        return fields
    
    @staticmethod
    def fetch_invalid_votes():
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("""
            SELECT vote.vote_id, checker.lastname || ', ' || checker.firstname AS name, reason
            FROM vote
            INNER JOIN checker
            ON vote.checker_id = checker.id
            WHERE is_valid=0
        """)

        fields = c.fetchall()

        return fields

    @staticmethod
    def fetch_vote(vote_id):
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("""
            SELECT checker.lastname || ', ' || checker.firstname AS name, is_valid, reason
            FROM vote
            INNER JOIN checker
            ON vote.checker_id = checker.id
            WHERE vote_id=?""",
            (vote_id,)
        )

        fields = c.fetchone()
        conn.close()

        if fields: return fields
