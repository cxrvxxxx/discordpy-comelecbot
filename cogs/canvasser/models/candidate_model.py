from typing import List, Union
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
    def get_candidate(connection, candidate_id: int=None, lastname: str=None, firstname: str=None, middle_initial: str=None) -> Union[List[Candidate], None]:
        if candidate_id and not CandidateModel._check_exists(connection, candidate_id):
            return None

        query = "SELECT * FROM tblCandidate WHERE "
        params = {}

        if candidate_id:
            query += "id=%(id)s "

            params["id"] = candidate_id
        elif lastname and firstname:
            query += "lastname LIKE %(lastname)s AND firstname LIKE %(firstname)s "

            params["lastname"] = lastname + '%'
            params["firstname"] = '%' + firstname + '%'
        elif lastname and not firstname:
            query += "lastname LIKE %(lastname)s "
            
            params["lastname"] = lastname + '%'
        elif firstname:
            query += "firstname LIKE %(firstname)s "

            params["firstname"] = '%' + firstname + '%'

        if middle_initial:
            if firstname or lastname:
                query += "AND middleInitial LIKE %(middleInitial)s "
            else:
                query += "middleInitial LIKE %(middleInitial)s "

            params["middleInitial"] = middle_initial + '%'

        with connection as conn:
            c = conn.cursor()
            c.execute(query[:-1], params)
            
            dataset = c.fetchall()

            if not dataset:
                return None
            
            candidates = []
            for data in dataset:
                rs_id, rs_lastname, rs_firstname, rs_middleInitial, rs_position, rs_affiliation = data

                c.execute("SELECT * FROM tblSSGPosition WHERE id=%(id)s", { "id": rs_position, })
                position = Position(*c.fetchone())

                c.execute("SELECT * FROM tblParty WHERE id=%(id)s", { "id": rs_affiliation, })
                affiliation = Party(*c.fetchone())

                candidate_data = [rs_id, rs_lastname, rs_firstname, rs_middleInitial, position, affiliation]

                candidates.append(Candidate(*candidate_data))
            
            return candidates
        
    @staticmethod
    def get_party(connection, name: str) -> Union[List[Candidate], None]:
        with connection as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM tblParty WHERE name LIKE %(name)s", { "name": '%' + name + '%', })
            party_data = c.fetchone()
            if not party_data:
                return None
            
            party = Party(*party_data)
            c.execute("SELECT * FROM tblCandidate WHERE affiliation=%(party)s ORDER BY position ASC", { "party": party.party_id })
            dataset = c.fetchall()

            if not dataset:
                return None
            
            candidates = []
            for data in dataset:
                rs_id, rs_lastname, rs_firstname, rs_middleInitial, rs_position, rs_affiliation = data

                c.execute("SELECT * FROM tblSSGPosition WHERE id=%(id)s", { "id": rs_position, })
                position = Position(*c.fetchone())

                candidate_data = [rs_id, rs_lastname, rs_firstname, rs_middleInitial, position, party]

                candidates.append(Candidate(*candidate_data))
            
            return candidates

    @staticmethod
    def get_position(connection, position_name: str) -> Union[Position, None]:
        with connection as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM tblSSGPosition WHERE name LIKE %(position_name)s", { "position_name": position_name + '%', })
            position_data = c.fetchone()
            if not position_data:
                return None
            
            return Position(*position_data)
        
    @staticmethod
    def get_candidate_by_id(connection, candidate_id) -> Union[Candidate, None]:
        sql = "SELECT * FROM tblCandidate WHERE id=%(candidate_id)s"

        with connection as conn:
            c = conn.cursor()
            c.execute(sql, { "candidate_id": candidate_id, })
            data = c.fetchone()

        if data:
            return Candidate(*data)
