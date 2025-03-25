#!/usr/bin/env python3

program_version = '1.3.8.7'
program_name = 'EasyABC ' + program_version

# Copyright (C) 2011-2014 Nils Liberg (mail: kotorinl at yahoo.co.uk)
# Copyright (C) 2015-2024 Seymour Shlien (mail: fy733@ncf.ca), Jan Wybren de Jong (jw_de_jong at yahoo dot com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

# # for finding memory leaks uncomment following two lines
# import gc
# gc.set_debug(gc.DEBUG_LEAK)
#
# # for finding segmentation fault or bus error (pip install faulthandler)
# try:
#     import faulthandler  # pip install faulthandler
#     faulthandler.enable()
# except ImportError:
#     sys.stderr.write('faulthandler not installed. Try: pip install faulthandler\n')
#     pass

import sys

PY3 = sys.version_info >= (3,0,0)
if not PY3:
    print("Python 2 is no longer supported. Please use:")
    print("   python3 easy_abc.py")
    exit()

abcm2ps_default_encoding = 'utf-8'  ## 'latin-1'
import codecs
utf8_byte_order_mark = codecs.BOM_UTF8  # chr(0xef) + chr(0xbb) + chr(0xbf) #'\xef\xbb\xbf'

if PY3:
    unichr = chr
    xrange = range
    def unicode(s):
        if isinstance(s, bytes):
            return s.decode()  # assumes utf-8
        return s
    max_int = sys.maxsize
    basestring = str
else:
    max_int = sys.maxint

import os, os.path
import wx
WX4 = wx.version().startswith('4')

from utils import *

application_path = get_application_path()

cwd = os.getenv('EASYABCDIR')
if not cwd:
    cwd = application_path

sys.path.append(cwd)

import re
import subprocess
import hashlib

if sys.version_info >= (3,0,0):
    import pickle as pickle # py3
else:
    import cPickle as pickle # py2

import threading
import shutil
import platform
import webbrowser
import time
import traceback
# import xml.etree.cElementTree as ET  # 1.3.7.4 [JWdJ] 2016-06-30
import zipfile
from datetime import datetime
from collections import deque, namedtuple, defaultdict
from io import StringIO
from wx.lib.scrolledpanel import ScrolledPanel
import wx.html
import wx.stc as stc
import wx.lib.agw.aui as aui
# import wx.lib.filebrowsebutton as filebrowse # 1.3.6.3 [JWdJ] 2015-04-22
import wx.lib.platebtn as platebtn
import wx.lib.mixins.listctrl as listmix
import wx.lib.agw.hypertreelist as htl
from wx.lib.embeddedimage import PyEmbeddedImage
# from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED # 1.3.7.3 [JWdJ] 2016-04-09
from wx import GetTranslation as _
from wxhelper import *
# from midiplayer import *
try:
    from fluidsynthplayer import *
    fluidsynth_available = True
except ImportError:
    sys.stderr.write('Warning: FluidSynth library not found. Playing using a SoundFont (.sf2) is disabled.\n')
    # sys.stderr.write(traceback.format_exc())
    fluidsynth_available = False

#FAU:MIDIPLAY: On Mac, it is possible to interface directly to the Midi syntethiser of mac OS via mplay: https://github.com/jheinen/mplay
# An adaptation is done to integrate with EasyABC
if wx.Platform == "__WXMAC__":
    from mplaysmfplayer import *
    
from xml2abc_interface import xml_to_abc, abc_to_xml
from midi2abc import midi_to_abc, Note, duration2abc
from generalmidi import general_midi_instruments
from abc_styler import ABCStyler
from abc_character_encoding import decode_abc, abc_text_to_unicode, get_encoding_abc
from abc_search import abc_matches_iter
from fractions import Fraction
from music_score_panel import MusicScorePanel
from svgrenderer import SvgRenderer
import itertools
from aligner import align_lines, extract_incipit, bar_sep, bar_sep_without_space, get_bar_length, bar_and_voice_overlay_sep
if sys.version_info >= (3,0,0):
    from queue import Queue # 1.3.6.2 [JWdJ] 2015-02
else:
    from Queue import Queue # 1.3.6.2 [JWdJ] 2015-02

application_running = True

if wx.Platform == "__WXMSW__":
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')
    import win32api
    import win32process

try:
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    if wx.Platform == "__WXMAC__":
        import pygame.midi as pypm
        pypm.init()
    else:
        import pygame
        import pygame.pypm as pypm
        pypm.Initialize()
except ImportError:
    try:
        import pypm
    except ImportError:
        sys.stderr.write('Warning: pygame/pypm module not found. Recording midi will not work\n')
finally:
    sys.stdout = old_stdout

def str2fraction(s):
    parts = [int(x.strip()) for x in s.split('/')]
    return Fraction(parts[0], parts[1])

Tune = namedtuple('Tune', 'xnum title rythm offset_start offset_end abc header num_header_lines')
MidiNote = namedtuple('MidiNote', 'start stop indices page svg_row')
class AbortException(Exception): pass
class Abcm2psException(Exception): pass
class NWCConversionException(Exception): pass

from abc_tune import *

dialog_background_colour = wx.Colour(245, 244, 235)
default_note_highlight_color = '#FF7F3F'
default_note_highlight_follow_color = '#CC00FF'
#default_style_color = {
#    'style_default_color':'#000000',
#    'style_chord_color':'#000000',
#    'style_comment_color':'#AAAAAA',
#    'style_specialcomment_color':'#888888',
#    'style_bar_color':'#000099',
#    'style_field_color':'#8C7853',
#    'style_fieldvalue_color':'#8C7853',
#    'style_embeddedfield_color':'#8C7853',
#    'style_embeddedfieldvalue_color':'#8C7853',
#    'style_fieldindex_color':'#000000',
#    'style_string_color':'#7F7F7F',
#    'style_lyrics_color':'#7F7F7F',
#    'style_grace_color':'#5a3700',
#    'style_ornament_color':'#777799',
#    'style_ornamentplus_color':'#888888',
#    'style_ornamentexcl_color':'#888888'
#}
default_style_color = {
    'style_default_color':'#131415',
    'style_chord_color':'#131415',
    'style_comment_color':'#656E77',
    'style_specialcomment_color':'#803378',
#    'style_bar_color':'#535A60',
    'style_bar_color':'#0000CC',
    'style_field_color':'#B75501',
    'style_fieldvalue_color':'#B75501',
    'style_embeddedfield_color':'#B75501',
    'style_embeddedfieldvalue_color':'#B75501',
    'style_fieldindex_color':'#000000',
    'style_string_color':'#2F6F44',
    'style_lyrics_color':'#51774e',
    'style_grace_color':'#5A3700',
    'style_ornament_color':'#015692',
    'style_ornamentplus_color':'#015692',
    'style_ornamentexcl_color':'#015692'
}

control_margin = 6
default_midi_volume = 96
default_midi_pan = 64
default_midi_instrument = 0

# 1.3.6.3 [JWdJ] 2015-04-22
class MidiTune(object):
    """ Container for abc2midi-generated .midi files """
    def __init__(self, abc_tune, midi_file=None, error=None):
        self.error = error
        self.midi_file = midi_file
        self.abc_tune = abc_tune

    def cleanup(self):
        if self.midi_file:
            if os.path.isfile(self.midi_file):
                os.remove(self.midi_file)
            self.midi_file = None

# 1.3.6.2 [JWdJ]
class SvgTune(object):
    """ Container for abcm2ps-generated .svg files """
    def __init__(self, abc_tune, svg_files, error=None):
        self.error = error
        self.svg_files = svg_files
        self.pages = {}
        self.abc_tune = abc_tune

    def render_page(self, page_index, renderer):
        if 0 <= page_index < self.page_count:
            page = self.pages.get(page_index, None)
            if page is None:
                page = renderer.svg_to_page(open(self.svg_files[page_index], 'rb').read())
                page.index = page_index
                self.pages[page_index] = page
        else:
            page = renderer.empty_page
        return page

    def cleanup(self):
        for f in self.svg_files:
            if os.path.isfile(f):
                os.remove(f)
        self.svg_files = ()

    def is_equal(self, svg_tune):
        if not isinstance(svg_tune, SvgTune):
            return False
        return self.abc_tune and self.abc_tune.is_equal(svg_tune.abc_tune)

    @property
    def page_count(self):
        return len(self.svg_files)

    @property
    def first_note_line_index(self):
        if self.abc_tune:
            return self.abc_tune.first_note_line_index
        return -1

    @property
    def tune_header_start_line_index(self):
        if self.abc_tune:
            return self.abc_tune.tune_header_start_line_index
        return -1

    @property
    def x_number(self):
        if self.abc_tune:
            return self.abc_tune.x_number
        return -1


# 1.3.6.3 [JWdJ] 2015-04-22
class AbcTunes(object):
    """ A holder for created tunes. Takes care of proper cleanup. """
    def __init__(self, cache_size=1):
        self.__tunes = {}
        self.cache_size = cache_size
        self.cached_tune_ids = deque()

    def get(self, tune_id):
        tune = self.__tunes.get(tune_id, None)
        return tune

    def add(self, tune):
        if tune.abc_tune and self.cache_size > 0:
            tune_id = tune.abc_tune.tune_id
            #if tune_id in self.__tunes:
            #    print 'tune already cached'
            while len(self.cached_tune_ids) >= self.cache_size:
                old_tune_id = self.cached_tune_ids.pop()
                self.remove(old_tune_id)
            self.__tunes[tune_id] = tune
            self.cached_tune_ids.append(tune_id)

    def cleanup(self):
        for tune_id in list(self.__tunes):
            self.remove(tune_id)
        self.__tunes = {}

    def remove(self, tune_id):
        tune = self.__tunes[tune_id]
        if tune is not None:
            tune.cleanup()
        del self.__tunes[tune_id]



#global variables
all_notes = "C,, D,, E,, F,, G,, A,, B,, C, D, E, F, G, A, B, C D E F G A B c d e f g a b c' d' e' f' g' a' b' c'' d'' e'' f'' g'' a'' b''".split()
doremi_prefixes = 'DRMFSLTdrmfslt' # 'd' corresponds to "do", 'r' to "re" and so on, DO vs. do is like C vs. c in ABC
doremi_suffixes = 'oeiaoaioOEIAOAIOlLhH'

execmessages = u''
visible_abc_code = u''

line_end_re = re.compile('\r\n|\r|\n')
tune_index_re = re.compile(r'^X:\s*(\d+)')

def note_to_index(abc_note):
    try:
        return all_notes.index(abc_note)
    except ValueError:
        return None

def text_to_lines(text):
    return line_end_re.split(text)

def read_abc_file(path):
    file_as_bytes = read_entire_file(path)
    encoding = get_encoding_abc(file_as_bytes)
    if encoding and encoding != 'utf-8':
        try:
            return file_as_bytes.decode(encoding)
        except UnicodeError:
            pass
    try:
        return file_as_bytes.decode('utf-8')
    except UnicodeError:
        return file_as_bytes.decode('latin-1')


# 1.3.6.3 [JWDJ] one function to determine font size
def get_normal_fontsize():
    if wx.Platform == "__WXMSW__":
        font_size = 10
    else:
        font_size = 14
    return font_size


def frac_mod(fractional_number, modulo):
    return fractional_number - modulo * int(fractional_number / modulo)


def start_process(cmd):
    """ Starts a process
    :param cmd: tuple containing executable and command line parameter
    :return: nothing
    """
    global execmessages # 1.3.6.4 [SS] 2015-05-27
    # 1.3.6.4 [SS] 2015-05-01
    if wx.Platform == "__WXMSW__":
        creationflags = win32process.DETACHED_PROCESS
    else:
        creationflags = 0
    # 1.3.6.4 [SS] 2015-05-27
    #process = subprocess.Popen(cmd,shell=False,stdin=None,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True,creationflags=creationflags)
    process = subprocess.Popen(cmd, shell=False, stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags)
    stdout_value, stderr_value = process.communicate()
    execmessages += '\n'+stderr_value + stdout_value
    return


def get_output_from_process(cmd, input=None, creationflags=None, cwd=None, bufsize=0, encoding='utf-8', errors='strict', output_encoding=None):
    stdin_pipe = None
    if input is not None:
        stdin_pipe = subprocess.PIPE
        if isinstance(input, basestring):
            input = input.encode(encoding, errors)

    if creationflags is None:
        if wx.Platform == "__WXMSW__":
            creationflags = win32process.CREATE_NO_WINDOW
        else:
            creationflags = 0

    process = subprocess.Popen(cmd, stdin=stdin_pipe, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags, cwd=cwd, bufsize=bufsize)
    stdout_value, stderr_value = process.communicate(input)
    returncode = process.returncode

    if output_encoding is None:
        output_encoding = encoding
    stdout_value, stderr_value = stdout_value.decode(output_encoding, errors), stderr_value.decode(output_encoding, errors)
    return stdout_value, stderr_value, returncode


def show_in_browser(url):
    handle = webbrowser.get()
    handle.open(url)


def get_default_path_for_executable(name):
    if wx.Platform == "__WXMSW__":
        exe_name = '{0}.exe'.format(name)
    else:
        exe_name = name

    path = os.path.join(cwd, 'bin', exe_name)
    if wx.Platform == "__WXGTK__":
        if not os.path.exists(path):
            path = '/usr/local/bin/{0}'.format(name)
        if not os.path.exists(path):
            path = '/usr/bin/{0}'.format(name)

    return path


# p09 2014-10-14 [SS]
def get_ghostscript_path():
    ''' Fetches the ghostscript path from the windows registry and returns it.
        This function may not see the 64-bit ghostscript installations, especially
        if Python was compiled as a 32-bit application.
    '''
    if sys.version_info >= (3,0,0):
        import winreg
    else:
        import _winreg as winreg

    available_versions = []
    for reg_key_name in [r"SOFTWARE\\GPL Ghostscript", r"SOFTWARE\\GNU Ghostscript"]:
        try:
            aReg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            aKey = winreg.OpenKey(aReg, reg_key_name)
            for i in range(100):
                try:
                    version = winreg.EnumKey(aKey, i)
                    bKey = winreg.OpenKey(aReg, reg_key_name + "\\%s" % version)
                    value, _ = winreg.QueryValueEx(bKey, 'GS_DLL')
                    winreg.CloseKey(bKey)
                    path = os.path.join(os.path.dirname(value), 'gswin32c.exe')
                    if os.path.exists(path):
                        available_versions.append((version, path))
                    path = os.path.join(os.path.dirname(value), 'gswin64c.exe')
                    if os.path.exists(path):
                        available_versions.append((version, path))
                except EnvironmentError:
                    break
            winreg.CloseKey(aKey)
        except:
            pass
    if available_versions:
        return sorted(available_versions)[-1][1]   # path to the latest version
    else:
        return None

# browser = None
# def upload_tune(tune, author):
#     ''' upload the tune to the site ABC WIKI site folkwiki.se (this UI option is only visible if the OS language is Swedish) '''
#     global browser
#     import mechanize
#     import tempfile
#     tune = tune.replace('\r\n', '\n')
#     text = '(:music:)\n%s\n(:musicend:)\n' % tune.strip()
#     if not browser:
#         browser = mechanize.Browser()
#     response = browser.open('https://www.folkwiki.se/Meta/Nyl%c3%a5t?n=Meta.Nyl%c3%a5t&base=Musik.Musik&action=newnumbered')
#     response = response.read()
#     import pdb; pdb.set_trace()
#     m = re.search(r"img src='(.*?action=captchaimage.*?)'", response)
#     if m:
#         captcha_url = m.group(1).encode('utf-8')
#         f = tempfile.NamedTemporaryFile(delete=False)
#         img_data = urlopen(captcha_url).read()

#         urlretrieve(urlunparse(parsed), outpath)
#         f.write(img_data)
#         f.close()
#         return ''
#     browser.select_form(nr=1)
#     browser['text'] = text.encode('utf-8')
#     browser['author'] = author.encode('utf-8')
#     response = browser.submit()
#     url = response.geturl()
#     url = url.split('?')[0]  # remove the part after the first '?'
#     return url

def launch_file(filepath):
    ''' open the given document using its associated program '''
    if wx.Platform == "__WXMSW__":
        os.startfile(filepath)
    elif wx.Platform == "__WXMAC__":
        subprocess.call(('open', filepath))
    elif os.name == 'posix':
        subprocess.call(('xdg-open', filepath))
    return True

def remove_non_note_fragments(abc, exclude_grace_notes=False):
    ''' remove parts of the ABC which is not notes or bar symbols by replacing them by spaces (in order to preserve offsets) '''

    repl_by_spaces = lambda m: ' ' * len(m.group(0))
    # replace non-note fragments of the text by replacing them by spaces (thereby preserving offsets), but keep also bar and repeat symbols
    abc = abc.replace('\r', '\n')
    abc = re.sub(r'(?s)%%beginps.+?%%endps', repl_by_spaces, abc)  # remove embedded postscript
    abc = re.sub(r'(?s)%%begintext.+?%%endtext', repl_by_spaces, abc)  # remove text
    abc = re.sub(comment_pattern, repl_by_spaces, abc) # remove comments
    abc = re.sub(r'\[\w:.*?\]', repl_by_spaces, abc)   # remove embedded fields
    abc = re.sub(r'(?m)^\w:.*?$', repl_by_spaces, abc) # remove normal fields
    abc = re.sub(r'\\"', repl_by_spaces, abc)          # remove escaped quote characters
    abc = re.sub(r'".*?"', repl_by_spaces, abc)        # remove strings
    abc = re.sub(r'!.+?!', repl_by_spaces, abc)        # remove ornaments like eg. !pralltriller!
    abc = re.sub(r'\+.+?\+', repl_by_spaces, abc)      # remove ornaments like eg. +pralltriller+
    if exclude_grace_notes:
        abc = re.sub(r'\{.*?\}', repl_by_spaces, abc)  # remove grace notes
    return abc

def get_notes_from_abc(abc, exclude_grace_notes=False):
    ''' returns a list of (start-offset, end-offset, abc-note-text) tuples for ABC notes/rests '''
    abc = remove_non_note_fragments(abc, exclude_grace_notes)

    # find and return ABC notes (including the text ranges)
    # 1.3.6.3 [JWDJ] 2015-3 made regex case sensitive again, because after typing Z and <space> a bar did not appear
    return [(note.start(0), note.end(0), note.group(0)) for note in
            re.finditer(r"([_=^]?[A-Ga-gz](,+|'+)?\d{0,2}(/\d{1,2}|/+)?)[><-]?", abc)]

def copy_bar_symbols_from_first_voice(abc):
    # normalize line endings (necessary for ^ in regexp) and extract the header and the two voices
    abc = re.sub(r'\r\n|\r', '\n', abc)
    m = re.match(r'(?sm)(.*?K:[^\n]+\s+)^V: *1(.*?)^V: *2\s*(.*)', abc)
    header, V1, V2 = m.groups()

    # replace strings and other parts with spaces and locate all bar symbols
    V1_clean = remove_non_note_fragments(V1)
    V2_clean = remove_non_note_fragments(V2)
    bar_seps1 = bar_sep_without_space.findall(V1_clean)
    bar_seps2 = bar_sep_without_space.findall(V2_clean)

    # abort, if the number of par symbols in the first and second voice doesn't match.
    if len(bar_seps1) != len(bar_seps2):
        print('warning: number of bar separators does not match (cannot complete operation)')
        return abc

    offset = 0
    for m in bar_sep_without_space.finditer(V2_clean):
        bar_symbol = bar_seps1.pop(0)
        bar_symbol = ' %s ' % bar_symbol.strip()
        start, end = m.start(0)+offset, m.end(0)+offset
        if bar_symbol != V2[start:end]:
            V2 = V2[:start] + bar_symbol + V2[end:]
            offset += len(bar_symbol) - (end-start)

    abc = header + 'V:1' + V1 + 'V:2\nI:repbra 0\n' + V2.lstrip()
    abc = abc.replace('\n', os.linesep)
    return abc

def process_MCM(abc):
    """ Processes sticky rhythm feature of mcmusiceditor https://www.mcmusiceditor.com/download/sticky-rhythm.pdf
    :param abc: abc possibly containing sticky rhythm
    :return: abc-compliant
    """
    abc, n = re.subn(r'(?m)^(L:\s*mcm_default)', r'L:1/8', abc)
    if n:
        # erase non-note fragments of the text by replacing them by spaces (thereby preserving offsets)
        repl_by_spaces = lambda m: ' ' * len(m.group(0))
        s = abc.replace('\r', '\n')
        s = re.sub(r'(?s)%%begin(ps|text).+?%%end(ps|text)', repl_by_spaces, s) # remove embedded text/postscript
        s = re.sub(r'(?m)^\w:.*?$|%.*$', repl_by_spaces, s)                 # remove non-embedded fields and comments
        s = re.sub(r'".*?"|!.+?!|\+\w+?\+|\[\w:.*?\]', repl_by_spaces, s)   # remove strings, ornaments and embedded fields

        fragments = []
        last_fragment_end = 0
        for m in re.finditer(r"(?P<note>([_=^]?[A-Ga-gxz](,+|'+)?))(?P<len>\d{0,2})(?P<dot>\.?)", s):
            if m.group('len') == '':
                length = 0
            else:
                length = Fraction(8, int(m.group('len')))
                if m.group('dot'):
                    length = length * 3 / 2

            start, end = m.start(0), m.end(0)
            fragments.append((False, abc[last_fragment_end:start]))
            fragments.append((True, m.group('note') + str(length)))
            last_fragment_end = end
        fragments.append((False, abc[last_fragment_end:]))
        abc = ''.join((text for is_note, text in fragments))
    return abc



def get_hash_code(*args):
    hash = hashlib.md5()
    for arg in args:
        if PY3 or type(arg) is unicode:
            arg = arg.encode('utf-8', 'ignore')
        hash.update(arg)
        if PY3:
            hash.update(program_name.encode('utf-8', 'ignore'))
        else:
            hash.update(program_name)
    return hash.hexdigest()[:10]

def change_abc_tempo(abc_code, tempo_multiplier):
    ''' multiples all Q: fields in the abc code by the given multiplier and returns the modified abc code '''

    def subfunc(m, multiplier):
        try:
            if '=' in m.group(0):
                parts = m.group(0).split('=')
                parts[1] = str(int(int(parts[1])*multiplier))
                return '='.join(parts)

            q = int(int(m.group(1))*multiplier)
            if '[' in m.group(0):
                return '[Q: %d]' % q
            else:
                return 'Q: %d' % q
        except:
            return m.group(0)

    abc_code, n1 = re.subn(r'(?m)^Q: *(.+)', lambda m, mul=tempo_multiplier: subfunc(m, mul), abc_code)
    abc_code, _ = re.subn(r'\[Q: *(.+)\]', lambda m, mul=tempo_multiplier: subfunc(m, mul), abc_code)
    # if no Q: field that is not inline add a new Q: field after the X: line
    # (it seems to be ignored by abcmidi if added earlier in the code)
    if n1 == 0:
        default_tempo = 120
        extra_line = 'Q:%d' % int(default_tempo * tempo_multiplier)
        lines = text_to_lines(abc_code)
        for i in range(len(lines)):
            if lines[i].startswith('X:'):
                lines.insert(i+1, extra_line)
                break
        abc_code = os.linesep.join(lines)
    return abc_code

def add_table_of_contents_to_postscript_file(filepath):
    def to_ps_string(s):  # handle unicode strings
        if any(c for c in s if ord(c) > 127):
            return '<FEFF%s>' % ''.join('%.4x' % ord(c) for c in s)   # encode unicode
        else:
            return '(%s)' % s.replace('(', r'\(').replace(')', r'\)') # escape any parenthesis
    lines = list(codecs.open(filepath, 'rU', 'utf-8'))
    for line in lines:
        if 'pdfmark' in line:
            return   # pdfmarks have already been added
    new_lines = []
    new_tune_state = False
    tunes = []
    for line in lines:
        new_lines.append(line)
        m = re.match(r'% --- (\d+) \((.*?)\) ---', line)
        if m:
            new_tune_state = True
            tune_index, tune_title = m.group(1), m.group(2)
            tunes.append((tune_index, tune_title))
        if new_tune_state and (line.rstrip().endswith('showc') or
                               line.rstrip().endswith('showr') or
                               line.rstrip().endswith('show')):
            ps_title = to_ps_string(decode_abc(tune_title))
            new_lines.append('[ /Dest /NamedDest%s /View [ /XYZ null null null ] /DEST pdfmark' % tune_index)
            new_lines.append('[ /Action /GoTo /Dest /NamedDest%s /Title %s /OUT pdfmark' % (tune_index, ps_title))
            new_tune_state = False  # now this tune has been handled, wait for next one....
    codecs.open(filepath, 'wb', 'utf-8').write(os.linesep.join(new_lines))

def sort_abc_tunes(abc_code, sort_fields, keep_free_text=True):
    lines = text_to_lines(abc_code)
    tunes = []
    file_header = []
    preceeding_lines = []
    Tune = namedtuple('Tune', 'lines header preceeding_lines')
    cur_tune = None
    for line in lines:

        if line.startswith('X:'):
            tune = Tune([], {}, [])
            if tunes:
                tune.preceeding_lines.extend(preceeding_lines)
            else:
                file_header = preceeding_lines
            preceeding_lines = []
            cur_tune = tune
            tunes.append(cur_tune)

        if cur_tune:
            cur_tune.lines.append(line)
            if re.match('[a-zA-Z]:', line):
                field = line[0]
                text = line[2:].strip().lower()
                if field == 'X':
                    try:
                        text = int(text)
                    except:
                        pass
                if field in cur_tune.header:
                    cur_tune.header[field] += '\n' + text
                else:
                    cur_tune.header[field] = text
            elif not line.strip():
                cur_tune = None
                preceeding_lines = [line]
        else:
            preceeding_lines.append(line)

    def get_sort_key_for_tune(tune, sort_fields):
        return tuple([tune.header.get(f, '').lower() for f in sort_fields])

    tunes = [(get_sort_key_for_tune(t, sort_fields), t) for t in tunes]
    tunes.sort()

    result = file_header
    for _, tune in tunes:
        if result and result[-1].strip() != '':
            result.append('')
        if keep_free_text:
            result.extend([l for l in tune.preceeding_lines if l.strip()])
        L = tune.lines[:]
        while L and not L[-1].strip():
            del L[-1]
        result.extend(L)
    return os.linesep.join(result)

# 1.3.6 [SS] 2014-12-17
def process_abc_code(settings, abc_code, header, minimal_processing=False, tempo_multiplier=None, landscape=False):
    ''' adds file header and possibly some extra fields, and may also change the Q: field '''

    #print traceback.extract_stack(None, 3)
    extra_lines = \
    '%%leftmargin 0.5cm\n' \
    '%%rightmargin 0.5cm\n' \
    '%%botmargin 0cm\n'  \
    '%%topmargin 0cm\n'

    if minimal_processing or settings['abcm2ps_clean']:
        extra_lines = ''

    if settings['abcm2ps_number_bars']:
        extra_lines += '%%barnumbers 1\n'
    if settings['abcm2ps_no_lyrics']:
        extra_lines += '%%musiconly 1\n'
    if settings['abcm2ps_refnumbers']:
        extra_lines += '%%withxrefs 1\n'
    if settings['abcm2ps_ignore_ends']:
        extra_lines += '%%continueall 1\n'
    if settings['abcm2ps_clean'] == False and settings['abcm2ps_defaults'] == False:
        extra_lines += '%%leftmargin ' + settings['abcm2ps_leftmargin'] + 'cm \n'
        extra_lines += '%%rightmargin ' + settings['abcm2ps_rightmargin'] + 'cm \n'
        extra_lines += '%%topmargin ' + settings['abcm2ps_topmargin'] + 'cm \n'
        extra_lines += '%%botmargin ' + settings['abcm2ps_botmargin'] + 'cm \n'
        extra_lines += '%%pagewidth ' + settings['abcm2ps_pagewidth'] + 'cm \n'
        extra_lines += '%%pageheight ' + settings['abcm2ps_pageheight'] + 'cm \n'

        extra_lines += '%%scale ' + settings['abcm2ps_scale'] + ' \n'
    parts = []
    if landscape and not minimal_processing:
        parts.append('%%landscape 1\n')
    if header:
        parts.append(header.rstrip() + os.linesep)
    if extra_lines:
        parts.append(extra_lines)
    parts.append(abc_code)
    abc_code = ''.join(parts)

    abc_code = re.sub(r'\[\[(.*/)(.+?)\]\]', r'\2', abc_code)  # strip PmWiki links and just include the link text
    if tempo_multiplier:
        abc_code = change_abc_tempo(abc_code, tempo_multiplier)

    abc_code = process_MCM(abc_code)

    # 1.3.6.3 [JWdJ] 2015-04-22 fixing newlines to part of process_abc_code
    abc_code = re.sub(r'\r\n|\r', '\n', abc_code)  ## TEST

    return abc_code

def AbcToPS(abc_code, cache_dir, extra_params='', abcm2ps_path=None, abcm2ps_format_path=None):
    ''' converts from abc to postscript. Returns (ps_file, error_message) tuple, where ps_file is None if the creation was not successful '''
    global execmessages
    # hash_code = get_hash_code(abc_code, read_text_if_file_exists(abcm2ps_format_path))
    ps_file = os.path.abspath(os.path.join(cache_dir, 'temp.ps'))

    # determine parameters
    cmd1 = [abcm2ps_path, '-', '-O', '%s' % ps_file]
    if extra_params:
        # split extra_params on spaces, but treat quoted strings as one element even if they contain spaces
        cmd1 = cmd1 + [x or y for (x, y) in re.findall(r'"(.+?)"|(\S+)', extra_params)]
    if abcm2ps_format_path and not '-F' in cmd1:
        # strip .fmt file ending
        if abcm2ps_format_path.lower().endswith('.fmt'):
            abcm2ps_format_path = abcm2ps_format_path[:-4]
        cmd1 = cmd1 + ['-F', abcm2ps_format_path]

    if os.path.exists(ps_file):
        os.remove(ps_file)

    input_abc = abc_code + os.linesep * 2
    stdout_value, stderr_value, returncode = get_output_from_process(cmd1, input=input_abc, encoding=abcm2ps_default_encoding)
    stderr_value = os.linesep.join([x for x in stderr_value.split('\n')
                                    if not x.startswith('abcm2ps-') and not x.startswith('File ') and not x.startswith('Output written on ')])
    stderr_value = stderr_value.strip()
    execmessages += '\nAbcToPs\n' + " ".join(cmd1) + '\n' + stdout_value + stderr_value
    if not os.path.exists(ps_file):
        ps_file = None
    return (ps_file, stderr_value)

def GetSvgFileList(first_page_file_path):
    ''' given 'file001.svg' this function will return all existing files in the series, eg. ['file001.svg', 'file002.svg'] '''
    result = []
    for i in range(1, 1000):
        fn = first_page_file_path.replace('001.svg', '%.3d.svg' % i)
        if os.path.exists(fn):
            result.append(fn)
        else:
            break
    return result

# 1.3.6 [SS] 2014-12-02 2014-12-07
def AbcToSvg(abc_code, header, cache_dir, settings, target_file_name=None, with_annotations=True, minimal_processing=False, landscape=False, one_file_per_page=True):
    global visible_abc_code
    # 1.3.6 [SS] 2014-12-17
    abc_code = process_abc_code(settings, abc_code, header, minimal_processing=minimal_processing, landscape=landscape)
    #hash = get_hash_code(abc_code, read_text_if_file_exists(abcm2ps_format_path), str(with_annotations)) # 1.3.6 [SS] 2014-11-13
    visible_abc_code = abc_code
    return abc_to_svg(abc_code, cache_dir, settings, target_file_name, with_annotations, one_file_per_page)

# 1.3.6.3 [JWDJ] 2015-04-21 splitted AbcToSvg up into 2 functions (abc_to_svg does not do preprocessing)
def abc_to_svg(abc_code, cache_dir, settings, target_file_name=None, with_annotations=True, one_file_per_page=True):
    """ converts from abc to postscript. Returns (svg_files, error_message) tuple, where svg_files is an empty list if the creation was not successful """
    global execmessages
    # 1.3.6.3 [SS] 2015-05-01
    global visible_abc_code
    abcm2ps_path = settings.get('abcm2ps_path', '')
    abcm2ps_format_path = settings.get('abcm2ps_format_path', '')
    extra_params = settings.get('abcm2ps_extra_params', '')
    # 1.3.6.3 [SS] 2015-05-01
    visible_abc_code = abc_code

    if target_file_name:
        svg_file = target_file_name
        svg_file_first = svg_file.replace('.svg', '001.svg')
    else:
        #grab svg file from cache if it exists
        #svg_file = os.path.abspath(os.path.join(cache_dir, 'temp_%s.svg' % hash)) # 1.3.6 [SS] 2014-11-13
        svg_file = os.path.abspath(os.path.join(cache_dir, 'temp.svg')) # 1.3.6 [SS] 2014-11-13
        svg_file_first = svg_file.replace('.svg', '001.svg')

        #if os.path.exists(svg_file_first):  p09 disable cache
            #return (GetSvgFileList(svg_file_first), '')

        # 1.3.6 [SS] 2014-11-16
        # clear out all 001.svg, 002.svg and etc. so the old files
        # do not appear accidently
        files_to_be_deleted = GetSvgFileList(svg_file_first)
        for f in files_to_be_deleted:
            os.remove(f)

    # determine parameters
    cmd1 = [abcm2ps_path, '-', '-O', '%s' % os.path.basename(svg_file)]
    if one_file_per_page:
        cmd1 = cmd1 + ['-v']
    else:
        cmd1 = cmd1 + ['-g']

    if with_annotations:
        cmd1 = cmd1 + ['-A']


    if extra_params:
        # split extra_params on spaces, but treat quoted strings as one element even if they contain spaces
        cmd1 = cmd1 + [x or y for (x, y) in re.findall(r'"(.+?)"|(\S+)', extra_params)]
    if abcm2ps_format_path and not '-F' in cmd1:
        # strip .fmt file ending
        if abcm2ps_format_path.lower().endswith('.fmt'):
            abcm2ps_format_path = abcm2ps_format_path[:-4]
        cmd1 = cmd1 + ['-F', abcm2ps_format_path]


    if os.path.exists(svg_file_first):
        os.remove(svg_file_first)

    #fse = sys.getfilesystemencoding()
    #cmd1 = [arg.encode(fse) if isinstance(arg,unicode) else arg for arg in cmd1]

    # clear execmessages any time the music panel is refreshed
    execmessages = u'\nAbcToSvg\n' + " ".join(cmd1)
    input_abc = abc_code + os.linesep * 2
    stdout_value, stderr_value, returncode = get_output_from_process(cmd1, input=input_abc, encoding=abcm2ps_default_encoding, bufsize=-1, cwd=os.path.dirname(svg_file))
    execmessages += '\n' + stdout_value + stderr_value

    if returncode < 0:
        execmessages += '\n' + _('%(program)s exited abnormally (errorcode %(error)#8x)') % {'program': 'Abcm2ps', 'error': returncode & 0xffffffff}
        raise Abcm2psException('Unknown error - abcm2ps may have crashed')
    stderr_value = os.linesep.join([x for x in stderr_value.splitlines()
                                    if not x.startswith('abcm2ps-') and not x.startswith('File ') and not x.startswith('Output written on ')])
    stderr_value = stderr_value.strip()
    if os.path.exists(svg_file_first):
        return (GetSvgFileList(svg_file_first), stderr_value)
    else:
        return ([], stderr_value)


def AbcToAbc(abc_code, cache_dir, params, abc2abc_path=None):
    ' converts from abc to abc. Returns (abc_code, error_message) tuple, where abc_code is None if abc2abc was not successful'
    global execmessages

    abc_code = re.sub(r'\\"', '', abc_code)  # remove escaped quote characters, since abc2abc cannot handle them

    # determine parameters
    cmd1 = [abc2abc_path, '-', '-r', '-b', '-e'] + params

    execmessages += '\nAbcToAbc\n' + " ".join(cmd1)

    input_abc = abc_code + os.linesep * 2
    stdout_value, stderr_value, returncode = get_output_from_process(cmd1, bufsize=-1, input=input_abc, encoding=abcm2ps_default_encoding)
    execmessages += '\n' + stderr_value
    if returncode < 0:
        execmessages += '\n' + _('%(program)s exited abnormally (errorcode %(error)#8x)') % {'program': 'Abc2abc', 'error': returncode & 0xffffffff}

    stderr_value = stderr_value.strip()
    stdout_value = stdout_value
    if returncode == 0:
        return stdout_value, stderr_value
    else:
        return None, stderr_value

# 1.3.6.4 [SS] 2015-06-22
def MidiToMftext(midi2abc_path, midifile):
    ' dissasemble midi file to text using midi2abc'
    global execmessages
    cmd1 = [midi2abc_path, midifile, '-mftext']
    execmessages += '\nMidiToMftext\n' + " ".join(cmd1)

    if os.path.exists(midi2abc_path):
        stdout_value, stderr_value, returncode = get_output_from_process(cmd1, bufsize=-1)
        midiframe = MyMidiTextTree(_('Disassembled Midi File'))
        midiframe.Show(True)
        midi_data = stdout_value
        midi_lines = midi_data.splitlines()
        midiframe.LoadMidiData(midi_lines)
    else:
        wx.MessageBox(_("Cannot find the executable midi2abc. Be sure it is in your bin folder and its path is defined in ABC Setup/File Settings."), _("Error"), wx.ICON_ERROR | wx.OK)

def get_midi_structure_as_text(midi2abc_path, midi_file):
    result = u''
    if os.path.exists(midi2abc_path):
        cmd = [midi2abc_path, midi_file, '-mftext']
        result, stderr_value, returncode = get_output_from_process(cmd, bufsize=-1)
    return result

# p09 2014-10-14 2014-12-17 2015-01-28 [SS]
def AbcToPDF(settings, abc_code, header, cache_dir, extra_params='', abcm2ps_path=None, gs_path=None, abcm2ps_format_path=None, generate_toc=False):
    global execmessages, visible_abc_code # 1.3.6.1 [SS] 2015-01-13
    pdf_file = os.path.abspath(os.path.join(cache_dir, 'temp.pdf'))
    # 1.3.6 [SS] 2014-12-17
    abc_code = process_abc_code(settings, abc_code, header, minimal_processing=True)
    (ps_file, error) = AbcToPS(abc_code, cache_dir, extra_params, abcm2ps_path, abcm2ps_format_path)
    if not ps_file:
        return None

    #if generate_toc:
    #    add_table_of_contents_to_postscript_file(ps_file)

    gs_path = unicode(gs_path)

    # convert ps to pdf
    # p09 we already checked for gs_path in restore_settings() 2014-10-14
    cmd2 = [gs_path, '-sDEVICE=pdfwrite', '-sOutputFile=%s' % pdf_file, '-dBATCH', '-dNOPAUSE', ps_file]
    #FAU:PDF:Manage the case where one put ps2pdf from ghostscript instead of gs directly
    if 'ps2pdf' in gs_path:
        cmd2 = [gs_path, ps_file, pdf_file]
    elif wx.Platform == "__WXMAC__" and int(platform.mac_ver()[0].split('.')[0]) <= 13 and gs_path == '/usr/bin/pstopdf':
        cmd2 = [gs_path, ps_file, '-o', pdf_file]
    if os.path.exists(pdf_file):
        os.remove(pdf_file)

    # 1.3.6.1 [SS] 2015-01-13
    execmessages += '\nAbcToPDF\n' + " ".join(cmd2)
    stdout_value, stderr_value, returncode = get_output_from_process(cmd2)
    # 1.3.6.1 [SS] 2015-01-13
    execmessages += '\n' + stderr_value
    if os.path.exists(pdf_file):
        return pdf_file

# 1.3.6.4 [SS] 2015-07-10
gchordpat = re.compile('\"[^\"]+\"')
keypat = re.compile('([A-G]|[a-g]|)(#|b?)')
def test_for_guitar_chords(abccode):
    ''' The function returns False if there are no guitar chords
        in the tune abccode; otherwise it returns True. It is
        not sufficient to just find a token with enclosed by
        double quotes. The token must begin with a letter between
        A-G or a-g. We try up to 5 times in case, the token is
        used to present other information above the staff.

        The function is used to create a cleaner processed file
        for MIDI by eliminating unnecessary %%MIDI commands.
    '''
    i = 0
    k = 0
    found = False
    while k < 5:
        m = gchordpat.search(abccode, i)
        if m:
            token = m.group(0)
            i = m.end() + 1
            if keypat.match(token[1:-1]):
                found = True
                break
        else:
            break
        k = k + 1
    return found


# 1.3.6.4 [SS] 2015-07-03
def list_voices_in(abccode):
    ''' The function scans the entire abccode searching for V:
        and extracts the voice identifier (assuming it is not
        too long). A list of all the unique identifiers are
        returned.
    '''
    voices = []
    [voices.append(v) for v in [m.group('voice_id') or m.group('inline_voice_id') for m in voice_re.finditer(abccode)] if v not in voices]
    return voices


# 1.3.6.4 [SS] 2015-07-03
def grab_time_signature(abccode):
    ''' The function detects the first time signature M: n/m in
        abccode and returns [n, m].
    '''
    fracpat = re.compile(r'(\d+)/(\d+)')
    loc = abccode.find('M:')
    meter = abccode[loc+2:loc+10]
    meter = meter.lstrip()
    if meter.find('C') >= 0:
        return [4, 4]
    m = fracpat.match(meter)
    if m:
        num = int(m.group(1))
        den = int(m.group(2))
    else:  #no M: in tune
        num = 4
        den = 4
    return [num, den]


# 1.3.6.4 [SS] 2015-07-03
def drum_intro(timesig):
    ''' Depending on the numerator of the time signature, the function
        returns a MIDI drum command which produces a sequence of clicks.
    '''
    n = timesig[0]
    if n == 2:
        d = '%%MIDI drum dd 77 76'
    elif n == 3:
        # 1.3.6.4 [SS] 2015-09-06
        d = '%%MIDI drum ddd 77 76 76'
    elif n == 4:
        d = '%%MIDI drum dddd 77 76 77 76 110 50 60 50'
    elif n == 6:
        d = '%%MIDI drum dddddd 77 76 76 77 76 76 110 50 50 60 50 50'
    elif n == 9:
        d = '%%MIDI drum ddddddddd 77 76 76 77 76 76 77 76 76 110 50 50 60 50 50 60 50 50'
    else:
        d = '%%MIDI drum d 77'
    return d


#1.3.6.4 [SS] 2015-07-05
def need_left_repeat(abccode):
    ''' Determine whether a left repeat |: is missing. If there
        are no right repeats (either :| or ::) then we do not need
        a left repeat. If a right repeat is found then we need
        to find a left repeat that appears before the first right
        repeat. Otherwise it is missing.
     '''
    loc1 = abccode.find(r':|')
    loc2 = abccode.find(r'::')
    if loc1 != -1 and loc2 != -1:
        loc = min(loc1, loc2)
    elif loc1 != -1:
        loc = loc1
    elif loc2 != -1:
        loc = loc2
    else:
        # no right repeat found
        return False

    loc1 = abccode.find(r'|:')
    if loc1 == -1:
        # left repeat missing but right repeat found
        return True
    if loc1 < loc:
        return False
    # left repeat found after right repeat. (Left repeat
    # missing for first repeat block.)
    return True



# 1.3.6.4 [SS] 2015-07-03
def make_abc_introduction(abccode, voicelist):
    ''' Given the music in abc notation, the function creates a sequence
        of clicks which counts in the tune. The function needs to determine
        the time signature and a list of all the voice names in the tune.
        If there are no voices, the sequence is in inserted after the first K:;
        otherwise, the sequence is inserted into the first voice and the
        other voices are padded with silent measures. Frequently, the
        left repeat symbol is omitted. We need to put a left repeat after
        the clicking sequence so that clicking sequence is not repeated.
    '''
    intro = []
    meter = grab_time_signature(abccode)

    if voicelist:
        intro.append("V: {0}".format(voicelist[0]))
    intro.append(drum_intro(meter))
    intro.append("%%MIDI drumon")
    if need_left_repeat(abccode):
        intro.append("Z|Z|:\\")
    else:
        intro.append("Z|Z|\\")
    intro.append("%%MIDI drumoff")

    if voicelist:
        for v in voicelist[1:]:
            intro.append("V: {0}".format(v))
            if need_left_repeat(abccode):
                intro.append("Z|Z|:\\")
            else:
                intro.append("Z|Z|\\")
    return intro


# 1.3.6  [SS] simplified the calling sequence 2014-11-15
def AbcToMidi(abc_code, header, cache_dir, settings, statusbar, tempo_multiplier, midi_file_name=None, add_follow_score_markers=False):
    global execmessages, visible_abc_code

    abc_code = process_abc_for_midi(abc_code, header, cache_dir, settings, tempo_multiplier)
    visible_abc_code = abc_code #p09 2014-10-22 [SS]

    abc_tune = AbcTune(abc_code)
    if midi_file_name is None:
        midi_file_name = os.path.abspath(os.path.join(cache_dir, 'temp%s.midi' % abc_tune.tune_id))
        # midi_file_name = generate_temp_file_name(cache_dir, '.midi')
    midi_file = abc_to_midi(abc_code, settings, midi_file_name, add_follow_score_markers)
    # P09 2014-10-26 [SS]
    MyInfoFrame.update_text()

    # 1.3.6 2014-12-16 [SS]
    MyAbcFrame.update_text()

    # 1.3.6 [SS] 2014-12-08
    if execmessages.find('Error') != -1:
        statusbar.SetStatusText(_('{0} reported some errors').format('Abc2midi'))
    elif execmessages.find('Warning') != -1:
        statusbar.SetStatusText(_('{0} reported some warnings').format('Abc2midi'))
    else:
        statusbar.SetStatusText('')

    if midi_file:
        return MidiTune(abc_tune, midi_file)
    else:
        return None

# 1.3.6.3 [JWDJ] 2015-04-21 split up AbcToMidi into 2 functions: preprocessing (process_abc_for_midi) and actual midi generation (abc_to_midi)
def process_abc_for_midi(abc_code, header, cache_dir, settings, tempo_multiplier):
    ''' This function inserts extra lines in the abc tune controlling the assignment of musical instruments to the different voices
        per the instructions in the ABC Settings/abc2midi and voices. If the tune already contains these instructions, eg. %%MIDI program,
        %%MIDI chordprog, etc. then the function avoids changing these assignments by suppressing the output of the additional commands.
        Note that these assignments can also be embedded in the body of the tune using the instruction [I: MIDI = program 10] for
        examples see https://abcmidi.sourceforge.io/ and click link [I:MIDI=...].
    '''
    global execmessages
    ####   set all the control flags which determine which %%MIDI commands are written

    play_chords = settings.get('play_chords')
    default_midi_program = settings.get('midi_program')
    default_midi_chordprog = settings.get('midi_chord_program')
    default_midi_bassprog = settings.get('midi_bass_program')
    # 1.3.6.4 [SS] 2015-06-07
    default_midi_melodyvol = settings.get('melodyvol')
    default_midi_chordvol = settings.get('chordvol')
    default_midi_bassvol = settings.get('bassvol')
    # 1.3.6.3 [SS] 2015-05-04
    default_tempo = settings.get('bpmtempo')
    # build the list of midi program to be used for each voice
    midi_program_ch_list = ['midi_program_ch%d' % ch for ch in range(1, 16 + 1)]

    # this flag is added just in case none would have been set but shouldn't be the case.
    if not default_midi_bassprog:
        default_midi_bassprog = default_midi_chordprog

    # verify if MIDI instructions are already present if yes, no extra command should be added

    add_midi_program_extra_line = True
    add_midi_volume_extra_line = True # 1.3.6.3 [JWDJ] 2015-04-21 added so that when abc contains instrument selection, the volume from the settings can still be used
    add_midi_gchord_extra_line = True
    add_midi_chordprog_extra_line = True
    add_midi_introduction = settings.get('midi_intro')  # 1.3.6.4 [SS] 2015-07-05

    if not test_for_guitar_chords(abc_code):
        add_midi_chordprog_extra_line = False
        add_midi_gchord_extra_line = False

    # 1.3.6.3 [JWDJ] 2015-04-17 header was forgotten when checking for MIDI directives
    abclines = text_to_lines(header + abc_code)
    for line in abclines:
        if line.startswith('%%MIDI program'):
            add_midi_program_extra_line = False
        elif line.startswith('%%MIDI control 7 '):
            add_midi_volume_extra_line = False
        elif line.startswith('%%MIDI gchord'):
            add_midi_gchord_extra_line = False
        elif line.startswith('%%MIDI chordprog') or line.startswith('%%MIDI bassprog'):
            add_midi_chordprog_extra_line = False
        if not (add_midi_program_extra_line or add_midi_volume_extra_line or add_midi_gchord_extra_line or add_midi_chordprog_extra_line):
            break

    #### create the abc_header which will be placed in front of the processed abc file
    # extra_lines is a list of all the MIDI commands to be put in abcheader

    #FAU: enforce at least one extra_lines to avoid to introduce a blank line
    extra_lines = ['%']

    # build default list of midi_program
    # this is needed in case no instrument per voices where defined or in case option "separate defaults per voice" is not checked

    midi_program_ch = []
    for channel in range(16):
        midi_program_ch.append([default_midi_program, default_midi_volume, default_midi_pan])

    separate_defaults_per_voice = settings.get('separate_defaults_per_voice', False)
    if separate_defaults_per_voice:
        for channel in range(16):
            program_vol_pan = settings.get(midi_program_ch_list[channel])
            if program_vol_pan:
                midi_program_ch[channel] = program_vol_pan

    # Though these instructions shouldn't be needed (they are added for each voice afterwards),
    # there is a problem with QuickTime on the Mac and these lines ensure that the MIDI file is
    # played correctly.
    if wx.Platform == "__WXMAC__":
        for channel in range(16):
            extra_lines.append('%%MIDI program {0} {1}'.format(channel+1, midi_program_ch[channel][0]))
        extra_lines.append('%%MIDI program {0}'.format(default_midi_program)) # 1.3.6 [SS] 2014-11-16
    if add_midi_volume_extra_line:
        extra_lines.append('%%MIDI control 7 {0}'.format(midi_program_ch[0][1]))
        extra_lines.append('%%MIDI control 10 {0}'.format(midi_program_ch[0][2]))

    # add extra instruction to play guitar chords
    if add_midi_gchord_extra_line:
        if play_chords:
            extra_lines.append('%%MIDI gchordon')
            # 1.3.6 [SS] 2014-11-26
            gchord = settings.get('gchord')
            if gchord and gchord != 'default':
                extra_lines.append('%%MIDI gchord '+ gchord)

        else:
            extra_lines.append('%%MIDI gchordoff')
    # add extra instruction to define instrument for guitar chords and bass
    # These lines should be added to only the voices that have guitar chords. However,
    # unless we scan the voice in advance, we do not know whether it does have guitar
    # chords. There is nothing wrong in including these commands in every voice since
    # they will be ignored if nonapplicable; but it makes a rather messy processed for
    # midi file which is harder to interpret.

    # The extra_lines are added after X:1 in case the tune is not multivoice but
    # has guitar chords embedded. If it is a multivoice tune or the tune does not
    # have guitar chords, these lines are not necessary but do not do any harm.
    #
    # 1.3.6.4 [SS] 2015-06-29
    if add_midi_program_extra_line:
        extra_lines.append('%%MIDI program {0}'.format(default_midi_program))

    if add_midi_chordprog_extra_line:
        extra_lines.append('%%MIDI chordprog {0}'.format(default_midi_chordprog))
        extra_lines.append('%%MIDI bassprog {0}'.format(default_midi_bassprog))
        # 1.3.6.4 [SS] 2015-06-07
        extra_lines.append('%%MIDI chordvol {0}'.format(default_midi_chordvol))
        extra_lines.append('%%MIDI bassvol {0}'.format(default_midi_bassvol))

    # 1.3.6.3 [SS] 2015-03-19
    if int(settings.get('transposition', 0)) != 0:
        extra_lines.append('%%MIDI transpose {0}'.format(settings['transposition']))

    # 1.3.6.3 [SS] 2015-05-04
    if default_tempo != 120:
        extra_lines.append('Q:1/4 = %s' % default_tempo)

    abcheader = os.linesep.join(extra_lines + [header.strip()])

    # 1.3.6.4 [SS] 2015-07-07
    voicelist = list_voices_in(abc_code)
    # 1.3.6.4 [SS] 2015-07-03
    if add_midi_introduction:
        midi_introduction = make_abc_introduction(abc_code, voicelist)

    ####  modify abc_code to add MIDI instruction just after voice definition
    # (because using channel only in header doesn't seem to allow association with voice

    abclines = text_to_lines(abc_code) # 1.3.6.3 [JWDJ] 2015-04-17 split abc_code without header

    # 1.3.7.0 [SS] 2016-01-05
    # always add %%MIDI control 7 so user can control volume of melody
    #if add_midi_program_extra_line or add_midi_gchord_extra_line or add_midi_introduction:
    if True:  # 1.3.7.0 [SS] 2016-01-05
        list_voice = [] # keeps track of the voices we have already seen
        new_abc_lines = [] # contains the new processed abc tune
        voice = 0
        header_finished = False
        for line in abclines:
            new_abc_lines.append(line)
            # do not take into account the definition present in the header (maybe it would be better... to be further analysed)
            if line.startswith('K:'):
                if not header_finished:
                    # 1.3.6.4 [SS] 2015-07-09
                    if len(voicelist) == 0:
                        new_abc_lines.append('%%MIDI control 7 {0}'.format(int(default_midi_melodyvol)))
                    # 1.3.6.4 [SS] 2015-07-03
                    if add_midi_introduction:
                        new_abc_lines.extend(midi_introduction)
                header_finished = True
            if header_finished:
                match = voice_re.match(line)
                if match:
                    inline_voice_id = match.group('inline_voice_id')
                    voice_ID = inline_voice_id or match.group('voice_id')
                    if voice_ID not in list_voice:
                        # 1.3.6.4 [SS] 2015-07-08
                        # if it is an inline voice, we are not want to include the following notes before
                        # specifying the %%MIDI parameters
                        if inline_voice_id:
                            # remove last line in new_abc and put it back afterwards
                            removedline = new_abc_lines.pop()
                            new_abc_lines.append('V: {0}'.format(voice_ID))

                        # 1.3.6.4 [SS] 2015-06-19
                        # ideally you should determine whether gchords are present in this voice
                        voice_has_gchords = True

                        #as it's a new voice, add MIDI program instruction
                        list_voice.append(voice_ID)
                        if add_midi_program_extra_line:
                            new_abc_lines.append('%%MIDI program {0}'.format(midi_program_ch[voice][0]))
                        if add_midi_volume_extra_line:
                            new_abc_lines.append('%%MIDI control 7 {0}'.format(midi_program_ch[voice][1]))
                            new_abc_lines.append('%%MIDI control 10 {0}'.format(midi_program_ch[voice][2]))

                        if voice_has_gchords:
                            if add_midi_gchord_extra_line:
                                if play_chords:
                                    new_abc_lines.append('%%MIDI gchordon')
                                else:
                                    new_abc_lines.append('%%MIDI gchordoff')
                            if add_midi_chordprog_extra_line:
                                new_abc_lines.append('%%MIDI chordprog {0}'.format(default_midi_chordprog))
                                new_abc_lines.append('%%MIDI bassprog {0}'.format(default_midi_bassprog))
                                # 1.3.6.4 [SS] 2015-06-19
                                new_abc_lines.append('%%MIDI chordvol {0}'.format(default_midi_chordvol))
                                new_abc_lines.append('%%MIDI bassvol {0}'.format(default_midi_bassvol))
                        if inline_voice_id:
                            new_abc_lines.append(removedline)
                        voice += 1
                        if voice == 16:
                            voice = 0

        abc_code = os.linesep.join(new_abc_lines)

    #### assemble everything together

    # 1.3.6.4 [SS] 2014-07-07 replacement for process_abc_code
    # we do not want any abcm2ps options added
    sections = [abcheader.rstrip() + os.linesep, abc_code]
    abc_code = ''.join(sections) # put it together
    abc_code = re.sub(r'\[\[(.*/)(.+?)\]\]', r'\2', abc_code)  # strip PmWiki links and just include the link text
    if tempo_multiplier:
        abc_code = change_abc_tempo(abc_code, tempo_multiplier)
    abc_code = process_MCM(abc_code)
    # 1.3.6.3 [JWdJ] 2015-04-22 fixing newlines to part of process_abc_code
    abc_code = re.sub(r'\r\n|\r', '\n', abc_code)  ## TEST
    # 1.3.6 [SS] 2014-12-17
    #abc_code = process_abc_code(settings,abc_code, abcheader, tempo_multiplier=tempo_multiplier, minimal_processing=True)

    abc_code = abc_code.replace(r'\"', ' ')  # replace escaped " characters with space since abc2midi doesn't understand them

    # make sure that X field is on the first line since abc2midi doesn't seem to support
    # fields and instructions that come before the X field
    if not abc_code.startswith('X:'):
        abclines = text_to_lines(abc_code) # take it apart again
        for i in range(len(abclines)):
            if abclines[i].startswith('X:'):
                line = abclines[i]
                del abclines[i]
                abclines.insert(0, line)
                break
        abc_code = os.linesep.join(abclines) # put it back together

    #### for debugging
    #Write temporary abc_file (for debug purpose)
    #temp_abc_file =  os.path.abspath(os.path.join(cache_dir, 'temp_%s.abc' % hash)) 1.3.6 [SS] 2014-11-13
    temp_abc_file = os.path.abspath(os.path.join(cache_dir, 'temp.abc')) # 1.3.6 [SS] 2014-11-13
    f = codecs.open(temp_abc_file, 'wb', 'UTF-8') #p08 patch
    f.write(abc_code)
    f.close()

    return abc_code



# 1.3.6.3 [JWDJ] 2015-04-21 split up AbcToMidi into 2 functions: preprocessing (process_abc_for_midi) and actual midi generation (abc_to_midi)
def abc_to_midi(abc_code, settings, midi_file_name, add_follow_score_markers):
    global execmessages

    abc2midi_path = settings.get('abc2midi_path')
    cmd = [abc2midi_path, '-', '-o', midi_file_name]
    cmd = add_abc2midi_options(cmd, settings, add_follow_score_markers)
    execmessages += '\nAbcToMidi\n' + " ".join(cmd)
    input_abc = abc_code + os.linesep * 2
    stdout_value, stderr_value, returncode = get_output_from_process(cmd, input=input_abc)
    execmessages += '\n' + stdout_value + stderr_value
    if stdout_value:
        stdout_value = re.sub(r'(?m)(writing MIDI file .*\r?\n?)', '', stdout_value)
    if returncode != 0:
        # 1.3.7.0 [SS] 2016-01-06
        execmessages += '\n' + _('%(program)s exited abnormally (errorcode %(error)#8x)') % { 'program': 'AbcToMidi', 'error': returncode & 0xffffffff }
        return None

    return midi_file_name

# 1.3.6 [SS] 2014-11-24
def add_abc2midi_options(cmd, settings, add_follow_score_markers):
    #Force BF option flag to be at the last position according to jwdj/EasyABC#86 and sshlien/abcmidi#8
    #if str2bool(settings['barfly']):
    #    cmd.append('-BF')
    if str2bool(settings['nofermatas']):
        cmd.append('-NFER')
    if str2bool(settings['nograce']):
        cmd.append('-NGRA')
    if str2bool(settings['nodynamics']):
        cmd.append('-NFNP')
    # 1.3.6.3 [SS] 2015-03-20
    if settings['tuning'] != '440':
        cmd.append('-TT %s' % settings['tuning'])
    # 1.3.6.4 [JWDJ] 2016-06-22
    if add_follow_score_markers:
        cmd.append('-EA')
    if str2bool(settings['barfly']):
        cmd.append('-BF')
    return cmd


# 1.3.6 [SS] 2014-11-24
def str2bool(v):
    ''' converts a string to a boolean if necessary'''
    if type(v) == str:
        return v.lower() in ('yes', 'true', 't', '1')
    else:
        return v

def fix_boxmarks_texts(abc):
    ''' Some Noteworthy Composer files use a special font where some note decorations are input
        as a single letter. Substitute real ABC decorations. '''
    decorations = {   # this list is not complete (eg. gliss decorations are currently left out)
        'c': '!arpeggio!',
        'h': 'T',
        'i': 'P',
        'j': 'P',
        'r': '!turn!',
        's': '!invertedturn!',
        't': 'u',
        'u': 'v',
        'x': '!<(!!<)!',
        'y': '!>(!!>)!',
        'z': '!>!', }
    abc = re.sub(r'"[^_]([%s])"' % ''.join(list(decorations)), lambda m: decorations[m.group(1)], abc)
    abc = abc.replace('"^tr"', 'T')
    return abc

def change_texts_into_chords(abc):
    ''' Change ABC fragments like "^G7" into "G7" by trying to identify strings that look like chords '''
    chord_types = 'm 7 m7 maj7 M7 6 m6 aug + aug7 dim dim7 9 m9 maj9 min Maj9 MAJ9 M9 11 dim9 sus sus4 Sus Sus4 sus9 7sus4 7sus9 5'.split()
    optional_chord_type = '(%s)?' % '|'.join(re.escape(c) for c in chord_types)
    return re.sub(r'(?<!\\)"[^_]([A-G][#b]? ?%s)(?<!\\)"' % optional_chord_type, r'"\1"', abc)

def NWCToXml(filepath, cache_dir, nwc2xml_path):
    global execmessages
    nwc_file_path = os.path.join(cache_dir, 'temp_nwc.nwc')
    xml_file_path = os.path.join(cache_dir, 'temp_nwc.xml')
    if os.path.exists(xml_file_path):
        os.remove(xml_file_path)
    shutil.copy(filepath, nwc_file_path)

    if not nwc2xml_path:
        if wx.Platform == "__WXMSW__":
            nwc2xml_path = os.path.join(cwd, 'bin', 'nwc2xml.exe')
        elif wx.Platform == "__WXMAC__":
            nwc2xml_path = os.path.join(cwd, 'bin', 'nwc2xml')
        else:
            nwc2xml_path = 'nwc2xml'

    #cmd = [nwc2xml_path, '--charset=ISO-8859-1', nwc_file_path]
    cmd = [nwc2xml_path, nwc_file_path]
    stdout_value, stderr_value, returncode = get_output_from_process(cmd)
    if returncode < 0:
        execmessages += '\n' + _('%(program)s exited abnormally (errorcode %(error)#8x)') % {'program': 'Nwc2xml', 'error': returncode & 0xffffffff}

    if not os.path.exists(xml_file_path) or returncode != 0:
        stderr_value = stderr_value.replace(os.path.dirname(nwc_file_path) + os.sep, '')  # simply any reference to the file path in the error message
        raise NWCConversionException(_('Error during conversion of %(filename)s: %(error)s' % {'filename': os.path.basename(filepath), 'error': stderr_value}))
    return xml_file_path


myRECORDSTOP = wx.NewEventType()
EVT_RECORDSTOP = wx.PyEventBinder(myRECORDSTOP, 1)
class RecordStopEvent(wx.PyCommandEvent):
    def __init__(self, eid, value=None):
        wx.PyCommandEvent.__init__(self, myRECORDSTOP, eid)
        self._value = value

    def GetValue(self):
        return self._value

gmidi_in = []

myMUSICUPDATEDONE = wx.NewEventType()
EVT_MUSIC_UPDATE_DONE = wx.PyEventBinder(myMUSICUPDATEDONE, 1)

class MusicPrintout(wx.Printout):
    def __init__(self, svg_files, zoom=1.0, title=None, painted_on_screen=False, can_draw_sharps_and_flats=True):
        wx.Printout.__init__(self, title=title or _('EasyABC music'))
        self.can_draw_sharps_and_flats = can_draw_sharps_and_flats
        self.svg_files = svg_files
        self.zoom = zoom
        self.painted_on_screen = painted_on_screen

    def HasPage(self, page):
        return page <= len(self.svg_files)

    def GetPageInfo(self):
        minPage = 1
        maxPage = len(self.svg_files)
        fromPage, toPage = minPage, maxPage
        return (minPage, maxPage, fromPage, toPage)

    def OnPrintPage(self, page_no):
        dc = self.GetDC()

        #-------------------------------------------
        # One possible method of setting scaling factors...

        svg = open(self.svg_files[page_no-1], 'rb').read()
        #new versions of abcm2ps adds a suffix 'in' to width and height
        #new versions of abcm2ps adds a suffix 'px' to width and height
        # 1.3.7.3 [JWDJ] use svg renderer to calculate width and height
        renderer = SvgRenderer(self.can_draw_sharps_and_flats, highlight_color='#000000')
        try:
            page = renderer.svg_to_page(svg)

            width = page.svg_width
            height = page.svg_height

            maxX = width
            maxY = height

            # Let's have at least 0 device units margin
            marginX = 0
            marginY = 0

            # Add the margin to the graphic size
            maxX += 2 * marginX
            maxY += 2 * marginY

            # Get the size of the DC in pixels
            (w, h) = dc.GetSize()

            # Calculate a suitable scaling factor
            scaleX = float(w) / maxX
            scaleY = float(h) / maxY

            # Use x or y scaling factor, whichever fits on the DC
            actualScale = min(scaleX, scaleY)

            # Calculate the position on the DC for centering the graphic
            posX = (w - (width * actualScale)) / 2.0
            #posY = (h - (height * actualScale)) / 2.0
            posY = 0

            # Set the scale and origin
            dc.SetUserScale(actualScale, actualScale)
            dc.SetDeviceOrigin(int(posX), int(posY))

            #-------------------------------------------
            if wx.Platform in ("__WXMSW__", "__WXMAC__") and (not self.painted_on_screen or True):
                # special case for windows since it doesn't support creating a GraphicsContext from a PrinterDC:
                dc.SetUserScale(actualScale/self.zoom, actualScale/self.zoom)
                renderer.zoom = self.zoom
                renderer.update_buffer(page)
                if self.painted_on_screen:
                    renderer.draw(page)
                    dc.DrawBitmap(renderer.buffer, 0, 0)
                else:
                    renderer.draw(page, dc=dc)
            else:
                renderer.zoom = 1.0
                renderer.update_buffer(page)
                renderer.draw(page, dc=dc)
        finally:
            renderer.destroy()
        return True

class MusicUpdateDoneEvent(wx.PyCommandEvent):
    def __init__(self, eid, value=None):
        wx.PyCommandEvent.__init__(self, myMUSICUPDATEDONE, eid)
        self._value = value

    def GetValue(self):
        return self._value

# 1.3.6 [SS] 2014-12-07 statusbar added
# 1.3.6.2 [SS] 2015-03-02 statusbar removed
class MusicUpdateThread(threading.Thread):
    def __init__(self, notify_window, settings, cache_dir):
        threading.Thread.__init__(self)
        self.daemon = True # 1.3.6.3 [JWdJ] to make sure the thread does not prevent EasyABC from exiting
        self.queue = Queue(maxsize=0) # 1.3.6.2 [JWdJ]
        self.notify_window = notify_window
        self.settings = settings
        self.cache_dir = cache_dir
        self.want_abort = False # 1.3.6.2 [JWdJ]

    # 1.3.6.2 [JWdJ] 2015-02 rewritten
    def run(self):
        while not self.want_abort:
            task = self.queue.get()
            self.queue.task_done()
            abc_tune = None
            try:
                abc_code, abc_header = task
                if not abc_code:
                    svg_files, error = [], None
                elif not 'K:' in abc_code:
                    raise Exception('K: field is missing')
                else:
                    # 1.3.6.3 [JWDJ] splitted pre-processing abc and generating svg
                    abc_code = process_abc_code(self.settings, abc_code, abc_header, minimal_processing=not self.settings.get('reduced_margins', True))
                    abc_tune = AbcTune(abc_code)
                    file_name = os.path.abspath(os.path.join(self.cache_dir, 'temp-%s-.svg' % abc_tune.tune_id))
                    # file_name = generate_temp_file_name(self.cache_dir, '-.svg', replace_ending='-001.svg')
                    svg_files, error = abc_to_svg(abc_code, self.cache_dir, self.settings, target_file_name=file_name)
            except Abcm2psException as e:
                # if abcm2ps crashes, then wait at least 10 seconds until next invocation
                svg_files, error = [], unicode(e)
                # wx.PostEvent(self.notify_window, MusicUpdateDoneEvent(-1, (svg_files, error)))
                # time.sleep(10.0)
                # continue
                # error_msg = traceback.format_exc()
                # print(error_msg)
                pass
            except Exception as e:
                svg_files, error = [], unicode(e)
                # error_msg = traceback.format_exc()
                # print(error_msg)
                pass
            svg_tune = SvgTune(abc_tune, svg_files, error)
            if application_running:
                wx.PostEvent(self.notify_window, MusicUpdateDoneEvent(-1, svg_tune))

    # 1.3.6.2 [JWdJ] 2015-02 rewritten
    def ConvertAbcToSvg(self, abc_code, abc_header, clear_queue=True):
        task = (abc_code, abc_header)
        if clear_queue:
            while not self.queue.empty():
                try:
                    self.queue.get(False)
                except Empty:
                    continue
                self.queue.task_done()
        self.queue.put(task)

    def abort(self):
        self.want_abort = True


# p09 new class for playing midi files if self.mc is not working 2014-10-14
# 1.3.6.3 [JWdJ] midithread extended so it works the same as the svg-thread
class MidiThread(threading.Thread):
    ''' This is how python runs a separate thread'''
    def __init__(self, settings):
        threading.Thread.__init__(self)
        self.daemon = True
        self.queue = Queue(maxsize=0) # 1.3.6.3 [JWdJ]
        self.settings = settings
        self.__want_abort = False # 1.3.6.3 [JWdJ]
        self.start()
        self.__is_busy = False

    def run(self):
        while not self.__want_abort:
            self.__is_busy = False
            command, params = self.queue.get()
            self.__is_busy = True
            midiplayer_path = params[0]
            midi_file = params[1]
            midiplayer_parameters = params[2].split()
            # 1.3.6.2 [SS] sleep no longer needed. abcToMidi not run as a
            # separate thread anymore.
            #time.sleep(0.5) # give abc2midi a chance to complete 2014-10-26 [SS]
            # 1.3.6.3 [SS] 2015-04-29
            # 1.3.6.3 [SS] 2015-05-08
            c = [midiplayer_path, midi_file] + midiplayer_parameters
            #note this is not the same as
            #c = [midiplayer_path, midi_file, midiplayer_parameters]
            try:
                start_process(c)
            except Exception as e:
                pass
                # print(e)
            self.queue.task_done()

    #p09 new function for playing midi files as a last resort 2014-10-14 [SS]
    def play_midi(self, midi_file):
        global execmessages
        # p09 an option in case you have trouble playing midi files.
        midiplayer_path = self.settings['midiplayer_path']
        # [SS] 2015-04-29
        midiplayer_params = self.settings['midiplayer_parameters']
        if midiplayer_path:
            execmessages += '\ncalling ' + midiplayer_path #1.3.6 [SS]
            self.queue_task('play', midiplayer_path, midi_file, midiplayer_params)

    def clear_queue(self):
        while not self.queue.empty():
            try:
                self.queue.get(False)
            except Empty:
                continue
            self.queue.task_done()

    def queue_task(self, command, *args):
        task = (command, args)
        self.queue.put(task)

    def abort(self):
        self.__want_abort = True

    @property
    def is_busy(self):
        return self.__is_busy


class RecordThread(threading.Thread):
    def __init__(self, notify_window, midi_in_device_ID, midi_out_device_ID=None, metre_1=3, metre_2=4, bpm=70):
        global gmidi_in
        threading.Thread.__init__(self)
        self._notify_window = notify_window
        self._want_abort = 0
        self.bpm = bpm
        self.metre_1 = metre_1
        self.metre_2 = metre_2
        self.midi_in = pypm.Input(midi_in_device_ID)
        if midi_out_device_ID is None:
            self.midi_out = None
        else:
            self.midi_out = pypm.Output(midi_out_device_ID, 0)
        gmidi_in.append(self.midi_in)
        gmidi_in.append(self.midi_out)
        self.notes = []
        self.is_running = False
        self.tick1 = wx_sound(os.path.join(cwd, 'sound', 'tick1.wav'))
        self.tick2 = wx_sound(os.path.join(cwd, 'sound', 'tick2.wav'))

    def timedelta_microseconds(self, td):
        return td.seconds*1000000 + td.microseconds

    @property
    def beat_duration(self):
        return 1000000 * 60 / self.bpm  # unit is microseconds

    @property
    def midi_in_poll(self):
        if wx.Platform == "__WXMAC__":
            return self.midi_in.poll()
        else:
            return self.midi_in.Poll()

    def number_to_note(self, number):
        notes = ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b']
        return notes[number%12]


    def run(self):
        self.is_running = True
        NOTE_ON = 0x09
        NOTE_OFF = 0x08
        i = 0
        noteon_time = {}
        start_time = datetime.now()
        last_tick = datetime.now()
        wx.CallAfter(self.tick1.Play)
        time.sleep(0.002)
        try:
            while not self._want_abort:
                while not self.midi_in_poll and not self._want_abort:
                    time.sleep(0.00025)
                    if self.timedelta_microseconds(datetime.now() - start_time) / self.beat_duration > i:
                        last_tick = datetime.now()
                        if i % self.metre_1 == 0:
                            wx.CallAfter(self.tick1.Play)
                        else:
                            wx.CallAfter(self.tick2.Play)
                        i += 1 #FAU: 20210102: One tick was missing the first time so incrementing i after the tick

                time_offset = self.timedelta_microseconds(datetime.now() - start_time)
                if self.midi_in_poll:
                    if wx.Platform == "__WXMAC__":
                        data = self.midi_in.read(1)
                    else:
                        data = self.midi_in.Read(1) # read only 1 message at a time
                    if self.midi_out is not None:
                        if wx.Platform == "__WXMAC__":
                            self.midi_out.write(data)
                        else:
                            self.midi_out.Write(data)
                    cmd = data[0][0][0] >> 4
                    midi_note = data[0][0][1]
                    midi_note_velocity = data[0][0][2]
                    #print(self.number_to_note(midi_note), midi_note_velocity)
                    if cmd == NOTE_ON and midi_note_velocity > 0:
                        noteon_time[midi_note] = time_offset
                        #print('note-on', midi_note, float(time_offset)/self.beat_duration)
                    elif (cmd == NOTE_OFF or midi_note_velocity ==0) and midi_note in noteon_time:
                        start = float(noteon_time[midi_note]) / self.beat_duration
                        end = float(time_offset) / self.beat_duration
                        self.notes.append([midi_note, start, end])
                        #print('note-off', midi_note, float(time_offset)/self.beat_duration)


        finally:
            if wx.Platform == "__WXMAC__":
                self.midi_in.close()
            else:
                self.midi_in.Close()
            if self.midi_out is not None:
                if wx.Platform == "__WXMAC__":
                    self.midi_out.close()
                else:
                    self.midi_out.Close()
            self.is_running = False
        self.quantize()
        wx.PostEvent(self._notify_window, RecordStopEvent(-1, self.notes))

    def quantize_swinged_16th(self, start_time):
        quantize_time = 0.25  # 1/16th
        return round(start_time / quantize_time) * quantize_time

    def quantize_triplet(self, notes):
        if len(notes) < 4:
            return False

        tolerance = 0.07
        first_note_start = round(notes[0][1] / 0.25) * 0.25

        durations = [n2[1]-n1[1] for n1, n2 in zip(notes[:3], notes[1:4])]

        for total_len in [1.0, 0.5]:
            if abs(durations[0] - total_len/3) < tolerance and \
               abs(durations[1] - total_len/3) < tolerance and \
               abs(durations[2] - total_len/3) < tolerance and \
               frac_mod(first_note_start, total_len) < tolerance:  # make sure that the start is on beat (8th) triplets, or on an 8th for 16th triplets

                notes[0][1] = first_note_start             # start time
                notes[1][1] = notes[0][1] + total_len /3   # start time
                notes[2][1] = notes[1][1] + total_len /3   # start time

                notes[0][2] = notes[0][1] + total_len / 3  # end time
                notes[1][2] = notes[1][1] + total_len / 3  # end time
                notes[2][2] = notes[2][1] + total_len / 3  # end time

                return True
        return False

    def quantize(self):
        quantized_notes = []

        if self.notes:
            distance_from_beat = frac_mod(self.notes[0][1], 1.0)
            if distance_from_beat > 0.5:
                distance_from_beat = -(1.0 - distance_from_beat)
            for note in self.notes:
                note[1] -= distance_from_beat/2

        for n1, n2 in zip(self.notes[0:-1], self.notes[1:]):
            n1[2] = n2[1]  # end of first is set to start of next note

        while self.notes:
            if self.quantize_triplet(self.notes):
                quantized_notes.extend(self.notes[:3])
                self.notes = self.notes[3:]
            else:
                note, start, end = self.notes.pop(0)
                start = self.quantize_swinged_16th(start)
                quantized_notes.append((note, start, end))

        for n1, n2 in zip(self.notes[0:-1], self.notes[1:]):
            n1[2] = n2[1]  # end of first is set to start of next note

        # quantize the end of the last note so that it ends at an even bar
        if quantized_notes:
            if self.metre_2 == 4:
                bar_length = float(self.metre_1)
            elif self.metre_2 == 8:
                bar_length = float(self.metre_1) / 2
            else:
                raise Exception('unknown metre')
            (note, start, end) = quantized_notes.pop()
            end = (int(end / bar_length) + 1) * bar_length     # set the end to be at the end of the bar
            quantized_notes.append((note, start, end))

        self.notes = [Note(start, end, note) for (note, start, end) in quantized_notes]

    def abort(self):
        self._want_abort = True


class FieldReferenceTree(htl.HyperTreeList):

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.SUNKEN_BORDER,
                 agwStyle=wx.TR_HAS_BUTTONS | wx.TR_HAS_VARIABLE_ROW_HEIGHT | wx.TR_HIDE_ROOT | wx.TR_ROW_LINES):

        htl.HyperTreeList.__init__(self, parent, id, pos, size, style, agwStyle)
        self.AddColumn(_('Field'))
        self.AddColumn(_('Description'))
        self.SetMainColumn(0)
        self.root = self.AddRoot("Hidden root")

        if wx.Platform == "__WXMSW__":
            self.EnableSelectionVista(True)

        # 1.3.6.2 [JWDJ] moved get_sections to AbcStructure.get_sections
        from tune_elements import AbcStructure # 1.3.7.1 [JWDJ] 2016-1 because of translation this import has to be done as late as possible
        for (title, fields) in AbcStructure.get_sections(cwd):
            child = self.AppendItem(self.root, title)
            self.SetPyData(child, None)
            self.SetItemText(child, '', 1)
            for (field_name, description) in fields:
                child2 = self.AppendItem(child, field_name)
                self.SetPyData(child2, None)
                self.SetItemText(child2, description, 1)
        self.SetColumnWidth(0, 250)
        self.SetColumnWidth(1, 800)

        # 1.3.6.2 [JWDJ] moved get_sections to AbcStructure.get_sections

class IncipitsFrame(wx.Dialog):
    def __init__(self, parent, settings):
        self.settings = settings
        wx.Dialog.__init__(self, parent, wx.ID_ANY, _('Generate incipits file...'), wx.DefaultPosition, wx.Size(530, 260))
        self.SetBackgroundColour(dialog_background_colour)
        border = control_margin
        sizer = box1 = wx.GridBagSizer()
        lb1 = wx.StaticText(self, wx.ID_ANY, _('Number of bars to extract:'))
        lb2 = wx.StaticText(self, wx.ID_ANY, _('Maximum number of repeats to extract:'))
        lb3 = wx.StaticText(self, wx.ID_ANY, _('Maximum number of titles/subtitles to extract:'))
        lb4 = wx.StaticText(self, wx.ID_ANY, _('Fields to sort by (eg. T):'))
        lb5 = wx.StaticText(self, wx.ID_ANY, _('Number of rows per column:'))
        self.edNumBars       = wx.SpinCtrl(self, wx.ID_ANY, "", min=1, max=10, initial=self.settings.get('incipits_numbars', 2))
        self.edNumRepeats    = wx.SpinCtrl(self, wx.ID_ANY, "", min=1, max=10, initial=self.settings.get('incipits_numrepeats', 1))
        self.edNumTitles     = wx.SpinCtrl(self, wx.ID_ANY, "", min=0, max=10, initial=self.settings.get('incipits_numtitles', 1))
        self.edSortFields    = wx.TextCtrl(self, wx.ID_ANY, self.settings.get('incipits_sortfields', ''))
        self.chkTwoColumns   = wx.CheckBox(self, wx.ID_ANY, _('&Two column output'))
        self.edNumRows       = wx.SpinCtrl(self, wx.ID_ANY, "", min=1, max=40, initial=self.settings.get('incipits_rows', 10))
        self.chkTwoColumns.SetValue(self.settings.get('incipits_twocolumns', True))
        for c in [self.edNumBars, self.edNumRepeats, self.edNumTitles, self.edNumRows, self.edSortFields]:
            c.SetValue(c.GetValue()) # this seems to be needed on OSX

        sizer.Add(lb1,                  pos=(0,0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(self.edNumBars,       pos=(0,1), flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(lb2,                  pos=(1,0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(self.edNumRepeats,    pos=(1,1), flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(lb3,                  pos=(2,0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(self.edNumTitles,     pos=(2,1), flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(lb4,                  pos=(3,0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(self.edSortFields,    pos=(3,1), flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(self.chkTwoColumns,   pos=(4,1), flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(lb5,                  pos=(5,0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(self.edNumRows,       pos=(5,1), flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        # ok, cancel buttons
        self.ok = wx.Button(self, wx.ID_ANY, _('&Ok'))
        self.cancel = wx.Button(self, wx.ID_ANY, _('&Cancel'))
        self.ok.SetDefault()
        # 1.3.6.1 [JWdJ] 2015-01-30 Swapped next two lines so OK-button comes first (OK Cancel)
        if WX4:
            btn_box = wx.BoxSizer(wx.HORIZONTAL)
            btn_box.Add(self.ok, wx.ID_OK)
            btn_box.Add(self.cancel, wx.ID_CANCEL)
        else:
            btn_box = wx.BoxSizer(wx.HORIZONTAL)
            btn_box.Add(self.ok, wx.ID_OK, flag=wx.ALIGN_RIGHT)
            btn_box.Add(self.cancel, wx.ID_CANCEL, flag=wx.ALIGN_RIGHT)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(box1, flag=wx.ALL | wx.EXPAND, border=10)
        self.sizer.Add(btn_box, flag=wx.ALL | wx.ALIGN_RIGHT, border=10)
        self.SetAutoLayout(True)
        self.Centre()
        self.sizer.Fit(self)
        self.SetSizer(self.sizer)

        self.ok.Bind(wx.EVT_BUTTON, self.OnOk)
        self.cancel.Bind(wx.EVT_BUTTON, self.OnCancel)
        self.chkTwoColumns.Bind(wx.EVT_CHECKBOX, self.OnTwoColumns)
        self.GrayUngray()
        self.save_settings()

    def GrayUngray(self):
        self.edNumRows.Enable(self.chkTwoColumns.IsChecked())

    def OnTwoColumns(self, evt):
        self.GrayUngray()

    def save_settings(self):
        self.settings['incipits_numbars'] = self.edNumBars.GetValue()
        self.settings['incipits_numrepeats'] = self.edNumRepeats.GetValue()
        self.settings['incipits_numtitles'] = self.edNumTitles.GetValue()
        self.settings['incipits_sortfields'] = self.edSortFields.GetValue().strip()
        self.settings['incipits_twocolumns'] = self.chkTwoColumns.IsChecked()
        self.settings['incipits_rows'] = self.edNumRows.GetValue()
        if self.settings['incipits_rows'] <= 0:
            self.settings['incipits_rows'] = 1

    def OnOk(self, evt):
        self.save_settings()
        self.EndModal(wx.ID_OK)

    def OnCancel(self, evt):
        self.EndModal(wx.ID_CANCEL)


#p09 Abcm2psSettingsFrame dialog box has been replaced with a
#tabbed notebook so we have lots of room for adding more options.
#2014-10-14
class MyNoteBook(wx.Frame):
    ''' Settings Notebook '''
    def __init__(self, parent, settings, statusbar):
        wx.Frame.__init__(self, parent, wx.ID_ANY, _("Abc settings"), style=wx.DEFAULT_FRAME_STYLE, name='settingsbook')
        # Add a panel so it looks the correct on all platforms
        p = wx.Panel(self)
        nb = wx.Notebook(p)
        # 1.3.6.4 [SS] 2015-05-26 added statusbar
        abcsettings = AbcFileSettingsFrame(nb, settings, statusbar, parent.mc)
        abcm2pspage = MyAbcm2psPage(nb, settings, abcsettings)
        self.chordpage = MyChordPlayPage(nb, settings)
        self.voicepage = MyVoicePage(nb, settings)
        # 1.3.6.1 [SS] 2015-02-02
        xmlpage    = MusicXmlPage(nb, settings)
        colorsettings = ColorSettingsFrame(nb, settings)
        nb.AddPage(abcm2pspage, _("Abcm2ps"))
        self.chordpage_id = nb.PageCount
        nb.AddPage(self.chordpage, _("Abc2midi"))
        self.voicepage_id = nb.PageCount
        nb.AddPage(self.voicepage, _("Voices"))
        nb.AddPage(xmlpage, _("MusicXML"))
        nb.AddPage(abcsettings, _("File Settings"))
        nb.AddPage(colorsettings, _("Colors"))
        nb.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

        sizer = wx.BoxSizer()
        sizer.Add(nb, 1, wx.ALL|wx.EXPAND)
        p.SetSizer(sizer)
        sizer.Fit(self)

    def OnPageChanged(self, event):
        if event.GetSelection() == self.voicepage_id:
            self.voicepage.FillControls()
        elif event.GetSelection() == self.chordpage_id:
            self.chordpage.FillControls()
        event.Skip()


class AbcFileSettingsFrame(wx.Panel):
    # 1.3.6.4 [SS] 2015-05-26 added statusbar
    def __init__(self, parent, settings, statusbar, mc):
        wx.Panel.__init__(self, parent)
        self.settings = settings
        self.statusbar = statusbar
        self.mc = mc
        self.SetBackgroundColour(dialog_background_colour)
        border = control_margin

        PathEntry = namedtuple('PathEntry', 'name display_name tooltip add_default wildcard on_change')

        # 1.3.6.3 [JWDJ] 2015-04-27 replaced TextCtrl with ComboBox for easier switching of versions
        self.needed_path_entries = [
            PathEntry('abcm2ps', _('abcm2ps executable:'), _('This executable is used to display the music'), True, None, None),
            PathEntry('abc2midi', _('abc2midi executable:'), _('This executable is used to make the midi file'), True, None, None),
            PathEntry('abc2abc', _('abc2abc executable:'), _('This executable is used to transpose the music'), True, None, None),
            # 1.3.6.4 [SS] 2015-06-22
            PathEntry('midi2abc', _('midi2abc executable:'), _('This executable is used to disassemble the output midi file'), True, None, None),
            PathEntry('gs', _('ghostscript executable:'), _('This executable is used to create PDF files'), False, None, None),
            PathEntry('nwc2xml', _('nwc2xml executable:'), _('For NoteWorthy Composer - Windows only'), False, None, None),
            PathEntry('ffmpeg', _('ffmpeg executable:'), _('This executable is used to convert music to compressed formats'), False, None, None),
            PathEntry('midiplayer', _('midiplayer:'), _('Your preferred MIDI player'), False, None, self.midiplayer_changed),
            PathEntry('soundfont', _('SoundFont:'), _('Your preferred SoundFont (.sf2)'), False, 'SoundFont (*.sf2;*.sf3)|*.sf2;*.sf3', self.soundfont_changed)
        ]


        if wx.Platform == "__WXMSW__":
            self.exe_file_mask = '*.exe'
        else:
            self.exe_file_mask = '*'

        sizer = wx.GridBagSizer()
        if wx.Platform == "__WXMAC__":
            sizer.Add(wx.StaticText(self, wx.ID_ANY, _('File paths to required executables') + ':'), pos=(0,0), span=(0,2), flag=wx.ALL, border=border)
            r = 1
        else:
            r = 0

        self.browsebutton_to_control = {}
        self.browsebutton_to_wildcard = {}
        self.control_to_name = {}
        self.afterchanged = {}
        for entry in self.needed_path_entries:
            setting_name = '%s_path' % entry.name
            current_path = self.settings.get(setting_name, '')
            self.afterchanged[setting_name] = entry.on_change
            setting_name_choices = '%s_path_choices' % entry.name
            path_choices = self.settings.get(setting_name_choices, '').split('|')
            path_choices = self.keep_existing_paths(path_choices)
            path_choices = self.append_exe(current_path, path_choices)
            if entry.add_default:
                path_choices = self.append_exe(self.get_default_path(entry.name), path_choices)
            control = wx.ComboBox(self, wx.ID_ANY, size=wx.Size(450,22),choices=path_choices, style=wx.CB_DROPDOWN)
            # [SS] 1.3.6.4 2015-12-23
            if current_path:
                control.SetValue(current_path)
            control.Bind(wx.EVT_TEXT, self.OnChangePath, control)

            self.control_to_name[control] = entry.name
            if entry.tooltip:
                control.SetToolTip(wx.ToolTip(entry.tooltip))

            browse_button = wx.Button(self, wx.ID_ANY, _('Browse...'))
            self.browsebutton_to_control[browse_button] = control
            self.browsebutton_to_wildcard[browse_button] = entry.wildcard
            sizer.Add(wx.StaticText(self, wx.ID_ANY, entry.display_name), pos=(r,0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
            sizer.Add(control, pos=(r,1), flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
            sizer.Add(browse_button, pos=(r,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

            browse_button.Bind(wx.EVT_BUTTON, self.OnBrowse, browse_button)

            r += 1

        sizer.AddGrowableCol(1)

        if wx.Platform == "__WXMAC__":
            box2 = sizer
        else:
            box2 = wx.StaticBoxSizer(wx.StaticBox(self, wx.ID_ANY, _("File paths to required executables")), wx.VERTICAL)
            box2.Add(sizer, flag=wx.ALL | wx.EXPAND)

        self.chkIncludeHeader = wx.CheckBox(self, wx.ID_ANY, _('Include file header when rendering tunes'))

        # 1.3.6.3 [SS] 2015-04-29
        extraplayerparam = wx.StaticText(self, wx.ID_ANY, _("Extra MIDI player parameters"))
        self.extras = wx.TextCtrl(self, wx.ID_ANY, size=(200, 22))

        midiplayer_params_sizer = wx.GridBagSizer()
        midiplayer_params_sizer.Add(self.chkIncludeHeader, pos=(0,0), span=(0,2), flag=wx.ALL, border=border)
        midiplayer_params_sizer.Add(extraplayerparam, pos=(1,0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        midiplayer_params_sizer.Add(self.extras, pos=(1,1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        self.restore_settings = wx.Button(self, wx.ID_ANY, _('Restore settings')) # 1.3.6.3 [JWDJ] 2015-04-25 renamed
        check_toolTip = _('Restore default file paths to abcm2ps, abc2midi, abc2abc, ghostscript when blank')
        self.restore_settings.SetToolTip(wx.ToolTip(check_toolTip))

        # build settings dialog with the previously defined box
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(box2, flag=wx.ALL | wx.EXPAND, border=10)
        # 1.3.6.1 [SS] 2015-01-28
        self.sizer.Add(midiplayer_params_sizer, flag=wx.ALL | wx.EXPAND, border=border)
        self.sizer.Add(self.restore_settings, flag=wx.ALL | wx.ALIGN_RIGHT, border=border)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)
        self.Centre()
        self.sizer.Fit(self)

        self.chkIncludeHeader.SetValue(self.settings.get('abc_include_file_header', True))
        self.extras.SetValue(self.settings.get('midiplayer_parameters', ''))

        # 1.3.6.1 [SS] 2015-01-28
        self.chkIncludeHeader.Bind(wx.EVT_CHECKBOX, self.On_Chk_IncludeHeader, self.chkIncludeHeader)
        # 1.3.6.3 [SS] 2015-04-29
        self.extras.Bind(wx.EVT_TEXT, self.On_extra_midi_parameters, self.extras)

        self.restore_settings.Bind(wx.EVT_BUTTON, self.OnRestoreSettings, self.restore_settings)

    def OnBrowse(self, evt):
        control = self.browsebutton_to_control[evt.EventObject]
        wildcard = self.browsebutton_to_wildcard[evt.EventObject]
        if (wildcard is None):
            wildcard = self.exe_file_mask
        path = control.GetValue()
        default_dir, default_file = os.path.split(path) # 1.3.6.3 [JWDJ] uses current folder as default
        dlg = wx.FileDialog(
            self, message=_("Choose a file"), defaultDir=default_dir, defaultFile=default_file, wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_CHANGE_DIR )
        try:
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                control.SetValue(path)
                if wx.Platform != "__WXMSW__":
                    # 1.3.6.4 [SS] 2015-06-23
                    self.change_path_for_control(control, path)  # 1.3.6.4 [JWDJ] 2015-06-23 in case control.SetValue(path) does not trigger OnChangePath
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window

    def OnChangePath(self, evt):
        if wx.Platform == "__WXMAC__":
            self.statusbar.SetStatusText('Updating path') # for Mac-users to see
        control = evt.EventObject
        path = evt.String
        self.change_path_for_control(control, path)

    def change_path_for_control(self, control, path):
        name = self.control_to_name[control]
        setting_name = '%s_path' % name
        self.settings[setting_name] = path
        if isinstance(control, wx.ComboBox):
            setting_name_choices = '%s_path_choices' % name
            paths = self.append_exe(path, control.Items)
            self.settings[setting_name_choices] = '|'.join(paths)
        # 1.3.6.4 [SS] 2015-05-26
        self.statusbar.SetStatusText(setting_name + ' was updated to '+ path)
        on_changed = self.afterchanged.get(setting_name)
        if on_changed is not None:
            on_changed(path)

    def midiplayer_changed(self, path):
        app = wx.GetApp()
        app.frame.update_play_button() # 1.3.6.3 [JWDJ] 2015-04-21 playbutton enabling centralized

    def soundfont_changed(self, sf2_path):
        try:
            if os.path.exists(sf2_path):
                wait = wx.BusyCursor()
                self.mc.set_soundfont(sf2_path)         # load another sound font
                del wait
        except:
            pass

    def On_Chk_IncludeHeader(self, event):
        self.settings['abc_include_file_header'] = self.chkIncludeHeader.GetValue()

    # [SS] 2015-04-29
    def On_extra_midi_parameters(self, event):
        self.settings['midiplayer_parameters'] = self.extras.GetValue()

    def OnRestoreSettings(self, event):
        # 1.3.6.1 [SS] 2015-02-03
        result = wx.MessageBox(_("This button will restore some of the paths to the executables (abcmp2s, abc2midi, etc.) to "
        "their defaults. In order that the program knows which paths to restore, you need to make those paths blank prior to continuing. "
        "You can do this by selecting the entry box, cntr-A to select all and cntr-X to delete. "
        "If this was not done, click Cancel first and then try again."),
                               _("Proceed?"), wx.ICON_QUESTION | wx.OK | wx.CANCEL)
        if result == wx.OK:
            for entry in self.needed_path_entries:
                setting_name = '%s_choices' % entry.name
                if setting_name in self.settings:
                    del self.settings[setting_name] # 1.3.6.3 [JWDJ] clean up unwanted paths

            frame = app._frames[0]
            frame.restore_settings()
            frame.settingsbook.Show(False)
            frame.settingsbook.Destroy()
            frame.settingsbook = MyNoteBook(self, self.settings, self.statusbar)
            frame.settingsbook.Show()

    def append_exe(self, path, paths):
        if path and not path in paths and os.path.isfile(path) and os.access(path, os.X_OK):
            paths.append(path)
        return paths

    def keep_existing_paths(self, paths):
        result = []
        for path in paths:
            if path and os.path.exists(path):
                result.append(path)
        return result

    def get_default_path(self, executable):
        if wx.Platform == "__WXMSW__":
            return os.path.join(cwd, 'bin', '%s.exe' % executable)
        elif wx.Platform == "__WXMAC__":
            return os.path.join(cwd, 'bin', executable)
        else:
            return os.path.join(cwd, 'bin', executable)


# p09 this was derived from the Abcm2psSettingsFrame. Now it is a separate page in the
# wx.notebook. 2014-10-14 [SS]
class MyChordPlayPage (wx.Panel):
    def __init__(self, parent, settings):
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour(dialog_background_colour) # 1.3.6.3 [JWDJ] 2014-04-28 same background for all tabs
        gridsizer = wx.FlexGridSizer(20, 4, 2, 2)
        # midi_box to set default instrument for playback
        midi_box = wx.GridBagSizer()
        border = control_margin
        self.settings = settings

        # 1.3.6.4 [SS] 2015-05-28 shrunk width from 250 to 200
        self.cmbMidiProgram = wx.ComboBox(self, wx.ID_ANY, choices=[], size=(200, 26), style=wx.CB_DROPDOWN | wx.CB_READONLY)
        #1.3.6.4 [SS] 2015-07-08
        self.sliderVol = wx.Slider(self, value=default_midi_volume, minValue=0, maxValue=127,
                                size=(128, -1), style=wx.SL_HORIZONTAL)
        self.Voltxt = wx.StaticText(self, wx.ID_ANY, " ")

        self.cmbMidiChordProgram = wx.ComboBox(self, wx.ID_ANY, choices=[], size=(200, 26), style=wx.CB_DROPDOWN | wx.CB_READONLY)
        #1.3.6.4 [SS] 2015-06-07
        self.sliderChordVol = wx.Slider(self, value=default_midi_volume, minValue=0, maxValue=127,
                                size=(128, -1), style=wx.SL_HORIZONTAL)
        self.ChordVoltxt = wx.StaticText(self, wx.ID_ANY, " ")

        self.cmbMidiBassProgram = wx.ComboBox(self, wx.ID_ANY, choices=[], size=(200, 26), style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.sliderBassVol = wx.Slider(self, value=default_midi_volume, minValue=0, maxValue=127,
                                size=(128, -1), style=wx.SL_HORIZONTAL)
        self.BassVoltxt = wx.StaticText(self, wx.ID_ANY, " ")

        #1.3.6.4 [SS] 2015-06-10
        self.sliderbeatsperminute = wx.Slider(self, value=120, minValue=60, maxValue=240,
                                size=(80, -1), style=wx.SL_HORIZONTAL)
        self.slidertranspose = wx.Slider(self, value=0, minValue=-11, maxValue=11,
                                size=(80, -1), style=wx.SL_HORIZONTAL)
        self.slidertuning = wx.Slider(self, value=440, minValue=415, maxValue=466,
                                size=(80, -1), style=wx.SL_HORIZONTAL)
        self.beatsperminutetxt = wx.StaticText(self, wx.ID_ANY, " ")
        self.transposetxt      = wx.StaticText(self, wx.ID_ANY, " ")
        self.tuningtxt         = wx.StaticText(self, wx.ID_ANY, " ")

        #1.3.6 [SS] 2014-11-21
        self.chkPlayChords = wx.CheckBox(self, wx.ID_ANY, _('Play chords'))
        self.nodynamics = wx.CheckBox(self, wx.ID_ANY, _('Ignore Dynamics'))
        self.nofermatas = wx.CheckBox(self, wx.ID_ANY, _('Ignore Fermatas'))
        self.nograce    = wx.CheckBox(self, wx.ID_ANY, _('No Grace Notes'))
        self.barfly     = wx.CheckBox(self, wx.ID_ANY, _('Barfly Mode'))
        self.midi_intro = wx.CheckBox(self, wx.ID_ANY, _('Count in'))

        #1.3.6 [SS] 2014-11-26
        gchordtxt = wx.StaticText(self, wx.ID_ANY, _("gchord pattern"))
        self.gchordcombo = wx.ComboBox(self, wx.ID_ANY, 'default', (-1, -1), (128, -1), [], wx.CB_DROPDOWN)
        gchordchoices = ['default', 'f', 'fzfz', 'gi', 'gihi', 'f4c2', 'ghihgh', 'g2hg2h']
        self.SetGchordChoices(gchordchoices)

        midi_box.Add(wx.StaticText(self, wx.ID_ANY, _('Instrument for playback') + ': '), pos=(0,0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.sliderVol, pos=(0,2), flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.Voltxt, pos=(0,3), flag=wx.ALL| wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.cmbMidiProgram, pos=(0,1), flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(wx.StaticText(self, wx.ID_ANY, _("Instrument for chord's playback") + ': '), pos=(1,0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.cmbMidiChordProgram, pos=(1,1), flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.sliderChordVol, pos=(1,2), flag=wx.ALL| wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.ChordVoltxt, pos=(1,3), flag=wx.ALL| wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(wx.StaticText(self, wx.ID_ANY, _("Instrument for bass chord's playback") + ': '), pos=(2,0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.cmbMidiBassProgram, pos=(2,1), flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.sliderBassVol, pos=(2,2), flag=wx.ALL| wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.BassVoltxt, pos=(2,3), flag=wx.ALL| wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)

        # 1.3.6.4 [SS] 2015-06-10
        midi_box.Add(wx.StaticText(self, wx.ID_ANY, _("Default Tempo") + ': '), pos=(3,0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.sliderbeatsperminute, pos=(3,1), flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.beatsperminutetxt, pos=(3,2), flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(wx.StaticText(self, wx.ID_ANY, _("Transposition") + ': '), pos=(4,0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.slidertranspose, pos=(4,1), flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.transposetxt, pos=(4,2), flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(wx.StaticText(self, wx.ID_ANY, _("Tuning") + ': '), pos=(5,0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.slidertuning, pos=(5,1), flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.tuningtxt, pos=(5,2), flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)

        midi_box.Add(self.chkPlayChords, pos=(6,0), flag=wx.ALL | wx.EXPAND, border=border)
        midi_box.Add(self.nodynamics, pos=(6,1), flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.nofermatas, pos=(7,0), flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.nograce, pos=(7,1), flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.barfly, pos=(8,0), flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.midi_intro, pos=(8,1), flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(gchordtxt, pos=(9,0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.gchordcombo, pos=(9,1), flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)

        self.chkPlayChords.SetValue(self.settings.get('play_chords', False))
        self.slidertranspose.SetValue(self.settings.get('transposition', 0))
        self.transposetxt.SetLabel(str(self.settings.get('transposition', 0)))
        self.slidertuning.SetValue(self.settings.get('tuning', 440))
        self.tuningtxt.SetLabel(str(self.settings.get('tuning', 440)))
        self.sliderVol.SetValue(int(self.settings.get('melodyvol', default_midi_volume)))
        self.Voltxt.SetLabel(str(self.settings.get('melodyvol', default_midi_volume)))
        self.sliderChordVol.SetValue(int(self.settings.get('chordvol', default_midi_volume)))
        self.ChordVoltxt.SetLabel(str(self.settings.get('chordvol', default_midi_volume)))
        self.sliderBassVol.SetValue(int(self.settings.get('bassvol', default_midi_volume)))
        self.BassVoltxt.SetLabel(str(self.settings.get('bassvol', default_midi_volume)))
        self.nodynamics.SetValue(self.settings.get('nodynamics', False))
        self.nofermatas.SetValue(self.settings.get('nofermatas', False))
        self.nograce.SetValue(self.settings.get('nograce', False))
        self.barfly.SetValue(self.settings.get('barfly', True))
        # 1.3.6.4 [SS[ 2015-07-05
        self.midi_intro.SetValue(self.settings.get('midi_intro', False))
        # 1.3.6.4 [SS] 2015-06-10
        bpmtempo = self.settings.get('bpmtempo', 120)
        self.sliderbeatsperminute.SetValue(int(bpmtempo))
        self.beatsperminutetxt.SetLabel(str(bpmtempo))

        beatsperminute_toolTip = _('Quarter notes per minute')
        ChordVol_toolTip = _('Volume level for chordal accompaniment')
        BassVol_toolTip  = _('Volume level for bass accompaniment')
        barfly_toolTip = _('The Barfly stress model is enabled provided the rhythm designator (R:) is recognized')
        nodynamics_toolTip = _('Dynamic markings like ff mp pp etc. are ignored if enabled')
        nofermatas_toolTip = _('Fermata markings are ignored if enabled')
        nograce_toolTip = _('Grace notes are ignored if enabled')
        transpose_toolTip = _('Transpose by the number of semitones')
        tuning_toolTip = _('Frequency of A in Hz')
        count_toolTip  = _('Two rest bars before music starts')
        vol_toolTip = _('Volume of melody line if the tune does not have any voices')

        self.sliderbeatsperminute.SetToolTip(wx.ToolTip(beatsperminute_toolTip))
        self.sliderChordVol.SetToolTip(wx.ToolTip(ChordVol_toolTip))
        self.sliderBassVol.SetToolTip(wx.ToolTip(BassVol_toolTip))
        self.nodynamics.SetToolTip(wx.ToolTip(nodynamics_toolTip))
        self.nofermatas.SetToolTip(wx.ToolTip(nofermatas_toolTip))
        self.nograce.SetToolTip(wx.ToolTip(nograce_toolTip))
        self.barfly.SetToolTip(wx.ToolTip(barfly_toolTip))
        self.midi_intro.SetToolTip(wx.ToolTip(count_toolTip))
        self.slidertranspose.SetToolTip(wx.ToolTip(transpose_toolTip))
        self.slidertuning.SetToolTip(wx.ToolTip(tuning_toolTip))
        self.sliderVol.SetToolTip(wx.ToolTip(vol_toolTip))

        #1.3.6 [SS] 2014-11-24
        self.chkPlayChords.Bind(wx.EVT_CHECKBOX, self.OnPlayChords)
        self.nodynamics.Bind(wx.EVT_CHECKBOX, self.OnNodynamics)
        self.nofermatas.Bind(wx.EVT_CHECKBOX, self.OnNofermatas)
        self.nograce.Bind(wx.EVT_CHECKBOX, self.OnNograce)
        self.barfly.Bind(wx.EVT_CHECKBOX, self.OnBarfly)
        self.sliderbeatsperminute.Bind(wx.EVT_SCROLL, self.OnBeatsPerMinute)
        self.slidertranspose.Bind(wx.EVT_SCROLL, self.OnTranspose)
        self.slidertuning.Bind(wx.EVT_SCROLL, self.OnTuning)
        #1.3.6.4 [SS] 2015-06-07
        self.sliderChordVol.Bind(wx.EVT_SCROLL, self.OnChordVol)
        self.sliderBassVol.Bind(wx.EVT_SCROLL, self.OnBassVol)
        #1.3.6.4 [SS] 2015-07-05
        self.midi_intro.Bind(wx.EVT_CHECKBOX, self.OnMidiIntro)
        #1.3.6.4 [SS] 2015-07-09
        self.sliderVol.Bind(wx.EVT_SCROLL, self.OnMelodyVol)

        #1.3.6 [SS] 2014-11-26
        self.gchordcombo.Bind(wx.EVT_COMBOBOX, self.OnGchordSelection, self.gchordcombo)
        self.gchordcombo.Bind(wx.EVT_TEXT, self.OnGchordSelection, self.gchordcombo)
        self.gchordcombo.SetToolTip(wx.ToolTip(_('f = fundamental\nc = chord\nz = rest\n\nfor chord C:\nf -> C,,\nc -> [C,E,G]\ng -> C\nh -> E\ni -> G\nj -> B\nG -> C,,\nH -> E,,\nI -> G,,\nJ -> B,')))

        #1.3.6 [SS] 2014-11-15
        self.cmbMidiProgram.Bind(wx.EVT_COMBOBOX, self.OnMidi_Program)
        self.cmbMidiChordProgram.Bind(wx.EVT_COMBOBOX, self.On_midi_chord_program)
        self.cmbMidiBassProgram.Bind(wx.EVT_COMBOBOX, self.On_midi_bass_program)

        self.SetSizer(midi_box)
        self.SetAutoLayout(True)
        self.Fit()
        self.Layout()
        self.controls_initialized = False

    def FillControls(self):
        if self.controls_initialized:
            return

        instruments = general_midi_instruments
        self.cmbMidiProgram.Append(instruments)
        self.cmbMidiChordProgram.Append(instruments)
        self.cmbMidiBassProgram.Append(instruments)
        try:
            self.cmbMidiProgram.Select(self.settings.get('midi_program', default_midi_instrument))
            self.cmbMidiChordProgram.Select(self.settings.get('midi_chord_program', 25))
            self.cmbMidiBassProgram.Select(self.settings.get('midi_bass_program', 25))
        except:
            pass

        self.controls_initialized = True


    def OnPlayChords(self, evt):
        self.settings['play_chords'] = self.chkPlayChords.GetValue()

# 1.3.6 [SS] 2014-11-24
    def OnNodynamics(self, evt):
        self.settings['nodynamics'] = self.nodynamics.GetValue()

    def OnNofermatas(self, evt):
        self.settings['nofermatas'] = self.nofermatas.GetValue()

    def OnNograce(self, evt):
        self.settings['nograce'] = self.nograce.GetValue()

    def OnBarfly(self, evt):
        self.settings['barfly'] = self.barfly.GetValue()

# 1.3.6.4 [SS] 2015-07-05
    def OnMidiIntro(self, evt):
        self.settings['midi_intro'] = self.midi_intro.GetValue()

    def OnMidi_Program(self, evt):
        self.settings['midi_program'] = self.cmbMidiProgram.GetSelection()

    def On_midi_chord_program(self, evt):
        self.settings['midi_chord_program'] = self.cmbMidiChordProgram.GetSelection()

    def On_midi_bass_program(self, evt):
        self.settings['midi_bass_program'] = self.cmbMidiBassProgram.GetSelection()

# 1.3.6 [SS] 2014-11-26
    def SetGchordChoices(self, choices):
        ''' sets the gchord string choices in the gchord combo widget '''
        self.gchordcombo.Clear()
        for item in choices:
            self.gchordcombo.Append(item)

    def OnGchordSelection(self, evt):
        ''' saves the gchord string selection '''
        self.settings['gchord'] = self.gchordcombo.GetValue()

# 1.3.6.4 [SS] 2015-06-10
    def OnBeatsPerMinute(self, evt):
        self.settings['bpmtempo'] = str(self.sliderbeatsperminute.GetValue())
        self.beatsperminutetxt.SetLabel(str(self.settings['bpmtempo']))


# 1.3.6.3 [SS] 2015-03-19
    def OnTranspose(self, evt):
        self.settings['transposition'] = self.slidertranspose.GetValue()
        self.transposetxt.SetLabel(str(self.settings['transposition']))

# 1.3.6.3 [SS] 2015-03-19
    def OnTuning(self, evt):
        self.settings['tuning'] = self.slidertuning.GetValue()
        self.tuningtxt.SetLabel(str(self.settings['tuning']))

#1.3.6.4 [SS] 2015-06-07
    def OnChordVol(self, evt):
        self.settings['chordvol'] = self.sliderChordVol.GetValue()
        self.ChordVoltxt.SetLabel(str(self.sliderChordVol.GetValue()))

#1.3.6.4 [SS] 2015-06-07
    def OnBassVol(self, evt):
        self.settings['bassvol'] = self.sliderBassVol.GetValue()
        self.BassVoltxt.SetLabel(str(self.sliderBassVol.GetValue()))

#1.3.6.4 [SS] 2015-07-09
    def OnMelodyVol(self, evt):
        melodyvol = self.sliderVol.GetValue()
        self.settings['melodyvol'] = melodyvol
        self.Voltxt.SetLabel(str(melodyvol))


# New panel to be able to set MIDI settings for the different voices
class MyVoicePage(wx.Panel):
    def __init__(self, parent, settings):
        wx.Panel.__init__(self, parent)
        self.settings = settings
        self.SetBackgroundColour(dialog_background_colour)
        border = control_margin
        channel = 1
        self.controls_initialized = False

        # definition of box for voice 1 to 16 (MIDI is limited to 16 channels)
        self.cmbMidiProgramCh_list = {}
        self.sldMidiControlVolumeCh_list = {}
        self.textValueMidiControlVolumeCh_list = {}
        self.sldMidiControlPanCh_list = {}
        self.textValueMidiControlPanCh_list = {}
        self.chkPerVoice = wx.CheckBox(self, wx.ID_ANY, _('Separate defaults per voice'))
        separate_defaults_per_voice = settings.get('separate_defaults_per_voice', False)
        self.chkPerVoice.Value = separate_defaults_per_voice
        self.chkPerVoice.Bind(wx.EVT_CHECKBOX, self.OnToggleDefaultsPerVoice)
        midi_box = wx.GridBagSizer()
        midi_box.Add(wx.StaticText(self, wx.ID_ANY, _('Default instrument:')), pos=(0,1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(wx.StaticText(self, wx.ID_ANY, _('Main Volume:')), pos=(0,3), span=(0,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(wx.StaticText(self, wx.ID_ANY, _('L/R Balance:')), pos=(0,6), span=(0,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        # For each of the 16th voice, instrument, volume and balance can be set separately
        if PY3:
            instrument_choices = []  # instruments fill be filled when tab is selected to speed up ABC settings
        else:
            instrument_choices = general_midi_instruments
        controls = []
        for channel in range(1, 16+1):
            cmbMidiProgram = wx.ComboBox(self, wx.ID_ANY, choices=instrument_choices, size=(200, 26),
                                                            style=wx.CB_READONLY)
            controls.append(cmbMidiProgram)
            self.cmbMidiProgramCh_list[channel] = cmbMidiProgram
            volumeSlider = wx.Slider(self, value=default_midi_volume, minValue=0, maxValue=127,
                                                                size=(80, -1), style=wx.SL_HORIZONTAL)
            # A text field is added to show value of slider as activating option SL_LABELS will show to many information
            self.sldMidiControlVolumeCh_list[channel] = volumeSlider
            controls.append(volumeSlider)

            volumeText = wx.StaticText(self, wx.ID_ANY, str(default_midi_volume), style=wx.ALIGN_RIGHT |
                                                                wx.ST_NO_AUTORESIZE, size=(30, 20))
            self.textValueMidiControlVolumeCh_list[channel] = volumeText

            panSlider = wx.Slider(self, value=default_midi_pan, minValue=0, maxValue=127,
                                                                size=(80, -1), style=wx.SL_HORIZONTAL)
            self.sldMidiControlPanCh_list[channel] = panSlider
            controls.append(panSlider)

            # A text field is added to show value of slider as activating option SL_LABELS will show to many information
            panText = wx.StaticText(self, wx.ID_ANY, str(default_midi_pan), style=wx.ALIGN_RIGHT |
                                                                wx.ST_NO_AUTORESIZE, size=(30, 20))
            self.textValueMidiControlPanCh_list[channel] = panText

            midi_box.Add(wx.StaticText(self, wx.ID_ANY, _('Voice n.%d: ') % channel), pos=(channel,0),
                         flag=wx.ALIGN_CENTER_VERTICAL, border=border)
            midi_box.Add(cmbMidiProgram, pos=(channel,1), flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
            #3rd column (col=2) is unused on purpose to leave some space (maybe replaced with some other spacer option later on)
            midi_box.Add(volumeSlider, pos=(channel,3),
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
            midi_box.Add(volumeText, pos=(channel,4),
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
            #6th column (col=5) is unused on purpose to leave some space (maybe replaced with some other spacer option later on)
            midi_box.Add(panSlider, pos=(channel,6),
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
            midi_box.Add(panText, pos=(channel,7),
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
            #Some properties are added to the slider to be able to update the associated text field with value when slider is moved
            volumeSlider.currentchannel=channel
            volumeSlider.Bind(wx.EVT_SCROLL, self.OnVolumeSliderScroll)
            panSlider.currentchannel=channel
            panSlider.Bind(wx.EVT_SCROLL, self.OnPanSliderScroll)
            # Binding
            cmbMidiProgram.currentchannel=channel
            cmbMidiProgram.Bind(wx.EVT_COMBOBOX, self.OnProgramSelection)

        # reset buttons box
        self.reset = wx.Button(self, wx.ID_ANY, _('&Reset'))
        controls.append(self.reset)
        if WX4:
            btn_box = wx.BoxSizer()
            btn_box.Add(self.reset)
        else:
            btn_box = wx.BoxSizer(wx.HORIZONTAL)
            btn_box.Add(self.reset, flag=wx.ALIGN_RIGHT)

        if not separate_defaults_per_voice:
            for control in controls:
                control.Disable() # IsEnabled = separate_defaults_per_voice
        self.voices_controls = controls

        reset_toolTip = _('The instrument for all voices is set to the default midi program. The volume and pan are set to 96/64.')
        self.reset.SetToolTip(wx.ToolTip(reset_toolTip))
        self.reset.Bind(wx.EVT_BUTTON, self.OnResetDefault)

        # add all box to the dialog to be displayed
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.chkPerVoice, flag=wx.ALL, border=border)
        self.sizer.Add(midi_box, flag=wx.ALL | wx.ALIGN_CENTER, border=border)
        self.sizer.Add(btn_box, flag=wx.ALL | wx.ALIGN_RIGHT, border=border)

        self.SetSizer(self.sizer)

        # try to set selection on previously defined instrument or default one or Piano
        self.midi_program_ch_list = ['midi_program_ch%d' % ch for ch in range(1, 16 + 1)]

    def OnToggleDefaultsPerVoice(self, event):
        separate_defaults_per_voice = event.EventObject.GetValue()
        self.settings['separate_defaults_per_voice'] = separate_defaults_per_voice
        controls = self.voices_controls
        if separate_defaults_per_voice:
            self.FillControls()
            for control in controls:
                control.Enable()
        else:
            for control in controls:
                control.Disable()

    def FillControls(self):
        if self.controls_initialized or not self.settings.get('separate_defaults_per_voice', False):
            return

        instruments = general_midi_instruments
        for channel in range(1, 16+1):
            if PY3:
                self.cmbMidiProgramCh_list[channel].Append(instruments)
            try:
                setting_name = self.midi_program_ch_list[channel-1]
                midi_info = self.settings.get(setting_name)
                if midi_info is None:
                    midi_info = [self.settings.get('midi_program', default_midi_instrument), default_midi_volume, default_midi_pan]
                self.cmbMidiProgramCh_list[channel].Select(midi_info[0])
                self.sldMidiControlVolumeCh_list[channel].SetValue(midi_info[1])
                self.textValueMidiControlVolumeCh_list[channel].SetLabel(str(midi_info[1]))
                self.sldMidiControlPanCh_list[channel].SetValue(midi_info[2])
                self.textValueMidiControlPanCh_list[channel].SetLabel(str(midi_info[2]))
            except:
                pass

        self.controls_initialized = True

    def OnProgramSelection(self, evt):
        obj = evt.GetEventObject()
        self.update_setting_for_channel(obj.currentchannel)

    def OnVolumeSliderScroll(self, evt):
        obj = evt.GetEventObject()
        val = obj.GetValue()
        channel = obj.currentchannel
        self.textValueMidiControlVolumeCh_list[channel].SetLabel("%d" % val)
        self.update_setting_for_channel(channel)

    def OnPanSliderScroll(self, evt):
        obj = evt.GetEventObject()
        val = obj.GetValue()
        channel = obj.currentchannel
        self.textValueMidiControlPanCh_list[channel].SetLabel("%d" % val)
        self.update_setting_for_channel(channel)

    def update_setting_for_channel(self, channel):
        self.settings[self.midi_program_ch_list[channel-1]] = [self.cmbMidiProgramCh_list[channel].GetSelection(),
                                                               self.sldMidiControlVolumeCh_list[channel].GetValue(),
                                                               self.sldMidiControlPanCh_list[channel].GetValue()]


    def OnResetDefault(self, evt):
        try:
            for channel in range(1, 16+1):
                self.cmbMidiProgramCh_list[channel].Select(self.settings.get('midi_program', default_midi_instrument))
                self.sldMidiControlVolumeCh_list[channel].SetValue(default_midi_volume)
                self.textValueMidiControlVolumeCh_list[channel].SetLabel(str(default_midi_volume))
                self.sldMidiControlPanCh_list[channel].SetValue(default_midi_pan)
                self.textValueMidiControlPanCh_list[channel].SetLabel(str(default_midi_pan))

                self.settings[self.midi_program_ch_list[channel-1]] = [self.cmbMidiProgramCh_list[channel].GetSelection(),
                                                                       self.sldMidiControlVolumeCh_list[channel].GetValue(),
                                                                       self.sldMidiControlPanCh_list[channel].GetValue()]
        except:
            pass





class MidiSettingsFrame(wx.Dialog):
    def __init__(self, parent, settings):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, _('Midi device settings'), wx.DefaultPosition, wx.Size(130, 80))
        self.settings = settings
        self.SetBackgroundColour(dialog_background_colour)
        border = control_margin
        sizer = wx.GridBagSizer(0, 0)
        sizer.Add(wx.StaticText(self, wx.ID_ANY, _('Input device')), wx.GBPosition(0, 0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(wx.StaticText(self, wx.ID_ANY, _('Output device')), wx.GBPosition(1, 0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        inputDevices = [_('None')]
        inputDeviceIDs = [None]
        outputDevices = [_('None')]
        outputDeviceIDs = [None]
        if 'pypm' in globals():
            if wx.Platform == "__WXMAC__":
                n = pypm.get_count()
            else:
                n = pypm.CountDevices()
        else:
            n = 0
        for i in range(n):
            if wx.Platform == "__WXMAC__":
                interface, name, input, output, opened = pypm.get_device_info(i)
                try:
                    name = str(name,'utf-8')
                except:
                    name = str(name,'mac_roman')
            else:
                interface, name, input, output, opened = pypm.GetDeviceInfo(i)
            if input:
                inputDevices.append(name)
                inputDeviceIDs.append(i)
            elif output:
                outputDevices.append(name)
                outputDeviceIDs.append(i)
        self.inputDeviceIDs = inputDeviceIDs
        self.outputDeviceIDs = outputDeviceIDs

        self.inputDevice = wx.ComboBox(self, wx.ID_ANY, size=(250, 22), choices=inputDevices, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.outputDevice = wx.ComboBox(self, wx.ID_ANY, size=(250, 22), choices=outputDevices, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.inputDevice.SetSelection(0)
        self.outputDevice.SetSelection(0)
        if settings.get('midi_device_in', None) in inputDeviceIDs:
            self.inputDevice.SetSelection(inputDeviceIDs.index(settings.get('midi_device_in', None)))
        if settings.get('midi_device_out', None) in outputDeviceIDs:
            self.outputDevice.SetSelection(outputDeviceIDs.index(settings.get('midi_device_out', None)))

        self.ok = wx.Button(self, wx.ID_ANY, _('&Ok'))
        self.cancel = wx.Button(self, wx.ID_ANY, _('&Cancel'))
        # 1.3.6.1 [JWdJ] 2015-01-30 Swapped next two lines so OK-button comes first (OK Cancel)
        if WX4:
            box = wx.BoxSizer()
            box.Add(self.ok, wx.ID_OK)
            box.Add(self.cancel, wx.ID_CANCEL)
        else:
            box = wx.BoxSizer(wx.HORIZONTAL)
            box.Add(self.ok, wx.ID_OK, flag=wx.ALIGN_RIGHT)
            box.Add(self.cancel, wx.ID_CANCEL, flag=wx.ALIGN_RIGHT)

        sizer.Add(self.inputDevice, wx.GBPosition(0, 1), flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(self.outputDevice, wx.GBPosition(1, 1), flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(box, wx.GBPosition(2, 0), (1, 2), flag=0 | wx.ALL | wx.ALIGN_RIGHT, border=border)
        self.ok.SetDefault()

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self.Centre()
        sizer.Fit(self)

        self.ok.Bind(wx.EVT_BUTTON, self.OnOk)
        self.cancel.Bind(wx.EVT_BUTTON, self.OnCancel)

    def OnOk(self, evt):
        self.settings['midi_device_in'] = self.inputDeviceIDs[self.inputDevice.GetSelection()]
        self.settings['midi_device_out'] = self.outputDeviceIDs[self.outputDevice.GetSelection()]
        self.EndModal(wx.ID_OK)

    def OnCancel(self, evt):
        self.EndModal(wx.ID_CANCEL)



# 1.3.6 [SS] 2014-12-04 2014-12-16
# For controlling the way abcm2ps runs
class MyAbcm2psPage(wx.Panel):
    # 1.3.6.1 [SS] 2015-02-02
    def __init__(self, parent, settings, abcsettingspage):
        wx.Panel.__init__(self, parent)
        self.settings = settings
        self.abcsettingspage = abcsettingspage
        self.SetBackgroundColour(dialog_background_colour)
        border = control_margin
        headingtxt = _('The options in this page controls how the music score is displayed.\n\n')
        heading = wx.StaticText(self, wx.ID_ANY, headingtxt)

        clean      = wx.StaticText(self, wx.ID_ANY, _("No page settings"))
        defaults   = wx.StaticText(self, wx.ID_ANY, _("EasyABC defaults"))
        numberbars = wx.StaticText(self, wx.ID_ANY, _("Include bar numbers"))
        refnumbers = wx.StaticText(self, wx.ID_ANY, _("Add X reference number"))
        nolyrics   = wx.StaticText(self, wx.ID_ANY, _("Suppress lyrics"))
        linends    = wx.StaticText(self, wx.ID_ANY, _("Ignore line ends"))
        leftmarg   = wx.StaticText(self, wx.ID_ANY, _("Left margin (cm)"))
        rightmarg  = wx.StaticText(self, wx.ID_ANY, _("Right margin (cm)"))
        topmarg    = wx.StaticText(self, wx.ID_ANY, _("Top margin (cm)"))
        botmarg = wx.StaticText(self, wx.ID_ANY, _("Bottom margin (cm)"))
        # 1.3.6.1 [SS] 2015-01-28
        pagewidth = wx.StaticText(self, wx.ID_ANY, _("Page width (cm)"))
        pageheight = wx.StaticText(self, wx.ID_ANY, _("Page height (cm)"))

        scalefact  = wx.StaticText(self, wx.ID_ANY, _("Scale factor (eg. 0.8)"))
        self.chkm2psclean = wx.CheckBox(self, wx.ID_ANY, '')
        self.chkm2psdef   = wx.CheckBox(self, wx.ID_ANY, '')
        self.chkm2psbar = wx.CheckBox(self, wx.ID_ANY, '')
        self.chkm2psref = wx.CheckBox(self, wx.ID_ANY, '')
        self.chkm2pslyr = wx.CheckBox(self, wx.ID_ANY, '')
        self.chkm2psend = wx.CheckBox(self, wx.ID_ANY, '')

        extras = wx.StaticText(self, wx.ID_ANY, _("Extra parameters"))
        self.extras = wx.TextCtrl(self, wx.ID_ANY, size=(350, 22))
        formatf = wx.StaticText(self, wx.ID_ANY, _("Format file"))
        # 1.3.6.4 [SS] 2015-09-11 2015-09-21
        try:
            self.format_choices = self.settings.get('abcm2ps_format_choices', '').split('|')
        except:
            self.format_choices = []
        # 1.3.6.4 [SS] 2015-09-11
        self.formatf  = wx.ComboBox(self, wx.ID_ANY, choices=self.format_choices, size = (350, -1), style=wx.CB_DROPDOWN)

        self.browsef = wx.Button(self, wx.ID_ANY, _('Browse...'), size = (-1, 22))

        self.leftmargin  = wx.TextCtrl(self, wx.ID_ANY, size=(55, 22))
        self.rightmargin = wx.TextCtrl(self, wx.ID_ANY, size=(55, 22))
        self.topmargin = wx.TextCtrl(self, wx.ID_ANY, size=(55, 22))
        self.botmargin = wx.TextCtrl(self, wx.ID_ANY, size=(55, 22))
        self.pagewidth = wx.TextCtrl(self, wx.ID_ANY, size=(55, 22))
        self.pageheight =wx.TextCtrl(self, wx.ID_ANY, size=(55, 22))

        # 1.3.6.1 [SS] 2015-12-28
        pagewidth_toolTip = _('The default is {0}').format('21.59')
        pageheight_toolTip = _('The default is {0}').format('27.94')
        leftmargin_toolTip = _('The default is {0}').format('1.78')
        rightmargin_toolTip = _('The default is {0}').format('1.78')
        topmargin_toolTip = _('The default is {0}').format('1.00')
        botmargin_toolTip = _('The default is {0}').format('1.00')
        extras_toolTip = _('Additional command line parameters to abcm2ps')
        formatf_toolTip = _('Right click the mouse to remove all choices')
        self.pagewidth.SetToolTip(wx.ToolTip(pagewidth_toolTip))
        self.pageheight.SetToolTip(wx.ToolTip(pageheight_toolTip))
        self.leftmargin.SetToolTip(wx.ToolTip(leftmargin_toolTip))
        self.rightmargin.SetToolTip(wx.ToolTip(rightmargin_toolTip))
        self.topmargin.SetToolTip(wx.ToolTip(topmargin_toolTip))
        self.botmargin.SetToolTip(wx.ToolTip(botmargin_toolTip))
        self.extras.SetToolTip(wx.ToolTip(extras_toolTip))
        self.formatf.SetToolTip(wx.ToolTip(formatf_toolTip))

        chkm2psdef_toolTip = _('Use the factory page settings of EasyABC')
        self.chkm2psdef.SetToolTip(wx.ToolTip(chkm2psdef_toolTip))
        chkm2psclean_toolTip = _('Do not add page settings')
        self.chkm2psclean.SetToolTip(wx.ToolTip(chkm2psclean_toolTip))

        self.chkm2psclean.SetValue(self.settings.get('abcm2ps_clean', False))
        self.chkm2psdef.SetValue(self.settings.get('abcm2ps_defaults'))
        self.chkm2psbar.SetValue(self.settings.get('abcm2ps_number_bars', False))
        self.chkm2psref.SetValue(self.settings.get('abcm2ps_refnumbers', False))
        self.chkm2pslyr.SetValue(self.settings.get('abcm2ps_no_lyrics', False))
        self.chkm2psend.SetValue(self.settings.get('abcm2ps_ignore_ends', False))
        self.leftmargin.SetValue(self.settings.get('abcm2ps_leftmargin', '1.78'))
        self.rightmargin.SetValue(self.settings.get('abcm2ps_rightmargin', '1.78'))
        self.topmargin.SetValue(self.settings.get('abcm2ps_topmargin', '1.0'))
        self.botmargin.SetValue(self.settings.get('abcm2ps_botmargin', '1.0'))
        # 1.3.6.1 [SS] 2015-01-28
        self.pagewidth.SetValue(self.settings.get('abcm2ps_pagewidth', '21.59'))
        self.pageheight.SetValue(self.settings.get('abcm2ps_pageheight', 27.94))
        self.extras.SetValue(self.settings.get('abcm2ps_extra_params', ''))
        self.formatf.SetValue(self.settings.get('abcm2ps_format_path', ''))

        self.chkm2psclean.Bind(wx.EVT_CHECKBOX, self.OnAbcm2psClean)
        self.chkm2psdef.Bind(wx.EVT_CHECKBOX, self.OnAbcm2psDefaults)
        self.chkm2psbar.Bind(wx.EVT_CHECKBOX, self.OnAbcm2psBar)
        self.chkm2pslyr.Bind(wx.EVT_CHECKBOX, self.OnAbcm2pslyrics)
        self.chkm2psref.Bind(wx.EVT_CHECKBOX, self.OnAbcm2psref)
        self.chkm2psend.Bind(wx.EVT_CHECKBOX, self.OnAbcm2psend)
        self.leftmargin.Bind(wx.EVT_TEXT, self.OnPSleftmarg, self.leftmargin)
        self.rightmargin.Bind(wx.EVT_TEXT, self.OnPSrightmarg, self.rightmargin)
        self.topmargin.Bind(wx.EVT_TEXT, self.OnPStopmarg, self.topmargin)
        self.botmargin.Bind(wx.EVT_TEXT, self.OnPSbotmarg, self.botmargin)
        # 1.3.6.1 [SS] 2015-01-28
        self.formatf.Bind(wx.EVT_TEXT, self.OnFormat, self.formatf)
        self.formatf.Bind(wx.EVT_RIGHT_DOWN, self.OnClean, self.formatf) #1.3.6.4
        self.extras.Bind(wx.EVT_TEXT, self.On_extra_params, self.extras)
        self.browsef.Bind(wx.EVT_BUTTON, self.OnBrowse_format, self.browsef)
        # 1.3.6.1 [SS] 2015-01-29
        self.pagewidth.Bind(wx.EVT_TEXT, self.OnPSpagewidth, self.pagewidth)
        self.pageheight.Bind(wx.EVT_TEXT, self.OnPSpageheight, self.pageheight)

        # 1.3.6 [SS] 2014-12-16
        # 1.3.6.3 [SS] 2015-03-15
        #fval = self.settings.get('abcm2ps_scale',0.9)
        self.scaleval = wx.TextCtrl(self, wx.ID_ANY, size=(50,22))
        self.scaleval.SetValue(self.settings.get('abcm2ps_scale',0.9))
        self.scaleval.SetToolTip(wx.ToolTip(_('Scales the separation between staff lines. Recommended value is {0}.'.format('0.80'))))

        # 1.3.6.2 [SS] 2015-04-21
        self.scaleval.Bind(wx.EVT_TEXT, self.OnPSScale, self.scaleval)

        grid_sizer = wx.GridBagSizer()
        grid_sizer.Add(heading, pos=(0,0), span=(1,7), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        grid_sizer.Add(clean, pos=(1,0), span=(1,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )
        grid_sizer.Add(self.chkm2psclean, pos=(1,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )

        grid_sizer.Add(defaults, pos=(1,4), span=(1,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )
        grid_sizer.Add(self.chkm2psdef, pos=(1,6), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )

        grid_sizer.Add(numberbars, pos=(3,0), span=(1,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )
        grid_sizer.Add(self.chkm2psbar, pos=(3,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )

        grid_sizer.Add(refnumbers, pos=(3,4), span=(1,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )
        grid_sizer.Add(self.chkm2psref, pos=(3,6), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )

        grid_sizer.Add(nolyrics, pos=(4,0), span=(1,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )
        grid_sizer.Add(self.chkm2pslyr, pos=(4,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )

        grid_sizer.Add(linends, pos=(4,4), span=(1,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )
        grid_sizer.Add(self.chkm2psend, pos=(4,6), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )

        self.grid_sizer_page_format = wx.GridBagSizer()
        self.grid_sizer_page_format.Add(leftmarg, pos=(0,0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )
        self.grid_sizer_page_format.Add(self.leftmargin, pos=(0,1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )

        self.grid_sizer_page_format.Add(rightmarg, pos=(0,3), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )
        self.grid_sizer_page_format.Add(self.rightmargin, pos=(0,4), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )

        self.grid_sizer_page_format.Add(topmarg, pos=(1,0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )
        self.grid_sizer_page_format.Add(self.topmargin, pos=(1,1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )

        self.grid_sizer_page_format.Add(botmarg, pos=(1,3), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )
        self.grid_sizer_page_format.Add(self.botmargin, pos=(1,4), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )

        self.grid_sizer_page_format.Add(pagewidth, pos=(2,0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )
        self.grid_sizer_page_format.Add(self.pagewidth, pos=(2,1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )

        self.grid_sizer_page_format.Add(pageheight, pos=(2,3), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )
        self.grid_sizer_page_format.Add(self.pageheight, pos=(2,4), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )

        self.grid_sizer_page_format.Add(scalefact, pos=(3,0), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )
        self.grid_sizer_page_format.Add(self.scaleval, pos=(3,1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )

        grid_sizer.Add(self.grid_sizer_page_format, pos=(2,1), span=(1,6), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )

        grid_sizer.Add(extras, pos=(5,0), span=(1,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )
        grid_sizer.Add(self.extras, pos=(5,2), span=(1,5), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )
        grid_sizer.Add(formatf, pos=(6,0), span=(1,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )
        grid_sizer.Add(self.formatf, pos=(6,2), span=(1,3), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )
        grid_sizer.Add(self.browsef, pos=(6,5), span=(1,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border )


        # 1.3.6.1 [SS] 2015-01-08
        if self.settings['abcm2ps_clean'] or self.settings['abcm2ps_defaults']:
            for sizeritem in self.grid_sizer_page_format.GetChildren():
                sizeritem.Show(False)
        else:
            for sizeritem in self.grid_sizer_page_format.GetChildren():
                sizeritem.Show(True)
        self.SetSizer(grid_sizer)
        self.SetAutoLayout(True)
        self.Fit()
        self.Layout()

    def OnAbcm2psClean(self, evt):
        self.settings['abcm2ps_clean'] = self.chkm2psclean.GetValue()
        if self.settings['abcm2ps_clean'] or self.settings['abcm2ps_defaults']:
        #    #self.box.Show(self.gridsizer3, show=False)
            for sizeritem in self.grid_sizer_page_format.GetChildren():
                sizeritem.Show(False)
        else:
            #self.box.Show(self.gridsizer3, show=True)
            for sizeritem in self.grid_sizer_page_format.GetChildren():
                sizeritem.Show(True)
        self.Layout()

    def OnAbcm2psDefaults(self, evt):
        self.settings['abcm2ps_defaults'] = self.chkm2psdef.GetValue()
        if self.settings['abcm2ps_clean'] or self.settings['abcm2ps_defaults']:
        #    self.box.Show(self.gridsizer3, show=False)
            for sizeritem in self.grid_sizer_page_format.GetChildren():
                sizeritem.Show(False)
        else:
        #    self.box.Show(self.gridsizer3, show=True)
            for sizeritem in self.grid_sizer_page_format.GetChildren():
                sizeritem.Show(True)
        self.Layout()

    def OnAbcm2psBar(self, evt):
        self.settings['abcm2ps_number_bars'] = self.chkm2psbar.GetValue()

    def OnAbcm2pslyrics(self, evt):
        self.settings['abcm2ps_no_lyrics'] = self.chkm2pslyr.GetValue()

    def OnAbcm2psref(self, evt):
        self.settings['abcm2ps_refnumbers'] = self.chkm2psref.GetValue()

    def OnAbcm2psend(self, evt):
        self.settings['abcm2ps_ignore_ends'] = self.chkm2psend.GetValue()

    # 1.3.6.2 [SS] 2015-03-15
    def OnPSScale(self, evt):
        val = self.scaleval.GetValue()
        m   = re.findall(r"\d+.\d+|\d+",val)
        if len(m) > 0 and 0.1 < float(val) < 1.5:
            self.settings['abcm2ps_scale'] = str(val)

    def OnPSleftmarg(self, evt):
        # 1.3.6.1 [SS] 2015-01-13
        val = self.leftmargin.GetValue()
        # extract only the number
        m   = re.findall(r"\d+.\d+|\d+",val)
        if len(m) > 0:
            val = str(m[0])
            self.settings['abcm2ps_leftmargin'] = val

    def OnPSrightmarg(self, evt):
        # 1.3.6.1 [SS] 2015-01-13
        val = self.rightmargin.GetValue()
        m   = re.findall(r"\d+.\d+|\d+",val)
        if len(m) > 0:
            val = str(m[0])
            self.settings['abcm2ps_rightmargin'] = val

    def OnPStopmarg(self, evt):
        # 1.3.6.1 [SS] 2015-01-13
        val = self.topmargin.GetValue()
        m   = re.findall(r"\d+.\d+|\d+",val)
        if len(m) > 0:
            val = str(m[0])
            self.settings['abcm2ps_topmargin'] = val

    def OnPSbotmarg(self, evt):
        # 1.3.6.1 [SS] 2015-01-13
        val = self.botmargin.GetValue()
        m   = re.findall(r"\d+.\d+|\d+",val)
        if len(m) > 0:
            val = str(m[0])
            self.settings['abcm2ps_botmargin'] = val

    # 1.3.6.1 [SS] 2015-01-28
    def OnPSpagewidth(self, evt):
        val = self.pagewidth.GetValue()
        m   = re.findall(r"\d+.\d+|\d+",val)
        if len(m) > 0:
            val = str(m[0])
            self.settings['abcm2ps_pagewidth'] = val

    def OnPSpageheight(self, evt):
        val = self.pageheight.GetValue()
        m   = re.findall(r"\d+.\d+|\d+",val)
        if len(m) > 0:
            val = str(m[0])
            self.settings['abcm2ps_pageheight'] = val

    def OnFormat(self, evt):
        path = evt.String
        self.set_format_path(path)
        # 1.3.6.4 [SS] 2015-09-11
        self.update_format_choices(path)
        # [SS] the SetItems does not work correctly in wxpython 2.7
        #self.formatf.SetItems(str(self.settings['abcm2ps_format_choices']))

    # 1.3.6.4 [SS] 2015-09-21
    def OnClean(self, evt):
        #print "right click"
        #if evt.ControlDown():
            #print "control down"
        result = wx.MessageBox(_("This will remove the selections in the combobox."), _("Proceed?"), wx.ICON_QUESTION | wx.YES | wx.NO)
        #print self.formatf.GetItems()
        if result == wx.YES:
            #self.formatf.Clear()
            self.formatf.SetItems([])
            self.settings['abcm2ps_format_choices'] = self.formatf.GetItems()


    def On_extra_params(self, evt):
        self.settings['abcm2ps_extra_params'] = self.extras.GetValue()

    def OnBrowse_format(self, evt):
        path = self.settings.get('abcm2ps_format_path', '')
        if not path:
            path = self.settings.get('previous_abcm2ps_format_path', '')
        default_dir, default_file = os.path.split(path)
        dlg = wx.FileDialog(
                self, message=_("Find PostScript format file"), defaultFile=default_file, defaultDir=default_dir, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_CHANGE_DIR )
        try:
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                self.formatf.SetValue(path)
                self.update_format_choices(path)
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window

    def update_format_choices(self, path):
        # 1.3.6.4 [SS] 2015-09-11
        if path and not path in self.format_choices and os.path.isfile(path) and os.access(path, os.R_OK):
            self.format_choices.append(path)
            self.settings['abcm2ps_format_choices'] = '|'.join(self.format_choices)
            if wx.Platform != "__WXMSW__":
                self.set_format_path(path)  # 1.3.6.4 [SS] 2015-09-17 in case control.SetValue(path) does not trigger OnChangePath

    def set_format_path(self, path):
        old_path = self.settings.get('abcm2ps_format_path', '')
        if old_path and path != old_path:
            self.settings['previous_abcm2ps_format_path'] = old_path
        self.settings['abcm2ps_format_path'] = path
        self.Parent.Parent.Parent.Parent.refresh_tunes()


class ColorSettingsFrame(wx.Panel):
    def __init__(self, parent, settings):
        wx.Panel.__init__(self, parent)
        self.settings = settings
        self.SetBackgroundColour(dialog_background_colour)
        border = control_margin

        grid_sizer = wx.GridBagSizer()

        notecolors    = wx.StaticText(self, wx.ID_ANY, _('Colors for note highlighting in music score'))
        editorcolors  = wx.StaticText(self, wx.ID_ANY, _('Colors of ABC code highlighting in editor'))

        note_highlight_color = self.settings.get('note_highlight_color', default_note_highlight_color)
        note_highlight_color_label = wx.StaticText(self, wx.ID_ANY, _("Note highlight color"))
        if PY3:
            self.note_highlight_color_picker = wx.ColourPickerCtrl(self, wx.ID_ANY, colour=wx.Colour(note_highlight_color))
        else:
            r = int(note_highlight_color[1:3], 16)
            g = int(note_highlight_color[3:5], 16)
            b = int(note_highlight_color[5:7], 16)
            self.note_highlight_color_picker = wx.ColourPickerCtrl(self, wx.ID_ANY, wx.Colour(r, g, b))

        note_highlight_follow_color = self.settings.get('note_highlight_follow_color', default_note_highlight_follow_color)
        note_highlight_follow_color_label = wx.StaticText(self, wx.ID_ANY, _("Note highlight color when follow score"))
        self.note_highlight_follow_color_picker = wx.ColourPickerCtrl(self, wx.ID_ANY, colour=wx.Colour(note_highlight_follow_color))

        grid_sizer.Add(notecolors,pos=(0,0),span=(1,10), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        
        grid_sizer.Add(note_highlight_color_label, pos=(1,1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        grid_sizer.Add(self.note_highlight_color_picker, pos=(1,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        grid_sizer.Add(note_highlight_follow_color_label, pos=(1,4), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        grid_sizer.Add(self.note_highlight_follow_color_picker, pos=(1,5), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        note_highlight_color_tooltip = _('Color of selected note')
        self.note_highlight_color_picker.SetToolTip(wx.ToolTip(note_highlight_color_tooltip))
        self.note_highlight_color_picker.Bind(wx.EVT_COLOURPICKER_CHANGED, self.OnNoteHighlightColorChanged)
        note_highlight_follow_color_tooltip = _('Color of currently playing note')
        self.note_highlight_follow_color_picker.SetToolTip(wx.ToolTip(note_highlight_follow_color_tooltip))
        self.note_highlight_follow_color_picker.Bind(wx.EVT_COLOURPICKER_CHANGED, self.OnNoteHighlightFollowColorChanged)

        self.style_labels = {
            'style_default_color':_("Default color"),
            'style_chord_color':_("Color of chords"),
            'style_bar_color':_("Color of bars"),
            'style_comment_color':_("Color of comment"),
            'style_specialcomment_color':_("Color of instructions/commands"),
            'style_fieldindex_color':_("Color of field index"),
            'style_field_color':_("Color of ABC fields"),
            'style_fieldvalue_color':_("Color of ABC fields value"),
            'style_embeddedfield_color':_("Color of embedded ABC fields"),
            'style_embeddedfieldvalue_color':_("Color of embedded ABC fields values"),
            'style_string_color':_("Color of string"),
            'style_lyrics_color':_("Color of lyrics"),
            'style_ornament_color':_("Color of ornament"),
            'style_ornamentplus_color':_("Color of ornament plus"),
            'style_ornamentexcl_color':_("Color of ornament excl"),
            'style_grace_color':_("Color of grace notes")
        }
        
        grid_sizer.Add(editorcolors,pos=(3,0),span=(1,10), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        i=4
        j=1
        self.color_picker = {}
        for key, label in self.style_labels.items():
            color = self.settings.get(key, default_style_color[key])
            color_text_label = wx.StaticText(self, wx.ID_ANY, label)
            self.color_picker[key] = wx.ColourPickerCtrl(self, wx.ID_ANY, colour=wx.Colour(color))
            grid_sizer.Add(color_text_label, pos=(i,j), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
            grid_sizer.Add(self.color_picker[key], pos=(i,j+1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
            self.color_picker[key].Bind(wx.EVT_COLOURPICKER_CHANGED, lambda evt, temp=key: self.OnFontColorChanged(evt,temp))
            if j>=7:
                i+=1
                j=1
            else:
                j+=3
        
        self.restore_color = wx.Button(self, wx.ID_ANY, _('Restore default colors'))
        check_toolTip = _('Restore default colors')
        self.restore_color.SetToolTip(wx.ToolTip(check_toolTip))
        
        grid_sizer.Add(self.restore_color, pos=(i+1,7), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        self.restore_color.Bind(wx.EVT_BUTTON, self.OnRestoreDefaultColors, self.restore_color)

        self.SetSizer(grid_sizer)
        self.SetAutoLayout(True)
        self.Fit()
        self.Layout()

    def OnNoteHighlightColorChanged(self, evt):
        wxcolor = self.note_highlight_color_picker.GetColour()
        color = wxcolor.GetAsString(flags=wx.C2S_HTML_SYNTAX)
        self.settings['note_highlight_color'] = color
        self.Parent.Parent.Parent.Parent.renderer.highlight_color = color

    def OnNoteHighlightFollowColorChanged(self, evt):
        wxcolor = self.note_highlight_follow_color_picker.GetColour()
        color = wxcolor.GetAsString(flags=wx.C2S_HTML_SYNTAX)
        self.settings['note_highlight_follow_color'] = color
        self.Parent.Parent.Parent.Parent.renderer.highlight_follow_color = color

    def UpdateEditor(self):
        font_info = self.settings.get('font')
        if font_info:
            face, size = font_info[-1], font_info[0]
            self.Parent.Parent.Parent.Parent.InitEditor(face, size)
        else:
            self.Parent.Parent.Parent.Parent.InitEditor()

    def OnFontColorChanged(self, evt, settings_key):
        wxcolor = self.color_picker[settings_key].GetColour()
        color = wxcolor.GetAsString(flags=wx.C2S_HTML_SYNTAX)
        self.settings[settings_key] = color
        self.UpdateEditor()
        
    def OnRestoreDefaultColors(self, evt):
        self.settings['note_highlight_color'] = default_note_highlight_color
        self.note_highlight_color_picker.SetColour(default_note_highlight_color)
        self.settings['note_highlight_follow_color'] = default_note_highlight_follow_color
        self.note_highlight_follow_color_picker.SetColour(default_note_highlight_follow_color)
        for key, color in default_style_color.items():
            self.settings[key] = color
            self.color_picker[key].SetColour(color)
        self.UpdateEditor()

# 1.3.6 [SS] 2014-12-01
# For controlling the way xml2abc and abc2xml operate
class MusicXmlPage(wx.Panel):
    def __init__(self, parent, settings):
        wx.Panel.__init__(self,parent)
        self.settings = settings
        self.SetBackgroundColour(dialog_background_colour)
        border = control_margin

        #headingtxt = _("The settings on this page control behaviour of the functions abc2xml and xml2abc.\nYou find these functions under Files/export and import. Hovering the mouse over\none of the checkboxes will provide more explanation. Further documentation can be found\nin the Readme.txt files which come with the abc2xml.py-??.zip and xml2abc.py-??.zip\ndistributions available from the Wim Vree's web site.\n\n")
        headingtxt = _("The settings on this page control behaviour of the functions abc2xml and xml2abc.\n\nYou find these functions under Files/export and import. Hovering the mouse over one of the checkboxes will provide more explanation.\nFurther documentation can be found from the Wim Vree's web site.\n")

        heading    = wx.StaticText(self, wx.ID_ANY, headingtxt)
        abc2xml    = wx.StaticText(self, wx.ID_ANY, _("abc2xml options"))
        compressed = wx.StaticText(self, wx.ID_ANY, _('Compressed xml'))
        xml2abc    = wx.StaticText(self, wx.ID_ANY, _('xml2abc option'))
        unfold     = wx.StaticText(self, wx.ID_ANY, _('Unfold Repeats'))
        mididata   = wx.StaticText(self, wx.ID_ANY, _('Midi Data'))
        volta      = wx.StaticText(self, wx.ID_ANY, _('Volta type setting'))
        numchar    = wx.StaticText(self, wx.ID_ANY, _('characters/line'))
        numbars    = wx.StaticText(self, wx.ID_ANY, _('bars per line'))
        credit     = wx.StaticText(self, wx.ID_ANY, _('credit filter'))
        ulength    = wx.StaticText(self, wx.ID_ANY, _('unit length'))
        xmlpage    = wx.StaticText(self, wx.ID_ANY, _('Page settings'))

        self.chkXmlCompressed = wx.CheckBox(self, wx.ID_ANY, '')
        self.chkXmlUnfold = wx.CheckBox(self, wx.ID_ANY, '')
        self.chkXmlMidi = wx.CheckBox(self, wx.ID_ANY, '')
        self.voltaval = wx.TextCtrl(self, wx.ID_ANY, size=(55, 22))
        self.maxchars = wx.TextCtrl(self, wx.ID_ANY, size=(55, 22))
        self.maxbars  = wx.TextCtrl(self, wx.ID_ANY, size=(55, 22))
        self.creditval = wx.TextCtrl(self, wx.ID_ANY, size=(55, 22))
        self.unitval  = wx.TextCtrl(self, wx.ID_ANY, size=(55, 22))
        self.XmlPage = wx.TextCtrl(self, wx.ID_ANY, size=(55, 22))
        #FAU Todo: expand option list to latest xml2abc capabilities

        self.chkXmlCompressed.SetValue(self.settings.get('xmlcompressed',False))
        self.chkXmlUnfold.SetValue(self.settings.get('xmlunfold',False))
        self.chkXmlMidi.SetValue(self.settings.get('xmlmidi',False))
        self.voltaval.SetValue(str(self.settings.get('xml_v')))
        self.maxbars.SetValue(self.settings.get('xml_b'))
        self.maxchars.SetValue(self.settings.get('xml_n'))
        self.creditval.SetValue(self.settings.get('xml_c'))
        self.unitval.SetValue(str(self.settings.get('xml_d')))
        self.XmlPage.SetValue(self.settings.get('xml_p'))

        # 1.3.6 [SS] 2014-12-19
        XmlCompressed_toolTip = _('When checked, abc2xml produces compressed xml files with extension mxl.')
        self.chkXmlCompressed.SetToolTip(wx.ToolTip(XmlCompressed_toolTip))
        XmlUnfold_toolTip = _('When checked, xml2abc turns off repeat translation and instead unfolds simple repeats.')
        self.chkXmlUnfold.SetToolTip(wx.ToolTip(XmlUnfold_toolTip))
        XmlMidi_toolTip = _('When checked, xml2abc outputs commands for midi volume and panning and the channel number. These commands are output in addition to the midi program number when it is present in the xml file.')
        self.chkXmlMidi.SetToolTip(wx.ToolTip(XmlMidi_toolTip))
        XmlPage_toolTip = _('The page format includes 6 numbers, eg. 0.7,25,15,1.2,1.2,1.2,1.2 which sets the scale to 0.7, the page height to 25 cm, the page width to 15 cm, and left, right, top and bottom margins to 1.2 cm. If the page format is blank, default values are assumed.')
        self.XmlPage.SetToolTip(wx.ToolTip(XmlPage_toolTip))
        maxchars_toolTip = _('Unless CPL is 0, it sets the maximum length for ABC output to CPL characters. The default is 100 characters. An integer number of bars, at least one, is always output.')
        self.maxchars.SetToolTip(wx.ToolTip(maxchars_toolTip))
        maxbars_toolTip = _('When not zero, BPL sets the number of bars per line. If both CPL and BPL is given, only CPL is used.')
        self.maxbars.SetToolTip(wx.ToolTip(maxbars_toolTip))
        creditval_toolTip = _('This filter tries to eliminate redundant T: fields. A higher level (up to 6) does less filtering. The default is 0 which filters as much as possible.')
        self.creditval.SetToolTip(wx.ToolTip(creditval_toolTip))
        unitval_toolTip = _('Unless D is 0, it sets the unit length for the output to abc field command L: 1/D. This overrides the computation of the optimal unit length.')
        self.unitval.SetToolTip(wx.ToolTip(unitval_toolTip))
        voltaval_toolTip = _("The default (V=0) translates volta brackets in all voices. V=1 prevents abcm2ps to write volta brackets on all but the first voice. (A %%repbra 0 command is added to each voice that hides its volta's.) When V=2 abcm2ps only typesets volta brackets on the first voice of each xml-part. When V=3 the volta brackets are only translated for the first abc voice, which has the same effect on the output of abcm2ps as V=1, but the abc code is not suited for abc2midi.")
        self.voltaval.SetToolTip(wx.ToolTip(voltaval_toolTip))

        # 1.3.6 [SS] 2014-12-20
        self.chkXmlCompressed.Bind(wx.EVT_CHECKBOX, self.OnXmlCompressed)
        self.chkXmlUnfold.Bind(wx.EVT_CHECKBOX, self.OnXmlUnfold)
        self.chkXmlMidi.Bind(wx.EVT_CHECKBOX, self.OnXmlMidi)
        self.voltaval.Bind(wx.EVT_TEXT, self.OnVolta)
        self.maxbars.Bind(wx.EVT_TEXT, self.OnMaxbars)
        self.maxchars.Bind(wx.EVT_TEXT, self.OnMaxchars)
        self.creditval.Bind(wx.EVT_TEXT, self.OnCreditval)
        self.unitval.Bind(wx.EVT_TEXT, self.OnUnitval)
        self.XmlPage.Bind(wx.EVT_TEXT, self.OnXmlPage)

        grid_sizer = wx.GridBagSizer()
        grid_sizer_abc2xml = wx.GridBagSizer()
        grid_sizer_xml2abc = wx.GridBagSizer()

        flags=wx.BOTTOM | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL

        grid_sizer.Add(heading, pos=(0,0), span=(1,4), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        grid_sizer_abc2xml.Add(abc2xml, pos=(0,0), span=(1,3), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        grid_sizer_abc2xml.Add(compressed, pos=(1,1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        grid_sizer_abc2xml.Add(self.chkXmlCompressed, pos=(1,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        grid_sizer_xml2abc.Add(xml2abc, pos=(0,0), span=(1,3), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        grid_sizer_xml2abc.Add(unfold, pos=(1,1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        grid_sizer_xml2abc.Add(self.chkXmlUnfold, pos=(1,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        grid_sizer_xml2abc.Add(mididata, pos=(2,1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        grid_sizer_xml2abc.Add(self.chkXmlMidi, pos=(2,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        grid_sizer_xml2abc.Add(volta, pos=(3,1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        grid_sizer_xml2abc.Add(self.voltaval, pos=(3,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        grid_sizer_xml2abc.Add(numchar, pos=(4,1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        grid_sizer_xml2abc.Add(self.maxchars, pos=(4,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        grid_sizer_xml2abc.Add(numbars, pos=(5,1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        grid_sizer_xml2abc.Add(self.maxbars, pos=(5,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        grid_sizer_xml2abc.Add(credit, pos=(6,1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        grid_sizer_xml2abc.Add(self.creditval, pos=(6,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        grid_sizer_xml2abc.Add(ulength, pos=(7,1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        grid_sizer_xml2abc.Add(self.unitval, pos=(7,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        grid_sizer_xml2abc.Add(xmlpage, pos=(8,1), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        grid_sizer_xml2abc.Add(self.XmlPage, pos=(8,2), flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        grid_sizer.Add(grid_sizer_abc2xml, pos=(1,0), flag=wx.ALL | wx.ALIGN_TOP, border=border)
        grid_sizer.Add(50, 40, pos=(1,1))
        grid_sizer.Add(grid_sizer_xml2abc, pos=(1,2), flag=wx.ALL | wx.ALIGN_TOP, border=border)
        
        self.SetSizer(grid_sizer)
        self.SetAutoLayout(True)
        self.Fit()
        self.Layout()

    def OnXmlCompressed(self, evt):
        self.settings['xmlcompressed'] = self.chkXmlCompressed.GetValue()

    def OnXmlUnfold(self, evt):
        self.settings['xmlunfold'] = self.chkXmlUnfold.GetValue()

    def OnXmlMidi(self, evt):
        self.settings['xmlmidi'] = self.chkXmlMidi.GetValue()

    def OnVolta(self, evt):
        self.settings['xml_v'] = self.voltaval.GetValue()

    def OnMaxbars(self, evt):
        self.settings['xml_b'] = self.maxbars.GetValue()

    def OnMaxchars(self, evt):
        self.settings['xml_n'] = self.maxchars.GetValue()

    def OnCreditval(self, evt):
        self.settings['xml_c'] = self.creditval.GetValue()

    def OnUnitval(self, evt):
        self.settings['xml_d'] = self.unitval.GetValue()

    def OnXmlPage(self, evt):
        self.settings['xml_p'] = self.XmlPage.GetValue()


class MidiOptionsFrame(wx.Dialog):
    def __init__(self, parent, ID=-1, title='', key='', metre='3/4', default_len='1/16'):
        wx.Dialog.__init__(self, parent, ID, _('ABC Options'), wx.DefaultPosition, wx.Size(300, 80))

        self.SetBackgroundColour(dialog_background_colour)
        border = control_margin
        sizer = wx.GridBagSizer(control_margin, control_margin)
        sizer.Add(wx.StaticText(self, wx.ID_ANY, u'K: ' + _('Key signature')), wx.GBPosition(0, 0), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(wx.StaticText(self, wx.ID_ANY, u'M: ' + _('Metre')), wx.GBPosition(1, 0), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(wx.StaticText(self, wx.ID_ANY, u'L: ' + _('Default note length')), wx.GBPosition(2, 0), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(wx.StaticText(self, wx.ID_ANY, u'T: ' + _('Title')), wx.GBPosition(3, 0), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(wx.StaticText(self, wx.ID_ANY, _('Bars per line')), wx.GBPosition(4, 0), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(wx.StaticText(self, wx.ID_ANY, _('Numbers of notes in anacrusis')), wx.GBPosition(5, 0), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)

        self.key = wx.TextCtrl(self, wx.ID_ANY, size=(150, 22))
        self.metre = wx.TextCtrl(self, wx.ID_ANY, size=(150, 22))
        self.default_len = wx.TextCtrl(self, wx.ID_ANY, size=(150, 22))
        self.title = wx.TextCtrl(self, wx.ID_ANY, size=(150, 22))
        self.bpl = wx.TextCtrl(self, wx.ID_ANY, size=(150, 22))
        self.num_notes_in_anacrusis = wx.TextCtrl(self, wx.ID_ANY, size=(150, 22))
        self.triplet_detection = wx.CheckBox(self, wx.ID_ANY, _('Detect triplets'))
        self.broken_rythm_detection = wx.CheckBox(self, wx.ID_ANY, _('Detect broken rythms'))
        self.slur_triplets = wx.CheckBox(self, wx.ID_ANY, _('Use slurs on triplets'))
        self.slur_8ths = wx.CheckBox(self, wx.ID_ANY, _('Use slurs on eights (useful for some waltzes)'))
        self.slur_16ths = wx.CheckBox(self, wx.ID_ANY, _('Use slurs on first pair of sixteenth (useful for some 16th polskas)'))
        self.ok = wx.Button(self, wx.ID_ANY, _('&Ok'))
        self.cancel = wx.Button(self, wx.ID_ANY, _('&Cancel'))
        # 1.3.6.1 [JWdJ] 2015-01-30 Swapped next two lines so OK-button comes first (OK Cancel)
        if WX4:
            box = wx.BoxSizer()
            box.Add(self.ok, wx.ID_OK)
            box.Add(self.cancel, wx.ID_CANCEL)
        else:
            box = wx.BoxSizer(wx.HORIZONTAL)
            box.Add(self.ok, wx.ID_OK, flag=wx.ALIGN_RIGHT)
            box.Add(self.cancel, wx.ID_CANCEL, flag=wx.ALIGN_RIGHT)

        sizer.Add(self.key,                     wx.GBPosition(0, 1), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(self.metre,                   wx.GBPosition(1, 1), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(self.default_len,             wx.GBPosition(2, 1), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(self.title,                   wx.GBPosition(3, 1), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(self.bpl,                     wx.GBPosition(4, 1), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(self.num_notes_in_anacrusis,  wx.GBPosition(5, 1), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(self.triplet_detection,       wx.GBPosition(6, 0), (1, 2), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(self.broken_rythm_detection,  wx.GBPosition(7, 0), (1, 2), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(self.slur_triplets,           wx.GBPosition(8, 0), (1, 2), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(self.slur_8ths,               wx.GBPosition(9, 0), (1, 2), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(self.slur_16ths,              wx.GBPosition(10,0), (1, 2), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(box,                          wx.GBPosition(11,0), (1, 2), flag=0 | wx.LEFT | wx.RIGHT | wx.ALIGN_RIGHT, border=border)

        self.triplet_detection.SetValue(True)
        self.broken_rythm_detection.SetValue(True)
        self.slur_triplets.SetValue(False)
        self.slur_16ths.SetValue(False)
        self.key.SetValue(key)
        self.metre.SetValue(str(metre))
        self.default_len.SetValue(str(default_len))
        self.num_notes_in_anacrusis.SetValue('0')
        self.bpl.SetValue('4')
        self.title.SetValue(title)
        self.ok.SetDefault()

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self.Centre()
        sizer.Fit(self)

        self.ok.Bind(wx.EVT_BUTTON, self.OnOk)
        self.cancel.Bind(wx.EVT_BUTTON, self.OnCancel)

    def OnOk(self, evt):
        self.EndModal(wx.ID_OK)

    def OnCancel(self, evt):
        self.EndModal(wx.ID_CANCEL)


class ErrorFrame(wx.Dialog):
    def __init__(self, parent, error_msg):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, _('Errors'), wx.DefaultPosition, wx.Size(700, 80))
        border = 10
        self.SetBackgroundColour(dialog_background_colour)

        sizer = wx.BoxSizer(wx.VERTICAL)
        font_size = get_normal_fontsize() # 1.3.6.3 [JWDJ] one function to set font size
        font = wx.Font(font_size, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Courier New")
        self.error = wx.TextCtrl(self, wx.ID_ANY, error_msg, size=(700, 300), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER|wx.HSCROLL)
        self.error.SetFont(font)

        self.ok = wx.Button(self, wx.ID_ANY, _('&Ok'))
        self.cancel = wx.Button(self, wx.ID_ANY, _('&Cancel'))
        # 1.3.6.1 [JWdJ] 2015-01-30 Swapped next two lines so OK-button comes first (OK Cancel)
        if WX4:
            box = wx.BoxSizer()
            box.Add(self.ok, wx.ID_OK)
            box.Add(self.cancel, wx.ID_CANCEL)
        else:
            box = wx.BoxSizer(wx.HORIZONTAL)
            box.Add(self.ok, wx.ID_OK, flag=wx.ALIGN_RIGHT)
            box.Add(self.cancel, wx.ID_CANCEL, flag=wx.ALIGN_RIGHT)

        sizer.Add(self.error, flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(box, flag=wx.ALL | wx.ALIGN_RIGHT, border=border)
        self.ok.SetDefault()

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self.Centre()
        sizer.Fit(self)

        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDownEvent)
        self.ok.Bind(wx.EVT_BUTTON, self.OnOk)
        self.cancel.Bind(wx.EVT_BUTTON, self.OnCancel)

    def OnKeyDownEvent(self, evt):
        if evt.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
        else:
            evt.Skip()

    def OnOk(self, evt):
        self.EndModal(wx.ID_OK)

    def OnCancel(self, evt):
        self.EndModal(wx.ID_CANCEL)


class ProgressFrame(wx.Frame):
    def __init__(self, parent, ID, title=_('Converting...')):
        wx.Frame.__init__(self, parent, ID, title, wx.DefaultPosition, wx.Size(500, 80))
        self.gauge = wx.Gauge(self, wx.ID_ANY, 100, (0, 0), (500, 80))
        self.Centre()
    def SetPercent(self, percent):
        self.gauge.SetValue(percent)


class FlexibleListCtrl(wx.ListCtrl, listmix.ColumnSorterMixin, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.ColumnSorterMixin.__init__(self, 3)
        self._resizeCol = 2
        self._resizeColStyle = "COL"
        self._resizeColMinWidth = 10
        self.il = wx.ImageList(1, 16)
        SmallUpArrow = PyEmbeddedImage(
        "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAADxJ"
        "REFUOI1jZGRiZqAEMFGke2gY8P/f3/9kGwDTjM8QnAaga8JlCG3CAJdt2MQxDCAUaOjyjKMp"
        "cRAYAABS2CPsss3BWQAAAABJRU5ErkJggg==")

        SmallDnArrow = PyEmbeddedImage(
        "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAEhJ"
        "REFUOI1jZGRiZqAEMFGke9QABgYGBgYWdIH///7+J6SJkYmZEacLkCUJacZqAD5DsInTLhDR"
        "bcPlKrwugGnCFy6Mo3mBAQChDgRlP4RC7wAAAABJRU5ErkJggg==")
        self.sm_up = self.il.Add(SmallUpArrow.GetBitmap())
        self.sm_dn = self.il.Add(SmallDnArrow.GetBitmap())
    def GetListCtrl(self):
        return self
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)
    def getColumnText(self, index, col):
        item = self.GetItem(index, col)
        text = item.GetText()
        return text
    def GetSecondarySortValues(self, col, key1, key2):
        """Returns a tuple of 2 values to use for secondary sort values when the
           items in the selected column match equal.  The default just returns the
           item data values."""
        if col == 0:
            return (self.itemDataMap[key1][1], self.itemDataMap[key2][1])
        elif col >= 1:
            return (self.itemDataMap[key1][0], self.itemDataMap[key2][0])
        else:
            return (None, None)

    def SelectItem(self, index, select=True):
        self.Select(index, select)

    def DeselectAll(self):
        item = self.GetFirstSelected()
        while item != -1:
            nextItem = self.GetNextSelected(item)
            self.SelectItem(item, False)
            item = nextItem


class AbcSearchPanel(wx.Panel):
    ''' For searching a directory of abc files for tunes containing a string. '''
    def __init__(self, parent, settings, statusbar):
        wx.Panel.__init__(self, parent)
        self.settings = settings
        self.statusbar = statusbar
        self.mainwindow = parent
        border = control_margin
        self.max_results = 5000

        find_what_label = wx.StaticText(self, wx.ID_ANY, _('Find what') + ':')

        default_choices = ['C:mozart', 'w:love', 'R:jig', 'M:6/8']
        self.find_what_ctrl = wx.ComboBox(self, wx.ID_ANY, choices=default_choices, style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER)
        self.focus_find_what()
        self.show_search_options_button = wx.Button(self, wx.ID_ANY, '...', size=(26, -1))

        options = [(_('Title'), 'T:'), (_('Composer'), 'C:'), (_('Lyrics'), 'w: W:')]
        searchfields = self.get_searchfields()
        menu = create_menu([], parent=self)
        for label, field in options:
            menuitem = append_menu_item(menu, label + ' (' + field + ')', '', self.on_toggle_option, kind=wx.ITEM_CHECK)
            menuitem.Help = field
            menuitem.Check(field.split()[0] in searchfields)
        menu.AppendSeparator()
        menuitem = append_menu_item(menu, _('Sort by title'), '', self.on_toggle_sort_search_results, kind=wx.ITEM_CHECK)
        menuitem.Check(settings.get('sort_search_results', True))

        self.search_menu = menu

        searchfolder_label = wx.StaticText(self, wx.ID_ANY, _("Look in") + ':')
        self.searchfolder_ctrl = wx.TextCtrl(self, wx.ID_ANY, settings['searchfolder'], style=wx.TE_PROCESS_ENTER)
        self.choose_search_folder_button = wx.Button(self, wx.ID_ANY, '...', size=(26, -1))

        self.progress = wx.Gauge(self, wx.ID_ANY)
        self.progress.Hide()
        self.progress_timer = None
        if wx.Platform != "__WXMSW__":  # on Windows not needed, but Linux and macOS need an update timer
            self.progress_timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.on_progress_timer, self.progress_timer)

        self.cancel_search_button = wx.Button(self, wx.ID_ANY, _('Cancel'))
        self.cancel_search_button.Hide()
        self.find_all_button = wx.Button(self, wx.ID_ANY, _('Find All'))
        self.list_ctrl = wx.ListBox(self, style=wx.LB_SINGLE)

        no_top_border = wx.BOTTOM | wx.LEFT | wx.RIGHT
        no_bottom_border = wx.TOP | wx.LEFT | wx.RIGHT
        mainsizer = wx.BoxSizer(wx.VERTICAL)
        mainsizer.Add(find_what_label, flag=no_bottom_border, border=border)

        whatSizer = wx.BoxSizer(wx.HORIZONTAL)
        whatSizer.Add(self.find_what_ctrl, 1, flag=wx.EXPAND | wx.BOTTOM | wx.LEFT, border=border)
        whatSizer.Add(self.show_search_options_button, 0, flag=no_top_border, border=border)
        mainsizer.Add(whatSizer, 0, flag=wx.EXPAND)

        mainsizer.Add(searchfolder_label, flag=no_bottom_border, border=border)
        folderSizer = wx.BoxSizer(wx.HORIZONTAL)
        folderSizer.Add(self.searchfolder_ctrl, 1, flag=wx.EXPAND | wx.BOTTOM | wx.LEFT, border=border)
        folderSizer.Add(self.choose_search_folder_button, 0, flag=no_top_border, border=border)

        progressSizer = wx.BoxSizer(wx.HORIZONTAL)
        progressSizer.Add(self.progress, 1, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.RESERVE_SPACE_EVEN_IF_HIDDEN, border=border)
        progressSizer.Add(self.cancel_search_button, 0, flag=wx.ALL | wx.RESERVE_SPACE_EVEN_IF_HIDDEN, border=border)
        progressSizer.Add(self.find_all_button, 0, flag=wx.ALL | wx.RESERVE_SPACE_EVEN_IF_HIDDEN, border=border)

        self.when_selecting = wx.RadioBox(self, wx.ID_ANY, _('When selecting'), choices=[_('Open file'), _('Copy tune to editor')], majorDimension=1)
        when_selecting_sizer = wx.BoxSizer(wx.HORIZONTAL)
        when_selecting_sizer.Add(self.when_selecting, 1, flag=wx.ALL | wx.RESERVE_SPACE_EVEN_IF_HIDDEN, border=border)

        mainsizer.Add(folderSizer, 0, flag=wx.EXPAND)
        mainsizer.Add(progressSizer, 0, flag=wx.EXPAND)
        mainsizer.Add(self.list_ctrl, 1, flag=wx.EXPAND)
        mainsizer.Add(when_selecting_sizer, 0, flag=wx.EXPAND)

        self.SetSizer(mainsizer)
        self.Show()

        self.Bind(wx.EVT_BUTTON, self.On_browse_abcsearch, self.choose_search_folder_button)
        self.Bind(wx.EVT_BUTTON, self.on_popup_search_menu, self.show_search_options_button)
        self.Bind(wx.EVT_BUTTON, self.On_start_search, self.find_all_button)
        self.Bind(wx.EVT_BUTTON, self.On_start_search, self.find_all_button)
        self.Bind(wx.EVT_BUTTON, self.on_cancel_search, self.cancel_search_button)
        self.Bind(wx.EVT_TEXT_ENTER, self.On_start_search, self.find_what_ctrl)
        self.Bind(wx.EVT_TEXT_ENTER, self.On_start_search, self.searchfolder_ctrl)
        self.list_ctrl.Bind(wx.EVT_LISTBOX, self.OnItemSelected, self.list_ctrl)

        self.search_thread = None
        self.last_results = None
        self.results_start_index = 0

    def get_searchfields(self):
        return self.settings.get('searchfields', 'T:').split(';')

    def set_searchfields(self, value):
        self.settings['searchfields'] = ';'.join(value)

    def on_progress_timer(self, event):
        self.progress.Pulse()

    def on_popup_search_menu(self, event):
        self.PopupMenu(self.search_menu, event.EventObject.Position)

    def on_toggle_sort_search_results(self, event):
        menu = event.EventObject
        menu_item = menu.FindItemById(event.Id)
        self.settings['sort_search_results'] = menu_item.IsChecked()

    def on_toggle_option(self, event):
        menu = event.EventObject
        menu_item = menu.FindItemById(event.Id)
        include = menu_item.IsChecked()
        fields = menu_item.Help.split()
        searchfields = self.get_searchfields()
        for field in fields:
            if include:
                if not field in searchfields:
                    searchfields.append(field)
            else:
                if field in searchfields:
                    searchfields.remove(field)
        self.set_searchfields([f for f in searchfields if f])

    def focus_find_what(self):
        self.find_what_ctrl.SetFocus()

    def On_browse_abcsearch(self, evt):
        ''' Selects the folder to open for searching'''
        old_path = self.searchfolder_ctrl.GetValue()
        path = wx_dirdialog(self, _("Open"), old_path)
        if path:
            self.settings['searchfolder'] = path
            self.searchfolder_ctrl.SetValue(path)

    def On_start_search(self, evt):
        ''' Initializes dictionaries and calls find_abc_files'''
        root = self.searchfolder_ctrl.GetValue()
        if not root or not os.path.exists(root):
            wx_show_message(_('Invalid path'), _('Please enter a valid path to start looking for ABC-files.'))
        else:
            searchstring = self.find_what_ctrl.GetValue().strip()
            if searchstring and not searchstring in self.find_what_ctrl.Items:
                wx_insert_dropdown_value(self.find_what_ctrl, searchstring, max=5)
            self.find_all_button.Disable()
            self.list_ctrl.Show(False)
            self.list_ctrl.Clear()
            self.cancel_search_button.Enable()
            self.cancel_search_button.Show()
            self.progress.Pulse()
            self.progress.Show()
            if self.progress_timer:
                self.progress_timer.Start(200, wx.TIMER_CONTINUOUS)

            sort_results = self.settings.get('sort_search_results', True)
            if self.search_thread:
                self.search_thread.abort()
            self.search_thread = SearchFilesThread(root, searchstring, self.get_searchfields(), self.on_after_search, sort_results)

    def on_after_search(self, aborted, items):
        self.last_results = items
        self.results_start_index = 0
        if not aborted:
            self.statusbar.SetStatusText(_('Found {0} results').format(len(items)))
            self.show_next_results(self.results_start_index)

        self.find_all_button.Enable()
        self.cancel_search_button.Hide()
        if self.progress_timer:
            self.progress_timer.Stop()
        self.progress.Hide()
        self.progress.SetValue(0)

    def on_cancel_search(self, event):
        self.abort_search()

    def abort_search(self):
        self.cancel_search_button.Disable()
        self.search_thread.abort()

    @property
    def is_searching(self):
        return self.search_thread and self.search_thread.is_alive()

    def clear_results(self):
        self.find_what_ctrl.SetValue('')
        if self.is_searching:
            self.search_thread.abort()
        else:
            self.list_ctrl.Clear()


# 1.3.6 [SS] 2014-12-02
    def OnItemSelected(self, evt):
        ''' Responds to a selected title in the search listbox results. The abc file
        containing the selected tune is opened and the table of contents is updated.'''
        index = evt.Selection  # line number in listbox
        if self.max_results > 0 and index >= self.max_results:
            self.show_next_results(self.max_results + self.results_start_index)
        else:
            index += self.results_start_index
            path, char_pos_in_file = self.search_thread.get_result_for_index(index)

            wait = wx.BusyCursor()
            if self.when_selecting.GetSelection() == 0:
                # open file and select tune
                if self.mainwindow.CanClose():
                    abc_text = read_abc_file(path)[0:char_pos_in_file]
                    byte_pos_in_file = len(abc_text.encode('utf-8'))
                    self.mainwindow.load_and_position(path, byte_pos_in_file)
            else:
                # open in current editor
                wholefile = read_abc_file(path)
                tune_start = find_start_of_tune(wholefile, char_pos_in_file)
                tune_end = find_end_of_tune(wholefile, char_pos_in_file)
                editor = self.mainwindow.editor
                editor.BeginUndoAction()

                last_pos = editor.GetLength()
                editor.GotoPos(last_pos)
                editor.SetSelection(last_pos, last_pos)

                empty_line = os.linesep
                if last_pos > 0 and editor.GetTextRange(last_pos - 1, last_pos) != '\n':
                    empty_line += os.linesep

                editor.ReplaceSelection(empty_line + wholefile[tune_start:tune_end])

                editor.EndUndoAction()
            del wait

    def show_next_results(self, start_index):
        results = self.last_results
        items = results
        end_index = len(results)
        if self.max_results > 0:
            end_index = start_index + self.max_results
            items = results[start_index:end_index]

        titles = [title for title, path, pos in items]
        if end_index < len(results):
            next_count = min(len(results) - end_index, self.max_results)
            titles.append(u'[ ' + _('Next {0} results').format(next_count) + u' ]')

        self.results_start_index = start_index
        wait = wx.BusyCursor()
        self.list_ctrl.Hide()
        self.list_ctrl.Clear()
        if titles:
            self.list_ctrl.InsertItems(titles, 0)
        self.list_ctrl.Show()
        del wait


search_parts_re = re.compile(r'(?:^| )([A-Za-z]:|%%)')
clean_lyrics_re = re.compile(r'\s*(?:-|\\-|\*|\|)\s*')
def lyrics_to_text(lyrics):
    return clean_lyrics_re.sub('', lyrics)

class SearchFilesThread(threading.Thread):
    def __init__(self, root, searchstring, searchfields, on_after_search, sort_search_results):
        threading.Thread.__init__(self)
        self.daemon = True
        self._stop_event = threading.Event()
        self.root = root
        self.searchstring = searchstring
        self.searchfields = searchfields
        self.on_after_search = on_after_search
        self.sort_search_results = sort_search_results
        self.search_results = []
        self.start()

    def abort(self):
        self._stop_event.set()

    @property
    def abort_requested(self):
        return self._stop_event.is_set()

    def run(self):
        self.find_abc_files(self.root, self.searchstring, self.searchfields)
        if self.sort_search_results:
            self.search_results = sorted(self.search_results, key=lambda sr: sr[0])

        if self.on_after_search is not None:
            wx.CallAfter(self.on_after_search, self.abort_requested, self.search_results)

# 1.3.6 [SS] 2014-11-23
    def find_abc_files(self, root, searchstring, searchfields):
        abcmatches = []
        for pathname in search_files(root, ['.abc', '.ABC']):  # currently not abortable
            abcmatches.append(pathname)

        search_parts = self.extract_search_parts(searchstring, searchfields)
        for pathname in abcmatches:
            self.find_abc_string(pathname, search_parts)
            if self.abort_requested:
                break

    def extract_search_parts(self, searchtext, searchfields):
        abckey = searchfields  # default search in title
        if not abckey or not abckey[0]:
            abckey = 'T:'
        search_parts = []
        allow_empty_text = False
        pos = 0
        for m in search_parts_re.finditer(searchtext):
            text = searchtext[pos:m.start(1)]
            self.add_searchpart(search_parts, abckey, text, allow_empty_text)
            abckey = m.group(1)
            pos = m.end(1)
            allow_empty_text = True

        text = searchtext[pos:]
        self.add_searchpart(search_parts, abckey, text, allow_empty_text)

        if not search_parts:
            search_parts.append([('T:', None)])
        return search_parts

    @staticmethod
    def add_searchpart(search_parts, abckey, text, allow_empty_text=False):
        if text or allow_empty_text:
            words = text.strip().lower().split()
            if isinstance(abckey, str):
                search_parts.append([(abckey, words)])
            else:
                search_parts.append([(k, words) for k in abckey])

# 1.3.6 [SS] 2014-11-30
    def find_abc_string(self, path, search_parts):
        wholefile = read_abc_file(path)
        prev_found_tune_positions = None
        for search_part in search_parts:
            found_tune_positions = {}
            for abckey, words in search_part:
                convert_line = lambda s: s
                if abckey in ('w:', 'W:'):
                    convert_line = lyrics_to_text

                loc = 0
                while loc != -1:
                    loc = wholefile.find(abckey, loc)
                    if loc == -1:
                        break
                    line_end = wholefile.find('\n', loc)
                    if line_end == -1:
                        break
                    if wholefile[loc - 1] == '\n':
                        start_pos = loc + len(abckey)
                        line = wholefile[start_pos:line_end]

                        index = 0
                        if words:
                            lline = convert_line(line).lower()
                            for word in words:
                                if word:
                                    index = lline.find(word)
                                    if index == -1:
                                        break  # all words must match

                        if index != -1:
                            start_pos += index
                            tune_start = find_start_of_tune(wholefile, start_pos)
                            if prev_found_tune_positions is None or tune_start in prev_found_tune_positions:
                                found_tune_positions[tune_start] = start_pos
                    loc = line_end
            prev_found_tune_positions = found_tune_positions

        if prev_found_tune_positions:
            for tune_pos in prev_found_tune_positions:
                title = get_tune_title_at_pos(wholefile, tune_pos)
                index = found_tune_positions[tune_pos]
                self.search_results.append((title, path, index))

    def get_result_for_index(self, index):
        _, path, pos = self.search_results[index]
        return path, pos  # character position in file


class MainFrame(wx.Frame):
    def __init__(self, parent, ID, app_dir, settings, options):
        wx.Frame.__init__(self, parent, ID, '%s - %s %s' % (program_name, _('Untitled'), 1),
                         wx.DefaultPosition, wx.Size(900, 850))
        #_icon = wx.EmptyIcon()
        #_icon.CopyFromBitmap(wx.Bitmap(os.path.join('img', 'logo.ico'), wx.BITMAP_TYPE_ICO))
        #self.SetIcon(_icon)
        if wx.Platform == "__WXMSW__":
            exeName = win32api.GetModuleFileName(win32api.GetModuleHandle(None))
            # 1.3.8.1 [mist13] Icon for Python version in Windows
            if "easy_abc" in exeName:
                icon = wx.Icon(exeName + ";0", wx.BITMAP_TYPE_ICO)
            else:
                icon = wx.Icon(os.path.join(application_path, 'img', 'logo.ico'))
            self.SetIcon(icon)
        global execmessages, visible_abc_code
        self.settings = settings
        self.current_svg_tune = None # 1.3.6.2 [JWdJ] 2015-02
        self.svg_tunes = AbcTunes()
        self.current_midi_tune = None # 1.3.6.3 [JWdJ] 2015-03
        self.midi_tunes = AbcTunes()
        self.__current_page_index = 0 # 1.3.6.2 [JWdJ] 2015-02
        self.applied_tempo_multiplier = 1.0 # 1.3.6.4 [JWdJ] 2015-05
        self.is_closed = False
        self.app_dir = app_dir
        self.cache_dir = os.path.join(self.app_dir, 'cache')
        self.settings_file = os.path.join(self.app_dir, 'settings1.3.dat')
        self.exclusive_file_mode = options.get('exclusive', False)
        self._current_file = None
        self.untitled_number = 1
        self.author = ''
        self.record_thread = None
        self.zoom_factor = 1.0
        self.selected_note_indices = []
        self.selected_note_descs = []
        self.played_notes_timeline = None
        self.current_time_slice = None
        self.future_time_slice = None
        self.keyboard_input_mode = False
        self.last_refresh_time = datetime.now()
        self.last_line_number_selected = -1
        self.queue_number_refresh_music = 0
        self.queue_number_follow_score = 0
        self.queue_number_movement = 0
        self.field_reference_frame = None
        self.find_data = wx.FindReplaceData()
        self.find_dialog = None
        self.replace_dialog = None
        self.settingsbook = None
        self.find_data.SetFlags(wx.FR_DOWN)
        self.execmessage_time = datetime.now() # 1.3.6 [SS] 2014-12-11
        self.is_fullscreen = False
        self.score_is_maximized = False

        self.load_settings()
        settings = self.settings

        # 1.3.6 [SS] 2014-12-07
        self.statusbar = self.CreateStatusBar()
        self.SetMinSize((100, 100))
        if settings.get('live_resize', False):
            self.manager = aui.AuiManager(self, agwFlags=aui.AUI_MGR_DEFAULT | aui.AUI_MGR_LIVE_RESIZE)
        else:
            self.manager = aui.AuiManager(self)

        self.printData = wx.PrintData()
        self.printData.SetPrintMode(wx.PRINT_MODE_PRINTER)

        self.setup_menus()
        self.setup_toolbar()
        self.mc = None

        if platform.system() == 'Windows':
            default_soundfont_path = os.environ.get('HOMEPATH', 'C:') + "\\SoundFonts\\FluidR3_GM.sf2"
        else:
            default_soundfont_path = '/usr/share/sounds/sf2/FluidR3_GM.sf2'

        soundfont_path = settings.get('soundfont_path', default_soundfont_path)
        self.uses_fluidsynth = False
        if fluidsynth_available and soundfont_path and os.path.exists(soundfont_path):
            try:
                init_soundfont_path = os.path.join(application_path, 'sound', 'example.sf2')
                if not os.path.exists(init_soundfont_path):
                    init_soundfont_path = soundfont_path
                self.mc = FluidSynthPlayer(init_soundfont_path)
                self.uses_fluidsynth = True
                self.mc.set_soundfont(soundfont_path, load_on_play=True)
            except Exception as e:
                error_msg = traceback.format_exc()
                self.mc = None
                
        #FAU:MIDIPLAY: on Mac add the ability to interface to System Midi Synth via mplay in case fluidsynth not available or not configured with soundfont
        if wx.Platform == "__WXMAC__" and self.mc is None:
            try:
                self.mc = MPlaySMFPlayer(self)
            except:
                error_msg = "Error on loading SMF Midi Player"
                self.mc = None

        if self.mc is None:
            try:
                backend = None
                from wxmediaplayer import WxMediaPlayer
                #FAU:MIDIPLAY:The Quicktime interface do not manage MIDI File on latest version of Mac so keep only possibility on Windows
                #if wx.Platform == "__WXMAC__":
                #    backend = wx.media.MEDIABACKEND_QUICKTIME
                #elif wx.Platform == "__WXMSW__":
                if wx.Platform == "__WXMSW__":
                    if platform.release() == 'XP':
                        backend = wx.media.MEDIABACKEND_DIRECTSHOW
                    else:
                        backend = wx.media.MEDIABACKEND_WMP10
                self.mc = WxMediaPlayer(self, backend)
            except NotImplementedError:
                from midiplayer import DummyMidiPlayer
                self.mc = DummyMidiPlayer()  # if media player not supported on this platform

        self.started_playing = False

        self.mc.OnAfterLoad += self.OnMediaLoaded
        self.mc.OnAfterStop += self.OnAfterStop
        self.play_music_thread = None

        # 1.3.7.3 [JWDJ] Removed wx.LC_SINGLE_SEL to enable multiselect tunes
        self.tune_list = FlexibleListCtrl(self, wx.ID_ANY, style=wx.LC_REPORT) #wx.LC_NO_HEADER)

        self.tune_list.InsertColumn(0, _('No.'), wx.LIST_FORMAT_RIGHT)
        self.tune_list.InsertColumn(1, _('Title'))

        self.tune_list.SetAutoLayout(True)
        self.editor = stc.StyledTextCtrl(self, -1)
        self.editor.SetCodePage(stc.STC_CP_UTF8)

        self.new_tune()

        # p09 include line numbering in the edit window. 2014-10-14 [SS]
        self.editor.SetMarginLeft(15)
        self.editor.SetMarginWidth(1,50)
        self.editor.SetMarginType(1,stc.STC_MARGIN_NUMBER)

        # 1.3.6.2 [JWdJ] 2015-02
        self.renderer = SvgRenderer(self.settings['can_draw_sharps_and_flats'], self.settings.get('note_highlight_color', default_note_highlight_color), self.settings.get('note_highlight_follow_color', default_note_highlight_follow_color))#'#FF0000')
        self.music_pane = MusicScorePanel(self, self.renderer)
        self.music_pane.SetBackgroundColour((255, 255, 255))
        self.music_pane.OnNoteSelectionChangedDesc = self.OnNoteSelectionChangedDesc

        error_font_size = get_normal_fontsize() # 1.3.6.3 [JWDJ] one function to set font size
        self.error_msg = wx.TextCtrl(self, wx.ID_ANY, '', size=(200, 100), style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER | wx.TE_READONLY | wx.TE_DONTWRAP)
        self.error_msg.SetFont(wx.Font(error_font_size, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Courier New"))
        self.error_pane = aui.AuiPaneInfo().Name("error message").Caption(_("ABC errors")).CloseButton(True).BestSize((160, 80)).Bottom()
        self.error_pane.Hide()
        self.error_msg.Hide() # 1.3.7 [JWdJ] 2016-01-06

        # 1.3.6.3 [JWdJ] 2015-04-21 ABC Assist added
        from abc_assist_panel import AbcAssistPanel  # 1.3.7.1 [JWDJ] 2016-1 because of translation this import has to be done as late as possible
        self.abc_assist_panel = AbcAssistPanel(self, self.editor, cwd, self.settings)
        self.assist_pane = aui.AuiPaneInfo().Name("abcassist").CaptionVisible(True).Caption(_("ABC assist")).\
            CloseButton(True).MinimizeButton(False).MaximizeButton(False).\
            Left().Layer(1).Position(1).BestSize(300, 600) # .PaneBorder(False) # Fixed()

        tune_list_pane = aui.AuiPaneInfo().Name("tune list").Caption(_("Tune list")).MinimizeButton(True).CloseButton(False).BestSize((265, 80)).Left().Row(0).Layer(1)
        editor_pane = aui.AuiPaneInfo().Name("abc editor").Caption(_("ABC code")).CloseButton(False).MinSize(40, 40).MaximizeButton(True).CaptionVisible(True).Center()
        music_pane_info = aui.AuiPaneInfo().Name("tune preview").Caption(_("Musical score")).MaximizeButton(True).MinimizeButton(True).CloseButton(False).BestSize((200, 280)).Right().Top()
        for pane_info in [tune_list_pane, editor_pane, music_pane_info, self.error_pane, self.assist_pane]:
            pane_info.Floatable(False).Dockable(False).Snappable(False).NotebookDockable(False)

        # do layout
        self.manager.AddPane(self.music_pane, music_pane_info)
        self.manager.AddPane(self.tune_list, tune_list_pane)
        self.manager.AddPane(self.editor, editor_pane)
        #self.manager.AddPane(self.error_msg, self.error_pane)
        self.manager.AddPane(self.abc_assist_panel, self.assist_pane)
        self.manager.Bind(aui.EVT_AUI_PANE_CLOSE, self.__onPaneClose)
        self.manager.Bind(aui.EVT_AUI_PANE_MAXIMIZE, self.__onPaneMaximize)
        self.manager.Bind(aui.EVT_AUI_PANE_RESTORE, self.__onPaneRestore)

        self.manager.Update()

        self.search_files_panel = None
        self.default_perspective = self.manager.SavePerspective()

        self.styler = ABCStyler(self.editor)

        font_info = settings.get('font')
        if font_info:
            face, size = font_info[-1], font_info[0]
            self.InitEditor(face, size)
        else:
            self.InitEditor()

        self.editor.SetDropTarget(MyFileDropTarget(self))
        self.tune_list.SetDropTarget(MyFileDropTarget(self))
        self.music_pane.SetDropTarget(MyFileDropTarget(self))
        self.abc_assist_panel.SetDropTarget(MyFileDropTarget(self))
        if wx.Platform == "__WXMSW__":
            self.GetMenuBar().SetDropTarget(MyFileDropTarget(self))

        self.tune_list_last_width = self.tune_list.GetSize().width

        self.index = 1
        self.tunes = []
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(2000, wx.TIMER_CONTINUOUS)

        self.tune_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnTuneSelected)
        self.tune_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnTuneDeselected)
        self.tune_list.Bind(wx.EVT_LEFT_DCLICK, self.OnTuneDoubleClicked)
        self.tune_list.Bind(wx.EVT_LEFT_DOWN, self.OnTuneListClick)
        self.editor.Bind(stc.EVT_STC_STYLENEEDED, self.styler.OnStyleNeeded)
        self.editor.Bind(stc.EVT_STC_CHANGE, self.OnChangeText)
        self.editor.Bind(stc.EVT_STC_MODIFIED, self.OnModified)
        self.editor.Bind(stc.EVT_STC_UPDATEUI, self.OnPosChanged)
        self.editor.Bind(wx.EVT_LEFT_UP, self.OnEditorMouseRelease)
        self.editor.Bind(wx.EVT_KEY_DOWN, self.OnKeyDownEvent)
        self.editor.Bind(wx.EVT_CHAR, self.OnCharEvent)
        self.editor.CmdKeyAssign(ord('+'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMIN)
        self.editor.CmdKeyAssign(ord('-'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMOUT)
        self.music_pane.Bind(wx.EVT_LEFT_DCLICK, self.OnMusicPaneDoubleClick)
        self.music_pane.Bind(wx.EVT_LEFT_DOWN, self.OnMusicPaneClick)
        self.music_pane.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClickMusicPane)
        # self.music_pane.Bind(wx.EVT_KEY_DOWN, self.OnMusicPaneKeyDown)

        self.load_and_apply_settings(load_window_size_pos=True)
        self.restore_settings()

        self.update_controls_using_settings()

        self.music_update_thread = MusicUpdateThread(self, self.settings, self.cache_dir)

        self.tune_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClickList, self.tune_list)

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(EVT_RECORDSTOP, self.OnRecordStop)
        self.Bind(EVT_MUSIC_UPDATE_DONE, self.OnMusicUpdateDone)
        self.editor.Bind(wx.EVT_KEY_DOWN, self.OnUpdate)
        self.music_pane.Bind(wx.EVT_KEY_DOWN, self.OnUpdate)
        self.tune_list.Bind(wx.EVT_KEY_DOWN, self.OnUpdate)
        self.music_pane.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)

        self.updating_text = False
        self.UpdateTuneList()

        self.play_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnPlayTimer, self.play_timer)
        self.play_timer.Start(50)
        self.music_update_thread.start()
        self.update_multi_tunes_menu_items()

        self.editor.SetFocus()
        wx.CallLater(100, self.editor.SetFocus)
        self.GrayUngray()

        self.OnClearCache(None) # P09 2014-10-26

        self.manager.GetPane(self.music_pane).Dockable(True) # 1.3.7.6 score pane movable
        # 1.3.7 [JWdJ] 2016-01-06
        self.ShowAbcAssist(self.settings.get('show_abc_assist', True))

        # 1.3.6.3 [SS] 2015-05-04
        self.statusbar.SetStatusText(_('This is the status bar. Check it occasionally.'))
        execmessages = _('You are running {0} on {1}').format(program_name, wx.Platform)
        execmessages += '\n' + _('You can get the latest version on') + ' https://sourceforge.net/projects/easyabc/'

    def update_controls_using_settings(self):
        # p09 Enable the play button if midiplayer_path is defined. 2014-10-14 [SS]
        self.update_play_button() # 1.3.6.3 [JWdJ] 2015-04-21 centralized playbutton enabling

        self.follow_score_check.SetValue(self.settings.get('follow_score', False))
        self.timing_slider.SetValue(self.settings.get('follow_score_timing_offset', 0))
        self.UpdateTimingSliderVisibility()

    def Destroy(self):
        self.renderer.destroy()
        self.renderer = None
        super(MainFrame, self).Destroy()

    def new_tune(self):
        self.document_name = _('Untitled') + ' %d' % self.untitled_number
        self.SetTitle('%s - %s' % (program_name, self.document_name))
        self.editor.ClearAll()
        self.editor.SetSavePoint()

    # 1.3.6.2 [JWdJ] 2015-02
    @property
    def current_page_index(self):
        return self.__current_page_index

    # 1.3.6.2 [JWdJ] 2015-02
    @current_page_index.setter
    def current_page_index(self, value):
        if self.__current_page_index != value:
            self.selected_note_indices = [] # 1.3.6.4 [JWDJ] 2015-07-11 having notes selected and switching to a different page resulted in (almost) nothing being played
            self.selected_note_descs = []

        self.__current_page_index = value
        if self.cur_page_combo.GetSelection() != value:
            if self.cur_page_combo.GetCount() > 0:  #[EPO] 2018-11-27 crashes in next statement if list empty
                self.cur_page_combo.Select(value)

    @property
    def current_file(self):
        return self._current_file

    @current_file.setter
    def current_file(self, value):
        self._current_file = value
        if value:
            self.add_recent_file(value)

    def add_recent_file(self, value):
        recent_files = self.settings.get('recentfiles', '').split('|')
        if recent_files[0] != value:
            if value in recent_files:
                recent_files.remove(value)
            recent_files.insert(0, value)
            if len(recent_files) > 10:
                recent_files = recent_files[:10]
            self.settings['recentfiles'] = '|'.join(recent_files)
            self.update_recent_files_menu()

    def OnPageSetup(self, evt):
        psdd = wx.PageSetupDialogData(self.printData)
        if not WX4:
            psdd.CalculatePaperSizeFromId()
        if platform.system() == 'Windows':
            psdd.EnableMargins(False)

        dlg = wx.PageSetupDialog(self, psdd)
        try:
            dlg.ShowModal()

            # this makes a copy of the wx.PrintData instead of just saving
            # a reference to the one inside the PrintDialogData that will
            # be destroyed when the dialog is destroyed
            self.printData = wx.PrintData(dlg.GetPageSetupData().GetPrintData())
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window

    def OnPrint(self, event):
        self.print_or_preview_svg(only_preview=False)

    def OnPrintPreview(self, event):
        self.print_or_preview_svg(only_preview=True)

    def print_or_preview_svg(self, only_preview):
        tunes = self.GetSelectedTunes()
        if len(tunes) == 0:
            return
        # if landscape is set in the ABC code, let that influence the page format
        abc = u''
        header = None
        title = None
        for tune in tunes:
            abc += tune.abc
            if header is None:
                header = tune.header
            if title is None:
                title = tune.title
        fullabc = header + abc
        if '%%landscape 1' in fullabc or '%%landscape true' in fullabc:
            self.printData.SetOrientation(wx.LANDSCAPE)
        if '%%landscape 0' in fullabc or '%%landscape false' in fullabc:
            self.printData.SetOrientation(wx.PORTRAIT)
        use_landscape = self.printData.GetOrientation() == wx.LANDSCAPE

        # 1.3.6 [SS] 2014-12-02  2014-12-07
        svg_files, error = AbcToSvg(abc, header, self.cache_dir,
                                    self.settings,
                                    minimal_processing=True,
                                    landscape=use_landscape)
        self.update_statusbar_and_messages()
        if svg_files:
            pdd = wx.PrintDialogData(self.printData)
            printout = MusicPrintout(svg_files, zoom=10.0, title=title, can_draw_sharps_and_flats=self.settings['can_draw_sharps_and_flats'])
            if only_preview:
                printout_for_preview = MusicPrintout(svg_files, zoom=1.0, title=title, painted_on_screen=True, can_draw_sharps_and_flats=self.settings['can_draw_sharps_and_flats'])
                self.preview = wx.PrintPreview(printout_for_preview, printout, pdd)

                if wx.Platform == "__WXMAC__":
                    self.preview.SetZoom(100)

                if WX4:
                    if not self.preview.IsOk:
                        return
                else:
                    if not self.preview.Ok():
                        return

                pfrm = wx.PreviewFrame(self.preview, self, _("EasyABC - print preview"))

                pfrm.Initialize()
                pfrm.SetPosition(self.GetPosition())
                pfrm.SetSize(self.GetSize())
                pfrm.Show(True)
            else:
                #pdd.SetToPage(len(svg_files))
                printer = wx.Printer(pdd)
                if printer.Print(self, printout, True):
                    self.printData = wx.PrintData(printer.GetPrintDialogData().GetPrintData())
                else:
                    wx.MessageBox(_("There was a problem printing.\nPerhaps your current printer is not set correctly?"), _("Printing"), wx.OK)

    def GetAbcToPlay(self):
        tune = self.GetSelectedTune()
        if tune:
            position, end_position = tune.offset_start, tune.offset_end
            if end_position > position and len(self.selected_note_descs) > 2: ## and False:
                text = self.editor.GetTextRange(position, end_position)
                notes = get_notes_from_abc(text)
                num_header_lines, first_note_line_index = self.get_num_extra_header_lines(tune)

                #FAU: Seems not needed and issue when selecting not on a second page as it is considering all lines from first page as header. jwdj/EasyABC#100
                #FAU: To be noted it was already removed from OnNoteSelectionChangedDesc
                # workaround for the fact the abcm2ps returns incorrect row numbers
                # check the row number of the first note and if it doesn't agree with the actual value
                # then pretend that we have more or less extra header lines
                #if self.music_pane.current_page.notes: # 1.3.6.2 [JWdJ] 2015-02
                #    actual_first_row = self.music_pane.current_page.notes[0][2]-1
                #    correction = (actual_first_row - first_note_line_index)
                #    num_header_lines += correction

                temp = text.replace('\r\n', ' \n').replace('\r', '\n')  # re.sub(r'\r\n|\r', '\n', text)
                line_start_offset = [m.start(0) for m in re.finditer(r'(?m)^', temp)]

                selected_note_offsets = []
                offset_chord = 0
                for (_, _, abc_row, abc_col, desc) in self.selected_note_descs:
                    abc_row -= num_header_lines
                    note_offset = line_start_offset[abc_row-1]+abc_col
                    if text[note_offset] == '[':
                        offset_chord += 1
                    if text[note_offset+offset_chord+1] == ']':
                        offset_chord = 0
                    selected_note_offsets.append(note_offset+offset_chord)

                unselected_note_offsets = [(start_offset, end_offset) for (start_offset, end_offset, _) in notes if not any(p for p in selected_note_offsets if start_offset <= p < end_offset)]
                unselected_note_offsets.sort()
                pieces = []
                pos = 0
                for start_offset, end_offset in unselected_note_offsets:
                    if start_offset > pos:
                        pieces.append(text[pos:start_offset])
                    pieces.append(' ' * (end_offset - start_offset))
                    pos = end_offset
                pieces.append(text[pos:])
                text = ''.join(pieces)

                # for some strange reason the MIDI sequence seems to be cut-off in the end if the last note is short
                # adding a silent extra note seems to fix this
                #text = text + os.linesep + '%%MIDI control 7 0' + os.linesep + 'A2'
                #FAU: the introduction of the previous line leads to have no sound at all on
                #     selection. using embedded instruction doesn' work either Thus remove it
                text = text.rstrip()# + '[I:MIDI control 7 0]' + os.linesep + 'A2'

                return (tune, text)
            return (tune, self.editor.GetTextRange(position, end_position))
        return (tune, '')

    def parse_desc(self, desc):
        parts = desc.split()
        row, col = list(map(int, parts[1].split(':')))
        return (row, col)

    def get_num_extra_header_lines(self, tune):
        # how many lines are there before the X: line in the processed ABC code?

        # 1.3.6 [SS] 2014-12-17
        lines = text_to_lines(process_abc_code(self.settings, tune.abc,
                tune.header,
                minimal_processing=not self.settings.get('reduced_margins', True)))
        num_header_lines = 0
        first_note_line_index = 0
        for i, line in enumerate(lines):
            if line.startswith('X:'):
                num_header_lines = i
                break
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not re.match(r'[A-Za-z]:', line) and not line.startswith('%'):
                first_note_line_index = i
                break

        num_header_lines += 0  # due to some oddity in newer versions of abcm2ps
        return (num_header_lines, first_note_line_index)

    def OnNoteSelectionChangedDesc(self, selected_note_indices, close_note_index=None):
        self.Raise()

        self.selected_note_indices = selected_note_indices
        self.selected_note_descs = [self.music_pane.current_page.notes[i] for i in selected_note_indices]

        self.editor.SetFocus()
        tune = self.GetSelectedTune()
        if not tune:
            return
        num_header_lines, first_note_line_index = self.get_num_extra_header_lines(tune)
        if 1==0: #self.is_really_playing and self.played_notes_timeline and selected_note_indices and close_note_index is None:
            page_index = self.music_pane.current_page.index
            note_index = min(selected_note_indices)
            pos_in_ms = next((n.start for n in self.played_notes_timeline if n.page == page_index and note_index in n.indices), -1)
            if pos_in_ms != -1:
                self.mc.Seek(pos_in_ms)

        position, end_position = tune.offset_start, tune.offset_end
        tune_start_line = self.editor.LineFromPosition(position)
        if close_note_index is None:
            row_cols = sorted([(desc[2], desc[3]) for desc in self.selected_note_descs])
        else:
            # 1.3.6.2 [JWdJ] 2015-02
            row_cols = [tuple(self.music_pane.current_page.notes[close_note_index][2:3+1])]

        #Following workaround is not needed apparently
        # workaround for the fact the abcm2ps returns incorrect row numbers
        # check the row number of the first note and if it doesn't agree with the actual value
        # then pretend that we have more or less extra header lines
        #if self.music_pane.current_page.notes:
        #    actual_first_row = self.music_pane.current_page.notes[0][2]-1
        #    num_header_lines += (actual_first_row - first_note_line_index)

        if end_position > position:
            if row_cols:
                row1, col1 = row_cols[0]
                row2, col2 = row_cols[-1]
                row1 += tune_start_line - num_header_lines - 1
                row2 += tune_start_line - num_header_lines - 1
                p1 = self.editor.PositionFromLine(row1) + col1
                p2 = self.editor.PositionFromLine(row2) + col2

                # p2 is the start of the last note, now find the end of it
                ##text = self.editor.GetTextRange(p2, p2+10)
                text = ''.join([self.editor.GetTextRange(i, i+1) for i in range(p2, p2+10)]) # this way of retrieving the next 10 chars seem more reliable in case one starts on some utf-8 char boundary or something

                notes = get_notes_from_abc(text)
                if notes:
                    p2 += notes[0][1]  # end-offset of first note found
                else:
                    p2 += 1

                # if the selection starts at a [ character and ends before the ] character, then extend it to the latter
                first_char = self.editor.GetTextRange(p1, p1+1)
                if first_char == '[' and ']' in text and text.index(']') >= p2-p1:
                    p2 = p1 + text.index(']') + 1

                # clip the positions to the start and end of the tune (for safety)
                p1, p2 = [min(max(p, position), end_position) for p in (p1, p2)]

                # scroll whole selection into view (if possible)
                self.editor.GotoPos(p1)
                self.editor.GotoPos(p2)
                self.editor.SetSelection(p1, p2)
            else:
                self.editor.SetSelectionEnd(self.editor.GetSelectionStart())

            # if this was not actually a direct click on a note, but rather in between, then place the cursor just before the closest note
            if close_note_index is not None:
                self.editor.SetSelectionEnd(self.editor.GetSelectionStart())

    def transpose_selected_note(self, amount):
        # TODO: finish this code
        notes = 'C D E F G A B c d e f g a b'.split()
        note = self.editor.GetSelectedText()
        i = notes.index(note[0])
        note = notes[i+amount] + note[1:]
        self.editor.ReplaceSelection(note)

    def OnResetView(self, evt):
        self.manager.LoadPerspective(self.default_perspective)
        self.manager.Update()
        if 'tune_col_widths' in self.settings:
            del self.settings['tune_col_widths']
        self.OnSettingsChanged()

    def OnSettingsChanged(self):
        self.save_settings()
        for frame in wx.GetApp().GetAllFrames():
            frame.load_and_apply_settings()

    def OnToggleMusicPaneMaximize(self, evt):
        pane = self.manager.GetPane('tune preview')
        if pane.IsMaximized():
            pane.Restore()
        else:
            pane.Maximize()
        self.manager.Update()
        self.Refresh()

    def OnMouseWheel(self, evt):
        if evt.ControlDown() or evt.CmdDown():
            value = self.zoom_slider.GetValue()
            if evt.GetWheelRotation() > 1:
                value += 50
            else:
                value -= 50
            if value < self.zoom_slider.GetMin():
                value = self.zoom_slider.GetMin()
            if value > self.zoom_slider.GetMax():
                value = self.zoom_slider.GetMax()
            self.zoom_slider.SetValue(value)
            self.OnZoomSlider(None)
        else:
            evt.Skip()

    def play(self):
        self.play_timer.Start(50)
        if self.settings.get('follow_score', False) and self.current_page_index != 0:
            self.select_page(0)
        wx.CallAfter(self.mc.Play)

    def stop_playing(self):
        self.mc.Stop()
        #FAU:remove highlighted notes
        self.music_pane.draw_notes_highlighted(None)
        #FAU:MIDIPLAY: play timer can be stopped no need to update progress slider
        self.play_timer.Stop()
        self.play_button.SetBitmap(self.play_bitmap)
        self.play_button.Refresh()
        self.progress_slider.SetValue(0)

    def update_playback_rate(self):
        if self.mc.supports_tempo_change_while_playing:
            tempo_multiplier = self.get_tempo_multiplier() / self.applied_tempo_multiplier
            self.mc.PlaybackRate = tempo_multiplier

    def OnBpmSlider(self, evt):
        self.update_playback_rate()

    def OnBpmSliderClick(self, evt):
        if evt.ControlDown() or evt.ShiftDown():
            self.bpm_slider.SetValue(0)
            self.OnBpmSlider(None)
        else:
            evt.Skip()

    # 1.3.6.3 [SS] 2015-05-05
    def reset_BpmSlider(self):
        self.bpm_slider.SetValue(0)
        self.bpm_slider.Enabled = True
        self.update_playback_rate() # 1.3.6.4 [JWDJ]

    def OnChangeLoopPlayback(self, event):
        loop = event.Selection != 0
        self.set_loop_midi_playback(loop)

    def OnChangeFollowScore(self, event):
        enabled = event.Selection != 0
        self.settings['follow_score'] = enabled
        self.UpdateTimingSliderVisibility()
        if enabled:
            if self.played_notes_timeline is None and self.current_midi_tune and self.current_svg_tune:
                self.played_notes_timeline = self.extract_note_timings(self.current_midi_tune, self.current_svg_tune)
        else:
            self.music_pane.draw_notes_highlighted(None)

    def UpdateTimingSliderVisibility(self):
        visible = self.follow_score_check.IsShown() and self.follow_score_check.GetValue()
        if visible ^ self.timing_slider.IsShown():
            self.timing_slider.Show(visible)

    def OnChangeTiming(self, event):
        self.settings['follow_score_timing_offset'] = event.Selection

    def OnTimingSliderClick(self, evt):
        if evt.ControlDown() or evt.ShiftDown():
            self.timing_slider.SetValue(0)
            self.settings['follow_score_timing_offset'] = 0
        else:
            evt.Skip()

    def start_midi_out(self, midifile):
        ''' Starts the Midi Player which runs as a separate thread in order not to
        hang up this program
        '''
        if self.play_music_thread is None:
            self.play_music_thread = MidiThread(self.settings)
        elif self.play_music_thread.is_busy:
            self.play_music_thread.abort()
            self.play_music_thread = MidiThread(self.settings)

        self.play_music_thread.play_midi(midifile)

    def do_load_media_file(self, path):
        if self.mc.Load(path):
            if wx.Platform == "__WXMSW__" and platform.release() != 'XP':
                # 1.3.6.3 [JWDJ] 2015-3 It seems mc.Play() triggers the OnMediaLoaded event
                self.mc.Play() # does not start playing but triggers OnMediaLoaded event
            #FAU:MIDIPLAY: added support for playback for Mac with SMF player For now kept apart from Windows
            #FAU:MIDIPLAY: %%TODO%% verify if can be merged with preceeding if
            #FAU:MIDIPLAY: 20250125 Not needed as correctly started based on OnMediaLoaded
            #elif wx.Platform == "__WXMAC__":
            #    self.mc.Play()
                #FAU:MIDIPLAY: Start timer to be able to have progress bar updated
            #    self.play_timer.Start(20)
            #    self.play_button.SetBitmap(self.pause_bitmap)
        else:
            wx.MessageBox(_("Unable to load %s: Unsupported format?") % path,
                          _("Error"), wx.ICON_ERROR | wx.OK)

    def OnMediaLoaded(self):
        def play():
            # if wx.Platform == "__WXMAC__":
            #    time.sleep(0.3) # 1.3.6.4 [JWDJ] on Mac the first note is skipped the first time. hope this helps
            # self.mc.Seek(self.play_start_offset, wx.FromStart)
            self.play_button.SetBitmap(self.pause_bitmap)
            self.progress_slider.SetRange(0, int(self.mc.Length())) #FAU:MIDIPLAY: mplay might return a float. thus forcing an int
            self.progress_slider.SetValue(0)
            self.OnBpmSlider(None)
            self.update_playback_rate()
            #FAU:MIDIPLAY: The next 'if' was when using MediaCtrl which is not used anymore. Todo: remove the corresponding code if confirmed
            #if wx.Platform == "__WXMAC__":
            #    self.mc.Seek(0)  # When using wx.media.MEDIABACKEND_QUICKTIME the music starts playing too early (when loading a file)
            #    time.sleep(0.5)  # hopefully this fixes the first notes not being played
            self.play()
        wx.CallAfter(play)

    def OnAfterStop(self):
        self.set_loop_midi_playback(False)
        # 1.3.6.3 [SS] 2015-05-04
        self.stop_playing()
        #FAU preserve latest bpm choice
        #self.reset_BpmSlider()
        #FAU20250125: Do not hide it if supported
        if self.settings['midiplayer_path']:
            self.flip_tempobox(False)
        if wx.Platform != "__WXMSW__":
            self.toolbar.Realize() # 1.3.6.4 [JWDJ] fixes toolbar repaint bug for Windows

    def OnToolRecord(self, evt):
        if self.record_thread and self.record_thread.is_running:
            self.record_thread.abort()
            self.record_thread = None		#EPO prevent segmentation error (undefined variable)
        else:
            midi_in_device_ID = self.settings.get('midi_device_in', None)
            if midi_in_device_ID is None:
                self.OnMidiSettings(None)
                midi_in_device_ID = self.settings.get('midi_device_in', None)
            midi_out_device_ID = self.settings.get('midi_device_out', None)
            if midi_in_device_ID is not None:
                metre_1, metre_2 = list(map(int, self.settings['record_metre'].split('/')))
                self.record_thread = RecordThread(self, midi_in_device_ID, midi_out_device_ID, metre_1, metre_2, bpm = self.settings['record_bpm'])
                self.record_thread.daemon = True
                self.record_thread.start()

    def OnToolStop(self, evt):
        #FAU 20250125: Cleaning, trying to centralised what is common to Stop avoiding of mon to Stop instead of multiple call
        self.OnAfterStop()
        #self.set_loop_midi_playback(False)
        #self.stop_playing()
        # 1.3.6.3 [SS] 2015-04-03
        #self.play_panel.Show(False)
        #self.flip_tempobox(False)
        #self.progress_slider.SetValue(0)
        # self.reset_BpmSlider()     #[EPO] 2018-11-20 make sticky - this is new functionality
        #if wx.Platform != "__WXMSW__":
        #    self.toolbar.Realize() # 1.3.6.4 [JWDJ] fixes toolbar repaint bug for Windows
        if self.record_thread and self.record_thread.is_running:
            self.OnToolRecord(None)
        #if self.uses_fluidsynth:
        #    self.OnAfterStop()
        self.editor.SetFocus()

    def OnSeek(self, evt):
        self.mc.Seek(self.progress_slider.GetValue())

    def OnZoomSlider(self, evt):
        old_factor = self.zoom_factor
        self.zoom_factor = float(self.zoom_slider.GetValue()) / 1000
        if self.zoom_factor != old_factor:
            self.renderer.zoom = self.zoom_factor # 1.3.6.2 [JWdJ] 2015-02
            self.music_pane.redraw()

    def OnZoomSliderClick(self, evt):
        if evt.ControlDown() or evt.ShiftDown():
            self.zoom_slider.SetValue(1000)
            self.OnZoomSlider(None)
        else:
            evt.Skip()

    def OnPlayTimer(self, evt):
        if not self.is_closed:
            if self.mc.is_playing:
                self.started_playing = True
                
                if wx.Platform == "__WXMAC__": #FAU:MIDIPLAY: Used to give the hand to MIDI player
                    delta = self.mc.IdlePlay()
                    #print(self.mc.get_songinfo)
                    if delta == 0:
                        if self.loop_midi_playback:
                            self.mc.Seek(0)
                        else:
                            self.mc.is_play_started = False
                
                offset = self.mc.Tell()
                if offset >= self.progress_slider.Max:
                    length = self.mc.Length()
                    self.progress_slider.SetRange(0, int(length)) #FAU:MIDIPLAY: mplay might return a float. thus forcing an int
                
                if self.settings.get('follow_score', False):
                    self.queue_number_follow_score += 1
                    queue_number = self.queue_number_follow_score
                    #wx.CallLater(1, self.FollowScore, offset, queue_number) #[EPO] 2018-11-20  first arg 0 causes exception
                    self.FollowScore(offset, queue_number)
                
                self.progress_slider.SetValue(offset)
            elif self.started_playing and not self.mc.is_paused: #and self.uses_fluidsynth 
                self.started_playing = False
                wx.CallLater(500, self.OnAfterStop)

    def FollowScore(self, offset, queue_number):
        if self.queue_number_follow_score != queue_number:
            return

        if not self.played_notes_timeline:
            return

        page = self.music_pane.current_page
        if not page:
            return

        offset += self.settings.get('follow_score_timing_offset', 0)

        current_time_slice = self.current_time_slice
        if current_time_slice and current_time_slice.start <= offset < current_time_slice.stop:
            return

        if current_time_slice is None or offset < current_time_slice.start:  # first time or after rewind
            self.played_notes_iter = iter(self.played_notes_timeline)

        for time_slice in self.played_notes_iter:
            if time_slice.start <= offset < time_slice.stop:
                current_time_slice = time_slice
                break

        self.current_time_slice = current_time_slice
        if current_time_slice.page == self.current_page_index:
            try:
                self.music_pane.draw_notes_highlighted(current_time_slice.indices, highlight_follow=True)
            except:
                pass
                # self.music_and_score_out_of_sync()

        # turning pages and going to next line has to be done slighty earlier
        if self.mc.unit_is_midi_tick:
            future_offset = offset + 480  # one quarter note should do
        else:
            future_offset = offset + 300  # 0.3 seconds should do
        future_time_slice = self.future_time_slice

        if future_time_slice is None or not (future_time_slice.start <= future_offset < future_time_slice.stop):
            if future_time_slice is None or future_offset < future_time_slice.start:
                self.future_notes_iter = iter(self.played_notes_timeline)

            future_time_slice = None
            for time_slice in self.future_notes_iter:
                if time_slice.start <= future_offset < time_slice.stop:
                    future_time_slice = time_slice
                    break

            self.future_time_slice = future_time_slice

        if future_time_slice is not None:
            try:
                if future_time_slice.page != self.current_page_index:
                    self.select_page(future_time_slice.page)
                    self.scroll_to_notes(self.music_pane.current_page, future_time_slice.indices)
                elif future_time_slice.svg_row != self.last_played_svg_row and future_time_slice.indices:
                    self.last_played_svg_row = future_time_slice.svg_row
                    self.scroll_to_notes(self.music_pane.current_page, future_time_slice.indices)
            except:
                pass
                # self.music_and_score_out_of_sync()

    def scroll_to_notes(self, page, indices):
        if not indices:
            return
        x, y, _, _, _ = page.notes[max(indices)]
        #if len(indices) > 1:
        #    x2, y2, _, _, _ = page.notes[min(indices)]
        #    x = (x + x2) // 2
        #    y = (y + y2) // 2
        self.scroll_music_pane(x, y)

    def music_and_score_out_of_sync(self):
        self.played_notes_timeline = None
        self.current_time_slice = None
        self.future_time_slice = None

    def OnRecordBpmSelected(self, evt):
        menu = evt.EventObject
        item = menu.FindItemById(evt.GetId())
        self.settings['record_bpm'] = int(item.GetItemLabelText())
        if self.record_thread:
            self.record_thread.bpm = self.settings['record_bpm']

    def OnRecordMetreSelected(self, evt):
        menu = evt.EventObject
        item = menu.FindItemById(evt.GetId())
        self.settings['record_metre'] = item.GetItemLabelText()


    # 1.3.6.3 [SS] 2015-05-03
    def flip_tempobox(self, state):
        ''' rearranges the toolbar depending on whether a midi file is played using the
            mc media player'''
        self.show_toolbar_panel(self.progress_slider.Parent, state)
        self.loop_check.Show(state)
        self.follow_score_check.Show(state)
        self.UpdateTimingSliderVisibility()
        self.toolbar.Realize()
        self.manager.Update()


    def show_toolbar_panel(self, panel, visible):
        panel.Show(visible)

    def setup_toolbar(self):
        self.toolbar = aui.AuiToolBar(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, style=aui.AUI_TB_NO_AUTORESIZE)#, agwStyle=aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW)
        try:
            self.toolbar.SetAGWWindowStyleFlag(aui.AUI_TB_PLAIN_BACKGROUND)
        except:
            pass
        self.id_play = 3000
        self.id_stop = 3001
        self.id_record = 3002
        self.id_refresh = 3003
        self.id_dynamics = 3004
        self.id_directions = 3005
        self.id_ornamentations = 3006
        self.id_add_tune = 3007
        self.id_abc_assist = 3008

        self.bpm_menu = bpm_menu = create_menu([], parent=self)
        for i, bpm in enumerate([30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140]):
            append_menu_item(bpm_menu, str(bpm), '', self.OnRecordBpmSelected, kind=wx.ITEM_RADIO)

        self.metre_menu = metre_menu = create_menu([], parent=self)
        for i, metre in enumerate(['2/4', '3/4', '4/4', '5/4']):
            append_menu_item(metre_menu, metre, '', self.OnRecordMetreSelected, kind=wx.ITEM_RADIO)

        self.record_popup = record_popup = create_menu([], parent=self)
        append_submenu(record_popup, _('Beats per minute'), bpm_menu)
        append_submenu(record_popup, _('Metre'), metre_menu)

        button_style = platebtn.PB_STYLE_DEFAULT | platebtn.PB_STYLE_NOBG
        image_path = self.get_image_path()
        self.play_bitmap = wx.Image(os.path.join(image_path, 'toolbar_play.png')).ConvertToBitmap()
        self.pause_bitmap = wx.Image(os.path.join(image_path, 'toolbar_pause.png')).ConvertToBitmap()
        self.play_button = play = platebtn.PlateButton(self.toolbar, self.id_play, "", self.play_bitmap, style=button_style)
        self.stop_button = stop = platebtn.PlateButton(self.toolbar, self.id_stop, "", wx.Image(os.path.join(image_path, 'toolbar_stop.png')).ConvertToBitmap(), style=button_style)
        self.record_btn = record = platebtn.PlateButton(self.toolbar, self.id_record, "", wx.Image(os.path.join(image_path, 'toolbar_record.png')).ConvertToBitmap(), style=button_style)

        play.SetHelpText('Play (F6)')
        record.SetMenu(record_popup)
        self.toolbar.AddControl(play)
        self.toolbar.AddControl(stop)
        self.toolbar.AddControl(record)
        self.toolbar.AddSeparator()

        # 1.3.6.3 [JWdJ] 2015-04-26 turned off abc assist for it is not finished yet
        abc_assist = platebtn.PlateButton(self.toolbar, self.id_abc_assist, "", wx.Image(os.path.join(image_path, 'bulb.png')).ConvertToBitmap(), style=button_style)
        abc_assist.SetHelpText(_('ABC assist'))
        abc_assist.SetToolTip(wx.ToolTip(_('ABC assist'))) # 1.3.7.0 [JWdJ] 2015-12
        self.toolbar.AddControl(abc_assist, label=_('ABC assist'))
        self.Bind(wx.EVT_BUTTON, self.OnToolAbcAssist, abc_assist) # 1.3.6.2 [JWdJ] 2015-03

        # ornamentations = self.toolbar.AddSimpleTool(self.id_ornamentations, "", wx.Image(os.path.join(image_path, 'toolbar_ornamentations.png')).ConvertToBitmap(), _('Note ornaments'))
        # dynamics = self.toolbar.AddSimpleTool(self.id_dynamics, "", wx.Image(os.path.join(image_path, 'toolbar_dynamics.png')).ConvertToBitmap(), _('Dynamics'))
        # directions = self.toolbar.AddSimpleTool(self.id_directions, "", wx.Image(os.path.join(image_path, 'toolbar_directions.png')).ConvertToBitmap(), _('Directions'))

        # self.Bind(wx.EVT_TOOL, self.OnToolDynamics, dynamics)
        # self.Bind(wx.EVT_TOOL, self.OnToolOrnamentation, ornamentations)
        # self.Bind(wx.EVT_TOOL, self.OnToolDirections, directions)

        self.toolbar.AddSeparator()

        self.zoom_slider = self.add_slider_to_toolbar(_('Zoom'), False, value=1000, minValue=500, maxValue=3000, size=(130, -1))

        #wx_slider_set_tick_freq(self.zoom_slider, 10)
        self.Bind(wx.EVT_SLIDER, self.OnZoomSlider, self.zoom_slider)
        self.zoom_slider.Bind(wx.EVT_LEFT_DOWN, self.OnZoomSliderClick)

        # 1.3.6.2 [JWdJ] 2015-02-15 text 'Page' was drawn multiple times. Replaced StaticLabel with StaticText
        self.cur_page_combo = self.add_combobox_to_toolbar(_('Page'), choices=[' 1 / 1 '], style=wx.CB_DROPDOWN | wx.CB_READONLY)
        if self.cur_page_combo.GetCount() > 0:  #EPO
            self.cur_page_combo.Select(0)
        self.Bind(wx.EVT_COMBOBOX, self.OnPageSelected, self.cur_page_combo)
        # 1.3.6.3 [SS] 2015-05-03
        self.bpm_slider = self.add_slider_to_toolbar(_('Tempo'), False, value=0, minValue=-100, maxValue=100, size=(130, -1))
        if wx.Platform == "__WXMSW__":
            self.bpm_slider.SetTick(0)  # place a tick in the middle for neutral tempo
        self.progress_slider = self.add_slider_to_toolbar(_('Play position'), False, value=0, minValue=0, maxValue=100, size=(130, -1))

        self.loop_check = self.add_checkbox_to_toolbar(_('Loop'))
        self.loop_check.Bind(wx.EVT_CHECKBOX, self.OnChangeLoopPlayback)

        self.follow_score_check = self.add_checkbox_to_toolbar(_('Follow score'))
        self.follow_score_check.Bind(wx.EVT_CHECKBOX, self.OnChangeFollowScore)

        self.timing_slider = self.add_slider_to_toolbar('', False, value=0, minValue=-1000, maxValue=1000, size=(130, -1))
        self.timing_slider.Bind(wx.EVT_SLIDER, self.OnChangeTiming)
        self.timing_slider.Bind(wx.EVT_LEFT_DOWN, self.OnTimingSliderClick)

        self.Bind(wx.EVT_SLIDER, self.OnSeek, self.progress_slider)
        self.Bind(wx.EVT_SLIDER, self.OnBpmSlider, self.bpm_slider)
        self.bpm_slider.Bind(wx.EVT_LEFT_DOWN, self.OnBpmSliderClick)

        play.Bind(wx.EVT_LEFT_DOWN, self.OnToolPlay)
        play.Bind(wx.EVT_LEFT_DCLICK, self.OnToolPlayLoop)
        self.Bind(wx.EVT_BUTTON, self.OnToolStop, stop)
        self.Bind(wx.EVT_BUTTON, self.OnToolRecord, record)

        self.popup_upload = self.create_upload_context_menu()

        # 1.3.6.3 [JWDJ] fixes toolbar repaint bug
        self.flip_tempobox(False)
        self.cur_page_combo.Parent.Show(False)

        self.manager.AddPane(self.toolbar, aui.AuiPaneInfo().
                            Name("tb2").Caption("Toolbar2").
                            ToolbarPane().Top().Floatable(True).Dockable(False))

    def add_slider_to_toolbar(self, label_text, show_value, *args, **kwargs):
        panel = wx.Panel(self.toolbar, -1)
        controls = [wx.Slider(panel, wx.ID_ANY, *args, **kwargs)]
        if show_value:
            controls.append(wx.StaticText(panel, wx.ID_ANY, str(kwargs['value'])))
        self.add_label_and_controls_to_panel(panel, label_text, controls)
        self.toolbar.AddControl(panel)
        if len(controls) == 1:
            return controls[0]
        else:
            return tuple(controls)

    def add_combobox_to_toolbar(self, label_text, *args, **kwargs):
        panel = wx.Panel(self.toolbar, -1)
        control = wx.ComboBox(panel, wx.ID_ANY, *args, **kwargs)
        self.add_label_and_controls_to_panel(panel, label_text, [control])
        self.toolbar.AddControl(panel)
        return control

    @staticmethod
    def add_label_and_controls_to_panel(panel, label_text, controls):
        box = wx.BoxSizer(wx.HORIZONTAL)
        if label_text:
            box.Add(wx.StaticText(panel, wx.ID_ANY, u'{0}: '.format(label_text)), flag=wx.ALIGN_CENTER_VERTICAL)
        for control in controls:
            box.Add(control, flag=wx.ALIGN_CENTER_VERTICAL)
        box.AddSpacer(20)
        panel.SetSizer(box)
        panel.SetAutoLayout(True)

    def add_checkbox_to_toolbar(self, *args, **kwargs):
        control = wx.CheckBox(self.toolbar, wx.ID_ANY, *args, **kwargs)
        self.toolbar.AddControl(control)
        return control

    def OnRecordStop(self, evt):
        notes = evt.GetValue()
        if notes:
            return self.handle_midi_conversion(notes=notes)

    def OnDoReMiModeChange(self, evt=None):
        if self.mni_TA_do_re_mi.IsChecked():
            self.SetStatusText(_("&Do-re-mi mode").replace('&', ''))
        else:
            self.SetStatusText('')

    def generate_incipits_abc(self):
        def get_num_music_lines_in_tune(abc):
            try:
                notes = re.split(r'K:.*\s*', abc, 1)[1]  # extract part after first K: field
                notes = re.sub(r'\[\w:.*?\]', '', notes) # remove fields
                return len([l for l in text_to_lines(notes) if l.strip()])  # return number of non-empty lines
            except IndexError:
                return 1

        result = []
        for i in range(self.tune_list.GetItemCount()):
            tune = self.GetTune(i)

            # make a copy of the tune header in order to be able to restore it after the incip extraction
            lines = text_to_lines(tune.abc)
            header = []
            title_count = 0
            for line in lines:
                if re.match('[a-zA-Z]:', line):
                    if line[0] == 'T':
                        title_count += 1
                        if title_count > self.settings['incipits_numtitles']:
                            continue
                    if line[0] != 'W':
                        header.append(line)
                elif re.match(r'\s*%', line):
                    pass
                else:
                    break

            incipit_parts = extract_incipit(os.linesep.join([tune.header, tune.abc]),
                                            num_bars=self.settings['incipits_numbars'],
                                            num_repeats=self.settings['incipits_numrepeats'])
            #abc = '[I:staffbreak]'.join(incipit_parts)
            abc = (os.linesep+'[T:][M:none]'+os.linesep).join(incipit_parts)
            abc = os.linesep.join(header + [abc, ''])
            result.append(abc)

        # extract file header
        lines = []
        editor = self.editor
        get_line = editor.GetLine
        for i in xrange(editor.GetLineCount()):
            line = get_line(i)
            if line.startswith('X:') or line.startswith('T:'):
                break
            elif re.match(r'%%.*|[a-zA-Z_]:.*', line):
                lines.append(line.rstrip())

        lines.append('')
        lines.append('%%topspace 0.0cm')
        lines.append('%%staffsep 0.7cm')
        lines.append('%%titleformat T-1') # C1 S1')
        lines.append('%%maxshrink 1.4')
        lines.append('%%musiconly 1')
        lines.append('%%printtempo 0')
        lines.append('%%titlefont Helvetica-Oblique 16')
        lines.append('%%subtitlefont Helvetica-Oblique 13')
        lines.append('')
        lines.append('')
        file_header = lines[:]
        lines.extend(result)
        abc_code = os.linesep.join(lines)

        if self.settings['incipits_sortfields']:
            sort_fields = re.findall('[A-Za-z]', self.settings['incipits_sortfields'])
            abc_code = sort_abc_tunes(abc_code, sort_fields)

        if self.settings['incipits_twocolumns']:
            parts = file_header

            # extract each tune (incipit)
            pos = [m.start(1) for m in re.compile('(^X:)', re.M).finditer(abc_code)] + [20 * 1024**2]
            all_tunes = [abc_code[s1:s2].strip() + os.linesep for s1, s2 in zip(pos[0:], pos[1:])]

            while all_tunes:
                # extract left column tunes with a total of max <<incipits_rows>> rows
                num_lines = 0
                left_tunes = []
                while all_tunes:
                    n = get_num_music_lines_in_tune(all_tunes[0])
                    if num_lines == 0 or num_lines + n <= self.settings['incipits_rows']:
                        left_tunes.append(all_tunes.pop(0))
                        num_lines += n
                    else:
                        break

                # extract right column tunes with a total of max <<incipits_rows>> rows
                num_lines = 0
                right_tunes = []
                while all_tunes:
                    n = get_num_music_lines_in_tune(all_tunes[0])
                    if num_lines == 0 or num_lines + n <= self.settings['incipits_rows']:
                        right_tunes.append(all_tunes.pop(0))
                        num_lines += n
                    else:
                        break

                left_col = ['%%multicol start',
                            '%%rightmargin 11.5cm',
                            '%%leftmargin 1.5cm', ''] + left_tunes
                right_col = ['%%multicol new',
                            '%%rightmargin 1.5cm',
                            '%%leftmargin 11.5cm', ''] + right_tunes + ['', '%%multicol end', '%%newpage', '']
                parts.extend(left_col)
                parts.extend(right_col)
            abc_code = os.linesep.join(parts)

        return abc_code

    def OnGenerateIncipits(self, evt):
        dlg = IncipitsFrame(self, self.settings)
        try:
            modal_result = dlg.ShowModal()
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window
        if modal_result != wx.ID_OK:
            return

        self.SetCursor(wx.HOURGLASS_CURSOR)
        abc = self.generate_incipits_abc()
        self.SetCursor(wx.STANDARD_CURSOR)

        frame = self.OnNew()
        frame.editor.SetText(abc)
        frame.editor.SetSavePoint()
        frame.editor.EmptyUndoBuffer()
        frame.document_name = self.document_name + ' ' + _('incipits')
        frame.SetTitle('%s - %s' % (program_name, frame.document_name))
        frame.UpdateTuneList()
        frame.tune_list.Select(0)

    def OnViewIncipits(self, evt):
        dlg = IncipitsFrame(self, self.settings)
        try:
            modal_result = dlg.ShowModal()
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window
        if modal_result != wx.ID_OK:
            return
        try:
            self.SetCursor(wx.HOURGLASS_CURSOR)
            abc = self.generate_incipits_abc()
            pdf_file = AbcToPDF(self.settings, abc, '', self.cache_dir, self.settings.get('abcm2ps_extra_params', ''),
                                                         self.settings.get('abcm2ps_path', ''),
                                                         self.settings.get('gs_path',''),
                                                         #self.settings.get('ps2pdf_path',''),
                                                         self.settings.get('abcm2ps_format_path', ''),
                                                         generate_toc = True)
            if pdf_file:
                launch_file(pdf_file)
            else:
                wx.MessageBox(_("Error: there was some trouble saving the file."), _("File could not be saved properly"), wx.OK)
        finally:
            self.SetCursor(wx.STANDARD_CURSOR)

    def OnSortTunes(self, evt):
        dlg = wx.TextEntryDialog(
            self, _('Which field(s) do you want to sort the tunes by? (eg. T for title)'), _('Sort tunes'), 'T')
        try:
            if dlg.ShowModal() == wx.ID_OK:
                sort_fields = re.findall('[A-Za-z]', dlg.GetValue())
                text = sort_abc_tunes(self.editor.GetText(), sort_fields)
                self.editor.BeginUndoAction()
                self.editor.SetText(text)
                self.editor.EndUndoAction()
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window

    def OnRenumberTunes(self, evt):
        dlg = wx.TextEntryDialog(
            self, _('Please specify the index of the first tune: '), _('Renumber X: fields'), '1')
        try:
            if dlg.ShowModal() == wx.ID_OK:
                xnum = int(dlg.GetValue())
                lines = text_to_lines(self.editor.GetText())
                for i in range(len(lines)):
                    if re.match(r'X:\s*\d+\s*$', lines[i]):
                        if lines[i].startswith('X: '):
                            lines[i] = 'X: %d' % xnum
                        else:
                            lines[i] = 'X:%d' % xnum
                        xnum += 1
                self.editor.BeginUndoAction()
                self.editor.SetText(os.linesep.join(lines))
                self.editor.EndUndoAction()
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window

    # 1.3.6 [SS] 2014-11-21
    def OnSearchDirectories(self, evt):
        self.show_search_in_files(True)

    def show_search_in_files(self, show):
        panel = self.search_files_panel
        if not panel:
            panel = AbcSearchPanel(self, self.settings, self.statusbar)
            self.search_files_panel = panel

        pane = self.manager.GetPane(self.search_files_panel)
        if not pane.IsOk():
            pane = aui.AuiPaneInfo().Name("search files").Caption(_("Find in Files")).MaximizeButton(False).MinimizeButton(False).CloseButton(True).BestSize((300, 600)).Right().Layer(1)
            self.manager.AddPane(self.search_files_panel, pane)
            self.manager.Update()

        if show:
            self.manager.RestorePane(pane)
            self.manager.Update()
        else:
            if self.abc_assist_panel.IsShown():
                self.abc_assist_panel.Hide()
            if pane.IsOk():
                self.manager.DetachPane(self.abc_assist_panel)
        self.manager.Update()


    # def OnUploadTune(self, evt):
    #     tune = self.GetSelectedTune()
    #     if tune:
    #         if not self.author:
    #             dialog = wx.TextEntryDialog(self, _('Please enter your full name (your FolkWiki entries will henceforth be associated with this name): '), _('Enter your name'), '')
    #             if dialog.ShowModal() != wx.ID_OK:
    #                 return
    #             self.author = dialog.GetValue().strip()

    #         url = upload_tune(tune.abc, self.author)
    #         webbrowser.open(url)

    def GetFileNameForTune(self, tune, file_extension):
        filename = tune.title
        if not filename:
            filename = '%s' % tune.xnum
        filename = re.sub(r'[\\/:"*?<>|]', ' ', filename).strip()
        filename = filename + file_extension
        return filename

    def OnExportToClipboard(self, evt):
        abc = os.linesep.join(tune.abc for tune in self.GetSelectedTunes(add_file_header=False))
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(abc))
            wx.TheClipboard.Close()

    def OnExportMidi(self, evt):
        self.export_tunes(_('Midi file'), '.mid', self.export_midi, only_selected=True)

    #Add an export all tunes to MIDI option
    def OnExportAllMidi(self, evt):
        self.export_tunes(_('Midi file'), '.mid', self.export_midi, only_selected=False)

    def export_midi(self, tune, filepath):
        tempo_multiplier = self.get_tempo_multiplier()
        midi_tune = AbcToMidi(tune.abc, tune.header, self.cache_dir, self.settings, self.statusbar, tempo_multiplier)
        if midi_tune:
            try:
                shutil.copy(midi_tune.midi_file, filepath)
                return True
            except:
                pass
                # print('failed to create %s' % filepath)
            finally:
                midi_tune.cleanup()
        return False

    def OnExportToMP3(self, evt):
        if self.uses_fluidsynth:
            self.export_tunes(_('MP3 file'), '.mp3', self.export_mp3, only_selected=True)
        else:
            self.ReportFluidSynthIsMissing()

    def OnExportToAAC(self, evt):
        if self.uses_fluidsynth:
            self.export_tunes(_('AAC file'), '.m4a', self.export_aac, only_selected=True)
        else:
            self.ReportFluidSynthIsMissing()

    def OnExportToWave(self, evt):
        if self.uses_fluidsynth:
            self.export_tunes(_('Wave file'), '.wav', self.export_wave, only_selected=True)
        else:
            self.ReportFluidSynthIsMissing()

    def ReportFluidSynthIsMissing(self):
            wx.MessageBox(_("Both the FluidSynth library and a valid SoundFont (see menu Settings -> ABC Settings -> File settings) are required for exporting to a wave file."),
                          _("Unable to export"), wx.ICON_INFORMATION | wx.OK)

    def export_wave(self, tune, filepath):
        tempo_multiplier = self.get_tempo_multiplier()
        midi_tune = AbcToMidi(tune.abc, tune.header, self.cache_dir, self.settings, self.statusbar, tempo_multiplier)
        if midi_tune:
            try:
                self.mc.render_to_file(midi_tune.midi_file, filepath)
                return True
            except:
                self.statusbar.SetStatusText(_('Failed to create {0}').format(filepath))
            finally:
                midi_tune.cleanup()
        return False

    def export_mp3(self, tune, filepath):
        self.export_ffmpeg(tune, filepath)

    def export_aac(self, tune, filepath):
        self.export_ffmpeg(tune, filepath)

    def export_ffmpeg(self, tune, filepath):
        global execmessages
        ffmpeg_path = self.settings['ffmpeg_path']
        if ffmpeg_path and os.path.exists(ffmpeg_path):
            base_name, ext = os.path.splitext(filepath)
            tmp_file = base_name + '.wav'
            if not self.export_wave(tune, tmp_file):
                return

            if os.path.exists(tmp_file):
                cmd = [ffmpeg_path, '-y', '-nostdin', '-i', tmp_file, '-vn', filepath]
                if ext == '.m4a':
                    cmd = [ffmpeg_path, '-y', '-nostdin', '-i', tmp_file, '-c:a', 'aac', '-q:a', '0.5', filepath]

                if os.path.exists(filepath):
                    os.remove(filepath)
                execmessages += '\nffmpeg\n' + " ".join(cmd)
                stdout_value, stderr_value, returncode = get_output_from_process(cmd)
                if returncode != 0:
                    execmessages += stderr_value
                    execmessages += stdout_value
                    print(stderr_value)
                    print(stdout_value)
                    print(returncode)

                if os.path.exists(tmp_file):
                    os.remove(tmp_file)
        else:
            dlg = wx.MessageDialog(self, _('ffmpeg was not found here. Go to settings and indicate the path'), _('Warning'), wx.OK)
            dlg.ShowModal()

    #Add an export all tunes to individual PDF option
    def OnExportAllPDFFiles(self, evt):
        self.export_pdf_tunes(only_selected=False)

    def OnExportPDF(self, evt):
        self.export_pdf_tunes(only_selected=True)

    def OnExportAllPDF(self, evt):
        self.export_pdf_tunes(only_selected=False, single_file=True)

    def OnExportSelectedToSinglePDF(self, evt):
        self.export_pdf_tunes(only_selected=True, single_file=True)

    def export_pdf(self, tune, filepath):
        pdf_file = AbcToPDF(self.settings, tune.abc, tune.header, self.cache_dir, self.settings.get('abcm2ps_extra_params', ''),
                                           self.settings.get('abcm2ps_path', ''),
                                           self.settings.get('gs_path',''),
                                           #self.settings.get('ps2pdf_path',''),
                                           self.settings.get('abcm2ps_format_path', ''))
        if pdf_file:
            return self.copy_to_destination_and_launch_file(pdf_file, filepath)

        return False

    def export_pdf_tunes(self, only_selected=False, single_file=False):
        gs_path = self.settings.get('gs_path')
        if not gs_path:
            dlg = wx.MessageDialog(self, _('EasyABC needs an external program called GhostScript to generate PDFs. You can get it from https://www.ghostscript.com/download/'), _('Warning'), wx.OK)
            dlg.ShowModal()
            return
        if not os.path.exists(gs_path):
            dlg = wx.MessageDialog(self, _('ghostscript was not found here. Go to settings and indicate the path'), _('Warning'), wx.OK)
            dlg.ShowModal()
            return

        self.export_tunes(_('PDF file'), '.pdf', self.export_pdf, only_selected=only_selected, single_file=single_file)

    def OnExportSVG(self, evt):
        self.export_tunes(_('SVG file'), '.svg', self.export_svg, only_selected=True)

    def export_svg(self, tune, filepath):
        # 1.3.6 [SS] 2014-12-02 2014-12-07
        svg_files, error = AbcToSvg(tune.abc, tune.header,
                                             self.cache_dir,
                                             self.settings,
                                             target_file_name=filepath,
                                             with_annotations=False)
        if svg_files:
            return launch_file(svg_files[0])
        return False

    def OnExportMusicXML(self, evt):
        self.export_tunes_to_musicxml(only_selected=True)

    def OnExportAllMusicXML(self, evt):
        self.export_tunes_to_musicxml(only_selected=False)

    def export_tunes_to_musicxml(self, only_selected):
        mxl = self.settings['xmlcompressed']
        global execmessages
        execmessages = u'abc_to_mxl   compression = ' + str(mxl) + '\n'
        extension = '.xml'
        filetype = _('MusicXML')
        if mxl:
            extension = '.mxl'
            filetype = _('Compressed MusicXML')

        self.export_tunes(filetype, extension, self.export_musicxml, only_selected=only_selected)

    def export_musicxml(self, tune, filepath):
        global execmessages
        mxl = self.settings['xmlcompressed']
        pageFormat = []
        errors = []
        # 1.3.6.3 [SS] 2015-05-07
        info_messages = []
        try:
            abc_to_xml(tune.header + os.linesep + tune.abc, filepath, mxl, pageFormat, info_messages)
        except Exception as e:
            error_msg = traceback.format_exc() + os.linesep + os.linesep.join(errors)
            mdlg = ErrorFrame(self, _('Error during conversion of X:{0} ("{1}"): {2}').format(tune.xnum, tune.title, error_msg))
            result = mdlg.ShowModal()
            mdlg.Destroy()
            return result == wx.ID_OK  # if ok is pressed, continue to process other tunes, if cancel, do not process more tunes

        # 1.3.6 [SS] 2014-12-10
        for infoline in info_messages:
            execmessages += infoline
        return True

    def OnExportHTML(self, evt):
        self.export_tunes(_('HTML file'), '.html', self.export_html, only_selected=True)

    def OnExportInteractiveHTML(self, evt):
        self.export_tunes(_('HTML file (interactive)'), '.html', self.export_interactive_html, only_selected=True, single_file=True)

    def export_html(self, tune, filepath):
        # 1.3.6 [SS] 2014-12-02 2014-12-07
        svg_files, error = AbcToSvg(tune.abc, tune.header,
                                             self.cache_dir,
                                             self.settings,
                                             with_annotations=False)
        if svg_files:
            f = codecs.open(filepath, 'wb', 'UTF-8')
            f.write('<html xmlns="http://www.w3.org/1999/xhtml">\n')
            f.write('<head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/> </head>\n')
            f.write('<body>\n\n')
            for fn in svg_files:
                svg = codecs.open(fn, 'rb', 'UTF-8').read()
                svg = svg[svg.index('<svg'):]
                f.write(svg)
                f.write('\n\n')
            f.write('</body></html>')
            f.close()
            return launch_file(filepath)
        return False

    def comment_pageheight(self, abc):
        return re.sub(r'(?m)^%%pageheight\b', '% %%pageheight', abc)

    def export_interactive_html(self, tune, filepath):
        f = codecs.open(filepath, 'wb', 'UTF-8')
        f.write('<!DOCTYPE HTML>\n')
        f.write('<html>\n<head>\n')
        f.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>\n')
        f.write('<script src="http://moinejf.free.fr/js/abcweb-1.js"></script>\n')
        f.write('<script src="http://moinejf.free.fr/js/snd-1.js"></script>\n')
        f.write('<style type="text/css">\n')
        f.write('svg {display:block}\n')
        f.write('@media print{body{margin:0;padding:0;border:0}.nop{display:none}}\n')
        f.write('</style>\n')
        f.write('</head>\n<body>\n<script type="text/vnd.abc">\n\n\n')
        file_header = self.comment_pageheight(tune.header)
        f.write(file_header)
        f.write('\n')
        abc = tune.abc
        if '%%MIDI drummap' in abc:
            abc = re.sub(r'%%MIDI drummap\s+(?P<note>\^[A-Ga-g])\s+(?P<midinote>\d+)', r'%%percmap \g<note> \g<midinote> x', abc)
            abc = re.sub(r'%%MIDI drummap\s+(?P<note>_[A-Ga-g])\s+(?P<midinote>\d+)', r'%%percmap \g<note> \g<midinote> circle-x', abc)
            abc = abc.replace('%%MIDI drummap ', '%%percmap ')

        if self.settings.get('play_chords') or '%%MIDI gchord' in abc:
            # prepend gchordon to each tune body
            abclines = text_to_lines(abc)
            new_abc_lines = []
            header_started = False
            for line in abclines:
                new_abc_lines.append(line)
                if line.startswith('X:'):
                    header_started = True
                elif line.startswith('K:') and header_started:
                    new_abc_lines.append('%%MIDI gchordon')
                    header_started = False
            abc = '\n'.join(new_abc_lines)
        f.write(self.comment_pageheight(abc))
        f.write('\n\n\n</script>\n</body>\n</html>')
        f.close()
        return launch_file(filepath)

    def OnExportAllHTML(self, evt):
        self.export_tunes(_('HTML file'), '.html', self.export_html, only_selected=False, single_file=True)

    def OnExportAllInteractiveHTML(self, evt):
        self.export_tunes(_('HTML file'), '.html', self.export_interactive_html, only_selected=False, single_file=True)

    def OnExportAllEpub(self, evt):
        tunes = []
        for i in range(self.tune_list.GetItemCount()):
            self.tune_list.Select(i)
            tunes.append(self.GetSelectedTune())
        if tunes:
            if self.current_file:
                filename = os.path.splitext(self.current_file)[0] + '.epub'
            else:
                filename = ''
            dlg = wx.FileDialog(self, message=_("Export all tunes as ..."), defaultFile=os.path.basename(filename), wildcard=_("Epub file") + " (*.epub)|*.epub", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            try:
                if dlg.ShowModal() == wx.ID_OK:
                    self.SetCursor(wx.HOURGLASS_CURSOR)
                    path = dlg.GetPath()
                    zip = zipfile.ZipFile(path, 'w')
                    zip.writestr('mimetype', 'application/epub+zip')
                    zip.writestr('META-INF/container.xml',
                                 '''<?xml version="1.0"?>
                                        <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
                                            <rootfiles> <rootfile full-path="OEBPS/book.opf" media-type="application/oebps-package+xml" /> </rootfiles>
                                        </container>''')
                    opf = '''<package unique-identifier="pub-id">
                            <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
                                <dc:identifier id="pub-id">urn:uuid:A1B0D67E-2E81-4DF5-9E67-A64CBE366809</dc:identifier>
                                <dc:title>ABC tunebook</dc:title>
                                <dc:language>en</dc:language>
                                <meta property="dcterms:modified">2012-05-01T12:00:00Z</meta>
                            </metadata>
                            <manifest>
                              %s
                            </manifest>
                        </package>'''

                    f = StringIO()
                    f.write('''<html xmlns="http://www.w3.org/1999/xhtml">''')
                    f.write('''<head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
                      <style type="text/css">
                        svg { float: left; clear: both; }
                      </style>
                    </head>
                    <body>\n\n''')
                    num_pages = []
                    for i, tune in enumerate(tunes):
                        # 1.3.6 [SS] 2014-12-02 2014-12-07
                        svg_files, error = AbcToSvg(tune.abc, tune.header,
                                                             self.cache_dir,
                                                             self.settings,
                                                             with_annotations=False,
                                                             one_file_per_page=False)
                        self.update_statusbar_and_messages()
                        if svg_files:
                            for j, fn in enumerate(svg_files):
                                zip.write(fn, 'OEBPS/Contents/tune%.2d_page%.2d.svg' % (i+1, j+1))
                    f.write('</body></html>')
                    zip.close()
                    self.SetCursor(wx.STANDARD_CURSOR)
                    #launch_file(path)
            finally:
                dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window

    def copy_to_destination_and_launch_file(self, file_name, destination_path):
        try:
            shutil.copy(file_name, destination_path)
            return launch_file(destination_path)
        except IOError as ex:
            pass
            # print(u'Failed to create %s: %s' % (destination_path.encode('utf-8'), os.strerror(ex.errno)))
        return False

    def OnExportToABC(self, evt):
        self.export_tunes(_('ABC file'), '.abc', self.export_abc, only_selected=True, single_file=True)

    def export_abc(self, tune, filepath):
        f = codecs.open(filepath, 'wb', 'utf-8')
        f.write(tune.header)
        f.write(os.linesep)
        f.write(tune.abc)
        f.close()
        frame = self.OnNew()
        frame.load(filepath.decode('utf-8'))
        return True

    def export_tune(self, tune, file_type, extension, convert_func, path, show_save_dialog=True):
        # 1.3.6.3 [SS] 2015-05-07
        global execmessages
        filename = self.GetFileNameForTune(tune, extension)
        filepath = os.path.join(path or '', filename)
        filepath = ensure_file_name_does_not_exist(filepath)

        if show_save_dialog:
            wildcard = u'{0} (*{1})|*{1}'.format(file_type, extension)
            default_dir, filename = os.path.split(filepath)
            dlg = wx.FileDialog(self, message=_("Export tune as ..."), defaultFile=filename, defaultDir=default_dir, wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            try:
                if dlg.ShowModal() == wx.ID_OK:
                    filepath = dlg.GetPath()
                else:
                    return False
            finally:
                dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window

        if not PY3:
            filepath = filepath.encode('utf-8')
        if convert_func(tune, filepath):
            execmessages = execmessages + u'creating '+ filepath + u'\n'
            # 1.3.6 [SS] 2014-12-08
            self.statusbar.SetStatusText(_('{0} was written').format(file_type))
            return True
        return False

    def create_tune_from_multi_abc(self, abc, header, num_header_lines):
        if self.current_file:
            title = os.path.splitext(os.path.basename(self.current_file))[0]
        else:
            title = _('Untitled')
        return Tune('', title, '', 0, 0, abc, header, num_header_lines)

    def export_tunes(self, file_type, extension, convert_func, only_selected=False, single_file=False):
        if single_file:
            if only_selected:
                selected_tunes = self.GetSelectedTunes(add_file_header=False)
                if selected_tunes:
                    if len(selected_tunes) == 1:
                        tunes = self.GetSelectedTunes(add_file_header=True)
                    else:
                        abc = os.linesep.join(tune.abc for tune in selected_tunes)
                        header, num_header_lines = self.GetFileHeaderBlock()
                        tunes = [self.create_tune_from_multi_abc(abc, header, num_header_lines)]
                else:
                    tunes = []
            else:
                abc, header, num_header_lines = self.editor.GetText(), '', 0
                tunes = [self.create_tune_from_multi_abc(abc, header, num_header_lines)]
        else:
            if only_selected:
                tunes = self.GetSelectedTunes()
            else:
                tunes = [self.GetTune(i) for i in xrange(self.tune_list.GetItemCount())]

        if len(tunes) == 0:
            return

        individual_save_dialog = only_selected or single_file

        if self.current_file:
            path = os.path.dirname(self.current_file)
        else:
            path = ''

        if not individual_save_dialog:
            dlg = wx.DirDialog(self, message=_("Choose a directory..."), style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
            try:
                if dlg.ShowModal() == wx.ID_OK:
                    path = dlg.GetPath()
                else:
                    return
            finally:
                dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window

        global execmessages
        execmessages = u''

        self.statusbar.SetStatusText(_('{0} files to create').format(len(tunes)))
        progdialog = None
        try:
            self.SetCursor(wx.HOURGLASS_CURSOR)

            # 1.3.6 [SS] 2014-12-08
            progdialog = wx.ProgressDialog(_('Exporting'), _('Remaining time'), len(tunes),
                                           style = wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE)
            j = 0
            for tune in tunes:
                j += 1
                running = progdialog.Update(j)
                if not running[0]:
                    break

                try:
                    success = self.export_tune(tune, file_type, extension, convert_func, path, show_save_dialog=individual_save_dialog)
                except Exception as e:
                    error_msg = traceback.format_exc()
                    print(error_msg)
                    success = False

                if not success:
                    break
        finally:
            self.SetCursor(wx.STANDARD_CURSOR)
            if progdialog:
                progdialog.Destroy()
        self.update_statusbar_and_messages()
        if success:
            self.statusbar.SetStatusText(_('Export completed'))
        else:
            self.statusbar.SetStatusText(_('Export failed'))

    def MoveTune(self, from_index, to_index):
        self.tune_list.GetItemData(from_index)
        (_, _, line_no) = self.tune_list.itemDataMap[from_index]
        offset_start = self.editor.PositionFromLine(line_no)
        offset_start, offset_end = self.GetTextRangeOfTune(offset_start)

        (_, _, line_no) = self.tune_list.itemDataMap[to_index]
        insert_pos = self.editor.PositionFromLine(line_no)

        if insert_pos > offset_start:
            _, insert_pos = self.GetTextRangeOfTune(insert_pos)
            insert_pos -= offset_end - offset_start

        self.editor.BeginUndoAction()
        abc = self.editor.GetTextRange(offset_start, offset_end)
        self.editor.SetSelection(offset_start, offset_end)
        self.editor.ReplaceSelection('')
        self.editor.InsertText(insert_pos, abc)
        self.editor.SetSelection(insert_pos, insert_pos)
        self.editor.EndUndoAction()

    def OnMoveTuneUp(self, evt):
        selected_index = self.tune_list.GetFirstSelected()
        if selected_index > 0:
            self.tune_list.DeselectAll()
            self.MoveTune(selected_index, selected_index - 1)

    def OnMoveTuneDown(self, evt):
        selected_index = self.tune_list.GetFirstSelected()
        if selected_index < self.tune_list.ItemCount - 1:
            self.tune_list.DeselectAll()
            self.MoveTune(selected_index, selected_index + 1)

    def OnMusicPaneClick(self, evt):
        if self.score_is_maximized:
            width, height = self.music_pane.Size
            x, y = evt.Position
            x_threshold = width / 3
            y_threshold = height / 3
            new_page = -1
            tune_list = self.tune_list
            total_tunes = tune_list.GetItemCount()

            if x < x_threshold:
                # previous page
                new_page = self.current_page_index - 1
                if new_page < 0:
                    new_page += self.current_svg_tune.page_count
            elif x > (width - x_threshold):
                # next page
                new_page = self.current_page_index + 1
                if new_page >= self.current_svg_tune.page_count:
                    new_page = 0
            elif y < y_threshold:
                # previous tune
                new_tune = tune_list.GetFirstSelected()
                if new_tune < 0:
                    new_tune = 0
                else:
                    new_tune -= 1
                    if new_tune < 0:
                        new_tune = total_tunes - 1
                tune_list.DeselectAll()
                tune_list.Select(new_tune)
            elif y > (height - y_threshold):
                # next tune
                new_tune = tune_list.GetFirstSelected()
                if new_tune < 0:
                    new_tune = 0
                else:
                    new_tune += 1
                    if new_tune >= total_tunes:
                        new_tune = 0
                tune_list.DeselectAll()
                tune_list.Select(new_tune)

            if 0 <= new_page < self.current_svg_tune.page_count and new_page != self.current_page_index:
                self.select_page(new_page)
                return

        evt.Skip()

    def OnRightClickMusicPane(self, evt):
        if self.score_is_maximized:
            self.toggle_fullscreen(evt)

    def OnMusicPaneDoubleClick(self, evt):
        self.editor.SetFocus()

    def toggle_fullscreen(self, evt):
        self.is_fullscreen = not self.is_fullscreen
        self.ShowFullScreen(self.is_fullscreen, style=wx.FULLSCREEN_ALL)

    def OnMusicPaneKeyDown(self, evt):
        c = evt.GetKeyCode()
        if c == wx.WXK_LEFT:
            self.music_pane.move_selection(-1)
        elif c == wx.WXK_RIGHT:
            self.music_pane.move_selection(1)
        elif c == wx.WXK_UP and evt.CmdDown():
            self.transpose_selected_note(1)
        elif c == wx.WXK_DOWN and evt.CmdDown():
            self.transpose_selected_note(-1)
        else:
            evt.Skip()

    def OnRightClickList(self, evt):
        self.selected_tune = self.tunes[evt.Index]
        self.tune_list.PopupMenu(self.popup_upload, evt.GetPoint())

    def OnInsertSymbol(self, evt):
        item = self.GetMenuBar().FindItemById(evt.Id)
        self.editor.SetSelectionEnd(self.editor.GetSelectionStart())
        self.AddTextWithUndo(item.GetHelp())
        self.refresh_tunes()

    # 1.3.6.3 [JWDJ] 2015-3 centralized enabling of play button
    def update_play_button(self):
        if self.mc is not None or self.settings['midiplayer_path']:
            self.play_button.Enable()
        else:
            self.play_button.Disable()

    def OnToolPlay(self, evt):
        if self.mc.is_playing:
            self.mc.Pause()
            self.play_button.SetBitmap(self.play_bitmap)
        elif self.mc.is_paused:
            self.mc.Play()
            self.play_button.SetBitmap(self.pause_bitmap)
        else:
            remove_repeats = evt.ControlDown() or evt.CmdDown()
            # 1.3.6.3 [SS] 2015-05-04
            if not self.settings['midiplayer_path']:
                self.flip_tempobox(True)
            self.bpm_slider.Enabled = self.mc.supports_tempo_change_while_playing
            #self.play_panel.Show(not self.settings['midiplayer_path']) # 1.3.6.2 [JWdJ] 2015-02
            # self.toolbar.Realize() # 1.3.6.3 [JWDJ] fixes toolbar repaint bug

            self.current_time_slice = None
            self.future_time_slice = None
            self.last_played_svg_row = None
            wx.CallAfter(self.PlayMidi, remove_repeats)
        self.editor.SetFocus()

    @property
    def loop_midi_playback(self):
        return self.mc.loop_midi_playback

    def set_loop_midi_playback(self, value):
        self.loop_check.SetValue(value)
        self.mc.set_loop_midi_playback(value)

    def OnToolPlayLoop(self, evt):
        if self.settings['midiplayer_path']:
            wx.MessageBox(_('Looping is not possible when using an external midi player. Empty the midiplayer path in Settings -> ABC Settings -> File Settings to regain the looping ability when you double click the play button'), _('Looping unavailable'), wx.OK | wx.ICON_INFORMATION)
        else:
            self.set_loop_midi_playback(True)
        if not self.mc.is_playing:
            self.OnToolPlay(evt)
        self.editor.SetFocus()

    def OnToolRefresh(self, evt):
        self.refresh_tunes()

    def refresh_tunes(self):
        self.last_refresh_time = datetime.now()
        self.UpdateTuneListAndReselectTune()
        self.OnTuneSelected(None)

    def OnToolAbcAssist(self, evt):
        # 1.3.7 [JWdJ] 2016-01-06
        pane = self.manager.GetPane(self.abc_assist_panel)
        shown = self.abc_assist_panel.IsShown() and pane.IsOk()
        if shown:
            if pane.IsFloating():
                pane.Dock()
            else:
                pane.Float()

            self.manager.Update()
            pane.Floatable(False) # JWDJ: moving a docked abc-assist must not let it float
            pane.Dockable(not pane.IsFloating()) # JWDJ: moving a floating abc-assist must not try to dock it again
        else:
            self.ShowAbcAssist(not shown)
        self.editor.SetFocus()

    # 1.3.7 [JWdJ] 2016-01-06
    def ShowAbcAssist(self, show):
        pane = self.manager.GetPane(self.abc_assist_panel)
        if show:
            if not pane.IsOk():
                self.manager.AddPane(self.abc_assist_panel, self.assist_pane)
                self.manager.Update()
                pane = self.manager.GetPane(self.abc_assist_panel)

            if pane.IsOk():
                self.manager.RestorePane(pane)
                self.manager.Update()

            if not self.abc_assist_panel.IsShown():
                self.abc_assist_panel.Show()
            self.manager.Update()

            self.abc_assist_panel.update_assist()
            if pane.IsFloating():
                # 1.3.6.2 [JWDJ] move abc assist alongside abc editor
                w, h = self.abc_assist_panel.GetClientSize()
                w += 2 # include border pixels
                editor_x, editor_y = self.editor.ClientToScreen((0, 0))
                new_size = self.tune_list.GetSize()[0], self.editor.GetSize()[1]
                pane.FloatingSize(new_size)
                pane.FloatingPosition((editor_x, editor_y))
                pane.Show()
                self.manager.Update()
                assist_x, assist_y = self.abc_assist_panel.ClientToScreen((0, 0))
                offset = editor_x - assist_x, editor_y - assist_y
                pane.FloatingPosition((editor_x + offset[0] - w, editor_y + offset[1]))
                self.manager.Update()
            # 1.3.7 [JWdJ] 2016-01-06
            pane.Dockable(not pane.IsFloating()) # JWDJ: moving a floating abc-assist must not try to dock it again
        else:
            if self.abc_assist_panel.IsShown():
                self.abc_assist_panel.Hide()
            if pane.IsOk():
                self.manager.DetachPane(self.abc_assist_panel)

        self.manager.Update()
        self.UpdateAbcAssistSetting()

    def UpdateAbcAssistSetting(self):
        pane = self.manager.GetPane(self.abc_assist_panel)
        show_abc_assist = pane.IsOk() and pane.IsShown() and self.abc_assist_panel.IsShown()
        self.settings['show_abc_assist'] = show_abc_assist

    def __onPaneClose(self, evt):
        if evt.pane.window == self.abc_assist_panel:
            self.settings['show_abc_assist'] = False
        if evt.pane.window == self.search_files_panel:
            self.search_files_panel.focus_find_what()
            self.search_files_panel.clear_results()

    def __onPaneMaximize(self, evt):
        if evt.pane.window == self.music_pane:
            self.score_is_maximized = True

    def __onPaneRestore(self, evt):
        if evt.pane.window == self.music_pane:
            self.score_is_maximized = False

    def OnToolDynamics(self, evt):
       try: self.toolbar.PopupMenu(self.popup_dynamics)
       except wx._core.PyAssertionError: pass

    def OnToolOrnamentation(self, evt):
       try: self.toolbar.PopupMenu(self.popup_ornaments)
       except wx._core.PyAssertionError: pass

    def OnToolDirections(self, evt):
       try: self.toolbar.PopupMenu(self.popup_directions)
       except wx._core.PyAssertionError: pass

    def CanClose(self, dont_ask = False):
        if self.editor.GetModify():
            if dont_ask:
                result = wx.ID_YES
            else:
                result = self.ask_save()
            if result == wx.ID_YES:
                if self.current_file:
                    try:
                        self.save()
                    except IOError:
                        wx.MessageBox(_("Error: there was some trouble saving the file."), _("File could not be saved properly"), wx.OK)
                        return False
                else:
                    result = self.save_as()
            if result == wx.ID_CANCEL:
                return False

        if self.record_thread != None:
            self.record_thread.abort()
            self.record_thread = None	#[EPO] 2018-11-20 prevent segmentation error (undefined variable)
        return True

    def OnNew(self, evt=None):
        self.save_settings()
        frame = wx.GetApp().NewMainFrame()
        frame.Show(True)
        # move new window slightly down to the right:
        width, height = tuple(wx.DisplaySize())
        x, y = self.GetPosition()
        x, y = (x + 40) % (width - 200), (y + 40) % (height - 200)
        frame.Move((x, y))
        return frame

    def OnOpen(self, evt):
        wildcard = _("ABC file") + " (*.abc;*.txt;*.mcm)|*.abc;*.txt;*.mcm|" + \
                   _('Any file') + " (*.*)|*"
        dlg = wx.FileDialog(
            self, message=_("Open ABC file"),
            defaultFile="", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_CHANGE_DIR )
        try:
            if dlg.ShowModal() == wx.ID_OK:
                if not self.editor.GetModify() and not self.current_file:     # if a new unmodified document
                    self.load(dlg.GetPath())
                else:
                    frame = self.OnNew()
                    frame.load(dlg.GetPath())
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window

    def OnImport(self, evt):
        wildcard = _('Any music file') + " (*.abc;*.txt,*.mcm;*.mid;*.midi;*.xml;*.mxl;*.nwc)|*.abc;*.txt;*.mcm;*.mid;*.midi;*.xml;*.mxl;*.nwc|" + \
                   _('ABC file') + " (*.abc;*.txt;*.mcm)|*.abc;*.txt;*.mcm|" + \
                   _('Midi file') + " (*.mid;*.midi)|*.mid;*.midi|" + \
                   _('MusicXML') + " (*.xml;*.mxl)|*.xml;*.mxl|" + \
                   _('Noteworthy Composer file') + " (*.nwc)|*.nwc|" + \
                   _('Any file') + " (*.*)|*"
        dlg = wx.FileDialog(
            self, message=_('Import and add tune'), #defaultDir='',
            defaultFile="", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_CHANGE_DIR )
        try:
            if dlg.ShowModal() == wx.ID_OK:
                self.OnDropFile(dlg.GetPath())
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window
        # self.UpdateTuneList() # 1.3.7.4 [JWDJ] No need to explicitly update tunelist, because adding lines triggers UpdateTuneList

    def load_or_import(self, filepath):
        if not self.editor.GetModify() and not self.editor.GetText().strip() and os.path.splitext(filepath)[1].lower() in ('.txt', '.abc', '.mcm', ''):
            self.load(filepath)
        else:
            self.OnDropFile(filepath)

    def abc_bytes_to_text(self, file_as_bytes):
        encoding = get_encoding_abc(file_as_bytes)
        if encoding and encoding != 'utf-8':
            try:
                return file_as_bytes.decode(encoding)
            except UnicodeError:
                try:
                    text = file_as_bytes.decode('utf-8')
                    modal_result = wx.MessageBox(_("This ABC file seems to be encoded using UTF-8 but contains no indication of this fact. "
                                                   "It is strongly recommended that an I:abc-charset field is added in order for you to load the file and safely save changes to it. "
                                                   "Do you want EasyABC to add this for you automatically?"), _("Add abc-charset field?"), wx.ICON_QUESTION | wx.YES | wx.NO)
                    if modal_result == wx.YES:
                        text = os.linesep.join(('I:abc-charset utf-8', text))
                    return text
                except UnicodeError:
                    pass
        try:
            return file_as_bytes.decode('utf-8')
        except UnicodeError:
            return file_as_bytes.decode('latin-1')

    @staticmethod
    def fix_end_of_line_sequence(text):
        if wx.Platform == "__WXMAC__":
            return text.replace('\r\n', '\n')
        else:
            # text = re.sub('\r+', '\r', text)
            if not '\n' in text:
                text = text.replace('\r', '\r\n')
            return text

    def load(self, filepath, editor_pos = None):
        try:
            file_as_bytes = read_entire_file(filepath)
        except IOError:
            wx.MessageBox(_("Could not find file.\nIt may have been moved or deleted. Choose File,Open to locate it."), _("File not found"), wx.OK)
            return

        text = self.abc_bytes_to_text(file_as_bytes)
        text = self.fix_end_of_line_sequence(text)

        self.current_file = filepath
        self.document_name = filepath
        self.SetTitle('%s - %s' % (program_name, self.document_name))
        self.updating_text = True
        try:
            self.editor.ClearAll()
            self.editor.SetText(text)
            if editor_pos:
                self.editor.SetCurrentPos(editor_pos)
            self.editor.SetSavePoint()
            self.editor.EmptyUndoBuffer()
        finally:
            self.updating_text = False

        self.UpdateTuneList()
        if editor_pos:
            self.select_tune_at_current_pos()
        else:
            self.tune_list.Select(0)

    def load_and_position(self, filepath, editor_pos):
        # import cProfile
        # profiler = cProfile.Profile()
        # profiler.enable()

        # self.Freeze()
        # try:
        if self.current_file == filepath:
            self.editor.SetCurrentPos(editor_pos)
            self.select_tune_at_current_pos()
        else:
            self.load(filepath, editor_pos)
        # finally:
        #     self.Thaw()

        # import pstats
        # p = pstats.Stats(profiler)
        # p.strip_dirs().sort_stats('cumulative').reverse_order().print_stats()

    def ask_save(self):
        dlg = wx.MessageDialog(self, _('Do you want to save your changes to %s?') % self.document_name,
                               _('Save changes?'), wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
        modal_result = dlg.ShowModal()
        dlg.Destroy()
        return modal_result

    def save(self):
        if self.current_file is None:
            self.save_as()
        else:
            f = open(self.current_file, 'wb')
            s = self.editor.GetText()
            if PY3 or type(s) is unicode:
                if PY3:
                    encoding = 'utf-8'
                else:
                    encoding = get_encoding_abc(s)
                try:
                    s.encode(encoding, 'strict')
                except UnicodeEncodeError as e: # 1.3.6.2 [JWdJ] 2015-02
                    sample_letters = s[e.start:e.end][:30]
                    modal_result = wx.MessageBox(_("This document contains characters (eg. %(ABC)s) that cannot be represented using the current character encoding (%(encoding)s). "
                                                   "Do you want to switch to using UTF-8 as your character encoding (recommended)? "
                                                   "(choosing No may cause some of these characters to be replaced by '?' when they are saved)") %
                                                   {'ABC': sample_letters, 'encoding': encoding},
                                                 _('Switch to UTF-8 encoding?'), wx.ICON_QUESTION | wx.YES | wx.NO)
                    if modal_result == wx.YES:
                        s = os.linesep.join(('I:abc-charset utf-8', s))
                        self.editor.BeginUndoAction()
                        self.editor.SetText(s)
                        self.editor.EndUndoAction()
                        encoding = 'utf-8'

                s = s.encode(encoding, 'replace')

            f.write(s)
            f.close()
            self.add_recent_file(self.current_file)
            self.editor.SetSavePoint()

    def save_as(self, directory=None):
        wildcard = _('ABC file') + " (*.abc)|*.abc"
        defaultDir = ''
        if self.current_file:
            defaultDir = os.path.dirname(self.current_file) or directory or cwd
        dlg = wx.FileDialog(
                self, message=_('Save ABC file %s') % self.document_name, defaultDir=defaultDir,
                defaultFile="", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR
                )
        try:
            result = dlg.ShowModal()
            if result == wx.ID_OK:
                if os.path.exists(dlg.GetPath()):
                    if wx.MessageDialog(self,
                                        _('The file already exists. Do you want to overwrite the existing file?'),
                                        _('Overwrite existing file?'), wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_QUESTION).ShowModal() != wx.ID_YES:
                        return wx.ID_CANCEL
                self.current_file = dlg.GetPath()
                self.document_name = os.path.basename(self.current_file)
                self.SetTitle('%s - %s' % (program_name, self.document_name))
                self.save()
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window
        return result

    def AbcToAbcCurrentTune(self, params):
        abc2abc_path = self.settings['abc2abc_path'] # 1.3.6 [SS] 2014-11-12
        tune = self.GetSelectedTune()
        if tune:
            trailing_space = tune.abc[-(len(tune.abc) - len(tune.abc.rstrip())):]
            (abc, error_msg) = AbcToAbc(tune.abc, self.cache_dir, params, abc2abc_path)
            if abc is not None:
                self.editor.BeginUndoAction()
                self.editor.SetSelection(tune.offset_start, tune.offset_end)
                self.editor.ReplaceSelection(abc.rstrip() + trailing_space)
                self.editor.SetSelection(tune.offset_start, self.editor.GetCurrentPos()-len(trailing_space))
                self.editor.EndUndoAction()
            if error_msg:
                wx.MessageDialog(self,
                                 _('abc2abc error/warnings: ') + os.linesep + error_msg,
                                 _('Abc2abc error message'), wx.OK | wx.CANCEL | wx.ICON_WARNING).ShowModal()

    def OnHalveL(self, evt):
        self.AbcToAbcCurrentTune(['-v'])
    def OnDoubleL(self, evt):
        self.AbcToAbcCurrentTune(['-d'])
    def OnTranspose(self, num_semitones):
        self.AbcToAbcCurrentTune(['-t', str(num_semitones)])
    def OnAlignBars(self, evt):
        tune = self.GetSelectedTune()
        if not tune:
            return
        first_line = self.editor.LineFromPosition(self.editor.GetSelectionStart())
        last_line = self.editor.LineFromPosition(self.editor.GetSelectionEnd())
        # if not multiple lines are select, then apply the alignment to the whole tune
        if first_line == last_line:
            first_line = self.editor.LineFromPosition(tune.offset_start)
            last_line = self.editor.LineFromPosition(tune.offset_end)

        # find the lines and line numbers that should be affected by the alignment (eg. field lines like K: should be excluded)
        line_numbers = []
        lines = []
        for i in range(first_line, last_line+1):
            line = self.editor.GetLine(i)
            if not re.match(r'[a-zA-Z]:', line) and not line.startswith('%') and line.strip():
                line_numbers.append(i)
                lines.append(line)

        # if there are more than two lines to align
        if len(lines) >= 2:
            # align the lines
            lines = align_lines(tune.abc, lines, True)

            # copy them back into the ABC editor
            self.editor.BeginUndoAction()
            for (i, line) in zip(line_numbers, lines):
                p1, p2 = self.editor.PositionFromLine(i), self.editor.GetLineEndPosition(i)
                self.editor.SetSelection(p1, p2)
                self.editor.ReplaceSelection(line.rstrip())
            self.editor.EndUndoAction()

            # select the whole tune
            self.editor.SetSelection(self.editor.PositionFromLine(line_numbers[0]),
                                     self.editor.GetLineEndPosition(line_numbers[-1]))

    @staticmethod
    def get_image_path():
        return os.path.join(application_path, 'img')

    def create_symbols_popup_menu(self, symbols):
        menu = create_menu([], parent=self)
        image_path = self.get_image_path()
        for symbol in symbols:
            if symbol == '-':
                menu.AppendSeparator()
            else:
                img_file = os.path.join(image_path, symbol + '.png')
                description = ('!%s!' % symbol).replace('!pralltriller!', 'P').replace('!accent!', '!>!').replace('!staccato!', '.').replace('!u!', 'u').replace('!v!', 'v').replace('!repeat_left!', '|:').replace('!repeat_right!', ':|').replace('!repeat_both!', '::').replace('!barline!', ' | ').replace('!repeat1!', '|1 ').replace('!repeat2!', ':|2 ')
                image = wx.Image(img_file)
                append_menu_item(menu, ' ', description, self.OnInsertSymbol, bitmap=image.ConvertToBitmap())
        return menu

    def create_upload_context_menu(self):
        menu = create_menu([
            (_('Move up'), '', self.OnMoveTuneUp),
            (_('Move down'), '', self.OnMoveTuneDown),
            (),
            (_('Copy'), '', self.OnExportToClipboard),
            (_('Export to &MIDI...'), '', self.OnExportMidi),
            (_('Export to &PDF...'), '', self.OnExportPDF),
            (_('Export to &one PDF...'), '', self.OnExportSelectedToSinglePDF, self.add_to_multi_list),
            (_('Export to &SVG...'), '', self.OnExportSVG),
            (_('Export to &HTML...'), '', self.OnExportHTML),
            (_('Export to HTML (&interactive)...'), '', self.OnExportInteractiveHTML),
            (_('Export to Music&XML...'), '', self.OnExportMusicXML),
            (_('Export to &ABC...'), '', self.OnExportToABC),
            (_('Export to &Wave...'), '', self.OnExportToWave),
            (_('Export to &MP3...'), '', self.OnExportToMP3),
            (_('Export to &AAC...'), '', self.OnExportToAAC)
        ], parent=self)

        # global current_locale
        # if current_locale.GetLanguageName(wx.LANGUAGE_DEFAULT) == 'Swedish':
        #     id = wx.NewId()
        #     item = wx.MenuItem(menu, id, _('Upload tune to FolkWiki'))
        #     menu.AppendItem(item)
        #     menu.AppendSeparator()
        #     self.Bind(wx.EVT_MENU, self.OnUploadTune, id=id)

        # if current_locale.GetLanguageName(wx.LANGUAGE_DEFAULT) == 'Danish':
        #     id = wx.NewId()
        #     item = wx.MenuItem(menu, id, _('Upload tune to Spillemandsportalen'))
        #     menu.AppendItem(item)
        #     menu.AppendSeparator()
        #     self.Bind(wx.EVT_MENU, self.OnUploadTune, id=id)
        #     item.Enable(False)  # disabled for now

        return menu

    def add_to_multi_list(self, menu_item):
        self.multi_tunes_menu_items += [menu_item]

    def setup_typing_assistance_menu(self):
        menu = self.mnu_TA = create_menu([], parent=self)
        self.mni_TA_active = append_menu_item(menu, _("&Active") + '\tCtrl+T', "", self.GrayUngray, kind=wx.ITEM_CHECK)
        menu.AppendSeparator()
        self.mni_TA_auto_case = append_menu_item(menu, _("Automatic uppercase/lowercase"), "", None, kind=wx.ITEM_CHECK)
        self.mni_TA_do_re_mi = append_menu_item(menu, _("&Do-re-mi mode"), "", self.OnDoReMiModeChange, kind=wx.ITEM_CHECK)
        self.mni_TA_add_note_durations = append_menu_item(menu, _("Add note &durations"), "", None, kind=wx.ITEM_CHECK)

        add_bar_menu = create_menu([], parent=self)
        self.mni_TA_add_bar_disabled = append_menu_item(add_bar_menu, _('Disabled'), "", None, kind=wx.ITEM_RADIO)
        self.mni_TA_add_bar = append_menu_item(add_bar_menu, _('Using spacebar'), "", None, kind=wx.ITEM_RADIO)
        self.mni_TA_add_bar_auto = append_menu_item(add_bar_menu, _('Automatic'), "", None, kind=wx.ITEM_RADIO)
        append_submenu(menu, _('Add &bar'), add_bar_menu)

        self.mni_TA_add_right = append_menu_item(menu, _('Add &matching right symbol: ), ], } and "'), "", None, kind=wx.ITEM_CHECK)
        return menu

    def setup_menus(self):
        # 1.3.7.1 [JWDJ] creation of menu bar now more structured using less code
        ornaments = 'v u - accent staccato tenuto - open plus snap - trill pralltriller mordent roll fermata - 0 1 2 3 4 5 - turn turnx invertedturn invertedturnx - shortphrase breath'.split()
        dynamics = 'p pp ppp - f ff fff - mp mf sfz'.split()
        directions = 'coda segno D.C. D.S. fine barline repeat_left repeat_right repeat_both repeat1 repeat2'.split()

        self.multi_tunes_menu_items = []
        self.popup_ornaments = self.create_symbols_popup_menu(ornaments)
        self.popup_dynamics = self.create_symbols_popup_menu(dynamics)
        self.popup_directions = self.create_symbols_popup_menu(directions)

        transpose_menu = create_menu([], parent=self)
        for i in reversed(range(-12, 12+1)):
            if i < 0:
                append_menu_item(transpose_menu, _('Down %d semitones') % abs(i), '', lambda e, i=i: self.OnTranspose(i))
            elif i == 0:
                transpose_menu.AppendSeparator()
            elif i > 0:
                append_menu_item(transpose_menu, _('Up %d semitones') % i, '', lambda e, i=i: self.OnTranspose(i))

        view_menu = create_menu([], parent=self)
        append_menu_item(view_menu, _("&Refresh music")+"\tF5", "", self.OnToolRefresh)
        self.mni_auto_refresh = append_menu_item(view_menu, _("&Automatically refresh music as I type"), "", None, kind=wx.ITEM_CHECK)
        view_menu.AppendSeparator()
        self.mni_reduced_margins = append_menu_item(view_menu, _("&Use reduced margins when displaying tunes on screen"), "", self.OnReducedMargins, kind=wx.ITEM_CHECK)
        append_menu_item(view_menu, _("&Change editor font..."), "", self.OnChangeFont)
        append_menu_item(view_menu, _("&Use default editor font"), "", self.OnUseDefaultFont)
        view_menu.AppendSeparator()
        append_menu_item(view_menu, _("&Reset window layout to default"), "", self.OnResetView)
        view_menu.AppendSeparator()
        append_menu_item(view_menu, _("&Full screen") + '\tShift+Alt+F', "", self.toggle_fullscreen)

        #self.append_menu_item(view_menu, _("&Maximize/restore musical score pane") + "\tCtrl+M", "", self.OnToggleMusicPaneMaximize)

        self.recent_menu = create_menu([], parent=self)

        menuBar = create_menu_bar([
            (_("&File")     , [
                (_('&New') + '\tCtrl+N', _("Create a new file"), self.OnNew, self.disable_in_exclusive_mode),
                (_('&Open...') + '\tCtrl+O', _("Open an existing file"), self.OnOpen, self.disable_in_exclusive_mode),
                (_("&Close") + '\tCtrl+W', _("Close the current file"), self.OnCloseFile, self.disable_in_exclusive_mode),
                (),
                (_("&Import and add..."), _("Import a song in ABC, Midi or MusicXML format and add it to the current document."), self.OnImport, self.disable_in_exclusive_mode),
                (),
                (_("&Export selected"), [
                    (_('as &PDF...'), '', self.OnExportPDF),
                    (_('as one &PDF...'), '', self.OnExportSelectedToSinglePDF, self.add_to_multi_list),
                    (_('as &MIDI...'), '', self.OnExportMidi),
                    (_('as &SVG...'), '', self.OnExportSVG),
                    (_('as &HTML...'), '', self.OnExportHTML),
                    (_('as HTML (&interactive)...'), '', self.OnExportInteractiveHTML),
                    (_('as Music&XML...'), '', self.OnExportMusicXML),
                    (_('as A&BC...'), '', self.OnExportToABC),
                    (_('as &Wave...'), '', self.OnExportToWave),
                    (_('as &MP3...'), '', self.OnExportToMP3),
                    (_('as &AAC...'), '', self.OnExportToAAC)]),
                (_("Export &all"), [
                    (_('as a &PDF Book...'), '', self.OnExportAllPDF),
                    (_('as PDF &Files...'), '', self.OnExportAllPDFFiles),
                    (_('as &MIDI...'), '', self.OnExportAllMidi),
                    (_('as &HTML...'), '', self.OnExportAllHTML),
                    (_('as HTML (&interactive)...'), '', self.OnExportAllInteractiveHTML),
                    #(_('as &EPUB...'), '', self.OnExportAllEpub),
                    (_('as Music&XML...'), '', self.OnExportAllMusicXML)]),
                (),
                (_("&Save") + "\tCtrl+S", _("Save the active file"), self.OnSave),
                (_("Save &As...") + "\tShift+Ctrl+S", _("Save the active file with a new filename"), self.OnSaveAs),
                (),
                (_("&Print...") + "\tCtrl+P", _("Print the selected tune"), self.OnPrint),
                (_("&Print preview") + "\tCtrl+Shift+P", '', self.OnPrintPreview),
                (_("P&age Setup..."), _("Change the printer and printing options"), self.OnPageSetup),
                (),
                (_('&Recent files'), self.recent_menu, self.disable_in_exclusive_mode),
                (),
                (wx.ID_EXIT, _("&Quit") + "\tCtrl+Q", _("Exit the application (prompt to save files)"), self.OnQuit)]),
            (_("&Edit")     , [
                (_("&Undo") + "\tCtrl+Z", _("Undo the last action"), self.OnUndo),
                (_("&Redo") + "\tCtrl+Y", _("Redo the last action"), self.OnRedo),
                (),
                (_("&Cut") + "\tCtrl+X", _("Cut the selection and put it on the clipboard"), self.OnCut),
                (_("&Copy") + "\tCtrl+C", _("Copy the selection and put it on the clipboard"), self.OnCopy),
                (_("&Paste") + "\tCtrl+V", _("Paste clipboard contents"), self.OnPaste),
                (_("&Delete"), _("Delete the selection"), self.OnDelete),
                (),
                (_("&Insert musical symbol"), [
                    (_('Note ornaments'), self.popup_ornaments),
                    (_('Directions'), self.popup_directions), # 1.3.6.1 [SS] 2015-01-22
                    (_('Dynamics'), self.popup_dynamics)]),
                (),
                (_("&Transpose"), transpose_menu),
                (_("&Change note length"), [
                    (_('Double note lengths') + '\tCtrl+Shift++', '', self.OnDoubleL),
                    (_('Halve note lengths') + '\tCtrl+Shift+-', '', self.OnHalveL)]),
                (_("A&lign bars") + "\tCtrl+Shift+A", '', self.OnAlignBars),
                (),
                (_("&Find...") + "\tCtrl+F", '', self.OnFind),
                (_("Find in Files") + '\tCtrl+Shift+F', '', self.OnSearchDirectories, self.disable_in_exclusive_mode), # 1.3.6 [SS] 2014-11-21
                (_("Find &Next") + "\t"+("F3" if wx.Platform != '__WXMAC__' else "Ctrl+G"), '', self.OnFindNext),
                (_("&Replace...") + "\t"+("Ctrl+H" if wx.Platform != "__WXMAC__" else "Alt+Ctrl+F"), '', self.OnReplace),
                (),
                (_("&Select all") + "\tCtrl+A", '', self.OnSelectAll)]),
            (_("&Settings") , [
                (_("&ABC settings") + '...', "", self.OnAbcSettings),
                (_("&Midi device settings") + "...", "", self.OnMidiSettings),
                (_("ABC &typing assistance"), self.setup_typing_assistance_menu()),
                (),
                (_('&Clear cache') + '...', '', self.OnClearCache), #1.3.6.1 [SS] 2015-1-10 do not use 5003 (on Linux it will add Ctr-S shortcut)
                (_('Cold &restart'), '', self.OnColdRestart)]), # 1.3.6.1 [SS] 2014-12-28
            (_("&Tools")    , [
                (_('Generate &incipits file...'), '', self.OnGenerateIncipits),
                (_('&View incipits...'), '', self.OnViewIncipits),
                (),
                (_('&Renumber X: fields...'), '', self.OnRenumberTunes),
                (_('&Sort tunes...'), '', self.OnSortTunes)]),
            (_("&View")     , view_menu),
            (_("&Internals"), [ #p09 [SS] 2014-10-22
                (_("Messages"), _("Show warnings and errors"), self.OnShowMessages),
                (_("Input processed tune"), '', self.OnShowAbcTune),
                (_("List of Tunes"), '', self.OnShowTunesList),
                (_("Output midi file"), '', self.OnShowMidiFile),
                (_("Show settings status"), '', self.OnShowSettings)]),
            (_("&Help")     , [
                (_("&Show fields and commands reference"), '', self.OnViewFieldReference),
                (),
                (_("&EasyABC Help"), _("Link to EasyABC Website"), self.OnEasyABCHelp),
                (_("&ABC Standard Version 2.1"), _("Link to the ABC Standard version 2.1"), self.OnABCStandard),
                (_("&Learn ABC"), _("Link to the ABC notation website"), self.OnABCLearn),
                (_("&Abcm2ps help"), _("Link to the Abcm2ps website"), self.OnAbcm2psHelp),
                (_("&Abc2midi help"), _("Link to the Abc2midi website"), self.OnAbc2midiHelp),
                (_("ABC &Quick Reference Card"), _("Link to a PDF with the most common ABC commands"), self.OnAbcCheatSheet),
                (),
                (_("&Check for update..."), _("Link to EasyABC download page"), self.OnCheckLastestVersion),
                (),
                (wx.ID_ABOUT, _("About EasyABC") + "...", '', self.OnAbout)
            ]),
        ], parent=self)

        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_FIND, self.OnFindNext)
        self.Bind(wx.EVT_FIND_NEXT, self.OnFindNext)
        self.Bind(wx.EVT_FIND_REPLACE, self.OnFindReplace)
        self.Bind(wx.EVT_FIND_REPLACE_ALL, self.OnFindReplaceAll)
        self.Bind(wx.EVT_FIND_CLOSE, self.OnFindClose)

    def disable_in_exclusive_mode(self, menu_item):
        if self.exclusive_file_mode:
            menu_item.Enable(False)

    def ShowMessages(self):
        global execmessages
        win = wx.FindWindowByName('infoframe')
        if win is None:
            self.msg = MyInfoFrame()
            self.msg.ShowText(execmessages)
            self.msg.Show()
        else:
            win.ShowText(execmessages)
            # 1.3.6.1 [JWdJ] 2015-01-30 When messages window is lost it will be focused again
            win.Iconize(False)
            win.Raise()

    def OnShowMessages(self, evt):
        self.ShowMessages()

    def OnShowAbcTune(self, evt):
        win = wx.FindWindowByName('abctuneframe')
        if win is None:
            # 1.3.6.3 [JWDJ] 2015-04-27 instance of MyInfoFrame was overwritten by mistake
            self.tune_frame = MyAbcFrame()
            self.tune_frame.ShowText(visible_abc_code)
            self.tune_frame.Show()
        else:
            win.ShowText(visible_abc_code)
            # 1.3.6.1 [SS] 2015-02-01
            win.Iconize(False)
            win.Raise()

    def OnShowTunesList(self, evt):
        win = wx.FindWindowByName('tuneslistframe')
        tunes_list = 'index|title|startline\n'
        for i, (index, title, startline) in enumerate(self.tunes):
            tunes_list = tunes_list + str(index) + '|' + str(title) + '|' + str(startline) +'\n'
        if win is None:
            self.tuneslist_frame = MyTunesListFrame()
            self.tuneslist_frame.ShowText(tunes_list)
            self.tuneslist_frame.Show()
        else:
            win.ShowText(tunes_list)
            win.Iconize(False)
            win.Raise()

    # 1.3.6 [SS] 2014-12-10
    def OnShowSettings(self, evt):
        global execmessages
        execmessages = u''
        for key in sorted(self.settings):
            line = key +' => '+ str(self.settings[key]) + '\n'
            execmessages += line
        # 1.3.6.1 [JWdJ] 2015-01-30 When messages window is lost it will be focused again
        self.ShowMessages()

    #1.3.6.4 [SS] 2015-06-22
    def OnShowMidiFile(self, evt):
        midi2abc_path = self.settings['midi2abc_path']
        if hasattr(self.current_midi_tune, 'midi_file'):
            MidiToMftext(midi2abc_path, self.current_midi_tune.midi_file)
        else:
            wx.MessageBox(_("You need to create the midi file by playing the tune"), _("Error") , wx.ICON_ERROR | wx.OK)

    def OnCloseFile(self, evt):
        if self.CanClose():
            self.current_file = None
            self.untitled_number += 1
            self.new_tune()
            self.OnTuneSelected(None)

    def OnSave(self, evt):
        self.save()

    def OnSaveAs(self, evt):
        self.save_as()

    def OnQuit(self, evt):
        for frame in wx.GetApp().GetAllFrames():
            if not frame.Close():
                break

    def do_command(self, cmd):
        self.editor.CmdKeyExecute(cmd)

    def OnUndo(self, evt):      #self.do_command(stc.STC_CMD_UNDO)
        if self.tune_list.HasFocus():
            return
        widget = self.FindFocus()
        widget.Undo()
    def OnRedo(self, evt):      #self.do_command(stc.STC_CMD_REDO)
        if self.tune_list.HasFocus():
            return
        widget = self.FindFocus()
        widget.Redo()
    def OnCut(self, evt):       #self.do_command(stc.STC_CMD_CUT)
        if self.tune_list.HasFocus():
            return
        widget = self.FindFocus()
        widget.Cut()
    def OnCopy(self, evt):      #self.do_command(stc.STC_CMD_COPY)
        if self.tune_list.HasFocus():
            self.OnExportToClipboard(evt)
        else:
            widget = self.FindFocus()
            widget.Copy()
    def OnPaste(self, evt):    #self.do_command(stc.STC_CMD_PASTE)
        if self.tune_list.HasFocus():
            return
        widget = self.FindFocus()
        widget.Paste()
    def OnDelete(self, evt):    #self.do_command(stc.STC_CMD_CLEAR)
        if self.tune_list.HasFocus():
            return
        widget = self.FindFocus()
        widget.Clear()
    def OnSelectAll(self, evt): #self.do_command(stc.STC_CMD_SELECTALL)
        if self.tune_list.HasFocus():
            for i in range(self.tune_list.GetItemCount()):
                self.tune_list.Select(i,1)
        else:
            widget = self.FindFocus()
            widget.SelectAll()

    def OnFind(self, evt):
        self.close_existing_find_and_replace_dialogs()
        self.find_dialog = wx.FindReplaceDialog(self, self.find_data, _("Find"))
        wx.CallLater(1, self.find_dialog.Show, True)

    def OnReplace(self, evt):
        self.close_existing_find_and_replace_dialogs()
        self.replace_dialog = wx.FindReplaceDialog(self, self.find_data, _("Find & Replace"), wx.FR_REPLACEDIALOG)
        wx.CallLater(1, self.replace_dialog.Show, True)

    def close_existing_find_and_replace_dialogs(self):
        if self.find_dialog:
            self.find_dialog.Close()
            self.find_dialog.Destroy()
            self.find_dialog = None
        if self.replace_dialog:
            self.replace_dialog.Close()
            self.replace_dialog.Destroy()
            self.replace_dialog = None

    def OnFindClose(self, evt):
        evt.GetDialog().Destroy()

    def get_scintilla_find_flags(self):
        self.findFlags = self.find_data.GetFlags()
        flags = 0
        if wx.FR_WHOLEWORD & self.findFlags:
            flags |= stc.STC_FIND_WHOLEWORD
        if wx.FR_MATCHCASE & self.findFlags:
            flags |= stc.STC_FIND_MATCHCASE
        return flags

    def OnFindReplace(self, evt):
        self.editor.BeginUndoAction()
        self.editor.ReplaceSelection(self.find_data.GetReplaceString())
        self.editor.EndUndoAction()
        wx.CallAfter(self.OnFindNext, evt)

    def OnFindReplaceAll(self, evt):
        try:
            self.editor.BeginUndoAction()
            text = self.editor.GetText()
            pattern = re.escape(self.find_data.GetFindString())
            if self.find_data.GetFlags() & wx.FR_WHOLEWORD:
                pattern = r'\b' + pattern + r'\b'
            if not (self.find_data.GetFlags() & wx.FR_MATCHCASE):
                pattern = '(?i)' + pattern
            text, count = re.subn(pattern, self.find_data.GetReplaceString(), text)
            self.editor.SetText(text.replace(self.find_data.GetFindString(), self.find_data.GetReplaceString()))
            self.editor.SetSelection(0, 0)
            self.editor.GotoPos(0)
        finally:
            self.editor.EndUndoAction()
        if count:
            msg = _('%d occurrences successfully replaced.') % count
        else:
            msg = _('Cannot find "%s"') % self.find_data.GetFindString()
        dlg = wx.MessageDialog(self, msg, _('Replace All'), wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnFindNextABC(self):
        find_abc = self.find_data.GetFindString().replace(':', '', 1).strip()

        # change selection to be at the end of the current selection and extract the rest of the text from that point on
        p1, p2 = self.editor.GetSelection()
        self.editor.SetSelection(p2, p2)
        abc = self.editor.GetTextRange(p2, self.editor.GetLength())
        abc = abc.encode('utf-8')

        # find occurances of the ABC search string
        for (start_offset, end_offset) in abc_matches_iter(abc, find_abc):
            p1, p2 = start_offset+p2, end_offset+p2  # both offsets are relative to p2, since that's where the extracted text starts
            self.editor.SetSelection(p1, p2)
            self.editor.EnsureVisible(self.editor.LineFromPosition(p2))
            self.editor.EnsureVisible(self.editor.LineFromPosition(p1))
            break
        else:
            self.editor.SetSelection(p1, p2)
            dlg = wx.MessageDialog(self, _('Cannot find "%s"') % self.find_data.GetFindString(), _('Find'), wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
            (self.find_dialog or self.replace_dialog).Raise()

    def OnFindNext(self, evt):
        dialog = self.find_dialog or self.replace_dialog
        if dialog is None:
            return
        dialog.Raise()
        if self.find_data.GetFindString().startswith(':'):
            self.OnFindNextABC()
        else:
            p1, p2 = self.editor.GetSelection()
            if self.find_data.GetFlags() & wx.FR_DOWN:
                self.editor.SetSelection(p2, p2)
            else:
                self.editor.SetSelection(p1, p2)
            self.editor.SearchAnchor()
            if self.find_data.GetFlags() & wx.FR_DOWN:
                search_func = self.editor.SearchNext
            else:
                search_func = self.editor.SearchPrev
            pos = search_func(self.get_scintilla_find_flags(), self.find_data.GetFindString())
            if pos == -1:
                self.editor.SetSelection(p1, p2)
                dlg = wx.MessageDialog(self, _('Cannot find "%s"') % self.find_data.GetFindString(), _('Find'), wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                (self.find_dialog or self.replace_dialog).Raise()
            else:
                p1, p2 = pos, pos+len(self.find_data.GetFindString())
                self.editor.SetSelection(p1, p2)
                self.editor.EnsureVisible(self.editor.LineFromPosition(p2))
                self.editor.EnsureVisible(self.editor.LineFromPosition(p1))
                # 1.3.6.1 [JWdJ] 2014-01-30 Cursor not lost after find-next
                self.editor.EnsureCaretVisible()

    def OnAbout(self, evt):
        dlg = AboutFrame(self)
        dlg.ShowModal()
        dlg.Destroy()

    def OnCheckLastestVersion(self, evt):
        show_in_browser('https://sourceforge.net/projects/easyabc/files/EasyABC/')

    def OnEasyABCHelp(self, evt):
        #FAU:HELP:the original page of EasyABC from Nils Libeg is not available anymore, so point to sourceforge guide
        #show_in_browser('https://www.nilsliberg.se/ksp/easyabc/')
        show_in_browser('https://easyabc.sourceforge.net')

    def OnABCStandard(self, evt):
        show_in_browser('https://abcnotation.com/wiki/abc:standard:v2.1')

    def OnABCLearn(self, evt):
        show_in_browser('https://abcnotation.com/learn')

    # 1.3.6.1 [SS] 2015-01-28
    def OnAbcm2psHelp(self, evt):
        show_in_browser('http://moinejf.free.fr/abcm2ps-doc/')

    # 1.3.6.1 [SS] 2015-01-28
    def OnAbc2midiHelp(self, evt):
        show_in_browser('https://abcmidi.sourceforge.io/')

    def OnAbcCheatSheet(self, evt):
        #FAU:HELP:The original ABC Quick Ref is not available changing to a github repository
        #show_in_browser('http://www.stephenmerrony.co.uk/uploads/ABCquickRefv0_6.pdf')
        show_in_browser('https://sourceforge.net/projects/easyabc/files/Documentation/ABCquickRefv0_6.pdf/download')

    def OnClearCache(self, evt):
        # make sure that any currently played/loaded midi file is released by the media control
        #patch from Seymour: ensure that the media player exists with the statement
        self.stop_playing()

        dir_name = os.path.join(self.app_dir, 'cache')
        # 1.3.6 [SS] 2014-11-16
        files = [os.path.join(dir_name, f) for f in os.listdir(dir_name) if f.startswith('temp') and f[-3:] in ('png', 'svg', 'abc', 'mid', 'idi', 'pdf')]

        if evt is None: #PO9 2014-10-26
            result = wx.OK # remove cache silently
        else:
            total_size = sum(os.path.getsize(f) for f in files)
            mb = float(total_size) / (1024**2)
            result = wx.MessageBox(_("This will remove %(count)s temporary files stored in the directory %(dir)s that in total use %(size).2f MB of your disk space. Proceed?") % {'count': len(files), 'dir': dir_name, 'size': mb},
                               _("Clear cache?"), wx.ICON_QUESTION | wx.OK | wx.CANCEL)
        if result == wx.OK:
            for f in files:
                try:
                    os.remove(f)
                except:
                    pass
            self.svg_tunes.cleanup()
            self.midi_tunes.cleanup()

    # 1.3.6.1 [SS] 2014-12-28 2015-01-22
    def OnColdRestart(self, evt):
        result = wx.MessageBox(_("This will close EasyAbc and put it in a state so that it starts with default settings."
        "i.e. the file settings1.3 will be deleted."),
                               _("Proceed?"), wx.ICON_QUESTION | wx.OK | wx.CANCEL)
        if result == wx.OK:
            f = os.path.join(self.app_dir, 'settings1.3.dat')
            os.remove(f)
            self.music_update_thread.abort()
            self.is_closed = True
            self.manager.UnInit()
            self.Destroy()

    def OnMidiSettings(self, evt):
        dlg = MidiSettingsFrame(self, self.settings)
        try:
            modal_result = dlg.ShowModal()
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window

    #p09 revised to use MyNoteBook
    def OnAbcSettings(self, evt):
        # 1.3.6.4 [SS] 2015-07-07
        win = wx.FindWindowByName('settingsbook')
        if win is None or not self.settingsbook:
            self.settingsbook = MyNoteBook(self, self.settings, self.statusbar)
            self.settingsbook.Show()
        else:
            win.Iconize(False)
            win.Raise()

    def OnChangeFont(self, evt):
        font = wx.GetFontFromUser(self, self.editor.GetFont(), _('Select a font for the ABC editor'))
        if font and font.IsOk():
            f = font
            self.settings['font'] = (f.GetPointSize(), f.GetFamily(), f.GetStyle(), f.GetWeight(), f.GetUnderlined(), f.GetFaceName())
            self.InitEditor(f.GetFaceName(), f.GetPointSize())

    def OnViewFieldReference(self, evt):
        if not self.field_reference_frame:
            self.field_reference_frame = frame = wx.Frame(self, wx.ID_ANY, _('ABC fields and commands reference'), wx.DefaultPosition, (700, 500),
                                                          style=wx.RESIZE_BORDER | wx.CLOSE_BOX | wx.FRAME_TOOL_WINDOW | wx.CAPTION | wx.FRAME_FLOAT_ON_PARENT | wx.SYSTEM_MENU  )
            tree = FieldReferenceTree(frame, -1)
            sizer = wx.GridSizer(1, 1, 0, 0)
            sizer.Add(tree, flag=wx.EXPAND)
            #frame.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            #tree.SetFont(frame.GetFont())
            frame.CreateStatusBar()
            frame.SetSizer(sizer)
            frame.SetAutoLayout(True)
            frame.Centre()
            frame.tree = tree
            frame.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnFieldReferenceItemDClick)
        self.field_reference_frame.Show(True)

    def OnFieldReferenceItemDClick(self, event):
        item = event.GetItem()
        if item and item.GetChildrenCount() == 0:
            cmd, desc = self.field_reference_frame.tree.GetItemText(item, 0), self.field_reference_frame.tree.GetItemText(item, 1)
            # 1.3.6.3 [JWdJ] 2015-02 bugfix: always insert at beginning of next line if current line is not empty
            current_line = self.editor.GetCurrentLine()
            text = cmd.ljust(30) + '% ' + desc
            line_start = self.editor.PositionFromLine(current_line)
            line_end = self.editor.GetLineEndPosition(current_line)
            if line_start != line_end:
                text = os.linesep + text
            self.editor.SetSelection(line_end, line_end)
            self.replace_selection(text)
        else:
            event.Skip()

    def OnUseDefaultFont(self, evt):
        if 'font' in self.settings:
            del self.settings['font']
            self.save_settings()
            for frame in wx.GetApp().GetAllFrames():
                frame.load_and_apply_settings()
                frame.InitEditor()

    def closestNoteData(self, page, row_offset, line, col):
        """Find the NoteData of the closest note to cursor position
        
        Parameters
        ----------
        page : SvgPage
            One page of score of SvgPage
        row_offset : int
            An offset to align line to a line of note
        line : int
            Line where the cursor or selection is in the editor
        col : int
            Col where the cursor or selection is in the editor
            
        Returns
        -------
        closest_note_data : namedTuple NoteData
            closest NoteData found in the page
        """
        
        closest_note_data = None
        line -= row_offset
        # Next variables initialised with a value that should be big enough to find closest
        closest_col = -9999
        note_delta = 9999
        bar_start = bar_start_tmp = 0
        bar_end = 9999
        
        if page.notes_in_row is not None and line in page.notes_in_row:
            for note_data in page.notes_in_row[line]:
                # note_type B is a Bar and first listed
                # need to manage cursor after last bar of the line
                if note_data.note_type == "B" and bar_start == 0:
                    if note_data.col > col:
                        bar_end = min(bar_end,note_data.col)
                        bar_start = bar_start_tmp
                    if note_data.col < col:
                        bar_start_tmp = max(bar_start_tmp,note_data.col)
                # note_type N is a Note, note_type R is a Rest
                if (note_data.note_type == "N" or note_data.note_type == "R") and bar_start<=note_data.col<=bar_end and (closest_note_data is None or col>=note_data.col) and (abs(col - note_data.col)<note_delta): 
                    note_delta=abs(col - note_data.col)
                    closest_note_data = note_data
        
        return closest_note_data

    def FindNotesIndicesBetween2Notes(self, page, note_data_1, note_data_2):
        """Find the indices of the notes between 2 notes
        
        Need to consider the various cases of selection.
        For now only single selection mode is supported with contiguous selection.
        Todo: manage multiple selections
        
        Parameters
        ----------
        page : SvgPage
            One page of score of SvgPage
        note_data_1 : namedtuple note_data
            Note data of the 1st note
        note_data_2 : namedtuple note_data
            Note data of the 2nd note
            
        Returns
        -------
        set_of_indices : set
            set containing all the indices of notes between two other notes (included)
        """
        
        set_of_indices = set()
        
        for row in page.notes_in_row:
            if row == note_data_1.row and row == note_data_2.row:
                for note_data in page.notes_in_row[row]:
                    if (note_data.note_type == "N" or note_data.note_type == "R") and note_data.col>=note_data_1.col and note_data.col<=note_data_2.col:
                        set_of_indices = set_of_indices.union(page.get_indices_for_row_col(note_data.row,note_data.col))
                break
            if row == note_data_1.row and row < note_data_2.row:
                for note_data in page.notes_in_row[row]:
                    if (note_data.note_type == "N" or note_data.note_type == "R") and note_data.col>=note_data_1.col:
                        set_of_indices = set_of_indices.union(page.get_indices_for_row_col(note_data.row,note_data.col))
            elif row > note_data_1.row and row < note_data_2.row:
                for note_data in page.notes_in_row[row]:
                    if (note_data.note_type == "N" or note_data.note_type == "R"):
                        set_of_indices = set_of_indices.union(page.get_indices_for_row_col(note_data.row,note_data.col))
            elif row > note_data_1.row and row == note_data_2.row:
                for note_data in page.notes_in_row[row]:
                    if (note_data.note_type == "N" or note_data.note_type == "R") and note_data.col<=note_data_2.col:
                        set_of_indices = set_of_indices.union(page.get_indices_for_row_col(note_data.row,note_data.col))
        
        return set_of_indices
        
    def ScrollMusicPaneToMatchEditor(self, select_closest_note=False, select_closest_page=False):
        """Scroll the score in the Music Pane to match the editor pointer and highlight notes
        
        Parameters
        ----------
        select_closest_note : bool, optional
            A flag to identify whether note closest to pointer in editor or
            text selection is to be highlighted (default is False)
        select_closest_page : bool, optional
            A flag used to align score view in Music Pane to editor selection
            (default is False)
            
        Returns
        -------
        Nothing to return
        """
        
        tune = self.GetSelectedTune()
        if not tune or not self.current_svg_tune or (not select_closest_note and not select_closest_page):
            #FAU: No need to continue to process
            return
        #if len(self.music_pane.current_page.notes) == 0:
        #    #FAU: Notes were never drawn, force to draw otherwise error in multipage when switching page
        #    self.music_pane.current_page.draw()
        
        # workaround for the fact the abcm2ps returns incorrect row numbers
        # check the row number of the first note and if it doesn't agree with the actual value
        # then pretend that we have more or less extra header lines
        num_header_lines, first_note_line_index = self.get_num_extra_header_lines(tune)

        caret_current_pos = self.editor.GetCurrentPos()
        caret_current_row = self.editor.LineFromPosition(caret_current_pos)
        tune_first_line_no = self.editor.LineFromPosition(tune.offset_start)

        #FAU: Get the text selection and then corresponding line
        #     To enable to highlight notes based on selection need also to make sure
        #     on which svgPage the selection starts and ends
        p1, p2 = self.editor.GetSelection()
        line_p2 = self.editor.LineFromPosition(p2)
        line_p1 = self.editor.LineFromPosition(p1)
        p1_page_index = p2_page_index = self.current_page_index
        
        #FAU: This part is to find the associated svgPage.
        #     It used to exit as soon as page of the cursor is found but need to browse completely
        #     as selection can be on multiple svgPages
        #if select_closest_page or select_closest_note:
        abc_from_editor = AbcTune(self.editor.GetTextRange(tune.offset_start, tune.offset_end))
        first_note_editor = abc_from_editor.first_note_line_index
        
        #if first_note_editor is not None:
        if first_note_editor is None:
            #No need to continue as no Note
            return
        
        caret_body_row = caret_current_row - tune_first_line_no - first_note_editor
        p1_body_row = max(line_p1 - tune_first_line_no - first_note_editor, 0)
        p2_body_row = max(line_p2 - tune_first_line_no - first_note_editor,0)
        if caret_body_row >= 0:
            # create a list of pages but start with the current page because it has the most chance
            #page_indices = [self.current_page_index] + \
            #               [p for p in range(self.current_svg_tune.page_count) if p != self.current_page_index]
            #FAU: To manage selection no need to prioritize
            page_indices = [p for p in range(self.current_svg_tune.page_count)]
            caret_svg_row = caret_body_row + self.current_svg_tune.first_note_line_index + 1 # row in svg-file is 1-based
            p1_row = p1_body_row + self.current_svg_tune.first_note_line_index + 1 
            p2_row = p2_body_row + self.current_svg_tune.first_note_line_index + 1 
            new_page_index = None
            for page_index in page_indices:
                page = self.current_svg_tune.render_page(page_index, self.renderer)
                page.draw()
                if page and page.notes_in_row and caret_svg_row in page.notes_in_row:
                    new_page_index = page_index
                    #FAU: Do not break anymore to find other pages for selection 
                    #break
                    #if p1_row == caret_svg_row and p2_row == caret_svg_row:
                    #    p1_page_index = p2_page_index = page_index
                    #    p1_page = p2_page = page
                    #    break
                if page and page.notes_in_row and p1_row in page.notes_in_row:
                    p1_page_index = page_index
                    p1_page = page
                if page and page.notes_in_row and p2_row in page.notes_in_row:
                    p2_page_index = page_index
                    p2_page = page
                #if new_page_index is not None and p1_page_index is not None and p2_page_index is not None:
                #    break

            if select_closest_page and new_page_index is not None and new_page_index != self.current_page_index:
                self.select_page(new_page_index)
        else:
            select_closest_note=False
            
        musicpane_current_page = self.music_pane.current_page # 1.3.6.2 [JWdJ]
        if len(musicpane_current_page.notes) == 0:
            #FAU: at this point in time notes should be drawn already thus if no notes then remove flag select
            select_closest_note=False
        
        #FAU: This is to track for the current page shown in the musicpane.
        current_page_index = self.current_page_index
        
        #FAU: To search for the closest note, value initialised corresponding to a long distance
        closest_xy = None
        #closest_col = -9999
        #note_delta = 9999
        #closest_note_indice = None
        closest_note_indice_p2 = None
        closest_note_data_p1 = None
        closest_note_data_p2 = None
        
        selection_multi_notes = False
        current_position_is_p1 = False
        if p1!=p2 and select_closest_note:
            #FAU:  As in a selection do not highlight the note just after the cursor. Thus remove 1.
            p2 -= 1
            selection_multi_notes = True
            #FAU: current_position_is_p1 is defined to identify which page to show depending on selection
            #     from left to right (False) or right to left (True).
            if p1 == caret_current_pos:
                current_position_is_p1 = True
        
        # 1.3.6.2 [JWdJ] 2015-02
        row_offset = tune_first_line_no - 1 - num_header_lines
        
        if select_closest_note:
            #FAU: This is to manage the case with selection not completely in the current page or even not at all comprised
            if p2_page_index != current_page_index or p1_page_index != current_page_index:                
                if (p2_page_index > current_page_index and p1_page_index > current_page_index) or (p2_page_index < current_page_index and p1_page_index < current_page_index):
                    #FAU: no need to continue to process so can return
                    musicpane_current_page.clear_note_selection()
                    if select_closest_note:
                        wx.CallAfter(self.music_pane.redraw)
                    return
                else:
                    if p2_page_index > current_page_index:
                        closest_note_data_p2 = self.closestNoteData(p2_page,row_offset,line_p2,p2 - self.editor.PositionFromLine(line_p2))
                        closest_note_indice_p2 = p2_page.get_indices_for_row_col(closest_note_data_p2.row,closest_note_data_p2.col)
                    if p1_page_index < current_page_index:
                        closest_note_data_p1 = self.closestNoteData(p1_page,row_offset,line_p1,col = p1 - self.editor.PositionFromLine(line_p1))
            
            #FAU: search note data corresponding to selection
            if closest_note_data_p2 is None:
                col = p2 - self.editor.PositionFromLine(line_p2)
                closest_note_data_p2 = self.closestNoteData(musicpane_current_page,row_offset,line_p2,col)
            if selection_multi_notes and closest_note_data_p2 is not None:
                if closest_note_data_p1 is None:
                    col = p1 - self.editor.PositionFromLine(line_p1)
                    closest_note_data_p1 = self.closestNoteData(musicpane_current_page,row_offset,line_p1,col)
                if closest_note_data_p1 is None:
                    #No note found close to p1 so ignore multi note selection
                    selection_multi_notes = False
                else:
                    selected_indices = self.FindNotesIndicesBetween2Notes(musicpane_current_page, closest_note_data_p1, closest_note_data_p2)
            else:
                selection_multi_notes = False
        
        ## 1.3.6.2 [JWdJ] 2015-02
        #for i, (x, y, abc_row, abc_col, desc) in enumerate(page.notes):
        #    abc_row += row_offset
        #    #FAU 20250126: search for the closest while not switching to next one to early
        #    #              with if abc_row == line and and (abs(col - abc_col) < abs(closest_col - abc_col))
        #    #              as soon as cursor shifted after the letter of note next note was selected even if only duration of previous note
        #    #              %%TODO%%: improve to consider highlight only if cursor is in a note?
        #    if abc_row == line and col>=abc_col and (abs(col - abc_col)<note_delta): # and (abs(col - abc_col) < abs(closest_col - abc_col))
        #        note_delta=abs(col - abc_col)
        #        closest_col = abc_col
        #        closest_xy = (x, y)
        #        if select_closest_note:
        #            closest_note_indice = i
        #            #if page.selected_indices != {i}:
        #            #    # 1.3.6.2 [JWdJ] 2015-02
        #            #    page.clear_note_selection()
        #            #    page.add_note_to_selection(i)
        #            #    self.selected_note_indices = [i]
        #            #    self.selected_note_descs = [page.notes[i] for i in self.selected_note_indices]
        
        if closest_note_data_p2 is not None:
            if closest_note_indice_p2 is None:
                closest_note_indice_p2 = musicpane_current_page.get_indices_for_row_col(closest_note_data_p2.row,closest_note_data_p2.col)
            closest_xy = (closest_note_data_p2.x,closest_note_data_p2.y)
            musicpane_current_page.clear_note_selection()
            if selection_multi_notes:
                self.selected_note_indices = []
                for i in selected_indices:
                    musicpane_current_page.add_note_to_selection(i)
                    self.selected_note_indices.append(i)
            elif select_closest_note:
                for i in closest_note_indice_p2:
                    musicpane_current_page.add_note_to_selection(i)
                    self.selected_note_indices = [i]
                
            self.selected_note_descs = [musicpane_current_page.notes[i] for i in self.selected_note_indices]
        elif select_closest_note:
            musicpane_current_page.clear_note_selection()
            if select_closest_note:
                wx.CallAfter(self.music_pane.redraw)
        
        if closest_note_data_p1 is not None and ((current_position_is_p1 and 
                    closest_note_data_p1.row in musicpane_current_page.notes_in_row)
                    or
                    (p1_page_index == current_page_index and p2_page_index != current_page_index)):
            closest_xy = (closest_note_data_p1.x,closest_note_data_p1.y)
        
        if closest_xy is not None:
            if select_closest_note:
                wx.CallAfter(self.music_pane.redraw)
            self.scroll_music_pane(*closest_xy)

    def scroll_music_pane(self, x, y):
        #FAU: Scroll function need to take into account the zoom factor
        x = self.zoom_factor*x
        y = self.zoom_factor*y
        sx, sy = self.music_pane.CalcUnscrolledPosition((0, 0))
        vw, vh = self.music_pane.VirtualSize
        w, h = self.music_pane.ClientSize
        margin = 50
        orig_scroll = (sx, sy)
        if not sx+margin <= x <= w+sx-margin:
            sx = x - w + w/5
        if not (sy+margin <= y <= h+sy-margin):
            sy = y-h/2
        sx = max(0, min(sx, vw))
        sy = max(0, min(sy, vh))
        if (sx, sy) != orig_scroll:
            ux, uy = self.music_pane.GetScrollPixelsPerUnit()
            self.music_pane.Scroll(int(sx/ux), int(sy/uy))

    def select_tune_at_current_pos(self):
        line_no = self.editor.LineFromPosition(self.editor.GetCurrentPos())
        total_tunes = self.tune_list.GetItemCount()
        found_index = next((i for i, (index, title, startline) in enumerate(self.tunes) if startline > line_no), total_tunes) - 1

        tune_list = self.tune_list
        get_item_data = tune_list.GetItemData
        if found_index == -1:
            tune_list.DeselectAll()
        else:
            index = next((i for i in xrange(tune_list.GetItemCount()) if get_item_data(i) == found_index), -1)  # list could be sorted
            if index != -1:
                if index == tune_list.GetFirstSelected():
                    self.ScrollMusicPaneToMatchEditor(select_closest_page=self.mni_auto_refresh.IsChecked())
                else:
                    tune_list.DeselectAll()
                    tune_list.SelectItem(index)
                    tune_list.EnsureVisible(index)
                    self.music_pane.Scroll(0, 0)

        if self.abc_assist_panel.IsShown():
            self.abc_assist_panel.update_assist()

    def OnMovedToDifferentLine(self, queue_number_movement):
        if self.queue_number_movement != queue_number_movement:
            return
        self.select_tune_at_current_pos()

    def AutoInsertXNum(self):
        xNum = 0
        editor = self.editor
        get_line = editor.GetLine
        for line_no in xrange(editor.GetLineCount()):
            m = tune_index_re.match(get_line(line_no))
            if m:
                xNum = max(xNum, int(m.group(1)))

        editor.BeginUndoAction()
        p = editor.GetCurrentPos()
        editor.SetSelection(p, p)
        editor.ReplaceSelection(str(xNum+1))
        line = editor.GetCurrentLine()
        end_pos = editor.GetLineEndPosition(line)
        editor.SetSelection(end_pos, end_pos)
        editor.EndUndoAction()

    def DoReMiToNote(self, char):
        doremi_index = doremi_prefixes.find(char)
        if doremi_index >= 0:
            tune = self.GetSelectedTune()
            if tune:
                matches = re.findall(r'(?<=[\r\n\[])K: *([A-Ga-g])', self.editor.GetTextRange(tune.offset_start, self.editor.GetCurrentPos()))
                if matches:
                    K = matches[-1]
                    base_note_index = note_to_index(K.upper())
                    note = all_notes[base_note_index + doremi_index]
                    if char == char.upper():
                        return note[0].upper()
                    else:
                        return note[0].lower()
        return char

    def OnCharEvent(self, evt):
        # 1.3.7 [JWdJ] 2016-01-06
        if self.current_svg_tune and evt.KeyCode in [wx.WXK_PAGEDOWN, wx.WXK_PAGEUP, wx.WXK_HOME, wx.WXK_END]:
            # 1.3.7.0 [JWdJ] 2015-12 Added shortcuts to navigate through pages
            new_page = -1
            if evt.KeyCode == wx.WXK_HOME and evt.GetModifiers() == (wx.MOD_ALT + wx.MOD_CONTROL):
                new_page = 0
            elif evt.KeyCode == wx.WXK_END and evt.GetModifiers() == (wx.MOD_ALT + wx.MOD_CONTROL):
                new_page = self.current_svg_tune.page_count - 1
            elif evt.KeyCode == wx.WXK_PAGEDOWN and evt.GetModifiers() in [wx.MOD_ALT, wx.MOD_ALT + wx.MOD_CONTROL]:
                new_page = self.current_page_index + 1
            elif evt.KeyCode == wx.WXK_PAGEUP and evt.GetModifiers() in [wx.MOD_ALT, wx.MOD_ALT + wx.MOD_CONTROL]:
                new_page = self.current_page_index - 1

            if 0 <= new_page < self.current_svg_tune.page_count and new_page != self.current_page_index:
                self.select_page(new_page)
                evt.Skip()
                return

        editor = self.editor
        cur_pos = editor.GetCurrentPos()
        in_music_code = self.position_is_music_code(cur_pos)

        c = unichr(evt.GetUnicodeKey())
        p1, p2 = editor.GetSelection()
        no_selection = p1 == p2

        # 1.3.6.2 [JWdJ] 2015-02
        line, caret = editor.GetCurLine()
        is_inside_field = len(line)>=2 and line[1] == ':' and re.match(r'[A-Za-z\+]', line[0]) or line.startswith('%')
        if is_inside_field:
            evt.Skip()
            return
        is_inside_chord = self.position_is_in_chord(cur_pos)
        at_end_of_line = not line[caret:].strip(' \r\n|:][')
        use_typing_assist = self.mni_TA_active.IsChecked()
        if use_typing_assist and in_music_code and not is_inside_chord:
            if c == '-' and no_selection:
                self.AddTextWithUndo('- ')
                return

            if c == ' ':
                try:
                    self.FixNoteDurations()
                    if no_selection and self.add_bar_if_needed():
                        return
                    else:
                        evt.Skip()
                except Exception:
                    evt.Skip()
                    raise
            elif self.mni_TA_add_bar_auto.IsChecked() and no_selection and c not in "-/<,'1234567890\"!":
                if c in '|]&':
                    if c == ']':
                        bar_text = '|]'
                    else:
                        bar_text = c
                    if self.add_bar_if_needed(bar_text):
                        return
                elif c == ':':
                    if not (caret == 1 and line.rstrip() in [u'X', u'Z']) and self.add_bar_if_needed(':|'):
                        return
                else:
                    self.add_bar_if_needed()

        # when there is a selection and 's' is pressed it serves as a shortcut for slurring
        if p1 != p2 and c == 's':
            c = '('

        if c == ':':
            # fill in unique tune index after typing X:
            evt.Skip()
            if (line.rstrip(), caret) == (u'X', 1):
                wx.CallAfter(self.AutoInsertXNum)

        elif c == '3' and p1 == p2 and editor.GetTextRange(p1-1, p1+1) == '()' and in_music_code:
            # if the user writes ( which is auto-completed to () and then writes 3, he/she probably
            # wants to start a triplet so we delete the right parenthesis
            editor.BeginUndoAction()
            editor.SetSelection(p1, p1+1)
            editor.ReplaceSelection(c)
            editor.EndUndoAction()

        elif (c in ']}' and editor.GetTextRange(p1, p1+1) == c and in_music_code) or \
                (c == '"'  and editor.GetTextRange(p1, p1+1) == c and editor.GetTextRange(p1-1, p1) != '\\'):
            # unless this is not a field line
            if re.match('[a-zA-Z]:', line):
                evt.Skip()
            # if there is already a ] or }, just move one step to the right
            else:
                editor.SetSelection(p1+1, p1+1)

        elif c in '([{"':
            start, end = {'(': '()', '[': '[]', '{': '{}', '"': '""'}[c]

            # if this is a text or chord, then don't replace selection, but insert the new text/chord in front of the note(s) selected
            if c == '"':
                editor.SetSelection(p1, p1)
                p2 = p1

            first_char, last_char = editor.GetTextRange(p1-1, p1), editor.GetTextRange(p2, p2+1)
            orig_p1 = p1

            # if this is a triplet with a leading '(' then virtually move the selection start a bit to the left
            if p1 != p2 and last_char == ')' and editor.GetTextRange(p1-3, p1) == '((3':
                p1 -= 2
                first_char = '('
            if p1 != p2 and first_char == start and last_char == end and first_char != '"':
                editor.BeginUndoAction()
                editor.SetSelection(p2, p2+1)
                editor.ReplaceSelection('')
                editor.SetSelection(p1-1, p1)
                editor.ReplaceSelection('')
                editor.SetSelection(orig_p1-1, p2-1)
                editor.EndUndoAction()
            elif p1 != p2 and c != '[':
                editor.BeginUndoAction()
                # if this is a triplet, then start the slur just before '(3' instead of after.
                if c == '(' and last_char == ' ' and editor.GetTextRange(p1-2, p1) == '(3':
                    editor.InsertText(p1-2, start)
                else:
                    editor.InsertText(p1, start)
                editor.InsertText(p2+1, end)
                editor.SetSelection(p1+1, p2+1)
                editor.EndUndoAction()
            elif in_music_code and use_typing_assist and self.mni_TA_add_right.IsChecked():
                if c == '"' and line.count('"') % 2 == 1 or \
                        c != '"' and line.count(end) > line.count(start):
                    evt.Skip()
                else:
                    editor.ReplaceSelection(start + end)
                    editor.SetSelection(p1+1, p1+1)
            else:
                evt.Skip()
        elif c in '<>' and (p2 - p1) > 1:
            try:
                editor.BeginUndoAction()
                base_pos = editor.GetSelectionStart()
                text = editor.GetSelectedText()
                notes = get_notes_from_abc(text, exclude_grace_notes=True)
                total_offset = 0
                for (start, end, abc_note_text) in notes[0::2]:
                    p = base_pos + end + total_offset
                    if re.match(r'[_=^]', abc_note_text):
                        p += 1
                    cur_char = editor.GetTextRange(p-1, p)
                    if cur_char == '<' and c == '>' or cur_char == '>' and c == '<':
                        editor.SetSelection(p-1, p)
                        editor.ReplaceSelection('')
                        total_offset -= 1
                    else:
                        editor.SetSelection(p, p)
                        editor.AddText(c)
                        total_offset += 1
                editor.SetSelection(p1, p2+total_offset)
            finally:
                editor.EndUndoAction()
        elif c == '.' and p1 != p2:
            # staccato selection
            try:
                editor.BeginUndoAction()
                base_pos = editor.GetSelectionStart()
                text = editor.GetSelectedText()
                notes = get_notes_from_abc(text, exclude_grace_notes=True)
                total_offset = 0
                for (start, end, abc_note_text) in notes:
                    p = base_pos + start + total_offset
                    #if re.match(r'[_=^]', abc_note_text):
                    #    p -= 1
                    cur_char = editor.GetTextRange(p-1, p)
                    if cur_char == '.':
                        editor.SetSelection(p-1, p)
                        editor.ReplaceSelection('')
                        total_offset -= 1
                    else:
                        editor.SetSelection(p, p)
                        editor.AddText(c)
                        total_offset += 1
                editor.SetSelection(p1, p2+total_offset)
            finally:
                editor.EndUndoAction()
        elif self.keyboard_input_mode and in_music_code:
            keys = u'asdfghjkl\xf6\xe4'
            sharp_keys = '' #u'\x00wertyuiop\xe5\x00'
            flat_keys = '' #u'<zxcvbnm,.-'

            i = -1
            if c in keys:
                i, accidental = keys.index(c), ''
            elif c in sharp_keys:
                i, accidental = sharp_keys.index(c), '^'
            elif c in flat_keys:
                i, accidental = flat_keys.index(c), '_'
            if i == -1:
                evt.Skip()
            else:
                if not self.keyboard_input_base_key:
                    self.keyboard_input_base_key = i
                else:
                    note = all_notes[i - self.keyboard_input_base_key + self.keyboard_input_base_note]
                    editor.ReplaceSelection(accidental + note)

        # automatically select uppercase/lowercase - choose the one that will make this note be closest to the previous note
        elif use_typing_assist and in_music_code and p1 == p2 and at_end_of_line and self.mni_TA_auto_case.IsChecked() \
            and (not self.mni_TA_do_re_mi.IsChecked() and c in 'abcdefgABCDEFG' or \
                  self.mni_TA_do_re_mi.IsChecked() and c in doremi_prefixes):

            if self.mni_TA_do_re_mi.IsChecked():
                c = self.DoReMiToNote(c)[0]

            # get the text of the previous and current line up to the position of the cursor
            prev_line = editor.GetLine(editor.GetCurrentLine()-1)
            text = prev_line + line[:caret]

            p = cur_pos

            last_note_number = None
            # go backwards (to the left from the cursor) and look for the first note
            for i in range(len(text)-1):
                if p-i >= 1 and self.position_is_music_code(p-i-1):
                    m = re.match(r"([A-Ga-g][,']?)", text[len(text)-1-i : len(text)-1-i+2])
                    if m:
                        last_note_number = note_to_index(m.group(0))
                        break

            if last_note_number is None:
                if self.mni_TA_do_re_mi.IsChecked():
                    editor.AddText(c)
                else:
                    evt.Skip()
            else:
                # sort matching note by distance to the last note and give a slightly penalty to
                # note names that include ' or , since we prefer jumping to an alternative somewhere in the middle
                all_matches = [(abs(i - last_note_number) + int(',' in n)*0 + int("'" in n)*0, n)
                               for (i, n) in enumerate(all_notes)
                               if n[0].lower() == c.lower() and len(n) == 1]    # temporarily turned off my advanced logic
                all_matches.sort()
                if all_matches:
                    if evt.ShiftDown():
                        c = all_matches[1][1]  # second "best" choice
                    else:
                        c = all_matches[0][1]  # first choice
                    c = c[0]
                    editor.AddText(c)
                else:
                    evt.Skip()

        elif use_typing_assist and in_music_code and self.mni_TA_do_re_mi.IsChecked():
            if c in doremi_prefixes:
                c = self.DoReMiToNote(c)
                editor.AddText(c)
            elif c not in doremi_suffixes:
                evt.Skip()

        else:
            evt.Skip()


    def get_metre_and_default_length(self, abc):
        return AbcTune(abc).get_metre_and_default_length()

    def FixNoteDurations(self):
        # 1.3.6.2 [JWdJ] 2015-02
        use_add_note_durations = self.mni_TA_active.IsChecked() and self.mni_TA_add_note_durations.IsChecked()
        if not use_add_note_durations:
            return

        tune = self.GetSelectedTune()
        if not tune:
            return

        line_start_offset = self.editor.PositionFromLine(self.editor.GetCurrentLine())
        text = self.editor.GetTextRange(line_start_offset, self.editor.GetCurrentPos())
        abc_up_to_selection = self.editor.GetTextRange(tune.offset_start, self.editor.GetCurrentPos())

        # find the position of the last bar symbol or space
        start_offset = max([0] + [m.start(0) for m in re.finditer('(%s)| ' % bar_sep.pattern, text)])
        text = text[start_offset:]
        notes = get_notes_from_abc(text, exclude_grace_notes=True)
        note_pattern = re.compile(r"(?P<note>([_=^]?[A-Ga-gxz]([,']+)?))(?P<len>\d{0,2}/\d{1,2}|/+|\d{0,2})(?P<dur_mod>[><]?)")

        # determine L: and M: fields
        metre, default_len = self.get_metre_and_default_length(abc_up_to_selection)

        # 1.3.6.3 [JWdJ] 2015-03
        if use_add_note_durations and not '[' in text:
            # does any of these notes have a duration specified?
            any_duration_specified = False
            for (start, end, abc_note_text) in notes:
                m = note_pattern.match(abc_note_text)
                if not m:
                    return
                if m.group('len'):
                    any_duration_specified = True
                    break
            if not any_duration_specified:
                total_duration = get_bar_length(text, default_len, metre)
                durations = []  # new durations to assign to notes
                if metre.denominator == 4 and total_duration != Fraction(1, 4):
                    if '(3' in text:
                        if len(notes) == 3:
                            durations = [Fraction(1,8), Fraction(1,8), Fraction(1,8)]
                    else:
                        if len(notes) == 1:
                            durations = [Fraction(1,4)]
                        elif len(notes) == 2:
                            durations = [Fraction(1,8)]*2
                        elif len(notes) == 3:
                            durations = [Fraction(1,8), Fraction(1,16), Fraction(1,16)]
                        elif len(notes) == 4:
                            durations = [Fraction(1,16)]*4
                elif str(metre) == str(Fraction(6, 8)):
                    if '(3' not in text:
                        if len(notes) == 1:
                            durations = [Fraction(3,8)]
                        if len(notes) == 2:
                            durations = [Fraction(1,4), Fraction(1,8)]
                        elif len(notes) == 3:
                            durations = [Fraction(1,8), Fraction(1,8), Fraction(1,8)]

                extra_offset = 0
                if durations:
                    sel_start = self.editor.GetSelectionStart()
                    self.editor.BeginUndoAction()
                    try:
                        for (d, (start, end, abc_note_text)) in zip(durations, notes):
                            abc_note_text_len = len(re.match(r"[_=^]?[A-Ga-gz](,+|'+)?", abc_note_text).group(0))
                            p = line_start_offset + start_offset + start + extra_offset + abc_note_text_len
                            dur_text = duration2abc(d / default_len)
                            extra_offset += len(dur_text)
                            self.editor.InsertText(p, dur_text)
                    finally:
                        self.editor.EndUndoAction()
                    sel_start += extra_offset
                    self.editor.SetSelection(sel_start, sel_start)

    def add_bar_if_needed(self, bar_text = '|'):
        tune = self.GetSelectedTune()
        if not tune:
            return

        # check if the bar is full and a new bar should start
        # 1.3.6.2 [JWdJ] 2015-02
        use_add_bar = self.mni_TA_active.IsChecked() and (self.mni_TA_add_bar.IsChecked() or self.mni_TA_add_bar_auto.IsChecked())
        if use_add_bar:
            current_pos = self.editor.GetCurrentPos()
            line_start_offset = self.editor.PositionFromLine(self.editor.GetCurrentLine())
            text = self.editor.GetTextRange(line_start_offset, current_pos)
            abc_up_to_selection = self.editor.GetTextRange(tune.offset_start, current_pos)

            start_offset = max([0] + [m.end(0) for m in bar_and_voice_overlay_sep.finditer(text)])  # offset of last bar symbol
            text = text[start_offset:]  # the text from the last bar symbol up to the selection point
            metre, default_len = self.get_metre_and_default_length(abc_up_to_selection)

            # 1.3.6.1 [JWdJ] 2015-01-28 bar lines for multirest Zn
            end_of_line_offset = self.editor.GetLineEndPosition(self.editor.GetCurrentLine())
            rest_of_line = self.editor.GetTextRange(current_pos, end_of_line_offset).strip()
            if re.match(r"^[XZ]\d*$", text):
                duration = metre
            else:
                duration = get_bar_length(text, default_len, metre)

            if (duration == metre and not bar_sep.match(rest_of_line) and
                    not (text.rstrip() and text.rstrip()[-1] in '[]:|')):
                self.insert_bar(bar_text)
                return True

    def insert_bar(self, bar_text = '|'):
        # 1.3.6.3 [JWDJ] 2015-3 don't add space before or after bar if space already present
        current_pos = self.editor.GetCurrentPos()
        pre_space = ''
        post_space = ''
        if current_pos > 0 and self.editor.GetTextRange(current_pos-1, current_pos) not in ' \r\n:':
            pre_space = ' '
        if current_pos == self.editor.GetTextLength() or self.editor.GetTextRange(current_pos, current_pos+1) != ' ':
            post_space = ' '
        self.AddTextWithUndo(pre_space + bar_text + post_space)
        if not post_space:
            skip_space_pos = self.editor.GetCurrentPos() + 1
            self.editor.SetSelection(skip_space_pos, skip_space_pos)

    def AddTextWithUndo(self, text):
        self.editor.BeginUndoAction()
        self.editor.AddText(text)
        self.editor.EndUndoAction()

    def replace_selection(self, text):
        self.editor.BeginUndoAction()
        self.editor.ReplaceSelection(text)
        self.editor.EndUndoAction()

    def position_is_music_code(self, position):
        style_at = self.editor.GetStyleAt
        return style_at(position) == self.styler.STYLE_DEFAULT \
            and style_at(position-1) not in (self.styler.STYLE_EMBEDDED_FIELD_VALUE, self.styler.STYLE_EMBEDDED_FIELD, self.styler.STYLE_COMMENT_NORMAL)

    def position_is_in_chord(self, position):
        style_at = self.editor.GetStyleAt
        return style_at(position-1) == self.styler.STYLE_CHORD

    def OnKeyDownEvent(self, evt):
        # temporary work-around for what seems to be a scintilla bug on Mac:
        if wx.Platform == "__WXMAC__" and evt.GetRawKeyCode() == 7683:
            wx.CallAfter(lambda: self.AddTextWithUndo('^'))
            evt.Skip()
            return

        editor = self.editor
        line, caret = editor.GetCurLine()
        in_music_code = self.position_is_music_code(editor.GetCurrentPos())

        use_typing_assist = self.mni_TA_active.IsChecked()
        if evt.GetKeyCode() == wx.WXK_RETURN:
            # 1.3.7.2 [JWDJ] 2016-03-17
            if in_music_code and use_typing_assist and self.mni_TA_add_bar_auto.IsChecked():
                self.add_bar_if_needed()

            # 1.3.6.3 [JWDJ] 2015-04-21 Added line continuation
            if use_typing_assist:
                line = editor.GetCurrentLine()
                for prefix in ['W:', 'w:', 'N:', 'H:', '%%', '%', '+:']:
                    prev_line = editor.GetLine(line-1)
                    if prev_line.startswith(prefix) and editor.GetLine(line).startswith(prefix):
                        if prev_line.startswith(prefix + ' '):  # whether to add a space after W:
                            prefix += ' '
                        wx.CallAfter(lambda: self.AddTextWithUndo(prefix))
                        break
            evt.Skip()
        elif evt.GetKeyCode() == wx.WXK_TAB:
            if in_music_code and editor.GetSelectionStart() == editor.GetSelectionEnd():
                wx.CallAfter(lambda: self.insert_bar())
            else:
                evt.Skip()
        elif evt.GetUnicodeKey() == ord('L') and evt.CmdDown():
            self.ScrollMusicPaneToMatchEditor(select_closest_note=True, select_closest_page=self.mni_auto_refresh.IsChecked())
        elif evt.MetaDown() and evt.GetKeyCode() == wx.WXK_UP:
            editor.GotoPos(0)
        elif evt.MetaDown() and evt.GetKeyCode() == wx.WXK_DOWN:
            editor.GotoPos(editor.GetLength())
        elif evt.MetaDown() and evt.GetKeyCode() == wx.WXK_LEFT:
            editor.GotoPos(editor.PositionFromLine(editor.GetCurrentLine()))
        elif evt.MetaDown() and evt.GetKeyCode() == wx.WXK_RIGHT:
            editor.GotoPos(editor.GetLineEndPosition(editor.GetCurrentLine()))
        else:
            evt.Skip()

    def StartKeyboardInputMode(self):
        editor = self.editor
        line_start_offset = editor.PositionFromLine(editor.GetCurrentLine())
        text = editor.GetTextRange(line_start_offset, editor.GetCurrentPos()) # line up to selection position
        notes = get_notes_from_abc(text)
        if notes:
            self.keyboard_input_mode = True
            m = re.match(r"([_=^]?)(?P<note>[A-Ga-gz][,']*)", notes[-1][-1])
            self.keyboard_input_base_note = note_to_index(m.group('note'))
            self.keyboard_input_base_key = None
            if self.keyboard_input_base_note == -1:
                self.keyboard_input_mode = False

    def OnEditorMouseRelease(self, evt):
        evt.Skip()
        p1, p2 = self.editor.GetSelection()
        if p1 == p2:
            self.ScrollMusicPaneToMatchEditor(select_closest_note=True, select_closest_page=self.mni_auto_refresh.IsChecked())
        else:
            self.ScrollMusicPaneToMatchEditor(select_closest_note=True, select_closest_page=False)

    # p09 This function needs more work, see comments below.
    def OnPosChanged(self, evt):
        # This function is called by the interrupt stc.EVT_STC_UPDATEUI
        # which occurs whenever the edit window is updated. This can
        # occur many times. To view who initializes the interrupt,
        # print traceback.extract_stack(None, n) where n is the
        # depth of the stack to view.
        #print traceback.extract_stack(None, 5)
        self.queue_number_movement += 1
        position = self.editor.GetCurrentPos()
        line_no = self.editor.LineFromPosition(position)
        #print '*****OnPosChanged***** : position =    ',position,'  ',line_no
        if line_no != self.last_line_number_selected:
            self.last_line_number_selected = line_no
            # 1.3.6 [SS] 2014-12-02
            #wx.CallLater(260, self.OnMovedToDifferentLine, self.queue_number_movement)
        # 1.3.6 [SS] 2014-12-02
        wx.CallLater(260, self.OnMovedToDifferentLine, self.queue_number_movement)
        # if you remove the comment from ScrollMusicToMatchEditor, you will
        # not be able to select a group of notes in the MusicPane. On the
        # otherhand, the following function allows the highlighted note
        # in the MusicPane follow the highlighted note in the editor when
        # it is controlled by the keyboard arrow keys. p09
        #FAU 20250126: To avoid to have sort of a race, keep the call but
        #              only when no action on the music pane to select
        #              Add a property in music_pane to identify when a drag selection is ongoing
        if not self.music_pane.mouse_select_ongoing:
            self.ScrollMusicPaneToMatchEditor(select_closest_note=True, select_closest_page=True) #patch p08


    def OnModified(self, evt):
        if self.updating_text:
            return
        if evt.GetLinesAdded() != 0:
            wx.CallAfter(self.UpdateTuneListAndReselectTune)

    def AutomaticUpdate(self, update_number):
        if self.queue_number_refresh_music == update_number:
            self.refresh_tunes()

    def OnChangeText(self, event):
        event.Skip()
        if self.updating_text:
            return
        self.GrayUngray()
        # if auto-refresh is on
        if self.mni_auto_refresh.IsChecked():
            self.queue_number_refresh_music += 1
            wx.CallLater(250, self.AutomaticUpdate, self.queue_number_refresh_music)

    def GrayUngray(self, evt=None):
        editMenu = self.GetMenuBar().GetMenu(1)
        undo, redo, _, cut, copy, paste, delete, _, insert_symbol, _, transpose, note_length, align_bars, _, find, _, findnext, replace, _, selectall = editMenu.GetMenuItems()
        undo.Enable(self.editor.CanUndo())
        redo.Enable(self.editor.CanRedo())

        for mni in (self.mni_TA_auto_case, self.mni_TA_do_re_mi, self.mni_TA_add_note_durations, self.mni_TA_add_right, self.mni_TA_add_bar_disabled, self.mni_TA_add_bar, self.mni_TA_add_bar_auto):
            mni.Enable(self.mni_TA_active.IsChecked())

    def OnUpdate(self, evt):
        c = evt.GetKeyCode()
        if c == wx.WXK_ESCAPE and self.is_fullscreen:
            self.toggle_fullscreen(evt)
        elif c == 344: #F5
            self.refresh_tunes()
        elif c == 345: #F6
            self.OnToolPlay(evt)
            self.play_button.Refresh()
        elif c == 346: #F7
            self.OnToolStop(evt)
        else:
            evt.Skip()

    def OnClose(self, evt):
        if self.is_closed:
            return
        if not self.CanClose():
            evt.Veto()
            return

        wx.GetApp().UnRegisterFrame(self)
        '''FAU 20201229: Need to stop the timer otherwise they could call back a routine that was destroyed and cause a segmentation fault on Mac'''
        self.play_timer.Stop()
        self.timer.Stop()
        '''FAU 20201228: TODO: is it really what we want to do when multiple window?'''
        if wx.TheClipboard.Open():
            wx.TheClipboard.Flush()  # the text on the clipboard should be available after the app has closed
            wx.TheClipboard.Close()

        self.music_update_thread.abort()
        if self.play_music_thread != None:
            self.play_music_thread.abort()
            self.play_music_thread = None
        if self.record_thread != None:
            self.record_thread.abort()
            self.record_thread = None

        self.svg_tunes.cleanup()
        self.midi_tunes.cleanup()
        self.settings['is_maximized'] = self.IsMaximized()
        self.Hide()
        self.Iconize(False)  # the x,y pos of the window is not properly saved if it's minimized
        self.save_settings()
        self.is_closed = True
        self.manager.UnInit()
        self.Destroy()

    def PlayMidi(self, remove_repeats=False):
        global execmessages # 1.3.6 [SS] 2014-11-11
        tune, abc = self.GetAbcToPlay()
        if not tune:
            return

        execmessages = u''
        if remove_repeats or (len(self.selected_note_indices) > 2):
            abc = abc.replace('|:', '').replace(':|', '').replace('::', '')
            execmessages += '\n*removing repeats*'

        tempo_multiplier = self.get_tempo_multiplier()

        follow_score = not self.settings['midiplayer_path']
        # 1.3.6 [SS] 2014-11-15 2014-12-08
        self.current_midi_tune = AbcToMidi(abc, tune.header, self.cache_dir, self.settings, self.statusbar, tempo_multiplier, \
            add_follow_score_markers=follow_score)
        self.applied_tempo_multiplier = tempo_multiplier
        # 1.3.7 [SS] 2016-01-05 in case abc2midi crashes
        midi_file = None
        if self.current_midi_tune:
            self.midi_tunes.add(self.current_midi_tune)
            midi_file = self.current_midi_tune.midi_file

        if midi_file:
            # p09 an option in case you have trouble playing midi files.
            if self.settings['midiplayer_path']:
                execmessages += '\ncalling ' + self.settings['midiplayer_path'] #1.3.6 [SS]
                self.start_midi_out(midi_file)
            else:
                self.played_notes_timeline = None
                self.started_playing = False
                if self.settings.get('follow_score', False):
                    try:
                        self.played_notes_timeline = self.extract_note_timings(self.current_midi_tune, self.current_svg_tune)
                    except Exception as e:
                        error_msg = traceback.format_exc()
                        execmessages += error_msg
                self.do_load_media_file(midi_file)

    def extract_note_timings(self, midi_tune, svg_tune):
        midi2abc_path = self.settings['midi2abc_path']
        if not svg_tune or not midi2abc_path or svg_tune.abc_tune.x_number != midi_tune.abc_tune.x_number:
            return []

        page_count = svg_tune.page_count
        if page_count == 0:
            return []

        lines = get_midi_structure_as_text(midi2abc_path, midi_tune.midi_file).splitlines()
        if not lines:
            return []

        pages = [svg_tune.render_page(p, self.renderer) for p in range(page_count)]
        page_index = 0
        page = pages[page_index]

        svg_rows = svg_tune.abc_tune.note_line_indices
        midi_rows = midi_tune.abc_tune.note_line_indices

        midi_lines = midi_tune.abc_tune.abc_lines
        svg_lines = svg_tune.abc_tune.abc_lines

        midi_col_to_svg_col = midi_tune.abc_tune.midi_col_to_svg_col

        if len(midi_rows) > len(svg_rows):
            # compensate for added lines for count-in
            svg_rows = list(svg_rows)
            for i in range(len(midi_rows)):
                if midi_lines[midi_rows[i]].strip() != svg_lines[svg_rows[i]].strip():
                    svg_rows.insert(i, -1)
                if len(svg_rows) > len(midi_rows):
                    return []  # out of sync

        if len(midi_rows) != len(svg_rows):
            return []  # out of sync

        svg_rows = [i + 1 for i in svg_rows]
        midi_rows = [i + 1 for i in midi_rows]

        errors = defaultdict(lambda: defaultdict(int))
        #FAU: jwdj/EasyABC#99 Starting from commit sshlien/abcmidi@705d9e1f737a2db9fdc615b622bc75204b1bcbee of midi2abc, Follow_score not working
        #FAU: This commit of midi2abc changed the format of CntlParm.
        #FAU: it used to be printf("CntlParm %2d %s = %d\n",chan+1, ctype[control],value);
        #FAU: it is now printf("CntlParm %2d %s = %d %d\n",chan+1, ctype[control],control,value);
        #FAU: Following regex is expecting only one decimal however an extra one is now present
        #FAU: To have a regex working for both version, \s*\d* is added
        #FAU: might need some further check
        #pos_re = re.compile(r'^\s*(\d+\.\d+)\s+CntlParm\s+1\s+unknown\s+=\s+(\d+)')
        pos_re = re.compile(r'^\s*(\d+\.\d+)\s+CntlParm\s+1\s+unknown\s+=\s*\d*\s+(\d+)')
        note_re = re.compile(r'^\s*(\d+\.\d+)\s+Note (on|off)\s+(\d+)\s+(\d+)')
        tempo_re = re.compile(r'^\s*(\d+\.\d+)\s+Metatext\s+tempo\s+=\s+(\d+\.\d+)\s+bpm')
        new_track_re = re.compile(r'^Track \d+ contains')

        def timediff_in_seconds(first, last, bpm):
            return (last - first) * 60 / bpm

        def time_value_to_milliseconds(value, tempos):
            tempos = [t for t in tempos if t[0] <= value]
            time_start, bpm, sec_until_time_start = tempos[-1]
            sec = sec_until_time_start + timediff_in_seconds(time_start, value, bpm)
            return int(sec * 1000)

        def append_tempo(tempos, time_start, tempo):
            sec_until_time_start = 0.0
            if tempos:
                later_start = [t for t in tempos if t[0] > time_start]
                if later_start:
                    raise Exception('Cannot insert tempo at {0}'.format(time_start))
                prev_start, prev_bpm, prev_sec_until_time_start = tempos[-1]
                sec_until_time_start = prev_sec_until_time_start + timediff_in_seconds(prev_start, time_start, prev_bpm)
            tempos.append((time_start, tempo, sec_until_time_start))

        ticks_per_quarter = 480
        tempos = []
        notes = []
        svg_row = None
        row_col_midi_notes = defaultdict(lambda: defaultdict(int))
        last_line_was_pos = False
        for line in lines:
            m = new_track_re.match(line)
            if m is not None:
                page_index = 0
                page = pages[page_index]
                active_notes = {}
                indices = set()
                continue

            m = pos_re.match(line)
            if m is not None:
                value = int(m.group(2))
                if not last_line_was_pos:
                    note_info = [value]
                    indices = set()
                    last_line_was_pos = True
                else:
                    note_info.append(value)
                    if len(note_info) == 5:
                        row = (note_info[0] << 14) + (note_info[1] << 7) + note_info[2]
                        col = (note_info[3] << 7) + note_info[4]

                        row_col_midi_notes[row][col] += 1
                        svg_row = svg_rows[midi_rows.index(row)]
                        svg_col = midi_col_to_svg_col(row, col)
                        if svg_col is not None:
                            for i in range(page_count):
                                indices = page.get_indices_for_row_col(svg_row, svg_col)
                                if indices:
                                    break
                                # wrong page perhaps
                                page_index += 1
                                page_index %= page_count
                                page = pages[page_index]

                            if not indices:
                                errors[row][col] += 1
            else:
                last_line_was_pos = False
                m = note_re.match(line)
                if m is not None:
                    time_value = float(m.group(1))
                    if self.mc.unit_is_midi_tick:
                        converted_time = time_value * ticks_per_quarter
                    else:
                        converted_time = time_value_to_milliseconds(time_value, tempos)

                    on_off = m.group(2)
                    channel = int(m.group(3))
                    note_num = int(m.group(4))
                    if on_off == 'on':
                        note_start = converted_time
                        active_notes[(channel, note_num)] = MidiNote(note_start, None, indices, page_index, svg_row or 0)
                    elif on_off == 'off':
                        note_stop = converted_time
                        note_on = active_notes.pop((channel, note_num), None)
                        if note_on is not None:
                            if page_index == note_on.page:
                                notes.append(MidiNote(note_on.start, note_stop, indices.union(note_on.indices), page_index, svg_row or 0))
                            else:
                                notes.append(MidiNote(note_on.start, note_stop, note_on.indices, note_on.page, note_on.svg_row))
                elif not self.mc.unit_is_midi_tick:
                    m = tempo_re.match(line)
                    if m is not None:
                        tempo_start = float(m.group(1))
                        tempo = float(m.group(2))
                        append_tempo(tempos, tempo_start, tempo)

        row_col_svg_notes = defaultdict(lambda: defaultdict(int))
        for page in pages:
            for row, col in page.notes_row_col:
                row_col_svg_notes[row][col+1] += 1  # svg column is zero based so add one to make it 1-based

        lines = []

        rows = list(errors)
        rows.sort()
        for row in rows:
            svg_row = svg_rows[midi_rows.index(row)]
            svg_cols = list(row_col_svg_notes[svg_row])
            if errors[row]:
                if svg_cols:
                    lines.append('Synchronization error in row {0} (SVG row {1}):'.format(row, svg_row))
                    cols = list(errors[row])
                    cols.sort()
                    prev_col = 0
                    line_parts = []
                    for col in cols:
                        line_parts.append(' ' * (col - prev_col - 1))
                        n = errors[row][col]
                        if n > 0:
                            line_parts.append('!')
                        prev_col = col
                    if svg_row > 1:
                        # output previous abc line from svg
                        lines.append(u'SVG{0:03d}:{1}'.format(svg_row-1, svg_lines[svg_row-2]))

                    lines.append(u'Errors:{0}'.format(''.join(line_parts)))
                else:
                    lines.append('Synchronization error in row {0} (SVG row {1} does not contain displayed notes)'.format(row, svg_row))

            if svg_cols:
                # output abc line from svg
                svg_line = svg_lines[svg_row-1]
                lines.append(u'SVG{0:03d}:{1}'.format(svg_row, svg_line))
                decoded_svg_line = abc_text_to_unicode(svg_line).encode('utf-8').decode('ascii', 'replace').replace('\uFFFD', '?')
                if decoded_svg_line != svg_line:
                    lines.append(u'SVG{0:03d}:{1}'.format(svg_row, decoded_svg_line))

                # mark the svg-notes
                svg_cols.sort()
                prev_col = 0
                line_parts = []
                for col in svg_cols:
                    line_parts.append(' ' * (col - prev_col - 1))
                    n = row_col_svg_notes[svg_row][col]
                    if n == 1:
                        line_parts.append('^')
                    elif 0 <= n <= 9:
                        line_parts.append('%d' % n)
                    else:
                        line_parts.append('*')
                    prev_col = col
                lines.append(u'SVG{0:03d}:{1}'.format(svg_row, ''.join(line_parts)))

                # output abc line from midi
                line = midi_lines[row-1]
                lines.append(u'MID{0:03d}:{1}'.format(row, line))

                # mark the midi-notes
                cols = list(row_col_midi_notes[row])
                cols.sort()
                prev_col = 0
                line_parts = []
                for col in cols:
                    line_parts.append(' ' * (col - prev_col - 1))
                    n = row_col_midi_notes[row][col]
                    if n == 1:
                        line_parts.append('^')
                    elif 0 <= n <= 9:
                        line_parts.append('%d' % n)
                    else:
                        line_parts.append('*')
                    prev_col = col
                lines.append(u'MID{0:03d}:{1}'.format(row, ''.join(line_parts)))
                lines.append('')

        if lines:
            global execmessages
            execmessages += '\n\n=== follow score ===\n\n'
            execmessages += os.linesep.join(lines)

        return self.group_notes_by_time(notes)

    def fill_time_gaps(self, time_slices):
        gaps = []
        last_stop = 0
        for time_slice in time_slices:
            if time_slice.start > last_stop:
                gaps.append(MidiNote(last_stop, time_slice.start, set(), time_slice.page, time_slice.svg_row))
            last_stop = time_slice.stop

        if gaps:
            time_slices += gaps
            time_slices.sort(key=lambda n: n.start)

        time_slices.insert(0, MidiNote(-max_int, 0, set(), 0, 0))
        last_page = time_slices[-1].page
        svg_row = time_slices[-1].svg_row
        time_slices.append(MidiNote(last_stop, max_int, set(), last_page, svg_row))
        return time_slices

    def group_notes_by_time(self, notes):
        takewhile = itertools.takewhile
        notes.sort(key=lambda n: n.start)
        time_slices = []
        active_notes = []
        time_stop = max_int
        page = 0
        while notes or active_notes:
            time_start = notes[0].start if notes else max_int
            if time_start <= time_stop:
                same_note_start = list(takewhile(lambda n: n.start == time_start, notes))
                notes = notes[len(same_note_start):]
                active_notes += same_note_start
                active_notes.sort(key=lambda n: n.stop)
                time_stop = min(active_notes[0].stop if active_notes else max_int, notes[0].start if notes else max_int)
            else:
                # a note stops before the next note starts
                time_start, time_stop = time_stop, time_start
                time_stop = min(time_stop, active_notes[0].stop if active_notes else max_int)

            # adding a new slice
            if active_notes:
                page = max([n.page for n in active_notes])
                active_notes = [n for n in active_notes if n.page == page] # prevent mingling of indices from different pages

            all_indices_for_time_slice = set().union(*[n.indices for n in active_notes])
            svg_row = min([n.svg_row for n in active_notes]) if active_notes else 0
            time_slices.append(MidiNote(time_start, time_stop, all_indices_for_time_slice, page, svg_row))

            # removing stopped notes
            stopped_notes = list(takewhile(lambda n: n.stop <= time_stop, active_notes))
            active_notes = active_notes[len(stopped_notes):]

        return self.fill_time_gaps(time_slices)

    def GetTextPositionOfTune(self, tune_index):
        position = self.editor.FindText(0, self.editor.GetTextLength(), 'X:%s' % tune_index, 0)
        if position == -1:
            position = self.editor.FindText(0, self.editor.GetTextLength(), 'X: %s' % tune_index, 0)
        return position

    def OnTuneListClick(self, evt):
        self.tune_list.SetFocus()
        evt.Skip()

    def SetErrorMessage(self, error_msg):
        old_err = self.error_msg.GetValue()
        self.error_msg.SetValue(error_msg)
        pane = self.manager.GetPane('error message')

        if old_err and not error_msg:
            # 1.3.7 [JWdJ] 2016-01-06
            self.error_msg.Hide()
            if pane.IsOk():
                self.manager.DetachPane(pane)
                pane.Hide()
            self.manager.Update()
        elif not old_err and error_msg:
            # 1.3.7 [JWdJ] 2016-01-06
            if not self.error_pane.IsOk():
                self.manager.AddPane(self.error_msg, self.error_pane)
                pane = self.manager.GetPane('error message')
            pane.Show()
            self.error_msg.Show()
            self.manager.Update()
            self.editor.ScrollToLine(self.editor.LineFromPosition(self.editor.GetCurrentPos()))

    def OnPageSelected(self, evt):
        self.select_page(self.cur_page_combo.GetSelection())
        self.editor.SetFocus()

    def select_page(self, page_index):
        self.current_page_index = page_index
        self.UpdateMusicPane()

    def UpdateMusicPane(self):
        pages = self.current_svg_tune.page_count
        # 1.3.6.2 [JWdJ] 2015-02
        if self.cur_page_combo.GetCount() != pages:
            # update page selection combo box
            sel = self.current_page_index
            self.cur_page_combo.Clear()
            for page in range(1, pages + 1):
                self.cur_page_combo.Append('%d / %d' % (page, pages))
            if not (sel < self.cur_page_combo.GetCount()):
                sel = 0
            self.current_page_index = sel

            # hide page controls if there are less than 2 pages
            # 1.3.6.2 [JWdJ] 2015-02
            self.cur_page_combo.Parent.Show(pages > 1)
            if wx.Platform != "__WXMSW__":
                self.toolbar.Realize() # 1.3.6.4 [JWDJ] fixes toolbar repaint bug on Windows

        # 1.3.6.2 [JWdJ] 2015-02
        try:
            page = self.current_svg_tune.render_page(self.current_page_index, self.renderer)
            self.music_pane.set_page(page)
            #FAU 20250128: rebuild highlight based on position in editor
            #              ScrollMusicPaneToMatchEditor is called without requesting to go to closest page
            page.clear_note_selection()
            self.ScrollMusicPaneToMatchEditor(select_closest_note=True, select_closest_page=False)
            self.update_statusbar_and_messages()
        except Exception as e:
            error_msg = traceback.format_exc()
            wx.CallLater(600, self.SetErrorMessage, u'Internal error when drawing svg: %s' % error_msg)
            self.music_pane.clear()

    # 1.3.6.2 [JWdJ] 2015-02
    def OnMusicUpdateDone(self, evt): # MusicUpdateDoneEvent
        # MusicUpdateThread.run posts an event MusicUpdateDoneEvent with the svg_files
        tune = evt.GetValue()
        same_tune = tune.is_equal(self.current_svg_tune)
        self.current_svg_tune = tune
        if not same_tune:
            self.music_and_score_out_of_sync()
            self.current_page_index = 0 # 1.3.7.2 [JWDJ] always go to first page after switching tunes

        self.svg_tunes.add(tune) # 1.3.6.3 [JWDJ] for proper disposable of svg files
        self.UpdateMusicPane()

    def GetTextRangeOfTune(self, offset):
        position = offset
        editor = self.editor
        start_line = editor.LineFromPosition(position)
        line_count = editor.GetLineCount()
        get_line = editor.GetLine
        end_line = start_line + 1
        while end_line < line_count and not get_line(end_line).startswith('X:'):
            end_line += 1
        end_position = editor.PositionFromLine(end_line)
        return (position, end_position)

    def GetFileHeaderBlock(self):
        if self.settings.get('abc_include_file_header', True):
            # collect all header lines
            lines = []
            # 1.3.6.4 [SS] 2015-09-07
            getall = False
            get_line = self.editor.GetLine
            for i in xrange(self.editor.GetLineCount()):
                line = get_line(i)
                if line.startswith('X:') or line.startswith('T:'):
                    break
                elif re.match(r'%%beginps',line):
                    getall = True
                    lines.append(line)
                elif re.match(r'%%.*|[a-zA-Z_]:.*', line):
                    lines.append(line)
                elif getall:
                    lines.append(line)
                if re.match(r'%%endps',line):
                    getall = False
            abc = ''.join(lines)
            # remove certain fields that are probably only used for title fields
            abc = re.sub(r'(?ms)(^%%multicol start.*%%multicol end[ \t]*?[\r\n]+)', '', abc)
            abc = re.sub(r'(?ms)(^%%begintext.*%%endtext.*?[\r\n]+)', '', abc)
            abc = re.sub(r'(?m)(^%%(EPS|text|multicol|center|sep|vskip|newpage).*[\r\n]*)', '', abc)

            num_header_lines = len(line_end_re.findall(abc))

            return (abc, num_header_lines)
        else:
            return ('', 0)

    def GetSelectedTune(self, add_file_header=True):
        selItem = self.tune_list.GetFirstSelected()
        if selItem >= 0:
            return self.GetTune(selItem, add_file_header)
        elif self.tune_list.ItemCount > 0:
            return self.GetTune(0, add_file_header)
        else:
            return None

    def selected_tune_iterator(self):
        i = self.tune_list.GetFirstSelected()
        if i >= 0:
            while i >= 0:
                yield i
                i = self.tune_list.GetNextSelected(i)
        elif self.tune_list.ItemCount > 0:
            yield 0

    def GetSelectedTunes(self, add_file_header=True):
        return [self.GetTune(i, add_file_header) for i in self.selected_tune_iterator()]

    def GetTune(self, listbox_index, add_file_header=True):
        index = self.tune_list.GetItemData(listbox_index)  # remap index in case items are sorted
        if index in self.tune_list.itemDataMap:
            (xnum, title, line_no) = self.tune_list.itemDataMap[index]
            offset_start = self.editor.PositionFromLine(line_no)
            offset_start, offset_end = self.GetTextRangeOfTune(offset_start)
            if add_file_header:
                header, num_header_lines = self.GetFileHeaderBlock()
            else:
                header, num_header_lines = '', 0
            abc = self.editor.GetTextRange(offset_start, offset_end)
            return Tune(xnum, title, '', offset_start, offset_end, abc, header, num_header_lines)
        else:
            return None

    def OnTuneDoubleClicked(self, evt):
        self.OnToolStop(evt)
        self.OnToolPlay(evt)
        evt.Skip()

    def update_multi_tunes_menu_items(self):
        selected = self.tune_list.GetFirstSelected()
        multi_select = selected >= 0 and self.tune_list.GetNextSelected(selected) >= 0

        for menu_item in self.multi_tunes_menu_items:
            menu_item.Enable(multi_select)

    def OnTuneDeselected(self, evt):
        selected = self.tune_list.GetFirstSelected()
        if selected >= 0 and self.tune_list.GetNextSelected(selected) < 0:
            self.OnTuneSelected(evt)
        self.update_multi_tunes_menu_items()

    def OnTuneSelected(self, evt):
        global execmessages # [SS] 1.3.6 2014-11-11

        # 1.3.6.4 [SS] 2015-06-11 -- to maintain consistency for different media players
        # self.reset_BpmSlider()

        dt = datetime.now() - self.execmessage_time # 1.3.6 [SS] 2014-12-11
        dtime = dt.seconds*1000 + dt.microseconds // 1000
        if evt is not None and dtime > 20000:
            execmessages = u''
        self.selected_tune = None
        self.update_multi_tunes_menu_items()

        tune = self.GetSelectedTune()
        if tune:
            self.music_update_thread.ConvertAbcToSvg(tune.abc, tune.header)
            if evt and (wx.Window.FindFocus() != self.editor and not (self.find_dialog and self.find_dialog.IsActive() or self.replace_dialog and self.replace_dialog.IsActive())):
                # 1.3.6.2 [JWdJ] 2015-02
                self.music_pane.current_page.clear_note_selection()
                self.selected_note_descs = []

                # HideLines() does not work correctly on either Windows
                # or Linux. The goal was to display only the selected
                # tune in the edit window using documented options
                # in the wxpython StyledTextCtrl widget. [SS] 2014-9-18
                #lastline = self.editor.LineFromPosition(tune.offset_end)
                #firstline = self.editor.LineFromPosition(tune.offset_start)
                #print 'from ',firstline,' to ',lastline
                #self.editor.HideLines(1,firstline)

                self.editor.SetSelection(tune.offset_start, tune.offset_start)
                self.editor.ScrollToLine(self.editor.LineFromPosition(tune.offset_start))
                self.music_pane.Scroll(0, 0)

                self.error_pane = self.manager.GetPane('error message').Hide()
                self.manager.Update()

    def UpdateTuneListAndReselectTune(self):
        self.UpdateTuneList(reselect_tune=True)

    def UpdateTuneList(self, reselect_tune=False):
        tune_list = self.tune_list
        selected_tune_index = None
        if reselect_tune:
            first_selected = tune_list.GetFirstSelected()
            if first_selected > 0:
                selected_tune_index = tune_list.GetItemData(tune_list.GetFirstSelected())
        tunes = self.GetTunes()
        tune_list.itemDataMap = dict(enumerate(tunes))

        different = (len(tunes) != len(self.tunes))
        if not different:
            for tune1, tune2 in zip(tunes, self.tunes):
                different = different or (tune1[:-1] != tune2[:-1])    # compare xnum, title but not line_no
        if different:
            top_item = tune_list.GetTopItem()
            tune_list.Freeze()
            tune_list.DeleteAllItems()
            set_item = tune_list.SetStringItem
            insert_item = tune_list.InsertStringItem
            set_item_data = tune_list.SetItemData
            get_item_count = tune_list.GetItemCount
            if WX4:
                insert_item = tune_list.InsertItem
                set_item = tune_list.SetItem
            for xnum, title, line_no in tunes:
                index = insert_item(get_item_count(), str(xnum))
                set_item(index, 1, title)
                set_item_data(index, index)

            last_index = get_item_count() - 1
            if selected_tune_index is not None and selected_tune_index <= last_index:
                tune_list.Select(selected_tune_index)

            # try to restore scroll state
            if tunes and top_item >= 0:
                last_visible_index = top_item + tune_list.GetCountPerPage() - 1
                if last_visible_index > last_index:
                    last_visible_index = last_index
                tune_list.EnsureVisible(last_visible_index)

            tune_list.Thaw()

        self.tunes = tunes

        self.SelectOnlyTuneIfTuneNotSelected()


    def OnTimer(self, evt):
        self.SelectOnlyTuneIfTuneNotSelected()

    def SelectOnlyTuneIfTuneNotSelected(self):
        if len(self.tunes) == 1 and self.tune_list.GetFirstSelected() == -1:
            self.tune_list.Select(0)
            self.OnTuneSelected(None)

    def GetTunes(self):
        editor = self.editor
        pos_from_line = editor.PositionFromLine
        get_text_range = editor.GetTextRange
        get_line = editor.GetLine
        search_tune_index = tune_index_re.search
        cur_index = None
        cur_startline = None
        cur_title = u''
        titles_found = 0
        tunes = []
        tunes_append = tunes.append
        n = editor.GetLineCount()
        for i in xrange(n):
            p = pos_from_line(i)
            try:
                t = get_text_range(p, p+2)
            except:
                t = ''
            if t == 'X:':
                if cur_index is not None:
                    tunes_append((cur_index, cur_title, cur_startline))
                    cur_index = None
                m = search_tune_index(get_line(i))
                if m:
                    cur_index = int(m.group(1))
                    cur_startline = i
                cur_title = u''
                titles_found = 0
            elif t == 'T:' and titles_found < 2 and cur_index is not None:
                title = decode_abc(strip_comments(get_line(i)[2:]).strip())
                cur_title = ' - '.join(filter(None, (cur_title, title)))

        if cur_index is not None:
            tunes_append((cur_index, cur_title, cur_startline))
        return tunes

    def GetTuneAbc(self, startpos):
        editor = self.editor
        get_line = editor.GetLine
        first_line_no = editor.LineFromPosition(startpos)
        lines = []
        for line_no in range(first_line_no, editor.GetLineCount()):
            line = get_line(line_no)
            if line.startswith('X:'):
                break
            lines.append(line)
        return ''.join(lines)

    def InitEditor(self, font_face=None, font_size=None):
        editor = self.editor
        editor.ClearDocumentStyle()
        editor.StyleClearAll()
        editor.SetLexer(stc.STC_LEX_CONTAINER)
        editor.SetProperty("fold", "0")
        editor.SetUseTabs(False)
        if not WX4:
            editor.SetUseAntiAliasing(True)

        if not font_face:
            fixedWidthFonts = ['Bitstream Vera Sans Mono', 'Courier New', 'Courier']
            #fixedWidthFonts = ['Lucida Grande', 'Monaco' 'Inconsolata', 'Consolas', 'Deja Vu Sans Mono', 'Droid Sans Mono', 'Courier', 'Andale Mono', 'Monaco', 'Courier New', 'Courier']
            wantFonts = fixedWidthFonts[:]
            size = 16
            if wx.Platform == "__WXMSW__":
                size = 10
            if wx.Platform == "__WXGTK__":
                size = 12
            fonts = wx.FontEnumerator()
            fonts.EnumerateFacenames()
            font_names = fonts.GetFacenames()
            font = None
            while wantFonts:
                font = wantFonts.pop(0)
                if font in font_names:
                    break
        else:
            font = font_face
            size = font_size
        editor.SetFont(wx.Font(size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName=font))

        editor.SetProperty("fold", "0")
        set_style = editor.StyleSetSpec
        set_style(self.styler.STYLE_DEFAULT, "fore:%s,face:%s,size:%d" % (self.settings.get('style_default_color',default_style_color['style_default_color']), font, size))
        set_style(self.styler.STYLE_CHORD, "fore:%s,face:%s,size:%d" % (self.settings.get('style_chord_color',default_style_color['style_chord_color']), font, size))
        # Comments
        set_style(self.styler.STYLE_COMMENT_NORMAL, "fore:%s,face:%s,italic,size:%d" % (self.settings.get('style_comment_color',default_style_color['style_comment_color']), font, size))
        set_style(self.styler.STYLE_COMMENT_SPECIAL, "fore:%s,face:%s,italic,size:%d" % (self.settings.get('style_specialcomment_color',default_style_color['style_specialcomment_color']), font, size))
        # Bar
        set_style(self.styler.STYLE_BAR, "fore:%s,face:%s,bold,size:%d" % (self.settings.get('style_bar_color',default_style_color['style_bar_color']), font, size))
        # Field
        set_style(self.styler.STYLE_FIELD,                "fore:%s,face:%s,bold,size:%d" % (self.settings.get('style_field_color',default_style_color['style_field_color']), font, size))
        set_style(self.styler.STYLE_FIELD_VALUE,          "fore:%s,face:%s,italic,size:%d" % (self.settings.get('style_fieldvalue_color',default_style_color['style_fieldvalue_color']), font, size))
        set_style(self.styler.STYLE_EMBEDDED_FIELD,       "fore:%s,face:%s,bold,size:%d" % (self.settings.get('style_embeddedfield_color',default_style_color['style_embeddedfield_color']), font, size))
        set_style(self.styler.STYLE_EMBEDDED_FIELD_VALUE, "fore:%s,face:%s,italic,size:%d" % (self.settings.get('style_embeddedfieldvalue_color',default_style_color['style_embeddedfieldvalue_color']), font, size))
        set_style(self.styler.STYLE_FIELD_INDEX,          "fore:%s,face:%s,bold,underline,size:%d" % (self.settings.get('style_fieldindex_color',default_style_color['style_fieldindex_color']), font, size))
        # Single quoted string
        set_style(self.styler.STYLE_STRING, "fore:%s,face:%s,italic,size:%d" % (self.settings.get('style_string_color',default_style_color['style_string_color']), font, size))
        # Lyrics
        set_style(self.styler.STYLE_LYRICS, "fore:%s,face:%s,italic,size:%d" % (self.settings.get('style_lyrics_color',default_style_color['style_lyrics_color']), font, size))

        set_style(self.styler.STYLE_GRACE, "fore:%s,face:%s,italic,size:%d" % (self.settings.get('style_grace_color',default_style_color['style_grace_color']), font, size))

        set_style(self.styler.STYLE_ORNAMENT, "fore:%s,face:%s,bold,size:%d" % (self.settings.get('style_ornament_color',default_style_color['style_ornament_color']), font, size))
        set_style(self.styler.STYLE_ORNAMENT_PLUS, "fore:%s,face:%s,size:%d" % (self.settings.get('style_ornamentplus_color',default_style_color['style_ornamentplus_color']), font, size))
        set_style(self.styler.STYLE_ORNAMENT_EXCL, "fore:%s,face:%s,size:%d" % (self.settings.get('style_ornamentexcl_color',default_style_color['style_ornamentexcl_color']), font, size))

        editor.SetModEventMask(wx.stc.STC_MODEVENTMASKALL & ~(wx.stc.STC_MOD_CHANGESTYLE | wx.stc.STC_PERFORMED_USER)) # [1.3.7.4] JWDJ: don't fire OnModified on style changes
        editor.Colourise(0, editor.GetLength())


    def OnDropFile(self, filename):
        global execmessages, visible_abc_code
        info_messages = []
        # [SS] 2014-12-18
        options = namedtuple ('Options', 'u m c d n b v x p j t v1 ped s stm')                     # emulate the options object
        options.m = 0; options.j = 0; options.p = []; options.b = 0; options.d = 0  # unused options
        options.n = 0; options.v = 0; options.u = 0; options.c = 0; options.x = 0   # but all may be used if needed
        options.t = 0; options.v1 = False; options.ped = True; options.s = 0; options.stm = 0
        if self.settings['xmlunfold']:
            options.u = 1
        if self.settings['xmlmidi']:
            options.m = 1
        if self.settings['xml_v'] != 0:
            options.v = int(self.settings['xml_v'])
        if self.settings['xml_n'] != 0:
            options.n = int(self.settings['xml_n'])
        if self.settings['xml_b'] != 0:
            options.b = int(self.settings['xml_b'])
        if self.settings['xml_c'] != 0:
            options.c = int(self.settings['xml_c'])
        if self.settings['xml_d'] != 0:
            options.d = int(self.settings['xml_d'])
        # 1.3.6.1 [SS] 2015-01-08
        if self.settings['xml_p'] != '' and self.settings['xml_p'] != 0:
            p = self.settings['xml_p'].split(',')
            for elem in p:
                options.p.append(float(elem))

        try:
            extension = os.path.splitext(filename)[1].lower()
            p = self.editor.GetLength()
            self.editor.SetSelection(p, p)
            if extension in ('.xml', '.mxl', '.musicxml'):
                # 1.3.6 [SS] 2014-12-18
                self.AddTextWithUndo(u'\n%s\n' % xml_to_abc(filename,options,info_messages))
                execmessages = u'abc_to_xml '+ filename
                for infoline in info_messages:
                    execmessages += infoline
                return True
            if extension == '.nwc':
                try:
                    xml_file_path = NWCToXml(filename, self.cache_dir, self.settings.get('nwc2xml_path', None))
                    # 1.3.6 [SS] 2014-12-18
                    abc_code = xml_to_abc(xml_file_path,options,info_messages)
                    abc_code = fix_boxmarks_texts(abc_code)
                    abc_code = change_texts_into_chords(abc_code)
                # 1.3.6.2 [JWdJ] 2015-02
                except NWCConversionException as e:
                    dlg = wx.MessageDialog(self, unicode(e), _('nwc2xml error'), wx.OK | wx.CANCEL)
                    result = dlg.ShowModal()
                    dlg.Destroy()
                    if result == wx.ID_OK:
                        return True
                    else:
                        raise AbortException()
                self.AddTextWithUndo(u'\n%s\n' % abc_code)
                return True
            elif extension in ('.abc', '.txt', '.mcm', ''):
                self.editor.BeginUndoAction()
                self.editor.AddText('\n\n')
                self.editor.AddText(open(filename, 'r').read().strip())
                self.editor.AddText('\n\n')
                self.editor.EndUndoAction()
                return True
            elif extension in ('.mid', '.midi'):
                return self.handle_midi_conversion(filename=filename)
        except AbortException:
            raise
        except:
            error_msg = traceback.format_exc()
            dlg = wx.MessageDialog(self, error_msg, _('Error'), wx.OK | wx.CANCEL)
            dlg.ShowModal()
            dlg.Destroy()
            raise
        self.execmessage_time = datetime.now() # 1.3.6 [SS] 2014-12-11


    # 1.3.6.1 [SS] 2015-01-19
    # When AbcToSvg is called in a thread, we should not try to write to the EasyAbc frame
    # since there is a chance that the resource is already being used by the main program.
    # To prevent this, I have moved this code to a separate method.
    def update_statusbar_and_messages(self):
        # P09 2014-10-26 [SS]
        global execmessages, visible_abc_code
        MyInfoFrame.update_text() # 1.3.6.3 [JWDJ] 2015-04-27

        # 1.3.6 2014-12-16 [SS]
        MyAbcFrame.update_text() # 1.3.6.3 [JWDJ] 2015-04-27


        # 1.3.6.3 2015-03-15 [SS]
        if execmessages.find('Error') != -1 or execmessages.find('error') != -1:
            self.statusbar.SetStatusText(_('{0} reported some errors').format('Abcm2ps'))
        elif execmessages.find('Warning') != -1 or execmessages.find('warning') != -1:
            self.statusbar.SetStatusText(_('{0} reported some warnings').format('Abcm2ps'))
        else:
            self.statusbar.SetStatusText('')

    def handle_midi_conversion(self, filename=None, notes=None):
        global execmessages
        midi2abc_path = self.settings.get('midi2abc_path')
        if midi2abc_path and os.path.exists(midi2abc_path):
            cmd = [midi2abc_path, '-f', filename]
            execmessages += '\nMidiToAbc\n' + " ".join(cmd)
            stdout_value, stderr_value, returncode = get_output_from_process(cmd)
            execmessages += '\n' + stdout_value + stderr_value
            if returncode != 0:
                execmessages += '\n' + _('%(program)s exited abnormally (errorcode %(error)#8x)') % { 'program': 'MidiToAbc', 'error': returncode & 0xffffffff }
                return None
            if stdout_value:
                self.AddTextWithUndo('\n' + stdout_value + '\n')
        else:
            self.internal_midi_conversion(filename, notes)

    def internal_midi_conversion(self, filename=None, notes=None):
        metre1, metre2 = [int(x) for x in self.settings['record_metre'].split('/')]
        metre = Fraction(metre1, metre2)
        abcs = [midi_to_abc(filename=filename, notes=notes, metre=metre, default_len=df) for df in [Fraction(1,16), Fraction(1,8)]]
        abc = sorted(abcs, key=lambda x: len(x))[0]

        # default field values
        key = ''
        metre = ''
        default_len = ''
        title = _('Name of tune')

        # try to extract field values from abc code
        m = re.search('K: *(.*)', abc)
        if m:
            key = m.group(1)
        m = re.search('M: *(.*)', abc)
        if m:
            metre = m.group(1)
        m = re.search('L: *(.*)', abc)
        if m:
            default_len = m.group(1)
        if filename:
            title = os.path.splitext(os.path.basename(filename))[0].capitalize().replace('_', ' ')

        dlg = MidiOptionsFrame(self, key=key, metre=metre, default_len=str(default_len), title=title)
        try:
            result = dlg.ShowModal() == wx.ID_OK
            if result:
                abc = midi_to_abc(filename=filename, notes=notes,
                                             key=dlg.key.GetValue(),
                                             metre=str2fraction(dlg.metre.GetValue()),
                                             title=dlg.title.GetValue(),
                                             default_len=str2fraction(dlg.default_len.GetValue()),
                                             bars_per_line=int(dlg.bpl.GetValue()),
                                             anacrusis_notes=int(dlg.num_notes_in_anacrusis.GetValue()),
                                             no_triplets=not dlg.triplet_detection.GetValue(),
                                             no_broken_rythms=not dlg.broken_rythm_detection.GetValue(),
                                             slur_8th_pairs=dlg.slur_8ths.GetValue(),
                                             slur_16th_pairs=dlg.slur_16ths.GetValue(),
                                             slur_triplets=dlg.slur_triplets.GetValue(),
                                             index=self.index)
                self.AddTextWithUndo('\n' + abc + '\n')
                self.index += 1
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window
        return result

    def OnReducedMargins(self, evt):
        self.settings['reduced_margins'] = self.mni_reduced_margins.IsChecked()
        self.refresh_tunes()

    def load_settings(self):
        try:
            settings = pickle.load(open(self.settings_file, 'rb'))
        except Exception:
            settings = {} # ignore non-existant settings file (it will be created when the program exits)
        self.settings.update(settings)
        return self.settings

    def load_and_apply_settings(self, load_window_size_pos=False, load_perspective=True):
        settings = self.load_settings()

        self.editor.SetZoom(settings.get('zoom', 0))
        if load_window_size_pos:
            # 1.3.6.3 [JWDJ] 2015-04-25 # sometimes window was unreachable because window_x and window_y set to -32000
            window_x = max(settings.get('window_x', 40), 0)
            window_y = max(settings.get('window_y', 40), 0)
            window_width = max(settings.get('window_width', 1000), 600)
            window_height = max(settings.get('window_height', 800), 400)
            dimensions = window_x, window_y, window_width, window_height
            if WX4:
                self.SetSize(*dimensions)
            else:
                self.SetDimensions(*dimensions)
        if load_perspective:
            perspective = settings.get('perspective')
            # 1.3.6.3 [JWDJ] 2015-04-14 only load perspective if there is any.
            if perspective:
                self.manager.LoadPerspective(perspective)
        self.bpm_slider.SetValue(0)
        self.zoom_slider.SetValue(settings.get('score_zoom', 1000))
        self.author = settings.get('author', '')
        self.mni_auto_refresh.Check(settings.get('auto_refresh', True))
        self.mni_reduced_margins.Check(settings.get('reduced_margins', True))
        self.mni_TA_active.Check(settings.get('typing_assistance_active', True))
        self.mni_TA_auto_case.Check(settings.get('typing_assistance_auto_case', False))
        self.mni_TA_do_re_mi.Check(settings.get('typing_assistance_do_re_mi', False))
        self.mni_TA_add_note_durations.Check(settings.get('typing_assistance_add_note_durations', False))
        self.mni_TA_add_bar.Check(settings.get('typing_assistance_add_bar', False))
        self.mni_TA_add_bar_auto.Check(settings.get('typing_assistance_add_bar_auto', True))
        self.mni_TA_add_right.Check(settings.get('typing_assistance_add_right', True))
        self.OnZoomSlider(None)
        self.Update()
        self.Refresh()
        self.Maximize(settings.get('is_maximized', False))

        self.update_recent_files_menu()

        for i, width in enumerate(self.settings.get('tune_col_widths', [37, 100])):
            self.tune_list.SetColumnWidth(i, width)

        self.settings['record_bpm'] = self.settings.get('record_bpm', 70)
        item = self.bpm_menu.FindItemById(self.bpm_menu.FindItem(str(self.settings['record_bpm'])))
        item.Check()

        self.settings['record_metre'] = self.settings.get('record_metre', '3/4')
        item = self.metre_menu.FindItemById(self.metre_menu.FindItem(self.settings['record_metre']))
        item.Check()

        # reset captions since this is ruined by LoadPerspective
        self.manager.GetPane('abc editor').Caption(_("ABC code"))
        self.manager.GetPane('tune list').Caption(_("Tune list"))
        self.manager.GetPane('tune preview').Caption(_("Musical score"))
        self.manager.GetPane('error message').Caption(_("ABC errors")).Hide()
        self.manager.GetPane('abcassist').Caption(_("ABC assist")) # 1.3.6.3 [JWDJ] 2015-04-21 added ABC assist
        self.manager.Update()
        self.music_pane.reset_scrolling()

    def get_tempo_multiplier(self):
        return 2.0 ** (float(self.bpm_slider.GetValue()) / 100)

    def save_settings(self):
        settings = self.settings
        settings['zoom'] = self.editor.GetZoom()
        settings['window_x'], settings['window_y'] = self.Position
        settings['window_width'], settings['window_height'] = self.Size
        settings['perspective'] = self.manager.SavePerspective()
        settings['author'] = self.author
        settings['tempo'] = int(100.0 * self.get_tempo_multiplier()) # 1.3.6.4 [JWDJ] not really necessary since setting 'tempo' is not used anymore
        settings['score_zoom'] = self.zoom_slider.GetValue()
        settings['auto_refresh'] = self.mni_auto_refresh.IsChecked()
        settings['reduced_margins'] = self.mni_reduced_margins.IsChecked()
        settings['typing_assistance_active'] = self.mni_TA_active.IsChecked()
        settings['typing_assistance_auto_case'] = self.mni_TA_auto_case.IsChecked()
        settings['typing_assistance_do_re_mi'] = self.mni_TA_do_re_mi.IsChecked()
        settings['typing_assistance_add_note_durations'] = self.mni_TA_add_note_durations.IsChecked()
        settings['typing_assistance_add_bar'] = self.mni_TA_add_bar.IsChecked()
        settings['typing_assistance_add_bar_auto'] = self.mni_TA_add_bar_auto.IsChecked()
        settings['typing_assistance_add_right'] = self.mni_TA_add_right.IsChecked()
        self.settings['tune_col_widths'] = [self.tune_list.GetColumnWidth(i) for i in range(self.tune_list.GetColumnCount())]

        try:
            pickle.dump(settings, open(self.settings_file, 'wb'))
        except IOError:
            pass


    # p09 This is a new function which verifies that the critical abcmidi
    # support functions are available. It also attempts to find the paths
    # to ghostscript if it is installed.  2014-10-14 [SS]
    def restore_settings(self):
        settings = self.settings

        abcm2ps_path = settings.get('abcm2ps_path')

        if not abcm2ps_path or not os.path.exists(abcm2ps_path):
            abcm2ps_path = get_default_path_for_executable('abcm2ps')

        if os.path.exists(abcm2ps_path):
            settings['abcm2ps_path'] = abcm2ps_path # 1.3.6 [SS] 2014-11-12
        else:
            dlg = wx.MessageDialog(self, _('abcm2ps was not found here. You need it to view the music. Go to settings and indicate the path.'), _('Warning'), wx.OK)
            dlg.ShowModal()

        abc2midi_path = settings.get('abc2midi_path', '')

        if not abc2midi_path or not os.path.exists(abc2midi_path):
            abc2midi_path = get_default_path_for_executable('abc2midi')

        if os.path.exists(abc2midi_path):
            settings['abc2midi_path'] = abc2midi_path # 1.3.6 [SS] 2014-11-12
        else:
            dlg = wx.MessageDialog(self, _('abc2midi was not found here. You need it to play the music. Go to settings and indicate the path.'), _('Warning'), wx.OK)
            dlg.ShowModal()

        midi2abc_path = settings.get('midi2abc_path')

        #1.3.6.4 [SS] 2015-06-22
        if not midi2abc_path or not os.path.exists(midi2abc_path):
            midi2abc_path = get_default_path_for_executable('midi2abc')

        if os.path.exists(midi2abc_path):
            settings['midi2abc_path'] = midi2abc_path
        else:
            dlg = wx.MessageDialog(self, _('midi2abc was not found here. You need it to play the music. Go to settings and indicate the path.'), _('Warning'), wx.OK)
            dlg.ShowModal()

        abc2abc_path = settings.get('abc2abc_path')

        if not abc2abc_path or not os.path.exists(abc2abc_path):
            abc2abc_path = get_default_path_for_executable('abc2abc')

        if os.path.exists(abc2abc_path):
            settings['abc2abc_path'] = abc2abc_path # 1.3.6 [SS] 2014-11-12
        else:
            # print('%s ***  not found ***' % abc2abc_path)
            dlg = wx.MessageDialog(self, _('abc2abc was not found here. You need it to transpose the music. Go to settings and indicate the path.'), _('Warning'), wx.OK)
            dlg.ShowModal()

        midiplayer_path = settings.get('midiplayer_path')
        if not midiplayer_path:
            settings['midiplayer_path'] = ''
        else:
            # 1.3.6.4 [SS] 2015-05-27
            if not os.path.exists(midiplayer_path):
                dlg = wx.MessageDialog(self, _('The midiplayer was not found. You will not be able to play the MIDI file.'), _('Warning'), wx.OK)
                dlg.ShowModal()

        gs_path = settings.get('gs_path')
        # 1.3.6.1 [SS] 2015-01-28

        if not gs_path:
            if wx.Platform == "__WXMSW__":
                gs_path = get_ghostscript_path()
                settings['gs_path'] = gs_path
            #FAU:PDF:pstopdf is not provided by Apple starting from MacOS Sonoma. So in any case look for ghostscript and use /usr/bin/pstopdf only if Mac OS version earlier than Sonoma.
            #elif wx.Platform == '__WXGTK__':
            else:
                try:
                    gs_path = subprocess.check_output(["which", "gs"])
                    settings['gs_path'] = gs_path[0:-1].decode()
                except:
                    if wx.Platform == "__WXMAC__" and int(platform.mac_ver()[0].split('.')[0]) <= 13:
                        settings['gs_path'] = '/usr/bin/pstopdf'
                    else:
                        settings['gs_path'] = ''
            #1.3.6.1 [SS] 2014-01-13
            #FAU:PDF:pstopdf is not provided by Apple starting from MacOS Sonoma. So merge with Ghostscript in case ghostscript is installed
            #elif wx.Platform == "__WXMAC__":
            #    gs_path = '/usr/bin/pstopdf'
            #    settings['gs_path'] = gs_path

        # 1.3.6.1 [SS] 2015-01-12 2015-01-22
        gs_path = settings['gs_path'] #eliminate trailing \n
        if gs_path and (os.path.exists(gs_path) == False):
            msg = _('The executable %s could not be found') % gs_path
            dlg = wx.MessageDialog(self, msg, _('Warning'), wx.OK)
            dlg.ShowModal()

        #Fix midi_program_ch settings - 1.3.5 to 1.3.6 compatibility 2014-11-14
        midi_program_ch_list = ['midi_program_ch%d' % ch for ch in range(1, 16 + 1)]
        for channel in range(16):
            if settings.get(midi_program_ch_list[channel]):
                pass
            else:
                settings[midi_program_ch_list[channel]] = [default_midi_instrument, default_midi_volume, default_midi_pan]

        #delete 'one_instrument_only'. It is no longer used. 1.3.6 [SS] 2014-11-20
        try:
            del self.settings['one_instrument_only']
        except:
            pass

        # 1.3.6 [SS] 2014-12-18
        new_settings = [('midi_program', default_midi_instrument), ('midi_chord_program', 24),
                        ('transposition',0), ('tuning',440),
                        ('nodynamics', False), ('nofermatas', False),
                        ('nograce', False), ('barfly', True),
                        ('searchfolder', self.app_dir), ('xmlcompressed', False),
                        ('xmlunfold', False), ('xmlmidi', False), ('xml_v','0'), ('xml_d', '0'),
                        ('xml_b','0'), ('xml_c', '0'), ('xml_n', '0'), ('xml_u', '0'),
                        ('xml_p', ''),
                        ('abcm2ps_number_bars', False), ('abcm2ps_no_lyrics', False),
                        ('abcm2ps_refnumbers', False), ('abcm2ps_ignore_ends', False),
                        ('abcm2ps_leftmargin', '1.78'), ('abcm2ps_rightmargin', '1.78'),
                        ('abcm2ps_topmargin', '1.00'), ('abcm2ps_botmargin', '1.00'),
                        ('abcm2ps_scale', '0.75'), ('abcm2ps_clean', False),
                        ('abcm2ps_defaults', True), ('abcm2ps_pagewidth', '21.59'),
                        ('abcm2ps_pageheight', '27.94'), ('midiplayer_parameters', ''),
                        ('bpmtempo', 120), ('chordvol', default_midi_volume), ('bassvol', default_midi_volume),
                        ('melodyvol', default_midi_volume), ('midi_intro', 0), ('version', program_version)
                       ]

        # 1.3.6 [SS] 2014-12-16
        for item in new_settings:
            term = item[0]
            value = item[1]
            if term in self.settings:
                pass
            else:
                self.settings[term] = value

        self.settings['gchord'] = 'default' # 1.3.6 [SS] 2014-11-26

    def update_recent_files_menu(self):
        if self.exclusive_file_mode:
            return
        recent_files = self.settings.get('recentfiles', '').split('|')
        while self.recent_menu.MenuItemCount > 0:
            delete_menuitem(self.recent_menu, self.recent_menu.FindItemByPosition(0))

        if len(recent_files) > 0:
            mru_index = 0
            recent_files_menu_id = 1100
            for path in recent_files:
                if path and os.path.exists(path):
                    append_menu_item(self.recent_menu, u'&{0}: {1}'.format(mru_index, path), path, self.on_recent_file, id=recent_files_menu_id)
                    recent_files_menu_id += 1
                    mru_index += 1

    def on_recent_file(self, event):
        menu = event.EventObject
        menu_item = menu.FindItemById(event.Id)
        path = menu_item.Help # 1.3.7.1 [JWDJ] sometimes wrong recent file was opened
        if not self.editor.GetModify() and not self.current_file:  # if a new unmodified document
            self.load(path)
        else:
            frame = self.OnNew()
            frame.load(path)


class MyFileDropTarget(wx.FileDropTarget):
    def __init__(self, frame):
        wx.FileDropTarget.__init__(self)
        self.frame = frame

    def OnDropFiles(self, x, y, filenames):
        frame = self.frame
        self.frame.Raise()

        # if it's just a single file and we don't have anything else loaded, just load the file normally
        if len(filenames) == 1 and not frame.editor.GetText().strip() and not frame.editor.GetModify() and not frame.current_file and os.path.splitext(filenames[0])[1].lower() in ['.txt', '.abc', '.mcm', '']:   # if a new unmodified document
            frame.load(filenames[0])
        else:
            try:
                try:
                    self.frame.editor.BeginUndoAction()
                    progress = ProgressFrame(self.frame, -1)
                    progress.Show(True)
                    for i, filename in enumerate(filenames):
                        if not self.frame.OnDropFile(filename):
                            break
                        progress.SetPercent(100 * (i+1) / len(filenames))
                finally:
                    self.frame.editor.EndUndoAction()
                    progress.Close()
            except AbortException:
                pass
            self.frame.UpdateTuneList()
            self.frame.tune_list.Select(self.frame.tune_list.GetItemCount()-1)
            self.frame.OnTuneSelected(None)

class AboutFrame(wx.Dialog):
    htmlpage = '''
<html>
<body bgcolor="#FAFAF0">
<center><img src="img/abclogo.png"/>
</center>
<p><b>{0}</b><br/>
an open source ABC editor for Windows, OSX and Linux. It is published under the <a href="https://www.gnu.org/licenses/gpl-2.0.html">GNU Public License</a>. </p>
<p><center>initial repository was at <a href="https://www.nilsliberg.se/ksp/easyabc/">https://www.nilsliberg.se/ksp/easyabc/</a></center></p>
<p><center>Now documentation available here<a href="https://easyabc.sourceforge.net">https://easyabc.sourceforge.net</a></center></p>
<p><u>Features</u>:</p>
<ul style="line-height: 150%; margin-top: 3px;">
  <li> Good ABC standard coverage thanks to internal use of abcm2ps and abc2midi
  <li> Syntax highlighting
  <li> Zoom support
  <li> Import MusicXML, MIDI and Noteworthy Composer files (the midi to abc translator is custom made in order to produce legible abc code with more sensible beams than the typical midi2abc output).
  <li> Export to MIDI, SVG, PDF (single tune or whole tune book).
  <li> Select notes by clicking on them and add music symbols by using drop-down menus in the toolbar.
  <li> Play the active tune as midi
  <li> Record songs from midi directly in the program (no OSX support at the moment).<br/>
  Just press Rec, play on your midi keyboard and then press Stop.
  <li> The musical score is automatically updated as you type in ABC code.
  <li> Support for unicode (utf-8) and other encodings.
  <li> Transpose and halve/double note length functionality (using abc2abc)
  <li> An abcm2ps format file can easily be specified in the settings.
  <li> ABC fields in the file header are applied to every single tune in a tune book.
  <li> Automatic alignment of bars on different lines
  <li> Available in <img src="img/new.gif"/>German, Dutch, Italian, French, Danish, Swedish, German and English</li>
  <li> Functions to generate incipits, sort tunes and renumber X: fields.</li>
  <li> Musical search function - search for note sequences irrespectively of key, etc. <img src="img/new.gif"/></li>
</ul>

<p><b>EasyABC</b> is brought to you by <b>Nils Liberg</b>, Copyright &copy; 2010-2012.</p>
<p><b>EasyABC</b> is maintained by <b>Jan Wybren de Jong</b>, <b>Seymour Shlien</b> and  by <b>Fr&eacute;d&eacute;ric Aup&eacute;pin</b> for Mac adaptation</p>
<p><b>Credits</b> - software components used by EasyABC:</p>
<ul class="nicelist">
<li><a href="http://moinejf.free.fr/">abcm2ps</a> for converting ABC code to note images (developed/maintained by Jean-Fran&ccedil;ois Moine)</li>
<li><a href="http://abc.sourceforge.net/abcMIDI/">abc2midi</a> for converting ABC code to midi (by James Allwright, maintained by Seymour Shlien)</li>
<li><a href="https://wim.vree.org/svgParse/xml2abc.html">xml2abc</a> for converting from MusicXML to ABC (by Willem Vree)</li>
<li><a href="https://sites.google.com/site/juria90/nwc">nwc2xml</a> for converting from Noteworthy Composer format to ABC via XML (by James Lee)</li>
<li><a href="https://www.wxpython.org/">wxPython</a> cross-platform user-interface framework</li>
<li><a href="https://www.scintilla.org/">scintilla</a> for the text editor used for ABC code</li>
<li><a href="https://www.mxm.dk/products/public/pythonmidi">python midi package</a> for the initial parsing of midi files to be imported</li>
<li><a href="https://www.pygame.org/download.shtml">pygame</a> (which wraps <a href="https://sourceforge.net/apps/trac/portmedia/wiki/portmidi">portmidi</a>) for real-time midi input</li>
<li><a href="https://www.fluidsynth.org/">FluidSynth</a> for playing midi (and made fit for Python with a <a href="https://wim.vree.org/svgParse/testplayer.html">player</a> by <a href="https://wim.vree.org/svgParse/">Willem Vree</a>)</li>
<li><a href="https://github.com/jheinen/mplay">Python MIDI Player</a> for playing midi on Mac</li>
<li>Thanks to Guido Gonzato for providing the fields and command reference extracted from his <a href="https://abcplus.sourceforge.net/#ABCGuide">Making music with ABC guide</a>.</li>
<li><br>Many thanks to the translators: Valerio&nbsp;Pelliccioni, Guido&nbsp;Gonzato&nbsp;(italian), Bendix&nbsp;R&oslash;dgaard&nbsp;(danish), Fr&eacute;d&eacute;ric&nbsp;Aup&eacute;pin&nbsp;(french), Bernard&nbsp;Weichel&nbsp;(german), Jan&nbsp;Wybren&nbsp;de&nbsp;Jong&nbsp;(dutch) and Wu&nbsp;Xiaotian&nbsp;(chinese).</li>
<li>Universal binaries of <a href="https://abcplus.sourceforge.net/#abcm2ps">abcm2ps</a> and <a href="https://abcplus.sourceforge.net/#abcmidi">abc2midi</a> for OSX are available thanks to Chuck&nbsp;Boody and Guido Gonzato</li>
</ul>

<p><b>Links</b></p>
<ul class="nicelist">
<li><a href="https://abcnotation.com/">abcnotation.com</a></li>
<li><a href="http://abcplus.sourceforge.net/">abcplus.sourceforge.net</a></li>
<li><a href="http://moinejf.free.fr/">Jef Moine's abcm2ps page</a></li>
<li><a href="https://abcmidi.sourceforge.io/">Seymour Shlien's abcMIDI page</a></li>
<li><a href="http://www.folkwiki.se/">folkwiki.se - Swedish folk music</a> (initial involvement of Nils here is the reason why he implemented the program)</li>
</ul>
</body>
</html>
'''.format(program_name)

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, wx.ID_ANY, _('About EasyABC'), size=(900, 600) )
        about_html = wx.html.HtmlWindow(self, -1)
        about_html.SetPage(self.htmlpage)
        button = wx.Button(self, wx.ID_OK, _('&Ok'))
        button.SetDefault()

        # Definition of the padding of the window
        lc = wx.LayoutConstraints()
        lc.top.SameAs(self, wx.Top, 5)
        lc.left.SameAs(self, wx.Left, 5)
        lc.bottom.SameAs(button, wx.Top, 5)
        lc.right.SameAs(self, wx.Right, 5)
        about_html.SetConstraints(lc)

        # Definition of the position of the OK button
        lc = wx.LayoutConstraints()
        lc.bottom.SameAs(self, wx.Bottom, 5)
        lc.centreX.SameAs(self, wx.CentreX)
        lc.width.AsIs()
        lc.height.AsIs()
        button.SetConstraints(lc)

        about_html.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.OnLinkClicked)

        self.SetAutoLayout(True)
        self.Layout()
        self.CentreOnParent(wx.BOTH)

    def OnLinkClicked(self, evt):
        webbrowser.open(evt.GetLinkInfo().GetHref())
        return wx.html.HTML_BLOCK


class MyTunesListFrame(wx.Frame):
    ''' Creates the TextCtrl for displaying the tunes list'''
    def __init__(self):
        # 1.3.6.1 [JWdJ] 2014-01-30 Resizing message window fixed
        wx.Frame.__init__(self, wx.GetApp().TopWindow, wx.ID_ANY, _("List of tunes"),style=wx.DEFAULT_FRAME_STYLE,name='tuneslistframe',size=(600,240))
        # Add a panel so it looks the correct on all platforms
        self.panel = ScrolledPanel(self)
        self.basicText = wx.TextCtrl(self.panel, wx.ID_ANY, "",style=wx.TE_MULTILINE | wx.TE_READONLY)
        # 1.3.6.3 [JWDJ] changed to fixed font so Abcm2ps-messages with a ^ make sense
        font = wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.basicText.SetFont(font)
        sizer = wx.BoxSizer()
        sizer.Add(self.basicText,1, wx.ALL|wx.EXPAND)
        self.panel.SetSizer(sizer)
        self.panel.SetupScrolling()

    def ShowText(self,text):
        self.basicText.Clear()
        self.basicText.AppendText(text)


#p09 2014-10-22

class MyInfoFrame(wx.Frame):
    ''' Creates the TextCtrl for displaying any messages from abc2midi or abcm2ps. '''
    def __init__(self):
        # 1.3.6.1 [JWdJ] 2014-01-30 Resizing message window fixed
        wx.Frame.__init__(self, wx.GetApp().TopWindow, wx.ID_ANY, _("Messages"),style=wx.DEFAULT_FRAME_STYLE,name='infoframe',size=(600,240))
        # Add a panel so it looks the correct on all platforms
        self.panel = ScrolledPanel(self)
        self.basicText = wx.TextCtrl(self.panel, wx.ID_ANY, "",style=wx.TE_MULTILINE | wx.TE_READONLY)
        # 1.3.6.3 [JWDJ] changed to fixed font so Abcm2ps-messages with a ^ make sense
        font = wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.basicText.SetFont(font)
        sizer = wx.BoxSizer()
        sizer.Add(self.basicText,1, wx.ALL|wx.EXPAND)
        self.panel.SetSizer(sizer)
        self.panel.SetupScrolling()

    def ShowText(self,text):
        self.basicText.Clear()
        self.basicText.AppendText(text)

    # 1.3.6.3 [JWDJ] 2015-04-27
    @staticmethod
    def update_text():
        global execmessages
        win = wx.FindWindowByName('infoframe')
        if win is not None:
            win.ShowText(execmessages)


class MyAbcFrame(wx.Frame):
    ''' Creates the TextCtrl for displaying any messages from abc2midi or abcm2ps. '''
    def __init__(self):
        wx.Frame.__init__(self, wx.GetApp().TopWindow, wx.ID_ANY, _("Processed Abc Tune"),style=wx.DEFAULT_FRAME_STYLE,name='abctuneframe')
        # 1.3.6.3 [JWdJ] 2015-04-22 bugfix: resizing processed abc tune page now works correctly
        self.basicText = stc.StyledTextCtrl(self, wx.ID_ANY, (-1, -1), (600, 450))
        self.basicText.SetMarginLeft(15)
        self.basicText.SetMarginWidth(1, 40)
        self.basicText.SetMarginType(1, stc.STC_MARGIN_NUMBER)

        font = wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        face = font.GetFaceName()
        size = font.GetPointSize()
        self.basicText.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT, "face:%s,size:%d" % (face, size)) # 1.3.6.3 [JWdJ] 2015-04-22 fixed font

        sizer = wx.BoxSizer()
        sizer.Add(self.basicText,1, wx.ALL | wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Fit(self)

    def ShowText(self, text):
        try:
            self.basicText.SetEditable(True)
        except:
            pass
        self.basicText.ClearAll() # 1.3.6.4 [SS] 2015-06-17
        self.basicText.AppendText(text)
        try:
            self.basicText.SetEditable(False) # 1.3.6.3 [JWdJ] 2015-04-22 abc code not editable
        except:
            pass # 1.3.6.3 [JWdJ] 2015-05-02 older wx-versions do not support SetEditable

    # 1.3.6.3 [JWDJ] 2015-04-27
    @staticmethod
    def update_text():
        global visible_abc_code
        win = wx.FindWindowByName('abctuneframe')
        if win is not None:
            win.ShowText(visible_abc_code)


#1.3.6.4 [SS] 2015-06-22
class MyMidiTextTree(wx.Frame):
    def __init__(self,title):
        wx.Frame.__init__(self, wx.GetApp().TopWindow, wx.ID_ANY, title, wx.DefaultPosition, wx.Size(450, 350))

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        vbox = wx.BoxSizer(wx.VERTICAL)
        panel1 = wx.Panel(self, -1)

        self.tree = wx.TreeCtrl(panel1, 1, wx.DefaultPosition, (-1, -1), wx.TR_HAS_BUTTONS )
        vbox.Add(self.tree, 1, wx.EXPAND)
        hbox.Add(panel1, 1, wx.EXPAND)
        panel1.SetSizer(vbox)
        self.SetSizer(hbox)
        self.Centre()

    def LoadMidiData(self,data):
        self.tree.DeleteAllItems()
        tracknum = '0'
        trk = {}
        for line in data:
            col = line.find('Track')
            if col == 0:
                words = line.split(' ')
                tracknum = words[1]
                trk[tracknum] = self.tree.AppendItem(self.root,line)
            else:
                if tracknum == '0':
                    self.root = self.tree.AddRoot(line)
                    continue
                self.tree.AppendItem(trk[tracknum],line)
        self.tree.Expand(self.root)


class MyApp(wx.App):
    def __init__(self, *args, **kargs):
        self._frames = []
        self.settings = {}
        wx.App.__init__(self, *args, **kargs)

    def CheckCanDrawSharpFlat(self):
        dc = wx.MemoryDC(wx_bitmap(200, 200, 32))
        dc.SetBackground(wx.WHITE_BRUSH)
        dc.Clear()
        dc = wx.GraphicsContext.Create(dc)
        try:
            for text in (u'G\u266d', u'G\u266f'):
                font_size = 12
                wxfont = wx.Font(font_size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, 'Helvetica', wx.FONTENCODING_DEFAULT )
                wxfont.SetPointSize(font_size)
                font = dc.CreateFont(wxfont, wx_colour('black'))
                dc.SetFont(font)
                (width, height, descent, externalLeading) = dc.GetFullTextExtent(text)
                dc.DrawText(text, 100, 100-height+descent)
            self.settings['can_draw_sharps_and_flats'] = True
        except wx.PyAssertionError:
            self.settings['can_draw_sharps_and_flats'] = False


    def NewMainFrame(self, options = None):
        frame = MainFrame(None, 0, self.app_dir, self.settings, options or {})
        self._frames.append(frame)
        return frame

    def UnRegisterFrame(self, frame):
        self._frames.remove(frame)

    def GetAllFrames(self):
        L = self._frames[:]
        L.sort(key=lambda f: not f.IsActive()) # make sure an active frame comes first in the list
        return L

    def MacOpenFile(self, filename):	# [EPO] 2018-11-20 TODO  dup open file creates two frames (why?)
        """Called for files dropped on dock icon, or opened via finders context menu"""
        #dlg = wx.MessageDialog(None,
        #                       "This app was just asked to open:\n%s\n"%filename,
        #                       "File Dropped",
        #                       wx.OK|wx.ICON_INFORMATION)
        #dlg.ShowModal()
        #dlg.Destroy()
        #frame = self.NewMainFrame()
        #frame.Show(True)
        #self.SetTopWindow(frame)
        ##path = os.path.abspath(sys.argv[1]).decode(sys.getfilesystemencoding())
        #self.frame.load_or_import(filename)
        if not self.frame.editor.GetModify() and not self.frame.current_file:     # if a new unmodified document
            self.frame.load(filename)
        else:
            self.frame = self.NewMainFrame()
            self.frame.load(filename)
            
    def MacNewFile(self):
        #dlg = wx.MessageDialog(None,
        #                       "This app was just asked to launch",
        #                       "App started",
        #                       wx.OK|wx.ICON_INFORMATION)
        #dlg.ShowModal()
        #dlg.Destroy()
        recent_file = self.settings.get('recentfiles', '').split('|')[0]
        if recent_file and os.path.exists(recent_file):
            path = recent_file

        if path :
            self.frame.load_or_import(path)

    def OnInit(self):
        try:
            self.SetAppName('EasyABC')
            #wx.SystemOptions.SetOptionInt('msw.window.no-clip-children', 1)
            app_dir = self.app_dir = wx.StandardPaths.Get().GetUserLocalDataDir()
            if not os.path.exists(app_dir):
                os.mkdir(app_dir)
            cache_dir = os.path.join(app_dir, 'cache')
            if not os.path.exists(cache_dir):
                os.mkdir(cache_dir)
            default_lang = wx.LANGUAGE_DEFAULT
            locale = wx.Locale(language=default_lang)
            locale.AddCatalogLookupPathPrefix(os.path.join(cwd, 'locale'))
            locale.AddCatalog('easyabc')
            self.locale = locale # keep this reference alive
            global current_locale
            current_locale = locale
            wx.ToolTip.Enable(True)
            wx.ToolTip.SetDelay(1000)

            self.CheckCanDrawSharpFlat()
            options = {}
            
            path = None
            if len(sys.argv) > 1:
                if sys.version_info >= (3,0,0): #FAU 20210101: In Python3 there isn't anymore the decode.
                    args = sys.argv
                else:
                    fse = sys.getfilesystemencoding()
                    args = [arg.decode(fse) for arg in sys.argv]

                i = 0
                while i < len(args):
                    arg = args[i]
                    i += 1
                    if arg.startswith('-'):
                        arg = arg[1:]
                        if arg == 'exclusive':
                            options[arg] = 'True'
                    else:
                        path = os.path.abspath(arg)

            #p08 We need to be able to find app.frame [SS] 2014-10-14
            self.frame = self.NewMainFrame(options)
            self.frame.Show(True)
            self.SetTopWindow(self.frame)

            # 1.3.8.4 [mist] Load most recent file
            if not path:
                recent_file = self.settings.get('recentfiles', '').split('|')[0]
                if recent_file and os.path.exists(recent_file):
                    path = recent_file

            #FAU: on Mac the sys.frozen is set by py2app and pyinstaller and is unset otherwise getattr( sys, 'frozen', False)
            if path and wx.Platform != "__WXMAC__":
                self.frame.load_or_import(path)
        except:
            sys.stdout.write(traceback.format_exc())
        return True

app = MyApp(0)

#import wx.lib.inspection
#wx.lib.inspection.InspectionTool().Show()

app.MainLoop()
application_running = False
current_locale = None
app = None

