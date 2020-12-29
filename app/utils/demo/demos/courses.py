from tests.courses import factories


class CourseDemo:
    INFO = 'Done. Generated Grades and Courses.'

    def generate(self):
        for i in range(3):
            self.generate_course()

    @staticmethod
    def generate_course() -> None:
        grade = factories.GradeFactory()

        for _ in range(3):
            course = factories.CourseFactory(grade=grade, teachers=[])
            group = factories.GroupFactory(course=course)

            for teacher in course.teachers.all():
                course.teachers.add(teacher)
            for _ in range(5):
                lecture = factories.LectureFactory(course=course)
                course.lectures.add(lecture)
            for _ in range(5):
                lab = factories.LabFactory(course=course, group=group)
                course.laboratories.add(lab)
            for _ in range(3):
                factories.CourseGroupFactory(course=course)
            course.save()
        grade.save()
