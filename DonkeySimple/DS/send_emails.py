import smtplib
from email.mime.text import MIMEText
import DonkeySimple.DS as ds
import settings
    
def send_email(send_to, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    
    msg['From'] = settings.EMAIL_FROM
    msg['To'] = send_to
    
    
    try:
        if hasattr(settings, 'EMAIL_PORT'):
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        else:
            server = smtplib.SMTP(settings.EMAIL_HOST)
        if hasattr(settings, 'EMAIL_USE_TLS') and settings.EMAIL_USE_TLS:
            server.ehlo()
            server.starttls()
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.sendmail(settings.EMAIL_FROM, [send_to], msg.as_string())
        server.quit()
        server.close()
        return True, ''
    except Exception, e:
        print 'Error Sending email: %r' % e
        return False, str(e)

def password_email(send_to, url, username, password):
    body = """%s

Your password has been reset.
username: %s
password: %s 
To login go to %s.
You should then change your password.""" % (settings.SITE_NAME, username, password, url)
    subject = '%s password reset for %s' % (username, settings.SITE_NAME)
    return send_email(send_to, subject, body)