"""
flagrantly ripped off from Django 1.7.0.alfa.0
From django.contrib.auth.hashers and django.utils.crypto with references to six removed
"""

import hashlib
import base64
import hmac
import struct
import binascii
from collections import OrderedDict
import time
import json, datetime
from DonkeySimple.DS import *
from DonkeySimple.DS.random_string import get_random_string
settings = get_settings()

UNUSABLE_PASSWORD_PREFIX = '!'
UNUSABLE_PASSWORD_SUFFIX_LENGTH = 40

import random
try:
    random = random.SystemRandom()
    using_sysrandom = True
except NotImplementedError:
    print 'A secure pseudo-random number generator is not available on your system. Falling back to Mersenne Twister.'
    using_sysrandom = False

class Auth(object):
    dt_format = '%a, %d-%b-%Y %H:%M:%S UTC'
    cookie = None
    msg = None
    username = None
    user = None
    
    def __init__(self):
        self._load_success, self.users = self._get_users()
    
    def login(self, username, password):
        if not self._load_success:
            self.msg = 'Error Loading Users file'
            return False
        if username not in self.users:
            self.msg = 'Username not found'
            return False
        self.user = self.users[username]
        pw = Password()
        correct_pw = pw.check_password(password, self.user['hash'])
        if not correct_pw:
            self.msg = 'Incorrect Password'
            return False
        self.cookie = self._generate_cookie()
        self.username = username
        self._update_user(self.username, self.cookie)
        self.msg = 'Logged in successfully'
        return True
    
    def logout(self, username):
        self.username = username
        self.cookie = self._generate_cookie()
        self._update_user(self.username, self.cookie)
    
    def check_cookie(self, cookies):
        if self._get_user(cookies):
            self.cookie = self._generate_cookie(self.user['cookie'])
            self._update_user(self.username, self.cookie)
            return True
        return False
    
    def get_sorted_users(self):
        return sorted(self.users.keys())
    
    def new_random_password(self, length=10):
        return get_random_string(length=length)
    
    def pop_user(self, username, save=False):
        user = self.users.pop(username)
        if save:
            self._save_users()
        return user
            
    def add_user(self, username, user, password=None):
        assert username not in self.users, 'User %s already exists!' % username
        if 'hash' not in user or password is not None:
            pw = Password()
            user['hash'] = pw.make_hash(password)
            user['cookie'] = self._generate_cookie()['value']
        if 'cookie' not in user:
            user['cookie'] = self._generate_cookie()['value']
        if 'admin' not in user:
            user['admin'] = False
        if 'created' not in user:
            user['created'] = datetime.datetime.utcnow().strftime(self.dt_format)
        self.users[username] = user
        self._save_users()
    
    def _get_user(self, cookies):
        if settings.COOKIE_NAME in cookies:
            cookie_value = cookies[settings.COOKIE_NAME].value
            for username, user in self.users.items():
                if user['cookie'] == cookie_value:
                    self.username = username
                    self.user = user
                    return True
        return False
    
    def _generate_cookie(self, value=None):
        if value is None:
            value = get_random_string(length=15)
        cook = {'version': 1}
        expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=settings.PASSWORD_EXPIRE_HOURS)
        cook['expires'] = expiration.strftime(self.dt_format)
        if hasattr(settings, 'COOKIE_DOMAIN'):
            cook['domain'] = settings.COOKIE_DOMAIN
        if hasattr(settings, 'COOKIE_PATH'):
            cook['path'] = settings.COOKIE_PATH
        return {'name': settings.COOKIE_NAME, 'value': value, 'extra_values': cook}
            
    def _update_user(self, username, cookie):
        self.users[username]['cookie'] = cookie['value']
        self.users[username]['last_seen'] = datetime.datetime.utcnow().strftime(self.dt_format)
        self._save_users()
            
    def _save_users(self):
        try:
            with open(USERS_FILE, 'w') as handle:
                json.dump(self.users, handle, sort_keys=True, indent=4, separators=(',', ': '))
        except Exception, e:
            print 'ERROR loading users file:', str(e)
            return False
        else:
            return True
    
    def _get_users(self):
        try:
            with open(USERS_FILE, 'r') as handle:
                users = json.load(handle)
        except Exception, e:
            print 'ERROR loading users file:', str(e)
            return False, {}
        else:
            return True, users

class Password(object):
    """
    From django.contrib.auth.hashers and django.utils.crypto
    """
    algorithm = "pbkdf2_sha256"
    iterations = 12000
    digest = hashlib.sha256

    def make_hash(self, password):
        if password is None:
            return UNUSABLE_PASSWORD_PREFIX + get_random_string(UNUSABLE_PASSWORD_SUFFIX_LENGTH)
        salt = get_random_string()
        return self._encode(password, salt)
        return "%s$%d$%s$%s" % (self.algorithm, self.iterations, salt, hash)

    def check_password(self, password, encoded):
        if password is None or encoded is None or encoded.startswith(UNUSABLE_PASSWORD_PREFIX):
            return False
        algorithm, iterations, salt, hash = encoded.split('$', 3)
        assert algorithm == self.algorithm
        encoded_2 = self._encode(password, salt, int(iterations))
        return _constant_time_compare(encoded, encoded_2)

    def safe_summary(self, encoded):
        algorithm, iterations, salt, hash = encoded.split('$', 3)
        assert algorithm == self.algorithm
        return OrderedDict([
            (_('algorithm'), algorithm),
            (_('iterations'), iterations),
            (_('salt'), _mask_hash(salt)),
            (_('hash'), _mask_hash(hash)),
        ])
        
    def _encode(self, password, salt, iterations=None):
        assert password is not None
        assert salt and '$' not in salt
        if not iterations:
            iterations = self.iterations
        hash = _pbkdf2(password, salt, iterations, digest=self.digest)
        hash = base64.b64encode(hash).decode('ascii').strip()
        return "%s$%d$%s$%s" % (self.algorithm, iterations, salt, hash)

def _constant_time_compare(val1, val2):
    """
    Returns True if the two strings are equal, False otherwise.

    The time taken is independent of the number of characters that match.

    For the sake of simplicity, this function executes in constant time only
    when the two strings have the same length. It short-circuits when they
    have different lengths. Since Django only uses it to compare hashes of
    known expected length, this is acceptable.
    """
    if len(val1) != len(val2):
        return False
    result = 0
    for x, y in zip(val1, val2):
        result |= ord(x) ^ ord(y)
    return result == 0

def _mask_hash(hash, show=6, char="*"):
    """
    Returns the given hash, with only the first ``show`` number shown. The
    rest are masked with ``char`` for security reasons.
    """
    masked = hash[:show]
    masked += char * len(hash[show:])
    return masked

def _pbkdf2(password, salt, iterations, dklen=0, digest=None):
    """
    Implements PBKDF2 as defined in RFC 2898, section 5.2

    HMAC+SHA256 is used as the default pseudo random function.

    As of 2011, 10,000 iterations was the recommended default which
    took 100ms on a 2.2Ghz Core 2 Duo. This is probably the bare
    minimum for security given 1000 iterations was recommended in
    2001. This code is very well optimized for CPython and is only
    four times slower than openssl's implementation. Look in
    django.contrib.auth.hashers for the present default.
    """
    assert iterations > 0
    if not digest:
        digest = hashlib.sha256
    password = _force_bytes(password)
    salt = _force_bytes(salt)
    hlen = digest().digest_size
    if not dklen:
        dklen = hlen
    if dklen > (2 ** 32 - 1) * hlen:
        raise OverflowError('dklen too big')
    l = -(-dklen // hlen)
    r = dklen - (l - 1) * hlen

    hex_format_string = "%%0%ix" % (hlen * 2)

    inner, outer = digest(), digest()
    if len(password) > inner.block_size:
        password = digest(password).digest()
    password += b'\x00' * (inner.block_size - len(password))
    inner.update(password.translate(hmac.trans_36))
    outer.update(password.translate(hmac.trans_5C))

    def F(i):
        u = salt + struct.pack(b'>I', i)
        result = 0
        for j in xrange(int(iterations)):
            dig1, dig2 = inner.copy(), outer.copy()
            dig1.update(u)
            dig2.update(dig1.digest())
            u = dig2.digest()
            result ^= _bin_to_long(u)
        return _long_to_bin(result, hex_format_string)

    T = [F(x) for x in range(1, l)]
    return b''.join(T) + F(l)[:r]

def _bin_to_long(x):
    """
    Convert a binary string into a long integer
    This is a clever optimization for fast xor vector math
    """
    return int(binascii.hexlify(x), 16)

def _long_to_bin(x, hex_format_string):
    """
    Convert a long integer into a binary string.
    hex_format_string is like "%020x" for padding 10 characters.
    """
    return binascii.unhexlify((hex_format_string % x).encode('ascii'))

def _force_bytes(s):
    """
    modified from django version
    """
    if isinstance(s, bytes):
        return s
    if isinstance(s, buffer):
        return bytes(s)
    if not isinstance(s, basestring):
        return bytes(s)
    else:
        return s.encode('utf-8', 'strict')

