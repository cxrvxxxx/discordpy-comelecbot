from typing import Union
from abc import ABCMeta

from ..classes.candidate import Candidate
from ..classes.position import Position
from ..classes.party import Party

class CandidateModel(ABCMeta):
    @staticmethod
    def _check_exists(connection, candidate_id: int) -> bool:
        with connection as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM tblCandidate WHERE id=%(id)s", { "id": candidate_id, })
            if c.fetchone():
                return True
            
        return False
    
    @staticmethod
    def add_student(connection, candidate: Candidate) -> bool:
        if CandidateModel._check_exists(connection, candidate.candidate_id):
            return False
        
        with connection as conn:
            c = conn.cursor()
            c.execute("""
            INSERT INTO tblCandidate (lastname, firstname, middleInitial, position, affiliation)
            VALUES (%(lastname)s, %(firstname)s, %(middleInitial)s, %(position)s, %(affiliation)s)
            """,
            {
                "lastname": candidate.lastname,
                "firstname": candidate.firstname,
                "middleInitial": candidate.middle_initial,
                "position": candidate.position.position_id,
                "affiliation": candidate.affiliation.party_id,
            })
            return True

    @staticmethod
    def update_student(connection, candidate: Candidate) -> bool:
        if not CandidateModel._check_exists(connection, candidate.candidate_id):
            return False
        
        with connection as conn:
            c = conn.cursor()
            c.execute("""
            UPDATE tblCandidate SET
            lastname=%(lastname)s,
            firstname=%(firstname)s,
            middleInitial=%(middleInitial)s,
            position=%(position)s,
            affiliation=%(affiliation)s
            WHERE id=%(id)s
            """,
            {
                "id": candidate.candidate_id,
                "lastname": candidate.lastname,
                "firstname": candidate.firstname,
                "middleInitial": candidate.middle_initial,
                "position": candidate.position.position_id,
                "affiliation": candidate.affiliation.party_id,
            })
            return True

    @staticmethod
    def get_candidate(connection, candidate_id: int=None, lastname: str=None, firstname: str=None, middle_initial: str=None) -> Union[Candidate, None]:
        if candidate_id and not CandidateModel._check_exists(connection, candidate_id):
            return None

        with connection as conn:
            c = conn.cursor()
            query = "SELECT * FROM tblCandidate WHERE "

            if candidate_id is not None:
                query += "id=%(id)s"

                c.execute(query, { "id": candidate_id, })
            else:
                query += "lastname LIKE %(lastname)s "
                params = { "lastname": lastname + '%', }

                if firstname is not None:
                    if not query.endswith(" AND "):
                        query += " AND "
                    query += "firstname LIKE %(firstname)s "
                    params["firstname"] = firstname + '%'

                if middle_initial is not None:
                    if not query.endswith(" AND "):
                        query += " AND "
                    query += "middleInitial LIKE %(middleInitial)s "
                    params["middleInitial"] = middle_initial

                c.execute(query, params)
            
            data = c.fetchone()
            if not data:
                return None
            
            rs_id, rs_lastname, rs_firstname, rs_middleInitial, rs_position, rs_affiliation = data

            c.execute("SELECT * FROM tblSSGPosition WHERE id=%(id)s", { "id": rs_position, })
            position = Position(*c.fetchone())

            c.execute("SELECT * FROM tblParty WHERE id=%(id)s", { "id": rs_affiliation, })
            affiliation = Party(*c.fetchone())

            candidate_data = [rs_id, rs_lastname, rs_firstname, rs_middleInitial, position, affiliation]

            return Candidate(*candidate_data)
