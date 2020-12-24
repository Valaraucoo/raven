from rest_framework import serializers

from courses import models
from users.api.serializers import StudentSerializer, TeacherSerializer


class CourseSerializer(serializers.ModelSerializer):
    teachers = TeacherSerializer(many=True)
    head_teacher = TeacherSerializer()

    class Meta:
        model = models.Course
        fields = ('name', 'teachers', 'head_teacher', 'has_exam', 'ects', 'slug',
                  'language', 'semester', 'is_actual')
        lookup_field = 'slug'


class CourseAdditionalStudentsSerializer(serializers.ModelSerializer):
    additional_students = StudentSerializer(many=True)

    class Meta:
        model = models.Course
        fields = ('name', 'slug', 'additional_students',)
        lookup_field = 'slug'
