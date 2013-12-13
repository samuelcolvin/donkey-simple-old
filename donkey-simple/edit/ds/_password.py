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

UNUSABLE_PASSWORD_PREFIX = '!'
UNUSABLE_PASSWORD_SUFFIX_LENGTH = 40

import random
try:
    random = random.SystemRandom()
    using_sysrandom = True
except NotImplementedError:
    print 'A secure pseudo-random number generator is not available on your system. Falling back to Mersenne Twister.'
    using_sysrandom = False

class Password(object):
    """
    From django.contrib.auth.hashers and django.utils.crypto
    """
    algorithm = "pbkdf2_sha256"
    iterations = 12000
    digest = hashlib.sha256

    def make_password(self, password):
        if password is None:
            return UNUSABLE_PASSWORD_PREFIX + _get_random_string(UNUSABLE_PASSWORD_SUFFIX_LENGTH)
        salt = _get_random_string()
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


def _get_random_string(length=12,
                      allowed_chars='abcdefghijklmnopqrstuvwxyz'
                                    'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    """
    based on django version but editted to avoid need for secret key
    Returns a securely generated random string.
    
    The default length of 12 with the a-z, A-Z, 0-9 character set returns
    a 71-bit value. log_2((26+26+10)^12) =~ 71 bits
    """
    if not using_sysrandom:
        # This is ugly, and a hack, but it makes things better than
        # the alternative of predictability. This re-seeds the PRNG
        # using a value that is hard for an attacker to predict, every
        # time a random string is required. This may change the
        # properties of the chosen random sequence slightly, but this
        # is better than absolute predictability.
        random.seed(
            hashlib.sha256(
                ("%s%s" % (
                    random.getstate(), time.time())).encode('utf-8')
            ).digest())
    return ''.join(random.choice(allowed_chars) for i in range(length))

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

