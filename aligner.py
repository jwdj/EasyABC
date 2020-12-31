import re
import string
import os
from fractions import Fraction
import sys
if sys.version_info.major > 2:
    basestring = str

bar_sep_symbols = ':|][|: :|[2 :|]2 :||: [|] :|] [|: :|| ||: :|: |:: ::| |[1 :|2 |] || [| :: .| |1 |: :| [1 [2 |'.split()
bar_sep = re.compile('(%s)' % '|'.join(' *' + re.escape(x)+' *' for x in bar_sep_symbols))
bar_sep_without_space = re.compile('(%s)' % '|'.join(re.escape(x) for x in bar_sep_symbols))
bar_and_voice_overlay_sep = re.compile('(%s)' % '|'.join(' *' + re.escape(x)+' *' for x in (bar_sep_symbols + ['&'])))

def get_default_len(abc):
    if re.search(r'(?m)^L: *mcm_default', abc):
        return 'mcm_default'
    else:
        m = re.search(r'(?m)^L: *(\d+)/(\d+)', abc)
        if m:
            return Fraction(int(m.group(1)), int(m.group(2)))
        else:
            return Fraction(1, 8)

def get_metre(abc):
    m = re.search(r'(?m)^M: *(\d+)/(\d+)', abc)
    if m:
        return Fraction(int(m.group(1)), int(m.group(2)))
    else:
        return Fraction(4, 4)

def get_key(abc):
    m = re.search(r'(?m)^K: *(\w+)', abc)
    if m:
        return m.group(1)
    else:
        return 'C'

def remove_non_note_fragments(abc):
    # replace non-note fragments of the text by replacing them by spaces (thereby preserving offsets), but keep also bar and repeat symbols
    abc = re.sub(r'(?m)%.*$', '', abc)     # remove comments
    abc = re.sub(r'\[\w:.*?\]', '', abc)   # remove embedded fields
    abc = re.sub(r'\\"', '', abc)          # remove escaped " characters
    abc = re.sub(r'".*?"', '', abc)        # remove strings
    abc = re.sub(r'\{.*?\}', '', abc)      # remove grace notes
    abc = re.sub(r'!.+?!', '', abc)        # remove ornaments like eg. !pralltriller!
    abc = re.sub(r'\+.+?\+', '', abc)      # remove ornaments like eg. +pralltriller+
    return abc

def replace_chords_by_first_note(abc):
    # replace "[AD]2 [B2C2e2]" by "A2 B2" - the first note in each chord
    abc = remove_non_note_fragments(abc)
    note_pattern = r"(?P<note>([_=^]?[A-Ga-gxz](,+|'+)?))(?P<length>\d{0,2}/\d{1,2}|/+|\d{0,2})(?P<broken>[><]?)"
    def sub_func(m):
        match = re.search(note_pattern, m.group(0))
        if match:
            return match.group(0)
        else:
            return ''
    return re.sub(r'\[.*?\]', sub_func, abc)

def get_bar_length(abc, default_length, metre):
    abc = remove_non_note_fragments(abc)
    abc = replace_chords_by_first_note(abc)

    # 1.3.6.5 [JWDJ] 2015-12-19 not only triplet support but also handling of other tuplets
    note_pattern = r"(?P<note>([_=^]?[A-Ga-gxz](,+|'+)?))(?P<length>\d{0,3}(?:/\d{0,3})*)(?P<dot>\.*)(?P<broken>[><]?)"
    tuplet_pattern = r"\((?P<p>[1-9])(?:\:(?P<q>[1-9]?))?(?:\:(?P<r>[1-9]?))?" # put p notes into the time of q for the next r notes
    total_length = Fraction(0)
    last_broken_rythm = ''
    tuplet_notes_left = 0  # how many notes in the current tuplet are we yet to see
    tuplet_time = 2

    for match in re.finditer(r'(%s)|(%s)' % (note_pattern, tuplet_pattern), abc):
        n = match.group(0)
        if n[0] == '(':
            tuplet_notes = int(match.group('p'))
            tuplet_time = match.group('q')
            if tuplet_time:
                tuplet_time = int(tuplet_time)
            else:
                if tuplet_notes in [3, 6]:
                    tuplet_time = 2
                elif tuplet_notes in [2, 4, 8]:
                    tuplet_time = 3
                else: #elif tuplet_notes in [5, 7, 9]:
                    if metre.numerator % 3 == 0:
                        tuplet_time = 3 # for compound meter 6/8, 9/8, 12/8, etc
                    else:
                        tuplet_time = 2

            tuplet_notes_left = match.group('q')
            if tuplet_notes_left:
                tuplet_notes_left = int(tuplet_notes_left)
            else:
                tuplet_notes_left = tuplet_notes
            continue
        length = match.group('length')
        if isinstance(default_length, basestring) and default_length == 'mcm_default':
            length = length.split('/')[0]  # ignore any fraction
            multiplier = Fraction(1, int(length))
            for dot in match.group('dot'):
                multiplier = multiplier * Fraction(3, 2)
            total_length = total_length + multiplier
        else:
            multiplier = Fraction(1)
            broken_rythm = match.group('broken')
            if broken_rythm == '>' or last_broken_rythm == '<':
                multiplier = Fraction(3, 2)
            elif broken_rythm == '<' or last_broken_rythm == '>':
                multiplier = Fraction(1, 2)
            last_broken_rythm = broken_rythm

            # 1.3.6.5 [JWDJ] 2015-12-19 divisor parsed similar to abcm2ps
            dividend = length.split('/')[0]
            if dividend:
                multiplier = multiplier * Fraction(int(dividend))

            for divmatch in re.finditer(r'/(\d*)', length):
                divisor = divmatch.group(1)
                if divisor:
                    divisor = int(divisor)
                else:
                    divisor = 2
                multiplier = multiplier / Fraction(divisor)

            if tuplet_notes_left:
                multiplier = multiplier * Fraction(tuplet_time, tuplet_notes)
                tuplet_notes_left -= 1
            total_length = total_length + multiplier * default_length
    return total_length

def is_likely_anacrusis(bar, default_length, metre):
    if not bar or bar_sep.match(bar):
        return False
    actual_length = get_bar_length(bar, default_length, metre)
    expected_length = metre
    ##print repr(bar), float(actual_length), float(expected_length)
    return float(actual_length) <= float(expected_length)*0.8

def align_beams(bars):
    n = len(bars)
    bar_parts = [re.split(' +', b) for b in bars]
    num_parts = min(len(p) for p in bar_parts)
    for i in range(num_parts):
        parts = [bar_parts[line_no][i] for line_no in range(n)]
        max_len = max(len(p) for p in parts)
        parts = [p.ljust(max_len) for p in parts]
        for line_no in range(n):
            bar_parts[line_no][i] = parts[line_no]
    bars = [' '.join(bar_parts[line_no]) for line_no in range(n)]
    return bars

def align_bars(bars, align_inside_bars_too=True):
    if bar_sep.match(bars[0]):
        bars = [' %s ' % b.strip() for b in bars]
    elif align_inside_bars_too:
        bars = align_beams(bars)
    max_len = max(len(b) for b in bars)
    return [b.ljust(max_len) for b in bars]

def align_bar_separators(bar_seps):
    bar_seps = [' %s ' % bs.strip() for bs in bar_seps]
    use_rjust = any(':|' in bs for bs in bar_seps)

    if any('|' in bs for bs in bar_seps):
        # try to center around the last occurance of '|'
        max_pos_pipe = max(b.rfind('|') for b in bar_seps)
        for i in range(len(bar_seps)):
            p = bar_seps[i].rfind('|')
            if 0 <= p < max_pos_pipe:
                bar_seps[i] = (' ' * (max_pos_pipe-p)) + bar_seps[i]
        max_len = max(len(b) for b in bar_seps)
        return [b.ljust(max_len) for b in bar_seps]
    else:
        max_len = max(len(b) for b in bar_seps)
        if use_rjust:
            return [b.rjust(max_len) for b in bar_seps]
        else:
            return [b.ljust(max_len) for b in bar_seps]

def split_line_into_parts(line):
    parts = bar_sep.split(line)
    parts = [p for p in parts if p]
    return parts

def align_lines(whole_abc, lines, align_inside_bars_too=False):
    n = len(lines)
    line_parts = [split_line_into_parts(line.strip()) for line in lines]

    # determine the number of bars and pad lines with fewer elements by '' strings
    num_bars = max(len(lp) for lp in line_parts) + 1
    for line_no, lp in enumerate(line_parts):
        line_parts[line_no] += ['']
        if len(lp) < num_bars:
            line_parts[line_no] += [''] * (num_bars - len(lp))

    if num_bars:
        default_len = get_default_len(whole_abc)
        metre = get_metre(whole_abc)

    first_bar_handled = False

    for i in range(num_bars):
        # if the first bar with notes haven't been handled yet, check if we're currently seeing any anacrusis
        if not first_bar_handled and any(re.search(r'[a-gA-Gxz]', line_parts[line_no][i]) for line_no in range(n)):
            first_bar_handled = True
            is_anacrusis = [is_likely_anacrusis(line_parts[line_no][i], default_len, metre) for line_no in range(n)]
            ##print is_anacrusis, default_len, metre, [line_parts[line_no][i] for line_no in range(n)]
            # if at least one bar is an anacrusis and not all, then add '' for the bars the aren't
            if any(is_anacrusis) and not all(is_anacrusis):
                for line_no, is_ana in enumerate(is_anacrusis):
                    if not is_ana:
                        line_parts[line_no].insert(i, '')

        # if some element is a bar and others aren't, then add a kind of pseudo element ('') in order for the alignment to work
        any_is_bar_sep = any(bar_sep.match(line_parts[line_no][i]) for line_no in range(n))
        if any_is_bar_sep:
            for line_no in range(n):
                if not bar_sep.match(line_parts[line_no][i]):
                    line_parts[line_no].insert(i, '')

        bars = [line_parts[line_no][i] for line_no in range(n)]
        if any_is_bar_sep:
            bars = align_bar_separators(bars)
        else:
            bars = align_bars(bars, align_inside_bars_too=align_inside_bars_too)
        for line_no in range(n):
            line_parts[line_no][i] = bars[line_no]

    lines = [''.join(line_parts[i]) for i in range(n)]
    if all(l.startswith(' ') for l in lines):
        lines = [l[1:] for l in lines]
    return lines

def extract_incipit(abc, num_bars=2, num_repeats=999):
    # split tune header and body (and remove non-embedded fields in the body, except for K: which is made embedded)
    lines = re.split('\r\n|\r|\n', abc)
    lines = [re.sub(r'\s*%.*$', '', line) for line in lines]  # remove comments
    header = []
    body = []
    in_body = False
    for line in lines:
        if in_body:
            if re.match(r'[a-zA-Z]:', line):
                if line.startswith('K:'):
                    line = '[%s]' % line   # convert K: field to [K:]
                else:
                    continue               # ignore fields in the tune body
            body.append(line)
        elif re.match(r'[a-zA-Z]:', line):
            header.append(line)
            if line.startswith('K:'):
                in_body = True

    abc, header = ' '.join(body), os.linesep.join(header)
    #print abc
    #print '-'*10
    #print header
    #print '-'*10

    default_len = get_default_len(header)
    metre = get_metre(header)
    key = get_key(header)

    parts = split_line_into_parts(abc.strip())
    inside_repeat_ending = False
    L = [[]]       # list of parts (bar seps and bars) for each repeat/ending
    key_at_start = '[%s]' % key
    last_seen_key = key_at_start
    for part in parts:
        L[-1].append(part)

        m = re.search(r'\[K:.*?\]', part)
        if m:
            last_seen_key = m.group(0)

        if bar_sep.match(part):
            if re.search(r'\|\d', part):
                inside_repeat_ending = True
            if inside_repeat_ending and ('||' in part or '|]' in part):
                inside_repeat_ending = False
                L.append([])  # start new repeat/part
                if last_seen_key != key_at_start:
                    L[-1].append(last_seen_key)
                    key_at_start = last_seen_key
            elif '|:' in part:
                L[-1].pop()
                L.append([])  # start new repeat/part
                if last_seen_key != key_at_start:
                    L[-1].append(last_seen_key)
                    key_at_start = last_seen_key
                # if last bar was anacrusis, move it over to the current repeat/part
                if len(L) > 1 and len(L[-2]) >= 1 and is_likely_anacrusis(L[-2][-1], default_len, metre):
                    L[-1].append(L[-2][-1])
                    del L[-2][-1]
                L[-1].append(part)

    def extract_bars(parts, num_bars, default_len, metre):
        result = []
        bar_count = 0
        first_bar_handled = False
        for part in parts:
            result.append(part)
            if re.search(r'[a-gA-Gxz]', part) and not re.match(r'\s*\[\w:.*?\]\s*', part):
                if first_bar_handled:
                    bar_count += 1
                else:
                    first_bar_handled = True
                    if is_likely_anacrusis(part, default_len, metre):
                        bar_count = 0
                    else:
                        bar_count = 1
            elif num_bars == bar_count:
                break
        return (' '.join(result)).strip()

    L = [extract_bars(parts, num_bars, default_len, metre) for parts in L]
    L = [x.strip() for x in L if x.strip()]
    L = L[:num_repeats]
    return L

if __name__ == "__main__":

    s = '''X:32
T:Kadrilj2
M:2/4
L:1/16
K:F
u(AB)|(cd)cB ABcd|c2f2 a4|(ag)(gf) (fe)(ed)|
d6 c2|(Bc)BA (GA)Bc|d2g2 b4|(ba)(ag) (gf)eg|f4 z2:|
K:Bb
|:F2|F4 d2Bc|d2FA B2B,C|(DB,)B,B, (DB,)B,B,|F2F2 F4|
e4 g2cd|e2AB c2FG|({B}(A)F)FF (AF)FF|(dB)BB B2:| '''

    print(extract_incipit(s, num_repeats=2, num_bars=2))
