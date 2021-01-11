import datetime

import pytest
from django.core.exceptions import ValidationError

from tests.courses import factories as course_factories
from tests.users import factories as users_factories


@pytest.mark.django_db
class TestGradeModel:
    def test_string_grade_model(self):
        grade = course_factories.GradeFactory()
        assert f'{grade.name} ({grade.start_year.year} - {grade.finish_year.year})' == str(grade)

    def test_finish_year(self):
        grade = course_factories.GradeFactory()
        assert grade.start_year + datetime.timedelta(days=365 * 3) == grade.finish_year


@pytest.mark.django_db
class TestCourseModel:
    def test_string_course_model(self):
        course = course_factories.CourseFactory()
        assert f'Course: {course.name}' == str(course)

    def test_clean_course_model(self):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        with pytest.raises(ValidationError):
            course = course_factories.CourseFactory(head_teacher=student)
            course.clean()
        course = course_factories.CourseFactory(head_teacher=teacher)
        course.clean()

    def test_total_students(self):
        grade = course_factories.GradeFactory()
        course = course_factories.CourseFactory(grade=grade)
        assert list(grade.students.all().union(course.additional_students.all())) == list(course.total_students)

    def test_students_without_groups(self):
        course = course_factories.CourseFactory()
        assert list(course.total_students) == course.students_without_groups


@pytest.mark.django_db
class TestCourseGroupModel:
    def test_string_course_group_model(self):
        course = course_factories.CourseFactory()
        course.save()
        group = course_factories.GroupFactory(course=course)
        group.save()
        assert group.name == str(group)

    def test_students_group_count(self):
        course = course_factories.CourseFactory()
        course.save()
        group = course_factories.GroupFactory(course=course)
        group.save()
        assert group.students.count() == group.students_count


@pytest.mark.django_db
class TestEventModel:
    def test_is_event_available(self):
        course = course_factories.CourseFactory()
        course.save()
        group = course_factories.GroupFactory(course=course)
        group.save()
        lab = course_factories.LabFactory(group=group)

        lab.show = True
        assert lab.is_available == True

        lab.show = False
        lab.time_delta = datetime.timedelta(days=0)
        assert lab.is_available == False

    def test_event_end_date(self):
        course = course_factories.CourseFactory()
        course.save()
        group = course_factories.GroupFactory(course=course)
        group.save()
        lab = course_factories.LabFactory(group=group)

        assert lab.date + lab.duration == lab.end_date


@pytest.mark.django_db
class TestLectureModel:
    def test_string_lecture_model(self):
        course = course_factories.CourseFactory()
        course.save()
        lecture = course_factories.LectureFactory(course=course)
        assert f'Lecture: {lecture.title}({lecture.date})' == str(lecture)

    def test_lecture_students(self):
        grade = course_factories.GradeFactory()
        grade.save()
        course = course_factories.CourseFactory(grade=grade)
        course.save()
        lecture = course_factories.LectureFactory(course=course)
        assert list(lecture.course.grade.students.all()) == list(lecture.students)


@pytest.mark.django_db
class TestLaboratoryModel:
    def test_string_laboratory_model(self):
        course = course_factories.CourseFactory()
        course.save()
        group = course_factories.GroupFactory(course=course)
        group.save()
        lab = course_factories.LabFactory(group=group)
        assert f'Laboratory: {lab.title}({lab.date})' == str(lab)


@pytest.mark.django_db
class TestCourseMarkModel:
    def test_string_course_mark_model(self):
        mark = course_factories.CourseMarkFactory()
        mark.save()
        assert f'Course Mark: {mark.student}, {mark.course}' == str(mark)

    def test_mark_decimal(self):
        mark = course_factories.CourseMarkFactory(mark=20)
        assert mark.mark_decimal == 2.0

        mark = course_factories.CourseMarkFactory(mark=50)
        assert mark.mark_decimal == 3.0

        mark = course_factories.CourseMarkFactory(mark=70)
        assert mark.mark_decimal == 4.0

        mark = course_factories.CourseMarkFactory(mark=80)
        assert mark.mark_decimal == 4.5

        mark = course_factories.CourseMarkFactory(mark=90)
        assert mark.mark_decimal == 5.0


@pytest.mark.django_db
class TestFinalCourseMarkModel:
    def test_string_final_course_mark_model(self):
        final_mark = course_factories.FinalCourseMarkFactory()
        final_mark.save()
        assert f'Final Course Mark: {final_mark.student}, {final_mark.course}' == str(final_mark)


@pytest.mark.django_db
class TestCourseNoticeModel:
    def test_string_course_notice_model(self):
        notice = course_factories.NoticeFactory()
        notice.save()
        assert f'Course Notice: {notice.course}, {notice.title}' == str(notice)


@pytest.mark.django_db
class TestAssignmentModel:
    assignment = None

    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        teacher = users_factories.TeacherFactory()
        course = course_factories.CourseFactory(head_teacher=teacher)
        course.teachers.add(teacher)
        course.save()
        group = course_factories.GroupFactory(course=course)
        group.save()
        lab = course_factories.LabFactory(course=course, group=group)
        assignment = course_factories.AssignmentFactory(laboratory=lab, teacher=teacher)

        self.assignment = assignment

    def test_string_assignment_model(self):
        assert f'Assignment: {self.assignment.title} {self.assignment.deadline}' == str(self.assignment)


@pytest.mark.django_db
class TestCourseFileModel:
    def test_string_file_model(self):
        file = course_factories.CourseFileFactory()
        assert f'{file.name} - {file.filename}' == str(file)
