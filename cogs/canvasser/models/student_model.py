from typing import Union

from ..classes.student import Student
from abc import ABCMeta

class StudentModel(ABCMeta):
    @staticmethod
    def _check_exists(connection, student_num: str) -> bool:
        with connection as conn:
            c = conn.cursor()
            c.execute("SELECT studentNo FROM tblStudent WHERE studentNo=%(studentNo)s", { "studentNo": student_num, })
            if c.fetchone():
                return True
            
        return False
    
    @staticmethod
    def add_student(connection, student: Student) -> bool:
        if StudentModel._check_exists(connection, student.student_num):
            return False
        
        with connection as conn:
            c = conn.cursor()
            c.execute("""INSERT INTO tblStudent VALUES
            (%(studentNo)s, %(department)s, %(yearLevel)s)""",
            {
                "studentNo": student.student_num,
                "department": student.program,
                "yearLevel": student.year
            })
            return True

    @staticmethod
    def update_student(connection, student: Student) -> bool:
        if not StudentModel._check_exists(connection, student.student_num):
            return False
        
        with connection as conn:
            c = conn.cursor()
            c.execute("UPDATE tblStudent SET department=%(department)s, yearLevel=%(yearLevel)s WHERE studentNo=%(studentNo)s",
            {
                "studentNo": student.student_num,
                "department": student.program,
                "yearLevel": student.year
            })
            return True

    @staticmethod
    def get_student(connection, student_num: str) -> Union[Student, None]:
        if not StudentModel._check_exists(connection, student_num):
            return None
        
        with connection as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM tblStudent WHERE studentNo=%(studentNo)s", { "studentNo": student_num, })
            student = Student(*c.fetchone())

        return student
