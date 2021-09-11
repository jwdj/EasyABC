#!/usr/bin/python

import re
import sys
PY3 = sys.version_info.major >= 3
try:
    from html import escape  # py3
except ImportError:
    from cgi import escape  # py2
import codecs
utf8_byte_order_mark = codecs.BOM_UTF8


unicode16_re = re.compile(r'\\u[0-9a-fA-F]{4}')
unicode32_re = re.compile(r'\\U[0-9a-fA-F]{8}')

unicode_char_to_abc = {
    u'\u00c0': u'\\`A', u'\u00e0': u'\\`a', u'\u00c8': u'\\`E', u'\u00e8': u'\\`e', u'\u00cc': u'\\`I', u'\u00ec': u'\\`i',
    u'\u00d2': u'\\`O', u'\u00f2': u'\\`o', u'\u00d9': u'\\`U', u'\u00f9': u'\\`u', u'\u00c1': u"\\'A", u'\u00e1': u"\\'a",
    u'\u00c9': u"\\'E", u'\u00e9': u"\\'e", u'\u00cd': u"\\'I", u'\u00ed': u"\\'i", u'\u00d3': u"\\'O", u'\u00f3': u"\\'o",
    u'\u00da': u"\\'U", u'\u00fa': u"\\'u", u'\u00dd': u"\\'Y", u'\u00fd': u"\\'y", u'\u00c2': u'\\^A', u'\u00e2': u'\\^a',
    u'\u00ca': u'\\^E', u'\u00ea': u'\\^e', u'\u00ce': u'\\^I', u'\u00ee': u'\\^i', u'\u00d4': u'\\^O', u'\u00f4': u'\\^o',
    u'\u00db': u'\\^U', u'\u00fb': u'\\^u', u'\u0176': u'\\^Y', u'\u0177': u'\\^y', u'\u00c3': u'\\~A', u'\u00e3': u'\\~a',
    u'\u00d1': u'\\~N', u'\u00f1': u'\\~n', u'\u00d5': u'\\~O', u'\u00f5': u'\\~o', u'\u00c4': u'\\"A', u'\u00e4': u'\\"a',
    u'\u00cb': u'\\"E', u'\u00eb': u'\\"e', u'\u00cf': u'\\"I', u'\u00ef': u'\\"i', u'\u00d6': u'\\"O', u'\u00f6': u'\\"o',
    u'\u00dc': u'\\"U', u'\u00fc': u'\\"u', u'\u0178': u'\\"Y', u'\u00ff': u'\\"y', u'\u00c7': u'\\cC', u'\u00e7': u'\\cc',
    u'\u00c5': u'\\AA', u'\u00e5': u'\\aa', u'\u00d8': u'\\/O', u'\u00f8': u'\\/o', u'\u0102': u'\\uA', u'\u0103': u'\\ua',
    u'\u0114': u'\\uE', u'\u0115': u'\\ue', u'\u0160': u'\\vS', u'\u0161': u'\\vs', u'\u017d': u'\\vZ', u'\u017e': u'\\vz',
    u'\u0150': u'\\HO', u'\u0151': u'\\Ho', u'\u0170': u'\\HU', u'\u0171': u'\\Hu', u'\u00c6': u'\\AE', u'\u00e6': u'\\ae',
    u'\u0152': u'\\OE', u'\u0153': u'\\oe', u'\u00df': u'\\ss', u'\u00d0': u'\\DH', u'\u00f0': u'\\dh', u'\u00de': u'\\TH',
    u'\u00fe': u'\\th' }

abc_to_unicode_char = dict((b, a) for (a, b) in unicode_char_to_abc.items())

abc_to_unicode_char_re = re.compile(u'|'.join(re.escape(c) for c in abc_to_unicode_char))


def ensure_unicode_py2(text):
    if not isinstance(text, unicode):
        return text.decode('utf-8')
    return text

def ensure_unicode_py3(text):
    if isinstance(text, bytes):
        return text.decode('utf-8')
    return text

if PY3:
    ensure_unicode = ensure_unicode_py3
else:
    ensure_unicode = ensure_unicode_py2

def unicode_escape_to_char_py2(value):
    return unicode(str(value), 'unicode-escape')

def unicode_escape_to_char_py3(value):
    return bytes(value, 'utf-8').decode('unicode-escape')

def abc_text_to_unicode_py2(text):
    result = ensure_unicode(text)
    if result:
        result = abc_to_unicode_char_re.sub(lambda m: abc_to_unicode_char[m.group(0)], result)
        result = unicode16_re.sub(lambda m: m.group(0).decode('unicode-escape'), result)
    return result

def abc_text_to_unicode_py3(text):
    result = ensure_unicode(text)
    if result:
        result = abc_to_unicode_char_re.sub(lambda m: abc_to_unicode_char[m.group(0)], result)
        result = unicode16_re.sub(lambda m: bytes(m.group(0), 'ascii').decode('unicode-escape'), result)
    return result

if PY3:
    unicode_escape_to_char = unicode_escape_to_char_py3
    abc_text_to_unicode = abc_text_to_unicode_py3
else:
    unicode_escape_to_char = unicode_escape_to_char_py2
    abc_text_to_unicode = abc_text_to_unicode_py2

def unicode_text_to_abc(text):
    result = ensure_unicode(text)
    result = u''.join(unicode_char_to_abc.get(c, c) for c in result)
    result = u''.join(r'\u{:04x}'.format(ord(c)) if ord(c) > 127 else c for c in result)
    return result

def unicode_text_to_html_abc(text):
    result = text
    if text:
        for ustr in unicode_char_to_abc:
            ch = unicode_escape_to_char(ustr)
            html = escape(ch)
            result = result.replace(ch, html)
            result = result.replace(ch, unicode_char_to_abc[ustr])
    return result




mapping = {'\\`A': u'\xc0',
'\\`E': u'\xc8',
'\\`I': u'\xcc',
'\\`O': u'\xd2',
'\\`U': u'\xd9',
'\\`a': u'\xe0',
'\\`e': u'\xe8',
'\\`i': u'\xec',
'\\`o': u'\xf2',
'\\`u': u'\xf9',
"\\'A": u'\xc1',
"\\'E": u'\xc9',
"\\'I": u'\xcd',
"\\'O": u'\xd3',
"\\'U": u'\xda',
"\\'Y": u'\xdd',
"\\'a": u'\xe1',
"\\'e": u'\xe9',
"\\'i": u'\xed',
"\\'o": u'\xf3',
"\\'u": u'\xfa',
"\\'y": u'\xfd',
"\\'S": u'\u015a',
"\\'Z": u'\u0179',
"\\'s": u'\u015b',
"\\'z": u'\u017a',
"\\'R": u'\u0154',
"\\'L": u'\u0139',
"\\'C": u'\u0106',
"\\'N": u'\u0143',
"\\'r": u'\u0155',
"\\'l": u'\u013a',
"\\'c": u'\u0107',
"\\'n": u'\u0144',
'\\^A': u'\xc2',
'\\^E': u'\xca',
'\\^I': u'\xce',
'\\^O': u'\xd4',
'\\^U': u'\xdb',
'\\^a': u'\xe2',
'\\^e': u'\xea',
'\\^i': u'\xee',
'\\^o': u'\xf4',
'\\^u': u'\xfb',
'\\^H': u'\u0124',
'\\^J': u'\u0134',
'\\^h': u'\u0125',
'\\^j': u'\u0135',
'\\^C': u'\u0108',
'\\^G': u'\u011c',
'\\^S': u'\u015c',
'\\^c': u'\u0109',
'\\^g': u'\u011d',
'\\^s': u'\u015d',
'\\,C': u'\xc7',
'\\,c': u'\xe7',
'\\,S': u'\u015e',
'\\,s': u'\u015f',
'\\,T': u'\u0162',
'\\,t': u'\u0163',
'\\,R': u'\u0156',
'\\,L': u'\u013b',
'\\,G': u'\u0122',
'\\,r': u'\u0157',
'\\,l': u'\u013c',
'\\,g': u'\u0123',
'\\,N': u'\u0145',
'\\,K': u'\u0136',
'\\,n': u'\u0146',
'\\,k': u'\u0137',
'\\"A': u'\xc4',
'\\"E': u'\xcb',
'\\"I': u'\xcf',
'\\"O': u'\xd6',
'\\"U': u'\xdc',
'\\"a': u'\xe4',
'\\"e': u'\xeb',
'\\"i': u'\xef',
'\\"o': u'\xf6',
'\\"u': u'\xfc',
'\\"y': u'\xff',
'\\~A': u'\xc3',
'\\~N': u'\xd1',
'\\~O': u'\xd5',
'\\~a': u'\xe3',
'\\~n': u'\xf1',
'\\~o': u'\xf5',
'\\~I': u'\u0128',
'\\~i': u'\u0129',
'\\~U': u'\u0168',
'\\~u': u'\u0169',
'\\oA': u'\xc5',
'\\oa': u'\xe5',
'\\oU': u'\u016e',
'\\ou': u'\u016f',
'\\=E': u'\u0112',
'\\=e': u'\u0113',
'\\=A': u'\u0100',
'\\=I': u'\u012a',
'\\=O': u'\u014c',
'\\=U': u'\u016a',
'\\=a': u'\u0101',
'\\=i': u'\u012b',
'\\=o': u'\u014d',
'\\=u': u'\u016b',
'\\=D': u'\u0110',
'\\=d': u'\u0111',
'\\=H': u'\u0126',
'\\=h': u'\u0127',
'\\=T': u'\u0166',
'\\=t': u'\u0167',
'\\/O': u'\xd8',
'\\/o': u'\xf8',
'\\/D': u'\u0110',
'\\/d': u'\u0111',
'\\/L': u'\u0141',
'\\/l': u'\u0142',
'"\\;A"': u'\u0104',
'"\\;a"': u'\u0105',
'"\\;E"': u'\u0118',
'"\\;e"': u'\u0119',
'"\\;I"': u'\u012e',
'"\\;U"': u'\u0172',
'"\\;i"': u'\u012f',
'"\\;u"': u'\u0173',
'\\vL': u'\u013d',
'\\vS': u'\u0160',
'\\vT': u'\u0164',
'\\vZ': u'\u017d',
'\\vl': u'\u013e',
'\\vs': u'\u0161',
'\\vt': u'\u0165',
'\\vz': u'\u017e',
'\\vC': u'\u010c',
'\\vE': u'\u011a',
'\\vD': u'\u010e',
'\\vN': u'\u0147',
'\\vR': u'\u0158',
'\\vc': u'\u010d',
'\\ve': u'\u011b',
'\\vd': u'\u010f',
'\\vn': u'\u0148',
'\\vr': u'\u0159',
'\\uA': u'\u0102',
'\\ua': u'\u0103',
'\\uG': u'\u011e',
'\\ug': u'\u011f',
'\\uU': u'\u016c',
'\\uu': u'\u016d',
'\\:O': u'\u0150',
'\\:U': u'\u0170',
'\\:o': u'\u0151',
'\\:u': u'\u0171',
'\\.Z': u'\u017b',
'\\.z': u'\u017c',
'\\.I': u'\u0130',
'\\.i': u'\u0131',
'\\.C': u'\u010a',
'\\.G': u'\u0120',
'\\.c': u'\u010b',
'\\.g': u'\u0121',
'\\.E': u'\u0116',
'\\.e': u'\u0117',
'(C)': u'\xa9',

'\\NS': u'\xa0',
'\\!!': u'\xa1',
'\\Ct': u'\xa2',
'\\Pd': u'\xa3',
'\\Cu': u'\xa4',
'\\Ye': u'\xa5',
'\\BB': u'\xa6',
'\\SE': u'\xa7',
"\\\':": u'\xa8',
'\\Co': u'\xa9',
'\\-a': u'\xaa',
'\\<<': u'\xab',
'\\NO': u'\xac',
'\\--': u'\xad',
'\\Rg': u'\xae',
"\\\'-": u'\xaf',
'\\DG': u'\xb0',
'\\+-': u'\xb1',
'\\2S': u'\xb2',
'\\3S': u'\xb3',
"\\\'\'": u'\xb4',
'\\My': u'\xb5',
'\\PI': u'\xb6',
'\\.M': u'\xb7',
"\\\',": u'\xb8',
'\\1S': u'\xb9',
'\\-o': u'\xba',
'\\>>': u'\xbb',
'\\14': u'\xbc',
'\\12': u'\xbd',
'\\34': u'\xbe',
'\\?I': u'\xbf',
'\\A!': u'\xc0',
"\\A\'": u'\xc1',
'\\A>': u'\xc2',
'\\A?': u'\xc3',
'\\A:': u'\xc4',
'\\AA': u'\xc5',
'\\AE': u'\xc6',
'\\C,': u'\xc7',
'\\E!': u'\xc8',
"\\E\'": u'\xc9',
'\\E>': u'\xca',
'\\E:': u'\xcb',
'\\I!': u'\xcc',
"\\I\'": u'\xcd',
'\\I>': u'\xce',
'\\I:': u'\xcf',
'\\D-': u'\xd0',
'\\N?': u'\xd1',
'\\O!': u'\xd2',
"\\O\'": u'\xd3',
'\\O>': u'\xd4',
'\\O?': u'\xd5',
'\\O:': u'\xd6',
'\\*X': u'\xd7',
'\\O/': u'\xd8',
'\\U!': u'\xd9',
"\\U\'": u'\xda',
'\\U>': u'\xdb',
'\\U:': u'\xdc',
"\\Y\'": u'\xdd',
'\\TH': u'\xde',
'\\ss': u'\xdf',
'\\a!': u'\xe0',
"\\a\'": u'\xe1',
'\\a>': u'\xe2',
'\\a?': u'\xe3',
'\\a:': u'\xe4',
'\\aa': u'\xe5',
'\\ae': u'\xe6',
'\\c,': u'\xe7',
'\\e!': u'\xe8',
"\\e\'": u'\xe9',
'\\e>': u'\xea',
'\\e:': u'\xeb',
'\\i!': u'\xec',
"\\i\'": u'\xed',
'\\i>': u'\xee',
'\\i:': u'\xef',
'\\d-': u'\xf0',
'\\n?': u'\xf1',
'\\o!': u'\xf2',
"\\o\'": u'\xf3',
'\\o>': u'\xf4',
'\\o?': u'\xf5',
'\\o:': u'\xf6',
'\\-:': u'\xf7',
'\\o/': u'\xf8',
'\\u!': u'\xf9',
"\\u\'": u'\xfa',
'\\u>': u'\xfb',
'\\u:': u'\xfc',
"\\y\'": u'\xfd',
'\\th': u'\xfe',
'\\y:': u'\xff',
'"\\A;"': u'\u0104',
"\\\'(": u'\u02d8',
'\\L/': u'\u0141',
'\\L<': u'\u013d',
"\\S\'": u'\u015a',
'\\S<': u'\u0160',
'\\S,': u'\u015e',
'\\T<': u'\u0164',
"\\Z\'": u'\u0179',
'\\Z<': u'\u017d',
'\\Z.': u'\u017b',
'"\\a;"': u'\u0105',
"\\\'(": u'\u02d8',
'\\l/': u'\u0142',
'\\l<': u'\u013e',
"\\s\'": u'\u015b',
"\\\'<": u'\u02c7',
'\\s<': u'\u0161',
'\\s,': u'\u015f',
'\\t<': u'\u0165',
"\\z\'": u'\u017a',
'\\\'\"': u'\u02dd',
'\\z<': u'\u017e',
'\\z.': u'\u017c',
"\\R\'": u'\u0154',
'\\A(': u'\u0102',
"\\L\'": u'\u0139',
"\\C\'": u'\u0106',
'\\C<': u'\u010c',
'"\\E;"': u'\u0118',
'\\E<': u'\u011a',
'\\D<': u'\u010e',
'\\D/': u'\u0110',
"\\N\'": u'\u0143',
'\\N<': u'\u0147',
'\\O\"': u'\u0150',
'\\R<': u'\u0158',
'\\U0': u'\u016e',
'\\U\"': u'\u0170',
'\\T,': u'\u0162',
"\\r\'": u'\u0155',
'\\a(': u'\u0103',
"\\l\'": u'\u013a',
"\\c\'": u'\u0107',
'\\c<': u'\u010d',
'"\\e;"': u'\u0119',
'\\e<': u'\u011b',
'\\d<': u'\u010f',
'\\d/': u'\u0111',
"\\n\'": u'\u0144',
'\\n<': u'\u0148',
'\\o\"': u'\u0151',
'\\r<': u'\u0159',
'\\u0': u'\u016f',
'\\u\"': u'\u0171',
'\\t,': u'\u0163',
"\\\'.": u'\u02d9',
'\\H/': u'\u0126',
'\\H>': u'\u0124',
'\\I.': u'\u0130',
'\\G(': u'\u011e',
'\\J>': u'\u0134',
'\\h/': u'\u0127',
'\\h>': u'\u0125',
'\\i.': u'\u0131',
'\\g(': u'\u011f',
'\\j>': u'\u0135',
'\\C.': u'\u010a',
'\\C>': u'\u0108',
'\\G.': u'\u0120',
'\\G>': u'\u011c',
'\\U(': u'\u016c',
'\\S>': u'\u015c',
'\\c.': u'\u010b',
'\\c>': u'\u0109',
'\\g.': u'\u0121',
'\\g>': u'\u011d',
'\\u(': u'\u016d',
'\\s>': u'\u015d',
'\\kk': u'\u0138',
'\\R,': u'\u0156',
'\\I?': u'\u0128',
'\\L,': u'\u013b',
'\\E-': u'\u0112',
'\\G,': u'\u0122',
'\\T/': u'\u0166',
'\\r,': u'\u0157',
'\\i?': u'\u0129',
'\\l,': u'\u013c',
'\\e-': u'\u0113',
'\\g,': u'\u0123',
'\\t/': u'\u0167',
'\\NG': u'\u014a',
'\\ng': u'\u014b',
'\\A-': u'\u0100',
'"\\I;"': u'\u012e',
'\\E.': u'\u0116',
'\\I-': u'\u012a',
'\\N,': u'\u0145',
'\\O-': u'\u014c',
'\\K,': u'\u0136',
'"\\U;"': u'\u0172',
'\\U?': u'\u0168',
'\\U-': u'\u016a',
'\\a-': u'\u0101',
'"\\i;"': u'\u012f',
'\\e.': u'\u0117',
'\\i-': u'\u012b',
'\\n,': u'\u0146',
'\\o-': u'\u014d',
'\\k,': u'\u0137',
'"\\u;"': u'\u0173',
'\\u?': u'\u0169',
'\\u-': u'\u016b',
'\\\\': u'\\',
'\\&': u'&',
'\\%': u'%',
r'{\aa}': u'\xe5',
r'{\aA}': u'\xc5'}

reverse_mapping = dict((b, a) for (a, b) in mapping.items())
encoded_char_re = re.compile('|'.join(re.escape(k) for k in mapping))

def decode_abc(abc_code): return encoded_char_re.sub(lambda m: mapping[m.group(0)], abc_code)
def encode_abc(abc_code): return ''.join(reverse_mapping.get(c, c) for c in abc_code)

abc_charset_re = re.compile(b'(%%|I:)abc-charset (?P<encoding>[-a-z0-9]+)')

def get_encoding_abc(abc_as_bytes, default_encoding = None):
    if abc_as_bytes[0:len(utf8_byte_order_mark)] == utf8_byte_order_mark:
        return 'utf-8'

    file_header = abc_as_bytes[:1024]
    match = abc_charset_re.search(file_header)
    if match:
        encoding = match.group('encoding')
        if PY3:
            encoding = encoding.decode()

        if encoding != 'utf-8':
            # normalize a bit
            if encoding in ['utf8', 'UTF-8', 'UTF8']:
                encoding = 'utf-8'
            codecs.lookup(encoding) # make sure that it exists at this point so as to avoid confusing errors later
        return encoding

    if file_header.startswith(b'%abc'):
        return 'utf-8'

    return default_encoding

