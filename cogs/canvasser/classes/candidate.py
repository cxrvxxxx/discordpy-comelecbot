from dataclasses import dataclass

from .party import Party
from .position import Position

@dataclass
class Candidate(object):
    _candidate_id: int
    _lastname: str
    _firstname: str
    _middle_initial: str
    _position: Position
    _affiliation: Party

    @property
    def candidate_id(self) -> int:
        return self._candidate_id
    
    @property
    def lastname(self) -> str:
        return self._lastname
    
    @property
    def firstname(self) -> str:
        return self._firstname
    
    @property
    def middle_initial(self) -> str:
        return self._middle_initial
    
    @property
    def position(self) -> Position:
        return self._position
    
    @property
    def affiliation(self) -> Party:
        return self._affiliation
