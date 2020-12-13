import pytest
from django.conf import settings
from django.urls import reverse

from tests.courses import factories as course_factories
from tests.users import factories as users_factories


@pytest.mark.django_db
class TestCoursesGuardianPermissionMixin:
    def get_courses_guardian_permission(self, client):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()

        grade = course_factories.GradeFactory()
        grade.save()
        course = course_factories.CourseFactory(grade=grade)

        url = reverse('courses:courses-detail')
        # client.force_login(student)
        response = client.get(url)
        # assert response.status_code == 302


@pytest.mark.django_db
class TestCourseView:
    def test_get_course(self, client):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade)

        url = reverse('courses:courses')
        client.force_login(teacher)
        response = client.get(url)
        assert response.status_code == 200

        client.force_login(student)
        response = client.get(url)
        assert response.status_code == 200

        # query = response.context.get('courses')

        resp_name = client.get(url, {'name': course.name})
        assert resp_name.status_code == 200

        resp_teacher = client.get(url, {'teacher': course.head_teacher})
        assert resp_teacher.status_code == 200

        resp_exam = client.get(url, {'has_exam': 2})
        assert resp_exam.status_code == 200
        # assert query.first().has_exam == resp_exam.context.get('courses').first().has_exam

        resp_exam = client.get(url, {'has_exam': 1})
        assert resp_exam.status_code == 200


@pytest.mark.django_db
class TestCoursesDetailView:
    def test_get_course_detail(self, client):
        student = users_factories.StudentFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade)

        client.force_login(student)
        url = reverse('courses:courses-detail', args=(course.slug,))
        response = client.get(url)
        assert response.status_code == 200

        # labs = response.context.get('available_labs')


@pytest.mark.django_db
class TestCourseGroupJoinListView:
    def test_get_course_group_join_list(self, client):
        student = users_factories.StudentFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory()
        course.save()
        group = course_factories.GroupFactory(course=course)

        client.force_login(student)
        url = reverse('courses:group', args=(course.slug,))
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestCourseGroupCreateView:
    def test_corde_group_create(self, client):
        pass


@pytest.mark.django_db
class TestCourseEditView:
    def test_get_course_edit(self, client):
        student = users_factories.StudentFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade)
        teacher = users_factories.TeacherFactory()

        url = reverse('courses:courses-edit', args=(course.slug,))

        client.force_login(student)
        response = client.get(url)
        assert response.status_code == 200

        client.force_login(teacher)
        response = client.get(url)
        assert response.status_code == 302

    def test_post_course_edit(self, client):
        student = users_factories.StudentFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade)
        teacher = users_factories.TeacherFactory()

        url = reverse('courses:courses-edit', args=(course.slug,))

        client.force_login(teacher)
        response = client.post(url)
        assert response.status_code == 302

        client.force_login(student)
        response = client.post(url)
        assert response.status_code == 200

        resp_name = client.post(url, {'name': course.name})
        assert resp_name.status_code == 200

        resp_description = client.post(url, {'description': course.description})
        assert resp_description.status_code == 200

@pytest.mark.django_db
class TestCourseGroupEditView:
    pass
