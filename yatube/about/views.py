from django.views.generic.base import TemplateView


class AboutAuthor(TemplateView):
    template_name: str = 'about/about_author.html'


class AboutTech(TemplateView):
    template_name: str = 'about/about_tech.html'
