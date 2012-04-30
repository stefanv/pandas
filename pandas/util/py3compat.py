import sys

PY3 = (sys.version_info[0] >= 3)

if PY3:
    def isidentifier(s):
        return s.isidentifier()

    def str_to_bytes(s, encoding='ascii'):
        return s.encode(encoding)

else:
    # Python 2
    import re
    _name_re = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*$")
    def isidentifier(s, dotted=False):
        return bool(_name_re.match(s))

    def str_to_bytes(s, encoding='ascii'):
        return s

try:
    from cStringIO import StringIO
except:
    from io import StringIO # no cStringIO in py3

try:
    from io import BytesIO
except:
    from cStringIO import StringIO as BytesIO # no BytesIO prior to py3

try:
    xrange = xrange
except NameError: # no xrange in py3
    xrange = range

