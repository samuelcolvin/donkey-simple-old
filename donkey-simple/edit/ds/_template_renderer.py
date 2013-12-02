import jinja2, json
from jinja2 import meta as jinja2_meta
import re, os
from _common import *

class RenderTemplate(object):
    def __init__(self, name):
        self._env = jinja2.Environment(loader= jinja2.FileSystemLoader(TEMPLATES_DIR))
        self._template = self._env.get_template(name)
    
    def render(self, context):
        return self._template.render(**context)
    
    def get_empty_context(self):
        context = self.get_context_types()
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
        self._process_file(self._template.filename)
        return self._codes, self._t_vars
    
    def _process_file(self, path):
        print 'processing', path
        code = open(path, 'r').read()
        ast = self._env.parse(code)
        t_vars = jinja2_meta.find_undeclared_variables(ast)
        finds = re.findall('{%.*?extends(.*?)%}', code)
        self._codes.append(code)
        self._t_vars.extend(t_vars)
        if len(finds) > 0:
            for f in finds:
                p = '%s/%s' % (TEMPLATES_DIR, f.strip('" '))
                self._process_file(p)
    
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
                t = 'html'
            if 'for' in finding:
                t= 'list'
        return success, t
    