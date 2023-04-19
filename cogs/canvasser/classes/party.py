from dataclasses import dataclass

@dataclass(frozen=True)
class Party(object):
    _party_id: int
    _name: str

    @property
    def party_id(self) -> int:
        return self._party_id
    
    @property
    def name(self) -> str:
        return self._name
