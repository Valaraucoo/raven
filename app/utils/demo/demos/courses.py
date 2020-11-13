from tests.courses import factories
from tests.users import factories as users_factories


class CourseDemo:
    def generate(self):
        for _ in range(3):
            self.generate_course()

    @staticmethod
    def generate_course() -> None:
        grade = factories.GradeFactory()
        students = [users_factories.StudentFactory() for _ in range(10)]
        for student in students:
            student.set_password("example123")
            student.save()
            grade.students.add(student)

        teachers = [users_factories.TeacherFactory() for _ in range(3)]

        for _ in range(3):
            course = factories.CourseFactory(grade=grade)
            for teacher in teachers:
                teacher.set_password("example123")
                teacher.save()
                course.teachers.add(teacher)
            course.save()


    def get_info(self):
        return [
            'Done. Generated Grades and Courses.'
        ]