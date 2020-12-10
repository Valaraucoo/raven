from django.contrib import messages
from django.views import generic
from django.shortcuts import render

from . import tasks
from . import forms
from . import models


class TicketCreateView(generic.View):
    template_name = "support/ticket-create.html"
    form_class = forms.TicketCreateForm

    def get_context_data(self, **kwargs):
        return {
            'form': self.get_form_class(**kwargs)
        }

    def get_form_class(self, **kwargs):
        return self.form_class(**kwargs)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(data=request.POST)

        form = context['form']
        category = request.POST.get('category')

        if form.is_valid() and category:
            if category == '1':
                category = models.SupportCategories.AUTHENTICATION
            elif category == '2':
                category = models.SupportCategories.COMMUNICATION
            elif category == '3':
                category = models.SupportCategories.FORGET_PASSWORD
            else:
                category = models.SupportCategories.OTHER
            email = request.user.email if request.user.is_authenticated else form.cleaned_data.get('email')
            fullname = f"{request.user.first_name} {request.user.last_name}" if request.user.is_authenticated else \
                form.data.get('fullname')
            description = form.data.get('description')
            models.SupportTicket.objects.create(
                email=email, issuer_fullname=fullname, description=description, category=category,
                status=models.SupportStatus.PROCESSING
            )
            tasks.send_support_notification_email(email, fullname, bcc=[], email_to=[email])
            messages.info(request, 'Przyjęto zgłoszenie, dziękujemy!')
        else:
            messages.error(request, 'Coś poszło nie tak, spróbuj ponownie!')
        return render(request, self.template_name, context)
