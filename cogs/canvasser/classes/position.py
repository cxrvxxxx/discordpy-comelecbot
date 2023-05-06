from dataclasses import dataclass

@dataclass(frozen=True)
class Position(object):
    _position_id: int
    _name: str

    @property
    def position_id(self) -> int:
        return self._position_id
    
    @property
    def name(self) -> str:
        return self._name
