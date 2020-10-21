import typing

from django.db import models
from django.views import generic


class DetailBaseView(generic.DetailView):
    title: str
    description: str = None
    template_name: str = None

    def get_context_data(self, **kwargs) -> typing.Dict:
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['description'] = self.description
        context['user'] = self.request.user
        context.update(self.get_context_obj())
        return context

    def get_context_obj(self) -> typing.Dict[str, models.Model]:
        return {'obj': self.object}
