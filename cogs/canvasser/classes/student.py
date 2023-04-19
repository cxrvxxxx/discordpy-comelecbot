from dataclasses import dataclass

@dataclass
class Student(object):
    _student_num: str
    _program: str
    _year: int

    @property
    def student_num(self) -> str:
        return self._student_num
    
    @property
    def program(self) -> str:
        return self._program
    
    @property
    def year(self) -> int:
        return self._year
