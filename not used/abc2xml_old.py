# coding=latin-1
'''
Copyright (C) 2012: W.G. Vree

This program is free software; you can redistribute it and/or modify it under the terms of the
GNU General Public License as published by the Free Software Foundation; either version 2 of
the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details. <http://www.gnu.org/licenses/gpl.html>.
'''

from pyparsing import Word, OneOrMore, Optional, Or, Literal, NotAny
from pyparsing import Group, oneOf, Suppress, ZeroOrMore, Combine
from pyparsing import srange, CharsNotIn, StringEnd, LineEnd, White, Regex
from pyparsing import nums, alphas, alphanums, ParseException
try:    import xml.etree.cElementTree as E
except: import xml.etree.ElementTree as E
import types, sys, os, re, datetime

VERSION = 33

def info (s, warn=1):
    x = (warn and '-- ' or '') + s
    try: sys.stderr.write (x + '\n')
    except: sys.stderr.write (repr (x) + '\n')

def abc_grammar ():     # header, voice and lyrics grammar for ABC

    #-----------------------------------------------------------------
    # ABC header (fld_text elements are matched later with reg. epr's)
    #-----------------------------------------------------------------

    number = Word (nums).setParseAction (lambda t: int (t[0]))
    field_str = Regex (r'(?:\\.|[^]\\])*')  # match anything until end of field, skip escaped \]
    field_str.setParseAction (lambda t: t[0].strip ())  # and strip spacing

    userdef_symbol  = Word (srange ('[H-Wh-w~]'), exact=1)
    hdr_fld = oneOf ('T C I O A Z N G H R B D F S') # header only fields
    bdy_fld = oneOf ('K L M Q P')                   # fields for body and header
    X_field = Literal ('X') + Suppress (':') + number
    U_field = Literal ('U') + Suppress (':') + userdef_symbol + Suppress ('=') + Word (alphas+'!')
    V_field = Literal ('V') + Suppress (':') + Word (alphanums) + field_str
    bdy_field = bdy_fld     + Suppress (':') + field_str
    hdr_field = hdr_fld     + Suppress (':') + field_str
    ifield = Suppress ('[') + (X_field | U_field | V_field | hdr_field | bdy_field) + Suppress (']')
    abc_header = OneOrMore (ifield) + StringEnd ()

    #---------------------------------------------------------------------------------
    # ABC voice (not white space sensitive, beams detected in note/rest parse actions)
    #---------------------------------------------------------------------------------

    inline_field =  Suppress ('[') + (bdy_field | V_field) + Suppress (']')

    note_length = Optional (number, 1) + Group (ZeroOrMore ('/')) + Optional (number, 2)
    octaveHigh = OneOrMore ("'").setParseAction (lambda t: len(t))
    octaveLow = OneOrMore (',').setParseAction (lambda t: -len(t))
    octave  = octaveHigh | octaveLow

    basenote = oneOf ('C D E F G A B c d e f g a b')
    accidental = oneOf ('^^ __ ^ _ =')
    spacer = Suppress ('y')
    invisible_rest  = Literal ('x')
    normal_rest = Literal ('z')
    slur_beg = oneOf ('( .(') + ~Word (nums)    # no tuplet_start
    slur_ends = OneOrMore (oneOf (') .)'))

    long_decoration = oneOf ('! +').suppress () + Word (alphanums + '().<>/') + oneOf ('! +').suppress ()
    decoration      = Literal ('.') | userdef_symbol | long_decoration | slur_beg
    decorations     = OneOrMore (decoration)
    staff_decos     = decorations + ~oneOf (': | [|] []')

    tie = oneOf ('.- -')
    rest = (normal_rest | invisible_rest ) + note_length
    pitch = Optional (accidental) + basenote + Optional (octave, 0)
    note = pitch + note_length + Optional (tie) + Optional (slur_ends)
    chord_note = Optional (decorations) + note.copy ()  # avoid burden of decoration parsing on each note
    chord = Suppress ('[') + OneOrMore (chord_note) + Suppress (']') + note_length + Optional (tie) + Optional (slur_ends)
    stem = note | chord | rest | spacer

    broken = Combine (OneOrMore ('<') | OneOrMore ('>'))

    tuplet_num   = Suppress ('(') + number
    tuplet_into  = Suppress (':') + Optional (number)
    tuplet_notes = Suppress (':') + Optional (number)
    tuplet_start = tuplet_num + Optional (tuplet_into + Optional (tuplet_notes))

    acciaccatura    = Literal ('/')
    grace_notes     = Suppress ('{') + Optional (acciaccatura) + OneOrMore (stem) + Suppress ('}')

    text_expression  = Optional (oneOf ('^ _ < > @'), '^') + CharsNotIn ('"')
    chord_accidental = oneOf ('# b =')
    triad            = oneOf ('Maj maj M min m aug dim + -')
    seventh          = oneOf ('7 Maj7 M7 maj7 m7 dim7 7- aug7 7+ m7b5')
    sixth            = oneOf ('6 m6')
    ninth            = oneOf ('9 M9 maj9 Maj9 m9')
    elevn            = oneOf ('11 M11 maj11 Maj11 m11')
    suspended        = oneOf ('sus sus2 sus4')
    chord_degree     = Combine (Optional (chord_accidental) + oneOf ('2 4 5 6 7 9 11 13'))
    chord_kind       = Optional (seventh | sixth | ninth | elevn | triad, '_') + Optional (suspended)
    chord_root       = oneOf ('C D E F G A B') + Optional (chord_accidental)
    chord_bass       = chord_root.copy ()   # copy because we need a separate parse action
    chordsym         = chord_root + chord_kind + ZeroOrMore (chord_degree) + Optional (Suppress ('/') + chord_bass)
    chord_sym        = chordsym + Optional (Literal ('(') + CharsNotIn (')') + Literal (')')).suppress ()
    chord_or_text    = Suppress ('"') + (chord_sym ^ text_expression) + Suppress ('"')

    volta = Optional (oneOf ('[ |')).suppress () + Combine (Word (nums) + ZeroOrMore (oneOf (', -') + Word (nums)))
    invisible_barline = oneOf ('[|] []')
    dashed_barline = Literal (':')
    voice_overlay = Combine (OneOrMore ('&'))
    bar_left = (oneOf ('[|: |: :') + Optional (volta)) | volta | Literal ('|')
    bars = ZeroOrMore (':') + ZeroOrMore ('[') + OneOrMore ('|') + ZeroOrMore (']')
    bar_right = Optional (decorations) + (invisible_barline | Combine (bars) | dashed_barline | voice_overlay)

    linebreak = Literal ('$') | ~decorations + Literal ('!')    # no need for I:linebreak !!!
    element = inline_field | broken | staff_decos | stem | chord_or_text | grace_notes | tuplet_start | linebreak
    measure = Group (ZeroOrMore (inline_field) + Optional (bar_left) + ZeroOrMore (element) + bar_right + Optional (linebreak))
    noBarMeasure = Group (Optional (bar_left) + OneOrMore (element) + Optional (linebreak))
    abc_voice = ZeroOrMore (measure) + Optional (noBarMeasure | Group (bar_left)) + StringEnd ()

    #----------------------------------------
    # ABC lyric lines (white space sensitive)
    #----------------------------------------

    skip_note   = oneOf ('* -')
    extend_note = Literal ('_')
    measure_end = Literal ('|')
    syl_chars   = CharsNotIn ('*~-_| \t\n')
    white       = Word (' \t')
    syllable    = Combine (syl_chars + ZeroOrMore (Literal ('~') + syl_chars)) + Optional ('-')
    lyr_elem    = (syllable | skip_note | extend_note | measure_end) + Optional (white).suppress ()
    lyr_head    = (Literal ('w:') + Optional (white)).suppress ()
    lyr_line    = Group (lyr_head + ZeroOrMore (lyr_elem) + LineEnd ().suppress ())

    #----------------------------------------------------------------
    # Parse actions to convert all relevant results into an abstract
    # syntax tree where all tree nodes are instances of pObj
    #----------------------------------------------------------------

    ifield.setParseAction (lambda t: pObj ('field', t))
    note_length.setParseAction (lambda t: pObj ('dur', (t[0], (t[2] << len (t[1])) >> 1)))
    chordsym.setParseAction (lambda t: pObj ('chordsym', t))
    chord_root.setParseAction (lambda t: pObj ('root', t))
    chord_kind.setParseAction (lambda t: pObj ('kind', t))
    chord_degree.setParseAction (lambda t: pObj ('degree', t))
    chord_bass.setParseAction (lambda t: pObj ('bass', t))
    text_expression.setParseAction (lambda t: pObj ('text', t))
    inline_field.setParseAction (lambda t: pObj ('inline', t))
    grace_notes.setParseAction (lambda t: pObj ('grace', t))
    acciaccatura.setParseAction (lambda t: pObj ('accia', t))
    note.setParseAction (noteActn)
    chord_note.setParseAction (noteActn)
    rest.setParseAction (restActn)
    decorations.setParseAction (lambda t: pObj ('deco', t))
    slur_ends.setParseAction (lambda t: pObj ('slurs', t))
    chord.setParseAction (lambda t: pObj ('chord', t))
    tie.setParseAction (lambda t: pObj ('tie', t))
    pitch.setParseAction (lambda t: pObj ('pitch', t))
    bar_right.setParseAction (lambda t: pObj ('rbar', t))
    bar_left.setParseAction (lambda t: pObj ('lbar', t))
    broken.setParseAction (lambda t: pObj ('broken', t))
    tuplet_start.setParseAction (lambda t: pObj ('tup', t))
    linebreak.setParseAction (lambda t: pObj ('linebrk', t))
    measure.setParseAction (doMaat)
    noBarMeasure.setParseAction (doMaat)
    syllable.setParseAction (lambda t: pObj ('syl', t))
    skip_note.setParseAction (lambda t: pObj ('skip', t))
    extend_note.setParseAction (lambda t: pObj ('ext', t))
    measure_end.setParseAction (lambda t: pObj ('sbar', t))

    lyr_block   = OneOrMore (lyr_line).leaveWhitespace ()   # after leaveWhiteSpace no more parse actions can be set!!

    return abc_header, abc_voice, lyr_block

class pObj (object):    # every relevant parse result is converted into a pObj
    def __init__ (s, name, t):  # t = list of nested parse results
        s.name = name   # name uniqueliy identifies this pObj
        rest = []       # collect parse results that are not a pObj
        attrs = {}      # new attributes
        for x in t:     # nested pObj's become attributes of this pObj
            if type (x) == pObj:
                attrs [x.name] = attrs.get (x.name, []) + [x]
            else:
                rest.append (x)             # collect non-pObj's (mostly literals)
        for name, xs in attrs.items ():
            if len (xs) == 1: xs = xs[0]    # only list if more then one pObj
            setattr (s, name, xs)           # create the new attributes
        s.t = rest      # all nested non-pObj's (mostly literals)
        s.objs = []     # for nested ordered (lyric) pObj's

    def __repr__ (s):   # make a nice string representation of a pObj
        r = []
        for nm in dir (s):
            if nm.startswith ('_'): continue # skip build in attributes
            elif nm == 'name': continue     # redundant
            else:
                x = getattr (s, nm)
                if not x: continue          # s.t may be empty (list of non-pObj's)
                if type (x) == types.ListType:  r.extend (x)
                else:                           r.append (x)
        xs = []
        for x in r:     # recursively call __repr__ and convert all strings to latin-1
            if not isinstance (x, types.StringTypes): xs.append (repr (x))
            else:                                     xs.append (x.encode ('latin-1'))
        return '(' + s.name + ' ' +','.join (xs) + ')'

global prevloc                  # global to remember previous match position of a note/rest
prevloc = 0
def detectBeamBreak (line, loc, t):
    global prevloc              # location in string 'line' of previous note match
    xs = line[prevloc:loc+1]    # string between previous and current note match
    xs = xs.lstrip ()           # first note match starts on a space!
    prevloc = loc               # location in string 'line' of current note match
    b = pObj ('bbrk', [' ' in xs])      # space somewhere between two notes -> beambreak
    t.insert (0, b)             # insert beambreak as a nested parse result

def noteActn (line, loc, t):    # detect beambreak between previous and current note/rest
    detectBeamBreak (line, loc, t)      # adds beambreak to parse result t as side effect
    return pObj ('note', t)

def restActn (line, loc, t):    # detect beambreak between previous and current note/rest
    detectBeamBreak (line, loc, t)  # adds beambreak to parse result t as side effect
    return pObj ('rest', t)

#-------------------------------------------------------------
# transformations of a measure (called by parse action doMaat)
#-------------------------------------------------------------

def simplify (a, b):    # divide a and b by their greatest common divisor
    x, y = a, b
    while b: a, b = b, a % b
    return x / a, y / a

def doBroken (prev, brk, x):
    nom1, den1 = prev.dur.t # duration of first note/chord
    nom2, den2 = x.dur.t    # duration of second note/chord
    if  brk == '>':
        nom1, den1  = simplify (3 * nom1, 2 * den1)
        nom2, den2  = simplify (1 * nom2, 2 * den2)
    elif brk == '<':
        nom1, den1  = simplify (1 * nom1, 2 * den1)
        nom2, den2  = simplify (3 * nom2, 2 * den2)
    elif brk == '>>':
        nom1, den1  = simplify (7 * nom1, 4 * den1)
        nom2, den2  = simplify (1 * nom2, 4 * den2)
    elif brk == '<<':
        nom1, den1  = simplify (1 * nom1, 4 * den1)
        nom2, den2  = simplify (7 * nom2, 4 * den2)
    else: return            # give up
    prev.dur.t = nom1, den1
    x.dur.t = nom2, den2

def convertBroken (t):  # convert broken rhythms to normal note durations
    prev = None
    brk = ''
    remove = []
    for i, x in enumerate (t):
        if x.name == 'note' or x.name == 'chord':
            if brk:                 # a broken sign was encountered
                doBroken (prev, brk, x)
                brk = ''
            else:
                prev = x            # remember the last note/chord
        elif x.name == 'broken':
            brk = x.t[0]
            remove.insert (0, i)    # highest index first
    for i in remove: del t[i]       # from high to low

def convertChord (t):   # convert chord to sequence of notes in musicXml-style
    ins = []
    for i, x in enumerate (t):
        if x.name == 'chord':
            num1, den1 = x.dur.t                # chord duration
            tie = getattr (x, 'tie', None)      # chord tie
            slurs = getattr (x, 'slurs', [])    # slur endings
            deco = getattr (x, 'deco', [])      # chord decorations
            for j, nt in enumerate (x.note):    # all notes of the chord
                num2, den2 = nt.dur.t           # note duration * chord duration
                nt.dur.t = simplify (num1 * num2, den1 * den2)
                if tie: nt.tie = tie            # tie on all chord notes
                if j == 0 and deco: nt.deco = deco      # decorations only on first chord note
                if j == 0 and slurs: nt.slurs = slurs   # slur endings only on first chord note
                if j > 0: nt.chord = pObj ('chord', [1]) # label all but first as chord notes
            ins.insert (0, (i, x.note))         # high index first
    for i, notes in ins:                        # insert from high to low
        for nt in reversed (notes):
            t.insert (i+1, nt)                  # insert chord notes after chord
        del t[i]                                # remove chord itself

def doMaat (t):             # t is a Group() result -> the measure is in t[0]
    convertBroken (t[0])    # remove all broken rhythms and convert to normal durations
    convertChord (t[0])     # replace chords by note sequences in musicXML style

#--------------------
# musicXML generation
#----------------------------------

def compChordTab ():    # avoid some typing work: returns mapping constant {ABC chordsyms -> musicXML kind}
    maj, min, aug, dim, dom, ch7, ch6, ch9, ch11 = 'major minor augmented diminished dominant -seventh -sixth -ninth -11th'.split ()
    triad   = zip ('Maj maj M min m aug dim + -'.split (), [maj, maj, maj, min, min, aug, dim])
    seventh = zip ('7 Maj7 M7 maj7 m7 dim7 7- aug7 7+ m7b5'.split (),
                   [dom, maj+ch7, maj+ch7, maj+ch7, min+ch7, dim+ch7, dim+ch7, aug+ch7, aug+ch7, 'half-diminished'])
    sixth   = zip ('6 m6'.split (), [maj+ch6, min+ch6])
    ninth   = zip ('9 M9 maj9 Maj9 m9'.split (), [dom+ch9, maj+ch9, maj+ch9, maj+ch9, min+ch9])
    elevn   = zip ('11 M11 maj11 Maj11 m11'.split (), [dom+ch11, maj+ch11, maj+ch11, maj+ch11, min+ch11])
    return dict (triad + seventh + sixth + ninth + elevn)

def addElem (parent, child, level):
    indent = 2
    chldrn = parent.getchildren ()
    if chldrn:
        chldrn[-1].tail += indent * ' '
    else:
        parent.text = '\n' + level * indent * ' '
    parent.append (child)
    child.tail = '\n' + (level-1) * indent * ' '

def addElemT (parent, tag, text, level):
    e = E.Element (tag)
    e.text = text
    addElem (parent, e, level)
    
def mkTmod (tmnum, tmden, lev):
    tmod = E.Element ('time-modification')
    addElemT (tmod, 'actual-notes', str (tmnum), lev + 1)
    addElemT (tmod, 'normal-notes', str (tmden), lev + 1)
    return tmod

def addDirection (parent, elem, lev, subel=None, placement='below'):
    dir = E.Element ('direction', placement=placement)
    addElem (parent, dir, lev)
    typ = E.Element ('direction-type')
    addElem (dir, typ, lev + 1)
    addElem (typ, elem, lev + 2)
    if subel != None: addElem (elem, subel, lev + 3)
    return dir

def alignLyr (vce, lyrs):
    empty_el = pObj ('leeg', '*')
    for k, lyr in enumerate (lyrs): # lyr = one full line of lyrics
        i = 0               # syl counter
        for msre in vce:    # reiterate the voice block for each lyrics line
            for elem in msre:
                if elem.name == 'note' and not hasattr (elem, 'chord'):
                    if i >= len (lyr): lr = empty_el
                    else: lr = lyr [i]
                    elem.objs.append (lr)
                    if lr.name != 'sbar': i += 1
            if i < len (lyr) and lyr[i].name == 'sbar': i += 1
    return vce

slur_move = re.compile (r'(?<!!)([}><][<>]?)(\)+)') # (?<!...) means: not preceeded by ...
def fixSlurs (x):   # repair slurs when after broken sign or grace-close
    return slur_move.sub (r'\2\1', x)

def splitHeaderVoices (abctext):
    r1 = re.compile (r'%.*$')           # comments
    r2 = re.compile (r'^([A-Z]:.*)$')   # information field
    r3 = Word (alphanums) | Suppress ('(') + OneOrMore (Word (alphanums)) + Suppress (')')
    xs, staves = [], []
    for x in abctext.split ('\n'):
        x = x.strip ()
        if x.startswith ('%%score'):    # extract voice mapping
            staves = [res[0] for res in r3.scanString (x)][1:]  # skip first item: "score"
        x2 = r1.sub ('', x)             # remove comment
        if not x2: continue             # empty line
        if x2[:2] == ('W:'): continue   # skip W: lyrics
        ro = r2.match (x2)
        if ro:                          # field -> inline_field, escape all ']'
            x2 = '[' + ro.group (1).replace (']',r'\]') + ']'
        if x2[:2] == '+:':              # new style continuation
            xs[-1] += x2[2:]
        elif xs and xs[-1][-1] ==  '\\':  # old style continuation
            xs[-1] = xs[-1][:-1] + x2
        else:
            xs.append (x2)

    r1 = re.compile (r'\[(\\.|[^]\\])*\]') # inline field with escaped ']'
    r2 = re.compile (r'\[K:')           # start of K: field
    r3 = re.compile (r'\[V:')           # start of V: field
    fields, voices = [], []
    for i, x in enumerate (xs):
        n = len (r1.sub ('', x))        # remove all inline fields
        if n > 0: break                 # real abc present -> end of header
        if r2.search (x):               # start of K: field
            fields.append (x)
            i += 1
            break                       # first K: field -> end of header
        if r3.search (x):               # start of V: field
            voices.append (x)
        else:
            fields.append (x)
    voices += xs[i:]
    header =  '\n'.join (fields)
    abctext = '\n'.join (voices)

    r1 = re.compile (r'\[V:(\S*)[ \]]') # get voice id from V: field
    vmap = {}                           # {voice id -> [voice abc string]}
    vorder = {}                         # mark document order of voices
    xs = re.split (r'(\[V:[^]]*\])', abctext)   # split on every V-field (V-fields included in split result list)
    if len (xs) == 1:                   # no voices
        vmap ['1'] = xs[0]
        vorder ['1'] = 1
    else:
        i = 1
        while i < len (xs):             # xs = ['', V-field, voice abc, V-field, voice abc, ...]
            vce, abc = xs[i:i+2]
            id = r1.search (vce).group (1)                  # get voice ID from V-field
            vmap[id] = vmap.get (id, []) + [vce, abc]       # collect abc-text for each voice id (include V-fields)
            if id not in vorder: vorder [id] = i            # store document order of first occurrence of voice id
            i += 2
    voices = []
    ixs = sorted ([(i, id) for id, i in vorder.items ()])   # restore document order of voices
    for i, id in ixs:
        voice = ''.join (vmap [id])                         # all abc of one voice
        xs = re.split (r'((?:\nw:[^\n]*)+)', voice)         # split voice into voice-lyrics blocks
        if len (xs) == 1:               # no lyrics
            voice = fixSlurs (xs[0])    # put slurs right after the notes
            vce_lyr = [[voice, '']]
        else:
            if xs[-1].strip () != '': xs.append ('w:')               # last block had no lyrics
            vce_lyr = []                # [[voice, lyrics],[],...] list of voice-lyrics blocks
            for k in range (0, len (xs) - 1, 2):
                voice, lyrics = xs [k:k+2]
                voice = fixSlurs (voice)    # put slurs right after the notes
                vce_lyr.append ((voice, lyrics))
        voices.append ((id, vce_lyr))

    return header, voices, staves

def mergeMeasure (m1, m2, slur_offset):
    slurs = m2.findall ('note/notations/slur')
    for slr in slurs:
        slrnum = int (slr.get ('number')) + slur_offset 
        slr.set ('number', str (slrnum))    # make unique slurnums in m2
    vs = m1.findall ('note/voice')          # all voice number elements in m1
    vnum_max = max ([int (v.text) for v in vs] + [0])   # highest voice number in m1
    vs = m2.findall ('note/voice')          # set all voice number elements in m2
    for v in vs: v.text  = str (vnum_max + 1)
    ls = m1.findall ('note/lyric')          # all lyric elements in m1
    lnum_max = max ([int (l.get ('number')) for l in ls] + [0]) # highest lyric number in m1
    ls = m2.findall ('note/lyric')          # update lyric elements in m2
    for el in ls:
        n = int (el.get ('number'))
        el.set ('number', str (n + lnum_max))
    ns = m1.findall ('note')    # determine the total duration of m1, subtract all backups
    dur1 = sum (int (n.find ('duration').text) for n in ns
                if n.find ('grace') == None and n.find ('chord') == None)
    dur1 -= sum (int (b.text) for b in m1.findall ('backup/duration'))
    nns, es = 0, []             # nns = number of real notes in m2
    for e in m2.getchildren (): # scan all elements of m2
        if e.tag == 'attributes': continue
        if e.tag == 'print': continue
        if e.tag == 'note' and e.find ('rest') == None: nns += 1
        es.append (e)           # buffer elements to be merged
    if nns > 0:                 # only merge if m2 contains any real notes
        b = E.Element ('backup')
        addElem (m1, b, level=3)
        addElemT (b, 'duration', str (dur1), level=4)
        for e in es: addElem (m1, e, level=3)   # merge buffered elements of m2

def mergePartList (parts, partlist):
    p1 = parts[0]
    for ip, p2 in enumerate (parts[1:]):
        slurs = p1.findall ('measure/note/notations/slur')  # find highest slur num in first part
        slur_max = max ([int (slr.get ('number')) for slr in slurs] + [0])
        for im, m2 in enumerate (p2.findall ('measure')):   # merge all measures of p2 into p1
            mergeMeasure (p1[im], m2, slur_max)     # may change slur numbers in p1
    return parts[0], partlist[0]

def mergeParts (parts, partlist, staves):
    if not staves: return parts, partlist  # no voice mapping
    vids = [pid[1:] for pid, _ in partlist] # strip P from part-ID -> abc voice-ID
    partsnew, partlistnew = [], []
    for voice_ids in staves:
        try: pixs = [vids.index (vid) for vid in voice_ids] # index in parts of each voice to be merged
        except: continue    # partname from %%score does not exist in partlist
        xparts = [parts[pix] for pix in pixs]
        xpartlist = [partlist[pix] for pix in pixs]
        mergedpart, mergedpartlist = mergePartList (xparts, xpartlist)
        partsnew.append (mergedpart)
        partlistnew.append (mergedpartlist)
    return partsnew, partlistnew

def mergePartMeasure (part, msre):  # merge msre into last measure of part
    slurs = part.findall ('measure/note/notations/slur')    # find highest slur num in part
    slur_max = max ([int (slr.get ('number')) for slr in slurs] + [0])
    last_msre = part.getchildren ()[-1] # last measure in part
    mergeMeasure (last_msre, msre, slur_max)

class MusicXml:
    typeMap = {1:'long', 2:'breve', 4:'whole', 8:'half', 16:'quarter', 32:'eighth', 64:'16th', 128:'32nd', 256:'64th'}
    dynaMap = {'p':1,'pp':1,'ppp':1,'f':1,'ff':1,'fff':1,'mp':1,'mf':1,'sfz':1}
    wedgeMap = {'>(':1, '>)':1, '<(':1,'<)':1}
    artMap = {'.':'staccato','>':'accent','accent':'accent','wedge':'staccatissimo','tenuto':'tenuto'}
    ornMap = {'trill':'trill-mark','T':'trill-mark','turn':'turn','uppermordent':'inverted-mordent','lowermordent':'mordent',
              'pralltriller':'inverted-mordent','mordent':'mordent','turn':'turn','invertedturn':'inverted-turn'}
    tecMap = {'upbow':'up-bow', 'downbow':'down-bow'}
    capoMap = {'fine':('Fine','fine','yes'), 'D.S.':('D.S.','dalsegno','segno'), 'D.C.':('D.C.','dacapo','yes'),'dacapo':('D.C.','dacapo','yes'),
               'dacoda':('To Coda','tocoda','coda'), 'coda':('coda','coda','coda'), 'segno':('segno','segno','segno')}
    sharpness = ['Cb','Gb','Db','Ab','Eb','Bb','F','C','G','D','A', 'E', 'B', 'F#','C#','G#','D#','A#']
    clefMap = { 'alto1':('C','1'), 'alto2':('C','2'), 'alto':('C','3'), 'tenor':('C','4'), 'bass3':('F','3'),
                'bass':('F','4'), 'treble':('G','2'), 'perc':('percussion',''), 'none':('','')}
    alterTab = {'=':'0', '_':'-1', '__':'-2', '^':'1', '^^':'2'}
    chordTab = compChordTab ()
    uSyms = {'~':'roll', 'H':'fermata','L':'>','M':'lowermordent','O':'coda',
             'P':'uppermordent','S':'segno','T':'trill','u':'upbow','v':'downbow'}

    def __init__ (s): s.reset ()
    def reset (s):
        s.divisions = 120   # xml duration of 1/4 note
        s.ties = {}         # {abc pitch tuple -> alteration} for all open ties
        s.slurstack = []    # stack of open slur numbers
        s.slurbeg = 0       # number of slurs to start (when slurs are detected at element-level)
        s.tmnum = 0         # time modification, numerator
        s.tmden = 0         # time modification, denominator
        s.ntup = 0          # number of tuplet notes remaining
        s.unitL =  (1, 8)   # default unit length
        s.unitLcur = (1, 8) # unit length of current voice
        s.keyAlts = {}      # alterations implied by key
        s.msreAlts = {}     # temporarily alterations
        s.curVolta = ''     # open volta bracket
        s.slurstack = []    # stack of open slur numbers
        s.title = ''        # title of music
        s.creator = {}      # {creator-type -> creator string}
        s.lyrdash = {}      # {lyric number -> 1 if dash between syllables}
        s.usrSyms = s.uSyms # user defined symbols
        s.prevNote = None   # xml element of previous note to correct beams (start, continue)
        s.grcbbrk = False   # remember any bbrk in a grace sequence
        s.linebrk = 0       # 1 if next measure should start with a line break
        s.bardecos = []     # barline decorations (coda, segno) that go into the next measure (MuseScore deficiency!)
        s.nextdecos = []    # decorations for the next note

    def mkPitch (s, acc, note, oct, lev):
        nUp = note.upper ()
        octnum = (4 if nUp == note else 5) + int (oct)
        pitch = E.Element ('pitch')
        addElemT (pitch, 'step', nUp, lev + 1)
        alter = ''
        if (note, oct) in s.ties:           alter = s.ties [(note,oct)] # tied note -> same alteration
        elif acc:
            s.msreAlts [(nUp, octnum)] = s.alterTab [acc]
            alter = s.alterTab [acc]                                    # explicit notated alteration
        elif (nUp, octnum) in s.msreAlts:   alter = s.msreAlts [(nUp, octnum)]  # temporary alteration
        elif nUp in s.keyAlts:              alter = s.keyAlts [nUp]     # alteration implied by the key
        if alter: addElemT (pitch, 'alter', alter, lev + 1)
        addElemT (pitch, 'octave', str (octnum), lev + 1)
        return pitch, alter

    def mkNote (s, n, lev):
        nnum, nden = n.dur.t        # abc dutation of note
        num, den = simplify (nnum * s.unitLcur[0], nden * s.unitLcur[1])  # normalised with unit length
        dvs = (4 * s.divisions * num) / den     # divisions is xml-duration of 1/4
        num, den = simplify (num, den * 4)      # scale by 1/4 for s.typeMap
        ndot = 0
        if num == 3: ndot = 1; den = den / 2    # look for dotted notes
        if num == 7: ndot = 2; den = den / 4
        nt = E.Element ('note')
        if getattr (n, 'chord', ''):       # a chord note
            chord = E.Element ('chord')
            addElem (nt, chord, lev + 1)
        elif getattr (n, 'grace', ''):  # a grace note
            grace = E.Element ('grace')
            addElem (nt, grace, lev + 1)
            dvs = 0                     # no real duration for a grace note
            if den <= 16: den = 32      # not longer than 1/8 for a grace note
        elif s.ntup >= 0: s.ntup -= 1   # count tuplet notes only on non-chord, non grace notes
        xmltype = str (s.typeMap [den]) # xml needs the note type in addition to duration
        acc, step, oct = '', 'C', '0'   # abc-notated pitch elements (accidental, pitch step, octave)
        alter = ''                      # xml alteration
        if n.name == 'rest':
            rest = E.Element ('rest')
            addElem (nt, rest, lev + 1)
        else:
            p = n.pitch.t           # get pitch elements from parsed tokens
            if len (p) == 3:    acc, step, oct = p
            else:               step, oct = p
            pitch, alter = s.mkPitch (acc, step, oct, lev + 1)
            addElem (nt, pitch, lev + 1)
        if s.ntup >= 0:             # modify duration for tuplet notes
            dvs = dvs * s.tmden / s.tmnum
        if dvs: addElemT (nt, 'duration', str (dvs), lev + 1)   # skip when dvs == 0, requirement of musicXML
        addElemT (nt, 'voice', '1', lev + 1)    # default voice, for merging later
        addElemT (nt, 'type', xmltype, lev + 1) # add note type
        if s.ntup >= 0:             # add time modification element for tuplet notes
            tmod = mkTmod (s.tmnum, s.tmden, lev + 1)
            addElem (nt, tmod, lev + 1)
        for i in range (ndot):      # add dots
            dot = E.Element ('dot')
            addElem (nt, dot, lev + 1)
        s.doBeams (n, nt, den, lev + 1)
        s.doNotations (n, (step, oct), alter, nt, lev + 1)
        if n.objs: s.doLyr (n, nt, lev + 1)
        return nt

    def doNotations (s, n, ptup, alter, nt, lev): # note, abc-pitch tupple, alteration, note-element, xml-level
        tstop = ptup in s.ties  # is there an open tie on this pitch tuple
        tstart = getattr (n, 'tie', 0)  # start a new tie
        decos = s.nextdecos     # decorations encountered so far
        ndeco = getattr (n, 'deco', 0)  # possible decorations of notes of a chord
        if ndeco: decos += ndeco.t
        s.nextdecos = []
        slurs = getattr (n, 'slurs', 0) # slur ends
        if not (tstop or tstart or decos or slurs or s.slurbeg): return nt
        nots = E.Element ('notations')  # notation element needed
        if tstop:               # stop tie
            del s.ties[ptup]    # remove flag
            tie = E.Element ('tied', type='stop')
            addElem (nots, tie, lev + 1)
        if tstart:              # start a tie
            s.ties[ptup] = alter    # remember pitch tuple to stop tie and apply same alteration
            tie = E.Element ('tied', type='start')
            addElem (nots, tie, lev + 1)
        if decos:               # look for slurs and decorations
            arts = []           # collect articulations
            for d in decos:     # do all slurs and decos
                d = s.usrSyms.get (d, d)    # try to replace user defined symbol
                if d == '(': s.slurbeg += 1; continue # slurs made in while loop at the end
                elif d == 'fermata' or d == 'H':
                    ntn = E.Element ('fermata', type='upright')
                elif d == 'arpeggio':
                    ntn = E.Element ('arpeggiate', number='1')
                else: arts.append (d); continue
                addElem (nots, ntn, lev + 1)
            if arts:        # do only note articulations and collect staff annotations in xmldecos
                rest = s.doArticulations (nots, arts, lev + 1)
                if rest: info ('unhandled note decorations: %s' % rest)
        while s.slurbeg > 0:
            s.slurbeg -= 1
            slurnum = len (s.slurstack) + 1
            s.slurstack.append (slurnum)
            ntn = E.Element ('slur', number='%d' % slurnum, type='start')
            addElem (nots, ntn, lev + 1)            
        if slurs:           # these are only slur endings
            for d in slurs.t:
                slurnum = s.slurstack.pop ()
                slur = E.Element ('slur', number='%d' % slurnum, type='stop')
                addElem (nots, slur, lev + 1)
        if nots.getchildren() != []:    # only add notations of not empty
            addElem (nt, nots, lev)

    def doArticulations (s, nots, arts, lev):
        decos = []
        for a in arts:
            if a in s.artMap:
                art = E.Element ('articulations')
                addElem (nots, art, lev)
                addElem (art, E.Element (s.artMap[a]), lev + 1)
            elif a in s.ornMap:
                orn = E.Element ('ornaments')
                addElem (nots, orn, lev)
                addElem (orn, E.Element (s.ornMap[a]), lev + 1)
            elif a in s.tecMap:
                tec = E.Element ('technical')
                addElem (nots, tec, lev)
                addElem (tec, E.Element (s.tecMap[a]), lev + 1)
            else: decos.append (a)  # return staff annotations
        return decos

    def doLyr (s, n, nt, lev):
        for i, lyrobj in enumerate (n.objs):
            if lyrobj.name != 'syl': continue
            dash = len (lyrobj.t) == 2
            if dash:
                if i in s.lyrdash:  type = 'middle'
                else:               type = 'begin'; s.lyrdash [i] = 1
            else:
                if i in s.lyrdash:  type = 'end';   del s.lyrdash [i]
                else:               type = 'single'
            lyrel = E.Element ('lyric', number = str (i + 1))
            addElem (nt, lyrel, lev)
            addElemT (lyrel, 'syllabic', type, lev + 1)
            addElemT (lyrel, 'text', lyrobj.t[0], lev + 1)

    def doBeams (s, n, nt, den, lev):
        if hasattr (n, 'chord') or hasattr (n, 'grace'):
            s.grcbbrk = s.grcbbrk or n.bbrk.t[0]    # remember if there was any bbrk in or before a grace sequence
            return
        bbrk = s.grcbbrk or n.bbrk.t[0] or den < 32
        s.grcbbrk = False
        if not s.prevNote:  pbm = None
        else:               pbm = s.prevNote.find ('beam')
        bm = E.Element ('beam', number='1')
        bm.text = 'begin'
        if pbm != None:
            if bbrk:
                if pbm.text == 'begin':
                    s.prevNote.remove (pbm)
                elif pbm.text == 'continue':
                    pbm.text = 'end'
            else: bm.text = 'continue'
        if den >= 32: addElem (nt, bm, lev)
        s.prevNote = nt

    def stopBeams (s):
        if not s.prevNote: return
        pbm = s.prevNote.find ('beam')
        if pbm != None:
            if pbm.text == 'begin':
                s.prevNote.remove (pbm)
            elif pbm.text == 'continue':
                pbm.text = 'end'
        s.prevNote = None

    def staffDecos (s, decos, maat, lev, bardecos=0):
        for d in decos:
            d = s.usrSyms.get (d, d)    # try to replace user defined symbol
            if d in s.dynaMap:
                dynel = E.Element ('dynamics')
                addDirection (maat, dynel, lev, E.Element (d))
            elif d in s.wedgeMap:  # wedge
                if ')' in d: type = 'stop'
                else: type = 'crescendo' if '<' in d else 'diminuendo'
                addDirection (maat, E.Element ('wedge', type=type), lev)
            elif d in ['coda', 'segno']:
                if bardecos: s.bardecos.append (d)  # postpone to begin next measure
                else:
                    text, attr, val = s.capoMap [d]
                    dir = addDirection (maat, E.Element (text), lev, placement='above')
                    sound = E.Element ('sound'); sound.set (attr, val)
                    addElem (dir, sound, lev + 1)
            elif d in s.capoMap:
                text, attr, val = s.capoMap [d]
                words = E.Element ('words'); words.text = text
                dir = addDirection (maat, words, lev, placement='above')
                sound = E.Element ('sound'); sound.set (attr, val)
                addElem (dir, sound, lev + 1)
            elif d == '(': s.slurbeg += 1   # start slur on next note
            else: s.nextdecos.append (d)    # keep annotation for the next note

    def doFields (s, maat, fieldmap, lev):
        def doClef ():
            clef = re.search (r'alto1|alto2|alto|tenor|bass3|bass|treble|perc|none', field)
            if clef:
                sign, line = s.clefMap [clef.group ()]
                if not sign: return
                c = E.Element ('clef')
                addElemT (c, 'sign', sign, lev + 2)
                if line: addElemT (c, 'line', line, lev + 2)
                atts.append ((4, c))

        atts = []               # collect xml attribute elements [(order-number, xml-element), ..]
        for ftype, field in fieldmap.items ():
            if not field:       # skip empty fields
                continue
            if ftype == 'Div':  # not an abc field, but handled as if
                d = E.Element ('divisions')
                d.text = field
                atts.append ((1, d))
            elif ftype == 'M':
                if field == 'none': continue
                if field == 'C': field = '4/4'
                elif field == 'C|': field = '2/2'
                t = E.Element ('time')
                beats, btype = field.split ('/')
                addElemT (t, 'beats', beats, lev + 2)
                addElemT (t, 'beat-type', btype, lev + 2)
                atts.append ((3, t))
            elif ftype == 'K':
                accs = ['F','C','G','D','A','E','B']    # == s.sharpness [6:13]
                key = re.search (r'([CDEFGAB][#b]?)(m?)', field)
                if key:
                    key, mode = key.groups ()
                    offset = 10 if mode else 7
                    fifths = s.sharpness.index (key) - offset
                    if fifths >= 0: s.keyAlts = dict (zip (accs[:fifths], fifths * ['1']))
                    else:           s.keyAlts = dict (zip (accs[fifths:], -fifths * ['-1']))
                    k = E.Element ('key')
                    addElemT (k, 'fifths', str (fifths), lev + 2)
                    addElemT (k, 'mode', 'major' if offset == 7 else 'minor', lev + 2)
                    atts.append ((2, k))                    
                doClef ()
            elif ftype == 'L':
                s.unitLcur = map (int, field.split ('/'))
            elif ftype == 'V':
                doClef ()
            else:
                info ('unhandled field: %s, content: %s' % (ftype, field))

        if atts:
            att = E.Element ('attributes')      # insert sub elements in the order required by musicXML
            addElem (maat, att, lev)
            for _, att_elem in sorted (atts):   # ordering !
                addElem (att, att_elem, lev + 1)

    def mkBarline (s, maat, loc, lev, style='', dir='', ending=''):
        b = E.Element ('barline', location=loc)
        if style:
            addElemT (b, 'bar-style', style, lev + 1)
        if s.curVolta:    # first stop a current volta
            end = E.Element ('ending', number=s.curVolta, type='stop')
            addElem (b, end, lev + 1)
            s.curVolta = ''
        if dir:
            r = E.Element ('repeat', direction=dir)
            addElem (b, r, lev + 1)
        if ending:
            ending = ending.replace ('-',',')   # MusicXML only accepts comma's
            end = E.Element ('ending', number=ending, type='start')
            addElem (b, end, lev + 1)
            s.curVolta = ending
        addElem (maat, b, lev)

    def doChordSym (s, maat, sym, lev):
        alterMap = {'#':'1','=':'0','b':'-1'}
        rnt = sym.root.t
        chord = E.Element ('harmony')
        addElem (maat, chord, lev)
        root = E.Element ('root')
        addElem (chord, root, lev + 1)
        addElemT (root, 'root-step', rnt[0], lev + 2)
        if len (rnt) == 2: addElemT (root, 'root-alter', alterMap [rnt[1]], lev + 2)
        kind = s.chordTab.get (sym.kind.t[0], 'major')
        addElemT (chord, 'kind', kind, lev + 1)
        degs = getattr (sym, 'degree', '')
        if degs:
            if type (degs) != types.ListType: degs = [degs]
            for deg in degs:
                deg = deg.t[0]
                if deg[0] == '#':   alter = '1';  deg = deg[1:]
                elif deg[0] == 'b': alter = '-1'; deg = deg[1:]
                else:               alter = '0';  deg = deg
                degree = E.Element ('degree')
                addElem (chord, degree, lev + 1)
                addElemT (degree, 'degree-value', deg, lev + 2)
                addElemT (degree, 'degree-alter', alter, lev + 2)
                addElemT (degree, 'degree-type', 'add', lev + 2)

    def mkMeasure (s, i, t, lev, fieldmap={}):
        s.msreAlts = {}
        s.ntup = -1
        overlay = 0
        maat = E.Element ('measure', number = str(i))
        if fieldmap: s.doFields (maat, fieldmap, lev + 1)
        if s.linebrk:   # there was a line break in the previous measure
            e = E.Element ('print')
            e.set ('new-system', 'yes')
            addElem (maat, e, lev + 1)
            s.linebrk = 0
        if s.bardecos:  # output coda and segno attached to the previous right barline
            s.staffDecos (s.bardecos, maat, lev + 1)
            s.bardecos = []
        for it, x in enumerate (t):
            if x.name == 'note' or x.name == 'rest':
                note = s.mkNote (x, lev + 1)
                addElem (maat, note, lev + 1)
            elif x.name == 'lbar':
                bar = x.t[0]
                if bar == '|': pass # skip redundant bar
                elif ':' in bar:    # forward repeat
                    volta = x.t[1] if len (x.t) == 2  else ''
                    s.mkBarline (maat, 'left', lev + 1, style='heavy-light', dir='forward', ending=volta)
                else:               # bar must be a volta number
                    s.mkBarline (maat, 'left', lev + 1, ending=bar)
            elif x.name == 'rbar':
                if hasattr (x, 'deco'): # MuseScore does not support this -> emergency solution
                    s.staffDecos (x.deco.t, maat, lev + 1, bardecos=1)  # coda, segno -> next measure
                bar = x.t[0]
                if ':' in bar:  # backward repeat
                    s.mkBarline (maat, 'right', lev + 1, style='light-heavy', dir='backward')
                elif bar == '||':
                    s.mkBarline (maat, 'right', lev + 1, style='light-light')
                elif '[' in bar or ']' in bar:
                    s.mkBarline (maat, 'right', lev + 1, style='light-heavy')
                elif bar[0] == '&': overlay = 1
            elif x.name == 'tup':
                if len (x.t) == 3:
                    s.tmnum, s.tmden, s.ntup = x.t
                else:
                    s.tmnum, s.tmden, s.ntup = x.t[0], 2, x.t[0]
            elif x.name == 'deco':
                s.staffDecos (x.t, maat, lev + 1)   # output staff decos, postpone note decos to next note
            elif x.name == 'text':
                pos, text = x.t[:2]
                place = 'above' if pos == '^' else 'below'
                words = E.Element ('words')
                words.text = text
                addDirection (maat, words, lev + 1, placement=place)
            elif x.name == 'inline':
                fieldtype, fieldval = x.t[:2]
                s.doFields (maat, {fieldtype:fieldval}, lev + 1)
            elif x.name == 'grace':
                if type (x.note) != types.ListType: x.note = [x.note]
                for i, nt in enumerate (x.note):
                    nt.grace = 1    # set grace attribute
                    note = s.mkNote (nt, lev + 1)    # forget decos
                    if i == 0 and getattr (x, 'accia', ''):
                        note.find ('grace').set ('slash', 'yes')
                    addElem (maat, note, lev + 1)
            elif x.name == 'linebrk':
                if it > 0 and t[it -1].name == 'lbar':  # we are at start of measure
                    e = E.Element ('print')             # output linebreak now
                    e.set ('new-system', 'yes')
                    addElem (maat, e, lev + 1)
                else:
                    s.linebrk = 1   # output linebreak at start of next measure
            elif x.name == 'chordsym':
                s.doChordSym (maat, x, lev + 1)
        s.stopBeams ()
        return maat, overlay

    def mkPart (s, maten, id, lev, attrs):
        s.slurstack = []
        s.unitLcur = s.unitL    # set the default unit length at begin of each voice
        s.curVolta = ''
        s.lyrdash = {}
        s.linebrk = 0
        part = E.Element ('part', id=id)
        msre, overlay = s.mkMeasure (1, maten[0], lev + 1, attrs)
        addElem (part, msre, lev + 1)
        for i, maat in enumerate (maten[1:]):
            msre, next_overlay = s.mkMeasure (i+2, maat, lev + 1)
            if overlay: mergePartMeasure (part, msre)
            else:       addElem (part, msre, lev + 1)
            overlay = next_overlay
        return part

    def mkScorePart (s, id, naam, lev):
        sp = E.Element ('score-part', id=id)
        nm = E.Element ('part-name')
        nm.text = naam
        addElem (sp, nm, lev + 1)
        return sp

    def mkPartlist (s, xs, lev):
        partlist = E.Element ('part-list')
        for id, naam in xs:
            sp = s.mkScorePart (id, naam, lev + 1)
            addElem (partlist, sp, lev + 1)
        return partlist

    def doHeaderField (s, fld, attrmap):
        type, value = fld.t[:2]
        if not value:    # skip empty field
            return
        if type == 'M':
            attrmap [type] = value
        elif type == 'L':
            s.unitL = map (int, fld.t[1].split ('/'))
        elif type == 'K':
            attrmap[type] = value
        elif type == 'T':
            if s.title: s.title = s.title + '\n' + value
            else:       s.title = value
        elif type == 'C':
            s.creator ['composer'] = s.creator.get ('composer', '') + value
        elif type == 'Z':
            s.creator ['lyricist'] = s.creator.get ('lyricist', '') + value
        elif type == 'U':
            sym = fld.t[2].strip ('!+')
            s.usrSyms [value] = sym
        else:
            info ('skipped header: %s' % fld)

    def parse (s, abctext):
        s.reset ()
        header, voices, staves = splitHeaderVoices (abctext)    # staves = [[voice names to be merged into one stave]]
        ps = []
        try:
            hs = abc_header.parseString (header)
            for id, vce_lyr in voices:  # vce_lyr = [voice-block] where voice-block = (measures, corresponding lyric lines)
                vcelyr = []             # list of measures where measure = list of elements (see syntax)
                prevLeftBar = None      # previous voice ended with a left-bar symbol (double repeat)
                for voice, lyr in vce_lyr:
                    vce = abc_voice.parseString (voice).asList ()
                    if prevLeftBar:
                        vce[0].insert (0, prevLeftBar)  # insert at begin of first measure
                        prevLeftBar = None
                    if vce[-1][-1].name == 'lbar':      # last measure ends with an lbar
                        prevLeftBar = vce[-1][-1]
                        del vce[-1]     # lbar was the only element in measure vce[-1]
                    lyr = lyr.strip ()  # strip leading \n (because we split on '\nw:...')
                    if lyr:             # no lyrics for this measures-lyrics block
                        lyr = lyr_block.parseString (lyr).asList ()
                        xs = alignLyr (vce, lyr)    # put all syllables into corresponding notes
                    else: xs = vce
                    vcelyr += xs
                elem1 = vcelyr [0][0]   # the first element of the first measure
                if  elem1.name == 'inline'and elem1.t[0] == 'V':    # is a voice definition
                    voicedef = elem1 
                    del vcelyr [0][0]   # do not read voicedef twice
                else:
                    voicedef = ''
                ps.append ((id, voicedef, vcelyr))
        except ParseException, err:
            xs = err.line[err.col-1:err.col+2]
            info (err.line.encode ('latin-1'), warn=0)  # err.line is a unicode string!!
            info ((err.col-1) * '-' + '^', warn=0)
            if re.match (r'\[[OAPZNGHRBDFSXTCIU]:', xs):
                info ('Error: header-only field %s appears after K:' % xs[1:], warn=0)
            else:
                info (str (err), warn=0)
            raise err

        s.unitL = (1, 8)
        s.title = ''
        s.creator = {}  # {creator type -> name string}
        score = E.Element ('score-partwise')
        attrmap = {'Div': str (s.divisions), 'K':'C treble', 'M':'4/4'}
        for res in hs:
            if res.name == 'field':
                s.doHeaderField (res, attrmap)
            else:
                info ('unexpected header item: %s' % res)

        lev = 0
        parts, partlist = [], []
        for vid, vcedef, vce in ps: # vcedef == first voice inline field
            pname = vid             # partname = voice ID
            if not vcedef:          # simple abc without voice definitions
                attrmap ['V'] = ''
            else:                   # abc with voice definitions
                if vid != vcedef.t[1]: info ('voice ids unequal: %s (reg-ex) != %s (grammar)' % (vid, vcedef.t[1]))
                rn = re.search (r'na?me?="([^"]*)"', vcedef.t[2])
                if rn: pname = rn.group (1)
                attrmap ['V'] = vcedef.t[2]
            pid = 'P%s' % vid       # let part id start with an alpha
            part = s.mkPart (vce, pid, lev + 1, attrmap)
            parts.append (part)
            partlist.append ((pid, pname))
        parts, partlist = mergeParts (parts, partlist, staves)  # merge parts into staves as indicated by %%score
        if s.title:
            addElemT (score, 'movement-title', s.title, lev + 1)

        ident = E.Element ('identification')
        addElem (score, ident, lev + 1)
        if s.creator:
            for ctype, cname in s.creator.items ():
                c = E.Element ('creator', type=ctype)
                c.text = cname
                addElem (ident, c, lev + 2)
        encoding = E.Element ('encoding')
        addElem (ident, encoding, lev + 2)
        software = E.Element ('software')
        software.text = 'abc2xml version %d, http://wim.vree.org/svgParse/abc2xml.html' % VERSION
        addElem (encoding, software, lev + 3)
        encodingDate = E.Element ('encoding-date')
        encodingDate.text = str (datetime.date.today ())
        addElem (encoding, encodingDate, lev + 3)

        partlist = s.mkPartlist (partlist, lev + 1)
        addElem (score, partlist, lev + 1)
        for part in parts:
            addElem (score, part, lev + 1)

        return score

def fixDoctype (elem, enc):
    xs = E.tostring (elem, encoding=enc)
    ys = xs.split ('\n')
    if enc == 'utf-8': ys.insert (0, "<?xml version='1.0' encoding='utf-8'?>")  # crooked logic of ElementTree lib
    ys.insert (1, '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 3.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">')
    return '\n'.join (ys)

def convert (pad, fnm, abctext):
    # these globals should be initialised (as in the __main__ secion) before calling convert
    global mxm                              # optimisation 1: keep instance of MusicXml
    global abc_header, abc_voice, lyr_block # optimisation 2: keep computed grammars
    score = mxm.parse (abctext)
    if pad:
        outfile = file (os.path.join (pad, fnm + '.xml'), 'wb')
        outfile.write (fixDoctype (score, 'utf-8'))
        outfile.close ()
    else:
        outfile = sys.stdout
        outfile.write (fixDoctype (score, 'latin-1'))
        outfile.write ('\n')
    info ('%s.xml written' % fnm, warn=0)
    
#----------------
# Main Program
#----------------
if __name__ == '__main__':
    from optparse import OptionParser
    from glob import glob
    import time
    global abc_header, abc_voice, lyr_block # keep computed grammars
    mxm = MusicXml ()

    parser = OptionParser (usage='%prog [-h] [-o DIR] <file1> [<file2> ...]', version='version %d' % VERSION)
    parser.add_option ("-o", action="store", help="store xml files in DIR", default='', metavar='DIR')
    options, args = parser.parse_args ()
    if len (args) == 0: parser.error ('no input file given')
    pad = options.o
    if pad:
        if not os.path.exists (pad): os.mkdir (pad)
        if not os.path.isdir (pad): parser.error ('%s is not a directory' % pad)

    abc_header, abc_voice, lyr_block = abc_grammar ()  # compute grammar only once per file set
    fnmext_list = []
    for i in args: fnmext_list += glob (i)
    if not fnmext_list: parser.error ('none of the input files exist')
    t_start = time.time ()
    for X, fnmext in enumerate (fnmext_list):
        fnm, ext = os.path.splitext (fnmext)
        if ext.lower () not in ('.abc'):
            info ('skipped input file %s, it should have extension .abc' % fnmext)
            continue
        if os.path.isdir (fnmext):
            info ('skipped directory %s. Only files are accepted' % fnmext)
            continue

        fobj = open (fnmext, 'rb')
        encoded_data = fobj.read ()
        fobj.close ()
        try:     enc = 'utf-8';   abctext = encoded_data.decode (enc)
        except:
            try: enc = 'latin-1'; abctext = encoded_data.decode (enc)
            except:
                info ('skipped file %s, because it is not encoded in utf-8 nor in latin-1')
                continue            
        info ('decoded %s from %s' % (fnmext, enc))
        try:
            convert (pad, fnm, abctext)     # convert string abctext -> file pad/fnm.xml
        except ParseException, err: pass    # output already printed
        except Exception, err: info ('an exception occurred.\n%s' % err)
    info ('done in %.2f secs' % (time.time () - t_start))
