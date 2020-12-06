import datetime

import factory
import factory.fuzzy as fuzzy

from courses import models
from courses.models import LANGUAGE_CHOICES, PROFILE_CHOICES
from tests.users import factories as users_factories

PROFILE_CHOICES = [x[0] for x in PROFILE_CHOICES]
LANGUAGE_CHOICES = [x[0] for x in LANGUAGE_CHOICES]


class GradeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Grade

    name = factory.Sequence(lambda n: "Grade %03d" % n)
    start_year = factory.Faker('date_object')
    supervisor = factory.SubFactory(users_factories.StudentFactory)
    profile = fuzzy.FuzzyChoice(PROFILE_CHOICES)

    @factory.post_generation
    def students(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for student in extracted:
                self.students.add(student)
        else:
            for _ in range(10):
                self.students.add(users_factories.StudentFactory())


class CourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Course

    name = factory.Sequence(lambda n: "Course %02d" % n)
    description = factory.Faker('text')
    head_teacher = factory.SubFactory(users_factories.TeacherFactory)
    grade = factory.SubFactory(GradeFactory)
    code_meu = '123'
    has_exam = False
    semester = fuzzy.FuzzyChoice([i for i in range(1, 8)])
    language = fuzzy.FuzzyChoice(LANGUAGE_CHOICES)
    lecture_hours = fuzzy.FuzzyChoice([i for i in range(1, 40)])
    labs_hours = fuzzy.FuzzyChoice([i for i in range(1, 40)])

    @factory.post_generation
    def teachers(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for teacher in extracted:
                self.teachers.add(teacher)
        else:
            for _ in range(3):
                self.teachers.add(users_factories.TeacherFactory())


class LectureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Lecture
    course = factory.SubFactory(CourseFactory)
    title = fuzzy.FuzzyText(length=16)
    description = factory.Faker('text')
    date = fuzzy.FuzzyDate(
        start_date=datetime.date.today() - datetime.timedelta(days=100),
        end_date=datetime.date.today() + datetime.timedelta(days=100),
    )


class CourseGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.CourseGroup
    course = factory.SubFactory(CourseFactory)
    name = fuzzy.FuzzyText(length=16)
