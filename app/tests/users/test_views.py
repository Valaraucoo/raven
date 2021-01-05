import pytest
from django.urls import reverse

from tests.courses import factories as course_factories
from tests.users import factories as users_factories


@pytest.mark.django_db
class TestProfileView:
    def test_get_profile(self, client):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()
        url = reverse('users:profile')

        client.force_login(teacher)
        response = client.get(url)
        assert response.status_code == 200

        client.force_login(student)
        response = client.get(url)
        assert response.status_code == 200

        profile = response.context.get('profile')
        assert profile.full_username == f"{profile.first_name} {profile.last_name} ({profile.email})"

    def test_get_unauthenticated_profile(self, client):
        url = reverse('users:profile')
        response = client.get(url)
        assert response.status_code == 302


class TestProfileDetailView:
    def test_get_profile_detail(self, user_client):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()

        student_url = reverse('users:profile-detail', args=(student.pk,))
        teacher_url = reverse('users:profile-detail', args=(teacher.pk,))

        response_student = user_client.get(student_url)
        response_teacher = user_client.get(teacher_url)

        assert response_student.context.get('profile') == student
        assert response_teacher.context.get('profile') == teacher

        user_id = user_client.session['_auth_user_id']
        url = reverse('users:profile-detail', args=(user_id,))

        response = user_client.get(url)
        assert response.status_code == 302


class TestProfileEditView:
    def test_post_unauthenticated_edit(self, client):
        url = reverse('users:profile-edit')
        response = client.post(url)
        assert response.status_code == 302

    def test_post_edit(self, user_client):
        url = reverse('users:profile-edit')
        response = user_client.post(url)
        assert response.status_code == 200

    def test_post_password_change(self, user_client):
        url = reverse('users:profile-edit')

    def test_post_edit_data(self, user_client):
        user = users_factories.StudentFactory()
        url = reverse('users:profile-edit')
        data = {
            'address': user.address,
            'description': user.description,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'image': user.image
        }

        response = user_client.post(url, data)
        assert response.status_code == 200


@pytest.mark.django_db
class TestDashboardView:
    def test_get_dashboard(self, client):
        student = users_factories.StudentFactory()
        url = reverse('users:dashboard')

        client.force_login(student)
        response = client.get(url)
        assert response.status_code == 200

        user = response.context.get('user')
        assert user.full_username == f"{user.first_name} {user.last_name} ({user.email})"

        teacher = users_factories.TeacherFactory()
        # grade = course_factories.GradeFactory()
        # grade.students.add(student)
        # grade.save()
        # course = course_factories.CourseFactory(grade=grade, head_teacher=teacher)
        client.force_login(teacher)
        assert response.status_code == 200
        # assert [course for course in teacher.courses_teaching.all() if course.is_actual] == response.context.get('courses')

    def test_get_unauthenticated_dashboard(self, client):
        url = reverse('users:dashboard')
        response = client.get(url)
        assert response.status_code == 302


@pytest.mark.django_db
class TestScheduleView:
    def test_get_schedule(self, client):
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

        url = reverse('users:schedule')

        client.force_login(student)
        response = client.get(url)
        assert response.status_code == 200

        client.force_login(teacher)
        response = client.get(url)
        assert response.status_code == 200

        # user = response.context.get('user')
        # assert False, grade.courses.all()

    def test_get_schedule_unauthenticated(self, client):
        url = reverse('users:schedule')
        response = client.get(url)
        assert response.status_code == 302


@pytest.mark.django_db
class TestNoticeView:
    def test_get_notice(self, client):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()

        url = reverse('users:notices')

        client.force_login(student)
        response = client.get(url)
        assert response.status_code == 200

        client.force_login(teacher)
        response = client.get(url)
        assert response.status_code == 200

        # user = response.context.get('user')
        # assert False, grade.courses.all()

    def test_get_notice_unauthenticated(self, client):
        url = reverse('users:notices')
        response = client.get(url)
        assert response.status_code == 302


@pytest.mark.django_db
class TestLoginView:
    def test_get_login(self, user_client):
        url = reverse('users:login')
        response = user_client.get(url)
        assert response.status_code == 302

    def test_get_unauthenticated_login(self, client):
        url = reverse('users:login')
        response = client.get(url)
        assert response.status_code == 200

        # student = users_factories.StudentFactory()
        # user = authenticate(email=student.email, password=student.email)
        # client.force_login(student)
        # user = get_user(client)
        # assert user.is_authenticated
        # response = client.get(url)
        # assert response.status_code == 302

    def test_post_authenticated_login(self, user_client):
        url = reverse('users:login')
        response = user_client.post(url)
        assert response.status_code == 302

    def _get_token(self, client, url, data):
        resp = client.get(url)
        data['csrfmiddlewaretoken'] = resp.cookies['csrftoken'].value
        return data

    def test_post_login(self, client):
        url = reverse('users:login')
        user = users_factories.StudentFactory()
        user.save()
        resp = client.post(url)
        data = {
            'csrfmiddlewaretoken': resp.cookies['csrftoken'].value,
            'email': user.email,
            'password': user.password,
            'remember': True
        }
        # data = self._get_token(client, url, data)
        response = client.post(url, data=data)
        assert response.status_code == 200


class TestLogoutView:
    def test_get_logout(self, user_client):
        url = reverse('users:logout')
        response = user_client.get(url)
        assert response.status_code == 302


@pytest.mark.django_db
class TestMarksView:
    def test_get_marks(self, client):
        url = reverse('users:marks')
        response = client.get(url)
        assert response.status_code == 302

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url)
        assert response.url == reverse('users:dashboard')

        student = users_factories.StudentFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade)
        course.save()
        mark = course_factories.CourseMarkFactory(student=student, course=course)
        client.force_login(student)
        response = client.get(url)
        marks = response.context.get('marks')
        assert marks.first().student == mark.student


@pytest.mark.django_db
class TestSummaryView:
    def test_get_summary(self, client):
        url = reverse('users:summary')
        response = client.get(url)
        assert response.status_code == 302

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url)
        assert response.url == reverse('users:dashboard')

        student = users_factories.StudentFactory()
        grade = course_factories.GradeFactory()
        grade.students.add(student)
        grade.save()
        course = course_factories.CourseFactory(grade=grade)
        course.save()
        final_mark = course_factories.FinalCourseMarkFactory(student=student, course=course)

        client.force_login(student)
        response = client.get(url)

        summary = response.context.get('summary')
        grades = response.context.get('grades')
        assert grades.first() == grade
        assert list(summary.keys())[0] == grade


@pytest.mark.django_db
class TestAssignmentsView:
    def test_get_assignments(self, client):
        url = reverse('users:assignments')
        response = client.get(url)
        assert response.status_code == 302

        teacher = users_factories.TeacherFactory()
        client.force_login(teacher)
        response = client.get(url)
        assert response.url == reverse('users:dashboard')

        student = users_factories.StudentFactory()
        client.force_login(student)
        response = client.get(url)
        # marks = response.context.get('marks')
        assert response.status_code == 200


class TestDeleteProfileImageView:
    def test_delete_image(self, user_client):
        user = users_factories.StudentFactory()
        user_client.force_login(user)

        assert 'defaults/default-picture.png' not in user.image.url

        url = reverse('users:profile-img-delete')
        response = user_client.get(url)
        user.refresh_from_db()

        assert 'defaults/default-picture.png' in user.image.url
