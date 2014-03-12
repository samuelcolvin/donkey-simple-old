"""
flagrantly ripped off from Django 1.7.0.alfa.0
From django.contrib.auth.hashers and django.utils.crypto with references to six removed
"""

import hashlib
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
    
def get_random_string(length=12,
                      allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    """
    based on django version but edited to avoid need for secret key
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