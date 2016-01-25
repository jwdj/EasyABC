#!/usr/bin/env python
# coding=latin-1
'''
Copyright (C) 2012: W.G. Vree
Contributions: M. Tarenskeen, N. Liberg, Paul Villiger

This program is free software; you can redistribute it and/or modify it under the terms of the
GNU General Public License as published by the Free Software Foundation; either version 2 of
the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details. <http://www.gnu.org/licenses/gpl.html>.
'''

try:    import xml.etree.cElementTree as E
except: import xml.etree.ElementTree as E
import os, sys, types, re

VERSION = 60

python3 = sys.version_info.major > 2
if python3:
    tupletype = tuple
    max_int = sys.maxsize
else:
    tupletype = types.TupleType
    max_int = sys.maxint

note_ornamentation_map = {        # for notations/, modified from EasyABC
    'ornaments/trill-mark':       'T',
    'ornaments/mordent':          'M',
    'ornaments/inverted-mordent': 'P',
    'ornaments/turn':             '!turn!',
    'ornaments/inverted-turn':    '!invertedturn!',
    'ornaments/tremolo':          '!///!',
    'technical/up-bow':           'u',
    'technical/down-bow':         'v',
    'technical/harmonic':         '!open!',
    'technical/open-string':      '!open!',
    'technical/stopped':          '!plus!',
    'articulations/accent':       '!>!',
    'articulations/strong-accent':'!>!',    # compromise
    'articulations/staccato':     '.',
    'articulations/staccatissimo':'!wedge!',
    'fermata':                    '!fermata!',
    'arpeggiate':                 '!arpeggio!',
    'articulations/tenuto':       '!tenuto!',
    'articulations/staccatissimo':'!wedge!', # not sure whether this is the right translation
    'articulations/spiccato':     '!wedge!', # not sure whether this is the right translation
    'articulations/breath-mark':  '!breath!', # this may need to be tested to make sure it appears on the right side of the note
    'articulations/detached-legato': '!tenuto!.',
}

dynamics_map = {    # for direction/direction-type/dynamics/
    'p':    '!p!',
    'pp':   '!pp!',
    'ppp':  '!ppp!',
    'f':    '!f!',
    'ff':   '!ff!',
    'fff':  '!fff!',
    'mp':   '!mp!',
    'mf':   '!mf!',
    'sfz':  '!sfz!',
}

def info (s, warn=1): sys.stderr.write ((warn and '-- ' or '') + s + '\n')

#-------------------
# data abstractions
#-------------------
class Measure:
    def __init__ (s, p):
        s.reset ()
        s.ixp = p       # part number  
        s.ixm = 0       # measure number
        s.mdur = 0      # measure duration (nominal metre value in divisions)
        s.divs = 0      # number of divisions per 1/4

    def reset (s):      # reset each measure
        s.attr = ''     # measure signatures, tempo
        s.lline = ''    # left barline, but only holds ':' at start of repeat, otherwise empty
        s.rline = '|'   # right barline
        s.lnum = ''     # (left) volta number

class Note:
    def __init__ (s, dur=0, n=None):
        s.tijd = 0      # the time in XML division units
        s.dur = dur     # duration of a note in XML divisions
        s.fact = None   # time modification for tuplet notes (num, div)
        s.tup = ['']    # start(s) and/or stop(s) of tuplet
        s.tupabc = ''   # abc tuplet string to issue before note
        s.beam = 0      # 1 = beamed
        s.grace = 0     # 1 = grace note
        s.before = ''   # extra abc string that goes before the note/chord
        s.after = ''    # the same after the note/chord
        s.ns = n and [n] or []  # notes in the chord
        s.lyrs = {}     # {number -> syllabe}

class Elem:
    def __init__ (s, string):
        s.tijd = 0      # the time in XML division units
        s.str = string  # any abc string that is not a note

class Counter:
    def inc (s, key, voice): s.counters [key][voice] = s.counters [key].get (voice, 0) + 1
    def clear (s, vnums):  # reset all counters
        tups = list( zip (vnums.keys (), len (vnums) * [0]))
        s.counters = {'note': dict (tups), 'nopr': dict (tups), 'nopt': dict (tups)}
    def getv (s, key, voice): return s.counters[key][voice]
    def prcnt (s, ip):  # print summary of all non zero counters
        for iv in s.counters ['note']:
            if s.getv ('nopr', iv) != 0:
                info ( 'part %d, voice %d has %d skipped non printable notes' % (ip, iv, s.getv ('nopr', iv)))
            if s.getv ('nopt', iv) != 0:
                info ( 'part %d, voice %d has %d notes without pitch' % (ip, iv, s.getv ('nopt', iv)))
            if s.getv ('note', iv) == 0: # no real notes counted in this voice
                info ( 'part %d, skipped empty voice %d' % (ip, iv))

class Music:
    def __init__(s, options):
        s.tijd = 0              # the current time
        s.maxtime = 0           # maximum time in a measure
        s.gMaten = []           # [voices,.. for all measures in a part]
        s.gLyrics = []          # [{num: (abc_lyric_string, melis)},.. for all measures in a part]
        s.vnums = {}            # all used voice id's in a part
        s.cnt = Counter ()      # global counter object
        s.vceCnt = 1            # the global voice count over all parts
        s.lastnote = None       # the last real note record inserted in s.voices
        s.bpl = options.b       # the max number of bars per line when writing abc
        s.cpl = options.n       # the number of chars per line when writing abc
        s.repbra = 0            # true if volta is used somewhere
        s.nvlt = options.v      # no volta on higher voice numbers
        s.jscript = options.j   # compatibility with javascript version

    def initVoices (s, newPart=0):
        s.vtimes, s.voices, s.lyrics = {}, {}, {}
        for v in s.vnums:
            s.vtimes [v] = 0    # {voice: the end time of the last item in each voice}
            s.voices [v] = []   # {voice: [Note|Elem, ..]}
            s.lyrics [v] = []   # {voice: [{num: syl}, ..]}
        if newPart: s.cnt.clear (s.vnums)   # clear counters once per part

    def incTime (s, dt):
        s.tijd += dt
        if s.tijd > s.maxtime: s.maxtime = s.tijd

    def appendElemCv (s, voices, elem):
        for v in voices:
            s.appendElem (v, elem) # insert element in all voices

    def insertElem (s, v, elem):    # insert at the start of voice v in the current measure
        obj = Elem (elem)
        obj.tijd = 0        # because voice is sorted later
        s.voices [v].insert (0, obj)

    def appendObj (s, v, obj, dur):
        obj.tijd = s.tijd
        s.voices [v].append (obj)
        s.incTime (dur)
        if s.tijd > s.vtimes[v]: s.vtimes[v] = s.tijd   # don't update for inserted earlier items

    def appendElem (s, v, elem):
        s.appendObj (v, Elem (elem), 0)

    def appendNote (s, v, note, noot):
        note.ns.append (noot)
        s.appendObj (v, note, int (note.dur))
        if noot != 'z':             # real notes and grace notes
            s.lastnote = note       # remember last note for later modifications (chord, grace)
            s.cnt.inc ('note', v)   # count number of real notes in each voice
            if not note.grace:                  # for every real note
                s.lyrics[v].append (note.lyrs)  # even when it has no lyrics

    def getLastRec (s, voice):
        if s.gMaten: return s.gMaten[-1][voice][-1] # the last record in the last measure
        return None                                 # no previous records in the first measure

    def getLastMelis (s, voice, num):   # get melisma of last measure
        if s.gLyrics:
            lyrdict = s.gLyrics[-1][voice]  # the previous lyrics dict in this voice
            if num in lyrdict: return lyrdict[num][1]   # lyrdict = num -> (lyric string, melisma)
        return 0 # no previous lyrics in voice or line number

    def addChord (s, noot):  # careful: we assume that chord notes follow immediately 
        s.lastnote.ns.append (noot)

    def addBar (s, lbrk, m): # linebreak, measure data
        if m.mdur and s.maxtime > m.mdur: info ('measure %d in part %d longer than metre' % (m.ixm+1, m.ixp+1))
        s.tijd = s.maxtime              # the time of the bar lines inserted here
        for v in s.vnums:
            if m.lline or m.lnum:       # if left barline or left volta number
                p = s.getLastRec (v)    # get the previous barline record
                if p:                   # in measure 1 no previous measure is available
                    x = p.str           # p.str is the ABC barline string
                    if m.lline:         # append begin of repeat, m.lline == ':'
                        x = (x + m.lline).replace (':|:','::').replace ('||','|')
                    if s.nvlt == 3:     # add volta number only to lowest voice in part 0 
                        if m.ixp + v == min (s.vnums): x += m.lnum
                    elif m.lnum:        # new behaviour with I:repbra 0
                        x += m.lnum     # add volta number(s) or text to all voices
                        s.repbra = 1    # signal occurrence of a volta
                    p.str = x           # modify previous right barline
                elif m.lline:           # begin of new part and left repeat bar is required
                    s.insertElem (v, '|:')
            if lbrk:
                p = s.getLastRec (v)    # get the previous barline record
                if p: p.str += lbrk     # insert linebreak char after the barlines+volta
            if m.attr:                  # insert signatures at front of buffer
                s.insertElem (v, '%s' % m.attr)
            s.appendElem (v, ' %s' % m.rline)   # insert current barline record at time maxtime
            s.voices[v] = sortMeasure (s.voices[v], m)  # make all times consistent
            lyrs = s.lyrics[v]          # [{number: sylabe}, .. for all notes]
            lyrdict = {}                # {number: (abc_lyric_string, melis)} for this voice
            nums = [num for d in lyrs for num in d.keys ()] # the lyrics numbers in this measure
            maxNums = max (nums + [0])  # the highest lyrics number in this measure
            for i in range (maxNums, 0, -1):
                xs = [syldict.get (i, '') for syldict in lyrs]  # collect the syllabi with number i
                melis = s.getLastMelis (v, i)  # get melisma from last measure
                lyrdict [i] = abcLyr (xs, melis)
            s.lyrics[v] = lyrdict       # {number: (abc_lyric_string, melis)} for this measure
            mkBroken (s.voices[v])
        s.gMaten.append (s.voices)
        s.gLyrics.append (s.lyrics)
        s.tijd = s.maxtime = 0
        s.initVoices ()

    def outVoices (s, divs, ip, isSib): # output all voices of part ip
        vvmap = {}                  # xml voice number -> abc voice number (one part)
        vnum_keys = s.vnums.keys ()
        if s.jscript or isSib: vnum_keys.sort ()
        lvc = min (vnum_keys)       # lowest xml voice number of this part
        for iv in vnum_keys:
            if s.cnt.getv ('note', iv) == 0:    # no real notes counted in this voice
                continue            # skip empty voices
            if abcOut.denL: unitL = abcOut.denL # take the unit length from the -d option
            else:           unitL = compUnitLength (iv, s.gMaten, divs) # compute the best unit length for this voice
            abcOut.cmpL.append (unitL)  # remember for header output
            vn, vl = [], {}         # for voice iv: collect all notes to vn and all lyric lines to vl
            for im in range (len (s.gMaten)):
                measure = s.gMaten [im][iv]
                vn.append (outVoice (measure, divs, im, ip, unitL))
                checkMelismas (s.gLyrics, s.gMaten, im, iv)
                for n, (lyrstr, melis) in s.gLyrics [im][iv].items ():
                    if n in vl:
                        while len (vl[n]) < im: vl[n].append ('') # fill in skipped measures
                        vl[n].append (lyrstr)
                    else:
                        vl[n] = im * [''] + [lyrstr]    # must skip im measures
            for n, lyrs in vl.items (): # fill up possibly empty lyric measures at the end
                mis = len (vn) - len (lyrs)
                lyrs += mis * ['']
            abcOut.add ('V:%d' % s.vceCnt)
            if s.repbra:
                if s.nvlt == 1 and s.vceCnt > 1: abcOut.add ('I:repbra 0')  # only volta on first voice
                if s.nvlt == 2 and iv > lvc:     abcOut.add ('I:repbra 0')  # only volta on first voice of each part
            if   s.cpl > 0:  s.bpl = 0      # option -n (max chars per line) overrules -b (max bars per line)
            elif s.bpl == 0: s.cpl = 100    # the default: 100 chars per line
            bn = 0                  # count bars
            while vn:               # while still measures available
                ib = 1
                chunk = vn [0]
                while ib < len (vn):
                    if s.cpl > 0 and len (chunk) + len (vn [ib]) >= s.cpl: break    # line full (number of chars)
                    if s.bpl > 0 and ib >= s.bpl: break                             # line full (number of bars)
                    chunk += vn [ib]
                    ib += 1
                bn += ib
                abcOut.add (chunk + ' %%%d' % bn)   # line with barnumer
                del vn[:ib]         # chop ib bars
                lyrlines = sorted (vl.items ())     # order the numbered lyric lines for output
                for n, lyrs in lyrlines:
                    abcOut.add ('w: ' + '|'.join (lyrs[:ib]) + '|')
                    del lyrs[:ib]
            vvmap [iv] = s.vceCnt   # xml voice number -> abc voice number
            s.vceCnt += 1           # count voices over all parts
        s.gMaten = []               # reset the follwing instance vars for each part
        s.gLyrics = []
        s.cnt.prcnt (ip+1)          # print summary of skipped items in this part
        return vvmap

class ABCoutput:
    pagekeys = 'scale,pageheight,pagewidth,leftmargin,rightmargin,topmargin,botmargin'.split (',')
    def __init__ (s, fnmext, pad, X, options):
        s.fnmext = fnmext
        s.outlist = []          # list of ABC strings
        s.title = 'T:Title'
        s.key = 'none'
        s.clefs = {}            # clefs for all abc-voices
        s.mtr = 'none'
        s.tempo = 0             # 0 -> no tempo field
        s.pad = pad             # the output path or none
        s.X = X + 1             # the abc tune number
        s.denL = options.d      # denominator of the unit length (L:) from -d option
        s.volpan = int (options.m)  # 0 -> no %%MIDI, 1 -> only program, 2 -> all %%MIDI
        s.cmpL = []             # computed optimal unit length for all voices
        s.jscript = options.j   # compatibility with javascript version
        if pad:
            _, base_name = os.path.split (fnmext)
            s.outfile = open (os.path.join (pad, base_name), 'w') # the ABC output file
        else:   s.outfile = sys.stdout
        if s.jscript: s.X = 1   # always X:1 in javascript version
        s.pageFmt = {}
        for k in s.pagekeys: s.pageFmt [k] = None
        if len (options.p) == 7:
            for k, v in zip (s.pagekeys, options.p):
                try: s.pageFmt [k] = float (v)
                except: info ('illegal float %s for %s', (k, v)); continue

    def add (s, str):
        s.outlist.append (str + '\n')   # collect all ABC output

    def mkHeader (s, stfmap, partlist, midimap): # stfmap = [parts], part = [staves], stave = [voices]
        accVce, accStf, staffs = [], [], stfmap[:]  # staffs is consumed
        for x in partlist:              # collect partnames into accVce and staff groups into accStf
            try: prgroupelem (x, ('', ''), '', stfmap, accVce, accStf)
            except: info ('lousy musicxml: error in part-list')
        staves = ' '.join (accStf)
        clfnms = {}
        for part, (partname, partabbrv) in zip (staffs, accVce):
            if not part: continue       # skip empty part
            firstVoice = part[0][0]     # the first voice number in this part
            nm  = partname.replace ('\n','\\n').replace ('.:','.').strip (':')
            snm = partabbrv.replace ('\n','\\n').replace ('.:','.').strip (':')
            clfnms [firstVoice] = (nm and 'nm="%s"' % nm or '') + (snm and ' snm="%s"' % snm or '')
        hd = ['X:%d\n%s\n' % (s.X, s.title)]
        for i, k in enumerate (s.pagekeys):
            if s.jscript and k in ['pageheight','topmargin', 'botmargin']: continue
            if s.pageFmt [k] != None: hd.append ('%%%%%s %.2f%s\n' % (k, s.pageFmt [k], i > 0 and 'cm' or ''))
        if staves and len (accStf) > 1: hd.append ('%%score ' + staves + '\n')
        tempo = s.tempo and 'Q:1/4=%s\n' % s.tempo or ''    # default no tempo field
        d = {}  # determine the most frequently occurring unit length over all voices
        for x in s.cmpL: d[x] = d.get (x, 0) + 1
        if s.jscript:   defLs = sorted (d.items (), lambda a,b: b[1] - a[1] or a[0] - b[0]) # when tie (1) sort on key (0)
        else:           defLs = sorted (d.items (), lambda a,b: b[1] - a[1])
        defL = s.denL and s.denL or defLs [0][0] # override default unit length with -d option
        hd.append ('L:1/%d\n%sM:%s\n' % (defL, tempo, s.mtr))
        hd.append ('I:linebreak $\nK:%s\n' % s.key)
        for vnum, clef in s.clefs.items ():
            ch, prg, vol, pan = midimap [vnum-1][:4]
            dmap = midimap [vnum - 1][4:]   # map of abc percussion notes to midi notes
            if dmap and 'perc' not in clef: clef = (clef + ' map=perc').strip ();
            hd.append ('V:%d %s %s\n' % (vnum, clef, clfnms.get (vnum, '')))
            if s.volpan > 1:    # option -m 2 -> output all recognized midi commands when needed and present in xml
                if ch > 0 and ch != vnum: hd.append ('%%%%MIDI channel %d\n' % ch)
                if prg > 0:  hd.append ('%%%%MIDI program %d\n' % (prg - 1))
                if vol >= 0: hd.append ('%%%%MIDI control 7 %.0f\n' % vol)  # volume == 0 is possible ...
                if pan >= 0: hd.append ('%%%%MIDI control 10 %.0f\n' % pan)
            elif s.volpan > 0: # default -> only output midi program command when present in xml
                if dmap and ch > 0: hd.append ('%%%%MIDI channel %d\n' % ch) # also channel if percussion part
                if prg > 0:  hd.append ('%%%%MIDI program %d\n' % (prg - 1))
            for abcNote, step, midiNote, notehead in dmap:
                if not notehead: notehead = 'normal'
                if abcMid (abcNote) != midiNote or abcNote != step:
                    if s.volpan > 0: hd.append ('%%%%MIDI drummap %s %s\n' % (abcNote, midiNote))
                    hd.append ('I:percmap %s %s %s %s\n' % (abcNote, step, midiNote, notehead))
            if defL != s.cmpL [vnum-1]: # only if computed unit length different from header
                hd.append ('L:1/%d\n' % s.cmpL [vnum-1])
        s.outlist = hd + s.outlist

    def writeall (s):  # determine the required encoding of the entire ABC output
        str = ''.join (s.outlist)
        if python3: s.outfile.write (str)
        elif s.jscript:
            s.outfile.write (str.encode ('utf-8'))      # always utf-8 in javascript version
        else:
            try:    s.outfile.write (str.encode ('latin-1'))    # prefer latin-1
            except: s.outfile.write (str.encode ('utf-8'))      # fall back to utf if really needed
        if s.pad: s.outfile.close ()                        # close each file with -o option
        else: s.outfile.write ('\n')                        # add empty line between tunes on stdout
        info ('%s written with %d voices' % (s.fnmext, len (s.clefs)), warn=0)

#----------------
# functions
#----------------
def abcLyr (xs, melis): # Convert list xs to abc lyrics.
    if not ''.join (xs): return '', 0  # there is no lyrics in this measure
    res = []
    for x in xs:        # xs has for every note a lyrics syllabe or an empty string
        if x == '':     # note without lyrics
            if melis: x = '_'   # set melisma
            else: x = '*'       # skip note
        elif x.endswith ('_') and not x.endswith ('\_'): # start of new melisma
            x = x.replace ('_', '') # remove and set melis boolean
            melis = 1           # so next skips will become melisma
        else: melis = 0         # melisma stops on first syllable
        res.append (x)
    return (' '.join (res), melis)

def simplify (a, b):    # divide a and b by their greatest common divisor
    x, y = a, b
    while b: a, b = b, a % b
    return x / a, y / a

def abcdur (nx, divs, uL):      # convert an musicXML duration d to abc units with L:1/uL
    if nx.dur == 0: return ''   # when called for elements without duration
    num, den = simplify (uL * nx.dur, divs * 4) # L=1/8 -> uL = 8 units
    if nx.fact:                 # apply tuplet time modification
        numfac, denfac = nx.fact
        num, den = simplify (num * numfac, den * denfac)
    if den > 64:                # limit the denominator to a maximum of 64
        num64 = 64. * num / den
        num, den = simplify (int (round (num64)), 64)
    if num == 1:
        if   den == 1: dabc = ''
        elif den == 2: dabc = '/'
        else:          dabc = '/%d' % den
    elif den == 1:     dabc = '%d' % num
    else:              dabc = '%d/%d' % (num, den)
    return dabc

def abcMid (note):  # abc note -> midi pitch
    r = re.search (r"([_^]*)([A-Ga-g])([',]*)", note)
    if not r: return -1
    acc, n, oct = r.groups ()
    nUp = n.upper ()
    p = 60 + [0,2,4,5,7,9,11]['CDEFGAB'.index (nUp)] + (12 if nUp != n else 0);
    if acc: p += (1 if acc[0] == '^' else -1) * len (acc)
    if oct: p += (12 if oct[0] == "'" else -12) * len (oct)
    return p

def staffStep (ptc, o, clef, tstep):
    ndif = 0
    if 'stafflines=1' in clef: ndif += 4                    # meaning of one line: E (xml) -> B (abc)
    if not tstep and clef.startswith ('bass'): ndif += 12   # transpose bass -> treble (C3 -> A4)
    if ndif:    # diatonic transposition == addition modulo 7
        nm7 = 'C,D,E,F,G,A,B'.split (',')
        n = nm7.index (ptc) + ndif
        ptc, o = nm7 [n % 7], o + n / 7
    if o > 4: ptc = ptc.lower ()
    if o > 5: ptc = ptc + (o-5) * "'"
    if o < 4: ptc = ptc + (4-o) * ","
    return ptc

def setKey (fifths, mode):
    accs = ['F','C','G','D','A','E','B']
    kmaj = ['Cb','Gb','Db','Ab','Eb','Bb','F','C','G','D','A', 'E', 'B', 'F#','C#']
    kmin = ['Ab','Eb','Bb','F', 'C', 'G', 'D','A','E','B','F#','C#','G#','D#','A#']
    key = ''
    if mode == 'major': key = kmaj [7 + fifths]
    if mode == 'minor': key = kmin [7 + fifths] + 'min'
    if fifths >= 0: msralts = dict (zip (accs[:fifths], fifths * [1]))
    else:           msralts = dict (zip (accs[fifths:], -fifths * [-1]))
    return key, msralts

def insTup (ix, notes, fact):   # read one nested tuplet
    tupcnt, halted = 0, 0
    nx = notes [ix]
    if 'start' in nx.tup:
        nx.tup.remove ('start') # do recursive calls when starts remain
    tix = ix                    # index of first tuplet note
    fn, fd = fact               # xml time-mod of the higher level
    fnum, fden = nx.fact        # xml time-mod of the current level
    tupfact = fnum/fn, fden/fd  # abc time mod of this level
    while ix < len (notes):
        nx = notes [ix]
        if isinstance (nx, Elem) or nx.grace:
            ix += 1             # skip all non tuplet elements
            continue
        if 'start' in nx.tup:   # more nested tuplets to start
            ix, tupcntR = insTup (ix, notes, tupfact)   # ix is on the stop note!
            tupcnt += tupcntR
        elif nx.fact:
            tupcnt += 1         # count tuplet elements
        if 'stop' in nx.tup:
            nx.tup.remove ('stop')
            halted = 1
            break
        if not nx.fact:         # stop on first non tuplet note
            ix = lastix         # back to last tuplet note
            halted = 1
            break
        lastix = ix
        ix += 1
    # put abc tuplet notation before the recursive ones
    tup = (tupfact[0], tupfact[1], tupcnt)
    if tup == (3, 2, 3): tupPrefix = '(3'
    else:                tupPrefix = '(%d:%d:%d' % tup
    notes [tix].tupabc = tupPrefix + notes [tix].tupabc
    return ix, tupcnt           # ix is on the last tuplet note

def mkBroken (vs):      # introduce broken rhythms (vs: one voice, one measure)
    vs = [n for n in vs if isinstance (n, Note)]
    i = 0
    while i < len (vs) - 1:
        n1, n2 = vs[i], vs[i+1]     # scan all adjacent pairs
        # skip if note in tuplet or has no duration or outside beam
        if not n1.fact and not n2.fact and n1.dur > 0 and n2.beam:
            if n1.dur * 3 == n2.dur:
                n2.dur = (2 * n2.dur) / 3
                n1.dur = n1.dur * 2
                n1.after = '<' + n1.after
                i += 1              # do not chain broken rhythms
            elif n2.dur * 3 == n1.dur:
                n1.dur = (2 * n1.dur) / 3
                n2.dur = n2.dur * 2
                n1.after = '>' + n1.after
                i += 1              # do not chain broken rhythms
        i += 1

def outVoice (measure, divs, im, ip, unitL):    # note/elem objects of one measure in one voice
    ix = 0
    while ix < len (measure):   # set all (nested) tuplet annotations
        nx = measure [ix]
        if isinstance (nx, Note) and nx.fact:
            ix, tupcnt = insTup (ix, measure, (1, 1))   # read one tuplet, insert annotation(s)
        ix += 1 
    vs = []
    for nx in measure:
        if isinstance (nx, Note):
            durstr = abcdur (nx, divs, unitL)           # xml -> abc duration string
            chord = len (nx.ns) > 1
            cns = [nt[:-1] for nt in nx.ns if nt.endswith ('-')]
            tie = ''
            if chord and len (cns) == len (nx.ns):      # all chord notes tied
                nx.ns = cns     # chord notes without tie
                tie = '-'       # one tie for whole chord
            s = nx.tupabc + nx.before
            if chord: s += '['
            for nt in nx.ns: s += nt
            if chord: s += ']' + tie
            if s.endswith ('-'): s, tie = s[:-1], '-'   # split off tie
            s += durstr + tie   # and put it back again
            s += nx.after
            nospace = nx.beam
        else:
            s = nx.str
            nospace = 1
        if nospace: vs.append (s)
        else: vs.append (' ' + s)
    return (''.join (vs))

def sortMeasure (voice, m):
    voice.sort (key=lambda o: o.tijd)   # sort on time
    time = 0
    v = []
    for nx in voice:    # establish sequentiality
        if nx.tijd > time: v.append (Note (nx.tijd - time, 'x')) # fill hole
        if isinstance (nx, Elem):
            if nx.tijd < time: nx.tijd = time # shift elems without duration to where they fit
            v.append (nx)
            time = nx.tijd
            continue
        if nx.tijd < time:                  # overlapping element
            if nx.ns[0] == 'z': continue    # discard overlapping rest
            if v[-1].tijd <= nx.tijd:       # we can do something
                if v[-1].ns[0] == 'z':      # shorten rest
                    v[-1].dur = nx.tijd - v[-1].tijd
                    if v[-1].dur == 0: del v[-1]        # nothing left
                    info ('overlap in part %d, measure %d: rest shortened' % (m.ixp+1, m.ixm+1))
                else:                       # make a chord of overlap
                    v[-1].ns += nx.ns
                    info ('overlap in part %d, measure %d: added chord' % (m.ixp+1, m.ixm+1))
                    nx.dur = (nx.tijd + nx.dur) - time  # the remains
                    if nx.dur <= 0: continue            # nothing left
                    nx.tijd = time          # append remains
            else:                           # give up
                info ('overlapping notes in one voice! part %d, measure %d, note %s discarded' % (m.ixp+1, m.ixm+1, isinstance (nx, Note) and nx.ns or nx.str))
                continue
        v.append (nx)
        time = nx.tijd + nx.dur
    #   when a measure contains no elements and no forwards -> no incTime -> s.maxtime = 0 -> right barline
    #   is inserted at time == 0 (in addbar) and is only element in the voice when sortMeasure is called
    if time == 0: info ('empty measure in part %d, measure %d, it should contain at least a rest to advance the time!' % (m.ixp+1, m.ixm+1))
    return v

def getPartlist (ps):   # correct part-list (from buggy xml-software)
    xs = [] # the corrected part-list
    e = []  # stack of opened part-groups
    for x in ps.getchildren (): # insert missing stops, delete double starts
        if x.tag ==  'part-group':
            num, type = x.get ('number'), x.get ('type')
            if type == 'start':
                if num in e:    # missing stop: insert one
                    xs.append (E.Element ('part-group', number = num, type = 'stop'))
                    xs.append (x)
                else:           # normal start
                    xs.append (x)
                    e.append (num)
            else:
                if num in e:    # normal stop
                    e.remove (num)
                    xs.append (x)
                else: pass      # double stop: skip it
        else: xs.append (x)
    for num in reversed (e):    # fill missing stops at the end
        xs.append (E.Element ('part-group', number = num, type = 'stop'))
    return xs

def parseParts (xs, d, e):  # -> [elems on current level], rest of xs
    if not xs: return [],[]
    x = xs.pop (0)
    if x.tag == 'part-group':
        num, type = x.get ('number'), x.get ('type')
        if type == 'start': # go one level deeper
            s = [x.findtext (n, '') for n in ['group-symbol','group-barline','group-name','group-abbreviation']]
            d [num] = s     # remember groupdata by group number
            e.append (num)  # make stack of open group numbers
            elemsnext, rest1 = parseParts (xs, d, e) # parse one level deeper to next stop
            elems, rest2 = parseParts (rest1, d, e)  # parse the rest on this level
            return [elemsnext] + elems, rest2
        else:               # stop: close level and return group-data
            nums = e.pop () # last open group number in stack order
            if xs and xs[0].get ('type') == 'stop':     # two consequetive stops
                if num != nums:                         # in the wrong order (tempory solution)
                    d[nums], d[num] = d[num], d[nums]   # exchange values    (only works for two stops!!!)
            sym = d[num]    # retrieve an return groupdata as last element of the group
            return [sym], xs
    else:
        elems, rest = parseParts (xs, d, e) # parse remaining elements on current level
        name = x.findtext ('part-name',''), x.findtext ('part-abbreviation','')
        return [name] + elems, rest

def bracePart (part):       # put a brace on multistaff part and group voices
    if not part: return []  # empty part in the score
    brace = []
    for ivs in part:
        if len (ivs) == 1:  # stave with one voice
            brace.append ('%s' % ivs[0])
        else:               # stave with multiple voices
            brace += ['('] + ['%s' % iv for iv in ivs] + [')']
        brace.append ('|')
    del brace[-1]           # no barline at the end
    if len (part) > 1:
        brace = ['{'] + brace + ['}']
    return brace

def prgroupelem (x, gnm, bar, pmap, accVce, accStf):    # collect partnames (accVce) and %%score map (accStf)
    if type (x) == tupletype:   # partname-tuple = (part-name, part-abbrev)
        y = pmap.pop (0)
        if gnm[0]: x = [n1 + ':' + n2 for n1, n2 in zip (gnm, x)]   # put group-name before part-name
        accVce.append (x)
        accStf.extend (bracePart (y))
    elif len (x) == 2:      # misuse of group just to add extra name to stave
        y = pmap.pop (0)
        nms = [n1 + ':' + n2 for n1, n2 in zip (x[0], x[1][2:])]    # x[0] = partname-tuple, x[1][2:] = groupname-tuple
        accVce.append (nms)
        accStf.extend (bracePart (y))
    else:
        prgrouplist (x, bar, pmap, accVce, accStf)

def prgrouplist (x, pbar, pmap, accVce, accStf):    # collect partnames, scoremap for a part-group
    sym, bar, gnm, gabbr = x[-1]    # bracket symbol, continue barline, group-name-tuple
    bar = bar == 'yes' or pbar      # pbar -> the parent has bar
    accStf.append (sym == 'brace' and '{' or '[')
    for z in x[:-1]:
        prgroupelem (z, (gnm, gabbr), bar, pmap, accVce, accStf)
        if bar: accStf.append ('|')
    if bar: del accStf [-1]         # remove last one before close
    accStf.append (sym == 'brace' and '}' or ']')

def compUnitLength (iv, maten, divs):   # compute optimal unit length
    uLmin, minLen = 0, max_int
    for uL in [4,8,16]:     # try 1/4, 1/8 and 1/16
        vLen = 0            # total length of abc duration strings in this voice
        for m in maten:     # all measures
            for e in m[iv]: # all notes in voice iv
                if isinstance (e, Elem) or e.dur == 0: continue # no real durations
                vLen += len (abcdur (e, divs, uL))  # add len of duration string
        if vLen < minLen: uLmin, minLen = uL, vLen  # remember the smallest
    return uLmin

def doSyllable (syl):
    txt = ''
    for e in syl:
        if   e.tag == 'elision': txt += '~'
        elif e.tag == 'text':   # escape - and space characters
            txt += (e.text or '').replace ('_','\_').replace('-', r'\-').replace(' ', '~')
    if not txt: return txt
    if syl.findtext('syllabic') in ['begin', 'middle']: txt += '-'
    if syl.find('extend') is not None:                  txt += '_'
    return txt

def checkMelismas (lyrics, maten, im, iv):
    if im == 0: return
    maat = maten [im][iv]               # notes of the current measure
    curlyr = lyrics [im][iv]            # lyrics dict of current measure
    prvlyr = lyrics [im-1][iv]          # lyrics dict of previous measure
    for n, (lyrstr, melis) in prvlyr.items ():  # all lyric numbers in the previous measure
        if n not in curlyr and melis:   # melisma required, but no lyrics present -> make one!
            ms = getMelisma (maat)      # get a melisma for the current measure
            if ms: curlyr [n] = (ms, 0) # set melisma as the n-th lyrics of the current measure

def getMelisma (maat):                  # get melisma from notes in maat
    ms = []
    for note in maat:                   # every note should get an underscore
        if not isinstance (note, Note): continue    # skip Elem's
        if note.grace: continue         # skip grace notes
        if note.ns [0] == 'z': break    # stop on first rest
        ms.append ('_')
    return ' '.join (ms)

#----------------
# parser
#----------------
class Parser:
    def __init__ (s, options):
        # unfold repeats, number of chars per line, credit filter level, volta option
        s.slurBuf = {}    # dict of open slurs keyed by slur number
        s.wedge_type = '' # remembers the type of the last open wedge (for proper closing)
        s.ingrace = 0     # marks a sequence of grace notes
        s.msc = Music (options)  # global music data abstraction
        s.unfold = options.u    # turn unfolding repeats on
        s.ctf = options.c       # credit text filter level
        s.gStfMap = []    # [[abc voice numbers] for all parts]
        s.midiMap = []    # midi-settings for each abc voice, in order
        s.drumInst = {}   # inst_id -> midi pitch for channel 10 notes
        s.drumNotes = {}  # (xml voice, abc note) -> (midi note, note head)
        s.instMid = []    # [{inst id -> midi-settings} for all parts]
        s.midDflt = [-1,-1,-1,-91] # default midi settings for channel, program, volume, panning
        s.msralts = {}    # xml-notenames (without octave) with accidentals from the key
        s.curalts = {}    # abc-notenames (with voice number) with passing accidentals
        s.stfMap = {}     # xml staff number -> [xml voice number]
        s.clefMap = {}    # xml staff number -> abc clef (for header only)
        s.curClef = {}    # xml staff number -> current abc clef
        s.clefOct = {}    # xml staff number -> current clef-octave-change
        s.curStf = {}     # xml voice number -> current xml staff number
        s.nolbrk = options.x;   # generate no linebreaks ($)
        s.jscript = options.j   # compatibility with javascript version
        s.ornaments = note_ornamentation_map.items ()
        if s.jscript: s.ornaments.sort ()
        s.doPageFmt = len (options.p) == 1 # translate xml page format
        s.tstep = options.t     # clef determines step on staff (percussion)

    def matchSlur (s, type2, n, v2, note2, grace, stopgrace): # match slur number n in voice v2, add abc code to before/after
        if type2 not in ['start', 'stop']: return   # slur type continue has no abc equivalent
        if n == None: n = '1'
        if n in s.slurBuf:
            type1, v1, note1, grace1 = s.slurBuf [n]
            if type2 != type1:              # slur complete, now check the voice
                if v2 == v1:                # begins and ends in the same voice: keep it
                    if type1 == 'start' and (not grace1 or not stopgrace):  # normal slur: start before stop and no grace slur
                        note1.before = '(' + note1.before   # keep left-right order!
                        note2.after += ')'
                    # no else: don't bother with reversed stave spanning slurs
                del s.slurBuf [n]           # slur finished, remove from stack
            else:                           # double definition, keep the last
                info ('double slur numbers %s-%s in part %d, measure %d, voice %d note %s, first discarded' % (type2, n, s.msr.ixp+1, s.msr.ixm+1, v2, note2.ns))
                s.slurBuf [n] = (type2, v2, note2, grace)
        else:                               # unmatched slur, put in dict
            s.slurBuf [n] = (type2, v2, note2, grace)
    
    def doNotations (s, note, nttn):
        for key, val in s.ornaments:
            if nttn.find (key) != None: note.before += val  # just concat all ornaments
        fingering = nttn.find ('technical/fingering')
        if fingering != None:   # strings or plug not supported in ABC
            note.before += '!%s!' % fingering.text     # validate text?
        wvln = nttn.find ('ornaments/wavy-line')
        if wvln != None:
            if   wvln.get ('type') == 'start': note.before = '!trill(!' + note.before # keep left-right order!
            elif wvln.get ('type') == 'stop': note.after += '!trill)!'

    def ntAbc (s, ptc, o, note, v):  # pitch, octave -> abc notation
        acc2alt = {'double-flat':-2,'flat-flat':-2,'flat':-1,'natural':0,'sharp':1,'sharp-sharp':2,'double-sharp':2}
        o += s.clefOct.get (s.curStf [v], 0)  # minus clef-octave-change value
        p = ptc
        if o > 4: p = ptc.lower ()
        if o > 5: p = p + (o-5) * "'"
        if o < 4: p = p + (4-o) * ","
        acc = note.findtext ('accidental')  # should be the notated accidental
        alt = note.findtext ('pitch/alter') # pitch alteration (midi)
        if alt == None and s.msralts.get (ptc, 0): alt = 0  # no alt but key implies alt -> natural!!
        if acc == None and alt == None: return p    # no acc, no alt
        elif acc != None:
            alt = acc2alt [acc]
        else:   # now see if we really must add an accidental
            alt = int (alt)
            if (p, v) in s.curalts:  # the note in this voice has been altered before
                if alt == s.curalts [(p, v)]: return p      # alteration still the same
            elif alt == s.msralts.get (ptc, 0): return p    # alteration implied by the key
            if 'stop' in [e.get ('type') for e in note.findall ('tie')]: return p   # don't alter tied notes
            info ('accidental %d added in part %d, measure %d, voice %d note %s' % (alt, s.msr.ixp+1, s.msr.ixm+1, v+1, p))
        s.curalts [(p, v)] = alt
        p = ['__','_','=','^','^^'][alt+2] + p # and finally ... prepend the accidental
        return p

    def doNote (s, n):    # parse a musicXML note tag
        note = Note ()
        v = int (n.findtext ('voice', '1'))
        if s.isSib: v += 100 * int (n.findtext ('staff', '1'))  # repair bug in Sibelius
        chord = n.find ('chord') != None
        p = n.findtext ('pitch/step') or n.findtext ('unpitched/display-step')
        o = n.findtext ('pitch/octave') or n.findtext ('unpitched/display-octave')
        r = n.find ('rest')
        numer = n.findtext ('time-modification/actual-notes')
        if numer:
            denom = n.findtext ('time-modification/normal-notes')
            note.fact = (int (numer), int (denom))
        note.tup = [x.get ('type') for x in n.findall ('notations/tuplet')]
        dur = n.findtext ('duration')
        grc = n.find ('grace')
        note.grace = grc != None
        note.before, note.after = '', '' # strings with ABC stuff that goes before or after a note/chord
        if note.grace and not s.ingrace: # open a grace sequence
            s.ingrace = 1
            note.before = '{'
            if grc.get ('slash') == 'yes': note.before += '/'   # acciaccatura
        stopgrace = not note.grace and s.ingrace
        if stopgrace:                   # close the grace sequence
            s.ingrace = 0
            s.msc.lastnote.after += '}' # close grace on lastenote.after
        if r == None and n.get ('print-object') == 'no': # not a rest and not visible
            s.msc.cnt.inc ('nopr', v)   # count skipped notes
            return                      # skip non printable notes
        if dur == None or note.grace: dur = 0
        note.dur = int (dur)
        if r == None and (not p or not o):  # not a rest and no pitch
            s.msc.cnt.inc ('nopt', v)       # count unpitched notes
            o, p = 5,'E'                    # make it an E5 ??
        nttn = n.find ('notations')     # add ornaments
        if nttn != None: s.doNotations (note, nttn)
        if r != None: noot = 'z'
        else: noot = s.ntAbc (p, int (o), n, v)
        if n.find ('unpitched') != None:
            clef = s.curClef [s.curStf [v]]     # the current clef for this voice
            step = staffStep (p, int (o), clef, s.tstep)        # (clef independent) step value of note on the staff
            instr = n.find ('instrument')
            instId = instr.get ('id') if instr != None else 'dummyId'
            midi = s.drumInst.get (instId, abcMid (noot))
            nh =  n.findtext ('notehead', '').replace (' ','-') # replace spaces in xml notehead names for percmap
            if nh == 'x': noot = '^' + noot.replace ('^','').replace ('_','')
            if nh == 'circle-x' or nh == 'diamond': noot = '_' + noot.replace ('^','').replace ('_','')
            if nh and n.find ('notehead').get ('filled','') == 'yes': nh += '+'
            s.drumNotes [(v, noot)] = (step, midi, nh) # keep data for percussion map
        if 'start' in [e.get ('type') for e in n.findall ('tie')]:          # n can have stop and start tie
            noot = noot + '-'
        note.beam = sum ([1 for b in n.findall('beam') if b.text in ['continue', 'end']]) + int (note.grace)
        lyrlast = 0; rsib = re.compile (r'^.*verse')
        for e in n.findall ('lyric'):
            lyrnum = int (rsib.sub ('', e.get ('number', '1'))) # also do Sibelius numbers
            if lyrnum == 0: lyrnum = lyrlast + 1                # and correct Sibelius bugs
            else: lyrlast = lyrnum
            note.lyrs [lyrnum] = doSyllable (e)
        if chord: s.msc.addChord (noot)
        else:
            xmlstaff = int (n.findtext ('staff', '1'))
            if s.curStf [v] != xmlstaff:    # the note should go to another staff
                dstaff = xmlstaff - s.curStf [v]    # relative new staff number
                s.curStf [v] = xmlstaff     # remember the new staff for this voice
                s.msc.appendElem (v, '[I:staff %+d]' % dstaff)  # insert a move before the note
            s.msc.appendNote (v, note, noot)
        for slur in n.findall ('notations/slur'):   # s.msc.lastnote points to the last real note/chord inserted above
            s.matchSlur (slur.get ('type'), slur.get ('number'), v, s.msc.lastnote, note.grace, stopgrace) # match slur definitions

    def doAttr (s, e):    # parse a musicXML attribute tag
        teken = {'C1':'alto1','C2':'alto2','C3':'alto','C4':'tenor','F4':'bass','F3':'bass3','G2':'treble','TAB':'','percussion':'perc'}
        dvstxt = e.findtext ('divisions')
        if dvstxt: s.msr.divs = int (dvstxt)
        steps = int (e.findtext ('transpose/chromatic', '0'))   # for transposing instrument
        fifths = e.findtext ('key/fifths')
        first = s.msc.tijd == 0 and s.msr.ixm == 0  # first attributes in first measure
        if fifths:
            key, s.msralts = setKey (int (fifths), e.findtext ('key/mode','major'))
            if first and not steps and abcOut.key == 'none':
                abcOut.key = key                # first measure -> header, if not transposing instrument or percussion part!
            elif key != abcOut.key or not first:
                s.msr.attr += '[K:%s]' % key    # otherwise -> voice
        beats = e.findtext ('time/beats')
        if beats:
            unit = e.findtext ('time/beat-type')
            mtr = beats + '/' + unit
            if first: abcOut.mtr = mtr          # first measure -> header
            else: s.msr.attr += '[M:%s]' % mtr # otherwise -> voice
            s.msr.mdur = (s.msr.divs * int (beats) * 4) / int (unit)    # duration of measure in xml-divisions
        toct = e.findtext ('transpose/octave-change', '')
        if toct: steps += 12 * int (toct)       # extra transposition of toct octaves
        for clef in e.findall ('clef'):         # a part can have multiple staves
            n = int (clef.get ('number', '1'))  # local staff number for this clef
            sgn = clef.findtext ('sign')
            line = clef.findtext ('line', '') if sgn != 'percussion' else ''
            cs = teken.get (sgn + line, '')
            oct = clef.findtext ('clef-octave-change', '') or '0'
            if oct: cs += {-2:'-15', -1:'-8', 1:'+8', 2:'+15'}.get (int (oct), '')
            s.clefOct [n] = -int (oct);         # xml playback pitch -> abc notation pitch
            if steps: cs += ' transpose=' + str (steps)
            lines = e.findtext ('staff-details/staff-lines')
            if lines: cs += ' stafflines=%s' % lines
            s.curClef [n] = cs                  # keep track of current clef (for percmap)
            if first: s.clefMap [n] = cs        # clef goes to header (where it is mapped to voices)
            else:
                voices = s.stfMap[n]            # clef change to all voices of staff n
                for v in voices:
                    if n != s.curStf [v]:       # voice is not at its home staff n
                        dstaff = n - s.curStf [v]
                        s.curStf [v] = n        # reset current staff at start of measure to home position
                        s.msc.appendElem (v, '[I:staff %+d]' % dstaff)
                    s.msc.appendElem (v, '[K:%s]' % cs)

    def doDirection (s, e): # parse a musicXML direction tag
        plcmnt = e.get ('placement')
        stfnum = int (e.findtext ('staff',1))   # directions belong to a staff
        vs = s.stfMap [stfnum][0]               # directions to first voice of staff
        t = e.find ('sound')        # there are many possible attributes for sound
        if t != None:
            minst = t.find ('midi-instrument')
            if minst:
                prg = t.findtext ('midi-instrument/midi-program')
                chn = t.findtext ('midi-instrument/midi-channel')
                vids = [v for v, id in s.vceInst.items () if id == minst.get ('id')]
                if vids: vs = vids [0]          # direction for the indentified voice, not the staff
                parm, inst = ('program', str (int (prg) - 1)) if prg else ('channel', chn)
                if inst and abcOut.volpan > 0: s.msc.appendElem (vs, '[I:MIDI= %s %s]' % (parm, inst))
            tempo = t.get ('tempo') # look for tempo attribute
            if tempo:
                if '.' in tempo: tempo = '%.2f' % float (tempo) # hope it is a number and insert in voice 1
                else:            tempo = '%d' % int (tempo)
                if s.msc.tijd == 0 and s.msr.ixm == 0: abcOut.tempo = tempo   # first measure -> header
                else: s.msc.appendElem (vs, '[Q:1/4=%s]' % tempo)   # otherwise -> voice
        dirtyp = e.find ('direction-type')
        if dirtyp != None:
            t = dirtyp.find ('wedge')
            if t != None:
                type = t.get ('type')
                if   type == 'crescendo':  x = '!<(!'; s.wedge_type = '<'
                elif type == 'diminuendo': x = '!>(!'; s.wedge_type = '>'
                elif type == 'stop':
                    if s.wedge_type == '<': x = '!<)!'
                    else:                   x = '!>)!'
                else: raise ValueError ('wrong wedge type')
                s.msc.appendElem (vs, x)        # to first voice
            txt = dirtyp.findtext ('words')     # insert text annotations
            if txt:
                plc = plcmnt == 'below' and '_' or '^'
                if int (e.get ('default-y', '0')) < 0: plc = '_'
                txt = txt.replace ('"','\\"').replace ('\n', ' ')
                if s.jscript: txt = txt.strip ()
                s.msc.appendElem (vs, '"%s%s"' % (plc, txt)) # to first voice
            for key, val in dynamics_map.items ():
                if dirtyp.find ('dynamics/' + key) != None:
                    s.msc.appendElem (vs, val)  # to first voice
            if dirtyp.find ('coda') != None: s.msc.appendElem (vs, 'O')
            if dirtyp.find ('segno') != None: s.msc.appendElem (vs, 'S')

    def doHarmony (s, e):   # parse a musicXMl harmony tag
        stfnum = int (e.findtext ('staff',1))   # harmony belongs to a staff
        vt = s.stfMap [stfnum][0]               # harmony to first voice of staff
        short = {'major':'', 'minor':'m', 'augmented':'+', 'diminished':'dim', 'dominant':'7', 'half-diminished':'m7b5'}
        accmap = {'major':'maj', 'dominant':'', 'minor':'m', 'diminished':'dim', 'augmented':'+', 'suspended':'sus'}
        modmap = {'second':'2', 'fourth':'4', 'seventh':'7', 'sixth':'6', 'ninth':'9', '11th':'11', '13th':'13'}
        altmap = {'1':'#', '0':'', '-1':'b'}
        root = e.findtext ('root/root-step','')
        alt = altmap.get (e.findtext ('root/root-alter'), '')
        sus = ''
        kind = e.findtext ('kind', '')
        if kind in short: kind = short [kind]
        elif '-' in kind:   # xml chord names: <triad name>-<modification>
            triad, mod = kind.split ('-')
            kind = accmap.get (triad, '') + modmap.get (mod, '')
            if kind.startswith ('sus'): kind, sus = '', kind    # sus-suffix goes to the end
        elif kind == 'none': kind = e.find ('kind').get ('text','')
        degrees = e.findall ('degree')
        for d in degrees:   # chord alterations
            kind += altmap.get (d.findtext ('degree-alter'),'') + d.findtext ('degree-value','')
        kind = kind.replace ('79','9').replace ('713','13').replace ('maj6','6')
        bass = e.findtext ('bass/bass-step','') + altmap.get (e.findtext ('bass/bass-alter'),'') 
        s.msc.appendElem (vt, '"%s%s%s%s%s"' % (root, alt, kind, sus, bass and '/' + bass))

    def doBarline (s, e):       # 0 = no repeat, 1 = begin repeat, 2 = end repeat
        rep = e.find ('repeat')
        if rep != None: rep = rep.get ('direction')
        if s.unfold:            # unfold repeat, don't translate barlines
            return rep and (rep == 'forward' and 1 or 2) or 0
        loc = e.get ('location')
        if loc == 'right':      # only change style for the right side
            style = e.findtext ('bar-style')
            if   style == 'light-light': s.msr.rline = '||'
            elif style == 'light-heavy': s.msr.rline = '|]'
        if rep != None:         # repeat found
            if rep == 'forward': s.msr.lline = ':'
            else:                s.msr.rline = ':|' # override barline style
        end = e.find ('ending')
        if end != None:
            if end.get ('type') == 'start':
                n = end.get ('number', '1').replace ('.','').replace (' ','')
                try: map (int, n.split (','))   # should be a list of integers
                except: n = '"%s"' % n.strip () # illegal musicXML
                s.msr.lnum = n          # assume a start is always at the beginning of a measure
            elif s.msr.rline == '|':    # stop and discontinue the same  in ABC ?
                s.msr.rline = '||'      # to stop on a normal barline use || in ABC ?
        return 0

    def doPrint (s, e):     # print element, measure number -> insert a line break
        if e.get ('new-system') == 'yes' or e.get ('new-page') == 'yes':
            if not s.nolbrk: return '$'  # a line break

    def doPartList (s, e):  # translate the start/stop-event-based xml-partlist into proper tree
        for sp in e.findall ('part-list/score-part'):
            midi = {}
            for m in sp.findall ('midi-instrument'):
                x = [m.findtext (p, s.midDflt [i]) for i,p in enumerate (['midi-channel','midi-program','volume','pan'])]
                pan = float (x[3])
                if pan >= -90 and pan <= 90:    # would be better to map behind-pannings
                    pan = (float (x[3]) + 90) / 180 * 127   # xml between -90 and +90
                midi [m.get ('id')] = [int (x[0]), int (x[1]), float (x[2]), pan]
                up = m.findtext ('midi-unpitched')
                if up: s.drumInst [m.get ('id')] = int (up) - 1 # store midi-pitch for channel 10 notes
            s.instMid.append (midi)
        ps = e.find ('part-list')               # partlist  = [groupelem]
        xs = getPartlist (ps)                   # groupelem = partname | grouplist
        partlist, _ = parseParts (xs, {}, [])   # grouplist = [groupelem, ..., groupdata]
        return partlist                         # groupdata = [group-symbol, group-barline, group-name, group-abbrev]

    def mkTitle (s, e):
        def filterCredits (y):  # y == filter level, higher filters less
            cs = []
            for x in credits:   # skip redundant credit lines
                if y < 6 and (x in title or x in mvttl): continue         # sure skip
                if y < 5 and (x in composer or x in lyricist): continue   # almost sure skip
                if y < 4 and ((title and title in x) or (mvttl and mvttl in x)): continue   # may skip too much
                if y < 3 and ([1 for c in composer if c in x] or [1 for c in lyricist if c in x]): continue # skips too much
                if y < 2 and re.match (r'^[\d\W]*$', x): continue       # line only contains numbers and punctuation
                cs.append (x)
            if y == 0 and (title + mvttl): cs = ''  # default: only credit when no title set
            return cs
        title = e.findtext ('work/work-title', '').strip ()
        mvttl = e.findtext ('movement-title', '').strip ()
        composer, lyricist, credits = [], [], []
        for creator in e.findall ('identification/creator'):
            if creator.text:
                if creator.get ('type') == 'composer':
                    composer += [line.strip () for line in creator.text.split ('\n')]
                elif creator.get ('type') in ('lyricist', 'transcriber'):
                    lyricist += [line.strip () for line in creator.text.split ('\n')]
        for credit in e.findall('credit'):
            cs = ''.join (e.text or '' for e in credit.findall('credit-words'))
            credits += [re.sub (r'\s*[\r\n]\s*', ' ', cs)]
        credits = filterCredits (s.ctf)
        if title: title = 'T:%s\n' % title.replace ('\n', '\nT:')
        if mvttl: title += 'T:%s\n' % mvttl.replace ('\n', '\nT:')
        if credits: title += '\n'.join (['T:%s' % c for c in credits]) + '\n'
        if composer: title += '\n'.join (['C:%s' % c for c in composer]) + '\n'
        if lyricist: title += '\n'.join (['Z:%s' % c for c in lyricist]) + '\n'
        if title: abcOut.title = title[:-1]
        s.isSib = 'Sibelius' in (e.findtext ('identification/encoding/software') or '')
        if s.isSib: info ('Sibelius MusicXMl is unreliable')

    def doDefaults (s, e):
        if not s.doPageFmt: return  # return if -pf option absent
        d = e.find ('defaults');
        if d == None: return;
        mils = d.findtext ('scaling/millimeters')   # mills == staff height (mm)
        tenths = d.findtext ('scaling/tenths')      # staff height in tenths
        if not mils or not tenths: return
        xmlScale = float (mils) / float (tenths);   # tenths -> mm
        space = 10 * xmlScale       # space between staff lines == 10 tenths
        abcScale = space / 2.117    # 2.117 mm = 6pt = space between staff lines for scale = 1.0 in abcm2ps
        abcOut.pageFmt ['scale'] = abcScale
        eks = 2 * ['page-layout/'] + 4 * ['page-layout/page-margins/']
        eks = [a+b for a,b in zip (eks, 'page-height,page-width,left-margin,right-margin,top-margin,bottom-margin'.split (','))]
        for i in range (6):
            v = d.findtext (eks [i])
            k = abcOut.pagekeys [i+1]   # pagekeys [0] == scale already done, skip it
            if not abcOut.pageFmt [k] and v:
                try: abcOut.pageFmt [k] = float (v) * xmlScale / 10.    # -> cm
                except: info ('illegal value %s for xml element %s', (v, eks [i])); continue    # just skip illegal values

    def locStaffMap (s, part):  # map voice to staff with majority voting
        vmap = {}   # {voice -> {staff -> n}} count occurrences of voice in staff
        s.vceInst = {}          # {voice -> instrument id} for this part
        s.msc.vnums = {}        # voice id's
        ns = part.findall ('measure/note')
        for n in ns:            # count staff allocations for all notes
            v = int (n.findtext ('voice', '1'))
            if s.isSib: v += 100 * int (n.findtext ('staff', '1'))  # repair bug in Sibelius
            s.msc.vnums [v] = 1 # collect all used voice id's in this part
            sn = int (n.findtext ('staff', '1'))
            if v not in vmap:
                vmap [v] = {sn:1}
            else:
                d = vmap[v]     # counter for voice v
                d[sn] = d.get (sn, 0) + 1   # ++ number of allocations for staff sn
            x = n.find ('instrument')
            if x != None: s.vceInst [v] = x.get ('id')
        s.stfMap, s.clefMap = {}, {}    # staff -> [voices], staff -> clef
        vks = vmap.keys ()
        if s.jscript or s.isSib: vks.sort ()
        for v in vks:           # choose staff with most allocations for each voice
            xs = [(n, sn) for sn, n in vmap[v].items ()]
            xs.sort ()
            stf = xs[-1][1]     # the winner: staff with most notes of voice v
            s.stfMap[stf] = s.stfMap.get (stf, []) + [v]
            s.curStf [v] = stf  # current staff of XML voice v

    def addStaffMap (s, vvmap): # vvmap: xml voice number -> global abc voice number
        part = [] # default: brace on staffs of one part
        for stf, voices in sorted (s.stfMap.items ()):  # s.stfMap has xml staff and voice numbers
            locmap = sorted ([vvmap [iv] for iv in voices if iv in vvmap])
            if locmap:          # abc voice number of staff stf
                part.append (locmap)
                clef = s.clefMap.get (stf, 'treble')    # {xml staff number -> clef}
                for iv in locmap: abcOut.clefs [iv] = clef
        s.gStfMap.append (part)

    def addMidiMap (s, ip, vvmap):      # map abc voices to midi settings
        instr = s.instMid [ip]          # get the midi settings for this part
        if instr.values (): defInstr = list(instr.values ())[0]   # default settings = first instrument
        else:               defInstr = s.midDflt    # no instruments defined
        xs = []
        for v, vabc in vvmap.items ():  # xml voice num, abc voice num
            ks = sorted (s.drumNotes.items ())
            ds = [(nt, step, midi, head) for (vd, nt), (step, midi, head) in ks if v == vd] # map perc notes
            id = s.vceInst.get (v, '')  # get the instrument-id for part with multiple instruments
            if id in instr:             # id is defined as midi-instrument in part-list
                   xs.append ((vabc, instr [id] + ds))  # get midi settings for id 
            else:  xs.append ((vabc, defInstr   + ds))  # only one instrument for this part
        xs.sort ()  # put abc voices in order
        s.midiMap.extend ([midi for v, midi in xs])

    def parse (s, fobj):
        e = E.parse (fobj)
        s.mkTitle (e)
        s.doDefaults (e)
        partlist = s.doPartList (e)
        parts = e.findall ('part')
        for ip, p in enumerate (parts):
            maten = p.findall ('measure')
            s.locStaffMap (p)   # {voice -> staff} for this part
            s.drumNotes = {}    # (xml voice, abc note) -> (midi note, note head)
            s.clefOct = {}      # xml staff number -> current clef-octave-change
            s.msc.initVoices (newPart = 1)  # create all voices
            aantalHerhaald = 0  # keep track of number of repititions
            herhaalMaat = 0     # target measure of the repitition
            s.msr = Measure (ip)   # various measure data
            while s.msr.ixm < len (maten):
                maat = maten [s.msr.ixm]
                herhaal, lbrk = 0, ''
                s.msr.reset ()
                s.curalts = {}  # passing accidentals are reset each measure
                es = maat.getchildren ()
                for e in es:
                    if   e.tag == 'note':       s.doNote (e)
                    elif e.tag == 'attributes': s.doAttr (e)
                    elif e.tag == 'direction':  s.doDirection (e)
                    elif e.tag == 'sound':      s.doDirection (maat) # sound element directly in measure!
                    elif e.tag == 'harmony':    s.doHarmony (e)
                    elif e.tag == 'barline': herhaal = s.doBarline (e)
                    elif e.tag == 'backup':
                        dt = int (e.findtext ('duration'))
                        s.msc.incTime (-dt)
                    elif e.tag == 'forward':
                        dt = int (e.findtext ('duration'))
                        s.msc.incTime (dt)
                    elif e.tag == 'print':  lbrk = s.doPrint (e)
                s.msc.addBar (lbrk, s.msr)
                if   herhaal == 1:
                    herhaalMaat = s.msr.ixm
                    s.msr.ixm += 1
                elif herhaal == 2:
                    if aantalHerhaald < 1:  # jump
                        s.msr.ixm = herhaalMaat
                        aantalHerhaald += 1
                    else:
                        aantalHerhaald = 0  # reset
                        s.msr.ixm += 1      # just continue
                else: s.msr.ixm += 1        # on to the next measure
            vvmap = s.msc.outVoices (s.msr.divs, ip, s.isSib)
            s.addStaffMap (vvmap)           # update global staff map
            s.addMidiMap (ip, vvmap)
        if vvmap:
            abcOut.mkHeader (s.gStfMap, partlist, s.midiMap)
            abcOut.writeall ()
        else: info ('nothing written, %s has no notes ...' % abcOut.fnmext)

#----------------
# Main Program
#----------------
if __name__ == '__main__':
    from optparse import OptionParser
    from glob import glob
    from zipfile import ZipFile 
    parser = OptionParser (usage='%prog [-h] [-u] [-m] [-c C] [-d D] [-n CPL] [-b BPL] [-o DIR] [-v V] [-x] [-p PFMT] <file1> [<file2> ...]', version=str(VERSION))
    parser.add_option ("-u", action="store_true", help="unfold simple repeats")
    parser.add_option ("-m", action="store", help="0 -> no %%MIDI, 1 -> minimal %%MIDI, 2-> all %%MIDI", default=0)
    parser.add_option ("-c", action="store", type="int", help="set credit text filter to C", default=0, metavar='C')
    parser.add_option ("-d", action="store", type="int", help="set L:1/D", default=0, metavar='D')
    parser.add_option ("-n", action="store", type="int", help="CPL: max number of characters per line (default 100)", default=0, metavar='CPL')
    parser.add_option ("-b", action="store", type="int", help="BPL: max number of bars per line", default=0, metavar='BPL')
    parser.add_option ("-o", action="store", help="store abc files in DIR", default='', metavar='DIR')
    parser.add_option ("-v", action="store", type="int", help="set volta typesetting behaviour to V", default=0, metavar='V')
    parser.add_option ("-x", action="store_true", help="output no line breaks")
    parser.add_option ("-p", action="store", help="pageformat PFMT (cm) = scale, pageheight, pagewidth, leftmargin, rightmargin, topmargin, botmargin", default='', metavar='PFMT')
    parser.add_option ("-j", action="store_true", help="switch for compatibility with javascript version")
    parser.add_option ("-t", action="store_true", help="staff step value in percmap depends on clef")   # simplifies later translation of I:percmap to %%map
    options, args = parser.parse_args ()
    if options.n < 0: parser.error ('only values >= 0')
    if options.b < 0: parser.error ('only values >= 0')
    if options.d and options.d not in [2**n for n in range (10)]:
        parser.error ('D should be on of %s' % ','.join ([str(2**n) for n in range (10)]))
    options.p = options.p and options.p.split (',') or [] # ==> [] | [string]
    if len (args) == 0: parser.error ('no input file given')
    pad = options.o
    if pad:
        if not os.path.exists (pad): os.mkdir (pad)
        if not os.path.isdir (pad): parser.error ('%s is not a directory' % pad)
    fnmext_list = []
    for i in args: fnmext_list += glob (i)
    if not fnmext_list: parser.error ('none of the input files exist')
    for X, fnmext in enumerate (fnmext_list):
        fnm, ext = os.path.splitext (fnmext)
        if ext.lower () not in ('.xml','.mxl'):
            info ('skipped input file %s, it should have extension .xml or .mxl' % fnmext)
            continue
        if os.path.isdir (fnmext):
            info ('skipped directory %s. Only files are accepted' % fnmext)
            continue
        if ext.lower () == '.mxl':          # extract .xml file from .mxl file
            z = ZipFile(fnmext)
            for n in z.namelist():          # assume there is always an xml file in a mxl archive !!
                if (n[:4] != 'META') and (n[-4:].lower() == '.xml'):
                    fobj = z.open (n)
                    break   # assume only one MusicXML file per archive
        else:
            fobj = open (fnmext)            # open regular xml file

        abcOut = ABCoutput (fnm + '.abc', pad, X, options)  # create global ABC output object
        psr = Parser (options)  # xml parser
        try:
            psr.parse (fobj)    # parse file fobj and write abc to <fnm>.abc
        except:
            etype, value, traceback = sys.exc_info ()   # works in python 2 & 3
            info ('** %s occurred: %s in %s' % (etype, value, fnmext), 0)
