from rest_framework import generics, mixins, viewsets
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from courses import models
from users import models as users_models

from .permissions import IsTeacherOrReadOnly
from .serializers import CourseAdditionalStudentsSerializer, CourseSerializer


class CourseListView(mixins.ListModelMixin, generics.GenericAPIView):
    queryset = models.Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        qs = models.Course.objects.all()
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(pk=user.pk)
            qs = qs.filter(teachers__in=[teacher.pk])
        if user.is_student:
            student = users_models.Student.objects.get(pk=user.pk)
            qs = qs.filter(grade__students__in=[student.pk])

        name = self.request.query_params.get('name')
        teacher = self.request.query_params.get('teacher')
        has_exam = int(self.request.query_params.get('exam', 0))
        language = self.request.query_params.get('language')
        semester = int(self.request.query_params.get('semester', 0))

        if name:
            qs = qs.filter(name__icontains=name)
        if teacher:
            qs = qs.filter(teachers__last_name__icontains=teacher)
        if has_exam and has_exam > 0:
            if has_exam == 1:
                qs = qs.filter(has_exam=True)
            if has_exam == 2:
                qs = qs.filter(has_exam=False)
        if language:
            qs = qs.filter(language=language.upper())
        if semester and semester > 0:
            qs = qs.filter(semester=semester)
        return qs


class CourseViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = models.Course.objects.all()
    serializer_class = CourseAdditionalStudentsSerializer
    permission_classes = [IsTeacherOrReadOnly, IsAuthenticated]
    lookup_field = "slug"

    def get_queryset(self):
        user = self.request.user
        teacher = users_models.Teacher.objects.get(pk=user.pk)
        return teacher.courses_teaching.all()


@api_view(['POST'])
def additional_course_student(request, the_slug):
    if not request.user.is_authenticated or request.user.role != 'teacher':
        return Response(status=401)
    if request.method == 'POST':
        email = request.data.get('email')
        course = models.Course.objects.get(slug=the_slug)
        if email and course:
            try:
                student = users_models.Student.objects.get(email=email)
                if student in course.grade.students.all() or student in course.additional_students.all():
                    return Response(status=200, data={'message': 'Ten użytkownik jest już dodany.'})
                if student:
                    course.additional_students.add(student)
            except Exception:
                return Response(status=404)
            return Response(status=200, data={'message': 'Pomyślnie dodano uzytkownika do kursu.'})
        return Response(status=400)
    return Response(status=401)
