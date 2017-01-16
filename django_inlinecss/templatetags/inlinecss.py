import urllib2
from django import template

from django.utils.encoding import smart_text
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from django_inlinecss import conf

register = template.Library()


class InlineCssNode(template.Node):
    def __init__(self, nodelist, filter_expressions):
        self.nodelist = nodelist
        self.filter_expressions = filter_expressions

    def render(self, context):
        rendered_contents = self.nodelist.render(context)
        css = ''
        for expression in self.filter_expressions:
            path = expression.resolve(context, True)
            if path is not None:
                path = smart_text(path)

            # We need to decide how to expand the path
            # depending on the storage class and
            # how to open the expanded path
            expand_path = staticfiles_storage.path
            open_path = open
            if not issubclass(staticfiles_storage.__class__, FileSystemStorage):
                expand_path = staticfiles_storage.url
                open_path = urllib2.urlopen

            expanded_path = expand_path(path)
            with open_path(expanded_path) as css_file:
                css = ''.join((css, css_file.read()))


        engine = conf.get_engine()(html=rendered_contents, css=css)
        return engine.render()


@register.tag
def inlinecss(parser, token):
    nodelist = parser.parse(('endinlinecss',))

    # prevent second parsing of endinlinecss
    parser.delete_first_token()

    args = token.split_contents()[1:]

    return InlineCssNode(
        nodelist,
        [parser.compile_filter(arg) for arg in args])
