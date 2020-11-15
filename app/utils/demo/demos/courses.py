from tests.courses import factories

from users.models import Student, Teacher


class CourseDemo:
    def generate(self):
        for i in range(3):
            self.generate_course(i)

    @staticmethod
    def generate_course(i) -> None:
        grade = factories.GradeFactory()
        students = Student.objects.all()[i*10:i*10+9]
        for student in students:
            grade.students.add(student)

        teachers = Teacher.objects.all()[i:i+3]

        for _ in range(3):
            course = factories.CourseFactory(grade=grade, teachers=[])
            for teacher in teachers:
                course.teachers.add(teacher)
            course.save()
        grade.save()

    def get_info(self):
        return [
            'Done. Generated Grades and Courses.'
        ]