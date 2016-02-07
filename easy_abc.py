#!/usr/bin/python2.7
#
program_name = 'EasyABC 1.3.7.1 2016-02-03'
# Copyright (C) 2011-2014 Nils Liberg (mail: kotorinl at yahoo.co.uk)
# Copyright (C) 2015-2016 Seymour Shlien (mail: fy733@ncf.ca)
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# V1.3.7.1
# - Dutch translation
# - ABC assist improvements
#
# V1.3.7.0
# Incremental improvements and bug fixes.
#
# New V1.3.6.4
# - Recent files menu
# - Font from .svg file now rendered properly
# - Some fixes to accommodate 1.3.6.3 issues on the Mac.
# - On Windows the 'Input Processed Tune' window was not updated correctly (since 1.3.6.3)
# - Added an option to play a short introduction (count in) before the music is played.
# - Added volume controls for the guitar bass/chord accompaniment
# - Added to internals show output midi file (an advanced feature for debugging)
#
# New V1.3.6.3
# When the cursor moves outside the current page, the correct page is automatically chosen
# Unique filenames for midi and svg to prevent problems when multiple editor windows are used
# Preprocessing abc file and generating midi/svg split up
# Volume-settings still work even when the abc code contains %%MIDI program
# Music score can be zoomed in further
# MIDI file starts a little faster after pressing play on Windows OS
# Play button acts as pause button when tune is playing
# Fixed "Processed Abc Tune": no longer editable and uses fixed font now. Also resizing fixed.
# More text translatable
# Easier switching between different versions of executables by using dropdown button in File Settings tab
# Removed buttons 'Change abcm2ps path' and 'Restore abcm2ps path' because the default can be chosen in de File Settings tab
# Sometimes opening the messages window showed the 'processed tune' window
# Added beats/minute controlled to the toolbar
# Changed Internals->Messages to fixed font so Abcm2ps-messages with a ^ make sense
#
#
# New V1.3.6.2
# EasyAbc now supports the abcm2ps voicecolor command which has been
# introduced in version 8.5 and higher. There have been other changes
# which improve the performance of the svg rendering functions.
#
#
# New V1.3.6.1
# Added settings/cold restart
# Eliminated path_ps2pdf settings option
# Checked the values of some of the page settings (for abcm2ps)
# Rearranged settings in Abc Settings NoteBook

# New in V1.3.6
# Reworking the internals/Messages.
# To make the abc file settings more transparent, they now show the
# default settings if the executables are found. However
# if you make them blank, the next time easyabc starts, it will
# set them to the defaults provided the executabls exist.
# The voice/channel settings is now a separate page in the
# abc settings tabbed book.
# Eliminated hash code from cached abc,svg,midi temp files.
# Added tools/search which searches recursively all abc files
# in a folder for a tune containing a specific word in the title.
# A list of all tunes found is shown in a listbox and clicking
# anyone of those tunes will automatically load the file.
# Added option to set the gchord pattern in the Abc Settings
# Changed the call sequence to AbcToSvg so that it is more compact.
# Added abcm2ps page in abc settings. The page provides an
# option to include bar line numbering in the music output.
# Added a status bar which is used to report any problems that
# are detected when processing a tune.
# The popup Error Messages have been suppressed. The user needs
# to go to the Internals/messages menu item to view the problems.
# A progress bar appears for operations that take a long time
# -- for example exporting a large collection of tunes to midi
# files. The user has the option of cancelling in the middle.
# Upgraded the xml modules (abc2xml.py-??, xml2abc.py-?? and
# xml2abc_interface) to the latest versions developed by Wim Vree.
# Added to the Internals menu, Show settings status function.
# Added Settings/Cold restart/ an option to put EasyAbc in
# the state as if it is running for the first time. The settings.1.3.dat
# file will be recreated with the initial settings.

#
# New in V1.3.5_p09 patch.
# On startup the program checks that the abc settings are consistent.
# The path to ghostscript and /or ps2pdf can be specified by the
# user. If the path to ps2pdf is specified, that program will be
# used to create the pdf file from the PostScript file.
# The abc settings dialog box has been replaced with a tabbed
# notebook leaving more space for more user options to be introduced
# in future versions of this program.
# Upgraded to abc2xml_v61 and xml2abc_v52.
# If midiplayer is defined in abc settings, that player will be used.
# Added 'internals' to the top menu for viewing some of the
# internals of the program. Internals/messages displays the warnings
# and error messages returned by abc2midi and other applications.
# Internals/input processed tune displays the abc file actually
# given to abc2midi or other applications so that line numbers
# can be matched with the warnings.
#
#
# New in V1.3.5_p08 patch.
# The music panel representation now responds to moving the cursor using
# arrow keys in the edit panel.
# Fixed a problem in playing a tune (converting to MIDI) when the
# tune has non ascii characters. (reported by Chuck Boody)
# The F7 key will stop playing MIDI music.
# Included a new application abccore.py which runs separately
# from easy_abc.py. It was created by Seymour Shlien and is in
# still in development.
#
# New in V1.3.5_p07 patch
# Add option to be able to set different instrument for each midi voice (request from Chuck Boody)
# Add option to be able to set volume and balance for each midi voice (request from Chuck Boody)
# Add option to have default instrument for all voices (previous behaviour)
# Remove experimental mention concerning abc2xml (request from Chuck Boody)
# Fix the fact that on MacOS X guitar chord are always played if the are define in another voice than voice 1 (reported by Chuck Boody)
# Try to reduce glitch while looping playback if double-click on play button
#
# New in V1.3.5_p06 patch
# upgrade to version 54 of abc2xml
# upgrade to version 2014-02-05 of abcMIDI (abc2abc and abc2midi)
# upgrade to version 7.7.1 of abcm2ps
# fixed alarm regarding musicxml file when imported in Finale (reported by Chuck Boody) need to verify with other software
# fixed bug: Easy_abc manages svg files created with version 7.6.5 and later for width/height (reported by Frederic Aupepin)
# increase size of line for staff lines, bar lines, and note stems (patch from Seymour)
#
# New in V1.3.5_p05 patch
# upgrade to version 2013-03-26 of abcMIDI (abc2abc and abc2midi)
# upgrade to version 7.5.2 of abcm2ps
# upgrade to version 50 of xml2abc
#
# New in V1.3.5_p04 patch
# fixed bug: note selection from tune with abcm2ps version 7.2.0 and later (reported by Chuck Boody)
#
# New in V1.3.5_p03 patch
# add an export all to individual pdf files (request from Chuck Boody)
#
# New in V1.3.5_p02 patch
# add an export all for midi (request from Chuck Boody)
# fixed bug: syntax highlighting ']' in comments (reported by Frederic Aupepin)
#
# New in V1.3.5_p01 patch
# fixed bug: syntax highlighting with lyrics (reported by Chuck Boody)
#
# All other changes from V1.3 to V1.3.5 are described in changes.txt
# which comes with the source code.


# Table of Contents
# ---------------------------------

#Global:
#   str2fractions(), calc_tune_id().read_text_if_file_exists,
#   get_ghostscript_path(), upload_tune(),
#   launch_file(), remove_non_note_fragments(), get_notes_from_abc(),
#   copy_bar_symbols_from_first_voice(), process_MCM(), get_hash_code(),
#   change_abc_tempo(), add_table_of_contents_to_postscript_file(),
#   sort_abc_tunes(), process_abc_code(), AbcToPS, GetSvgFileList(),
#   AbcToSvg(), AbcToAbc(), MidiToMftext(),  set_gs_path_for_platform(),
#   AbcToPDF(), test_for_guitar_chords(), list_voices_in(),
#   grab_time_signature(), drum_intro(),  need_left_repeat(),
#   make_abc_introduction(),  AbcToMidi(), process_abc_for_midi(),
#   add_abc2midi_options(), str2bool(), fix_boxmarks(),
#   change_texts_into_chords(), NWCToXml(), frac_mod()

#class AbcTune()
#    abc_code()

#class MidiTune()
#    cleanup()

#class SvgTune()
#    render_page(),clear_pages(),cleanup(),page_count()

#class MusicPrintout()
#   HasPage(), GetPageInfo(), OnPrintPage()

#class MusicUpdateDoneEvent()

#class MusicUpdateThread()
#   run(), ConvertAbcToSvg(), abort()

#  frac_mod(), start_process()

#class MidiThread()
#   run(), play_midi, clear_queue, queue_task
#   abort, is_busy()

#class RecordThread()
#   timedelta_microseconds(), beat_duration(), run(), quantize_swinged_16th(),
#   quantize_triplet(), quantize(), abort()

#class IncipitsFrame()
#  GrayUngray(), OnTwoColumns(), save_settings(), OnOk(), OnCancel()

#class NewTuneFrame()

#class MyNoteBook()

#class AbcFileSettingsFrame()
#   OnBrowse(), OnChangePath(), change_path_for_control(), On_Chk_IncludeHeader()
#   OnPath_midiplayer(), OnRestoreSettings()
#   append_exe(), keep_existing_paths(), get_default_path()

#class MyChordPlayPage()
#   OnPlayChords(), OnNodynamics(), OnNofermatas(), OnNograce(), OnBarfly()
#   OnMidiIntro(), OnMidi_Program(), On_midi_chord_program(),
#   On_midi_bass_program, SetGchordChoices(), OnGchordSelection(),
#   OnBeatsPerMinute(),  OnTranspose(), OnTuning(), OnChordVol(), OnBassVol()

#class MyVoicePage()
#  OnProgramSelection(), OnSliderScroll(), OnResetDefault()

#class MyAbcm2psPage()
#  OnAbcm2psClean(), OnAbcm2psDefaults(), OnAbcm2psBar()
#  OnAbcm2pslyrics(), OnAbcm2psref(), OnAbcm2psend()
#  OnPSScale(), OnPSleftmarg(), OnPSrightmarg(),
#  OnPStopmarg(), OnPSbotmarg(), OnPSpagewidth(),
#  OnPSpageheight(), OnFormat(), On_extra_params(),
#  OnBrowse_format()

#class MyXmlPage()
#   OnXmlPage(), OnXmlCompressed(), OnXmlUnfold(), OnXmlMidi()
#   OnVolta(), OnMaxbars(), OnMaxchrs(), OnCreditval(), OnUnitval()

#class MidiSettingsFrame()
#   OnOk(), OnCancel()

#class MidiOptionsFrame()
#   OnOk(), OnCancel()

#class ErrorFrame()
#   OnKeyDownEvent(), OnOk(), OnCancel()

#class ProgressFrame()
#   SetPercent()

#class FlexibleListCtrl()
#   GetListCtrl(), GetSortImages(), getColumnText(), GetSecondarySortValues()

#class MySearchFrame()
#   On_browse_abcsearch(), On_start_search(), find_abc_files(),
#   find_abc_string(),OnItemSelected()

#class MyHtmlFrame()

#class MyOpenPopupMenu()

#class MainFrame()
#   OnPageSetup(),OnPrint(),OnPrintPreview(),GetAbcToPlay(),
#   parse_desc(), get_num_extra_header_lines(),OnNoteSelectionChangeDesc(),
#   transpose_selected_note(), OnResetView(), OnSettingsChanged(),
#   OnToggleMusicPaneMaximize(), OnMouseWheel(), update_playback_rate()
#   OnBpmSlider(), OnBpmSliderClick(), start_midi_out(),
#   do_load_media_file(), OnMediaLoaded(),
#   OnMediaStop(), OnMediaFinished(), OnToolRecord(),
#   OnToolStop(), OnSeek(), OnZoomSlider(), OnPlayTimer(),
#   OnRecordBpmSelected(), OnRecordMetreSelected(), flip_toolbar(),
#   setup_toolbar(), OnViewRythm(), OnRecordStop(), OnDoReMiModeChange(),
#   generate_incipits_abc(), OnGenerateIncipits(), OnViewIncipits()
#   OnSortTunes(), OnRenumberTunes(), OnSearchDirectories(),
#   OnUploadTune(), OnGetFileNameForTune(), OnExportMidi(),
#   OnExportAllMidi(), OnExportAllPDFFiles(), OnExportPDF()
#   OnExportSVG(), OnExportMusicXML(), OnExportAllMusicXML(),
#   OnExportHTML(), OnExportAllHTML(), createArchive(),
#   OnExportAllEpub(), OnExportAllPDF(),
#   OnMusicPaneDoubleClick(), OnMusicPaneKeyDown(), OnRightClickList(),
#   OnInsertSymbol(),  OnToolPlay(), OnToolPlayLoop(),
#   OnToolRefresh(), OnToolAbcAssist(), UpdateAbcAssistSetting(),
#   __onPaneClose(), OnToolAddTune(), OnToolDynamics(),
#   OnToolOrnamentation(), OnToolDirections(), CanClose(),
#   OnNew(),  OnOpen(),  OnImport(), get_encoding(),
#   load_or_import(), load(), ask_save(), save(),
#   save_as(), AbcToAbcCurrentTune(), OnHaveL(), OnDoubleL(),
#   OnTranspose(), OnAlignBars(), create_symbols_popup_menu(),
#   create_menu_bar(), create_menu(), append_menu_item()
#   create_upload_context_menu(), setup_typing_assistance_menu(),
#   setup_menus(), OnShowMessages(), ShowMessages(), OnShowAbcTune(),
#   OnCloseFile(), OnSave(), OnSaveAs(), OnQuit(),
#   do_command(),  OnUndo(), OnRedo(), OnCut(), OnCopy(),
#   OnPaste(), OnDelete(), OnSelectAll(), OnFind(),
#   OnReplace, OnFindClose(), get_scintilla_find_flags(),
#   OnFindReplace(), OnFindReplaceAll(), OnFindNextABC(),
#   OnFindNext(), OnAbout(), OnEasyABCHelp(), OnABCStandard(),
#   OnABCLearn(), OnAbcm2psHelp(), OnClearCache(), OnMidiSettings(),
#   OnAbcSettings(), OnChangeFont(), OnViewFieldReference(),
#   OnFieldReferenceItemDClick(), OnUseDefaultFont(),
#   ScrollMusicPaneToMatchEditor(), OnMovedToDifferentLine(),
#   AutoInsertXNum(), DoReMiToNote(), OnCharEvent(),
#   FixNoteDurations(), AddTextWithUndo(), OnKeyDownEvent(),
#   StartKeyboardInputMode(), OnEditorMouseRelease(),
#   OnPosChanged(), OnModified(), AutomaticUpdate(),
#   OnChange(),  GrayUnGray(), OnUpdate(), OnClose(),
#   DetermineMidiPlayRange(), PlayMidi(), GetTextPositionOfTune()
#   OnTuneListClick(), SetErrorMessage(), OnPageSelected(),
#   UpdateMusicPane(), OnMusicUpdateDone(), GetTextRangeOfTune()
#   GetFileHeaderBlock(), GetSelectedTune(), GetTune(),
#   OnTuneDoubleClicked(), OnTuneSelected(), UpdateTuneList()
#   UpdateTuneListVisibility(), OnTimer(), GetTunes(),
#   GetTuneAbc(), InitEditor(), OnDropFile(), update_statusbar_and_messages()
#   handle_midi_conversion(), OnReducedMargins(), load_settings(),
#   save_settings(), restore_settings()

#class MyFileDropTarget()

#class AboutFrame()

#class MyInfoFrame()
#   ShowText(), update_text()

#class MyAbcFrame()
#   ShowText(), update_text()

#class MyMidiTextTree
#   LoadMidiData

#class MyApp()
#   CheckCanDrawSharpFlat(), NewMainFrame(), UnRegisterFrame(),
#   GetAllFrames(), MacOpenFile(), OnInit(),

abcm2ps_default_encoding = 'utf-8'  ## 'latin-1'
utf8_byte_order_mark = chr(0xef) + chr(0xbb) + chr(0xbf) #'\xef\xbb\xbf'

import os, os.path
import sys
import wx
if os.getenv('EASYABCDIR'):
    cwd = os.getenv('EASYABCDIR')
else:
    cwd = os.getcwd()
    if os.path.isabs(sys.argv[0]):
        cwd = os.path.dirname(sys.argv[0])
        # 1.3.6.3 [JWDJ] 2015-04-27 On Windows replace forward slashes with backslashes
        if wx.Platform == "__WXMSW__":
            cwd = cwd.replace('/', '\\')
sys.path.append(cwd)

import re
import subprocess
import codecs
import hashlib
import cPickle as pickle
import urllib2 # 1.3.6.2 [JWdJ] 2015-02
import threading
import shutil
import platform
import webbrowser
import time
import traceback
import xml.etree.cElementTree as ET
import zipfile
import uuid # 1.3.6.3 [JWdJ] 2015-04-22
from datetime import datetime
from collections import deque, namedtuple
from UserString import MutableString
from cStringIO import StringIO
from wx.lib.scrolledpanel import ScrolledPanel
import wx.html
import wx.stc as stc
import wx.lib.agw.aui as aui
import wx.lib.rcsizer as rcs
# import wx.lib.filebrowsebutton as filebrowse # 1.3.6.3 [JWdJ] 2015-04-22
import wx.media
import wx.lib.platebtn as platebtn
import wx.lib.mixins.listctrl as listmix
import wx.lib.agw.hypertreelist as htl
from wx.lib.embeddedimage import PyEmbeddedImage
from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED
from wx import GetTranslation as _

##from xml2abc_nils import xml_to_abc
from xml2abc_interface import xml_to_abc, abc_to_xml
from midi2abc import midi_to_abc, Note, duration2abc
# from midi_meta_data import midi_to_meta_data # 1.3.6.3 [JWdJ] 2015-04-22
from generalmidi import general_midi_instruments
# from ps_parser import Abcm2psOutputParser # 1.3.6.3 [JWdJ] 2015-04-22
from abc_styler import ABCStyler
from abc_character_encoding import decode_abc, encode_abc
from abc_search import abc_matches_iter
from fraction import Fraction
from music_score_panel import MusicScorePanel
from svgrenderer import SvgRenderer
from aligner import align_lines, extract_incipit, bar_sep, bar_sep_without_space, get_bar_length
##from midi_processing import humanize_midi
from Queue import Queue # 1.3.6.2 [JWdJ] 2015-02

if wx.Platform == "__WXMSW__":
    import win32api
    import win32process
try:
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
        sys.stderr.write('Warning: pygame/pypm module not found. Recording midi will not work')

def str2fraction(s):
    parts = [int(x.strip()) for x in s.split('/')]
    return Fraction(parts[0], parts[1])

Tune = namedtuple('Tune', 'xnum title rythm offset_start offset_end abc header num_header_lines')
class AbortException(Exception): pass
class Abcm2psException(Exception): pass
class NWCConversionException(Exception): pass

# 1.3.6.3 [JWdJ] renamed BaseTune to AbcTune and added functions
class AbcTune(object):
    def __init__(self, abc_code, tune_id=None):
        self.__abc_code = abc_code
        self.__abc_lines = None
        self.__tune_header_start_line_index = None
        self.__first_note_line_index = None
        self.__tune_id = tune_id

    @property
    def abc_code(self):
        return self.__abc_code

    @property
    def abc_lines(self):
        if self.__abc_lines is None:
            self.__abc_lines = self.abc_code.splitlines()
        return self.__abc_lines

    @property
    def first_note_line_index(self):
        if self.__first_note_line_index is None:
            line_no = 1 # start with 1 because body starts 1 line after K field
            for line in iter(self.abc_lines):
                if line.startswith('K:'):
                    self.__first_note_line_index = line_no
                    break
                line_no += 1

        return self.__first_note_line_index

    @property
    def tune_header_start_line_index(self):
        if self.__tune_header_start_line_index is None:
            line_no = 0 # start with 0 because header starts with the X field
            for line in iter(self.abc_lines):
                if line.startswith('X:'):
                    self.__tune_header_start_line_index = line_no
                    break
                line_no += 1
        return self.__tune_header_start_line_index

    @staticmethod
    def generate_tune_id(abc_code):
        return uuid.uuid4()

    @property
    def tune_id(self):
        if self.__tune_id is None:
            self.__tune_id = self.generate_tune_id(self.abc_code)
        return self.__tune_id

    @staticmethod
    def generate_temp_file_name(path, ending, replace_ending=None):
        i = 0
        file_exists = True
        while file_exists:
            file_name = os.path.abspath(os.path.join(path, "temp{0:02d}{1}".format(i, ending)))
            file_exists = os.path.exists(file_name)
            if not file_exists and replace_ending is not None:
                f = os.path.abspath(os.path.join(path, "temp{0:02d}{1}".format(i, replace_ending)))
                file_exists = os.path.exists(f)
            i += 1

        return file_name


# 1.3.6.3 [JWdJ] 2015-04-22
class MidiTune(AbcTune):
    """ Container for abc2midi-generated .midi files """
    def __init__(self, abc_code, midi_file=None, error=None, tune_id=None):
        super(MidiTune, self).__init__(abc_code, tune_id)
        self.error = error
        self.midi_file = midi_file

    def cleanup(self):
        if self.midi_file:
            if os.path.isfile(self.midi_file):
                os.remove(self.midi_file)
            self.midi_file = None

# 1.3.6.2 [JWdJ]
class SvgTune(AbcTune):
    """ Container for abcm2ps-generated .svg files """
    def __init__(self, abc_code, svg_files, error=None, tune_id=None):
        super(SvgTune, self).__init__(abc_code, tune_id=tune_id)
        self.error = error
        self.svg_files = svg_files
        self.pages = {}

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

    @property
    def page_count(self):
        return len(self.svg_files)

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
        if tune.abc_code and self.cache_size > 0:
            tune_id = tune.tune_id
            #if tune_id in self.__tunes:
            #    print 'tune already cached'
            while len(self.cached_tune_ids) >= self.cache_size:
                old_tune_id = self.cached_tune_ids.pop()
                self.remove(old_tune_id)
            self.__tunes[tune_id] = tune
            self.cached_tune_ids.append(tune_id)

    def cleanup(self):
        for tune_id in self.__tunes.keys():
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

# 1.3.6.3 [JWDJ] one function to determine font size
def get_normal_fontsize(): 
    if wx.Platform == "__WXMSW__":
        font_size = 10
    else:
        font_size = 14
    return font_size

def read_text_if_file_exists(filepath):
    ''' reads the contents of the given file if it exists, otherwise returns the empty string '''
    if filepath and os.path.exists(filepath):
        return open(filepath, 'rb').read()
    else:
        return ''

# p09 2014-10-14 [SS]
def get_ghostscript_path():
    ''' Fetches the ghostscript path from the windows registry and returns it.
        This function may not see the 64-bit ghostscript installations, especially
        if Python was compiled as a 32-bit application.
    '''
    import _winreg

    available_versions = []
    for reg_key_name in [r"SOFTWARE\\GPL Ghostscript", r"SOFTWARE\\GNU Ghostscript"]:
        try:
            aReg = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
            aKey = _winreg.OpenKey(aReg, reg_key_name)
            for i in range(100):
                try:
                    version = _winreg.EnumKey(aKey,i)
                    bKey = _winreg.OpenKey(aReg, reg_key_name + "\\%s" % version)
                    value, _ = _winreg.QueryValueEx(bKey, 'GS_DLL')
                    _winreg.CloseKey(bKey)
                    path = os.path.join(os.path.dirname(value), 'gswin32c.exe')
                    if os.path.exists(path):
                        available_versions.append((version, path))
                    path = os.path.join(os.path.dirname(value), 'gswin64c.exe')
                    if os.path.exists(path):
                        available_versions.append((version, path))
                except EnvironmentError:
                    break
            _winreg.CloseKey(aKey)
        except:
            pass
    if available_versions:
        return sorted(available_versions)[-1][1]   # path to the latest version
    else:
        return None

browser = None
def upload_tune(tune, author):
    ''' upload the tune to the site ABC WIKI site folkwiki.se (this UI option is only visible if the OS language is Swedish) '''
    global browser
    import mechanize
    import tempfile
    tune = tune.replace('\r\n', '\n')
    text = '(:music:)\n%s\n(:musicend:)\n' % tune.strip()
    if not browser:
        browser = mechanize.Browser()
    response = browser.open('http://www.folkwiki.se/Meta/Nyl%c3%a5t?n=Meta.Nyl%c3%a5t&base=Musik.Musik&action=newnumbered')
    response = response.read()
    import pdb; pdb.set_trace()
    m = re.search(r"img src='(.*?action=captchaimage.*?)'", response)
    if m:
        from urllib import urlretrieve
        captcha_url = m.group(1).encode('utf-8')
        f = tempfile.NamedTemporaryFile(delete=False)
        img_path = f.name
        print captcha_url
        print img_path
        img_data = urllib2.urlopen(captcha_url).read()
        urlretrieve(urlparse.urlunparse(parsed), outpath)
        print img_data
        f.write(img_data)
        f.close()
        return ''
    browser.select_form(nr=1)
    browser['text'] = text.encode('utf-8')
    browser['author'] = author.encode('utf-8')
    response = browser.submit()
    url = response.geturl()
    url = url.split('?')[0]  # remove the part after the first '?'
    return url

def launch_file(filepath):
    ''' open the given document using its associated program '''
    if wx.Platform == "__WXMSW__":
        os.startfile(filepath)
    elif wx.Platform == "__WXMAC__":
        subprocess.call(('open', filepath))
    elif os.name == 'posix':
        subprocess.call(('xdg-open', filepath))

def remove_non_note_fragments(abc, exclude_grace_notes=False):
    ''' remove parts of the ABC which is not notes or bar symbols by replacing them by spaces (in order to preserve offsets) '''

    repl_by_spaces = lambda m: ' ' * len(m.group(0))
    # replace non-note fragments of the text by replacing them by spaces (thereby preserving offsets), but keep also bar and repeat symbols
    abc = abc.replace('\r', '\n')
    abc = re.sub(r'(?s)%%beginps.+?%%endps', repl_by_spaces, abc)  # remove embedded postscript
    abc = re.sub(r'(?s)%%begintext.+?%%endtext', repl_by_spaces, abc)  # remove text
    abc = re.sub(r'(?m)%.*$', repl_by_spaces, abc)     # remove comments
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
            re.finditer(r"([_=^]?[[A-Ga-gz](,+|'+)?\d{0,2}(/\d{1,2}|/+)?)[><-]?", abc)]

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
        print 'warning: number of bar separators does not match (cannot complete operation)'
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
    """ Processes sticky rhythm feature of mcmusiceditor http://www.mcmusiceditor.com/download/sticky-rhythm.pdf
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
        if type(arg) is unicode:
            arg = arg.encode('utf-8', 'ignore')
        hash.update(arg)
        hash.update(program_name)
    return hash.hexdigest()[:10]

def change_abc_tempo(abc_code, tempo_multiplier):
    ''' multiples all Q: fields in the abc code by the given multiplier and returns the modified abc code '''

    def subfunc(m, multiplier):
        try:
            if '=' in m.group(0):
                parts = m.group(0).split('=')
                parts[1] = str(int( int(parts[1])*multiplier ))
                return '='.join(parts)

            q = int( int(m.group(1))*multiplier )
            if '[' in m.group(0):
                return '[Q: %d]' % q
            else:
                return 'Q: %d' % q
        except:
            return m.group(0)

    abc_code, n1 = re.subn(r'(?m)^Q: *(.+)', lambda m, mul=tempo_multiplier: subfunc(m, mul), abc_code)
    abc_code, n2 = re.subn(r'\[Q: *(.+)\]', lambda m, mul=tempo_multiplier: subfunc(m, mul), abc_code)
    # if no Q: field that is not inline add a new Q: field after the X: line
    # (it seems to be ignored by abcmidi if added earlier in the code)
    if n1 == 0:
        default_tempo = 120
        extra_line = 'Q:%d' % int(default_tempo * tempo_multiplier)
        lines = re.split('\r\n|\r|\n', abc_code)
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
    lines = re.split('\r\n|\r|\n', abc_code)
    tunes = []
    file_header = []
    preceeding_lines = []
    Tune = namedtuple('Tune', 'lines header preceeding_lines')
    cur_tune = None
    inside_begin = ''
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
        return tuple([tune.header.get(f, '') for f in sort_fields])

    tunes = [(get_sort_key_for_tune(t, sort_fields), t) for t in tunes]
    tunes.sort()
    ##print '\n'.join([str(x[0]) for x in tunes])

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
def process_abc_code(settings,abc_code, header, minimal_processing=False, tempo_multiplier=None, landscape=False):
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
    hash_code = get_hash_code(abc_code, read_text_if_file_exists(abcm2ps_format_path))
    ps_file = os.path.abspath(os.path.join(cache_dir, 'temp.ps'))

    # determine path
    if wx.Platform == "__WXMSW__":
        creationflags = win32process.CREATE_NO_WINDOW
    else:
        creationflags = 0

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


    process = subprocess.Popen(cmd1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags = creationflags, universal_newlines=True)
    stdout_value, stderr_value = process.communicate(input=(abc_code+os.linesep*2).encode(abcm2ps_default_encoding))
    stderr_value = os.linesep.join([x for x in stderr_value.split('\n')
                                    if not x.startswith('abcm2ps-') and not x.startswith('File ') and not x.startswith('Output written on ')])
    stderr_value = stderr_value.strip().decode(abcm2ps_default_encoding, 'replace')
    execmessages += '\nAbcToPs\n' + " ".join(cmd1) + '\n' + stdout_value + stderr_value
    #print execmessages
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
def AbcToSvg(abc_code, header, cache_dir, settings,  target_file_name=None, with_annotations=True, minimal_processing=False, landscape=False, one_file_per_page=True):
    global visible_abc_code
    # 1.3.6 [SS] 2014-12-17
    abc_code = process_abc_code(settings,abc_code, header, minimal_processing=minimal_processing, landscape=landscape)
    #hash = get_hash_code(abc_code, read_text_if_file_exists(abcm2ps_format_path), str(with_annotations)) # 1.3.6 [SS] 2014-11-13
    visible_abc_code = abc_code
    return abc_to_svg(abc_code, cache_dir, settings, target_file_name, with_annotations, one_file_per_page)

# 1.3.6.3 [JWDJ] 2015-04-21 splitted AbcToSvg up into 2 functions (abc_to_svg does not do preprocessing)
def abc_to_svg(abc_code, cache_dir, settings, target_file_name=None, with_annotations=True, one_file_per_page=True):
    """ converts from abc to postscript. Returns (svg_files, error_message) tuple, where svg_files is an empty list if the creation was not successful """
    global execmessages
    # 1.3.6.3 [SS] 2015-05-01
    global visible_abc_code
    abcm2ps_path =         settings.get('abcm2ps_path','')
    abcm2ps_format_path =  settings.get('abcm2ps_format_path','')
    extra_params =         settings.get('abcm2ps_extra_params','')
    # 1.3.6.3 [SS] 2015-05-01
    visible_abc_code = abc_code

    #print traceback.extract_stack(None, 5)

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


    # determine path
    if wx.Platform == "__WXMSW__":
        creationflags = win32process.CREATE_NO_WINDOW
    else:
        creationflags = 0

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
    # execmessages += '\nAbcToSvg\n' + " ".join(cmd1) 1.3.6.4 [JWdJ]
    execmessages = '\nAbcToSvg\n' + " ".join(cmd1)
    process = subprocess.Popen(cmd1, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags, universal_newlines=True, cwd=os.path.dirname(svg_file))
    stdout_value, stderr_value = process.communicate(input=(abc_code+os.linesep*2).encode(abcm2ps_default_encoding))
    execmessages += '\n' + stdout_value + stderr_value


    if process.returncode < 0:
        raise Abcm2psException('Unknown error - abcm2ps may have crashed')
    #dt = datetime.now() - t
    ##if wx.Platform != "__WXGTK__":
    ##    print 'abcm2ps time:\t', dt.seconds * 1000 + dt.microseconds/1000
    stderr_value = os.linesep.join([x for x in stderr_value.split('\n')
                                    if not x.startswith('abcm2ps-') and not x.startswith('File ') and not x.startswith('Output written on ')])
    stderr_value = stderr_value.strip().decode(abcm2ps_default_encoding, 'replace')
    if not os.path.exists(svg_file_first) or 'svg: ' in stderr_value:
        return ([], stderr_value)
    else:
        return (GetSvgFileList(svg_file_first), stderr_value)



def AbcToAbc(abc_code, cache_dir, params, abc2abc_path=None):
    ' converts from abc to abc. Returns (abc_code, error_message) tuple, where abc_code is None if abc2abc was not successful'
    global execmessages

    abc_code = re.sub(r'\\"', '', abc_code)  # remove escaped quote characters, since abc2abc cannot handle them

    # hash = get_hash_code(abc_code) # 1.3.6.3 [JWDJ] 2015-04-21 not used anymore

    # determine path
    if wx.Platform == "__WXMSW__":
        creationflags = win32process.CREATE_NO_WINDOW
    else:
        creationflags = 0

    # determine parameters
    cmd1 = [abc2abc_path, '-', '-r', '-b', '-e'] + params

    execmessages += '\nAbcToAbc\n' + " ".join(cmd1)

    process = subprocess.Popen(cmd1, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags)
    stdout_value, stderr_value = process.communicate(input=(abc_code+os.linesep*2).encode(abcm2ps_default_encoding))
    execmessages += '\n' + stderr_value
    if process.returncode < 0:
        raise Abcm2psException('Unknown error - abc2abc may have crashed')
    stderr_value = stderr_value.strip().decode(abcm2ps_default_encoding, 'replace')
    stdout_value = stdout_value.decode(abcm2ps_default_encoding, 'replace')
    if process.returncode == 0:
        return (stdout_value, stderr_value)
    else:
        return (None, stderr_value)

# 1.3.6.4 [SS] 2015-06-22
def MidiToMftext (midi2abc_path, midifile):
    ' dissasemble midi file to text using midi2abc'
    global execmessages
    creationflags = 0
    cmd1 = [midi2abc_path, midifile, '-mftext']
    execmessages += '\nMidiToMftext\n' + " ".join(cmd1)

    if os.path.exists(midi2abc_path):
        process = subprocess.Popen(cmd1, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=creationflags)
        stdout_value, stderr_value = process.communicate()
        #print stdout_value

        midiframe = MyMidiTextTree('Disassembled Midi File')
        midiframe.Show(True)
        midi_data = stdout_value
        midi_lines = midi_data.splitlines()
        midiframe.LoadMidiData(midi_lines)
    else:
        wx.MessageBox(_("Cannot find the executable midi2abc. Be sure it is in your bin folder and its path is defined in ABC Setup/File Settings."), ("Error") ,wx.ICON_ERROR | wx.OK)


# p09 2014-10-14 [SS]
def set_gs_path_for_platform(gs_path):
    if gs_path:
        return
    if wx.Platform == "__WXMSW__":
        gs_path = get_ghostscript_path()
        if not gs_path:
            wx.MessageBox(_("Ghostscript could not be found. You need to install Ghostscript and set the path to the Ghostscript executable in order to use this feature."), _("Error"), wx.ICON_ERROR | wx.OK)
            return None
    elif wx.Platform == "__WXMAC__":
        #gs_path = osx_gs_binary [SS] 2015-04-08
        gs_path  = '/usr/bin/pstopdf'
    else:
        gs_path = gs #default is linux [JWDJ: is gs an unresolved reference?]
    return gs_path


# p09 2014-10-14 2014-12-17 2015-01-28 [SS]
def AbcToPDF(settings,abc_code, header, cache_dir, extra_params='', abcm2ps_path=None, gs_path=None,  abcm2ps_format_path=None, generate_toc=False):
    global execmessages, visible_abc_code # 1.3.6.1 [SS] 2015-01-13
    pdf_file = os.path.abspath(os.path.join(cache_dir, 'temp.pdf'))
    # 1.3.6 [SS] 2014-12-17
    abc_code = process_abc_code(settings,abc_code, header, minimal_processing=True)
    (ps_file, error) = AbcToPS(abc_code, cache_dir, extra_params, abcm2ps_path, abcm2ps_format_path)
    if not ps_file:
        return None

    #if generate_toc:
    #    add_table_of_contents_to_postscript_file(ps_file)

    # convert ps to pdf
    creationflags = 0

    #1.3.6.1 [SS] 2015-01-28
    if wx.Platform == "__WXMSW__":
        creationflags = win32process.CREATE_NO_WINDOW
    # p09 we already checked for gs_path in restore_settings() 2014-10-14
    fontmap_dir = r'D:\MyFontmap'
    cmd2 = [gs_path, '-sDEVICE=pdfwrite', '-sOutputFile=%s' % pdf_file, '-dBATCH', '-dNOPAUSE', ps_file]
    # [SS] 2015-04-08
    if wx.Platform == "__WXMAC__":
        cmd2 = [gs_path, ps_file, '-o', pdf_file]
    if os.path.exists(pdf_file):
        os.remove(pdf_file)

    # 1.3.6.1 [SS] 2015-01-13
    execmessages += '\nAbcToPDF\n' + " ".join(cmd2)
    process = subprocess.Popen(cmd2, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags = creationflags)
    stdout_value, stderr_value = process.communicate()
    # 1.3.6.1 [SS] 2015-01-13
    execmessages += '\n' + stderr_value
    if os.path.exists(pdf_file):
        return pdf_file

# 1.3.6.4 [SS] 2015-07-10
gchordpat = re.compile('\"[^\"]+\"')
keypat    =  re.compile('([A-G]|[a-g]|)(#|b?)')
def test_for_guitar_chords (abccode):
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
        m = gchordpat.search(abccode,i)
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
def list_voices_in (abccode):
    ''' The function scans the entire abccode searching for V:
        and extracts the voice identifier (assuming it is not
        too long). A list of all the unique identifiers are
        returned.
    '''

    start = 0;
    voices = []
    while start != -1:
        loc = abccode.find('V:',start)
        if loc == -1:
            break
        segment = abccode[loc+2:loc+12]
        # in case of inline V: eg [V:3] replace ] with white space
        segment = segment.replace(']',' ')
        elemlist = segment.split()
        elem1 = elemlist[0]
        if elem1 not in voices:
            voices.append(elem1)
        start = loc+2

    return voices


# 1.3.6.4 [SS] 2015-07-03
def grab_time_signature (abccode):
    ''' The function detects the first time signature M: n/m in 
        abccode and returns [n, m].
    '''    
    fracpat = re.compile('(\d+)/(\d+)')
    loc = abccode.find('M:')
    meter = abccode[loc+2:loc+10]
    meter = meter.lstrip()
    if meter.find('C') >= 0 :
        return [4,4]
    m = fracpat.match(meter)
    if m:
        num = int(m.group(1))
        den = int(m.group(2))
    else:  #no M: in tune
        num = 4
        den = 4
    return [num, den]


# 1.3.6.4 [SS] 2015-07-03
def drum_intro (timesig):
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
def need_left_repeat (abccode):
    ''' Determine whether a left repeat |: is missing. If there
        are no right repeats (either :| or ::) then we do not need
        a left repeat. If a right repeat is found then we need
        to find a left repeat that appears before the first right
        repeat. Otherwise it is missing.
     '''
    loc1 = abccode.find(r':|')
    loc2 = abccode.find(r'::')
    if loc1 != -1 and loc2 != -1:
        loc = min(loc1,loc2)
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
def make_abc_introduction (abccode,voicelist):
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
def AbcToMidi(abc_code, header, cache_dir, settings, statusbar, tempo_multiplier, midi_file_name=None):
    global execmessages, visible_abc_code

    abc_code = process_abc_for_midi(abc_code, header, cache_dir, settings, tempo_multiplier)
    visible_abc_code = abc_code #p09 2014-10-22 [SS]

    tune_id = AbcTune.generate_tune_id(abc_code)

    if midi_file_name is None:
        midi_file_name = os.path.abspath(os.path.join(cache_dir, 'temp%s.midi' % tune_id))
        # midi_file_name = AbcTune.generate_temp_file_name(cache_dir, '.midi')
    midi_file = abc_to_midi(abc_code, settings, midi_file_name)
    # P09 2014-10-26 [SS]
    MyInfoFrame.update_text()

    # 1.3.6 2014-12-16 [SS]
    MyAbcFrame.update_text()

    # 1.3.6 [SS] 2014-12-08
    # time.sleep(0.2)
    if execmessages.find('Error') != -1:
        statusbar.SetStatusText(_('{0} reported some errors').format('Abc2midi'))
    elif execmessages.find('Warning') != -1:
        statusbar.SetStatusText(_('{0} reported some warnings').format('Abc2midi'))
    else:
        statusbar.SetStatusText('')

    if midi_file:
        return MidiTune(abc_code, midi_file, tune_id=tune_id)
    else:
        return None

# 1.3.6.3 [JWDJ] 2015-04-21 split up AbcToMidi into 2 functions: preprocessing (process_abc_for_midi) and actual midi generation (abc_to_midi)
def process_abc_for_midi(abc_code, header, cache_dir, settings, tempo_multiplier):

    ''' This function inserts extra lines in the abc tune controlling the assignment of musical instruments to the different voices
        per the instructions in the ABC Settings/abc2midi and voices. If the tune already contains these instructions, eg. %%MIDI program,
        %%MIDI chordprog, etc. then the function avoids changing these assignments by suppressing the output of the additional commands.
        Note that these assignments can also be embedded in the body of the tune using the instruction [I: MIDI = program 10] for
        examples see http://ifdo.ca/~seymour/runabc/abcguide/abc2midi_guide.html and click link [I:MIDI=...].
    '''
    global execmessages
    #print traceback.extract_stack(None, 5)



    ####   set all the control flags which determine which %%MIDI commands are written

    play_chords            = settings.get('play_chords')
    default_midi_program   = settings.get('midi_program')
    default_midi_chordprog = settings.get('midi_chord_program')
    default_midi_bassprog  = settings.get('midi_bass_program')
    # 1.3.6.4 [SS] 2015-06-07
    default_midi_chordvol  = settings.get('chordvol')
    default_midi_bassvol   = settings.get('bassvol')
    # 1.3.6.3 [SS] 2015-05-04
    default_tempo          = settings.get('bpmtempo')
    add_meta_data          = False
    #build the list of midi program to be used for each voice
    midi_program_ch_list=['midi_program_ch1', 'midi_program_ch2', 'midi_program_ch3', 'midi_program_ch4',
                          'midi_program_ch5', 'midi_program_ch6', 'midi_program_ch7', 'midi_program_ch8',
                          'midi_program_ch9', 'midi_program_ch10', 'midi_program_ch11', 'midi_program_ch12',
                          'midi_program_ch13', 'midi_program_ch14', 'midi_program_ch15', 'midi_program_ch16']
    default_midi_program_ch = []
    for channel in range(16):
        default_midi_program_ch.append(settings.get(midi_program_ch_list[channel]))

    #this flag is added just in case none would have been set but shouldn't be the case.
    if not default_midi_bassprog:
        default_midi_bassprog=default_midi_chordprog

    # verify if MIDI instructions are already present if yes, no extra command should be added

    add_midi_program_extra_line = True
    add_midi_volume_extra_line = True # 1.3.6.3 [JWDJ] 2015-04-21 added so that when abc contains instrument selection, the volume from the settings can still be used
    add_midi_gchord_extra_line = True
    add_midi_chordprog_extra_line = True
    add_midi_introduction = settings.get('midi_intro')  # 1.3.6.4 [SS] 2015-07-05

    if test_for_guitar_chords (abc_code) == False:
        add_midi_chordprog_extra_line  = False
        add_midi_gchord_extra_line = False

    # 1.3.6.3 [JWDJ] 2015-04-17 header was forgotten when checking for MIDI directives
    abclines = re.split('\r\n|\r|\n', header + abc_code)
    for i in range(len(abclines)):
        line = abclines[i]
        if line.startswith('%%MIDI program'):
            add_midi_program_extra_line=False
        elif line.startswith('%%MIDI control 7 '):
            add_midi_volume_extra_line=False
        elif line.startswith('%%MIDI gchord'):
            add_midi_gchord_extra_line=False
        elif line.startswith('%%MIDI chordprog') or line.startswith('%%MIDI bassprog') :
            add_midi_chordprog_extra_line=False
        if not (add_midi_program_extra_line or add_midi_volume_extra_line or add_midi_gchord_extra_line or add_midi_chordprog_extra_line): break




    #### create the abc_header which will be placed in front of the processed abc file
    # extra_lines is a list of all the MIDI commands to be put in abcheader

    extra_lines = []

    # build default list of midi_program
    # this is needed in case no instrument per voices where defined or in case option "use default one for all voices" is checked
    midi_program_ch=default_midi_program_ch
    if len(midi_program_ch)<16:
        for channel in range(len(midi_program_ch), 16+1):
            midi_program_ch.append([default_midi_program,64,64])

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

    #add extra instruction to play guitar chords
    if add_midi_gchord_extra_line:
        if play_chords:
            extra_lines.append('%%MIDI gchordon')
            # 1.3.6 [SS] 2014-11-26
            if settings['gchord'] != 'default':
                extra_lines.append('%%MIDI gchord '+ settings['gchord'])

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
    if settings.get('transposition', '0') != '0':
         extra_lines.append('%%MIDI transpose {0}'.format(settings['transposition']))

    # 1.3.6.3 [SS] 2015-05-04
    if default_tempo != 120:
        extra_lines.append('Q:1/4 = %s' % default_tempo)

    abcheader = os.linesep.join(extra_lines + [header.strip()])

    # 1.3.6.4 [SS] 2015-07-07
    voicelist = list_voices_in(abc_code)
    # 1.3.6.4 [SS] 2015-07-03
    if add_midi_introduction:
        midi_introduction = make_abc_introduction(abc_code,voicelist)



    ####  modify abc_code to add MIDI instruction just after voice definition
    # (because using channel only in header doesn't seem to allow association with voice

    abclines = re.split('\r\n|\r|\n', abc_code) # 1.3.6.3 [JWDJ] 2015-04-17 split abc_code without header

    # 1.3.7.0 [SS] 2016-01-05 
    # always add %%MIDI control 7 so user can control volume of melody
    #if add_midi_program_extra_line or add_midi_gchord_extra_line or add_midi_introduction:
    if True:  # 1.3.7.0 [SS] 2016-01-05 
        list_voice=[] # keeps track of the voices we have already seen
        new_abc_lines=[] # contains the new processed abc tune
        voice=0
        header_finished=False
        for i in range(len(abclines)):
            line = abclines[i]
            new_abc_lines.append(line)
            # do not take into account the definition present in the header (maybe it would be better... to be further analysed)
            if line.startswith('K:'):
                # 1.3.6.4 [SS] 2015-07-09
                if not header_finished and len(voicelist) == 0:
                    new_abc_lines.append('%%MIDI control 7 {0}'.format(int(settings['melodyvol'])))
                # 1.3.6.4 [SS] 2015-07-03
                if not header_finished and add_midi_introduction:
                    for j in range(len(midi_introduction)):
                        new_abc_lines.append(midi_introduction[j])
                header_finished=True
            # 1.3.6.3 [JWDJ] 2015-04-21
            if (line.startswith('V:') or line.startswith('[V:')) and header_finished:
                #extraction of the voice ID
                if line.startswith('V:'):
                    voice_def=line[2:].strip()
                else:
                    voice_def=line[3:].strip()
                voice_parse = voice_def.split()
                if voice_parse:
                    voice_ID = voice_parse[0].rstrip(']')
                    if voice_ID not in list_voice:
                        # 1.3.6.4 [SS] 2015-07-08
                        # if it is an inline voice, we are not want to include the following notes before
                        # specifying the %%MIDI parameters
                        if line.startswith('[V:'):
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
                        if line.startswith('[V:'):
                            new_abc_lines.append(removedline)
                        voice += 1

        abc_code = os.linesep.join([l.strip() for l in new_abc_lines])



    #### assemble everything together

    # 1.3.6.4 [SS] 2014-07-07 replacement for process_abc_code
    # we do not want any abcm2ps options added
    sections = []
    sections.append(abcheader.rstrip() + os.linesep)
    sections.append(abc_code)
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
    abclines = re.split('\r\n|\r|\n', abc_code) # take it apart again
    for i in range(len(abclines)):
        if abclines[i].startswith('X:'):
            line = abclines[i]
            del abclines[i]
            abclines.insert(0, line)
            break
    abc_code = os.linesep.join([l.strip() for l in abclines]) # put it back together


    #### for debugging
    #Write temporary abc_file (for debug purpose)
    #temp_abc_file =  os.path.abspath(os.path.join(cache_dir, 'temp_%s.abc' % hash)) 1.3.6 [SS] 2014-11-13
    temp_abc_file =  os.path.abspath(os.path.join(cache_dir, 'temp.abc')) # 1.3.6 [SS] 2014-11-13
    f = codecs.open(temp_abc_file, 'wb', 'UTF-8') #p08 patch
    f.write(abc_code)
    f.close()

    return abc_code



# 1.3.6.3 [JWDJ] 2015-04-21 split up AbcToMidi into 2 functions: preprocessing (process_abc_for_midi) and actual midi generation (abc_to_midi)
def abc_to_midi(abc_code, settings, midi_file_name):
    global execmessages
    if wx.Platform == "__WXMSW__":
        creationflags = win32process.CREATE_NO_WINDOW
    else:
        creationflags = 0

    if True: # p09 disable cache memory
    #if not os.path.exists(midi_file): #p09 disable cache
        abc2midi_path = settings.get('abc2midi_path')
        cmd = [abc2midi_path, '-', '-o', midi_file_name]
        cmd = add_abc2midi_options(cmd, settings)
        execmessages += '\nAbcToMidi\n' + " ".join(cmd)
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags = creationflags)
        stdout_value, stderr_value = process.communicate(input=(abc_code+os.linesep*2).encode('latin-1', 'ignore'))
        execmessages += '\n' + stdout_value + stderr_value
        if stdout_value:
            stdout_value = re.sub(r'(?m)(writing MIDI file .*\r?\n?)', '', stdout_value)
        if process.returncode != 0:
            # 1.3.7.0 [SS] 2016-01-06
            execmessages += '\n' + _('AbcToMidi exited abnormally (errorcode %#8x)') % (process.returncode & 0xffffffff)
            return None

        #if humanize:
        #    humanize_midi(midi_file, midi_file)
        #    pass
    return midi_file_name

# 1.3.6 [SS] 2014-11-24
def add_abc2midi_options(cmd,settings):
    if str2bool(settings['barfly']):
        cmd.append('-BF')
    if str2bool(settings['nofermatas']):
        cmd.append('-NFER')
    if str2bool(settings['nograce']):
        cmd.append('-NGRA')
    if str2bool(settings['nodynamics']):
        cmd.append('-NFNP')
    # 1.3.6.3 [SS] 2015-03-20
    if settings['tuning'] != '440':
        cmd.append('-TT %s' % settings['tuning'])
    return cmd


# 1.3.6 [SS] 2014-11-24
def str2bool(v):
    ''' converts a string to a boolean if necessary'''
    if type(v) == str:
        return v.lower() in ('yes', 'true', 't' ,'1')
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
    abc = re.sub(r'"[^_]([%s])"' % ''.join(decorations.keys()), lambda m: decorations[m.group(1)], abc)
    abc = abc.replace('"^tr"', 'T')
    return abc

def change_texts_into_chords(abc):
    ''' Change ABC fragments like "^G7" into "G7" by trying to identify strings that look like chords '''
    chord_types = 'm 7 m7 maj7 M7 6 m6 aug + aug7 dim dim7 9 m9 maj9 min Maj9 MAJ9 M9 11 dim9 sus sus4 Sus Sus4 sus9 7sus4 7sus9 5'.split()
    optional_chord_type = '(%s)?' % '|'.join(re.escape(c) for c in chord_types)
    return re.sub(r'(?<!\\)"[^_]([A-G][#b]? ?%s)(?<!\\)"' % optional_chord_type, r'"\1"', abc)

def NWCToXml(filepath, cache_dir, nwc2xml_path):
    nwc_file_path = os.path.join(cache_dir, 'temp_nwc.nwc')
    xml_file_path = os.path.join(cache_dir, 'temp_nwc.xml')
    if os.path.exists(xml_file_path):
        os.remove(xml_file_path)
    shutil.copy(filepath, nwc_file_path)

    if wx.Platform == "__WXMSW__":
        creationflags = win32process.CREATE_NO_WINDOW
    else:
        creationflags = 0
    if not nwc2xml_path:
        if wx.Platform == "__WXMSW__":
            nwc2xml_path = os.path.join(cwd, 'bin', 'nwc2xml.exe')
        elif wx.Platform == "__WXMAC__":
            nwc2xml_path = os.path.join(cwd, 'bin', 'nwc2xml')
        else:
            nwc2xml_path = 'nwc2xml'

    #cmd = [nwc2xml_path, '--charset=ISO-8859-1', nwc_file_path]
    cmd = [nwc2xml_path, nwc_file_path]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags = creationflags)
    stdout_value, stderr_value = process.communicate()

    if not os.path.exists(xml_file_path) or process.returncode != 0:
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
        return (minPage,maxPage,fromPage,toPage)

    def OnPrintPage(self, page):
        dc = self.GetDC()

        #-------------------------------------------
        # One possible method of setting scaling factors...

        svg = open(self.svg_files[page-1], 'rb').read()
        #new versions of abcm2ps adds a suffix 'in' to width and height
        #m = re.search(r'width="(\d+)"\s+height="(\d+)"', svg)
        #width, height = int(m.group(1)), int(m.group(2))

        m = re.search(r'width="(\d+[.]?\d*)(?:in"|")\s+height="(\d+[.]?\d*)(?:in"|")', svg)
        if re.search('^\d+$', m.group(1)):
            width = int(m.group(1))
        else:
            width = float(m.group(1))*72
        if re.search('^\d+$', m.group(2)):
            height = int(m.group(2))
        else:
            height = float(m.group(2))*72 # The factor 72 changes inches to pixels.

        maxX = width
        maxY = height

        # Let's have at least 0 device units margin
        marginX = 0
        marginY = 0

        # Add the margin to the graphic size
        maxX += 2 * marginX
        maxY += 2 * marginY

        # Get the size of the DC in pixels
        (w, h) = dc.GetSizeTuple()

        # Calculate a suitable scaling factor
        scaleX = float(w) / maxX
        scaleY = float(h) / maxY

        # Use x or y scaling factor, whichever fits on the DC
        actualScale = min(scaleX, scaleY)

        # Calculate the position on the DC for centering the graphic
        posX = (w - (width * actualScale)) / 2.0
        posY = (h - (height * actualScale)) / 2.0
        posY = 0

        # Set the scale and origin
        dc.SetUserScale(actualScale, actualScale)
        dc.SetDeviceOrigin(int(posX), int(posY))

        #-------------------------------------------
        if wx.Platform in ("__WXMSW__", "__WXMAC__") and (not self.painted_on_screen or True):
            # special case for windows since it doesn't support creating a GraphicsContext from a PrinterDC:
            dc.SetUserScale(actualScale/self.zoom, actualScale/self.zoom)
            r = SvgRenderer(self.can_draw_sharps_and_flats)
            r.zoom = self.zoom
            r.set_svg(svg)
            dc.DrawBitmap(r.buffer, 0, 0)
        else:
            r = SvgRenderer(self.can_draw_sharps_and_flats)
            r.zoom = 1.0
            r.set_svg(svg, dc)

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
            tune_id = None
            svg_files, error = [], u''
            try:
                abc_code, abc_header = task
                if not 'K:' in abc_code:
                    raise Exception('K: field is missing')
                else:
                    # 1.3.6.3 [JWDJ] splitted pre-processing abc and generating svg
                    abc_code = process_abc_code(self.settings, abc_code, abc_header, minimal_processing=not self.settings.get('reduced_margins', True))
                    tune_id = AbcTune.generate_tune_id(abc_code)
                    file_name = os.path.abspath(os.path.join(self.cache_dir, 'temp-%s-.svg' % tune_id))
                    # file_name = AbcTune.generate_temp_file_name(self.cache_dir, '-.svg', replace_ending='-001.svg')
                    svg_files, error = abc_to_svg(abc_code, self.cache_dir, self.settings, target_file_name=file_name)
            except Abcm2psException as e:
                # if abcm2ps crashes, then wait at least 10 seconds until next invocation
                svg_files, error = [], unicode(e)
                # wx.PostEvent(self.notify_window, MusicUpdateDoneEvent(-1, (svg_files, error)))
                # time.sleep(10.0)
                # continue
                error_msg = ''.join(traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))
                print error_msg
                pass
            except Exception as e:
                svg_files, error = [], unicode(e)
                error_msg = ''.join(traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))
                print error_msg
                pass
            svg_tune = SvgTune(abc_code, svg_files, error, tune_id=tune_id)
            wx.PostEvent(self.notify_window, MusicUpdateDoneEvent(-1, svg_tune))

    # 1.3.6.2 [JWdJ] 2015-02 rewritten
    def ConvertAbcToSvg(self, abc_code, abc_header, clear_queue = True):
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
    process = subprocess.Popen(cmd,shell=False,stdin=None,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=creationflags)
    stdout_value, stderr_value = process.communicate()
    execmessages += '\n'+stderr_value + stdout_value
    return

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
            c = [midiplayer_path,  midi_file] + midiplayer_parameters
            #note this is not the same as
            #c = [midiplayer_path,  midi_file, midiplayer_parameters]
            try:
                start_process(c)
            except Exception as e:
                print e
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
    def __init__(self, notify_window, midi_in_device_ID, midi_out_device_ID=None, metre_1=3, metre_2=4, bpm = 70):
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
        self.tick1 = wx.Sound(os.path.join(cwd, 'sound', 'tick1.wav'))
        self.tick2 = wx.Sound(os.path.join(cwd, 'sound', 'tick2.wav'))

    def timedelta_microseconds(self, td):
        return td.seconds*1000000 + td.microseconds

    @property
    def beat_duration(self):
        return 1000000 * 60/self.bpm

    def run(self):
        #beat_duration = 1000000 * 60/self.bpm  # unit is microseconds
        self.is_running = True
        NOTE_ON = 0x09
        NOTE_OFF= 0x08
        i = 0
        noteon_time = {}
        start_time = datetime.now()
        last_tick = datetime.now()
        wx.CallAfter(self.tick1.Play)
        time.sleep(0.002)
        try:
            while not self._want_abort:
                while not self.midi_in.Poll() and not self._want_abort:
                    time.sleep(0.00025)
                    if self.timedelta_microseconds(datetime.now() - start_time) / self.beat_duration > i:
                        last_tick = datetime.now()
                        i += 1
                        if i % self.metre_1 == 0:
                            wx.CallAfter(self.tick1.Play)
                        else:
                            wx.CallAfter(self.tick2.Play)
                time_offset = self.timedelta_microseconds(datetime.now() - start_time)
                if self.midi_in.Poll():
                    data = self.midi_in.Read(1) # read only 1 message at a time
                    if self.midi_out is not None:
                        self.midi_out.Write(data)
                    cmd = data[0][0][0] >> 4
                    midi_note = data[0][0][1]
                    if cmd == NOTE_ON:
                        noteon_time[midi_note] = time_offset
                        ##print 'note-on', midi_note, float(time_offset)/beat_duration
                    elif cmd == NOTE_OFF and midi_note in noteon_time:
                        start = float(noteon_time[midi_note]) / self.beat_duration
                        end = float(time_offset) / self.beat_duration
                        self.notes.append([midi_note, start, end])
                        ##print 'note-off', midi_note, float(time_offset)/beat_duration

        finally:
            self.midi_in.Close()
            if self.midi_out is not None:
                self.midi_out.Close()
            self.is_running = False
        self.quantize()
        wx.PostEvent(self._notify_window, RecordStopEvent(-1, self.notes))

    def quantize_swinged_16th(self, start_time):
        quantize_time = 0.25  # 1/16th
        return round(start_time / quantize_time) * quantize_time

        # 1.3.6.2 [JWdJ] 2015-02 commented out folllowing lines
        # because they are never executed
        # beats = int(start_time / 1.0)
        # offset_from_beat = start_time - beats
        # len_16th = 0.25 # 1/4 of a beat's duration
        # positions_for_16ths = [0, len_16th*0.9, len_16th*2*0.9, len_16th*3, len_16th*4]
        # best_pos = 0
        # for pos in positions_for_16ths:
        #     if abs(offset_from_beat - pos) < abs(offset_from_beat - best_pos):
        #         best_pos = pos
        # return beats * 1.0 + best_pos

    def quantize_triplet(self, notes):
        if len(notes) < 4:
            return False

        tolerance = 0.07
        first_note_start = round(notes[0][1] / 0.25) * 0.25  #self.quantize_swinged_16th(notes[0][1])

        #durations = [n[2] - n[1] for n in notes[:3]]
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
        quantize_time = 0.25  # 1/16th

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
            ##print end, int(end / bar_length), bar_length
            end = (int(end / bar_length) + 1) * bar_length     # set the end to be at the end of the bar
            ##print end
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
        wx.Dialog.__init__(self, parent, -1, _('Generate incipits file...'), wx.DefaultPosition, wx.Size(530, 260))
        self.SetBackgroundColour(wx.Colour(245, 244, 235))
        border = 4
        sizer = box1 = rcs.RowColSizer()
        lb1 = wx.StaticText(self, -1, _('Number of bars to extract:'))
        lb2 = wx.StaticText(self, -1, _('Maximum number of repeats to extract:'))
        lb3 = wx.StaticText(self, -1, _('Maximum number of titles/subtitles to extract:'))
        lb4 = wx.StaticText(self, -1, _('Fields to sort by (eg. T):'))
        lb5 = wx.StaticText(self, -1, _('Number of rows per column:'))
        self.edNumBars       = wx.SpinCtrl(self, -1, "", min=1, max=10, initial=self.settings.get('incipits_numbars', 2))
        self.edNumRepeats    = wx.SpinCtrl(self, -1, "", min=1, max=10, initial=self.settings.get('incipits_numrepeats', 1))
        self.edNumTitles     = wx.SpinCtrl(self, -1, "", min=0, max=10, initial=self.settings.get('incipits_numtitles', 1))
        self.edSortFields    = wx.TextCtrl(self, -1, self.settings.get('incipits_sortfields', ''))
        self.chkTwoColumns   = wx.CheckBox(self, -1, _('&Two column output'))
        self.edNumRows       = wx.SpinCtrl(self, -1, "", min=1, max=40, initial=self.settings.get('incipits_rows', 10))
        self.chkTwoColumns.SetValue(self.settings.get('incipits_twocolumns', True))
        for c in [self.edNumBars, self.edNumRepeats, self.edNumTitles, self.edNumRows, self.edSortFields]:
            c.SetValue(c.GetValue()) # this seems to be needed on OSX

        sizer.Add(lb1,                  row=0, col=0, flag=wx.wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(self.edNumBars,       row=0, col=1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(lb2,                  row=1, col=0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(self.edNumRepeats,    row=1, col=1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(lb3,                  row=2, col=0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(self.edNumTitles,     row=2, col=1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(lb4,                  row=3, col=0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(self.edSortFields,    row=3, col=1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(self.chkTwoColumns,   row=4, col=1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(lb5,                  row=5, col=0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(self.edNumRows,       row=5, col=1, flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        # ok, cancel buttons
        self.ok = wx.Button(self, -1,     _('&Ok'))
        self.cancel = wx.Button(self, -1, _('&Cancel'))
        self.ok.SetDefault()
        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        # 1.3.6.1 [JWdJ] 2015-01-30 Swapped next two lines so OK-button comes first (OK Cancel)
        btn_box.Add(self.ok, wx.ID_OK, flag=wx.ALIGN_RIGHT)
        btn_box.Add(self.cancel, wx.ID_CANCEL, flag=wx.ALIGN_RIGHT)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(box1,    flag=wx.ALL | wx.EXPAND, border=10)
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


class NewTuneFrame(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, _('Add new tune'), wx.DefaultPosition, wx.Size(230, 80))
        self.SetBackgroundColour(wx.Colour(245, 244, 235))
        border = 4
        sizer = wx.GridBagSizer(5, 5)
        font_size = get_normal_fontsize() # 1.3.6.3 [JWDJ] one function to set font size

        #fields = ['K: Key signature',
        #          'M: Metre',
        #          'L: Default note length',
        #          'T: Title',
        #          ]
        #fields = [('X:', _('Tune index number')),
        #          ('T:', _('Title')),
        #          ('K:', _('Key')),
        #          ('M:', _('Metre')),
        #          ('L:', _('Default note length')),
        #          ('C:', _('Composer')),
        #          ('O:', _('Origin')),
        #          ]

        sizer = rcs.RowColSizer()
        for i, field in enumerate(fields):
            sizer.Add(wx.StaticText(self, -1, field),  row=i, col=0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
            sizer.Add(wx.TextCtrl(self, -1),           row=i, col=1, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
            #sizer.Add(wx.StaticText(self, -1, expl),   row=i, col=2, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        box1 = wx.StaticBoxSizer(wx.StaticBox(self, -1, _("Additional command line parameters to abcm2ps")), wx.VERTICAL)
        box1.Add(sizer, flag=wx.ALL | wx.EXPAND, border=border)
        self.sizer = box1
        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)
        self.Centre()
        self.sizer.Fit(self)


#p09 Abcm2psSettingsFrame dialog box has been replaced with a
#tabbed notebook so we have lots of room for adding more options.
#2014-10-14
class MyNoteBook(wx.Frame):
    ''' Settings Notebook '''
    def __init__(self, settings, statusbar):
        wx.Frame.__init__(self, wx.GetApp().TopWindow, wx.ID_ANY, _("Abc settings"),style=wx.DEFAULT_FRAME_STYLE,name='settingsbook')
        # Add a panel so it looks the correct on all platforms
        p = wx.Panel(self)
        nb = wx.Notebook(p)
        # 1.3.6.4 [SS] 2015-05-26 added statusbar
        abcsettings = AbcFileSettingsFrame(nb,settings,statusbar)
        chordpage = MyChordPlayPage(nb,settings)
        voicepage = MyVoicePage(nb,settings)
        # 1.3.6.1 [SS] 2015-02-02
        abcm2pspage = MyAbcm2psPage(nb,settings,abcsettings)
        xmlpage    = MyXmlPage(nb,settings)
        nb.AddPage(abcm2pspage,"Abcm2ps")
        nb.AddPage(chordpage,"Abc2midi")
        nb.AddPage(voicepage,"Voices")
        nb.AddPage(xmlpage,"Xml")
        nb.AddPage(abcsettings,"File Settings")


        sizer = wx.BoxSizer()
        sizer.Add(nb,1,wx.ALL|wx.EXPAND)
        p.SetSizer(sizer)
        sizer.Fit(self)


class AbcFileSettingsFrame(wx.Panel):
    # 1.3.6.4 [SS] 2015-05-26 added statusbar
    def __init__(self, parent, settings, statusbar):
        wx.Panel.__init__(self, parent)
        # -1, _('ABC settings'), wx.DefaultPosition, wx.Size(530, 500))
        self.settings = settings
        self.statusbar = statusbar
        self.SetBackgroundColour(wx.Colour(245, 244, 235))
        border = 4

        PathEntry = namedtuple('PathEntry', 'name display_name tooltip add_default')

        # 1.3.6.3 [JWDJ] 2015-04-27 replaced TextCtrl with ComboBox for easier switching of versions
        self.needed_path_entries = [
            PathEntry('abcm2ps', _('abcm2ps executable:'), _('This executable is used to display the music'), True),
            PathEntry('abc2midi', _('abc2midi executable:'), _('This executable is used to make the midi file'), True),
            PathEntry('abc2abc', _('abc2abc executable:'), _('This executable is used to transpose the music'), True),
            # 1.3.6.4 [SS] 2015-06-22
            PathEntry('midi2abc', _('midi2abc executable:'), _('This executable is used to disassemble the output midi file'), True),
            PathEntry('gs', _('ghostscript executable:'), _('This executable is used to create PDF files'), False),
            PathEntry('nwc2xml', _('nwc2xml executable:'),_('For NoteWorthy Composer - Windows only'), False),
            PathEntry('midiplayer', _('midiplayer:'), _('Your preferred MIDI player'), False)
        ]

        if wx.Platform == "__WXMSW__":
            self.exe_file_mask = '*.exe'
        else:
            self.exe_file_mask = '*'

        self.restore_settings = wx.Button(self, -1, _('Restore settings')) # 1.3.6.3 [JWDJ] 2015-04-25 renamed
        check_toolTip = _('Restore default file paths to abcm2ps, abc2midi, abc2abc, ghostscript when blank')
        self.restore_settings.SetToolTip(wx.ToolTip(check_toolTip))

        # 1.3.6.3 [SS] 2015-04-29
        extraplayerparam = wx.StaticText(self,-1, _("Extra MIDI player parameters"))
        self.extras = wx.TextCtrl(self,-1,size=(200,22))

        sizer = rcs.RowColSizer()
        if wx.Platform == "__WXMAC__":
            sizer.Add(wx.StaticText(self, -1, _('File paths to required executables') + ':'), row=0, col=0, colspan=2, flag=wx.ALL, border=border)
            r = 1
        else:
            r = 0

        self.browsebutton_to_control = {}
        self.control_to_name = {}
        for entry in self.needed_path_entries:
            setting_name = '%s_path' % entry.name
            current_path = self.settings.get(setting_name, '')
            #if wx.Platform == "__WXMAC__":
            #    control = wx.TextCtrl(self)
            #else:
            setting_name_choices = '%s_path_choices' % entry.name
            path_choices = self.settings.get(setting_name_choices, '').split('|')
            path_choices = self.keep_existing_paths(path_choices)
            path_choices = self.append_exe(current_path, path_choices)
            if entry.add_default:
                path_choices = self.append_exe(self.get_default_path(entry.name), path_choices)
            control = wx.ComboBox(self, -1, choices=path_choices, style=wx.CB_DROPDOWN)
            # [SS] 1.3.6.4 2015-12-23
            if current_path:
                control.SetValue(current_path)
            control.Bind(wx.EVT_TEXT, self.OnChangePath, control)

            self.control_to_name[control] = entry.name
            if entry.tooltip:
                control.SetToolTip(wx.ToolTip(entry.tooltip))

            browse_button = wx.Button(self, -1, _('Browse...'))
            self.browsebutton_to_control[browse_button] = control
            sizer.Add(wx.StaticText(self, -1, entry.display_name), row=r, col=0, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
            sizer.Add(control, row=r, col=1,  flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
            sizer.Add(browse_button, row=r, col=2,  flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

            browse_button.Bind(wx.EVT_BUTTON, self.OnBrowse, browse_button)

            r += 1

        sizer.AddGrowableCol(1)

        if wx.Platform == "__WXMAC__":
            box2 = sizer
        else:
            box2 = wx.StaticBoxSizer(wx.StaticBox(self, -1, _("File paths to required executables")), wx.VERTICAL)
            box2.Add(sizer, flag=wx.ALL | wx.EXPAND)

        sizer = wx.GridBagSizer(5, 5)
        font_size = get_normal_fontsize() # 1.3.6.3 [JWDJ] one function to set font size

        # [SS] 1.3.6.3 2015-04-29
        self.gridsizer = wx.FlexGridSizer(0,4,2,2)
        self.gridsizer.Add(extraplayerparam,0,0,0,0)
        self.gridsizer.Add(self.extras,0,0,0,0)

        self.chkIncludeHeader = wx.CheckBox(self, -1, _('Include file header when rendering tunes'))



        # build settings dialog with the previously defined box
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(box2, flag=wx.ALL | wx.EXPAND, border=10)
        # 1.3.6.1 [SS] 2015-01-28
        #self.sizer.Add(box1, flag=wx.ALL | wx.EXPAND, border=10)
        self.sizer.Add(self.chkIncludeHeader, flag=wx.ALL | wx.EXPAND, border=10)
        self.sizer.Add(self.gridsizer, flag=wx.ALL | wx.EXPAND, border=10)
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
        self.extras.Bind(wx.EVT_TEXT, self.On_extra_midi_parameters,self.extras)

        self.restore_settings.Bind(wx.EVT_BUTTON, self.OnRestoreSettings, self.restore_settings)

    def OnBrowse(self, evt):
        control = self.browsebutton_to_control[evt.EventObject]
        wildcard = self.exe_file_mask
        default_dir = os.path.dirname(control.GetValue()) # 1.3.6.3 [JWDJ] uses current folder as default
        dlg = wx.FileDialog(
                self, message=_("Choose a file"), defaultDir=default_dir, defaultFile="", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.CHANGE_DIR )
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
        if setting_name == 'midiplayer_path':
            app = wx.GetApp()
            app.frame.update_play_button() # 1.3.6.3 [JWDJ] 2015-04-21 playbutton enabling centralized

    def On_Chk_IncludeHeader(self,event):
        self.settings['abc_include_file_header'] = self.chkIncludeHeader.GetValue()

    # [SS] 2015-04-29
    def On_extra_midi_parameters(self,event):
        self.settings['midiplayer_parameters'] = self.extras.GetValue()

    def OnRestoreSettings(self,event):
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
            frame.book.Show(False)
            frame.book.Destroy()
            frame.book = MyNoteBook(self.settings)
            frame.book.Show()

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
    def __init__(self,parent,settings):
        wx.Panel.__init__(self,parent)
        self.SetBackgroundColour(wx.Colour(245, 244, 235)) # 1.3.6.3 [JWDJ] 2014-04-28 same background for all tabs
        gridsizer   = wx.FlexGridSizer(20,4,2,2)
        #self.program = ''
        # midi_box to set default instrument for playback
        midi_box = rcs.RowColSizer()
        border = 4
        self.settings = settings

        # 1.3.6.4 [SS] 2015-05-28 shrunk width from 250 to 200
        self.chkPlayChords = wx.CheckBox(self, -1, _('Play chords'))
        self.cmbMidiProgram = wx.ComboBox(self, -1, choices=general_midi_instruments, size=(200, 26), style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.cmbMidiChordProgram = wx.ComboBox(self, -1, choices=general_midi_instruments, size=(200, 26), style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.cmbMidiBassProgram = wx.ComboBox(self, -1, choices=general_midi_instruments, size=(200, 26), style=wx.CB_DROPDOWN | wx.CB_READONLY)
        #1.3.6 [SS] 2014-11-15

        #1.3.6.4 [SS] 2015-06-10
        self.sliderbeatsperminute = wx.Slider(self, value=120, minValue=60, maxValue=240,
                                size=(80, -1), style=wx.SL_HORIZONTAL)
        self.slidertranspose=wx.Slider(self, value=0, minValue=-11, maxValue=11,
                                size=(80, -1), style=wx.SL_HORIZONTAL)
        self.slidertuning=wx.Slider(self, value=440, minValue=415, maxValue=466,
                                size=(80, -1), style=wx.SL_HORIZONTAL)
        self.beatsperminutetxt = wx.StaticText(self,-1," ")
        self.transposetxt      = wx.StaticText(self,-1," ")
        self.tuningtxt         = wx.StaticText(self,-1," ")

        #1.3.6.4 [SS] 2015-07-08
        self.sliderVol=wx.Slider(self, value=96, minValue=0, maxValue=127,
                                size=(128, -1), style=wx.SL_HORIZONTAL)
        self.Voltxt = wx.StaticText(self,-1," ")
        #1.3.6.4 [SS] 2015-06-07
        self.sliderChordVol=wx.Slider(self, value=96, minValue=0, maxValue=127,
                                size=(128, -1), style=wx.SL_HORIZONTAL)
        self.ChordVoltxt = wx.StaticText(self,-1," ")
        self.sliderBassVol=wx.Slider(self, value=96, minValue=0, maxValue=127,
                                size=(128, -1), style=wx.SL_HORIZONTAL)
        self.BassVoltxt = wx.StaticText(self,-1," ")


        #1.3.6 [SS] 2014-11-21
        self.nodynamics = wx.CheckBox(self, -1, _('Ignore Dynamics'))
        self.nofermatas = wx.CheckBox(self, -1, _('Ignore Fermatas'))
        self.nograce    = wx.CheckBox(self, -1, _('No Grace Notes'))
        self.barfly     = wx.CheckBox(self, -1, _('Barfly Mode'))
        self.midi_intro = wx.CheckBox(self, -1, _('Count in'))

        #1.3.6 [SS] 2014-11-26
        gchordtxt = wx.StaticText(self,-1, _("gchord pattern"))
        self.gchordcombo = wx.ComboBox(self,-1,'default',(-1,-1),(128,-1),[],wx.CB_DROPDOWN)
        gchordchoices = ['default','f','fzfz','gi','gihi','f4c2','ghihgh','g2hg2h']
        self.SetGchordChoices(gchordchoices)


        midi_box.Add(wx.StaticText(self, -1, _('Instrument for playback: ')), row=0, col=0, flag=wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.sliderVol, row=0, col=2,flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL,border=border)
        midi_box.Add(self.Voltxt,row=0,col=3,flag=wx.ALL| wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.cmbMidiProgram, row=0, col=1,  flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(wx.StaticText(self, -1, _("Instrument for chord's playback: ")), row=1, col=0, flag=wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.cmbMidiChordProgram, row=1, col=1,  flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.sliderChordVol,row=1,col=2,flag=wx.ALL| wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.ChordVoltxt,row=1,col=3,flag=wx.ALL| wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(wx.StaticText(self, -1, _("Instrument for bass chord's playback: ")), row=2, col=0, flag=wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.cmbMidiBassProgram, row=2, col=1,  flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.sliderBassVol,row=2,col=2,flag=wx.ALL| wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.BassVoltxt,row=2,col=3,flag=wx.ALL| wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
 
        # 1.3.6.4 [SS] 2015-06-10
        midi_box.Add(wx.StaticText(self, -1, _("Default Tempo: ")), row=3, col=0, flag=wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.sliderbeatsperminute,row=3, col = 1, flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border) 
        midi_box.Add(self.beatsperminutetxt,row=3, col = 2, flag= wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL,border=border) 
        midi_box.Add(wx.StaticText(self, -1, _("Transposition: ")), row=4, col=0, flag=wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.slidertranspose,row=4, col = 1, flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.transposetxt,row=4, col = 2, flag= wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL,border=border) 
        midi_box.Add(wx.StaticText(self, -1, _("Tuning: ")), row=5, col=0, flag=wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.slidertuning,row=5, col = 1, flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.tuningtxt,row=5, col = 2, flag= wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL,border=border) 

        midi_box.Add(self.chkPlayChords, row=6, col=0, flag=wx.ALL | wx.EXPAND,border=border)
        midi_box.Add(self.nodynamics, row=6,col=1,flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.nofermatas, row=7,col=0,flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.nograce, row=7,col=1,flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.barfly, row=8,col=0,flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.midi_intro, row=8,col=1,flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(gchordtxt, row=9,col=0,flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)
        midi_box.Add(self.gchordcombo, row=9,col=1,flag=wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, border=border)

        self.chkPlayChords.SetValue(self.settings.get('play_chords', False))
        self.slidertranspose.SetValue(self.settings.get('transposition',0))
        self.transposetxt.SetLabel(str(self.settings.get('transposition','0')))
        self.slidertuning.SetValue(self.settings.get('tuning',440))
        self.tuningtxt.SetLabel(str(self.settings.get('tuning','440')))
        self.sliderVol.SetValue(int(self.settings.get('melodyvol',96)))
        self.Voltxt.SetLabel(str(self.settings.get('melodyvol','96')))
        self.sliderChordVol.SetValue(int(self.settings.get('chordvol',96)))
        self.ChordVoltxt.SetLabel(str(self.settings.get('chordvol','96')))
        self.sliderBassVol.SetValue(int(self.settings.get('bassvol',96)))
        self.BassVoltxt.SetLabel(str(self.settings.get('bassvol','96')))
        self.nodynamics.SetValue(self.settings.get('nodynamics',False))
        self.nofermatas.SetValue(self.settings.get('nofermatas',False))
        self.nograce.SetValue(self.settings.get('nograce',False))
        self.barfly.SetValue(self.settings.get('barfly',True))
        # 1.3.6.4 [SS[ 2015-07-05
        self.midi_intro.SetValue(self.settings.get('midi_intro',False))
        # 1.3.6.4 [SS] 2015-06-10
        self.sliderbeatsperminute.SetValue(int(self.settings.get('bpmtempo',120)))
        self.beatsperminutetxt.SetLabel(str(self.settings.get('bpmtempo','120')))

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

        #1.3.6 [SS] 2014-11-15
        #self.chkSameInstrumentVoice.SetValue(self.settings.get('one_instrument_only', True))
        #update the enabling status of the button depending on the previously saved information
        #if self.settings.get('one_instrument_only', True):
            #self.midiprogramchannelbtn1.Disable()
        #else:
            #self.midiprogramchannelbtn1.Enable()
        try:
            self.cmbMidiProgram.Select(self.settings.get('midi_program', 1))
            self.cmbMidiChordProgram.Select(self.settings.get('midi_chord_program', 25))
            self.cmbMidiBassProgram.Select(self.settings.get('midi_bass_program', 25))
        except:
            pass

        #1.3.6 [SS] 2014-11-24
        #self.chkSameInstrumentVoice.Bind(wx.EVT_CHECKBOX, self.ShowOrHideInstrumentPerVoice)
        self.chkPlayChords.Bind(wx.EVT_CHECKBOX,self.OnPlayChords)
        self.nodynamics.Bind(wx.EVT_CHECKBOX,self.OnNodynamics)
        self.nofermatas.Bind(wx.EVT_CHECKBOX,self.OnNofermatas)
        self.nograce.Bind(wx.EVT_CHECKBOX,self.OnNograce)
        self.barfly.Bind(wx.EVT_CHECKBOX,self.OnBarfly)
        self.sliderbeatsperminute.Bind(wx.EVT_SCROLL, self.OnBeatsPerMinute)
        self.slidertranspose.Bind(wx.EVT_SCROLL, self.OnTranspose)
        self.slidertuning.Bind(wx.EVT_SCROLL, self.OnTuning)
        #1.3.6.4 [SS] 2015-06-07
        self.sliderChordVol.Bind(wx.EVT_SCROLL, self.OnChordVol)
        self.sliderBassVol.Bind(wx.EVT_SCROLL, self.OnBassVol)
        #1.3.6.4 [SS] 2015-07-05
        self.midi_intro.Bind(wx.EVT_CHECKBOX,self.OnMidiIntro)
        #1.3.6.4 [SS] 2015-07-09
        self.sliderVol.Bind(wx.EVT_SCROLL,self.OnMelodyVol)

        #1.3.6 [SS] 2014-11-26
        self.gchordcombo.Bind(wx.EVT_COMBOBOX,self.OnGchordSelection,self.gchordcombo)
        self.gchordcombo.Bind(wx.EVT_TEXT,self.OnGchordSelection,self.gchordcombo)
        self.gchordcombo.SetToolTip(wx.ToolTip(_('for chord C:\nf --> C,,  c -> [C,E,G] z --> rest\ng --> C, h --> E, i --> G, j--> B,\nG --> C,, H --> E,, I --> G,,\nJ --> B,')))


        #1.3.6 [SS] 2014-11-15
        self.cmbMidiProgram.Bind(wx.EVT_COMBOBOX,self.OnMidi_Program)
        self.cmbMidiChordProgram.Bind(wx.EVT_COMBOBOX,self.On_midi_chord_program)
        self.cmbMidiBassProgram.Bind(wx.EVT_COMBOBOX,self.On_midi_bass_program)

        #midi_box.AddGrowableCol(1)
        self.SetSizer(midi_box)
        self.SetAutoLayout(True)
        #midi_box.SetSizer()
        self.Fit()
        self.Layout()




    def OnPlayChords(self,evt):
        self.settings['play_chords']           = self.chkPlayChords.GetValue()

# 1.3.6 [SS] 2014-11-24
    def OnNodynamics(self,evt):
        self.settings['nodynamics']            = self.nodynamics.GetValue()

    def OnNofermatas(self,evt):
        self.settings['nofermatas']            = self.nofermatas.GetValue()

    def OnNograce(self,evt):
        self.settings['nograce']               = self.nograce.GetValue()

    def OnBarfly(self,evt):
        self.settings['barfly']                = self.barfly.GetValue()

# 1.3.6.4 [SS] 2015-07-05
    def OnMidiIntro(self,evt):
        self.settings['midi_intro']            = self.midi_intro.GetValue()

    def OnMidi_Program(self,evt):
        self.settings['midi_program']          = self.cmbMidiProgram.GetSelection()

    def On_midi_chord_program(self,evt):
        self.settings['midi_chord_program']    = self.cmbMidiChordProgram.GetSelection()

    def On_midi_bass_program(self,evt):
        self.settings['midi_bass_program']     = self.cmbMidiBassProgram.GetSelection()

# 1.3.6 [SS] 2014-11-26
    def SetGchordChoices(self,choices):
        ''' sets the gchord string choices in the gchord combo widget '''
        self.gchordcombo.Clear()
        for item in choices:
            self.gchordcombo.Append(item)

    def OnGchordSelection(self,evt):
        ''' saves the gchord string selection '''
        self.settings['gchord']  =   self.gchordcombo.GetValue()

# 1.3.6.4 [SS] 2015-06-10
    def OnBeatsPerMinute(self, evt):
        self.settings['bpmtempo'] = str(self.sliderbeatsperminute.GetValue())
        self.beatsperminutetxt.SetLabel(str(self.settings['bpmtempo']))


# 1.3.6.3 [SS] 2015-03-19
    def OnTranspose(self,evt):
        self.settings['transposition'] = self.slidertranspose.GetValue()
        self.transposetxt.SetLabel(str(self.settings['transposition']))

# 1.3.6.3 [SS] 2015-03-19
    def OnTuning(self,evt):
        self.settings['tuning'] = self.slidertuning.GetValue()
        self.tuningtxt.SetLabel(str(self.settings['tuning']))

#1.3.6.4 [SS] 2015-06-07
    def OnChordVol(self,evt):
        self.settings['chordvol'] = self.sliderChordVol.GetValue()
        self.ChordVoltxt.SetLabel(str(self.sliderChordVol.GetValue()))

#1.3.6.4 [SS] 2015-06-07
    def OnBassVol(self,evt):
        self.settings['bassvol'] = self.sliderBassVol.GetValue()
        self.BassVoltxt.SetLabel(str(self.sliderBassVol.GetValue()))

#1.3.6.4 [SS] 2015-07-09
    def OnMelodyVol(self,evt):
        melodyvol = self.sliderVol.GetValue()
        self.settings['melodyvol'] = melodyvol
        self.Voltxt.SetLabel(str(melodyvol))
        
        




# New panel to be able to set MIDI settings for the different voices
class MyVoicePage(wx.Panel):
    def __init__(self, parent, settings):
        wx.Panel.__init__(self,parent)
        self.settings = settings

        self.SetBackgroundColour(wx.Colour(245, 244, 235))
        border = 4
        channel = 1

        # definition of box for voice 1 to 16 (MIDI is limited to 16 channels)
        midi_box_ch_list={}
        self.cmbMidiProgramCh_list={}
        self.sldMidiControlVolumeCh_list={}
        self.textValueMidiControlVolumeCh_list={}
        self.sldMidiControlPanCh_list={}
        self.textValueMidiControlPanCh_list={}
        midi_box = rcs.RowColSizer()
        midi_box.Add(wx.StaticText(self, -1, _('Default instrument:')), row=0, col=1, flag=wx.ALIGN_CENTER_VERTICAL, border=10)
        midi_box.Add(wx.StaticText(self, -1, _('Main Volume:')), row=0, col=3, colspan=2, flag=wx.ALIGN_CENTER_VERTICAL, border=10)
        midi_box.Add(wx.StaticText(self, -1, _('L/R Balance:')), row=0, col=6, colspan=2, flag=wx.ALIGN_CENTER_VERTICAL, border=10)

        # For each of the 16th voice, instrument, volume and balance can be set separately
        for channel in range(1, 16+1):
            self.cmbMidiProgramCh_list[channel]=wx.ComboBox(self, -1, choices=general_midi_instruments, size=(200, 26),
                                                            style=wx.CB_READONLY) #wx.CB_DROPDOWN |
            self.sldMidiControlVolumeCh_list[channel]=wx.Slider(self, value=64, minValue=0, maxValue=127,
                                                                size=(80, -1), style=wx.SL_HORIZONTAL) # | wx.SL_LABELS
            # A text field is added to show value of slider as activating option SL_LABELS will show to many information
            self.textValueMidiControlVolumeCh_list[channel]=wx.StaticText(self, -1, '64', style=wx.ALIGN_RIGHT |
                                                                wx.ST_NO_AUTORESIZE, size=(30,20))
            self.sldMidiControlPanCh_list[channel]=wx.Slider(self, value=64, minValue=0, maxValue=127,
                                                                size=(80, -1), style=wx.SL_HORIZONTAL) # | wx.SL_LABELS
            # A text field is added to show value of slider as activating option SL_LABELS will show to many information
            self.textValueMidiControlPanCh_list[channel]=wx.StaticText(self, -1, '64', style=wx.ALIGN_RIGHT |
                                                                wx.ST_NO_AUTORESIZE, size=(30,20))
            midi_box.Add(wx.StaticText(self, -1, _('Voice n.%d: ') % channel), row=channel, col=0,
                         flag=wx.ALIGN_CENTER_VERTICAL, border=border)
            midi_box.Add(self.cmbMidiProgramCh_list[channel], row=channel, col=1, flag=wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
            #3rd column (col=2) is unused on purpose to leave some space (maybe replaced with some other spacer option later on)
            midi_box.Add(self.sldMidiControlVolumeCh_list[channel], row=channel, col=3,
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
            midi_box.Add(self.textValueMidiControlVolumeCh_list[channel], row=channel, col=4,
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
            #6th column (col=5) is unused on purpose to leave some space (maybe replaced with some other spacer option later on)
            midi_box.Add(self.sldMidiControlPanCh_list[channel], row=channel, col=6,
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
            midi_box.Add(self.textValueMidiControlPanCh_list[channel], row=channel, col=7,
                         flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
            #Some properties are added to the slider to be able to update the associated text field with value when slider is moved
            self.sldMidiControlVolumeCh_list[channel].infotype="Volume"
            self.sldMidiControlVolumeCh_list[channel].currentchannel=channel
            self.sldMidiControlVolumeCh_list[channel].Bind(wx.EVT_SCROLL, self.OnSliderScroll)
            self.sldMidiControlPanCh_list[channel].infotype="Pan"
            self.sldMidiControlPanCh_list[channel].currentchannel=channel
            self.sldMidiControlPanCh_list[channel].Bind(wx.EVT_SCROLL, self.OnSliderScroll)
            # Binding
            self.cmbMidiProgramCh_list[channel].currentchannel=channel
            self.cmbMidiProgramCh_list[channel].Bind(wx.EVT_COMBOBOX,self.OnProgramSelection)

        midi_box.AddGrowableCol(1)

        # reset buttons box
        self.reset = wx.Button(self, -1, _('&Reset'))
        btn_box = wx.BoxSizer(wx.HORIZONTAL)
        btn_box.Add(self.reset, flag=wx.ALIGN_RIGHT)
        reset_toolTip = _('The instrument for all voices is set to the default midi program. The volume and pan are set to 96/64.')
        self.reset.SetToolTip(wx.ToolTip(reset_toolTip))

        # add all box to the dialog to be displayed
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(midi_box, flag=wx.ALL | wx.ALIGN_RIGHT, border=border)
        self.sizer.Add(btn_box, flag=wx.ALL | wx.ALIGN_RIGHT, border=border)

        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)
        self.Centre()
        self.sizer.Fit(self)

        # try to set selection on previously defined instrument or default one or Piano
        self.midi_program_ch_list=['midi_program_ch1', 'midi_program_ch2', 'midi_program_ch3', 'midi_program_ch4',
                                   'midi_program_ch5', 'midi_program_ch6', 'midi_program_ch7', 'midi_program_ch8',
                                   'midi_program_ch9', 'midi_program_ch10', 'midi_program_ch11', 'midi_program_ch12',
                                   'midi_program_ch13', 'midi_program_ch14', 'midi_program_ch15', 'midi_program_ch16']
        try:
            for channel in range(1, 16+1):
                if self.settings.get(self.midi_program_ch_list[channel-1]):
                    midi_info=self.settings.get(self.midi_program_ch_list[channel-1])
                else:
                    midi_info=[self.settings.get('midi_program', 1),96,64]
                self.cmbMidiProgramCh_list[channel].Select(midi_info[0])
                self.sldMidiControlVolumeCh_list[channel].SetValue(midi_info[1])
                self.textValueMidiControlVolumeCh_list[channel].SetLabel("%d" % midi_info[1])
                self.sldMidiControlPanCh_list[channel].SetValue(midi_info[2])
                self.textValueMidiControlPanCh_list[channel].SetLabel("%d" % midi_info[2])
        except:
            pass

        self.reset.Bind(wx.EVT_BUTTON, self.OnResetDefault)

    def OnProgramSelection(self,evt):
        obj = evt.GetEventObject()
        val = obj.GetValue()
        #print obj.currentchannel
        #print val
        currentchannel = obj.currentchannel
        self.settings[self.midi_program_ch_list[currentchannel-1]] = [self.cmbMidiProgramCh_list[currentchannel].GetSelection(),
                                                               self.sldMidiControlVolumeCh_list[currentchannel].GetValue(),
                                                               self.sldMidiControlPanCh_list[currentchannel].GetValue()]

    def OnSliderScroll(self, evt):
        obj = evt.GetEventObject()
        val = obj.GetValue()

        if obj.infotype=="Volume":
            self.textValueMidiControlVolumeCh_list[obj.currentchannel].SetLabel("%d" % val)
        if obj.infotype=="Pan":
            self.textValueMidiControlPanCh_list[obj.currentchannel].SetLabel("%d" % val)
        currentchannel = obj.currentchannel
        self.settings[self.midi_program_ch_list[currentchannel-1]] = [self.cmbMidiProgramCh_list[currentchannel].GetSelection(),
                                                               self.sldMidiControlVolumeCh_list[currentchannel].GetValue(),
                                                               self.sldMidiControlPanCh_list[currentchannel].GetValue()]

    def OnResetDefault(self, evt):
        try:
            for channel in range(1, 16+1):
                self.cmbMidiProgramCh_list[channel].Select(self.settings.get('midi_program', 1))
                self.sldMidiControlVolumeCh_list[channel].SetValue(96)
                self.textValueMidiControlVolumeCh_list[channel].SetLabel("96")
                self.sldMidiControlPanCh_list[channel].SetValue(64)
                self.textValueMidiControlPanCh_list[channel].SetLabel("64")

                # 1.3.6 [SS] 2014-11-16
                #if (self.cmbMidiProgramCh_list[channel].GetSelection()!=self.settings.get('midi_program', 1) or
                    #self.sldMidiControlVolumeCh_list[channel].GetValue()!=64 or
                    #self.sldMidiControlPanCh_list[channel].GetValue()!=64):

                self.settings[self.midi_program_ch_list[channel-1]] = [self.cmbMidiProgramCh_list[channel].GetSelection(),
                                                                       self.sldMidiControlVolumeCh_list[channel].GetValue(),
                                                                       self.sldMidiControlPanCh_list[channel].GetValue()]
                # 1.3.6 [SS] 2014-11-16
                #else:
                    #if self.midi_program_ch_list[channel-1] in self.settings: del self.settings[self.midi_program_ch_list[channel-1]]
        except:
            pass





class MidiSettingsFrame(wx.Dialog):
    def __init__(self, parent, settings):
        wx.Dialog.__init__(self, parent, -1, _('Midi device settings'), wx.DefaultPosition, wx.Size(130, 80))
        self.settings = settings
        self.SetBackgroundColour(wx.Colour(245, 244, 235))
        border = 4
        sizer = wx.GridBagSizer(5, 5)
        sizer.Add(wx.StaticText(self, -1, _('Input device')),       wx.GBPosition(0, 0), flag=wx.ALL | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(wx.StaticText(self, -1, _('Output device')),      wx.GBPosition(1, 0), flag=wx.ALL | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)

        inputDevices = [_('None')]
        inputDeviceIDs = [None]
        outputDevices = [_('None')]
        outputDeviceIDs = [None]
        if 'pypm' in globals():
            n = pypm.CountDevices()
        else:
            n = 0
        for i in range(n):
            interface, name, input, output, opened = pypm.GetDeviceInfo(i)
            if input:
                inputDevices.append(name)
                inputDeviceIDs.append(i)
            elif output:
                outputDevices.append(name)
                outputDeviceIDs.append(i)
        self.inputDeviceIDs = inputDeviceIDs
        self.outputDeviceIDs = outputDeviceIDs

        self.inputDevice = wx.ComboBox(self, -1, size=(250, 22), choices=inputDevices, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.outputDevice = wx.ComboBox(self, -1, size=(250, 22), choices=outputDevices, style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.inputDevice.SetSelection(0)
        self.outputDevice.SetSelection(0)
        if settings.get('midi_device_in', None) in inputDeviceIDs:
            self.inputDevice.SetSelection(inputDeviceIDs.index(settings.get('midi_device_in', None)))
        if settings.get('midi_device_out', None) in outputDeviceIDs:
            self.outputDevice.SetSelection(outputDeviceIDs.index(settings.get('midi_device_out', None)))

        self.ok = wx.Button(self, -1, _('&Ok'))
        self.cancel = wx.Button(self, -1, _('&Cancel'))
        box = wx.BoxSizer(wx.HORIZONTAL)
        # 1.3.6.1 [JWdJ] 2015-01-30 Swapped next two lines so OK-button comes first (OK Cancel)
        box.Add(self.ok, wx.ID_OK, flag=wx.ALIGN_RIGHT)
        box.Add(self.cancel, wx.ID_CANCEL, flag=wx.ALIGN_RIGHT)
        sizer.Add(self.inputDevice,   wx.GBPosition(0, 1), flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(self.outputDevice,  wx.GBPosition(1, 1), flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=border)
        sizer.Add(box,                wx.GBPosition(2,0), (1, 2), flag=0 | wx.ALL | wx.ALL | wx.ALIGN_RIGHT, border=border)
        self.ok.SetDefault()

        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self.Centre()
        sizer.Fit(self)

        self.ok.Bind(wx.EVT_BUTTON, self.OnOk)
        self.cancel.Bind(wx.EVT_BUTTON, self.OnCancel)

    def OnOk(self, evt):
        self.settings['midi_device_in']  = self.inputDeviceIDs[self.inputDevice.GetSelection()]
        self.settings['midi_device_out'] = self.outputDeviceIDs[self.outputDevice.GetSelection()]
        self.EndModal(wx.ID_OK)

    def OnCancel(self, evt):
        self.EndModal(wx.ID_CANCEL)



# 1.3.6 [SS] 2014-12-04 2014-12-16
# For controlling the way abcm2ps runs
class MyAbcm2psPage(wx.Panel):
    # 1.3.6.1 [SS] 2015-02-02
    def __init__(self, parent, settings,abcsettingspage):
        wx.Panel.__init__(self,parent)
        self.settings = settings
        self.abcsettingspage = abcsettingspage
        self.SetBackgroundColour(wx.Colour(245, 244, 235))
        border = 4
        headingtxt = _('The options in this page controls how the music score is displayed.\n\n')
        heading = wx.StaticText(self,-1,headingtxt)


        clean      = wx.StaticText(self,-1, _("No page settings"))
        defaults   = wx.StaticText(self,-1, _("EasyABC defaults"))
        numberbars = wx.StaticText(self,-1, _("Include bar numbers"))
        refnumbers = wx.StaticText(self,-1, _("Add X reference number"))
        nolyrics   = wx.StaticText(self,-1, _("Suppress lyrics"))
        linends    = wx.StaticText(self,-1, _("Ignore line ends"))
        leftmarg   = wx.StaticText(self,-1, _("Left margin (cm)"))
        rightmarg  = wx.StaticText(self,-1, _("Right margin (cm)"))
        topmarg    = wx.StaticText(self,-1, _("Top margin (cm)"))
        botmarg = wx.StaticText(self,-1, _("Bottom margin (cm)"))
        # 1.3.6.1 [SS] 2015-01-28
        pagewidth = wx.StaticText(self,-1, _("Page width (cm)"))
        pageheight = wx.StaticText(self,-1, _("Page height (cm)"))

        extras = wx.StaticText(self,-1, _("Extra parameters"))
        self.extras = wx.TextCtrl(self,-1,size=(350,22))
        formatf = wx.StaticText(self,-1, _("Format file"))
        # 1.3.6.4 [SS] 2015-09-11 2015-09-21
        try:
            self.format_choices = self.settings.get('abcm2ps_format_choices','').split('|') 
        except:
            self.format_choices = []
        # 1.3.6.4 [SS] 2015-09-11
        self.formatf  = wx.ComboBox(self,-1,choices=self.format_choices,size = (350,-1),style=wx.CB_DROPDOWN)
        
        self.browsef = wx.Button(self,-1, _('Browse...'),size = (-1,22))

        scalefact  = wx.StaticText(self,-1, _("Scale factor (eg. 0.8)"))
        self.chkm2psclean = wx.CheckBox(self,-1,'')
        self.chkm2psdef   = wx.CheckBox(self,-1,'')
        self.chkm2psbar = wx.CheckBox(self, -1, '')
        self.chkm2psref = wx.CheckBox(self, -1, '')
        self.chkm2pslyr = wx.CheckBox(self, -1, '')
        self.chkm2psend = wx.CheckBox(self, -1, '')
        self.leftmargin  = wx.TextCtrl(self, -1, size=(55, 22))
        self.rightmargin = wx.TextCtrl(self, -1, size=(55, 22))
        self.topmargin = wx.TextCtrl(self, -1, size=(55, 22))
        self.botmargin = wx.TextCtrl(self, -1, size=(55, 22))
        self.pagewidth = wx.TextCtrl(self, -1, size=(55,22))
        self.pageheight =wx.TextCtrl(self, -1, size=(55,22))

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

        self.chkm2psclean.SetValue(self.settings.get('abcm2ps_clean',False))
        self.chkm2psdef.SetValue(self.settings.get('abcm2ps_defaults'))
        self.chkm2psbar.SetValue(self.settings.get('abcm2ps_number_bars',False))
        self.chkm2psref.SetValue(self.settings.get('abcm2ps_refnumbers',False))
        self.chkm2pslyr.SetValue(self.settings.get('abcm2ps_no_lyrics',False))
        self.chkm2psend.SetValue(self.settings.get('abcm2ps_ignore_ends',False))
        self.leftmargin.SetValue(self.settings.get('abcm2ps_leftmargin','1.78'))
        self.rightmargin.SetValue(self.settings.get('abcm2ps_rightmargin','1.78'))
        self.topmargin.SetValue(self.settings.get('abcm2ps_topmargin','1.0'))
        self.botmargin.SetValue(self.settings.get('abcm2ps_botmargin','1.0'))
        # 1.3.6.1 [SS] 2015-01-28
        self.pagewidth.SetValue(self.settings.get('abcm2ps_pagewidth','21.59'))
        self.pageheight.SetValue(self.settings.get('abcm2ps_pageheight',27.94))
        self.extras.SetValue(self.settings.get('abcm2ps_extra_params', ''))
        self.formatf.SetValue(self.settings.get('abcm2ps_format_path',''))


        self.chkm2psclean.Bind(wx.EVT_CHECKBOX,self.OnAbcm2psClean)
        self.chkm2psdef.Bind(wx.EVT_CHECKBOX,self.OnAbcm2psDefaults)
        self.chkm2psbar.Bind(wx.EVT_CHECKBOX,self.OnAbcm2psBar)
        self.chkm2pslyr.Bind(wx.EVT_CHECKBOX,self.OnAbcm2pslyrics)
        self.chkm2psref.Bind(wx.EVT_CHECKBOX,self.OnAbcm2psref)
        self.chkm2psend.Bind(wx.EVT_CHECKBOX,self.OnAbcm2psend)
        self.leftmargin.Bind(wx.EVT_TEXT,self.OnPSleftmarg,self.leftmargin)
        self.rightmargin.Bind(wx.EVT_TEXT,self.OnPSrightmarg,self.rightmargin)
        self.topmargin.Bind(wx.EVT_TEXT,self.OnPStopmarg,self.topmargin)
        self.botmargin.Bind(wx.EVT_TEXT,self.OnPSbotmarg,self.botmargin)
        # 1.3.6.1 [SS] 2015-01-28
        self.formatf.Bind(wx.EVT_TEXT,self.OnFormat,self.formatf)
        self.formatf.Bind(wx.EVT_RIGHT_DOWN,self.OnClean,self.formatf) #1.3.6.4
        self.extras.Bind(wx.EVT_TEXT,self.On_extra_params,self.extras)
        self.browsef.Bind(wx.EVT_BUTTON,self.OnBrowse_format,self.browsef)
        # 1.3.6.1 [SS] 2015-01-29
        self.pagewidth.Bind(wx.EVT_TEXT,self.OnPSpagewidth,self.pagewidth)
        self.pageheight.Bind(wx.EVT_TEXT,self.OnPSpageheight,self.pageheight)

        # 1.3.6 [SS] 2014-12-16
        # 1.3.6.3 [SS] 2015-03-15
        #fval = self.settings.get('abcm2ps_scale',0.9)
        self.scaleval = wx.TextCtrl(self,-1,size=(50,22))
        self.scaleval.SetValue(self.settings.get('abcm2ps_scale',0.9))
        self.scaleval.SetToolTip(wx.ToolTip('Scales the separation between staff lines. Recommended value 0.80.'))

        # 1.3.6.2 [SS] 2015-04-21
        self.scaleval.Bind(wx.EVT_TEXT,self.OnPSScale,self.scaleval)

        # 1.3.6 [SS] 2014-12-16
        self.box = wx.BoxSizer(wx.VERTICAL)
        gridsizer1 = wx.GridBagSizer(vgap = 8,hgap =2)
        gridsizer2 = wx.FlexGridSizer(0,4,2,2)
        self.box.Add(gridsizer1,0,wx.EXPAND)
        self.box.Add(gridsizer2,0,wx.EXPAND)

        # 1.3.6.1 [SS] 2015-01-08 2015-01-28
        self.gridsizer4 = wx.FlexGridSizer(0,3,2,2)
        self.box.Add(self.gridsizer4,0,wx.EXPAND)
        self.gridsizer3 = wx.FlexGridSizer(0,4,2,2)
        self.box.Add(self.gridsizer3,0,wx.EXPAND)

        gridsizer1.Add(heading,(1,1))

        gridsizer2.Add(clean,0,0,0,0)
        gridsizer2.Add(self.chkm2psclean,0,0,0,0)

        gridsizer2.Add(defaults,0,0,0,0)
        gridsizer2.Add(self.chkm2psdef,0,0,0,0)

        gridsizer2.Add(numberbars,0,0,0,0)
        gridsizer2.Add(self.chkm2psbar,0,0,0.0)

        gridsizer2.Add(refnumbers,0,0,0.0)
        gridsizer2.Add(self.chkm2psref,0,0,0,0)

        gridsizer2.Add(nolyrics,0,0,0,0)
        gridsizer2.Add(self.chkm2pslyr,0,0,0,0)

        gridsizer2.Add(linends,0,0,0,0)
        gridsizer2.Add(self.chkm2psend,0,0,0,0)

        # 1.3.6.1 [SS] 2015-01-08
        self.gridsizer3.Add(leftmarg,0,0,0,0)
        self.gridsizer3.Add(self.leftmargin,0,0,0,0)

        self.gridsizer3.Add(rightmarg,0,0,0,0)
        self.gridsizer3.Add(self.rightmargin,0,0,0,0)

        self.gridsizer3.Add(topmarg,0,0,0,0)
        self.gridsizer3.Add(self.topmargin,0,0,0,0)

        self.gridsizer3.Add(botmarg,0,0,0,0)
        self.gridsizer3.Add(self.botmargin,0,0,0,0)

        self.gridsizer3.Add(pagewidth,0,0,0,0)
        self.gridsizer3.Add(self.pagewidth,0,0,0,0)

        self.gridsizer3.Add(pageheight,0,0,0,0)
        self.gridsizer3.Add(self.pageheight,0,0,0,0)

        self.gridsizer3.Add(scalefact,0,0.0,0)
        self.gridsizer3.Add(self.scaleval,0,0.0,0)

        # 1.3.6.1 [SS] 2015-01-28
        self.gridsizer4.Add(extras,0,0,0,0)
        self.gridsizer4.Add(self.extras,0,0,0,0)
        self.gridsizer4.Add((1,20))
        self.gridsizer4.Add(formatf,0,0,0,0)
        self.gridsizer4.Add(self.formatf,0,0,0,0)
        self.gridsizer4.Add(self.browsef,0,0,0,0)


        self.SetSizer(self.box)
        self.Fit()

        # 1.3.6.1 [SS] 2015-01-08
        if self.settings['abcm2ps_clean'] or self.settings['abcm2ps_defaults']:
            self.box.Show(self.gridsizer3,show=False)
        else:
            self.box.Show(self.gridsizer3,show=True)

    def OnAbcm2psClean(self,evt):
        self.settings['abcm2ps_clean']               = self.chkm2psclean.GetValue()
        if self.settings['abcm2ps_clean'] or self.settings['abcm2ps_defaults']:
            self.box.Show(self.gridsizer3,show=False)
        else:
            self.box.Show(self.gridsizer3,show=True)

    def OnAbcm2psDefaults(self,evt):
        self.settings['abcm2ps_defaults']            = self.chkm2psdef.GetValue()
        if self.settings['abcm2ps_clean'] or self.settings['abcm2ps_defaults']:
            self.box.Show(self.gridsizer3,show=False)
        else:
            self.box.Show(self.gridsizer3,show=True)

    def OnAbcm2psBar(self,evt):
        self.settings['abcm2ps_number_bars']         = self.chkm2psbar.GetValue()


    def OnAbcm2pslyrics(self,evt):
        self.settings['abcm2ps_no_lyrics']           = self.chkm2pslyr.GetValue()

    def OnAbcm2psref(self,evt):
        self.settings['abcm2ps_refnumbers']          = self.chkm2psref.GetValue()

    def OnAbcm2psend(self,evt):
        self.settings['abcm2ps_ignore_ends']         = self.chkm2psend.GetValue()


    # 1.3.6.2 [SS] 2015-03-15
    def OnPSScale(self,evt):
        val = self.scaleval.GetValue()
        m   = re.findall("\d+.\d+|\d+",val)
        if len(m) > 0 and float(val) >0.1 and float(val) < 1.5:
            self.settings['abcm2ps_scale'] = str(val)

    def OnPSleftmarg(self,evt):
        # 1.3.6.1 [SS] 2015-01-13
        val = self.leftmargin.GetValue()
        # extract only the number
        m   = re.findall("\d+.\d+|\d+",val)
        if len(m) > 0:
            val = str(m[0])
            self.settings['abcm2ps_leftmargin'] = val

    def OnPSrightmarg(self,evt):
        # 1.3.6.1 [SS] 2015-01-13
        val = self.rightmargin.GetValue()
        m   = re.findall("\d+.\d+|\d+",val)
        if len(m) > 0:
            val = str(m[0])
            self.settings['abcm2ps_rightmargin'] = val

    def OnPStopmarg(self,evt):
        # 1.3.6.1 [SS] 2015-01-13
        val = self.topmargin.GetValue()
        m   = re.findall("\d+.\d+|\d+",val)
        if len(m) > 0:
            val = str(m[0])
            self.settings['abcm2ps_topmargin'] = val

    def OnPSbotmarg(self,evt):
        # 1.3.6.1 [SS] 2015-01-13
        val = self.botmargin.GetValue()
        m   = re.findall("\d+.\d+|\d+",val)
        if len(m) > 0:
            val = str(m[0])
            self.settings['abcm2ps_botmargin'] = val

    # 1.3.6.1 [SS] 2015-01-28
    def OnPSpagewidth(self,evt):
        val = self.pagewidth.GetValue()
        m   = re.findall("\d+.\d+|\d+",val)
        if len(m) > 0:
            val = str(m[0])
            self.settings['abcm2ps_pagewidth'] = val

    def OnPSpageheight(self,evt):
        val = self.pageheight.GetValue()
        m   = re.findall("\d+.\d+|\d+",val)
        if len(m) > 0:
            val = str(m[0])
            self.settings['abcm2ps_pageheight'] = val

    def OnFormat(self,evt):
        path = evt.String
        self.settings['abcm2ps_format_path'] =  path
        # 1.3.6.4 [SS] 2015-09-11
        if path and not path in self.format_choices and os.path.isfile(path) and os.access(path, os.R_OK):
            self.format_choices.append(path)
            self.settings['abcm2ps_format_choices'] = '|'.join(self.format_choices)
            # [SS] the SetItems does not work correctly in wxpython 2.7
            #self.formatf.SetItems(str(self.settings['abcm2ps_format_choices']))

    # 1.3.6.4 [SS] 2015-09-21
    def OnClean(self,evt):
        #print "right click"
        #if evt.ControlDown():
            #print "control down"
        result = wx.MessageBox(_("This will remove the selections in the combobox."),_("Proceed?"), wx.ICON_QUESTION | wx.YES | wx.NO)
        #print self.formatf.GetItems()
        if result == wx.YES:
            #self.formatf.Clear()
            self.formatf.SetItems([])
            self.settings['abcm2ps_format_choices'] =  self.formatf.GetItems()


    def On_extra_params(self,evt):
        self.settings['abcm2ps_extra_params'] = self.extras.GetValue()

    def OnBrowse_format(self,evt):
        dlg = wx.FileDialog(
                self, message=_("Find PostScript format file"), defaultFile="",  style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.CHANGE_DIR )
        try:
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                self.formatf.SetValue(path)
                # 1.3.6.4 [SS] 2015-09-11
                if path and not path in self.format_choices and os.path.isfile(path) and os.access(path, os.R_OK):
                    self.format_choices.append(dlg.GetPath())
                    self.settings['abcm2ps_format_choices'] = '|'.join(self.format_choices)
                    if wx.Platform != "__WXMSW__":
                        self.settings['abcm2ps_format_path'] = path  # 1.3.6.4 [SS] 2015-09-17 in case control.SetValue(path) does not trigger OnChangePath



        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window

# 1.3.6 [SS] 2014-12-01
# For controlling the way xml2abc and abc2xml operate
class MyXmlPage(wx.Panel):
    def __init__(self, parent, settings):
        wx.Panel.__init__(self,parent)
        self.settings = settings
        self.SetBackgroundColour(wx.Colour(245, 244, 235))
        border = 4

        headingtxt = _("The settings on this page control behaviour of the functions abc2xml and xml2abc.\nYou find these functions under Files/export and import. Hovering the mouse over\none of the checkboxes will provide more explanation. Further documentation can be found\nin the Readme.txt files which come with the abc2xml.py-??.zip and xml2abc.py-??.zip\ndistributions available from the Wim Vree's web site.\n\n")

        heading    = wx.StaticText(self,-1,headingtxt)
        abc2xml    = wx.StaticText(self,-1,"abc2xml options")
        compressed = wx.StaticText(self,-1,'Compressed xml')
        xmlpage    = wx.StaticText(self,-1,'Page settings')
        unfold     = wx.StaticText(self,-1,'Unfold Repeats')
        mididata   = wx.StaticText(self,-1,'Midi Data')
        volta      = wx.StaticText(self,-1,'Volta type setting')
        xml2abc    = wx.StaticText(self,-1,'xml2abc option')
        numchar    = wx.StaticText(self,-1,'characters/line')
        numbars    = wx.StaticText(self,-1,'bars per line')
        credit     = wx.StaticText(self,-1,'credit filter')
        ulength    = wx.StaticText(self,-1,'unit length')



        self.XmlPage = wx.TextCtrl(self, -1, size=(300,20))
        self.maxchars = wx.TextCtrl(self,-1, size=(40,20))
        self.maxbars  = wx.TextCtrl(self,-1, size=(40,20))
        self.voltaval = wx.TextCtrl(self,-1, size=(40,20))
        self.creditval = wx.TextCtrl(self,-1,size=(40,20))
        self.unitval  = wx.TextCtrl(self,-1,size= (40,20))
        self.chkXmlCompressed = wx.CheckBox(self, -1, '')
        self.chkXmlUnfold = wx.CheckBox(self, -1, '')
        self.chkXmlMidi = wx.CheckBox(self, -1, '')

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
        XmlUnfold_toolTip = _('When checked, xml2abc turns off repeat translation and instead unfolds simple repeats instead.')
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
        voltaval_toolTip = _("The default (V=0) translates volta backets in all voices. V=1 prevents abcm2ps to write volta brackets on all but the first voice. (A %%repbra 0 command is added to each voice that hides its volta's.) When V=2 abcm2ps only typesets volta brackets on the first voice of each xml-part. When V=3 the volta brackets are only translated for the first abc voice, which has the same effect on the output of abcm2ps as V=1, but the abc code is not suited for abc2midi.")
        self.voltaval.SetToolTip(wx.ToolTip(voltaval_toolTip))


        # 1.3.6 [SS] 2014-12-20
        self.chkXmlCompressed.Bind(wx.EVT_CHECKBOX,self.OnXmlCompressed)
        self.chkXmlUnfold.Bind(wx.EVT_CHECKBOX,self.OnXmlUnfold)
        self.chkXmlMidi.Bind(wx.EVT_CHECKBOX,self.OnXmlMidi)
        self.voltaval.Bind(wx.EVT_TEXT,self.OnVolta)
        self.maxbars.Bind(wx.EVT_TEXT,self.OnMaxbars)
        self.maxchars.Bind(wx.EVT_TEXT,self.OnMaxchars)
        self.creditval.Bind(wx.EVT_TEXT,self.OnCreditval)
        self.unitval.Bind(wx.EVT_TEXT,self.OnUnitval)
        self.XmlPage.Bind(wx.EVT_TEXT,self.OnXmlPage)

        # 1.3.6 [SS] 2014-12-18
        box = wx.BoxSizer(wx.VERTICAL)
        gridsizer1 = wx.GridBagSizer(vgap = 8,hgap =2)
        gridsizer2 = wx.FlexGridSizer(0,2,2,2)
        box.Add(gridsizer1,0,wx.EXPAND)
        box.Add(gridsizer2,0,wx.EXPAND)

        gridsizer1.Add(heading,(1,1))

        gridsizer2.Add((1,20))
        gridsizer2.Add((1,20))

        gridsizer2.Add(abc2xml,0,0,0)
        gridsizer2.Add((1,1))

        gridsizer2.Add(compressed,0,0,0)
        gridsizer2.Add(self.chkXmlCompressed,0,0,0)

        gridsizer2.Add((1,20))
        gridsizer2.Add((1,20))

        gridsizer2.Add(xml2abc,0,0,0)
        gridsizer2.Add((1,1))

        gridsizer2.Add(unfold,0,0,0)
        gridsizer2.Add(self.chkXmlUnfold,0,0,0)

        gridsizer2.Add(mididata,0,0,0)
        gridsizer2.Add(self.chkXmlMidi,0,0,0)

        gridsizer2.Add(volta,0,0,0)
        gridsizer2.Add(self.voltaval,0,0,0)

        gridsizer2.Add(numchar,0,0,0)
        gridsizer2.Add(self.maxchars,0,0,0)

        gridsizer2.Add(numbars,0,0,0)
        gridsizer2.Add(self.maxbars,0,0,0)

        gridsizer2.Add(credit,0,0,0)
        gridsizer2.Add(self.creditval,0,0,0)

        gridsizer2.Add(ulength,0,0,0)
        gridsizer2.Add(self.unitval,0,0,0)

        gridsizer2.Add(xmlpage,0,0,0)
        gridsizer2.Add(self.XmlPage,0,0,0)


        self.SetSizer(box)
        self.Fit()
        self.Layout()


    def OnXmlCompressed(self,evt):
        self.settings['xmlcompressed']   = self.chkXmlCompressed.GetValue()

    def OnXmlUnfold(self,evt):
        self.settings['xmlunfold']       = self.chkXmlUnfold.GetValue()

    def OnXmlMidi(self,evt):
        self.settings['xmlmidi']         = self.chkXmlMidi.GetValue()

    def OnVolta(self,evt):
        self.settings['xml_v']           = self.voltaval.GetValue()

    def OnMaxbars(self,evt):
        self.settings['xml_b']           = self.maxbars.GetValue()

    def OnMaxchars(self,evt):
        self.settings['xml_n']           = self.maxchars.GetValue()

    def OnCreditval(self,evt):
        self.settings['xml_c']           = self.creditval.GetValue()

    def OnUnitval(self,evt):
        self.settings['xml_d']           = self.unitval.GetValue()

    def OnXmlPage(self,evt):
        self.settings['xml_p']           = self.XmlPage.GetValue()



class MidiOptionsFrame(wx.Dialog):
    def __init__(self, parent, ID=-1, title='', key='', metre='3/4', default_len='1/16'):
        wx.Dialog.__init__(self, parent, ID, _('ABC Options'), wx.DefaultPosition, wx.Size(300, 80))

        self.SetBackgroundColour(wx.Colour(245, 244, 235))
        border = 10
        sizer = wx.GridBagSizer(5, 5)
        sizer.Add(wx.StaticText(self, -1, u'K: ' + _('Key signature')),       wx.GBPosition(0, 0), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(wx.StaticText(self, -1, u'M: ' + _('Metre')),               wx.GBPosition(1, 0), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(wx.StaticText(self, -1, u'L: ' + _('Default note length')), wx.GBPosition(2, 0), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(wx.StaticText(self, -1, u'T: ' + _('Title')),               wx.GBPosition(3, 0), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(wx.StaticText(self, -1, _('Bars per line')),          wx.GBPosition(4, 0), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(wx.StaticText(self, -1, _('Numbers of notes in anacrusis')),  wx.GBPosition(5, 0), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=border)

        self.key = wx.TextCtrl(self, -1, size=(150, 22))
        self.metre = wx.TextCtrl(self, -1, size=(150, 22))
        self.default_len = wx.TextCtrl(self, -1, size=(150, 22))
        self.title = wx.TextCtrl(self, -1, size=(150, 22))
        self.bpl = wx.TextCtrl(self, -1, size=(150, 22))
        self.num_notes_in_anacrusis = wx.TextCtrl(self, -1, size=(150, 22))
        self.triplet_detection = wx.CheckBox(self, -1, _('Detect triplets'))
        self.broken_rythm_detection = wx.CheckBox(self, -1, _('Detect broken rythms'))
        self.slur_triplets = wx.CheckBox(self, -1, _('Use slurs on triplets'))
        self.slur_8ths = wx.CheckBox(self, -1, _('Use slurs on eights (useful for some waltzes)'))
        self.slur_16ths = wx.CheckBox(self, -1, _('Use slurs on first pair of sixteenth (useful for some 16th polskas)'))
        self.ok = wx.Button(self, -1, _('&Ok'))
        self.cancel = wx.Button(self, -1, _('&Cancel'))
        box = wx.BoxSizer(wx.HORIZONTAL)
        #box.AddStretchSpacer()
        # 1.3.6.1 [JWdJ] 2015-01-30 Swapped next two lines so OK-button comes first (OK Cancel)
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
        wx.Dialog.__init__(self, parent, -1, _('Errors'), wx.DefaultPosition, wx.Size(700, 80))
        border = 10
        self.SetBackgroundColour(wx.Colour(245, 244, 235))

        sizer = wx.BoxSizer(wx.VERTICAL)
        font_size = get_normal_fontsize() # 1.3.6.3 [JWDJ] one function to set font size
        font = wx.Font(font_size, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Courier New")
        self.error = wx.TextCtrl(self, -1, error_msg, size=(700, 300), style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER|wx.HSCROLL)
        self.error.SetFont(font)

        self.ok = wx.Button(self, -1, _('&Ok'))
        self.cancel = wx.Button(self, -1, _('&Cancel'))
        box = wx.BoxSizer(wx.HORIZONTAL)
        # 1.3.6.1 [JWdJ] 2015-01-30 Swapped next two lines so OK-button comes first (OK Cancel)
        box.Add(self.ok, wx.ID_OK, flag=wx.ALIGN_RIGHT)
        box.Add(self.cancel, wx.ID_CANCEL, flag=wx.ALIGN_RIGHT)
        sizer.Add(self.error, flag=wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border=border)
        sizer.Add(box, flag=wx.TOP | wx.BOTTOM | wx.LEFT | wx.RIGHT | wx.ALIGN_RIGHT, border=border)
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
        self.gauge = wx.Gauge(self, -1, 100, (0, 0), (500, 80))
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

        #----------------------------------------------------------------------
        SmallDnArrow = PyEmbeddedImage(
        "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAEhJ"
        "REFUOI1jZGRiZqAEMFGke9QABgYGBgYWdIH///7+J6SJkYmZEacLkCUJacZqAD5DsInTLhDR"
        "bcPlKrwugGnCFy6Mo3mBAQChDgRlP4RC7wAAAABJRU5ErkJggg==")
        self.sm_up = self.il.Add(SmallUpArrow.GetBitmap())
        self.sm_dn = self.il.Add(SmallDnArrow.GetBitmap())
        #self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
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



# 1.3.6 [SS] 2014-11-21
class MySearchFrame(wx.Frame):
    ''' For searching a directory of abc files for tunes containing a string. '''
    def __init__(self,parent,settings):
        wx.Frame.__init__(self, wx.GetApp().TopWindow, wx.ID_ANY, _("Search files"), style=wx.DEFAULT_FRAME_STYLE, name='searcher')
        # Add a panel so it looks the correct on all platforms
        wx.Frame.SetDimensions(self,-1,-1,380,400)
        self.searchdata = ''
        searchfold = wx.StaticText(self,-1, _("Folder"))
        self.frame = parent
        self.searchfoldtxt = wx.TextCtrl(self,-1,settings['searchfolder'],(-1,-1),(200,-1))
        self.browsebut = wx.Button(self, -1, _('Browse'), size=(-1,26))
        searchlab = wx.StaticText(self,-1, _('Text'))
        self.searchstring = wx.TextCtrl(self,-1,self.searchdata,(-1,-1),(200,-1))
        self.startbut = wx.Button(self,-1, _('Search'), size = (-1,26))
        self.list_ctrl = wx.ListCtrl(self, size=(380,360), style=wx.LC_REPORT |wx.BORDER_SUNKEN|wx.LC_SINGLE_SEL)
        self.list_ctrl.InsertColumn(0, _('Title'), width=400)

        self.settings = settings
        self.running = 0
        self.searchlocator = {}
        self.searchpaths = {}
        self.count = 0


        mainsizer = wx.BoxSizer(wx.VERTICAL)
        sizer1   = wx.GridBagSizer(vgap=8,hgap=8)
        sizer2   = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(searchfold,(1,1))
        sizer1.Add(self.searchfoldtxt,(1,2))
        sizer1.Add(self.browsebut,(1,3))
        sizer1.Add(searchlab,(2,1))
        sizer1.Add(self.searchstring,(2,2))
        sizer1.Add(self.startbut,(2,3))
        sizer2.Add(self.list_ctrl,0,wx.ALL|wx.EXPAND)
        mainsizer.Add(sizer1,0,wx.ALL|wx.EXPAND)
        mainsizer.Add(sizer2,1,wx.ALL|wx.EXPAND)
        mainsizer.SetMinSize((360,200))
        self.SetSizer(mainsizer)
        self.Show()

        self.Bind(wx.EVT_BUTTON,self.On_browse_abcsearch,self.browsebut)
        self.Bind(wx.EVT_BUTTON,self.On_start_search,self.startbut)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED,self.OnItemSelected,self.list_ctrl)


    def On_browse_abcsearch(self,evt):
        ''' Selects the folder to open for searching'''
        dlg = wx.DirDialog(self, _("Open"), _("Choose a folder"), wx.OPEN)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                self.settings['searchfolder'] = dlg.GetPath()
                self.searchfoldtxt.SetValue(self.settings['searchfolder'])
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window


    def On_start_search(self,evt):
        ''' Initializes dictionaries and calls find_abc_files'''
        self.list_ctrl.DeleteAllItems()
        self.searchlocator = {}
        self.searchline = {}
        self.searchpaths = {}
        self.count = 0
        self.find_abc_files()


# 1.3.6 [SS] 2014-11-23
    def find_abc_files(self):
        ''' Does a recursive search of all folders inside root for abc files
            storing the results in the list abcmatches. Pops up a progress
            bar and searches each abc file in abcmatches for a specific
            searchstring in the title field by calling find_abc_string.'''
        # adapted from Programming Python by Mark Lutz
        root = self.settings['searchfolder']
        searchstring  = self.searchstring.GetValue()
        list_ctrl = self.list_ctrl
        searchstring = searchstring.lower()
        abcmatches = []
        for (dirname,dirshere,fileshere) in os.walk(root):
            #print fileshere
            for filename in fileshere:
                if filename.endswith('.abc') or filename.endswith('.ABC'):
                    pathname = os.path.join(dirname,filename)
                    abcmatches.append(pathname)

        progmax = len(abcmatches)
        progdialog = wx.ProgressDialog(_('Searching directory'), _('Remaining time'),
                     progmax,style = wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME |
                     wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE)
        try:
            #for name in abcmatches: print name
            k = 0
            for pathname in abcmatches:
                #print str(k) + ' ' + pathname
                k += 1
                running = progdialog.Update(k)
                #self.search_for_abc_string(pathname,'T:',searchstring,running,list_ctrl)
                self.find_abc_string(pathname,'T:',searchstring,list_ctrl)
                if running[0] == False or k > progmax:
                    break
        finally:
            progdialog.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window

# 1.3.6 [SS] 2014-11-30
    def find_abc_string(self,path,abckey,searchstring,list_ctrl):
        f = open(path,'rb') # read in binary to avoid problem with EOL characters
        wholefile = f.read()
        f.close()
        encoding = self.frame.get_encoding(wholefile)
        wholefile = wholefile.decode(encoding)
        loc = 0
        searchstring = searchstring.decode(encoding)
        #wholefile = wholefile.decode('utf-8')
        lwholefile = wholefile.lower()
        while loc != -1:
            loc = wholefile.find(abckey,loc)
            if loc == -1:
                break
            linend = wholefile.find('\n',loc)
            if linend == -1:
                break
            index = lwholefile.find(searchstring,loc,linend)
            if index != -1:
                list_ctrl.InsertStringItem(self.count,wholefile[loc+2:linend])
                self.searchpaths[self.count] = path
                self.searchlocator[self.count] = index
                #1.3.6
                #self.searchline is used for debugging only (see OnItemSelected below)
                self.searchline[self.count] = wholefile.count('\n',0,loc)
                self.count += 1
            loc = linend


# 1.3.6 [SS] 2014-12-02
    def OnItemSelected(self,evt):
        ''' Responds to a selected title in the search listbox results. The abc file
        containing the selected tune is opened and the table of contents is updated.'''
        global app
        frame = app._frames[0]
        index = evt.GetIndex() #line number in listbox
        path = self.searchpaths[index]
        loc = self.searchlocator[index] #character position in file
        line = self.searchline[index]
        #print 'line = ',line,' char = ',loc
        if frame.current_file != path:
            frame.document_name = path
            frame.SetTitle('%s - %s' % (program_name, frame.document_name))
            frame.editor.ClearAll()
            frame.load(path)
        # SetCurrentPos will position the editor on the selected tune
        # and should automatically position the music window and the tune_list.
        frame.editor.SetCurrentPos(loc)



class MyHtmlFrame(wx.Frame):
    ''' Creates an html window for displaying the help info. '''
    def __init__(self):
        wx.Frame.__init__(self, wx.GetApp().TopWindow,-1, title = _('Help Window'), name='htmlframe')

        # Add a panel so it looks the correct on all platforms
        global overview
        html = wx.html.HtmlWindow(self)
        if "gtk2" in wx.PlatformInfo:
            html.SetStandardFonts()
        html.SetPage(overview)


class MyOpenPopupMenu(wx.Menu):
    ''' menu which opens when you right click on the Open button'''
    def __init__(self):
        wx.Menu.__init__(self)
        item = wx.MenuItem(self,-1, _("Open abc file"))
        self.AppendItem(item)


class MainFrame(wx.Frame):
    def __init__(self, parent, ID, app_dir, settings):
        wx.Frame.__init__(self, parent, ID, '%s - %s %s' % (program_name, _('Untitled'), 1),
                         wx.DefaultPosition, wx.Size(900, 850))
        #_icon = wx.EmptyIcon()
        #_icon.CopyFromBitmap(wx.Bitmap(os.path.join('img', 'logo.ico'), wx.BITMAP_TYPE_ICO))
        #self.SetIcon(_icon)
        if wx.Platform == "__WXMSW__":
            exeName = win32api.GetModuleFileName(win32api.GetModuleHandle(None))
            icon = wx.Icon(exeName + ";0", wx.BITMAP_TYPE_ICO)
            self.SetIcon(icon)
        global execmessages, visible_abc_code
        self.settings = settings
        self.current_svg_tune = None # 1.3.6.2 [JWdJ] 2015-02
        self.svg_tunes = AbcTunes()
        self.current_midi_tune = None # 1.3.6.3 [JWdJ] 2015-03
        self.midi_tunes = AbcTunes()
        self.__current_page_index = 0 # 1.3.6.2 [JWdJ] 2015-02
        self.loop_midi_playback = False
        self.applied_tempo_multiplier = 1.0 # 1.3.6.4 [JWdJ] 2015-05
        self.is_closed = False
        self.app_dir = app_dir
        self.cache_dir = os.path.join(self.app_dir, 'cache')
        self.settings_file = os.path.join(self.app_dir, 'settings1.3.dat')
        self._current_file = None
        self.untitled_number = 1
        self.document_name = _('Untitled') + ' %d' % self.untitled_number
        self.author = ''
        self.record_thread = None
        self.zoom_factor = 1.0
        self.selected_note_indices = []
        self.selected_note_descs = []
        self.keyboard_input_mode = False
        self.last_refresh_time = datetime.now()
        self.last_line_number_selected = -1
        self.queue_number_refresh_music = 0
        self.queue_number_movement = 0
        self.field_reference_frame = None
        self.find_data = wx.FindReplaceData()
        self.find_dialog = None
        self.replace_dialog = None
        self.settingsbook = None
        self.find_data.SetFlags(wx.FR_DOWN)
        self.execmessage_time = datetime.now() # 1.3.6 [SS] 2014-12-11

        # 1.3.6 [SS] 2014-12-07
        self.statusbar = self.CreateStatusBar()
        #print 'statusbar = ',self.statusbar
        self.SetMinSize((100, 100))
        self.manager = aui.AuiManager(self)

        self.printData = wx.PrintData()
        self.printData.SetPrintMode(wx.PRINT_MODE_PRINTER)

        self.setup_menus()
        self.setup_toolbar()

        try:
            if wx.Platform == "__WXMAC__":
                self.mc = wx.media.MediaCtrl(self, szBackend=wx.media.MEDIABACKEND_QUICKTIME)
            elif wx.Platform == "__WXMSW__":
                if platform.release() == 'XP':
                    self.mc = wx.media.MediaCtrl(self, szBackend=wx.media.MEDIABACKEND_DIRECTSHOW)
                else:
                    self.mc = wx.media.MediaCtrl(self, szBackend=wx.media.MEDIABACKEND_WMP10)
            else:
                self.mc = wx.media.MediaCtrl(self)
            self.mc.Hide()
            self.Bind(wx.media.EVT_MEDIA_LOADED, self.OnMediaLoaded)
            # Bind other event to be sure to act on the first one that occurs (evenif they should be almost at the same time)
            self.Bind(wx.media.EVT_MEDIA_FINISHED, self.OnMediaFinished)
            self.Bind(wx.media.EVT_MEDIA_STOP, self.OnMediaStop)
        except NotImplementedError:
            self.mc = None  # if media player not supported on this platform

        # self.media_file_loaded = False
        self.play_music_thread = None

        self.tune_list = FlexibleListCtrl(self, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL) #wx.LC_NO_HEADER)

        self.tune_list.InsertColumn(0, _('No.'), wx.LIST_FORMAT_RIGHT)
        self.tune_list.InsertColumn(1, _('Title'))
        #self.tune_list.InsertColumn(2, _('Rythm'))

        self.tune_list.SetAutoLayout(True)
        self.editor = stc.StyledTextCtrl(self, -1)
        self.editor.SetCodePage(stc.STC_CP_UTF8)

        # p09 include line numbering in the edit window. 2014-10-14 [SS]
        self.editor.SetMarginLeft(15)
        self.editor.SetMarginWidth(1,40)
        self.editor.SetMarginType(1,stc.STC_MARGIN_NUMBER)

        # 1.3.6.2 [JWdJ] 2015-02
        self.renderer = SvgRenderer(self.settings['can_draw_sharps_and_flats'])
        self.music_pane = MusicScorePanel(self, self.renderer)
        self.music_pane.SetBackgroundColour((255, 255, 255))
        self.music_pane.OnNoteSelectionChangedDesc = self.OnNoteSelectionChangedDesc

        error_font_size = get_normal_fontsize() # 1.3.6.3 [JWDJ] one function to set font size
        self.error_msg = wx.TextCtrl(self, -1, '', size=(200, 100), style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER | wx.TE_READONLY | wx.TE_DONTWRAP)
        self.error_msg.SetFont(wx.Font(error_font_size, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Courier New"))
        self.error_pane = aui.AuiPaneInfo().Name("error message").Caption(_("ABC errors")).CloseButton(True).BestSize((160, 80)).Bottom()
        self.error_pane.Hide()
        self.error_msg.Hide() # 1.3.7 [JWdJ] 2016-01-06

         # 1.3.6.3 [JWdJ] 2015-04-21 ABC Assist added
        from abc_assist_panel import AbcAssistPanel  # 1.3.7.1 [JWDJ] 2016-1 because of translation this import has to be done as late as possible
        self.abc_assist_panel = AbcAssistPanel(self, self.editor, cwd, self.settings)
        self.assist_pane = aui.AuiPaneInfo().Name("abcassist").CaptionVisible(True).Caption(_("ABC assist")).\
            CloseButton(True).MinimizeButton(False).MaximizeButton(False).\
            Left().BestSize(265, 300) # .PaneBorder(False) # Fixed()

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

        self.manager.Update()
        self.default_perspective = self.manager.SavePerspective()


        self.styler = ABCStyler(self.editor)
        self.InitEditor()
        self.editor.Colourise(0, self.editor.GetLength())

        self.editor.SetDropTarget(MyFileDropTarget(self))
        self.tune_list.SetDropTarget(MyFileDropTarget(self))
        self.music_pane.SetDropTarget(MyFileDropTarget(self))
        self.GetMenuBar().SetDropTarget(MyFileDropTarget(self))

        self.tune_list_last_width = self.tune_list.GetSize().width

        self.index = 1
        self.tunes = []
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer.Start(2000, wx.TIMER_CONTINUOUS)

        self.tune_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnTuneSelected)
        self.tune_list.Bind(wx.EVT_LEFT_DCLICK, self.OnTuneDoubleClicked)
        self.tune_list.Bind(wx.EVT_LEFT_DOWN, self.OnTuneListClick)
        self.editor.Bind(stc.EVT_STC_STYLENEEDED, self.styler.OnStyleNeeded)
        self.editor.Bind(stc.EVT_STC_CHANGE, self.OnChange)
        self.editor.Bind(stc.EVT_STC_MODIFIED, self.OnModified)
        self.editor.Bind(stc.EVT_STC_UPDATEUI, self.OnPosChanged)
        self.editor.Bind(wx.EVT_LEFT_UP, self.OnEditorMouseRelease)
        ##self.editor.Bind(stc.EVT_STC_KEY, self.OnKeyPressed)
        self.editor.Bind(wx.EVT_KEY_DOWN, self.OnKeyDownEvent)
        self.editor.Bind(wx.EVT_CHAR, self.OnCharEvent)
        self.editor.CmdKeyAssign(ord('+'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMIN)
        self.editor.CmdKeyAssign(ord('-'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMOUT)
        #self.editor.CmdKeyClearAll()
        #self.editor.CmdKeyAssign(ord('\t'), 0, 2172)  # not used
        self.music_pane.Bind(wx.EVT_LEFT_DCLICK, self.OnMusicPaneDoubleClick)
        #self.music_pane.Bind(wx.EVT_KEY_DOWN, self.OnMusicPaneKeyDown)

        self.load_settings(load_window_size_pos=True)
        self.restore_settings()

        # p09 Enable the play button if midiplayer_path is defined. 2014-10-14 [SS]
        self.update_play_button() # 1.3.6.3 [JWdJ] 2015-04-21 centralized playbutton enabling

        #1.3.6 [SS] 2014-12-07 (self.statusbar)
        #1.3.6.2 [SS] 2015-03-03 self.statusbar removed
        self.music_update_thread = MusicUpdateThread(self, self.settings, self.cache_dir)

        self.tune_list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClickList, self.tune_list)

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(EVT_RECORDSTOP, self.OnRecordStop)
        self.Bind(EVT_MUSIC_UPDATE_DONE, self.OnMusicUpdateDone)
        self.editor.Bind(wx.EVT_KEY_DOWN, self.OnUpdate)
        self.music_pane.Bind(wx.EVT_KEY_DOWN, self.OnUpdate)
        self.tune_list.Bind(wx.EVT_KEY_DOWN, self.OnUpdate)
        self.music_pane.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)

        self.UpdateTuneList()
        self.UpdateTuneListVisibility(True)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnPlayTimer)
        self.timer.Start(150)
        self.music_update_thread.start()

        self.editor.SetFocus()
        wx.CallLater(100, self.editor.SetFocus)
        self.GrayUngray()

        self.OnClearCache(None) # P09 2014-10-26

        # 1.3.7 [JWdJ] 2016-01-06
        self.ShowAbcAssist(self.settings.get('show_abc_assist', False))

        # 1.3.6.3 [SS] 2015-05-04
        self.statusbar.SetStatusText(_('This is the status bar. Check it occasionally.'))
        execmessages = _('You are running {0} on {1}\nYou can get the latest version on http://sourceforge.net/projects/easyabc/\n'.format(program_name, wx.Platform))

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
            self.cur_page_combo.Select(value)

    @property
    def current_file(self):
        return self._current_file

    @current_file.setter
    def current_file(self, value):
        self._current_file = value
        if value:
            recent_files = self.settings.get('recentfiles', '').split('|')
            if value in recent_files:
                recent_files.remove(value)
            recent_files.insert(0, value)
            if len(recent_files) > 10:
                recent_files = recent_files[:10]
            self.settings['recentfiles'] = '|'.join(recent_files)
            self.update_recent_files_menu()

    def OnPageSetup(self, evt):
        psdd = wx.PageSetupDialogData(self.printData)
        psdd.CalculatePaperSizeFromId()
        psdd.EnableMargins(False)
        dlg = wx.PageSetupDialog(self, psdd)
        try:
            dlg.ShowModal()

            # this makes a copy of the wx.PrintData instead of just saving
            # a reference to the one inside the PrintDialogData that will
            # be destroyed when the dialog is destroyed
            self.printData = wx.PrintData( dlg.GetPageSetupData().GetPrintData() )
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window

    def OnPrint(self, event):
        tune = self.GetSelectedTune()
        if not tune:
            return
        # if landscape is set in the ABC code, let that influence the page format
        if ('%%landscape 1' in (tune.header + tune.abc) or
            '%%landscape true' in (tune.header + tune.abc)):
            self.printData.SetOrientation(wx.LANDSCAPE)
        if ('%%landscape 0' in (tune.header + tune.abc) or
            '%%landscape false' in (tune.header + tune.abc)):
            self.printData.SetOrientation(wx.PORTRAIT)
        use_landscape = self.printData.GetOrientation() == wx.LANDSCAPE

        # 1.3.6 [SS] 2014-12-02  2014-12-07
        svg_files, error = AbcToSvg(tune.abc, tune.header, self.cache_dir,
                                    self.settings,
                                    minimal_processing=True,
                                    landscape=use_landscape)
        self.update_statusbar_and_messages()
        if svg_files:
            pdd = wx.PrintDialogData(self.printData)
            pdd.SetToPage(len(svg_files))
            printer = wx.Printer(pdd)
            printout = MusicPrintout(svg_files, zoom=10.0, title=tune.title,
                                     can_draw_sharps_and_flats=self.settings['can_draw_sharps_and_flats'])

            if not printer.Print(self, printout, True):
                wx.MessageBox(_("There was a problem printing.\nPerhaps your current printer is not set correctly?"), _("Printing"), wx.OK)
            else:
                self.printData = wx.PrintData( printer.GetPrintDialogData().GetPrintData() )
            printout.Destroy()

    def OnPrintPreview(self, event):
        tune = self.GetSelectedTune()
        if tune is None:
            return
        # if landscape is set in the ABC code, let that influence the page format
        if ('%%landscape 1' in (tune.header + tune.abc) or
            '%%landscape true' in (tune.header + tune.abc)):
            self.printData.SetOrientation(wx.LANDSCAPE)
        if ('%%landscape 0' in (tune.header + tune.abc) or
            '%%landscape false' in (tune.header + tune.abc)):
            self.printData.SetOrientation(wx.PORTRAIT)
        use_landscape = self.printData.GetOrientation() == wx.LANDSCAPE
        #1.3.6 [SS] 2014-12-02 2014-12-07
        svg_files, error = AbcToSvg(tune.abc, tune.header, self.cache_dir,
                                    self.settings,
                                    minimal_processing=True,
                                    landscape=use_landscape)
        self.update_statusbar_and_messages()
        if svg_files:
            data = wx.PrintDialogData(self.printData)
            printout = MusicPrintout(svg_files, zoom=1.0, title=tune.title, painted_on_screen=True, can_draw_sharps_and_flats=self.settings['can_draw_sharps_and_flats'])
            printout2 = MusicPrintout(svg_files, zoom=10.0, title=tune.title, can_draw_sharps_and_flats=self.settings['can_draw_sharps_and_flats'])
            self.preview = wx.PrintPreview(printout, printout2, data)

            if wx.Platform == "__WXMAC__":
                self.preview.SetZoom(100)

            if not self.preview.Ok():
                return

            pfrm = wx.PreviewFrame(self.preview, self, _("EasyABC - print preview"))

            pfrm.Initialize()
            pfrm.SetPosition(self.GetPosition())
            pfrm.SetSize(self.GetSize())
            pfrm.Show(True)

    def GetAbcToPlay(self):
        tune = self.GetSelectedTune()
        if tune:
            position, end_position = tune.offset_start, tune.offset_end
            if end_position > position:
                if len(self.selected_note_descs) > 2: ## and False:
                    text = self.editor.GetTextRange(position, end_position).encode('utf-8', 'ignore')
                    notes = get_notes_from_abc(text)
                    num_header_lines, first_note_line_index = self.get_num_extra_header_lines(tune)

                    # workaround for the fact the abcm2ps returns incorrect row numbers
                    # check the row number of the first note and if it doesn't agree with the actual value
                    # then pretend that we have more or less extra header lines
                    if self.music_pane.current_page.notes: # 1.3.6.2 [JWdJ] 2015-02
                        actual_first_row = self.music_pane.current_page.notes[0][2]-1
                        correction = (actual_first_row - first_note_line_index)
                        num_header_lines += correction

                    temp = text.replace('\r\n', ' \n').replace('\r', '\n')  # re.sub(r'\r\n|\r', '\n', text)
                    line_start_offset = [m.start(0) for m in re.finditer(r'(?m)^', temp)]

                    selected_note_offsets = []
                    for (x, y, abc_row, abc_col, desc) in self.selected_note_descs:
                        abc_row -= num_header_lines
                        selected_note_offsets.append(line_start_offset[abc_row-1]+abc_col)

                    text = MutableString(text)

                    for i, (start_offset, end_offset, note_text) in enumerate(notes):
                        is_selected = any(p for p in selected_note_offsets if start_offset <= p < end_offset)
                        if not is_selected:
                            for j in range(start_offset, end_offset):
                                text[j] = ' '
                    text = str(text).decode('utf-8')
                    # for some strange reason the MIDI sequence seems to be cut-off in the end if the last note is short
                    # adding a silent extra note seems to fix this
                    text = text + os.linesep + '%%MIDI control 7 0' + os.linesep + 'A2'

                    return (tune, text)
            return (tune, self.editor.GetTextRange(position, end_position))
        return (tune, '')

    def parse_desc(self, desc):
        parts = desc.split()
        row, col = map(int, parts[1].split(':'))
        return (row, col)

    def get_num_extra_header_lines(self, tune):
        # how many lines are there before the X: line in the processed ABC code?

        # 1.3.6 [SS] 2014-12-17
        lines = re.split('\r\n|\r|\n', process_abc_code(self.settings,tune.abc,
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
            frame.load_settings()

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

    # 1.3.6.3 [JWdJ] 2015-04-21 added helper functions for playing MIDI
    def normalize_volume(self):
        if wx.Platform != "__WXMAC__":
            try: self.mc.Volume = 0.9
            except: pass

    def play(self):
        self.normalize_volume()
        self.mc.Play()

    def play_again(self):
        if not self.is_playing():
            self.mc.Seek(0)
            self.mc.Play()

    def stop_playing(self):
        if self.mc:
            self.play_button.SetBitmap(self.play_bitmap)
            self.mc.Stop()
            self.mc.Load('NONEXISTANT_FILE____.mid') # be sure the midi file is released 2014-10-25 [SS]

    def is_playing(self):
        return self.mc and self.mc.GetState() == wx.media.MEDIASTATE_PLAYING

    def is_paused(self):
        return self.mc and self.mc.GetState() == wx.media.MEDIASTATE_PAUSED

    def set_playback_rate(self, playback_rate):
        if self.mc and (self.is_playing() or wx.Platform != "__WXMAC__"):
            self.mc.PlaybackRate = playback_rate
            # self.normalize_volume() # [JWDJ] why here?

    def update_playback_rate(self):
        tempo_multiplier = self.get_tempo_multiplier() / self.applied_tempo_multiplier
        self.set_playback_rate(tempo_multiplier)

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
        self.update_playback_rate() # 1.3.6.4 [JWDJ]

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
        # self.media_file_loaded = False
        if self.mc.Load(path):
            if wx.Platform == "__WXMSW__" and platform.release() != 'XP':
                # 1.3.6.3 [JWDJ] 2015-3 It seems mc.Play() triggers the OnMediaLoaded event
                # time.sleep(0.15) # is way to short anyway (JWDJ)
                # self.OnMediaLoaded(None)
                self.mc.Play() # does not start playing but triggers OnMediaLoaded event
        else:
            wx.MessageBox(_("Unable to load %s: Unsupported format?") % path,
                          _("Error"), wx.ICON_ERROR | wx.OK)

    def OnMediaLoaded(self, evt):
        self.media_slider.SetRange(0, self.mc.Length())
        self.media_slider.SetValue(0)
        self.OnBpmSlider(None)
        def play():
            self.normalize_volume()
            # if wx.Platform == "__WXMAC__":
            #    time.sleep(0.3) # 1.3.6.4 [JWDJ] on Mac the first note is skipped the first time. hope this helps
            #self.mc.Seek(self.play_start_offset, wx.FromStart)
            self.play_button.SetBitmap(self.pause_bitmap)
            self.play()
            self.update_playback_rate()

        wx.CallAfter(play)

    def OnMediaStop(self, evt):
        #if media is finished but playback as a loop was used relaunch the playback immediatly
        #and prevent media of being stop (event is vetoed as explained in MediaCtrl documentation)
        if self.mc and self.loop_midi_playback:
            self.play_again()
            evt.Veto()

    def OnMediaFinished(self, evt):
        #if media is finished but playback as a loop was used relaunch the playback immediatly
        # (OnMediaStop should already have restarted it if required as event STOP arrive before FINISHED)
        if self.mc:
            if self.loop_midi_playback:
                self.play_again()
            else:
            # 1.3.6.3 [SS] 2015-05-04
                self.flip_tempobox(False)      
                self.stop_playing()
                self.reset_BpmSlider()

    def OnToolRecord(self, evt):
        if self.record_thread and self.record_thread.is_running:
            self.record_thread.abort()
        else:
            midi_in_device_ID = self.settings.get('midi_device_in', None)
            if midi_in_device_ID is None:
                self.OnMidiSettings(None)
                midi_in_device_ID = self.settings.get('midi_device_in', None)
            midi_out_device_ID = self.settings.get('midi_device_out', None)
            if midi_in_device_ID is not None:
                metre_1, metre_2 = map(int, self.settings['record_metre'].split('/'))
                self.record_thread = RecordThread(self, midi_in_device_ID, midi_out_device_ID, metre_1, metre_2, bpm = self.settings['record_bpm'])
                self.record_thread.start()

    def OnToolStop(self, evt):
        self.loop_midi_playback = False
        self.stop_playing()
        # 1.3.6.3 [SS] 2015-04-03
        #self.play_panel.Show(False)
        self.flip_tempobox(False)
        self.reset_BpmSlider()
        if wx.Platform != "__WXMSW__":
            self.toolbar.Realize() # 1.3.6.4 [JWDJ] fixes toolbar repaint bug for Windows
        if self.record_thread and self.record_thread.is_running:
            self.OnToolRecord(None)

    def OnSeek(self, evt):
        self.mc.Seek(self.media_slider.GetValue())

    def OnZoomSlider(self, evt):
        old_factor = self.zoom_factor
        self.zoom_factor = float(self.zoom_slider.GetValue()) / 1000
        if self.zoom_factor != old_factor:
            self.renderer.zoom = self.zoom_factor # 1.3.6.2 [JWdJ] 2015-02
            self.music_pane.redraw()

    def OnPlayTimer(self, evt):
        if self.mc and not self.is_closed:
            offset = self.mc.Tell()
            self.media_slider.SetValue(offset)
            #if self.mc.GetState() == wx.media.MEDIASTATE_PLAYING and offset > self.play_end_offset + 300:
            #    self.mc.Stop()
            if offset <= 0 and not self.is_playing() and self.loop_midi_playback:
                self.play_again()

    def OnRecordBpmSelected(self, evt):
        for item in self.bpm_menu.GetMenuItems():
            if item.GetId() == evt.GetId():
                self.settings['record_bpm'] = int(item.GetText())
                if self.record_thread:
                    self.record_thread.bpm = self.settings['record_bpm']

    def OnRecordMetreSelected(self, evt):
        for item in self.metre_menu.GetMenuItems():
            if item.GetId() == evt.GetId():
                self.settings['record_metre'] = item.GetText()

    # 1.3.6.3 [SS] 2015-05-03
    def flip_tempobox(self,state):
        ''' rearranges the toolbar depending on whether a midi file is played using the
            mc media player'''
        # self.show_toolbar_panel(self.bpm_slider.Parent, state)
        self.show_toolbar_panel(self.media_slider.Parent, state)
        self.toolbar.Realize()

    def show_toolbar_panel(self, panel, visible):
        #for sizer_item in panel.Sizer.Children:
        #    sizer_item.Show(visible)
        panel.Show(visible)

    def setup_toolbar(self):
        self.toolbar = aui.AuiToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize)#, agwStyle=aui.AUI_TB_DEFAULT_STYLE | aui.AUI_TB_OVERFLOW)
        self.toolbar.SetToolAlignment(wx.ALIGN_CENTER_VERTICAL)
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

        self.bpm_menu = bpm_menu = wx.Menu()
        for i, bpm in enumerate([30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140]):
            id = 5501 + i
            item = wx.MenuItem(bpm_menu, id, str(bpm), kind=wx.ITEM_RADIO)
            bpm_menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnRecordBpmSelected, id=id)
        self.metre_menu = metre_menu = wx.Menu()
        for i, metre in enumerate(['2/4', '3/4', '4/4', '5/4']):
            id = 5601 + i
            item = wx.MenuItem(metre_menu, id, metre, kind=wx.ITEM_RADIO)
            metre_menu.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnRecordMetreSelected, id=id)
        self.record_popup = record_popup = wx.Menu()
        record_popup.AppendMenu(5500, _('Beats per minute'), bpm_menu)
        record_popup.AppendMenu(5600, _('Metre'), metre_menu)

        button_style = platebtn.PB_STYLE_DEFAULT | platebtn.PB_STYLE_NOBG

        self.play_bitmap = wx.Image(os.path.join(cwd, 'img', 'toolbar_play.png')).ConvertToBitmap()
        self.pause_bitmap = wx.Image(os.path.join(cwd, 'img', 'toolbar_pause.png')).ConvertToBitmap()
        self.play_button = play =  platebtn.PlateButton(self.toolbar, self.id_play, "", self.play_bitmap, style=button_style)
        self.stop_button = stop =  platebtn.PlateButton(self.toolbar, self.id_stop, "", wx.Image(os.path.join(cwd, 'img', 'toolbar_stop.png')).ConvertToBitmap(), style=button_style)
        self.record_btn = record = platebtn.PlateButton(self.toolbar, self.id_record, "", wx.Image(os.path.join(cwd, 'img', 'toolbar_record.png')).ConvertToBitmap(), style=button_style)
        ##self.refresh = refresh = platebtn.PlateButton(self.toolbar, self.id_refresh, "", wx.Image(os.path.join(cwd, 'img', 'toolbar_refresh.png')).ConvertToBitmap(), style=button_style)
        #add_tune = platebtn.PlateButton(self.toolbar, self.id_add_tune, "", wx.Image(os.path.join(cwd, 'img', 'new.gif')).ConvertToBitmap(), style=button_style)

        play.SetHelpText('Play (F6)')
        record.SetMenu(record_popup)
        self.toolbar.AddControl(play)
        self.toolbar.AddControl(stop)
        self.toolbar.AddControl(record)
        ##self.toolbar.AddControl(refresh)
        self.toolbar.AddSeparator()

        # 1.3.6.3 [JWdJ] 2015-04-26 turned off abc assist for it is not finished yet
        abc_assist = platebtn.PlateButton(self.toolbar, self.id_abc_assist, "", wx.Image(os.path.join(cwd, 'img', 'bulb.png')).ConvertToBitmap(), style=button_style)
        abc_assist.SetHelpText(_('ABC assist'))
        abc_assist.SetToolTip(wx.ToolTip(_('ABC assist'))) # 1.3.7.0 [JWdJ] 2015-12
        self.toolbar.AddControl(abc_assist, label=_('ABC assist'))
        self.Bind(wx.EVT_BUTTON, self.OnToolAbcAssist, abc_assist) # 1.3.6.2 [JWdJ] 2015-03

        ornamentations = self.toolbar.AddSimpleTool(self.id_ornamentations, "", wx.Image(os.path.join(cwd, 'img', 'toolbar_ornamentations.png')).ConvertToBitmap(), 'Ornamentations')
        dynamics = self.toolbar.AddSimpleTool(self.id_dynamics, "", wx.Image(os.path.join(cwd, 'img', 'toolbar_dynamics.png')).ConvertToBitmap(), 'Dynamics')
        directions = self.toolbar.AddSimpleTool(self.id_directions, "", wx.Image(os.path.join(cwd, 'img', 'toolbar_directions.png')).ConvertToBitmap(), 'Directions')
        self.toolbar.AddSeparator()

        self.zoom_slider = self.add_slider_to_toolbar(_('Zoom'), False, 1000, 500, 3000, (30, 60), (130, 22))
        self.zoom_slider.SetTickFreq(10, 0)
        self.Bind(wx.EVT_SLIDER, self.OnZoomSlider, self.zoom_slider)

        # 1.3.6.2 [JWdJ] 2015-02-15 text 'Page' was drawn multiple times. Replaced StaticLabel with StaticText
        self.cur_page_combo = self.add_combobox_to_toolbar(_('Page'), choices=['99 / 99'], style=wx.CB_DROPDOWN | wx.CB_READONLY)
        self.cur_page_combo.Select(0)
        self.Bind(wx.EVT_COMBOBOX, self.OnPageSelected, self.cur_page_combo)

        # 1.3.6.3 [SS] 2015-05-03
        self.bpm_slider = self.add_slider_to_toolbar(_('Tempo'), False, 0, -100, 100, (-1, -1), (130, 22))
        if wx.Platform == "__WXMSW__":
            self.bpm_slider.SetTick(0)  # place a tick in the middle for neutral tempo
        self.media_slider = self.add_slider_to_toolbar(_('Play position'), False, 25, 1, 100, (-1, -1), (130, 22))

        self.Bind(wx.EVT_SLIDER, self.OnSeek, self.media_slider)
        self.Bind(wx.EVT_SLIDER, self.OnBpmSlider, self.bpm_slider)
        self.bpm_slider.Bind(wx.EVT_LEFT_DOWN, self.OnBpmSliderClick)

        self.Bind(wx.EVT_TOOL, self.OnToolDynamics, dynamics)
        self.Bind(wx.EVT_TOOL, self.OnToolOrnamentation, ornamentations)
        self.Bind(wx.EVT_TOOL, self.OnToolDirections, directions)
        play.Bind(wx.EVT_LEFT_DOWN, self.OnToolPlay)
        play.Bind(wx.EVT_LEFT_DCLICK, self.OnToolPlayLoop)
        self.Bind(wx.EVT_BUTTON, self.OnToolStop, stop)
        self.Bind(wx.EVT_BUTTON, self.OnToolRecord, record)
        ##self.Bind(wx.EVT_BUTTON, self.OnToolRefresh, refresh)
        ##self.Bind(wx.EVT_BUTTON, self.OnToolAddTune, add_tune)

        self.popup_upload = self.create_upload_context_menu()

        # 1.3.6.3 [JWDJ] fixes toolbar repaint bug
        self.flip_tempobox(False)
        #self.play_panel.Show(False)
        self.cur_page_combo.Parent.Show(False)

        self.manager.AddPane(self.toolbar, aui.AuiPaneInfo().
                            Name("tb2").Caption("Toolbar2").
                            ToolbarPane().Top().Floatable(True).Dockable(False))

    def add_slider_to_toolbar(self, label_text, show_value, *args, **kwargs):
        panel = wx.Panel(self.toolbar, -1)
        controls = [wx.Slider(panel, -1, *args, **kwargs)]
        if show_value:
            controls.append(wx.StaticText(panel, -1, str(kwargs['value'])))
        self.add_label_and_controls_to_panel(panel, label_text, controls)
        self.toolbar.AddControl(panel)
        if len(controls) == 1:
            return controls[0]
        else:
            return tuple(controls)

    def add_combobox_to_toolbar(self, label_text, *args, **kwargs):
        panel = wx.Panel(self.toolbar, -1)
        control = wx.ComboBox(panel, -1, *args, **kwargs)
        self.add_label_and_controls_to_panel(panel, label_text, [control])
        self.toolbar.AddControl(panel)
        return control

    @staticmethod
    def add_label_and_controls_to_panel(panel, label_text, controls):
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(wx.StaticText(panel, -1, u'{0}: '.format(label_text)), flag=wx.ALIGN_CENTER_VERTICAL)
        for control in controls:
            box.Add(control, flag=wx.ALIGN_CENTER_VERTICAL)
        box.AddSpacer(20)
        panel.SetSizer(box)
        panel.SetAutoLayout(True)

    def OnViewRythm(self, evt):
        pass

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
                return len([l for l in re.split(r'\r\n|\r|\n', notes) if l.strip()])  # return number of non-empty lines
            except IndexError:
                return 1

        result = []
        for i in range(self.tune_list.GetItemCount()):
            tune = self.GetTune(i)

            # make a copy of the tune header in order to be able to restore it after the incip extraction
            lines = re.split('\r\n|\r|\n', tune.abc)
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
                elif re.match('\s*%', line):
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
        for i in range(self.editor.GetLineCount()):
            line = self.editor.GetLine(i)
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
            pdf_file = AbcToPDF(self.settings,abc, '', self.cache_dir, self.settings.get('abcm2ps_extra_params', ''),
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
                lines = re.split('\r\n|\r|\n', self.editor.GetText())
                for i in range(len(lines)):
                    if re.match('X:\s*\d+\s*$', lines[i]):
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
    def OnSearchDirectories(self,evt):
        win = wx.FindWindowByName('searcher')
        if win is not None:
            return
        self.search = MySearchFrame(self,self.settings)
        self.search.Show()



    def OnUploadTune(self, evt):
        tune = self.GetSelectedTune()
        if tune:
            if not self.author:
                dialog = wx.TextEntryDialog(self, _('Please enter your full name (your FolkWiki entries will henceforth be associated with this name): '), _('Enter your name'), '')
                if dialog.ShowModal() != wx.ID_OK:
                    return
                self.author = dialog.GetValue().strip()

            url = upload_tune(tune.abc, self.author)
            webbrowser.open(url)

    def GetFileNameForTune(self, tune, file_extension):
        filename = tune.title
        if not filename:
            filename = '%s' % tune.xnum
        filename = re.sub(r'[\\/:"*?<>|]', ' ', filename).strip()
        filename = filename + file_extension
        return filename

    def OnExportMidi(self, evt):
        # 1.3.6.3 [SS] 2015-05-07
        global execmessages

        tune = self.GetSelectedTune()
        if tune:
            # 1.3.6 [SS] 2014-11-16 2014-12-08
            tempo_multiplier = self.get_tempo_multiplier()
            midi_tune = AbcToMidi(tune.abc, tune.header, self.cache_dir, self.settings, self.statusbar, tempo_multiplier)

            if midi_tune:
                midi_file = midi_tune.midi_file
                filename = self.GetFileNameForTune(tune, '.mid')
                dlg = wx.FileDialog(self, message=_("Export tune as ..."), defaultFile=filename, wildcard="Midi file (*.mid)|*.mid", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                try:
                    if dlg.ShowModal() == wx.ID_OK:
                        shutil.copy(midi_file, dlg.GetPath())
                        # 1.3.6.3 [SS] 2015-05-07
                        filepath = dlg.GetPath()
                        execmessages = execmessages + u'creating '+ filepath.encode('utf-8') + u'\n'
                finally:
                    dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window
                    midi_tune.cleanup()

            # 1.3.6 [SS] 2014-12-08
            self.statusbar.SetStatusText(_('Midi file was written'))

    #Add an export all tunes to MIDI option
    def OnExportAllMidi(self, evt):
        # 1.3.6.3 [SS] 2015-05-07
        global execmessages

        dlg = wx.DirDialog(self, message=_("Choose a directory..."), style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        ntunes = self.tune_list.GetItemCount()
        outstring = _('There are {0} midi files to create').format(ntunes)
        self.statusbar.SetStatusText(outstring)
        progdialog = None
        try:
            if dlg.ShowModal() == wx.ID_OK:
                tunes = [self.GetTune(i) for i in range(self.tune_list.GetItemCount())]
                #tunes = [self.GetTune(i) for i in ntunes]

                # 1.3.6 [SS] 2014-12-08
                progdialog = wx.ProgressDialog(_('Searching directory'), _('Remaining time'),
                     ntunes,style = wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME |
                     wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE)

                j = 0
                for tune in tunes:

                    j += 1
                    running = progdialog.Update(j)
                    if running[0] == False or j > ntunes:
                        break

                    # 1.3.6 [SS] 2014-11-16 2014-12-08
                    tempo_multiplier = self.get_tempo_multiplier()
                    midi_tune = AbcToMidi(tune.abc, tune.header, self.cache_dir, self.settings, self.statusbar, tempo_multiplier)

                    if midi_tune:
                        midi_file = midi_tune.midi_file
                        filename = self.GetFileNameForTune(tune, '.mid')
                        filepath = os.path.join(dlg.GetPath(), filename)
#                       dlg = wx.FileDialog(self, message=_("Export tune as ..."), defaultFile=filename, wildcard="Midi file (*.mid)|*.mid", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
#                       if dlg.ShowModal() == wx.ID_OK:
                        try:
                            shutil.copy(midi_file, filepath.encode('utf-8'))
                        except:
                            print 'failed to create ',filepath.encode('utf-8')

                        # 1.3.6.3 [SS] 2015-05-07
                        execmessages = execmessages + u'creating '+ filepath.encode('utf-8') + u'\n'

                        midi_tune.cleanup()
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window
        # 1.3.6 [SS] 2014-12-08
            if progdialog:
                progdialog.Destroy()
        self.statusbar.SetStatusText(_('All midi files were written'))

    #Add an export all tunes to individual PDF option
    def OnExportAllPDFFiles(self, evt):
        # 1.3.6 [SS] 2014-12-08
        ntunes = self.tune_list.GetItemCount()
        outstring = _('There are %d PDF files to create') % ntunes
        self.statusbar.SetStatusText(outstring)

        dlg = wx.DirDialog(self, message=_("Choose a directory..."), style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

        try:
            if dlg.ShowModal() == wx.ID_OK:
                tunes = [self.GetTune(i) for i in range(self.tune_list.GetItemCount())]
                #for i in range(self.tune_list.GetItemCount()):
                #    self.tune_list.Select(i)
                #    tunes.append(self.GetSelectedTune())

                # 1.3.6 [SS] 2014-12-08
                progdialog = wx.ProgressDialog(_('Searching directory'), _('Remaining time'),
                     ntunes,style = wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME |
                     wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE)
                j = 0

                global execmessages
                execmessages = u''

                for tune in tunes:
                    # 1.3.6 [SS] 2014-12-08
                    j += 1
                    running = progdialog.Update(j)
                    if running[0] == False or j > ntunes:
                        break

                    pdf_file = AbcToPDF(self.settings,tune.abc, tune.header, self.cache_dir, self.settings.get('abcm2ps_extra_params', ''),
                                                       self.settings.get('abcm2ps_path', ''),
                                                       self.settings.get('gs_path',''),
                                                       #self.settings.get('ps2pdf_path',''),
                                                       self.settings.get('abcm2ps_format_path', ''))
                    if pdf_file:
                        filename = self.GetFileNameForTune(tune, '.pdf')
                        filepath = os.path.join(dlg.GetPath(), filename)
                        # 1.3.6 [SS] 2014-12-08
                        try:
                            shutil.copy(pdf_file, filepath.encode('utf-8'))
                        except:
                            print 'failed to create ',filepath.encode('utf-8')
        finally:
            launch_file(dlg.GetPath())
            dlg.Destroy()
            # 1.3.6 [SS] 2014-12-08
            progdialog.Destroy()
            self.statusbar.SetStatusText(_('PDF files created.'))

    def OnExportPDF(self, evt):
        if not os.path.exists(self.settings.get('gs_path')):
            dlg = wx.MessageDialog(self, _('ghostscript was not found here. Go to settings and indicate the path'), _('Warning'), wx.OK)
            dlg.ShowModal()
            return
        tune = self.GetSelectedTune()
        if tune:
            global execmessages
            execmessages = u''
            pdf_file = AbcToPDF(self.settings,tune.abc, tune.header, self.cache_dir, self.settings.get('abcm2ps_extra_params', ''),
                                                       self.settings.get('abcm2ps_path', ''),
                                                       self.settings.get('gs_path',''),
                                                       #self.settings.get('ps2pdf_path',''),
                                                       self.settings.get('abcm2ps_format_path', ''))
            if pdf_file:
                filename = self.GetFileNameForTune(tune, '.pdf')
                dlg = wx.FileDialog(self, message=_("Export tune as ..."), defaultFile=filename, wildcard=_("PDF file") + " (*.pdf)|*.pdf", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                try:
                    if dlg.ShowModal() == wx.ID_OK:
                        self.copy_to_destination_and_launch_file(pdf_file, dlg.GetPath())
                finally:
                    dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window

    def OnExportSVG(self, evt):
        tune = self.GetSelectedTune()
        if tune:
            filename = self.GetFileNameForTune(tune, '.svg')
            dlg = wx.FileDialog(self, message=_("Export tune as ..."), defaultFile=filename, wildcard=_("SVG file") + " (*.svg)|*.svg", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            try:
                if dlg.ShowModal() == wx.ID_OK:
                    path = dlg.GetPath()
                    #shutil.copy(svg_file, path)
                    # 1.3.6 [SS] 2014-12-02 2014-12-07
                    svg_files, error = AbcToSvg(tune.abc, tune.header,
                                                         self.cache_dir,
                                                         self.settings,
                                                         target_file_name=path,
                                                         with_annotations=False)
                    self.update_statusbar_and_messages()
                    if svg_files:
                        launch_file(svg_files[0])
                    else:
                        pass
            finally:
                dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window


    def OnExportMusicXML(self, evt):
        tune = self.GetSelectedTune()

        # 1.3.6 [SS] 2014-12-10
        global execmessages, visible_abc_code
        visible_abc_code = ''
        for abcline in tune.abc:
            visible_abc_code = visible_abc_code + abcline
        mxl = self.settings['xmlcompressed']
        pageFormat = []

        # 1.3.6 [SS] 2014-12-21 (does not work on musescore?)
        #if self.settings['xml_p'] != '' and self.settings['xml_p'] != 0:
            #p = self.settings['xml_p'].split(',')
            #for elem in p:
                #pageFormat.append(float(elem))
            #print pageFormat
        info_messages = []

        if tune:       # [SS] 1.3.6 2014-12-15
            if mxl:
                filename = self.GetFileNameForTune(tune, '.mxl')
                dlg = wx.FileDialog(self, message=_("Export tune as ..."), defaultFile=filename, wildcard=_('Compressed MusicXML') + " (*.mxl)|*.mxl", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            else:
                filename = self.GetFileNameForTune(tune, '.xml')
                dlg = wx.FileDialog(self, message=_("Export tune as ..."), defaultFile=filename, wildcard=_('MusicXML') + " (*.xml)|*.xml", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            try:
                if dlg.ShowModal() == wx.ID_OK:
                    try:
                        errors = []
                        #1.3.6 [SS] 2014-12-10
                        abc_to_xml(tune.header + os.linesep + tune.abc, dlg.GetPath(),mxl, pageFormat, info_messages)
                        execmessages = u'abc_to_mxl   compression = ' + str(mxl) + '\n'
                        for infoline in info_messages:
                            execmessages += infoline
                    except Exception as e:
                        error_msg = ''.join(traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)) + os.linesep + os.linesep.join(errors)
                        mdlg = ErrorFrame(self, _('Error during conversion of X:{0} ("{1}"): {2}').format(tune.xnum, tune.title, error_msg))
                        result = mdlg.ShowModal()
                        mdlg.Destroy()
            finally:
                dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window
            # 1.3.6 2014-11-12 2014-12-10 [SS]
            self.statusbar.SetStatusText(_('XML file was created.'))
            MyInfoFrame.update_text() # 1.3.6.3 [JWDJ] 2015-04-27
            MyAbcFrame.update_text() # 1.3.6.3 [JWDJ] 2015-04-27

    def OnExportAllMusicXML(self, evt):
        dlg = wx.DirDialog(self, message=_("Choose a directory..."), style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        ntunes = self.tune_list.GetItemCount()

        #1.3.6 [SS] 2014-12-10
        global execmessages
        mxl = self.settings['xmlcompressed']
        pageFormat = []
        info_messages = []
        execmessages = 'abc_to_mxl   compression = ' + str(mxl) + '\n'

        try:
            if dlg.ShowModal() == wx.ID_OK:
                tunes = [self.GetTune(i) for i in range(self.tune_list.GetItemCount())]
                #for i in range(self.tune_list.GetItemCount()):
                #    self.tune_list.Select(i)
                #    tunes.append(self.GetSelectedTune())

                # 1.3.6 [SS] 2014-12-08
                progdialog = wx.ProgressDialog(_('Searching directory'),_('Remaining time'),
                     ntunes,style = wx.PD_CAN_ABORT | wx.PD_ELAPSED_TIME |
                     wx.PD_REMAINING_TIME | wx.PD_AUTO_HIDE)
                j = 0

                for tune in tunes:

                    # 1.3.6 [SS] 2014-12-08
                    j += 1
                    running = progdialog.Update(j)
                    if running[0] == False or j > ntunes:
                        break

                    filename = self.GetFileNameForTune(tune, '.xml')
                    filepath = os.path.join(dlg.GetPath(), filename)
                    errors = []
                    # 1.3.6.3 [SS] 2015-05-07
                    info_messages = []
                    try:
                        abc_to_xml(tune.header + os.linesep + tune.abc, filepath, mxl, pageFormat, info_messages)
                    except Exception as e:
                        error_msg = ''.join(traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback)) + os.linesep + os.linesep.join(errors)
                        mdlg = ErrorFrame(self, _('Error during conversion of X:{0} ("{1}"): {2}').format(tune.xnum, tune.title, error_msg))
                        result = mdlg.ShowModal()
                        mdlg.Destroy()
                        if result != wx.ID_OK:  # if ok is pressed, continue to process other tunes, if cancel, do not process more tunes
                            break
                    # 1.3.6 [SS] 2014-12-10
                    for infoline in info_messages:
                        execmessages += infoline
        finally:
            dlg.Destroy()
            self.statusbar.SetStatusText(_('XML files were created.'))
            progdialog.Destroy()
            # 1.3.6 [SS] 2014-12-10
            MyInfoFrame.update_text() # 1.3.6.3 [JWDJ] 2015-04-27


    def OnExportHTML(self, evt):
        tune = self.GetSelectedTune()
        if tune:
            filename = self.GetFileNameForTune(tune, '.html')
            dlg = wx.FileDialog(self, message=_("Export tune as ..."), defaultFile=filename, wildcard=_("HTML file") + " (*.html)|*.html", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            try:
                if dlg.ShowModal() == wx.ID_OK:
                    path = dlg.GetPath()
                    # 1.3.6 [SS] 2014-12-02 2014-12-07
                    svg_files, error = AbcToSvg(tune.abc, tune.header,
                                                         self.cache_dir,
                                                         self.settings,
                                                         with_annotations=False)
                    self.update_statusbar_and_messages()
                    if svg_files:
                        f = codecs.open(path, 'wb', 'UTF-8')
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
                        launch_file(path)
            finally:
                dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window

    def OnExportAllHTML(self, evt):
        global execmessages # 1.3.6.3 [SS] 2015-05-09
        tunes = []
        for i in range(self.tune_list.GetItemCount()):
            self.tune_list.Select(i)
            tunes.append(self.GetSelectedTune())
        if tunes:
            if self.current_file:
                filename = os.path.splitext(self.current_file)[0] + '.html'
            else:
                filename = ''
            dlg = wx.FileDialog(self, message=_("Export all tunes as ..."), defaultFile=os.path.basename(filename), wildcard=_("HTML file") + " (*.html)|*.html", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            try:
                if dlg.ShowModal() == wx.ID_OK:
                    self.SetCursor(wx.HOURGLASS_CURSOR)
                    path = dlg.GetPath()
                    # 1.3.6.3 [SS] 2015-05-09
                    execmessages = u'creating ' + path  + '\n'
                    f = codecs.open(path, 'wb', 'UTF-8')
                    f.write('''<html xmlns="http://www.w3.org/1999/xhtml">''')
                    f.write('''<head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
                      <style type="text/css">
                        svg { float: left; clear: both; }
                      </style>
                    </head>
                    <body>\n\n''')
                    for tune in tunes:
                        # 1.3.6 [SS] 2014-12-02 2014-12-07
                        svg_files, error = AbcToSvg(tune.abc, tune.header,
                                                             self.cache_dir,
                                                             self.settings,
                                                             with_annotations=False,
                                                             one_file_per_page=False)
                        self.update_statusbar_and_messages()
                        if svg_files:
                            for fn in svg_files:
                                svg = codecs.open(fn, 'rb', 'UTF-8').read()
                                svg = svg[svg.index('<svg'):]
                                f.write(svg)
                                f.write('\n\n')
                    f.write('</body></html>')
                    self.SetCursor(wx.STANDARD_CURSOR)
                    launch_file(path)
            finally:
                dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window

    def createArchive(self, rootDir, outputPath):
        cwd = os.getcwd()
        os.chdir(rootDir)
        fout.write('mimetype', compress_type = zipfile.ZIP_STORED)
        fileList = [os.path.join('META-INF', 'container.xml'), os.path.join('OEBPS', 'content.opf')]
        for itemPath in EpubBook.__listManifestItems(os.path.join('OEBPS', 'content.opf')):
            fileList.append(os.path.join('OEBPS', itemPath))
        for filePath in fileList:
            fout.write(filePath, compress_type = zipfile.ZIP_DEFLATED)
        fout.close()
        os.chdir(cwd)


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
            launch_file(destination_path)
        except IOError as ex:
            print u'Failed to create %s: %s' % (destination_path.encode('utf-8'), os.strerror(ex.errno))

    def OnExportAllPDF(self, evt):
        if self.current_file:
            filename = os.path.splitext(self.current_file)[0] + '.pdf'
        else:
            filename = ''
        default_dir, filename = os.path.split(filename)
        dlg = wx.FileDialog(self, message=_("Export all tunes as ..."), defaultDir=default_dir, defaultFile=filename, wildcard=_("PDF file") + " (*.pdf)|*.pdf", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                self.SetCursor(wx.HOURGLASS_CURSOR)
                global execmessages
                execmessages = u''
                pdf_file = AbcToPDF(self.settings,self.editor.GetText(), '', self.cache_dir, self.settings.get('abcm2ps_extra_params', ''),
                                                                               self.settings.get('abcm2ps_path', ''),
                                                                               self.settings.get('gs_path',''),
                                                                               #self.settings.get('ps2pdf_path',''),
                                                                               self.settings.get('abcm2ps_format_path', ''),
                                                                               generate_toc = True)
                self.SetCursor(wx.STANDARD_CURSOR)
                if pdf_file:
                    self.copy_to_destination_and_launch_file(pdf_file, dlg.GetPath())
                else:
                    wx.MessageBox(_("Error: there was some trouble saving the file."), _("File could not be saved properly"), wx.OK)
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window

    def OnMusicPaneDoubleClick(self, evt):
        self.editor.SetFocus()

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

    def OnRightClickList(self, evt):
        self.selected_tune = self.tunes[evt.Index]
        self.tune_list.PopupMenu(self.popup_upload, evt.GetPoint())

    def OnInsertSymbol(self, evt):
        item = self.GetMenuBar().FindItemById(evt.Id)
        self.editor.SetSelectionEnd(self.editor.GetSelectionStart())
        self.AddTextWithUndo(item.GetHelp())
        self.OnToolRefresh(None)

    # 1.3.6.3 [JWDJ] 2015-3 centralized enabling of play button
    def update_play_button(self):
        if self.mc is not None or self.settings['midiplayer_path']:
            self.play_button.Enable()
        else:
            self.play_button.Disable()

    def OnToolPlay(self, evt):
        if self.is_playing():
            self.mc.Pause()
            self.play_button.SetBitmap(self.play_bitmap)
        elif self.is_paused():
            self.mc.Play()
            self.play_button.SetBitmap(self.pause_bitmap)
        else:
            remove_repeats = evt.ControlDown() or evt.CmdDown()
            # 1.3.6.3 [SS] 2015-05-04
            if not self.settings['midiplayer_path']:
                self.flip_tempobox(True)
            #self.play_panel.Show(not self.settings['midiplayer_path']) # 1.3.6.2 [JWdJ] 2015-02
            # self.toolbar.Realize() # 1.3.6.3 [JWDJ] fixes toolbar repaint bug

            if remove_repeats:
                def play():
                    self.PlayMidi(True)
            else:
                def play():
                    self.PlayMidi(False)

            wx.CallAfter(play)

    def OnToolPlayLoop(self, evt):
        if not self.settings['midiplayer_path']:
            self.loop_midi_playback = True
        else:
            wx.MessageBox(_('Looping is not possible when using an external midi player. Empty the midiplayer path in Settings -> ABC Settings -> File Settings to regain the looping ability when you double click the play button'), _('Looping unavailable'), wx.OK | wx.ICON_INFORMATION)
        self.OnToolPlay(evt)

    def OnToolRefresh(self, evt):
        self.last_refresh_time = datetime.now()
        self.UpdateTuneList()
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
            # wx.CallAfter(self.UpdateAbcAssistSetting()) # seems to be too early, pane is still shown

    def OnToolAddTune(self, evt):
        dlg = NewTuneFrame(self)
        try:
            modal_result = dlg.ShowModal()
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window
        if modal_result != wx.ID_OK:
            return

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
        if self.record_thread:
            self.record_thread.abort()
        return True

    def OnNew(self, evt=None):
        self.save_settings()
        frame = wx.GetApp().NewMainFrame()
        frame.Show(True)
        # move new window slightly down to the right:
        width, height = tuple(wx.DisplaySize())
        x, y = self.GetPositionTuple()
        x, y = (x + 40) % (width - 200), (y + 40) % (height - 200)
        frame.Move((x, y))
        return frame

    def OnOpen(self, evt):
        wildcard = _("ABC file") + " (*.abc;*.txt;*.mcm)|*.abc;*.txt;*.mcm|" + \
                   _('Any file') + " (*.*)|*"
        dlg = wx.FileDialog(
            self, message=_("Open ABC file"), #defaultDir='',
            defaultFile="", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.CHANGE_DIR )
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
            defaultFile="", wildcard=wildcard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.CHANGE_DIR )
        try:
            if dlg.ShowModal() == wx.ID_OK:
                self.OnDropFile(dlg.GetPath())
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window
        self.UpdateTuneList()

    def get_encoding(self, abc_code):
        encoding = 'latin-1'

        # strip the utf-8 byte order mark if present
        if type(abc_code) is str and abc_code.startswith(utf8_byte_order_mark):
            abc_code = abc_code[len(utf8_byte_order_mark):]
            ##encoding = 'utf-8'

        if abc_code.startswith('%abc-2.1'):
            encoding = 'utf-8'
        match = re.search('(%%|I:)abc-charset (?P<encoding>[-a-z0-9]+)', abc_code)
        if match:
            encoding = match.group('encoding')
            codecs.lookup(encoding) # make sure that it exists at this point so as to avoid confusing errors later

        # normalize a bit
        if encoding in ['utf-8', 'utf8', 'UTF-8', 'UTF8']:
            encoding = 'utf-8'

        return encoding

    def load_or_import(self, filepath):
        if not self.editor.GetModify() and not self.editor.GetText().strip() and os.path.splitext(filepath)[1].lower() in ('.txt', '.abc', '.mcm', ''):
            self.load(filepath)
        else:
            self.OnDropFile(filepath)

    def load(self, filepath):
        try:
            f = open(filepath, 'rb')
            text = f.read()
            encoding = self.get_encoding(text)

            # if there's an utf-8 BOM strip it, and if necessary ask if the user wants to add an abc-charset field
            if text.startswith(utf8_byte_order_mark) and encoding != 'utf-8':
                text = text[len(utf8_byte_order_mark):]
                try:
                    # is it possible to re-encode the text using the default encoding without problems?
                    s = text.decode('utf-8', 'ignore')
                    s.encode(encoding)
                except UnicodeError:
                    modal_result = wx.MessageBox(_("This ABC file seems to be encoded using UTF-8 but contains no indication of this fact. "
                                                   "It is strongly recommended that an I:abc-charset field is added in order for you to load the file and safely save changes to it. "
                                                   "Do you want EasyABC to add this for you automatically?"), _("Add abc-charset field?"), wx.ICON_QUESTION | wx.YES | wx.NO)
                    if modal_result == wx.YES:
                        text = os.linesep.join(('I:abc-charset utf-8', text))
                        encoding = 'utf-8'

            text = text.decode(encoding)
        except IOError:
            wx.MessageBox(_("Could not find file.\nIt may have been moved or deleted. Choose File,Open to locate it."), _("File not found"), wx.OK)
            return

        if wx.Platform == "__WXMAC__":
            text = text.replace('\r\n', '\r')
        else:
            text = re.sub('\r+', '\r', text)
            if not '\n' in text:
                text = text.replace('\r', '\r\n')

        self.current_file = filepath
        #self.document_name = os.path.basename(filepath) #1.3.6 [SS] 2014-12-01
        self.document_name = filepath
        self.SetTitle('%s - %s' % (program_name, self.document_name))
        self.editor.ClearAll()
        self.editor.SetText(text)
        self.editor.SetSavePoint()
        self.editor.EmptyUndoBuffer()
        self.UpdateTuneList()
        self.tune_list.Select(0)

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
            if type(s) is unicode:
                encoding = self.get_encoding(s)
                try:
                    s.encode(self.get_encoding(s), 'strict')
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
            self.editor.SetSavePoint()
            #self.was_non_modified = True

    def save_as(self, directory=None):
        wildcard = _('ABC file') + " (*.abc)|*.abc"
        defaultDir = ''
        if self.current_file:
            defaultDir = os.path.dirname(self.current_file) or directory or cwd
        dlg = wx.FileDialog(
                self, message=_('Save ABC file %s') % self.document_name, defaultDir=defaultDir,
                defaultFile="", wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.CHANGE_DIR
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
        if 2 <= len(lines) < 100:
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

    def create_symbols_popup_menu(self, symbols):
        menu = wx.Menu()
        for symbol in symbols:
            if symbol == '-':
                menu.AppendSeparator()
            else:
                img_file = os.path.join(cwd, 'img', symbol + '.png')
                id = wx.NewId()
                item = wx.MenuItem(menu, id, ' ')
                image = wx.Image(img_file)
                item.SetBitmap(image.ConvertToBitmap())
                item.SetHelp(('!%s!' % symbol).replace('!pralltriller!', 'P').replace('!accent!', '!>!').replace('!staccato!', '.').replace('!u!', 'u').replace('!v!', 'v').replace('!repeat_left!', '|:').replace('!repeat_right!', ':|').replace('!repeat_both!', '::').replace('!barline!', ' | ').replace('!repeat1!', '|1 ').replace('!repeat2!', ':|2 '))
                menu.AppendItem(item)
                self.Bind(wx.EVT_MENU, self.OnInsertSymbol, id=id)
        return menu

    def create_upload_context_menu(self):
        locale = wx.Locale()
        menu = wx.Menu()
        if locale.GetLanguageName(wx.LANGUAGE_DEFAULT) == 'Swedish':
            id = wx.NewId()
            item = wx.MenuItem(menu, id, _('Upload tune to FolkWiki'))
            menu.AppendItem(item)
            menu.AppendSeparator()
            self.Bind(wx.EVT_MENU, self.OnUploadTune, id=id)

        if locale.GetLanguageName(wx.LANGUAGE_DEFAULT) == 'Danish':
            id = wx.NewId()
            item = wx.MenuItem(menu, id, _('Upload tune to Spillemandsportalen'))
            menu.AppendItem(item)
            menu.AppendSeparator()
            self.Bind(wx.EVT_MENU, self.OnUploadTune, id=id)
            item.Enable(False)  # disabled for now

        id = wx.NewId()
        item = wx.MenuItem(menu, id, _('Export to &MIDI...'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnExportMidi, id=id)
        item = wx.MenuItem(menu, wx.NewId(), _('Export to &PDF...'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnExportPDF, id=item.GetId())
        item = wx.MenuItem(menu, wx.NewId(), _('Export to &SVG...'))
        menu.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnExportSVG, id=item.GetId())

        return menu

    def setup_typing_assistance_menu(self):
        doremi_id = wx.NewId()
        menu = self.mnu_TA = wx.Menu()
        self.mni_TA_active = menu.AppendCheckItem(wx.NewId(), _("&Active") + '\tCtrl+T', "")
        menu.AppendSeparator()
        self.mni_TA_auto_case = menu.AppendCheckItem(wx.NewId(), _("Automatic uppercase/lowercase"), "")
        #self.mni_TA_do_re_mi = wx.MenuItem(None, doremi_id, _("&Do-re-mi mode") + "\tCtrl+D", "")
        #self.mni_TA_do_re_mi.SetKind(wx.ITEM_CHECK)
        self.mni_TA_do_re_mi = menu.AppendCheckItem(doremi_id, _("&Do-re-mi mode") + " (experimental)" + "\tCtrl+D", "")
        #self.mni_TA_do_re_mi.Enable(False)
        self.mni_TA_add_note_durations = menu.AppendCheckItem(wx.NewId(), _("Add note &durations"), "")
        self.mni_TA_add_bar = menu.AppendCheckItem(wx.NewId(), _("Add &bar"), "")
        self.mni_TA_add_right = menu.AppendCheckItem(wx.NewId(), _('Add &matching right symbol: ), ], } and "'), "")
        self.Bind(wx.EVT_MENU, self.GrayUngray, id=self.mni_TA_active.GetId())
        self.Bind(wx.EVT_MENU, self.OnDoReMiModeChange, id=doremi_id)
        return menu

    def create_menu_bar(self, items):
        menuBar = wx.MenuBar()
        for item in items:
            label = item[0]
            items = item[1]
            if not isinstance(items, wx.Menu):
                items = self.create_menu(items)
            menuBar.Append(items, label)
        return menuBar

    def create_menu(self, items):
        menu = wx.Menu()
        for item in items:
            if len(item) == 0:
                menu.AppendSeparator()
            elif len(item) == 2:
                label = item[0]
                sub_menu = item[1]
                if not isinstance(sub_menu, wx.Menu):
                    sub_menu = self.create_menu(sub_menu)
                menu.AppendMenu(-1, label, sub_menu)
            else:
                if isinstance(item[0], int):
                    id = item[0]
                    item = tuple(list(item)[1:]) # strip id from tuple
                    self.append_menu_item(menu, *item, id=id)
                else:
                    self.append_menu_item(menu, *item)
        return menu

    def append_menu_item(self, menu, label, description, handler, kind=wx.ITEM_NORMAL, id=-1):
        menu_item = menu.Append(id, label, description, kind)
        if handler is not None:
            self.Bind(wx.EVT_MENU, handler, menu_item)
        return menu_item

    def setup_menus(self):
        # 1.3.7.1 [JWDJ] creation of menu bar now more structured using less code
        ornaments = 'v u - accent staccato tenuto - open plus snap - trill pralltriller mordent roll fermata - 0 1 2 3 4 5 - turn turnx invertedturn invertedturnx - shortphrase breath'.split()
        dynamics = 'p pp ppp - f ff fff - mp mf sfz'.split()
        directions = 'coda segno D.C. D.S. fine barline repeat_left repeat_right repeat_both repeat1 repeat2'.split()
        self.popup_ornaments = self.create_symbols_popup_menu(ornaments)
        self.popup_dynamics = self.create_symbols_popup_menu(dynamics)
        self.popup_directions = self.create_symbols_popup_menu(directions)

        transpose_menu = wx.Menu()
        for i in reversed(range(-12, 12+1)):
            if i < 0:
                self.append_menu_item(transpose_menu, _('Down %d semitones') % abs(i), '', lambda e, i=i: self.OnTranspose(i))
            elif i == 0:
                transpose_menu.AppendSeparator()
            elif i > 0:
                self.append_menu_item(transpose_menu, _('Up %d semitones') % i, '', lambda e, i=i: self.OnTranspose(i))

        view_menu = wx.Menu()
        self.append_menu_item(view_menu, _("&Refresh music")+"\tF5", "", self.OnToolRefresh)
        self.mni_auto_refresh = self.append_menu_item(view_menu, _("&Automatically refresh music as I type"), "", None, kind=wx.ITEM_CHECK)
        view_menu.AppendSeparator()
        self.mni_reduced_margins = self.append_menu_item(view_menu, _("&Use reduced margins when displaying tunes on screen"), "", self.OnReducedMargins, kind=wx.ITEM_CHECK)
        self.append_menu_item(view_menu, _("&Change editor font..."), "", self.OnChangeFont)
        self.append_menu_item(view_menu, _("&Use default editor font"), "", self.OnUseDefaultFont)
        view_menu.AppendSeparator()
        self.append_menu_item(view_menu, _("&Reset window layout to default"), "", self.OnResetView)
        #self.append_menu_item(view_menu, _("&Maximize/restore musical score pane\tCtrl+M"), "", self.OnToggleMusicPaneMaximize)
        #view_menu.AppendSeparator()
        #self.append_menu_item(view_menu, _('View rythm column...'), self.OnViewRythm, kind=wx.ITEM_CHECK)

        self.recent_menu = wx.Menu()

        if wx.Platform == "__WXMSW__":
            close_shortcut = '\tAlt+F4'
        else:
            close_shortcut = '\tCtrl+W'

        menuBar = self.create_menu_bar([
            (_("&File")     , [
                (_('&New\tCtrl+N'), _("Create a new file"), self.OnNew),
                (_("&Open...\tCtrl+O"), _("Open an existing file"), self.OnOpen),
                (_("&Close") + close_shortcut, _("Close the current file"), self.OnCloseFile),
                (),
                (_("&Import and add..."), _("Import a song in ABC, Midi or MusicXML format and add it to the current document."), self.OnImport),
                (),
                (_("&Export selected"), [
                    (_('as &PDF...'), '', self.OnExportPDF),
                    (_('as &MIDI...'), '', self.OnExportMidi),
                    (_('as &SVG...'), '', self.OnExportSVG),
                    (_('as &HTML...'), '', self.OnExportHTML),
                    (_('as Music&XML...'), '', self.OnExportMusicXML)]),
                (_("Export &all"), [
                    (_('as a &PDF Book...'), '', self.OnExportAllPDF),
                    (_('as PDF &Files...'), '', self.OnExportAllPDFFiles),
                    (_('as &MIDI...'), '', self.OnExportAllMidi),
                    (_('as &HTML...'), '', self.OnExportAllHTML),
                    #(_('as &EPUB...'), '', self.OnExportAllEpub),
                    (_('as Music&XML...'), '', self.OnExportAllMusicXML)]),
                (),
                (_("&Save\tCtrl+S"), _("Save the active file"), self.OnSave),
                (_("Save &As...\tShift+Ctrl+S"), _("Save the active file with a new filename"), self.OnSaveAs),
                (),
                (_("&Print...\tCtrl+P"), _("Print the selected tune"), self.OnPrint),
                (_("&Print preview\tCtrl+Shift+P"), '', self.OnPrintPreview),
                (_("P&age Setup..."), _("Change the printer and printing options"), self.OnPageSetup),
                (),
                (_('&Recent files'), self.recent_menu),
                (),
                (wx.ID_EXIT, _("&Quit\tCtrl+Q"), _("Exit the application (prompt to save files)"), self.OnQuit)]),
            (_("&Edit")     , [
                (_("&Undo\tCtrl+Z"), _("Undo the last action"), self.OnUndo),
                (_("&Redo\tCtrl+Y"), _("Redo the last action"), self.OnRedo),
                (),
                (_("&Cut\tCtrl+X"), _("Cut the selection and put it on the clipboard"), self.OnCut),
                (_("&Copy\tCtrl+C"), _("Copy the selection and put it on the clipboard"), self.OnCopy),
                (_("&Paste\tCtrl+V"), _("Paste clipboard contents"), self.OnPaste),
                (_("&Delete\tDel"), _("Delete the selection"), self.OnDelete),
                (),
                (_("&Insert musical symbol"), [
                    (_('Note ornaments'), self.popup_ornaments),
                    (_('Directions'),     self.popup_directions), # 1.3.6.1 [SS] 2015-01-22
                    (_('Dynamics'),       self.popup_dynamics)]),
                (),
                (_("&Transpose"), transpose_menu),
                (_("&Change note length"), [
                    (_('Double note lengths\tCtrl+Shift++'), '', self.OnDoubleL),
                    (_('Halve note lengths\tCtrl+Shift+-'), '', self.OnHalveL)]),
                (_("A&lign bars\tCtrl+Shift+A"), '', self.OnAlignBars),
                (),
                (_("&Find...\tCtrl+F"), '', self.OnFind),
                (_("&Find Next\tF3"), '', self.OnFindNext),
                (_("&Replace...\tCtrl+H"), '', self.OnReplace),
                (),
                (_("&Select all\tCtrl+A"), '', self.OnSelectAll)]),
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
                (_('&Sort tunes...'), '', self.OnSortTunes),
                (_('Search directories...'), '', self.OnSearchDirectories)]), # 1.3.6 [SS] 2014-11-21
            (_("&View")     , view_menu),
            (_("&Internals"), [ #p09 [SS] 2014-10-22
                (_("Messages"), _("Show warnings and errors"), self.OnShowMessages),
                (_("Input processed tune"),'', self.OnShowAbcTune),
                (_("Output midi file"), '', self.OnShowMidiFile),
                (_("Show settings status"),'', self.OnShowSettings)]),
            (_("&Help")     , [
                (_("&Show fields and commands reference"), '', self.OnViewFieldReference),
                (),
                (_("&EasyABC Help"), _("Link to EasyABC Website"), self.OnEasyABCHelp),
                (_("&ABC Standard Version 2.1"), _("Link to the ABC Standard version 2.1"), self.OnABCStandard),
                (_("&Learn ABC"), _("Link to the ABC notation website"), self.OnABCLearn),
                (_("&Abcm2ps help"), _("Link to the Abcm2ps website"), self.OnAbcm2psHelp),
                (_("&Abc2midi help"), _("Link to the Abc2midi website"), self.OnAbc2midiHelp),
                (),
                (wx.ID_ABOUT, _("About EasyABC") + "...", '', self.OnAbout)
            ]),
        ])

        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_FIND, self.OnFindNext)
        self.Bind(wx.EVT_FIND_NEXT, self.OnFindNext)
        self.Bind(wx.EVT_FIND_REPLACE, self.OnFindReplace)
        self.Bind(wx.EVT_FIND_REPLACE_ALL, self.OnFindReplaceAll)
        self.Bind(wx.EVT_FIND_CLOSE, self.OnFindClose)

    def ShowMessages(self):
        global execmessages
        win = wx.FindWindowByName('infoframe')
        if win is None:
            self.msg = MyInfoFrame()
            self.msg.ShowText(execmessages)
            self.msg.Show()
        else:
            self.msg.ShowText(execmessages)
            # 1.3.6.1 [JWdJ] 2015-01-30 When messages window is lost it will be focused again
            self.msg.Iconize(False)
            self.msg.Raise()

    def OnShowMessages(self,evt):
        self.ShowMessages()

    def OnShowAbcTune(self,evt):
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

    # 1.3.6 [SS] 2014-12-10
    def OnShowSettings(self,evt):
        global execmessages
        execmessages = u''
        for key in sorted(self.settings):
            line = key +' => '+ str(self.settings[key]) + '\n'
            execmessages += line
        # 1.3.6.1 [JWdJ] 2015-01-30 When messages window is lost it will be focused again
        self.ShowMessages()

    #1.3.6.4 [SS] 2015-06-22
    def OnShowMidiFile(self,evt):
        midi2abc_path = self.settings['midi2abc_path']
        if hasattr(self.current_midi_tune,'midi_file'):
            MidiToMftext (midi2abc_path,self.current_midi_tune.midi_file)
        else:
            wx.MessageBox(_("You need to create the midi file by playing the tune"), ("Error") ,wx.ICON_ERROR | wx.OK)


    def OnCloseFile(self, evt):
        self.Close()
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
    def OnUndo(self, evt):      self.do_command(stc.STC_CMD_UNDO)
    def OnRedo(self, evt):      self.do_command(stc.STC_CMD_REDO)
    def OnCut(self, evt):       self.do_command(stc.STC_CMD_CUT)
    def OnCopy(self, evt):      self.do_command(stc.STC_CMD_COPY)
    def OnPaste(self, evt):     self.do_command(stc.STC_CMD_PASTE)
    def OnDelete(self, evt):    self.do_command(stc.STC_CMD_CLEAR)
    def OnSelectAll(self, evt): self.do_command(stc.STC_CMD_SELECTALL)
    def OnFind(self, evt):
        if self.find_dialog:
            self.find_dialog.Raise()
            return
        if self.replace_dialog:
            self.replace_dialog.Close()
            self.replace_dialog.Destroy()
            self.replace_dialog = None
        self.find_dialog = wx.FindReplaceDialog(self, self.find_data, _("Find"))
        wx.CallLater(300, self.find_dialog.Show, True)
    def OnReplace(self, evt):
        if self.replace_dialog:
            self.replace_dialog.Raise()
            return
        if self.find_dialog:
            self.find_dialog.Close()
            self.find_dialog.Destroy()
            self.find_dialog = None
        self.replace_dialog = wx.FindReplaceDialog(self, self.find_data, _("Find & Replace"), wx.FR_REPLACEDIALOG)
        wx.CallLater(300, self.replace_dialog.Show, True)
    def OnFindClose(self, evt):
        #self.mni_find.Enable(True)
        #self.mni_replace.Enable(True)
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
            ##wx.CallLater(1200, self.ScrollMusicPaneToMatchEditor, select_closest_note=True)
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
            #print 'current position = ',self.editor.GetCurrentPos()
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

    def OnEasyABCHelp(self, evt):
        handle = webbrowser.get()
        handle.open('http://www.nilsliberg.se/ksp/easyabc/')

    def OnABCStandard(self, evt):
        handle = webbrowser.get()
        handle.open('http://abcnotation.com/wiki/abc:standard:v2.1')

    def OnABCLearn(self, evt):
        handle = webbrowser.get()
        handle.open('http://abcnotation.com/learn')

    # 1.3.6.1 [SS] 2015-01-28
    def OnAbcm2psHelp(self, evt):
        handle = webbrowser.get()
        handle.open('http://moinejf.free.fr/abcm2ps-doc/')

    # 1.3.6.1 [SS] 2015-01-28
    def OnAbc2midiHelp(self, evt):
        handle = webbrowser.get()
        handle.open('http://ifdo.ca/~seymour/runabc/abcguide/abc2midi_guide.html')


    def OnClearCache(self, evt):
        # make sure that any currently played/loaded midi file is released by the media control
        #patch from Seymour: ensure that the media player exists with the statement
        self.stop_playing()

        dir_name = os.path.join(self.app_dir, 'cache')
        # 1.3.6 [SS] 2014-11-16
        #files = [os.path.join(dir_name, f) for f in os.listdir(dir_name) if f.startswith('temp_') and f[-3:] in ('png', 'svg', 'abc', 'mid', 'idi')]
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
        self.OnToolRefresh(None)


    # 1.3.6.1 [SS] 2014-12-28 2015-01-22
    def OnColdRestart(self,evt):
        result = wx.MessageBox(_("This will close EasyAbc and put it in a state so that it starts with default settings."
        "i.e. the file settings1.3 will be deleted."),
                               _("Proceed?"), wx.ICON_QUESTION | wx.OK | wx.CANCEL)
        if result == wx.OK:
            f = os.path.join(self.app_dir,'settings1.3.dat')
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
        if win is None:
            self.settingsbook = MyNoteBook(self.settings, self.statusbar)
            self.settingsbook.Show()
        else:
            self.settingsbook.Iconize(False)
            self.settingsbook.Raise()

    def OnChangeFont(self, evt):
        font = wx.GetFontFromUser(self, self.editor.GetFont(), _('Select a font for the ABC editor'))
        if font.IsOk():
            f = font
            self.settings['font'] = (f.GetPointSize(), f.GetFamily(), f.GetStyle(), f.GetWeight(), f.GetUnderlined(), f.GetFaceName())
            self.OnSettingsChanged()

    def OnViewFieldReference(self, evt):
        if not self.field_reference_frame:
            self.field_reference_frame = frame = wx.Frame(self, -1, _('ABC fields and commands reference'), wx.DefaultPosition, (700, 500),
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
                frame.load_settings()
                frame.InitEditor()

    def ScrollMusicPaneToMatchEditor(self, select_closest_note=False, select_closest_page=False):
        tune = self.GetSelectedTune()
        if not tune or not self.current_svg_tune:
            return
        page = self.music_pane.current_page # 1.3.6.2 [JWdJ]

        # workaround for the fact the abcm2ps returns incorrect row numbers
        # check the row number of the first note and if it doesn't agree with the actual value
        # then pretend that we have more or less extra header lines
        num_header_lines, first_note_line_index = self.get_num_extra_header_lines(tune)
        #actual_first_row = page.notes[0][2]-1
        #num_header_lines += (actual_first_row - first_note_line_index)

        current_pos = self.editor.GetCurrentPos()
        current_row = self.editor.LineFromPosition(current_pos)
        tune_first_line_no = self.editor.LineFromPosition(tune.offset_start)

        if select_closest_page:
            abc_from_editor = AbcTune(self.editor.GetTextRange(tune.offset_start, tune.offset_end))
            first_note_editor = abc_from_editor.first_note_line_index
            if first_note_editor is not None:
                current_body_row = current_row - tune_first_line_no - first_note_editor
                if current_body_row >= 0:
                    # create a list of pages but start with the current page because it has the most chance
                    page_indices = [self.current_page_index] + \
                                   [p for p in range(self.current_svg_tune.page_count) if p != self.current_page_index]
                    current_svg_row = current_body_row + self.current_svg_tune.first_note_line_index + 1 # row in svg-file is 1-based
                    new_page_index = None
                    for page_index in page_indices:
                        page = self.current_svg_tune.render_page(page_index, self.renderer)
                        if page and page.notes_in_row and current_svg_row in page.notes_in_row:
                            new_page_index = page_index
                            break

                    if new_page_index is not None and new_page_index != self.current_page_index:
                        self.current_page_index = new_page_index
                        self.UpdateMusicPane()

        closest_xy = None
        closest_col = -9999
        line = self.editor.GetCurrentLine()
        col = self.editor.GetCurrentPos() - self.editor.PositionFromLine(line)
        # 1.3.6.2 [JWdJ] 2015-02
        row_offset = tune_first_line_no - 1 - num_header_lines

        # 1.3.6.2 [JWdJ] 2015-02
        for i, (x, y, abc_row, abc_col, desc) in enumerate(page.notes):
            abc_row += row_offset
            if abc_row == line and (abs(col - abc_col) < abs(closest_col - abc_col)):
                closest_col = abc_col
                closest_xy = (x, y)
                if select_closest_note:
                    if page.selected_indices != {i}:
                        # 1.3.6.2 [JWdJ] 2015-02
                        page.clear_note_selection()
                        page.add_note_to_selection(i)
                        self.selected_note_indices = [i]
                        self.selected_note_descs = [page.notes[i] for i in self.selected_note_indices]

        if closest_xy:
            if select_closest_note:
                wx.CallAfter(self.music_pane.redraw)

            x, y = closest_xy
            x, y = x*self.zoom_factor, y*self.zoom_factor
            #sx, sy = self.music_pane.GetScrollPos(wx.HORIZONTAL), self.music_pane.GetScrollPos(wx.VERTICAL)
            sx, sy = self.music_pane.CalcUnscrolledPosition((0, 0))
            vw, vh = self.music_pane.GetVirtualSizeTuple()
            w, h = self.music_pane.GetClientSizeTuple()
            margin = 20
            #if y > sy+margin:
            #    sy = y-h-margin*2
            #elif y < h+sy-margin:
            #    sy = y-margin*2
            orig_scroll = (sx, sy)
            if not sx+margin <= x <= w+sx-margin:
                sx = x - w + w/5
            if not (sy+margin <= y <= h+sy-margin):
                sy = y-h/2
            sx = max(0, min(sx, vw))
            sy = max(0, min(sy, vh))
            if (sx, sy) != orig_scroll:
                #print 'scroll', sx, sy
                ux, uy = self.music_pane.GetScrollPixelsPerUnit()
                self.music_pane.Scroll(sx/ux, sy/uy)

    def OnMovedToDifferentLine(self, queue_number_movement):
        #print 'OnMovedToDifferentLine = ',queue_number_movement,' ',self.queue_number_movement
        if self.queue_number_movement == queue_number_movement:
            new_tune_selected = False
            found_index = None
            line_no = self.editor.LineFromPosition(self.editor.GetCurrentPos())
            for i, (index, title, rythm, startline) in enumerate(self.tunes):
                if startline > line_no:
                    break
                found_index = i
            for i in range(self.tune_list.GetItemCount()):
                index = self.tune_list.GetItemData(i)
                if index == found_index and i != self.tune_list.GetFirstSelected():
                    new_tune_selected = True
                    self.tune_list.SetItemState(i, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
                    self.tune_list.EnsureVisible(i)
                    self.music_pane.Scroll(0, 0)
            if not new_tune_selected:
                self.ScrollMusicPaneToMatchEditor(select_closest_page=self.mni_auto_refresh.IsChecked())

            if self.abc_assist_panel.IsShown():
                self.abc_assist_panel.update_assist()

    def AutoInsertXNum(self):
        xNum = 0
        for line_no in range(self.editor.GetLineCount()):
            m = re.match(r'^X:\s*(\d+)', self.editor.GetLine(line_no))
            if m:
                xNum = max(xNum, int(m.group(1)))

        line = self.editor.GetCurrentLine()
        # start = self.editor.PositionFromLine(line)
        p = self.editor.GetCurrentPos()
        self.editor.BeginUndoAction()
        self.editor.SetSelection(p, p)
        self.editor.ReplaceSelection(str(xNum+1))
        self.editor.SetSelection(self.editor.GetLineEndPosition(line), self.editor.GetLineEndPosition(line))
        self.editor.EndUndoAction()

    def DoReMiToNote(self, char):
        if char in doremi_prefixes:
            tune = self.GetSelectedTune()
            if tune:
                matches = re.findall(r'(?<=[\r\n\[])K: *([A-Ga-g])', self.editor.GetTextRange(tune.offset_start, self.editor.GetCurrentPos()))
                if matches:
                    K = matches[-1]
                    doremi_index = doremi_prefixes.index(char)
                    base_note_index = all_notes.index(K.upper())
                    note = all_notes[base_note_index + doremi_index]
                    if char == char.upper():
                        return note[0].upper()
                    else:
                        return note[0].lower()
        return char

    def OnCharEvent(self, evt):
        style = self.editor.GetStyleAt(self.editor.GetCurrentPos())
        is_string_style = self.styler.STYLE_STRING
        is_default_style = (style in [self.styler.STYLE_DEFAULT, self.styler.STYLE_GRACE])

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
                self.current_page_index = new_page
                self.UpdateMusicPane()
                evt.Skip()
                return

        c = unichr(evt.GetUniChar())
        p1, p2 = self.editor.GetSelection()
        # 1.3.6.2 [JWdJ] 2015-02
        # selected_indices_backup = self.music_pane.current_page.selected_indices.copy()
        line, caret = self.editor.GetCurLine()
        is_inside_field = len(line)>=2 and line[1] == ':' and re.match(r'[A-Za-z\+]', line[0]) or line.startswith('%')
        if is_inside_field:
            evt.Skip()
            return

        at_end_of_line = not self.editor.GetTextRange(self.editor.GetCurrentPos(), self.editor.GetLineEndPosition(self.editor.GetCurrentLine())).strip('| : ] [')

        if c == ' ' and self.mni_TA_active.IsChecked() and not is_inside_field and is_default_style:
            try:
                if not self.FixNoteDurations():
                    evt.Skip()
            except Exception:
                evt.Skip()
                raise

        # when there is a selection and 's' is pressed it serves as a shortcut for slurring
        elif p1 != p2 and c == 's':
            c = '('

        elif c == ':':
            evt.Skip()
            if (line.rstrip(), caret) == (u'X', 1):
                wx.CallAfter(self.AutoInsertXNum)

        elif c == '3' and p1 == p2 and self.editor.GetTextRange(p1-1, p1+1) == '()' and is_default_style:
            # if the user writes ( which is auto-completed to () and then writes 3, he/she probably
            # wants to start a triplet so we delete the right parenthesis
            self.editor.BeginUndoAction()
            self.editor.SetSelection(p1, p1+1)
            self.editor.ReplaceSelection(c)
            self.editor.EndUndoAction()

        elif (c in ']}' and self.editor.GetTextRange(p1, p1+1) == c and is_default_style) or \
                (c == '"'  and self.editor.GetTextRange(p1, p1+1) == c and self.editor.GetTextRange(p1-1, p1) != '\\'):
            (text,pos) = self.editor.GetCurLine()
            # unless this is not a field line
            if re.match('[a-zA-Z]:', text):
                evt.Skip()
            # if there is already a ] or }, just move one step to the right
            else:
                self.editor.SetSelection(p1+1, p1+1)

        elif c in '([{"':
            start, end = {'(': '()', '[': '[]', '{': '{}', '"': '""'}[c]

            # if this is a text or chord, then don't replace selection, but insert the new text/chord in front of the note(s) selected
            if c == '"':
                self.editor.SetSelection(p1, p1)
                p2 = p1

            first_char, last_char = self.editor.GetTextRange(p1-1, p1), self.editor.GetTextRange(p2, p2+1)
            orig_p1 = p1

            # if this is a triplet with a leading '(' then virtually move the selection start a bit to the left
            if p1 != p2 and last_char == ')' and self.editor.GetTextRange(p1-3, p1) == '((3':
                p1 -= 2
                first_char = '('
            if p1 != p2 and first_char == start and last_char == end and first_char != '"':
                self.editor.BeginUndoAction()
                self.editor.SetSelection(p2, p2+1)
                self.editor.ReplaceSelection('')
                self.editor.SetSelection(p1-1, p1)
                self.editor.ReplaceSelection('')
                self.editor.SetSelection(orig_p1-1, p2-1)
                self.editor.EndUndoAction()
            elif p1 != p2 and c != '[':
                self.editor.BeginUndoAction()
                # if this is a triplet, then start the slur just before '(3' instead of after.
                if c == '(' and last_char == ' ' and self.editor.GetTextRange(p1-2, p1) == '(3':
                    self.editor.InsertText(p1-2, start)
                else:
                    self.editor.InsertText(p1, start)
                self.editor.InsertText(p2+1, end)
                self.editor.SetSelection(p1+1, p2+1)
                self.editor.EndUndoAction()
            elif is_default_style and (self.mni_TA_active.IsChecked() and self.mni_TA_add_right.IsChecked()):
                line, _ = self.editor.GetCurLine()
                if c == '"' and line.count('"') % 2 == 1 or \
                        c != '"' and line.count(end) > line.count(start):
                    evt.Skip()
                else:
                    self.editor.ReplaceSelection(start + end)
                    self.editor.SetSelection(p1+1, p1+1)
            else:
                evt.Skip()
        elif c in '<>' and (p2 - p1) > 1:
            try:
                self.editor.BeginUndoAction()
                base_pos = self.editor.GetSelectionStart()
                text = self.editor.GetSelectedText()
                notes = get_notes_from_abc(text, exclude_grace_notes=True)
                total_offset = 0
                for (start, end, abc_note_text) in notes[0::2]:
                    p = base_pos + end + total_offset
                    if re.match(r'[_=^]', abc_note_text):
                        p += 1
                    cur_char = self.editor.GetTextRange(p-1, p)
                    if cur_char == '<' and c == '>' or cur_char == '>' and c == '<':
                        self.editor.SetSelection(p-1, p)
                        self.editor.ReplaceSelection('')
                        total_offset -= 1
                    else:
                        self.editor.SetSelection(p, p)
                        self.editor.AddText(c)
                        total_offset += 1
                self.editor.SetSelection(p1, p2+total_offset)
            finally:
                self.editor.EndUndoAction()
        elif c == '.' and p1 != p2:
            try:
                self.editor.BeginUndoAction()
                base_pos = self.editor.GetSelectionStart()
                text = self.editor.GetSelectedText()
                notes = get_notes_from_abc(text, exclude_grace_notes=True)
                total_offset = 0
                for (start, end, abc_note_text) in notes:
                    p = base_pos + start + total_offset
                    #if re.match(r'[_=^]', abc_note_text):
                    #    p -= 1
                    cur_char = self.editor.GetTextRange(p-1, p)
                    if cur_char == '.':
                        self.editor.SetSelection(p-1, p)
                        self.editor.ReplaceSelection('')
                        total_offset -= 1
                    else:
                        self.editor.SetSelection(p, p)
                        self.editor.AddText(c)
                        total_offset += 1
                self.editor.SetSelection(p1, p2+total_offset)
            finally:
                self.editor.EndUndoAction()
        elif self.keyboard_input_mode and is_default_style:
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
                    self.editor.ReplaceSelection(accidental + note)

        # automatically select uppercase/lowercase - choose the one that will make this note be closest to the previous note
        elif p1 == p2 and at_end_of_line and is_default_style and (self.mni_TA_active.IsChecked() and self.mni_TA_auto_case.IsChecked()) and \
                 (not self.mni_TA_do_re_mi.IsChecked() and c in 'abcdefgABCDEFG' or \
                  self.mni_TA_do_re_mi.IsChecked() and c in doremi_prefixes):
            last_note_number = None

            if self.mni_TA_do_re_mi.IsChecked():
                c = self.DoReMiToNote(c)[0]

            # get the text of the previous and current line up to the position of the cursor
            prev_line = self.editor.GetLine(self.editor.GetCurrentLine()-1)
            this_line, pos = self.editor.GetCurLine()
            text, pos = prev_line + this_line[:pos], pos + len(prev_line)

            p = self.editor.GetCurrentPos()

            # go backwards (to the left from the cursor) and look for the first note
            for i in range(len(text)-1):
                if p-i >= 1 and self.editor.GetStyleAt(p-i-1) in [self.styler.STYLE_DEFAULT, self.styler.STYLE_GRACE]:
                    m = re.match(r"([A-Ga-g])[,']?", text[len(text)-1-i:len(text)-1-i+2])
                    if m:
                        last_note_number = all_notes.index(m.group(0))
                        break

            if last_note_number is None:
                if self.mni_TA_do_re_mi.IsChecked():
                    self.editor.AddText(c)
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
                    self.editor.AddText(c)
                else:
                    evt.Skip()

        elif self.mni_TA_active.IsChecked() and self.mni_TA_do_re_mi.IsChecked() and is_default_style:
            if c in doremi_prefixes:
                c = self.DoReMiToNote(c)
                self.editor.AddText(c)
            elif c not in doremi_suffixes:
                evt.Skip()

        else:
            evt.Skip()

        # if event was processed, restore the old note selection
##        if not evt.GetSkipped():
##            def restore():
##                print 'restore', selected_indices_backup
##                self.music_pane.current_page.clear_note_selection()
##                for i in selected_indices_backup:
##                    self.music_pane.current_page.add_note_to_selection(i)
##                self.music_pane.redraw()
##            wx.CallLater(1260, restore)

    def FixNoteDurations(self):
        # 1.3.6.2 [JWdJ] 2015-02
        use_add_note_durations = self.mni_TA_active.IsChecked() and self.mni_TA_add_note_durations.IsChecked()
        use_add_bar = self.mni_TA_active.IsChecked() and self.mni_TA_add_bar.IsChecked()
        if not use_add_note_durations and not use_add_bar:
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
        note_durations = []
        note_pattern = re.compile(r"(?P<note>([_=^]?[A-Ga-gxz]([,']+)?))(?P<len>\d{0,2}/\d{1,2}|/+|\d{0,2})(?P<dur_mod>[><]?)")

        # determine L: and M: fields
        lines = re.split('\r\n|\r|\n', abc_up_to_selection)
        default_len = Fraction(1, 8)
        metre = Fraction(4, 4)
        # 1.3.7 [JWdJ] 2016-01-06
        meter_pattern = r'M:\s*(?:(\d+)/(\d+)|(C\|?))'
        for line in lines:
            m = re.match(r'^L:\s*(\d+)/(\d+)', line)
            if m:
                default_len = Fraction(int(m.group(1)), int(m.group(2)))
            m = re.search(r'^{0}'.format(meter_pattern), line)
            if m:
                # 1.3.7 [JWdJ] 2016-01-06
                if m.group(1) is not None:
                    metre = Fraction(int(m.group(1)), int(m.group(2)))
                elif m.group(3) == 'C':
                    metre = Fraction(4, 4)
                elif m.group(3) == 'C|':
                    metre = Fraction(2, 2)
            for m in re.finditer(r'\[{0}\]'.format(meter_pattern), line):
                if m.group(1) is not None:
                    metre = Fraction(int(m.group(1)), int(m.group(2)))
                elif m.group(3) == 'C':
                    metre = Fraction(4, 4)
                elif m.group(3) == 'C|':
                    metre = Fraction(2, 2)
            for m in re.finditer(r'\[L:\s*(\d+)/(\d+)\]', line):
                default_len = Fraction(int(m.group(1)), int(m.group(2)))

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

        # check if the bar is full and a new bar should start
        # 1.3.6.2 [JWdJ] 2015-02
        if use_add_bar:
            current_pos = self.editor.GetCurrentPos()
            text = self.editor.GetTextRange(line_start_offset, current_pos)
            start_offset = max([0] + [m.end(0) for m in bar_sep.finditer(text)])  # offset of last bar symbol
            text = text[start_offset:]  # the text from the last bar symbol up to the selection point

            # 1.3.6.1 [JWdJ] 2015-01-28 bar lines for multirest Zn
            end_of_line_offset = self.editor.GetLineEndPosition(self.editor.GetCurrentLine())
            rest_of_line = self.editor.GetTextRange(current_pos, end_of_line_offset).strip()
            if re.match(r"^[XZ]\d*$", text):
                duration = metre
            else:
                duration = get_bar_length(text, default_len, metre)

            if (duration >= metre and not bar_sep.match(rest_of_line) and
                    not (text.rstrip() and text.rstrip()[-1] in '[]:|')):
                self.insert_bar()
                return True

    def insert_bar(self):
        # 1.3.6.3 [JWDJ] 2015-3 don't add space before or after bar if space already present
        current_pos = self.editor.GetCurrentPos()
        pre_space = ''
        post_space = ''
        if current_pos > 0 and self.editor.GetTextRange(current_pos-1, current_pos) not in ' \r\n:':
            pre_space = ' '
        if current_pos == self.editor.GetTextLength() or self.editor.GetTextRange(current_pos, current_pos+1) != ' ':
            post_space = ' '
        self.AddTextWithUndo(pre_space+'|'+post_space)
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

    def OnKeyDownEvent(self, evt):
        # temporary work-around for what seems to be a scintilla bug on Mac:
        if wx.Platform == "__WXMAC__" and evt.GetRawKeyCode() == 7683:
            wx.CallAfter(lambda: self.AddTextWithUndo('^'))
            evt.Skip()
            return

        # remap the tab key to '|'
        #if evt.GetUniChar() == ord('\t'):
        #    self.editor.ReplaceSelection('|')
        #    evt.StopPropagation()
        #    return

        line, caret = self.editor.GetCurLine()
        is_inside_field = len(line)>=2 and line[1] == ':' and re.match(r'[A-Za-z]', line[0]) or line.startswith('%')
        is_default_style = (self.editor.GetStyleAt(self.editor.GetCurrentPos()) in
                               [self.styler.STYLE_DEFAULT, self.styler.STYLE_GRACE])

        if evt.GetKeyCode() == wx.WXK_RETURN:
            line = self.editor.GetCurrentLine()
            # 1.3.6.3 [JWDJ] 2015-04-21 Added line continuation
            for prefix in ['W:', 'w:', 'N:', 'H:', '%%', '%', '+:']:
                if self.editor.GetLine(line-1).startswith(prefix) and self.editor.GetLine(line).startswith(prefix):
                    if self.editor.GetLine(line-1).startswith(prefix+' '):  # whether to add a space after W:
                        wx.CallAfter(lambda: self.AddTextWithUndo(prefix + ' '))
                        break
                    else:
                        wx.CallAfter(lambda: self.AddTextWithUndo(prefix))
                        break
            evt.Skip()
        elif evt.GetKeyCode() == wx.WXK_TAB:
            if not is_inside_field and self.editor.GetSelectionStart() == self.editor.GetSelectionEnd():
                wx.CallAfter(lambda: self.insert_bar())
            else:
                evt.Skip()
##        elif evt.GetUniChar() == ord('D') and evt.CmdDown() and False:
##            if self.keyboard_input_mode:
##                self.keyboard_input_mode = False
##            else:
##                self.StartKeyboardInputMode()
        elif evt.GetUniChar() == ord('L') and evt.CmdDown():
            self.ScrollMusicPaneToMatchEditor(select_closest_note=True, select_closest_page=self.mni_auto_refresh.IsChecked())
        elif evt.MetaDown() and evt.GetKeyCode() == wx.WXK_UP:
            self.editor.GotoPos(0)
        elif evt.MetaDown() and evt.GetKeyCode() == wx.WXK_DOWN:
            self.editor.GotoPos(self.editor.GetLength())
        elif evt.MetaDown() and evt.GetKeyCode() == wx.WXK_LEFT:
            self.editor.GotoPos(self.editor.PositionFromLine(self.editor.GetCurrentLine()))
        elif evt.MetaDown() and evt.GetKeyCode() == wx.WXK_RIGHT:
            self.editor.GotoPos(self.editor.GetLineEndPosition(self.editor.GetCurrentLine()))
        else:
            evt.Skip()

    def StartKeyboardInputMode(self):
        line_start_offset = self.editor.PositionFromLine(self.editor.GetCurrentLine())
        text = self.editor.GetTextRange(line_start_offset, self.editor.GetCurrentPos()) # line up to selection position
        notes = get_notes_from_abc(text)
        if notes:
            self.keyboard_input_mode = True
            m = re.match(r"([_=^]?)(?P<note>[A-Ga-gz][,']*)", notes[-1][-1])
            self.keyboard_input_base_note = all_notes.index(m.group('note'))
            self.keyboard_input_base_key = None
            if self.keyboard_input_base_note == -1:
                self.keyboard_input_mode = False

    def OnEditorMouseRelease(self, evt):
        evt.Skip()
        p1, p2 = self.editor.GetSelection()
        if p1 == p2:
            self.ScrollMusicPaneToMatchEditor(select_closest_note=True, select_closest_page=self.mni_auto_refresh.IsChecked())

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
        #self.ScrollMusicPaneToMatchEditor(select_closest_note=True, select_closest_page=True) #patch p08


    def OnModified(self, evt):
        if evt.GetLinesAdded() != 0:
            wx.CallAfter(self.UpdateTuneList)

    def AutomaticUpdate(self, update_number):
        if self.queue_number_refresh_music == update_number:
            self.OnToolRefresh(None)

    def OnChange(self, event):
        self.GrayUngray()
        event.Skip()
        # if auto-refresh is on
        if self.mni_auto_refresh.IsChecked():
            self.queue_number_refresh_music += 1
            wx.CallLater(250, self.AutomaticUpdate, self.queue_number_refresh_music)

    def GrayUngray(self, evt=None):
        editMenu = self.GetMenuBar().GetMenu(1)
        undo, redo, _, cut, copy, paste, delete, _, insert_symbol, _, transpose, note_length, align_bars, _, find, findnext, replace, _, selectall = editMenu.GetMenuItems()
        undo.Enable(self.editor.CanUndo())
        redo.Enable(self.editor.CanRedo())
        paste.Enable(self.editor.CanPaste())

        for mni in (self.mni_TA_auto_case, self.mni_TA_do_re_mi, self.mni_TA_add_bar, self.mni_TA_add_note_durations, self.mni_TA_add_right):
            mni.Enable(self.mni_TA_active.IsChecked())
        #self.mni_TA_do_re_mi.Enable(False)

    def OnUpdate(self, evt):
        if evt.GetKeyCode() == 344: #F5
            self.UpdateTuneList()
            self.OnTuneSelected(None)
        elif evt.GetKeyCode() == 345: #F6
            self.PlayMidi()
        elif evt.GetKeyCode() == 346: #F7
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

        if wx.TheClipboard.Open():
            wx.TheClipboard.Flush()  # the text on the clipboard should be available after the app has closed
            wx.TheClipboard.Close()

        self.music_update_thread.abort()
        self.svg_tunes.cleanup()
        self.midi_tunes.cleanup()
        self.settings['is_maximized'] = self.IsMaximized()
        #self.error_pane.Show()
        self.Hide()
        self.Iconize(False)  # the x,y pos of the window is not properly saved if it's minimized
        self.save_settings()
        self.is_closed = True
        self.manager.UnInit()
        self.Destroy()

    # 1.3.6.3 [JWDJ] DetermineMidiPlayRange is not used anymore
    # def DetermineMidiPlayRange(self, tune, midi_file):
    #     start = None
    #     end = None
    #     if False and self.selected_note_indices:
    #         offsets = midi_to_meta_data(midi_file)
    #
    #         # what's the (row, col) range of the selection
    #         p1, p2 = self.editor.GetSelection()
    #         row1, row2 = self.editor.LineFromPosition(p1), self.editor.LineFromPosition(p2)
    #         col1, col2 = p1-self.editor.PositionFromLine(row1), p2-self.editor.PositionFromLine(row2)
    #         # adjust so that the X: line corresponds to row number 0
    #         start_row = self.editor.LineFromPosition(tune.offset_start)
    #         row1 -= start_row
    #         row2 -= start_row
    #         ##print (row1, col1), (row2, col2)
    #
    #         if offsets:
    #             for i, (row, col, time) in enumerate(offsets):
    #                 row = row - 17 - 1 # 17 is the number of extra rows added by process_abc_code, and -1 is to make it zero-based
    #                 ##print (row, col, time)
    #                 if row1 <= row <= row2 and col1 <= col < col2:  # if inside selection
    #                     if start is None or time < start:
    #                         start = int(time)
    #                     if end is None or time > end:
    #                         if i < len(offsets)-1:
    #                             end = int(offsets[i+1][2])-1   # end just before the next note starts
    #                         else:
    #                             end = None
    #     self.play_start_offset = start or 0
    #     self.play_end_offset = end or 9999999999999

    def PlayMidi(self, remove_repeats=False):
        global execmessages # 1.3.6 [SS] 2014-11-11
        tune, abc = self.GetAbcToPlay()
        if not tune:
            return

        execmessages = u''
        if remove_repeats or (len(self.selected_note_indices) > 1):
            abc = abc.replace('|:', '').replace(':|', '').replace('::', '')
            execmessages += '\n*removing repeats*'

        tempo_multiplier = self.get_tempo_multiplier()

        # 1.3.6 [SS] 2014-11-15 2014-12-08
        self.current_midi_tune = AbcToMidi(abc, tune.header ,self.cache_dir, self.settings, self.statusbar, tempo_multiplier)
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
                # 1.3.6.3 [JWDJ] 2015-3 DetermineMidiPlayRange not used anymore
                # self.DetermineMidiPlayRange(tune, midi_file)
                self.do_load_media_file(midi_file)

    def GetTextPositionOfTune(self, tune_index):
        position = self.editor.FindText(0, self.editor.GetTextLength(), 'X:%s' % tune_index, 0)
        if position == -1:
            position = self.editor.FindText(0, self.editor.GetTextLength(), 'X: %s' % tune_index, 0)
        return position

    def OnTuneListClick(self, evt):
        self.tune_list.SetFocus()
        evt.Skip()

    def SetErrorMessage(self, error_msg):
        #print traceback.extract_stack(None, 5)
        #print 'SetErrorMessage called ',error_msg
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
        # 1.3.6.2 [JWdJ] 2015-02
        self.current_page_index = self.cur_page_combo.GetSelection()
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
            self.update_statusbar_and_messages()
        except Exception as e:
            error_msg = ''.join(traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))
            wx.CallLater(600, self.SetErrorMessage, u'Internal error when drawing svg: %s' % error_msg)
            self.music_pane.clear()

    # 1.3.6.2 [JWdJ] 2015-02
    def OnMusicUpdateDone(self, evt): # MusicUpdateDoneEvent
        # MusicUpdateThread.run posts an event MusicUpdateDoneEvent with the svg_files
        tune = evt.GetValue()
        self.current_svg_tune = tune
        self.svg_tunes.add(tune) # 1.3.6.3 [JWDJ] for proper disposable of svg files
        self.UpdateMusicPane()
        #self.SetErrorMessage(error) 1.3.6 [SS] 2014-12-07

    def GetTextRangeOfTune(self, offset):
        position = offset
        start_line = self.editor.LineFromPosition(position)
        end_line = start_line + 1
        while end_line < self.editor.GetLineCount() and not self.editor.GetLine(end_line).startswith('X:'):
            end_line += 1
        end_position = self.editor.GetLineEndPosition(end_line-1)
        return (position, end_position)

    def GetFileHeaderBlock(self):
        if self.settings.get('abc_include_file_header', True):
            # collect all header lines
            lines = []
            # 1.3.6.4 [SS] 2015-09-07
            getall = False
            for i in range(self.editor.GetLineCount()):
                line = self.editor.GetLine(i)
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

            num_header_lines = len(re.findall(r'\r\n|\r|\n', abc))

            return (abc, num_header_lines)
        else:
            return ('', 0)

    def GetSelectedTune(self, add_file_header=True):
        selItem = self.tune_list.GetFirstSelected()
        #print 'GetSelectedTune = ',selItem
        if selItem >= 0:
            return self.GetTune(selItem, add_file_header)
        else:
            return None

    def GetTune(self, listbox_index, add_file_header=True):
        index = self.tune_list.GetItemData(listbox_index)  # remap index in case items are sorted
        if index in self.tune_list.itemDataMap:
            (xnum, title, rythm, line_no) = self.tune_list.itemDataMap[index]
            offset_start = self.editor.PositionFromLine(line_no)
            offset_start, offset_end = self.GetTextRangeOfTune(offset_start)
            if add_file_header:
                header, num_header_lines = self.GetFileHeaderBlock()
            else:
                header, num_header_lines = '', 0
            abc = self.editor.GetTextRange(offset_start, offset_end)
            return Tune(xnum, title, rythm, offset_start, offset_end, abc, header, num_header_lines)
        else:
            return None

    def OnTuneDoubleClicked(self, evt):
        self.OnToolPlay(evt)
        evt.Skip()

    def OnTuneSelected(self, evt):
        global execmessages # [SS] 1.3.6 2014-11-11
        #print 'evt = '+ str(evt) + '  ' + str(self.tune_list.GetFirstSelected())
        #print traceback.extract_stack(None, 5)
        #self.execmessage_time set by OnDropFile(self, filename)

        # 1.3.6.4 [SS] 2015-06-11 -- to maintain consistency for different media players
        self.reset_BpmSlider()

        dt = datetime.now() - self.execmessage_time # 1.3.6 [SS] 2014-12-11
        dtime = dt.seconds*1000 + dt.microseconds/1000
        if evt is not None and dtime > 20000:
            execmessages = ''
        self.selected_tune = None

        tune = self.GetSelectedTune()
        if tune:
            self.music_update_thread.ConvertAbcToSvg(tune.abc, tune.header)
            if evt and (wx.Window.FindFocus() != self.editor and not (self.find_dialog and self.find_dialog.IsActive() or self.replace_dialog and self.replace_dialog.IsActive())):
            #if evt and wx.Window.FindFocus() != self.editor:
            #print wx.Window.FindFocus()
            #if evt and wx.Window.FindFocus() == self.tune_list:
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

    def UpdateTuneList(self):
        if self.tune_list.GetFirstSelected() > 0:
            selected_tune_index = self.tune_list.GetItemData(self.tune_list.GetFirstSelected())
        else:
            selected_tune_index =None
        tunes = self.GetTunes()
        self.tune_list.itemDataMap = dict(enumerate(self.tunes))

        different = (len(tunes) != len(self.tunes))
        if not different:
            for tune1, tune2 in zip(tunes, self.tunes):
                different = different or (tune1[:-1] != tune2[:-1])    # compare xnum, title and rythm but not line_no
        if different:
            top_item = self.tune_list.GetTopItem()
            self.tune_list.Freeze()
            self.tune_list.DeleteAllItems()
            for xnum, title, rythm, line_no in tunes:
                index = self.tune_list.InsertStringItem(self.tune_list.GetItemCount(), str(xnum))
                self.tune_list.SetStringItem(index, 1, title)
                #self.tune_list.SetStringItem(index, 2, rythm)
                self.tune_list.SetItemData(index, index)
                if index == selected_tune_index:
                    self.tune_list.SetItemState(index, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)


            # try to restore scroll state
            if tunes and top_item >= 0:
                last_visible_index = top_item + self.tune_list.GetCountPerPage() - 1
                if last_visible_index > self.tune_list.GetItemCount()-1:
                    last_visible_index = self.tune_list.GetItemCount()-1
                self.tune_list.EnsureVisible(last_visible_index)

            self.tune_list.Thaw()

        self.tunes = tunes

        if len(self.tunes) == 1 and self.tune_list.GetFirstSelected() == -1:
            self.tune_list.Select(0)
            self.OnTuneSelected(None)

        self.UpdateTuneListVisibility()


    def UpdateTuneListVisibility(self, force_update=False):
        pass
##        tune_list = self.manager.GetPane('tune list')
##        print len(self.tunes), tune_list.IsShown()
##        if len(self.tunes) > 1 and (not tune_list.IsShown() or force_update):
##            tune_list.Show()
##            print 'show tl'
##            self.manager.Update
##        elif len(self.tunes) <= 1 and (tune_list.IsShown() or force_update or True):
##            tune_list.Hide()
##            print 'hide tl'
##            self.manager.Update

    def OnTimer(self, evt):
        #self.UpdateTuneList()
        if len(self.tunes) == 1 and self.tune_list.GetFirstSelected() == -1:
            #self.tune_list.SetSelection(0)
            self.tune_list.Select(0)
            self.OnTuneSelected(None)
        self.OnToolRefresh(None)

    def GetTunes(self):
        n = self.editor.GetLineCount()
        cur_index = None
        cur_startline = None
        tunes = []
        for i in range(n):
            p = self.editor.PositionFromLine(i)
            try:
                t = self.editor.GetTextRange(p, p+2)
            except:
                t = ''
            if t == 'X:':
                if cur_index is not None:
                    tunes.append((cur_index, cur_title, cur_rythm, cur_startline))
                text = self.editor.GetLine(i)
                m = re.search(r'X: *(\d+)', text)
                if m:
                    cur_index = int(m.group(1))
                    cur_startline = i
                else:
                    cur_index = None
                cur_title = u''
                cur_rythm = u''
            elif cur_index is not None and t == 'T:' and not cur_title:
                cur_title = decode_abc(self.editor.GetLine(i)[2:].strip())
            elif cur_index is not None and t == 'R:' and not cur_rythm:
                cur_rythm = decode_abc(self.editor.GetLine(i)[2:].strip())

        if cur_index is not None:
            tunes.append((cur_index, unicode(cur_title or ''), unicode(cur_rythm or ''), cur_startline))
        return tunes

    def GetTuneAbc(self, startpos):
        first_line_no = self.editor.LineFromPosition(startpos)
        lines = [self.editor.GetLine(first_line_no)]
        for line_no in range(first_line_no+1, self.editor.GetLineCount()):
            line = self.editor.GetLine(line_no)
            if line.startswith('X:'):
                break
            lines.append(line)
        return ''.join(lines)

    def InitEditor(self, font_face=None, font_size=None):
        self.editor.ClearDocumentStyle()
        self.editor.StyleClearAll()
        self.editor.SetLexer(stc.STC_LEX_CONTAINER)
        self.editor.SetProperty("fold", "0")
        self.editor.SetUseTabs(False)
        self.editor.SetUseAntiAliasing(True)

        if not font_face:
            fixedWidthFonts = ['Bitstream Vera Sans Mono', 'Courier New', 'Courier']
            #fixedWidthFonts = ['Lucida Grande', 'Monaco' 'Inconsolata', 'Consolas', 'Deja Vu Sans Mono', 'Droid Sans Mono', 'Courier', 'Andale Mono', 'Monaco', 'Courier New', 'Courier']
            variableWidthFonts = ['Bitstream Vera Sans', 'Arial', 'Verdana']
            wantFonts = fixedWidthFonts[:]
            #wantFonts = variableWidthFonts[:]
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
            self.SetFont(wx.Font(size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, faceName=font))
        else:
            font = font_face
            size = font_size

        self.editor.SetProperty("fold", "0")
        self.editor.StyleSetSpec(self.styler.STYLE_DEFAULT, "fore:#000000,face:%s,size:%d" % (font, size))
        # Comments
        self.editor.StyleSetSpec(self.styler.STYLE_COMMENT_NORMAL,  "fore:#AAAAAA,face:%s,italic,size:%d" % (font, size))
        self.editor.StyleSetSpec(self.styler.STYLE_COMMENT_SPECIAL, "fore:#888888,face:%s,italic,size:%d" % (font, size))
        # Bar
        self.editor.StyleSetSpec(self.styler.STYLE_BAR, "fore:#00007F,face:%s,bold,size:%d" % (font, size))
        # Field
        self.editor.StyleSetSpec(self.styler.STYLE_FIELD,                "fore:#8C7853,face:%s,bold,size:%d" % (font, size))
        self.editor.StyleSetSpec(self.styler.STYLE_FIELD_VALUE,          "fore:#8C7853,face:%s,italic,size:%d" % (font, size))
        self.editor.StyleSetSpec(self.styler.STYLE_EMBEDDED_FIELD,       "fore:#8C7853,face:%s,bold,size:%d" % (font, size))
        self.editor.StyleSetSpec(self.styler.STYLE_EMBEDDED_FIELD_VALUE, "fore:#8C7853,face:%s,italic,size:%d" % (font, size))
        self.editor.StyleSetSpec(self.styler.STYLE_FIELD_INDEX,          "fore:#000000,face:%s,bold,underline,size:%d" % (font, size))
        # Single quoted string
        self.editor.StyleSetSpec(self.styler.STYLE_STRING, "fore:#7F7F7F,face:%s,italic,size:%d" % (font, size))
        # Lyrics
        self.editor.StyleSetSpec(self.styler.STYLE_LYRICS, "fore:#7F7F7F,face:%s,italic,size:%d" % (font, size))

        self.editor.StyleSetSpec(self.styler.STYLE_GRACE, "fore:#5a3700,face:%s,italic,size:%d" % (font, size))

        self.editor.StyleSetSpec(self.styler.STYLE_ORNAMENT, "fore:#777799,face:%s,bold,size:%d" % (font, size))
        self.editor.StyleSetSpec(self.styler.STYLE_ORNAMENT_PLUS, "fore:#888888,face:%s,size:%d" % (font, size))
        self.editor.StyleSetSpec(self.styler.STYLE_ORNAMENT_EXCL, "fore:#888888,face:%s,size:%d" % (font, size))

        self.editor.Colourise(0, self.editor.GetLength())


    def OnDropFile(self, filename):
        global execmessages, visible_abc_code
        info_messages = []
        # [SS] 2014-12-18
        options = namedtuple ('Options', 'u m c d n b v x p j')                     # emulate the options object
        options.m = 0; options.j = 0; options.p = []; options.b = 0; options.d = 0  # unused options
        options.n = 0; options.v = 0; options.u = 0; options.c = 0; options.x = 0   # but all may be used if needed
        if self.settings['xmlunfold']:
            options.u = 1
        if self.settings['xmlmidi']:
            options.m = 1
        if self.settings['xml_v'] != 0 :
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
            print options.p

        try:
            extension = os.path.splitext(filename)[1].lower()
            p = self.editor.GetLength()
            self.editor.SetSelection(p, p)
            if extension in ('.xml', '.mxl'):
                # 1.3.6 [SS] 2014-12-18
                self.AddTextWithUndo(u'\n%s\n' % xml_to_abc(filename,options,info_messages))
                execmessages = 'abc_to_xml '+ filename
                for infoline in info_messages:
                    execmessages += infoline
                return True
            if extension == '.nwc':
                try:
                    xml_file_path = NWCToXml(filename, self.cache_dir, self.settings.get('nwc2xml_path', None))
                    # 1.3.6 [SS] 2014-12-18
                    abc_code = xml_to_abc(xml_file_path,options,info_messages)
                    if '%%score 1 2' in abc_code:
                        abc_code = re.sub('%%score 1 2\s*', '', abc_code)
                        #abc_code = copy_bar_symbols_from_first_voice(abc_code)
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
            error_msg = ''.join(traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))
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
                self.editor.BeginUndoAction()
                self.editor.AddText('\n')
                self.editor.AddText(midi_to_abc(filename=filename, notes=notes,
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
                                    )
                self.editor.AddText('\n')
                self.editor.EndUndoAction()
                self.index += 1
        finally:
            dlg.Destroy() # 1.3.6.3 [JWDJ] 2015-04-21 always clean up dialog window
        return result

    def OnReducedMargins(self, evt):
        self.settings['reduced_margins'] = self.mni_reduced_margins.IsChecked()
        self.OnToolRefresh(None)

    def load_settings(self, load_window_size_pos=False, load_perspective=True):
        try:
            settings = pickle.load(open(self.settings_file, 'rb'))
        except Exception:
            settings = {} # ignore non-existant settings file (it will be created when the program exits)
        self.editor.SetZoom(settings.get('zoom', 0))
        if load_window_size_pos:
            # 1.3.6.3 [JWDJ] 2015-04-25 # sometimes window was unreachable because window_x and window_y set to -32000
            window_x = max(settings.get('window_x', 40), 0)
            window_y = max(settings.get('window_y', 40), 0)
            self.SetDimensions(window_x, window_y,
                               settings.get('window_width', 1000), settings.get('window_height', 800))
        if load_perspective:
            perspective = settings.get('perspective')
            # 1.3.6.3 [JWDJ] 2015-04-14 only load perspective if there is any.
            if perspective:
                self.manager.LoadPerspective(perspective)
        #self.bpm_slider.SetValue(settings.get('tempo', 100))
        self.bpm_slider.SetValue(0)
        self.zoom_slider.SetValue(settings.get('score_zoom', 1100))
        self.author = settings.get('author', '')
        self.mni_auto_refresh.Check(settings.get('auto_refresh', True))
        self.mni_reduced_margins.Check(settings.get('reduced_margins', True))
        self.mni_TA_active.Check(settings.get('typing_assistance_active', True))
        self.mni_TA_auto_case.Check(settings.get('typing_assistance_auto_case', False))
        self.mni_TA_do_re_mi.Check(settings.get('typing_assistance_do_re_mi', False))
        self.mni_TA_add_note_durations.Check(settings.get('typing_assistance_add_note_durations', False))
        self.mni_TA_add_bar.Check(settings.get('typing_assistance_add_bar', True))
        self.mni_TA_add_right.Check(settings.get('typing_assistance_add_right', True))
        self.OnZoomSlider(None)
        self.Update()
        self.Refresh()
        self.settings.update(settings)
        self.Maximize(settings.get('is_maximized', False))

        self.update_recent_files_menu()

        for i, width in enumerate(self.settings.get('tune_col_widths', [37, 100])):
            self.tune_list.SetColumnWidth(i, width)

        self.settings['record_bpm'] = self.settings.get('record_bpm', 70)
        for item in self.bpm_menu.GetMenuItems():
            if item.GetText() == str(self.settings['record_bpm']):
                item.Check()

        self.settings['record_metre'] = self.settings.get('record_metre', '3/4')
        for item in self.metre_menu.GetMenuItems():
            if item.GetText() == self.settings['record_metre']:
                item.Check()

        # reset captions since this is ruined by LoadPerspective
        self.manager.GetPane('abc editor').Caption(_("ABC code"))
        self.manager.GetPane('tune list').Caption(_("Tune list"))
        self.manager.GetPane('tune preview').Caption(_("Musical score"))
        self.manager.GetPane('error message').Caption(_("ABC errors")).Hide()
        self.manager.GetPane('abcassist').Caption(_("ABC assist")) # 1.3.6.3 [JWDJ] 2015-04-21 added ABC assist
        self.manager.Update()

        if 'font' in settings:
            face, size = settings['font'][-1], settings['font'][0]
            self.InitEditor(face, size)
            self.editor.SetFont(wx.Font(*settings['font']))

        self.music_pane.reset_scrolling()

    def get_tempo_multiplier(self):
        return 2.0 ** (float(self.bpm_slider.GetValue()) / 100)

    def save_settings(self):
        settings = self.settings
        settings['zoom'] = self.editor.GetZoom()
        settings['window_x'], settings['window_y']  = self.GetPositionTuple()
        settings['window_width'], settings['window_height'] = self.GetSizeTuple()
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

        # 1.3.6.4 [SS] 2015-07-16 ensure that EasyAbc links to the latest binaries
        # when the user starts version 1.3.6.4 for the first time.
        version = settings.get('version','0')
        if version != '1.3.6.4':
            abcm2ps_path  = None
            abc2midi_path = None
            abc2abc_path  = None 
            midi2abc_path = None

 
        abcm2ps_path = settings.get('abcm2ps_path')

        if not abcm2ps_path:
            if wx.Platform == "__WXMSW__":
                abcm2ps_path = os.path.join(cwd, 'bin', 'abcm2ps.exe')
            elif wx.Platform == "__WXMAC__":
                abcm2ps_path = os.path.join(cwd, 'bin', 'abcm2ps')
            else:
                abcm2ps_path = os.path.join(cwd, 'bin', 'abcm2ps')

        if os.path.exists(abcm2ps_path):
            settings['abcm2ps_path'] = abcm2ps_path # 1.3.6 [SS] 2014-11-12
        else:
            print abcm2ps_path,' ***  not found ***'
            dlg = wx.MessageDialog(self, _('abcm2ps was not found here. You need it to view the music. Go to settings and indicate the path.'), _('Warning'),wx.OK)
            dlg.ShowModal()


        abc2midi_path = settings.get('abc2midi_path')

        if not abc2midi_path:
            if wx.Platform == "__WXMSW__":
                abc2midi_path = os.path.join(cwd, 'bin', 'abc2midi.exe')
            elif wx.Platform == "__WXMAC__":
                abc2midi_path = os.path.join(cwd, 'bin', 'abc2midi')
            else:
                abc2midi_path = os.path.join(cwd, 'bin', 'abc2midi')

        if os.path.exists(abc2midi_path):
            settings['abc2midi_path'] = abc2midi_path # 1.3.6 [SS] 2014-11-12
        else:
            print abc2midi_path,' ***  not found ***'
            dlg = wx.MessageDialog(self, _('abc2midi was not found here. You need it to play the music. Go to settings and indicate the path.'), _('Warning'),wx.OK)
            dlg.ShowModal()


        abc2abc_path = settings.get('abc2abc_path')

        if not abc2abc_path:
            if wx.Platform == "__WXMSW__":
                abc2abc_path = os.path.join(cwd, 'bin', 'abc2abc.exe')
            elif wx.Platform == "__WXMAC__":
                abc2abc_path = os.path.join(cwd, 'bin', 'abc2abc')
            else:
                abc2abc_path = os.path.join(cwd, 'bin', 'abc2abc')

        midi2abc_path = settings.get('midi2abc_path')

        #1.3.6.4 [SS] 2015-06-22
        if not midi2abc_path:
            if wx.Platform == "__WXMSW__":
                midi2abc_path = os.path.join(cwd, 'bin', 'midi2abc.exe')
            elif wx.Platform == "__WXMAC__":
                midi2abc_path = os.path.join(cwd, 'bin', 'midi2abc')
            else:
                midi2abc_path = os.path.join(cwd, 'bin', 'midi2abc')

        settings['midi2abc_path'] = midi2abc_path

        if os.path.exists(abc2abc_path):
            settings['abc2abc_path'] = abc2abc_path # 1.3.6 [SS] 2014-11-12
        else:
            print abc2abc_path,' ***  not found ***'
            dlg = wx.MessageDialog(self,_('abc2abc was not found here. You need it to transpose the music. Go to settings and indicate the path.'),_('Warning'),wx.OK)
            dlg.ShowModal()

        midiplayer_path = settings.get('midiplayer_path')
        if not midiplayer_path:
            settings['midiplayer_path'] = ''
        else:
            # 1.3.6.4 [SS] 2015-05-27
            if not os.path.exists(midiplayer_path):
                dlg = wx.MessageDialog(self,_('The midiplayer was not found. You will not be able to play the MIDI file.'),_('Warning'),wx.OK)
                dlg.ShowModal() 

        gs_path = settings.get('gs_path')
        # 1.3.6.1 [SS] 2015-01-28
        #ps2pdf_path = settings.get('ps2pdf_path')
        #print 'gs_path = ',gs_path

        if not gs_path:
            if wx.Platform == "__WXMSW__":
                gs_path = get_ghostscript_path()
                settings['gs_path'] = gs_path
            elif wx.Platform == '__WXGTK__':
                gs_path = subprocess.check_output(["which", "gs"])
                #print gs_path
                settings['gs_path'] = gs_path[0:-1]
            #1.3.6.1 [SS] 2014-01-13
            elif wx.Platform == "__WXMAC__":
                #gs_path = os.path.join(cwd, 'gs-8.71-macosx')
                gs_path = '/usr/bin/pstopdf'
                settings['gs_path'] = gs_path
                # 1.3.6.1 [SS] 2015-01-28
                #ps2pdf_path = os.path.join(cwd, 'pstopdf')
                #settings['ps2pdf_path'] = ps2pdf_path

        # 1.3.6.1 [SS] 2015-01-12 2015-01-22
        gs_path = settings['gs_path'] #eliminate trailing \n
        if gs_path and (os.path.exists(gs_path) == False):
            msg = _('The executable %s could not be found') % gs_path
            dlg = wx.MessageDialog(self,msg,_('Warning'),wx.OK)
            dlg.ShowModal()

        # 1.3.6.1 [SS] 2015-01-13 2015-01-28
        #if wx.Platform == "__WXMAC__" and (os.path.exists(gs_path) == False):
            #if ps2pdf_path and  os.path.exists(ps2pdf_path) == False:
                #msg = 'The executable '+ps2pdf_path+' could not be found.'
                #dlg = wx.MessageDialog(self,msg,'Warning',wx.OK)
                #dlg.ShowModal()


        #print 'ps2pdf_path = ',ps2pdf_path
        nwc2xml_path = settings.get('nwc2xml_path')
        #print 'nwc2xml_path = ',nwc2xml_path
        if wx.Platform == "__WXMSW__":
            pass
        elif wx.Platform == "__WXMAC__":
            pass
        elif wx.Platform == "__WXGTK__":
            pass
        else:
            pass

# Upgrade to 1.3.6
        #Fix midi_program_ch settings - 1.3.5 to 1.3.6 compatibility 2014-11-14
        midi_program_ch_list=['midi_program_ch1', 'midi_program_ch2', 'midi_program_ch3', 'midi_program_ch4',
                              'midi_program_ch5', 'midi_program_ch6', 'midi_program_ch7', 'midi_program_ch8',
                              'midi_program_ch9', 'midi_program_ch10', 'midi_program_ch11', 'midi_program_ch12',
                              'midi_program_ch13', 'midi_program_ch14', 'midi_program_ch15', 'midi_program_ch16']
        for channel in range(1, 16+1):
            if settings.get(midi_program_ch_list[channel-1]):
                pass
            else:
                settings[midi_program_ch_list[channel-1]] = [0, 96, 64]

        #delete 'one_instrument_only'. It is no longer used. 1.3.6 [SS] 2014-11-20
        try:
            del self.settings['one_instrument_only']
        except:
            pass

        # 1.3.6 [SS] 2014-12-18
        new_settings = [('midi_program', 0), ('midi_chord_program', 24),
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
                        ('bpmtempo', '120'), ('chordvol', '96'), ('bassvol', '96'),
                        ('melodyvol', '96'), ('midi_intro', 0), ('version', '1.3.6.4')
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
        recent_files = self.settings.get('recentfiles', '').split('|')
        while self.recent_menu.MenuItemCount > 0:
            self.recent_menu.DeleteItem(self.recent_menu.FindItemByPosition(0))

        if len(recent_files) > 0:
            mru_index = 0
            recent_files_menu_id = 1100
            for path in recent_files:
                if path and os.path.exists(path):
                    self.append_menu_item(self.recent_menu, u'&{0}: {1}'.format(mru_index, path), path, self.on_recent_file, id=recent_files_menu_id)
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
        #frame = wx.GetApp().GetTopWindow()
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
an open source ABC editor for Windows, OSX and Linux. It is published under the <a href="http://www.gnu.org/licenses/gpl-2.0.html">GNU Public License</a>. </p>
<p><center><a href="http://www.nilsliberg.se/ksp/easyabc/">http://www.nilsliberg.se/ksp/easyabc/</a></center></p>
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
  <li> Available in <img src="img/new.gif"/>Dutch, Italian, French, Danish, Swedish and English</li>
  <li> Functions to generate incipits, sort tunes and renumber X: fields.</li>
  <li> Musical search function - search for note sequences irrespectively of key, etc. <img src="img/new.gif"/></li>
</ul>

<p><b>EasyABC</b> is brought to you by <b>Nils Liberg</b>, Copyright &copy; 2010-2012.</p>
<p><b>Credits</b> - software components used by EasyABC:</p>
<ul class="nicelist">
<li><a href="http://moinejf.free.fr/">abcm2ps</a> for converting ABC code to note images (developed/maintained by Jean-Fran&ccedil;ois Moine)</li>
<li><a href="http://abc.sourceforge.net/abcMIDI/">abc2midi</a> for converting ABC code to midi (by James Allwright, maintained by Seymour Shlien)</li>
<li><a href="http://wim.vree.org/svgParse/xml2abc.html">xml2abc</a> for converting from MusicXML to ABC (by Willem Vree)</li>
<li><a href="http://sites.google.com/site/juria90/nwc">nwc2xml</a> for converting from Noteworthy Composer format to ABC via XML (by James Lee)</li>
<li><a href="http://www.wxpython.org/">wxPython</a> cross-platform user-interface framework</li>
<li><a href="http://www.scintilla.org/">scintilla</a> for the text editor used for ABC code</li>
<li><a href="http://www.mxm.dk/products/public/pythonmidi">python midi package</a> for the initial parsing of midi files to be imported</li>
<li><a href="http://www.pygame.org/download.shtml">pygame</a> (which wraps <a href="http://sourceforge.net/apps/trac/portmedia/wiki/portmidi">portmidi</a>) for real-time midi input</li>
<li>Thanks to Guido Gonzato for providing the fields and command reference.
<li><br>Many thanks to the translators: Valerio&nbsp;Pelliccioni, Guido&nbsp;Gonzato&nbsp;(italian), Bendix&nbsp;R&oslash;dgaard&nbsp;(danish), Fr&eacute;d&eacute;ric&nbsp;Aup&eacute;pin&nbsp;(french) and Jan&nbsp;Wybren&nbsp;de&nbsp;Jong&nbsp;(dutch).</li>
<li>Universal binaries of abcm2ps and abc2midi for OSX are available thanks to Chuck&nbsp;Boody.</li>
</ul>

<p><b>Links</b></p>
<ul class="nicelist">
<li><a href="http://abcnotation.com/">abcnotation.com</a></li>
<li><a href="http://abcplus.sourceforge.net/">abcplus.sourceforge.net</a></li>
<li><a href="http://moinejf.free.fr/">Jef Moine's abcm2ps page</a></li>
<li><a href="http://ifdo.ca/~seymour/runabc/top.html">Seymour Shlien's abcMIDI page</a></li>
<li><a href="http://www.folkinfo.org/">folkinfo.org</a> (uses code from EasyABC to support MusicXML to ABC conversion)</li>
<li><a href="http://www.folkwiki.se/">folkwiki.se - Swedish folk music</a> (my involvement here is the reason why I implemented the program)</li>
</ul>
</body>
</html>
'''.format(program_name)

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, _('About EasyABC'), size=(900, 600) )
        os.chdir(cwd)
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


#p09 2014-10-22

class MyInfoFrame(wx.Frame):
    ''' Creates the TextCtrl for displaying any messages from abc2midi or abcm2ps. '''
    def __init__(self):
        # 1.3.6.1 [JWdJ] 2014-01-30 Resizing message window fixed
        wx.Frame.__init__(self, wx.GetApp().TopWindow, wx.ID_ANY, _("Messages"),style=wx.DEFAULT_FRAME_STYLE,name='infoframe',size=(600,240))
        # Add a panel so it looks the correct on all platforms
        self.panel = ScrolledPanel(self)
        self.basicText = wx.TextCtrl(self.panel,-1,"",style=wx.TE_MULTILINE | wx.TE_READONLY)
        # 1.3.6.3 [JWDJ] changed to fixed font so Abcm2ps-messages with a ^ make sense
        font = wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.basicText.SetFont(font)
        sizer = wx.BoxSizer()
        sizer.Add(self.basicText,1,wx.ALL|wx.EXPAND)
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
        self.basicText = stc.StyledTextCtrl(self, -1, (-1, -1), (600, 450))
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

        self.tree = wx.TreeCtrl(panel1, 1, wx.DefaultPosition, (-1,-1), wx.TR_HAS_BUTTONS )
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
        buffer = wx.EmptyBitmap(200, 200, 32)
        dc = wx.MemoryDC(buffer)
        dc.SetBackground(wx.WHITE_BRUSH)
        dc.Clear()
        dc = wx.GraphicsContext.Create(dc)
        try:
            for text in (u'G\u266d', u'G\u266f'):
                font_size = 12
                wxfont = wx.Font(font_size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, 'Helvetica', wx.FONTENCODING_DEFAULT )
                wxfont.SetPointSize(font_size)
                font = dc.CreateFont(wxfont, wx.NamedColour('black'))
                dc.SetFont(font)
                (width, height, descent, externalLeading) = dc.GetFullTextExtent(text)
                dc.DrawText(text, 100, 100-height+descent)
            self.settings['can_draw_sharps_and_flats'] = True
        except wx.PyAssertionError:
            self.settings['can_draw_sharps_and_flats'] = False


    def NewMainFrame(self):
        frame = MainFrame(None, 0, self.app_dir, self.settings)
        self._frames.append(frame)
        return frame

    def UnRegisterFrame(self, frame):
        self._frames.remove(frame)

    def GetAllFrames(self):
        L = self._frames[:]
        L.sort(key=lambda f: not f.IsActive()) # make sure an active frame comes first in the list
        return L

    def MacOpenFile(self, filename):
        frame = self.NewMainFrame()
        frame.Show(True)
        self.SetTopWindow(frame)
        ##path = os.path.abspath(sys.argv[1]).decode(sys.getfilesystemencoding())
        frame.load_or_import(filename)

    def OnInit(self):
        self.SetAppName('EasyABC')
        #wx.SystemOptions.SetOptionInt('msw.window.no-clip-children', 1)
        app_dir = self.app_dir = wx.StandardPaths.Get().GetUserLocalDataDir()
        if not os.path.exists(app_dir):
            os.mkdir(app_dir)
        cache_dir = os.path.join(app_dir, 'cache')
        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)

        default_lang = wx.LANGUAGE_DEFAULT
        ##default_lang = wx.LANGUAGE_JAPANESE
        locale = wx.Locale(language=default_lang)
        locale.AddCatalogLookupPathPrefix(os.path.join(cwd, 'locale'))
        locale.AddCatalog('easyabc')
        self.locale = locale # keep this reference alive
        wx.ToolTip.Enable(True)
        wx.ToolTip.SetDelay(1000)

        locale = wx.Locale(language=default_lang)
        #locale = wx.Locale(wx.LANGUAGE_JAPANESE)
        locale.AddCatalogLookupPathPrefix(os.path.join(cwd, 'locale'))
        locale.AddCatalog('easyabc')

        self.CheckCanDrawSharpFlat()

        #p08 We need to be able to find app.frame [SS] 2014-10-14
        self.frame = self.NewMainFrame()
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        if len(sys.argv) > 1:
            path = os.path.abspath(sys.argv[1]).decode(sys.getfilesystemencoding())
            self.frame.load_or_import(path)
        return True

app = MyApp(0)

#import wx.lib.inspection
#wx.lib.inspection.InspectionTool().Show()

app.MainLoop()



