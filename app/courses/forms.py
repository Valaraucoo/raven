from django import forms

from courses import models

tailwind_form = 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4' \
                 ' mb-3 leading-tight focus:outline-none focus:bg-white focus:border-gray-500'


class LectureCreateForm(forms.Form):
    title = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': tailwind_form,
        'placeholder': 'Tytuł',
    }))
    date = forms.DateField(widget=forms.DateInput(attrs={
        'class': tailwind_form,
        'placeholder': '01.01.2021'
    }))
    time = forms.TimeField(widget=forms.TimeInput(attrs={
        'class': tailwind_form,
        'placeholder': '12:30'
    }))
    duration = forms.IntegerField(widget=forms.NumberInput(attrs={
        'class': tailwind_form,
        'placeholder': '90',
        'min': '1'
    }))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': tailwind_form,
        'cols': 30,
        'rows': 5
    }))
    show = forms.BooleanField(required=False)
    meeting = forms.BooleanField(initial=True, required=False)


class LaboratoryCreateForm(LectureCreateForm):
    group = forms.ModelChoiceField(queryset=models.CourseGroup.objects.all(),
                                   widget=forms.RadioSelect(attrs={'class': 'text-sm text-gray-700'}))


class CourseFileForm(forms.Form):
    filename = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': tailwind_form,
        'placeholder': 'Nazwa pliku',
    }))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': tailwind_form,
        'cols': 30,
        'rows': 5
    }))
    file = forms.FileField(required=True, widget=forms.FileInput(attrs={
        'class': tailwind_form
    }))


class CourseGroupModelForm(forms.ModelForm):
    class Meta:
        model = models.CourseGroup
        fields = ('name', 'students',)
        widgets = {
            'name': forms.TextInput(attrs={'class': tailwind_form}),
            'students': forms.CheckboxSelectMultiple(attrs={'class': 'text-sm text-gray-700'})
        }


class CourseNoticeModelForm(forms.ModelForm):
    class Meta:
        model = models.CourseNotice
        fields = ('title', 'content',)
        widgets = {
            'title': forms.TextInput(attrs={'class': tailwind_form}),
            'content': forms.Textarea(attrs={
                'class': tailwind_form,
                'cols': 30,
                'rows': 5
            })
        }


class CourseMarkModelForm(forms.ModelForm):
    class Meta:
        model = models.CourseMark
        fields = ('mark', 'description')
        widgets = {
            'mark': forms.NumberInput(attrs={'class': tailwind_form}),
            'description': forms.Textarea(attrs={
                'class': tailwind_form,
                'cols': 30,
                'rows': 5,
                'placeholder': 'Opis'
            }),
        }


class CourseSetFinalMarkModelForm(forms.ModelForm):
    class Meta:
        model = models.FinalCourseMark
        fields = ('mark', 'description')
        widgets = {
            'mark': forms.NumberInput(attrs={'class': tailwind_form}),
            'description': forms.Textarea(attrs={
                'class': tailwind_form,
                'cols': 30,
                'rows': 5,
                'placeholder': 'Opis'
            }),
        }


class AssignmentCreateModelForm(forms.ModelForm):
    class Meta:
        model = models.Assignment
        fields = ('deadline', 'title', 'content')
        widgets = {
            'deadline': forms.DateTimeInput(attrs={
                'class': tailwind_form,
                'placeholder': '01.01.2021'
            }),
            'title': forms.TextInput(attrs={'class': tailwind_form, 'placeholder': 'Tytul'}),
            'content': forms.Textarea(attrs={
                'class': tailwind_form,
                'cols': 30,
                'rows': 5
            })
        }
