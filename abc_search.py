import re

all_notes = "| C,, D,, E,, F,, G,, A,, B,, C, D, E, F, G, A, B, C D E F G A B c d e f g a b c' d' e' f' g' a' b' c'' d'' e'' f'' g'' a'' b''".split()
note2number = dict([(n, i) for (i, n) in enumerate(all_notes)])
note_pattern = re.compile(r"([ABCDEFG],*|[abcdefg]'*)")
repl_by_spaces = lambda m: ' ' * len(m.group(0))

remove_non_notes = re.compile(r'(?xm)' + '|'.join([
               r'\%\%beginps(.|\s)+?\%\%endps',  # remove embedded postscript
               r'\%\%begintext(.|\s)+?\%\%endtext',   # remove text
               r'\[\w:.*?\]',    # remove embedded fields
               #r'(?m)^\w:.*?$',  # remove normal fields
               r'^\w:.*?$',  # remove normal fields
               #r'(?m)%.*$',      # remove comments
               r'%.*$',      # remove comments
               r'\[\w:.*?\]',    # remove embedded fields
               r'\\"',           # remove escaped " characters
               r'".*?"',         # remove strings
               r'\\"',           # remove escaped quote characters
               r'\{.*?\}',       # remove grace notes
               r'!.+?!',         # remove ornaments like eg. !pralltriller!
               r'\+.+?\+',       # remove ornaments like eg. +pralltriller+
               r'\{.*?\}',       # remove grace notes
               ]), flags=re.M)

def remove_non_note_fragments(abc):
    # replace non-note fragments of the text by replacing them by spaces (thereby preserving offsets), but keep also bar and repeat symbols
    return remove_non_notes.sub(repl_by_spaces, abc.replace('\r', '\n'))

def get_intervals_from_abc(abc):
    abc = remove_non_note_fragments(abc)
    notes = [note2number[m] for m in note_pattern.findall(abc)]
    intervals = [i2-i1 for (i1,i2) in zip(notes[:-1], notes[1:])]
    return ''.join([chr(74+i) for i in intervals])

def get_matches(abc, abc_search_intervals):
    abc = remove_non_note_fragments(abc)
    matches = list(note_pattern.finditer(abc))               # the matched notes in the abc
    notes = [note2number[m.group(0)] for m in matches]       # the note number for each note
    offsets = [m.span(0) for m in matches]                   # the start/end offset in the ABC code for each note
    intervals = [i2-i1 for (i1,i2) in zip(notes[:-1], notes[1:])]  # the intervals between pairs of notes
    intervals = ''.join([chr(74+i) for i in intervals])            # the intervals coded as strings
    # find the search string among all the intervals
    for m in re.finditer(re.escape(abc_search_intervals), intervals):
        i = m.start(0)      # the offset in the search string is the same as the index of the note
        start, end = offsets[i][0], offsets[i+len(abc_search_intervals)][1]
        yield (start, end)  # return start and end offset in the ABC code for the matched sequence of notes

def abc_matches_iter(abc, search_string):
    search = get_intervals_from_abc(search_string)
    offset = 0  # the total character offset from the beginning of the abc text
    tunes = abc.split('X:')  # split the code up per tune

    for i, tune in enumerate(tunes):
        if i > 0: tune = 'X:' + tune  # add back the X: to the tunes from which it was removed during the split

        # find matches
        for start_offset_in_tune, end_offset_in_tune in get_matches(tune, search):
            # convert the offsets within the tune to global offsets
            start, end = (offset+start_offset_in_tune, offset+end_offset_in_tune)
            yield (start, end)

        offset += len(tune)

if __name__ == '__main__':
    search = 'CEG'
    abc = '''' GE CE GE'''

    for r in abc_matches_iter(abc, search):
        pass
