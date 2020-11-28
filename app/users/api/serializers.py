from rest_framework import serializers

from users import models


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Student
        fields = ('first_name', 'pk', 'last_name', 'email', 'is_online',)


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Teacher
        fields = ('first_name', 'pk', 'last_name', 'email', 'is_online',)
