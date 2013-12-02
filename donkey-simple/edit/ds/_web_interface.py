import jinja2

EDITOR_TEMPLATE_DIR = 'templates_editor'

class WebInterface(object):
    def __init__(self):
        self._env = jinja2.Environment(loader=jinja2.FileSystemLoader(EDITOR_TEMPLATE_DIR))
    
    def base_page(self):
        self._template = self._env.get_template('base.html')
        return self._template.render()
    