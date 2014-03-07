import os
import DonkeySimple.DS as ds
import HTMLParser

class UniversalProcessor(object):
    def process(self, fields):
        if 'action' in fields:
            for name in fields:
                print '%s:' % name, 
                if hasattr(fields[name], 'value'):
                    if 'password' in name:
                        print '*'*len(fields[name].value)
                    else:
                        print fields[name].value
                else:
                    print fields[name]
            action_func = fields['action'].value.replace('-', '_')
            if hasattr(self, action_func):
                self.fields = fields
                getattr(self, action_func)()
            else:
                raise Exception('ProcessForm has no function called %s' % action_func)
            
    def _password_reset_email(self, username):
        auth = ds.Auth()
        if username not in auth.users:
            return False
        user = auth.pop_user(username)
        pw = auth.new_random_password()
        email = user['email']
        url = os.environ['HTTP_REFERER']
        e_index = url.index('/edit/') + 5
        url = url[:e_index] + '/'
        if '@' in email:
            success, msg = ds.password_email(user['email'], url, username, pw)
            if success:
                auth.add_user(username, user, pw)
                self._add_msg('Password email sent', 'success')
                return True
            else:
                self._add_msg('Error sending email, not changing password', 'errors')
                self._add_msg(msg, 'errors')
        return False

class ProcessForm(UniversalProcessor):
    created_item = None
    def __init__(self, add_msg, fields, isadmin, username):
        self._add_msg = add_msg
        self.isadmin = isadmin
        self.username = username
        self.regen_users = False
        self.process(fields)
    
    def generate_site(self):
        ds.SiteGenerator(self._add_msg).generate_entire_site()
        self._add_msg('Site generated successfully', 'success')
        
    def edit_page(self):
        page_con = ds.con.Pages()
        if 'page-name' not in self.fields:
            self._add_msg('page name may not be blank', 'errors')
            return
        page_name = self.fields['page-name'].value
        t_con = ds.con.Templates()
        template = t_con.get_cfile_fid(self.fields['page-template-id'].value)
        page_con.create_cfile(template.repo, page_name, template.filename)
        context = dict([(name, self.fields[name].value) for name in self.fields])
        ftypes = dict([(name.replace('contype-', ''), self.fields[name].value) for name in self.fields if name.startswith('contype-')])
        page_con.update_context(context, ftypes)
        page = page_con.generate_page()
        self.created_item = page.id
        self._add_msg('"%s" successfully saved' % page.filename, 'success')
        
    def delete_page(self):
        page = ds.con.Pages()
        t_con = ds.con.Templates()
        template = t_con.get_cfile_fid(self.fields['page-template-id'].value)
        self._delete_file(page, None, 'page-name', repo = template.repo)
        
    def edit_template(self):
        t = ds.con.Templates()
        text = self._unescape_file_text()
        filename = self.fields['file-name'].value
        repo = self.fields['repo'].value
        fname = t.write_file(text, repo, filename)
        self._add_msg('"%s" successfully saved' % fname, 'success')
        
    def delete_template(self):
        t = ds.con.Templates()
        self._delete_file(t, 'repo', 'file-name')
        
    def upload_template(self):
        self._process_files('files', ds.con.Templates())
        
    def edit_static(self):
        static = ds.con.Statics()
        repo = self.fields['repo'].value
        if self.fields['file-type'].value == 'Text':
            text = self._unescape_file_text()
            name = self.fields['file-name'].value
            cfile = static.write_file(text, repo, name)
        else:
            src_id = self.fields['previous-file-id'].value
            src_cfile = static.cfiles[src_id]
            dst_name = self.fields['file-name'].value
            dst_cfile = static.create_cfile(repo, dst_name)
            if src_id == dst_cfile.id:
                return
            cfile = static.copy_file(src_cfile, dst_cfile)
        self._add_msg('"%s" successfully saved' % cfile.filename, 'success')
            
    def delete_static(self):
        static = ds.con.Statics()
        self._delete_file(static, 'repo', 'file-name')
        
    def edit_user(self):
        if 'previous-username' in self.fields:
            prev_username = self.fields['previous-username'].value
            if not self.isadmin and prev_username != self.username:
                return self._add_msg('Permission Denied', 'errors')
        elif not self.isadmin:
            return self._add_msg('Permission Denied', 'errors')
        username = self.fields['username'].value
        formuser = {'email': self.fields['email'].value}
        formuser['admin'] = self.isadmin and 'admin' in self.fields and self.fields['admin'].value == 'on'
        auth = ds.Auth()
        msg_type = 'success'
        if 'previous-username' not in self.fields:
            if username in auth.users:
                self._add_msg('user "%s" already exists, not creating user' % username, 'errors')
                return
            action_type = 'created'
            newuser = formuser
        else:
            olduser = auth.pop_user(prev_username)
            newuser = dict(olduser)
            newuser.update(formuser)
            if newuser == olduser and prev_username == username:
                action_type = 'not changed'
                msg_type = 'info'
            else:
                action_type = ''
                if newuser != olduser:
                    action_type = 'editted'
                if prev_username != username:
                    action_type += ' username changed'
        auth.add_user(username, newuser)
        self.created_item = username
        self.regen_users = True
        self._add_msg('"%s" %s' % (username, action_type), msg_type)
    
    def delete_user(self):
        if not self.isadmin:
            return self._add_msg('Permission Denied', 'errors')
        username = self.fields['previous-username'].value
        auth = ds.Auth()
        auth.pop_user(username, save=True)
        self.regen_users = True
        self._add_msg('deleted "%s"' % username, 'success')
    
    def email_pword_user(self):
        username = self.fields['previous-username'].value
        if not self.isadmin and username != self.username:
            return self._add_msg('Permission Denied', 'errors')
        else:
            self._password_reset_email(username)

    def change_user_password(self):
        username = self.fields['username'].value
        if not self.isadmin and username != self.username:
            return self._add_msg('Permission Denied', 'errors')
        pw1 = self.fields['password1'].value
        pw2 = self.fields['password2'].value
        if pw1 != pw2:
            self._add_msg('Passwords do not match', 'errors')
            return
        pw = pw1
        if len(pw) < ds.MIN_PASSWORD_LENGTH:
            self._add_msg('Password must be at least %d characters in length' % ds.MIN_PASSWORD_LENGTH, 'errors')
            return
        auth = ds.Auth()
        user = auth.pop_user(username)
        auth.add_user(username, user, pw)
        self._add_msg('"%s" password updated' % username, 'success')
        
    def upload_static(self):
        self._process_files('files', ds.con.Statics())
    
    def _process_files(self, field_name, controller):
        if isinstance(self.fields[field_name], list):
            for f in self.fields[field_name]:
                self._process_file(f, controller)
        else:
            self._process_file(self.fields[field_name], controller)
    
    def _process_file(self, file_field, controller):
        if file_field.file:
            name = file_field.filename
            path = controller.new_file_path(name)
            fout = file(path, 'wb')
            while 1:
                chunk = file_field.file.read(100000)
                if not chunk: break
                fout.write(chunk)
            fout.close()
            controller.set_mod(path)
            self._add_msg('File successfully uploaded to "%s"' % path, 'success')
        else:
            self._add_msg('Error getting file from upload', 'error')
        
    def _delete_file(self, controller, repo_field_name, file_field_name, repo = None):
        if repo is None:
            repo = self.fields[repo_field_name].value
        filename = self.fields[file_field_name].value
        print repo, filename
        fname = controller.delete_file(repo = repo, filename = filename)
        self._add_msg('"%s" successfully deleted' % fname.display, 'success')
    
    def _unescape_file_text(self):
        return HTMLParser.HTMLParser().unescape(self.fields['file-text'].value)
    
class AnonFormProcessor(UniversalProcessor):
    def __init__(self, add_msg, fields):
        self._add_msg = add_msg
        self.process(fields)
 
    def reset_password(self):
        username = self.fields['username'].value
        success = self._password_reset_email(username)