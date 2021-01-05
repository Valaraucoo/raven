import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from courses import forms
from tests.courses import factories as course_factories
from tests.users import factories as users_factories


@pytest.mark.django_db
class TestCoursesGuardianPermissionMixin:
    def get_courses_guardian_permission(self, client):
        student = users_factories.StudentFactory()
        student2 = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        teacher2 = users_factories.TeacherFactory()

        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade, head_teacher=teacher)

        url = reverse('courses:courses-detail')
        client.force_login(student)
        response = client.get(url)
        assert response.status_code == 200

        client.force_login(student2)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        client.force_login(teacher)
        response = client.get(url)
        assert response.status_code == 200

        client.force_login(teacher2)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

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
    def setup_method(self, db):
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
        assert response.status_code == 302

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
    def setup_method(self):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade, head_teacher=teacher)
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
        assert response.url == reverse('courses:courses')

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

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
    def setup_method(self, db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade, head_teacher=teacher)
        course.save()
        lecture = course_factories.LectureFactory(course=course)

        self.student = student
        self.course = course
        self.teacher = teacher
        self.lecture = lecture

    def test_get_lecture_detail(self, client):
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
    def setup_method(self, db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade, head_teacher=teacher)
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
    def setup_method(self, db):
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
        self.laboratory = lab

    def test_get_laboratory_detail(self, client):
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
    def setup_method(self, db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade, head_teacher=teacher)
        course.teachers.add(teacher)
        course.save()
        group = course_factories.GroupFactory(course=course)
        group.save()
        lab = course_factories.LabFactory(group=group)

        self.student = student
        self.course = course
        self.teacher = teacher
        self.laboratory = lab

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
    def setup_method(self, db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade, head_teacher=teacher)
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
    def setup_method(self, db):
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
        # form = response.context.get('form')
        # assert form.is_valid()


class TestCoursesGroupEditView:
    student = None
    teacher = None
    course = None
    group = None

    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade, head_teacher=teacher)
        course.save()
        group = course_factories.GroupFactory(course=course)
        group.save()

        self.student = student
        self.course = course
        self.teacher = teacher
        self.group = group

    def test_group_create(self, client):
        url = reverse('courses:group-create', args=(self.course.slug,))
        client.force_login(self.student)
        response = client.get(url)
        assert response.status_code == 302

        teacher2 = users_factories.TeacherFactory()
        client.force_login(teacher2)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        client.force_login(self.teacher)
        response = client.post(url, {'name': self.group.name, 'course': self.course})
        assert response.url == reverse('courses:group-edit', args=(self.group.pk + 1,))

        client.force_login(self.teacher)
        response = client.get(url)
        assert response.status_code == 200

    def test_group_delete(self, client):
        url = reverse('courses:group-delete', args=(self.course.slug, 0,))
        client.force_login(self.student)
        response = client.get(url)
        assert response.status_code == 302

        teacher2 = users_factories.TeacherFactory()
        client.force_login(teacher2)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        client.force_login(self.teacher)
        response = client.get(url)
        assert response.status_code == 302

    def test_group_join(self, client):
        url = reverse('courses:group-join-group', args=(self.course.slug, 0,))
        client.force_login(self.teacher)
        response = client.get(url)
        assert response.status_code == 302

        student_without_group = users_factories.StudentFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student_without_group)
        grade.save()
        course = course_factories.CourseFactory(grade=grade)
        course.save()

        client.force_login(student_without_group)
        response = client.get(url)
        #assert response.status_code == 302  # response.url == reverse('courses:courses-detail', args=(course.slug,))
        assert response.url == reverse('courses:courses')

        grade.students.add(student_without_group)
        grade.save()
        group = course_factories.GroupFactory(course=course)
        group.save()
        group.students.add(student_without_group)

        assert [student for student in group.students.all()] == [student_without_group]
        client.force_login(student_without_group)
        response = client.get(url)
        assert response.status_code == 302


class TestLectureChangesView:
    student = None
    teacher = None
    course = None
    lecture = None

    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        course = course_factories.CourseFactory(head_teacher=teacher)
        course.teachers.add(teacher)
        course.save()
        lecture = course_factories.LectureFactory(course=course)

        self.student = student
        self.course = course
        self.teacher = teacher
        self.lecture = lecture

    def test_delete_lecture(self, client):
        url = reverse('courses:lectures-delete', args=(self.course.slug, 0,))
        client.force_login(self.student)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        client.force_login(self.teacher)
        response = client.get(url)
        assert response.status_code == 302

    def test_add_lecture_file(self, client):
        url = reverse('courses:lectures-file-add', args=(self.lecture.pk,))
        client.force_login(self.student)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        client.force_login(self.teacher)
        file = SimpleUploadedFile("file.txt", b"these are the file contents!")

        form = client.post(url, {'filename': 'test', 'description': 'opis', 'file': file})
        response = client.get(url, {'lecture': self.lecture, 'form': form})
        assert response.status_code == 200

        form = client.post(url, {'filename': 'test', 'description': 'opis', 'file': 'file2.txt'})
        response = client.get(url, {'lecture': self.lecture, 'form': form})
        assert response.status_code == 200

    def test_delete_lecture_file(self, client):
        url_delete = reverse('courses:lectures-file-delete', args=(self.lecture.pk, 0))
        client.force_login(self.student)
        response = client.get(url_delete)
        assert response.url == reverse('courses:courses')

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url_delete)
        assert response.url == reverse('courses:courses')

        client.force_login(self.teacher)
        file = SimpleUploadedFile("file.txt", b"these are the file contents!")
        url_add = reverse('courses:lectures-file-add', args=(self.lecture.pk,))
        form = client.post(url_add, {'filename': 'test', 'description': 'opis', 'file': file})
        client.get(url_add, {'lecture': self.lecture, 'form': form})

        response = client.get(url_delete)
        assert response.status_code == 302


class TestLaboratoryChangesView:
    student = None
    teacher = None
    course = None
    laboratory = None

    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        course = course_factories.CourseFactory(head_teacher=teacher)
        course.teachers.add(teacher)
        course.save()
        group = course_factories.GroupFactory(course=course)
        group.save()
        lab = course_factories.LabFactory(course=course, group=group)

        self.student = student
        self.course = course
        self.teacher = teacher
        self.laboratory = lab

    def test_add_laboratory_file(self, client):
        url = reverse('courses:laboratory-file-add', args=(self.laboratory.pk,))
        client.force_login(self.student)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        client.force_login(self.teacher)
        file = SimpleUploadedFile("file.txt", b"these are the file contents!")

        form = client.post(url, {'filename': 'test', 'description': 'opis', 'file': file})
        response = client.get(url, {'laboratory': self.laboratory, 'form': form})
        assert response.status_code == 200

        form = client.post(url, {'filename': 'test', 'description': 'opis', 'file': 'file2.txt'})
        response = client.get(url, {'laboratory': self.laboratory, 'form': form})
        assert response.status_code == 200

    def test_delete_laboratory_file(self, client):
        url_delete = reverse('courses:laboratory-file-delete', args=(self.laboratory.pk, 0))
        client.force_login(self.student)
        response = client.get(url_delete)
        assert response.url == reverse('courses:courses')

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url_delete)
        assert response.url == reverse('courses:courses')

        client.force_login(self.teacher)
        file = SimpleUploadedFile("file.txt", b"these are the file contents!")
        url_add = reverse('courses:laboratory-file-add', args=(self.laboratory.pk,))
        form = client.post(url_add, {'filename': 'test', 'description': 'opis', 'file': file})
        client.get(url_add, {'laboratory': self.laboratory, 'form': form})

        response = client.get(url_delete)
        assert response.status_code == 302


class TestCourseNoticeView:
    student = None
    teacher = None
    course = None
    notice = None

    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        course = course_factories.CourseFactory(head_teacher=teacher)
        course.teachers.add(teacher)
        course.save()
        notice = course_factories.NoticeFactory(course=course, sender=teacher)
        notice.not_viewed.add(student)
        notice.save()

        self.student = student
        self.course = course
        self.teacher = teacher
        self.notice = notice

    def test_get_notice(self, client):
        url = reverse('courses:notices', args=(self.course.slug,))
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()

        client.force_login(student)
        response = client.get(url)
        assert response.status_code == 302

        client.force_login(teacher)
        response = client.get(url)
        assert response.status_code == 302

        client.force_login(self.student)
        response = client.get(url)
        assert response.status_code == 200

    def test_post_notice(self, client):
        url = reverse('courses:notices', args=(self.course.slug,))
        teacher = users_factories.TeacherFactory()

        client.force_login(teacher)
        response = client.post(url)
        assert response.status_code == 302

        client.force_login(self.student)
        response = client.post(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestMyCourseMarkView:
    student = None
    teacher = None
    course = None
    mark = None

    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        course = course_factories.CourseFactory(head_teacher=teacher)
        course.teachers.add(teacher)
        course.save()
        mark = course_factories.CourseMarkFactory(course=course, student=student, teacher=teacher)

        self.student = student
        self.teacher = teacher
        self.course = course
        self.mark = mark

    def test_get_my_mark(self, client):
        url = reverse('courses:my-marks', args=(self.course.slug,))

        client.force_login(self.student)
        response = client.get(url)
        assert response.status_code == 200

        student2 = users_factories.StudentFactory()
        client.force_login(student2)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        teacher2 = users_factories.TeacherFactory()
        client.force_login(teacher2)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        client.force_login(self.teacher)
        response = client.get(url)
        assert response.url == reverse('courses:courses-marks', args=(self.course.slug,))


class TestCourseMarkView:
    student = None
    teacher = None
    course = None
    mark = None

    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        course = course_factories.CourseFactory(head_teacher=teacher)
        course.teachers.add(teacher)
        course.save()
        mark = course_factories.CourseMarkFactory(course=course, student=student, teacher=teacher)

        self.student = student
        self.teacher = teacher
        self.course = course
        self.mark = mark

    def test_get_mark(self, client):
        url = reverse('courses:courses-marks', args=(self.course.slug,))

        client.force_login(self.student)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        client.force_login(self.teacher)
        response = client.get(url)
        assert response.status_code == 200

    def test_post_mark(self, client):
        url = reverse('courses:courses-marks', args=(self.course.slug,))

        client.force_login(self.student)
        response = client.post(url)
        assert response.url == reverse('courses:courses')

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.post(url)
        assert response.url == reverse('courses:courses')

        client.force_login(self.teacher)
        response = client.post(url)
        assert response.status_code == 200


class TestCourseTotalMarkView:
    student = None
    teacher = None
    course = None
    mark = None

    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        course = course_factories.CourseFactory(head_teacher=teacher)
        course.teachers.add(teacher)
        course.save()
        mark = course_factories.CourseMarkFactory(course=course, student=student, teacher=teacher)

        self.student = student
        self.teacher = teacher
        self.course = course
        self.mark = mark

    def test_get_total_mark(self, client):
        url = reverse('courses:courses-total-marks', args=(self.course.slug,))

        client.force_login(self.student)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        client.force_login(self.teacher)
        response = client.get(url)
        assert response.status_code == 200


class TestCourseFinalMarkView:
    student = None
    teacher = None
    course = None
    mark = None

    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        course = course_factories.CourseFactory(head_teacher=teacher)
        course.teachers.add(teacher)
        course.save()
        mark = course_factories.FinalCourseMarkFactory(course=course, student=student, teacher=teacher)

        self.student = student
        self.teacher = teacher
        self.course = course
        self.mark = mark

    def test_set_final_mark(self, client):
        url = reverse('courses:set-final-mark', args=(self.course.slug + 'nieistniejacy', self.student.pk,))
        client.force_login(self.teacher)
        response = client.post(url)
        assert response.status_code == 302

        url = reverse('courses:set-final-mark', args=(self.course.slug, self.student.pk + 10000,))
        response = client.post(url)
        assert response.status_code == 302

        url = reverse('courses:set-final-mark', args=(self.course.slug, self.student.pk,))

        client.force_login(self.student)
        response = client.post(url)
        assert response.url == reverse('courses:courses')

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.post(url)
        assert response.url == reverse('courses:courses')

    def test_edit_final_mark(self, client):
        url = reverse('courses:edit-final-mark', args=(self.course.slug + 'nieistniejacy', self.student.pk,))
        client.force_login(self.teacher)
        response = client.post(url)
        assert response.status_code == 302

        url = reverse('courses:edit-final-mark', args=(self.course.slug, self.student.pk + 10000, ))
        response = client.post(url)
        assert response.status_code == 302

        url = reverse('courses:edit-final-mark', args=(self.course.slug, self.student.pk,))

        teacher2 = users_factories.TeacherFactory()
        client.force_login(teacher2)
        response = client.post(url)
        assert response.url == reverse('courses:courses')

        client.force_login(self.teacher)
        response = client.post(url)
        assert response.status_code == 200

        client.force_login(self.student)
        response = client.post(url)
        assert response.url == reverse('courses:courses')


class TestCourseMarkEditView:
    student = None
    teacher = None
    course = None
    mark = None

    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        course = course_factories.CourseFactory(head_teacher=teacher)
        course.teachers.add(teacher)
        course.save()
        mark = course_factories.CourseMarkFactory(course=course, student=student, teacher=teacher)

        self.student = student
        self.teacher = teacher
        self.course = course
        self.mark = mark

    def test_get_mark_edit(self, client):
        url = reverse('courses:courses-marks-edit', args=(self.mark.pk,))

        student = users_factories.StudentFactory()
        client.force_login(student)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        client.force_login(self.teacher)
        response = client.get(url)
        assert response.status_code == 200

    def test_post_mark_edit(self, client):
        url = reverse('courses:courses-marks-edit', args=(self.mark.pk,))

        student = users_factories.StudentFactory()
        client.force_login(student)
        response = client.post(url)
        assert response.url == reverse('courses:courses')

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.post(url)
        assert response.url == reverse('courses:courses')

        client.force_login(self.teacher)
        response = client.post(url)
        assert response.status_code == 200

    def test_delete_mark(self, client):
        url = reverse('courses:courses-marks-delete', args=(self.course.slug + 'nieistniejacy', 0,))
        client.force_login(self.teacher)
        response = client.post(url)
        assert response.status_code == 302

        url = reverse('courses:courses-marks-delete', args=(self.course.slug, 0,))
        count = self.course.marks.all().count()

        client.force_login(self.student)
        response = client.post(url)
        assert response.url == reverse('courses:courses')

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.post(url)
        assert response.url == reverse('courses:courses')

        client.force_login(self.teacher)
        response = client.post(url)
        assert response.status_code == 302
        assert self.course.marks.all().count() == count - 1


class TestAssignmentView:
    student = None
    teacher = None
    lab = None
    assignment = None

    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        course = course_factories.CourseFactory(head_teacher=teacher)
        course.teachers.add(teacher)
        course.save()
        group = course_factories.GroupFactory(course=course)
        group.save()
        lab = course_factories.LabFactory(course=course, group=group)
        assignment = course_factories.AssignmentFactory(laboratory=lab, teacher=teacher)

        self.student = student
        self.teacher = teacher
        self.lab = lab
        self.assignment = assignment

    def test_get_assignment_create(self, client):
        url = reverse('courses:assignments-create', args=(self.lab.pk,))

        client.force_login(self.student)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url)
        assert response.url == reverse('courses:courses')

        client.force_login(self.teacher)
        response = client.get(url)
        assert response.status_code == 200

    def test_post_assignment_create(self, client):
        url = reverse('courses:assignments-create', args=(self.lab.pk,))

        client.force_login(self.student)
        response = client.post(url)
        assert response.url == reverse('courses:courses')

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.post(url)
        assert response.url == reverse('courses:courses')

    def test_delete_assignment(self, client):
        url = reverse('courses:assignments-delete', args=(self.lab.pk + 100, 0,))
        client.force_login(self.teacher)
        response = client.post(url)
        assert response.status_code == 302

        url = reverse('courses:assignments-delete', args=(self.lab.pk, 0,))
        count = self.lab.assignments.all().count()

        client.force_login(self.student)
        response = client.post(url)
        assert response.url == reverse('courses:courses')

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.post(url)
        assert response.url == reverse('courses:courses')

        client.force_login(self.teacher)
        response = client.post(url)
        assert response.status_code == 302
        assert self.lab.assignments.all().count() == count - 1
