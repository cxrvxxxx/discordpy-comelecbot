import sqlite3 as sql

from . import db_path

class Candidate:
    def __init__(self, id, name, department, valid, void):
        self.__id = id
        self.__name = name
        self.__department = department
        self.__valid = valid
        self.__void = void

    def get_name(self):
        return self.__name
    
    def get_department(self):
        return self.__department
    
    def get_valid(self):
        return self.__valid
    
    def get_void(self):
        return self.__void

    @classmethod
    def process_names(cls, _names, department, valid):
        names = _names.split(";")

        conn = sql.connect(db_path)
        c = conn.cursor()

        for name in names:
            if not name:
                continue

            candidate = cls.get_by_name(name)

            if not candidate:
                c.execute("""
                    INSERT INTO candidate (name, department, valid, void)
                    VALUES (:name, :department, :valid, :void)""",
                    {
                        "name": name,
                        "department": department,
                        "valid": 1 if valid else 0,
                        "void": 1 if not valid else 0
                    }
                )

                conn.commit()
                continue
            
            c.execute("""
            UPDATE candidate
            SET
                valid=:valid,
                void=:void
            WHERE
                name=:name""",
                {
                    "name": name,
                    "valid": candidate.get_valid() + 1 if valid else candidate.get_valid(),
                    "void": candidate.get_void() + 1 if not valid else candidate.get_void()
                }
            )

            conn.commit()
        
        conn.close()

    @classmethod
    def get_by_name(cls, name):
        conn = sql.connect(db_path)
        c = conn.cursor()

        c.execute("""
            SELECT * FROM candidate
            WHERE
                name=?""",
            (name,)
        )

        fields = c.fetchone()
        conn.close()

        if fields:
            return cls(*fields)
