import jinja2
import _site_generator

EDITOR_TEMPLATE_DIR = 'templates_editor'

class WebInterface(object):
    def __init__(self):
        self._env = jinja2.Environment(loader=jinja2.FileSystemLoader(EDITOR_TEMPLATE_DIR))
    
    def index(self):
        self._template = self._env.get_template('edit_index.html')
        context = {'title': 'Editor'}
        sg = _site_generator.SiteGenerator()
        context['pages'] = []
        for _, page in sg.get_pages():
            context['pages'].append({'link': '#', 'name': page['name']})
        
        return self._template.render(**context)
    