import jinja2, json
from jinja2 import meta as jinja2_meta
import re, os
from _common import *

def _get_template_path(repo_template):
    try:
        path_parts = tuple(repo_template.split('/'))
        template = path_parts[-1]
        repo = path_parts[0]
        if repo == REPOS_DIR: repo = path_parts[1]
    except Exception, e:
        raise jinja2.TemplateNotFound('Problem getting template path, got "%s", error: %s' % (repo_template, str(e)))
    return os.path.join(repo, TEMPLATES_DIR, template)

class DSFileSystemLoader(jinja2.FileSystemLoader):
    def __init__(self, **kwargs):
        super(DSFileSystemLoader, self).__init__(REPOS_DIR, **kwargs)
    
    def get_source(self, environment, repo_template):
        template_path = _get_template_path(repo_template)
        return super(DSFileSystemLoader, self).get_source(environment, template_path)
    
def get_env(global_context = None):
    env = jinja2.Environment(loader= DSFileSystemLoader())
    if global_context:
        env.globals = global_context
    return env

class RenderTemplate(object):
    def __init__(self, name, repo, env=None):
        if env:
            self._env = env
        else:
            self._env = get_env()
        self._template = self._env.get_template('/'.join([repo, name]))
    
    def render(self, context):
        return self._template.render(**context)
    
    def get_empty_context(self):
        context = self.get_context_types()
        context = {name: t for name, t in context.items() if t != 'list'}
        for var, t in context.items():
            context[var] = {'value': '', 'type': t}
            if t == 'list':
                context[var]['type'] = []
        return context
    
    def get_context_types(self):
        codes, t_vars = self._code_vars()
        context = {}
        for var in t_vars:
            context[var] = self._get_var(codes, var)
        return context
    
    def _code_vars(self):
        self._codes = []
        self._t_vars = []
        self._process_file(self._template.name)
        return self._codes, self._t_vars
    
    def _process_file(self, repo_template):
        template_path = os.path.join(REPOS_DIR, _get_template_path(repo_template))
        code = open(template_path, 'r').read()
        ast = self._env.parse(code)
        t_vars = jinja2_meta.find_undeclared_variables(ast)
        finds = re.findall('{%.*?extends(.*?)%}', code)
        self._codes.append(code)
        self._t_vars.extend(t_vars)
        for f in finds:
            self._process_file(f.strip(' "'))
    
    def _get_var(self, codes, var):
        for code in codes:
            finds = re.findall('{{.*?%s.*?}}' % var, code)
            success, t = self._process_finding(finds, var)
            if not success:
                finds = re.findall('{%%.*?%s.*?%%}' % var, code)
                success, t = self._process_finding(finds, var)
            if success:
                return t
        return 'unknown'
        
    def _process_finding(self, finds, var):
        t = 'unknown'
        success = False
        if len(finds) > 0:
            success = True
            finding = finds[0]
            t = 'string'
            if 'safe' in finding:
                t = 'markdown'
            if 'for' in finding:
                t= 'list'
        return success, t
    