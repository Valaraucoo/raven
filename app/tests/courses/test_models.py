import datetime

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from courses import models as course_models
from tests.courses import factories as course_factories
from tests.users import factories as users_factories


@pytest.mark.django_db
class TestGradeModel:
    def test_string_grade_model(self):
        grade = course_factories.GradeFactory()
        assert f'Grade: {grade.name} ({grade.start_year.year} - {grade.finish_year.year})' == str(grade)

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
        assert (lab.date - timezone.now().date() < lab.time_delta) == lab.is_available

        lab.time_delta = datetime.timedelta(days=0)
        assert lab.is_available == False

    def test_event_held(self):
        course = course_factories.CourseFactory()
        course.save()
        group = course_factories.GroupFactory(course=course)
        group.save()
        lab = course_factories.LabFactory(group=group)

        assert (lab.date < timezone.now().date()) == lab.was_held

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

class TestCourseFileModel:
    pass

# class TestLectureMarkModel:
#     def test_string_lecture_model(self,db):
#         student = users_factories.StudentFactory()
#         teacher = users_factories.TeacherFactory()
#         course = course_factories.CourseFactory()
#         course.save()
#         lecture = course_factories.LectureFactory(course=course)
#         course.save()
#         lecture_mark = course_factories.LectureMarkFactory(lecture=lecture,student=student,teacher=teacher)
#         assert f'Lecture Mark: {lecture_mark.student}, {lecture_mark.lecture}' == str(lecture_mark)

