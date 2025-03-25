from zipfile import ZipFile
import os
import re
import xml2abc
import abc2xml
from collections import namedtuple
import xml.etree.ElementTree as E
import sys
PY3 = sys.version_info.major > 2

class StringFile(object):
    def __init__(self):
        self.parts = []
    def write(self, s):
        if PY3:
            if type (s) is bytes:
                s = s.decode ('utf-8', 'replace')
        else:
            s = unicode(s, 'utf-8')
        self.parts.append(s)
    def getvalue(self):
        return u''.join(self.parts)

def info (info_string, message, warn=1):
    if PY3:
        if type (message) is bytes:
            message = message.decode ('latin-1', 'replace')
    else:
        if type (message) is str:
            message = message.decode ('latin-1', 'replace')
    message = (warn and u'-- ' or u'') + message + u'\n'  # warnings prepended with --
    info_string.append (message)

# compatible with abc2xml.py version 63 and higher [WV] 2014-12-05
# info_messages should be a (empty) list, defined outside by the caller. After return this list contains all info messages of abc2xml
def abc_to_xml(abc, output_filepath, mxl=False, pageFormat=None, info_messages=None):

    # pageFormat: option to set the page format
    # note that the default pagelayout of abc2xml changed in version 63 and is now the same as in abcm2ps
    # scale, page height (mm), page width (mm), margin left (mm), -right, -top, -bottom
    # pageFormat = [0.5, 150, 200, 10, 10, 10, 10]    # for example, all numbers can be floats

    # option to save as compressed xml
    # True -> compressed mxl file, False -> normal xml file, 'a' or 'add' -> both compressed and normal xml saved
    # mxl = True  # for example

    if not pageFormat:
        pageFormat = []
    if not hasattr (abc2xml, 'abc_header'): # compute grammar only once
        abc2xml.abc_header, abc2xml.abc_voice, abc2xml.abc_scoredef, abc2xml.abc_percmap = abc2xml.abc_grammar ()
        abc2xml.mxm = abc2xml.MusicXml()    # mxm should be set in abc2xml, otherwise the options won't work

    if info_messages is None:   # only information messages of abc2xml, a real error raises an exception that contains the error message
        info_messages = []      # when info_messages is not passed by the caller this is a dummy and gets lost on return
    abc2xml.info = lambda message, warn=1: info (info_messages, message, warn)

    abc2xml.mxm.pageFmtCmd = pageFormat # should be a list of 7 floats

    path, filename = os.path.split (output_filepath)
    basename, extension = os.path.splitext (filename)
    abc2xml.convert(path, basename, abc, mxl, rOpt=False, bOpt=True)

# compatible with xml2abc.py version 54 and higher [WV] 2014-12-05
# info_messages should be a (empty) list, defined outside by the caller. After return this list contains all info messages of abc2xml
def xml_to_abc (filename, options, info_messages = None):
    file_numbers = [int(x) for x in re.findall(r'(\d+)', filename)]
    if file_numbers and 0 <= file_numbers[-1] <= 100000:
        X = file_numbers[-1]
    else:
        X = 1

    # 1.3.6 [SS] 2014-12-18
    #options = namedtuple ('Options', 'u m c d n b v x p j')                     # emulate the options object
    #options.m = 0; options.j = 0; options.p = []; options.b = 0;                # unused options
    #options.n = 0; options.v = 0; options.u = 0; options.c = 0; options.x = 0   # but all may be used if needed

    if info_messages is None:   # will contain all information messages of abc2xml,
        info_messages = []      # a real error raises an exception that contains the error message
    #xml2abc.info = lambda message, warn=1: info (info_messages, message, warn)

    results = []
    info_xml2abc=''
    for L in (4, 8, 16):        # make three passes to determine the shortest translation
        options.d = L
        #abcOut = xml2abc.ABCoutput ('','', X-1, options)
        #abcOut.outfile = StringFile ()
        #xml2abc.abcOut = abcOut
        #xml2abc.fnm = ''
        if os.path.splitext(filename)[1].lower() == '.mxl':
            z = ZipFile(filename)
            #fobj = z.open([n for n in z.namelist() if n[:4] != 'META' and n[-4:].lower() == '.xml'][0])
            for n in z.namelist():          # assume there is always an xml file in a mxl archive !!
                if (n[:4] != 'META') and ((n[-4:].lower() == '.xml') or (n[-9:].lower() == '.musicxml')):
                    fobj = z.open (n)
                    break   # assume only one MusicXML file per archive            
        else:
            fobj = open(filename, 'rb')

        while info_messages: info_messages.pop ()
        #xml2abc.Parser (options).parse (fobj)
        #s = abcOut.outfile.getvalue ()
        #FAU: Default parameters for xml2abc 157:
        #u=0; b=0; n=0; c=0; v=0; d=0; m=0; x=0; t=0;
        #stm=0; mnum=-1; no36=0; p='f'; s=0; j=0; v1=0; ped=0;
        #FAU Todo: Need to extend the management of other options
        s, info_xml2abc = xml2abc.vertaal(fobj.read(),u=options.u, b=options.b, n=options.n, c=options.c, v=options.v, d=L, m=options.m, p=options.p)
        #Allowed parameters for xml2abc:
        #u=0; b=0; n=0; c=0; v=0; d=0; m=0; x=0; t=0;
        #stm=0; mnum=-1; p='f'; s=0; j=0; v1=0; ped=0;

        #if True:
        #    s = re.sub(r'%%MIDI program \d+( \d+)?\n', '', s)              # remove MIDI program data
        #    s = re.sub(r'(?m)^ +', '', s)                                  # remove leading spaces on lines
        #    s = re.sub(r'(?m)^(?![a-zA-Z]:)([^%\n]+)%\d+\n', r'\1\n', s)   # remove bar number comments
        #    if s.count('V:') == 2 and 'V:1 treble' in s:                   # if there is just one voice (two mentions of V: in that case) with standard clef
        #        s = re.sub(r'(?m)^(V:\d+.*\n)', '', s)                     #   remove all V: field lines
        #    s = s.replace('V:1 treble nm="Right Hand"\nV:2 treble nm="Left Hand"\nV:1', 'V:1')
        #    s = re.sub(r'(:\|]?)\s+\|]', r'\1', s)
        #    s = s.replace('|] |]', '|]')
        #    s = s.replace(':|[|:', '::')
        #    s = s.replace(':||:', '::')
#
        #    for long_art, short_name in [('!tenuto!', 't'), ('!invertedturn!', 'i')]:
        #        if long_art in s:  # make abc code shorter by using U: field for tenuto
        #            s = s.replace('I:linebreak $', 'I:linebreak $\nU:%s=%s' % (short_name, long_art[1:-1]))
        #            s = s.replace(long_art, short_name)

        results.append(s)

    return sorted(results, key=lambda x: len(x))[0]

if __name__ == '__main__':
    xml_test_file = 'zBeet.xml'
    abc_test_file = './zBeet_test.abc'  # note the path "./" because an empty path will cause the output to go to stdout.

    # TEST xml2abc
    info_messages = []
    s = xml_to_abc (xml_test_file, info_messages)
    print(repr(s))                                   # the abc translation
    print(info_messages)
    #~ import codecs
    #~ codecs.open('output_temp.abc', 'wb', 'utf-8').write(s)   # if you want the test output in a file

    # TEST abc2xml
    info_messages = []
    fobj = open (abc_test_file, 'rb')
    encoded_data = fobj.read ()
    fobj.close ()
    abctext = encoded_data if type (encoded_data) == abc2xml.uni_type else abc2xml.decodeInput (encoded_data)

    abc_to_xml (abctext, abc_test_file, False, [], info_messages)
    print(info_messages)                             # the translation will be written to zBeet_test.xml, in the same dir as this interface
