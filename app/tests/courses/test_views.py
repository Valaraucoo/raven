import pytest
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
    student = None
    teacher = None
    course = None

    @pytest.fixture(autouse=True)
    def setup_method(self,db):
        student = users_factories.StudentFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade)
        course.save()
        teacher = users_factories.TeacherFactory()

        self.student = student
        self.course = course
        self.teacher = teacher

    def test_get_course_edit(self, client):
        url = reverse('courses:courses-edit', args=(self.course.slug,))

        client.force_login(self.student)
        response = client.get(url)
        assert response.status_code == 200

        client.force_login(self.teacher)
        response = client.get(url)
        assert response.status_code == 302

    def test_post_course_edit(self, client):
        url = reverse('courses:courses-edit', args=(self.course.slug,))

        client.force_login(self.teacher)
        response = client.post(url)
        assert response.status_code == 302

        client.force_login(self.student)
        response = client.post(url)
        assert response.status_code == 200

        resp_name = client.post(url, {'name': self.course.name})
        assert resp_name.status_code == 200

        resp_description = client.post(url, {'description': self.course.description})
        assert resp_description.status_code == 200

@pytest.mark.django_db
class TestCourseGroupEditView:
    student = None
    teacher = None
    course = None
    group = None

    @pytest.fixture(autouse=True)
    def setup_method(self,db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade)
        course.save()
        group = course_factories.GroupFactory(course=course)

        self.student = student
        self.teacher = teacher
        self.course = course
        self.group = group

    def test_get_course_group_edit(self, client):
        url = reverse('courses:group-edit', args=(self.group.pk,))

        client.force_login(self.student)
        response = client.get(url)
        assert response.status_code == 302

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url)
        assert response.status_code == 302

        client.force_login(self.teacher)
        response = client.get(url)
        assert response.status_code == 200

    def test_post_course_group_edit(self, client):
        url = reverse('courses:group-edit', args=(self.group.pk,))

        client.force_login(self.student)
        response = client.post(url)
        assert response.status_code == 302

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.post(url)
        assert response.status_code == 302

        client.force_login(self.teacher)
        response = client.post(url)
        assert response.status_code == 200

        resp_name = client.post(url, {'name': self.course.name})
        assert resp_name.status_code == 200

class TestLectureDetailView:
    student = None
    teacher = None
    course = None
    lecture = None

    @pytest.fixture(autouse=True)
    def setup_method(self,db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade)
        course.save()
        lecture = course_factories.LectureFactory(course=course)

        self.student = student
        self.course = course
        self.teacher = teacher
        self.lecture = lecture

    def test_get_lecture_detail(self,client):
        url = reverse('courses:lectures-detail', args=(self.lecture.pk,))

        # client.force_login(self.student)
        # response = client.get(url)
        # assert response.status_code == 200

        student = users_factories.StudentFactory()
        client.force_login(student)
        response = client.get(url)
        assert response.status_code == 302

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url)
        assert response.status_code == 302

class TestLectureEditView:
    student = None
    teacher = None
    course = None
    lecture = None

    @pytest.fixture(autouse=True)
    def setup_method(self,db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade)
        course.save()
        lecture = course_factories.LectureFactory(course=course)

        self.student = student
        self.course = course
        self.teacher = teacher
        self.lecture = lecture

    def test_get_lecture_edit(self, client):
        url = reverse('courses:lectures-edit', args=(self.lecture.pk,))

        client.force_login(self.student)
        response = client.get(url)
        assert response.status_code == 302

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url)
        assert response.status_code == 302

        client.force_login(self.teacher)
        response = client.get(url)
        assert response.status_code == 200

    def test_post_lecture_edit(self, client):
        url = reverse('courses:lectures-edit', args=(self.lecture.pk,))

        client.force_login(self.student)
        response = client.post(url)
        assert response.status_code == 302

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.post(url)
        assert response.status_code == 302

        client.force_login(self.teacher)
        response = client.post(url)
        assert response.status_code == 200

class TestLaboratoryDetailView:
    student = None
    teacher = None
    course = None
    laboratory = None

    @pytest.fixture(autouse=True)
    def setup_method(self,db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade)
        course.save()
        group = course_factories.GroupFactory(course=course)
        group.save()
        lab = course_factories.LabFactory(group=group)

        self.student = student
        self.course = course
        self.teacher = teacher
        self.laboratory= lab

    def test_get_laboratory_detail(self,client):
        url = reverse('courses:laboratory-detail', args=(self.laboratory.pk,))

        # client.force_login(self.student)
        # response = client.get(url)
        # assert response.status_code == 200

        student = users_factories.StudentFactory()
        client.force_login(student)
        response = client.get(url)
        assert response.status_code == 302

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url)
        assert response.status_code == 302

class TestLaboratoryEditView:
    student = None
    teacher = None
    course = None
    laboratory = None

    @pytest.fixture(autouse=True)
    def setup_method(self,db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade, head_teacher=teacher)
        course.save()
        group = course_factories.GroupFactory(course=course)
        group.save()
        lab = course_factories.LabFactory(group=group)

        self.student = student
        self.course = course
        self.teacher = teacher
        self.laboratory= lab

    def test_get_laboratory_edit(self, client):
        url = reverse('courses:laboratory-edit', args=(self.laboratory.pk,))

        client.force_login(self.student)
        response = client.get(url)
        assert response.status_code == 302

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url)
        assert response.status_code == 302

        client.force_login(self.teacher)
        response = client.get(url)
        assert response.status_code == 200

    def test_post_laboratory_edit(self, client):
        url = reverse('courses:laboratory-edit', args=(self.laboratory.pk,))

        client.force_login(self.student)
        response = client.post(url)
        assert response.status_code == 302

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.post(url)
        assert response.status_code == 302

        client.force_login(self.teacher)
        response = client.post(url)
        assert response.status_code == 200

class TestLectureCreateView:
    student = None
    teacher = None
    course = None
    lecture = None

    @pytest.fixture(autouse=True)
    def setup_method(self,db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade)
        course.save()
        lecture = course_factories.LectureFactory(course=course)

        self.student = student
        self.course = course
        self.teacher = teacher
        self.lecture = lecture

    def test_get_lecture_create(self, client):
        url = reverse('courses:lectures-create', args=(self.course.slug,))

        client.force_login(self.student)
        response = client.get(url)
        assert response.status_code == 302

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url)
        assert response.status_code == 302

        client.force_login(self.teacher)
        response = client.get(url)
        assert response.status_code == 200

    def test_post_lecture_edit(self, client):
        url = reverse('courses:lectures-create', args=(self.course.slug,))

        client.force_login(self.student)
        response = client.post(url)
        assert response.status_code == 302

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.post(url)
        assert response.status_code == 302

        client.force_login(self.teacher)
        response = client.post(url)
        assert response.status_code == 200


class TestLaboratoryCreateView:
    student = None
    teacher = None
    course = None
    group = None
    laboratory = None

    @pytest.fixture(autouse=True)
    def setup_method(self,db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade)
        course.save()
        group = course_factories.GroupFactory(course=course)
        group.save()
        lab = course_factories.LabFactory(group=group)

        self.student = student
        self.course = course
        self.teacher = teacher
        self.group = group
        self.laboratory = lab

    def test_get_laboratory_create(self, client):
        url = reverse('courses:laboratory-create', args=(self.course.slug,))

        client.force_login(self.student)
        response = client.get(url)
        assert response.status_code == 302

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url)
        assert response.status_code == 302

        client.force_login(self.teacher)
        response = client.get(url)
        assert response.status_code == 200

    def test_post_laboratory_create(self, client):
        url = reverse('courses:laboratory-create', args=(self.course.slug,))

        client.force_login(self.student)
        response = client.post(url)
        assert response.status_code == 302

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.post(url)
        assert response.status_code == 302

        client.force_login(self.teacher)
        response = client.post(url)
        assert response.status_code == 200
        #form = response.context.get('form')
        #assert form.is_valid()

