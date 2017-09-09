import re
from fractions import Fraction

def abc_length_to_fraction(length):    
    if length:
        nums = map(int, re.findall(r'\d+', length))
        if len(nums) == 2:
            return Fraction(nums[0], nums[1])
        elif length.startswith('/') and len(nums) == 1:
            return Fraction(1, nums[0])
        elif length.startswith('/'):
            return Fraction(1, 2**length.count('/'))
        else:
            return Fraction(nums[0])
    else:
        return Fraction(1)

def tokenize_abc(abc):
    # some reusable or complex patterns
    length = '(?P<length>/\d+|\d+/\d+?|\d+/*|/*)'    
    tie = "(?P<tie>-?(?P<tie_dir>[,']?))"
    note = r'''(?P<accidental>\^{1,2}|_{0,2}|=)
               (?P<note>[A-Ga-g])
               (?P<octave>'+|,*)''' + length + tie
    nth_repeat_num = r'(?P<repeat_num>\d+([,-]\d+)*)'    
    barline = r':? \[? \| \]? (%s | :?) | \[\|?\] | :' % nth_repeat_num

    # all tokens: [(token_name, regexp), ...] 
    tokens = [('field', r'^(?P<field>[A-Za-z]):\s*(?P<value>.*)'),
              ('inline_field',         r'\[(?P<field>[A-Za-z]):\s*(?P<value>.*?)\]'),
              ('instruction',          r'^%%(?P<instruction>[-_a-zA-Z]+)\s*(?P<parameters>.*)'),
              ('newline',              r'(\r\n|\r|\n)+'),
              ('space',                r'\s+'),                                  
              ('note',                 note),
              ('rest',                 r'(?P<rest>[zxy])' + length),
              ('text',                 r' " (?P<placement>[_^<>]|@[-+0-9,.]+ ) (?P<text>.*?) (?<!\\)" '),
              ('nth_repeat',           r'\[' + nth_repeat_num),
              ('barline',              barline),
              ('harmony',              r'"(?P<harmony>.*?)"'),                        
              ('tuplet_start',         r'\( (?P<n1>\d+) (:(?P<n2>\d+))? (:(?P<n3>\d+))?'),        
              ('slur_begin',           r"(?P<dot>\.?)   \(   (?P<direction>[,']?)"),
              ('slur_end',             r'\.?\)'),
              ('chord_start',          r'\['),
              ('chord_end',            r'\]'+length+tie),      # this could also be the end of a repeat, eg. [1 ... ]
              ('grace_start',          r'{\s*(?P<slash>/?)'),  # for the sake of simplicity the acciaccatura/slash is associated with this token
              ('grace_end',            r'}'),              
              ('broken_rythm',         r'\<+|\>+'),
              ('decoration',           r'![-a-zA-Z0-9]+?!'),
              ('old_style_decoration', r'\+[-a-zA-Z0-9]+?\+'),                        
              ('line_continuation',    r'\\'),
              ('voice_overlay',        r'&'),
              ('special_char',         r'[!#$*+;?@`]'),
              ('staccato',             r'\.'),
              ('comment',              r'%.*'),
              ('user_symbol',          r'[H-Yh-w~]'),
              ('free_floating_tie',    r"-(?P<tie_dir>[,']?)"),  # a tie that's (incorrectly) not written immediately after the note it belongs to              
              ]    
    tokens = [(t, re.compile(pattern, re.M | re.X)) for (t, pattern) in tokens]  # compile the regular expressions    

    # step through the ABC code and try to match a token at each position
    pos = 0
    inside_beam = False
    inside_grace = False
    while pos < len(abc):        
        for token, pattern in tokens:
            m = pattern.match(abc, pos=pos)
            if m:
                properties = m.groupdict()
                
                # convert length from string to fraction (if present)
                if 'length' in properties:
                    properties['length'] = abc_length_to_fraction(properties['length'])

                inside_grace = (inside_grace or token == 'grace_start') and token != 'grace_end'

                if not inside_grace:
                    # inject beam_start/beam_end tokens if necessary
                    if inside_beam and token in ('space','newline'):
                        inside_beam = False
                        yield 'beam_end', {}, ''
                    elif not inside_beam and token in ('note','barline'):
                        inside_beam = True
                        yield 'beam_start', {}, ''
                    
                yield token, properties, m.group(0)
                pos += len(m.group(0))                
                break
        else:
            print 'warning: no match found at offset %d (%s). Aborting.' % (pos, repr(abc[pos:pos+100]))
            break
    if inside_beam:
        yield 'beam_end', {}, ''

class ABCOptions(object):
    def __init__(self):
        self.options = {}
        self.beam_break_tokens = ('space', 'newline')

class Measure(object):
    def __init__(self, parent_voice):
        self.parent_voice = parent_voice

class Voice(object):
    def __init__(self):
        self.measures = []
        self.cur_measure = Measure()
    def break_beam(self):
        pass

class ABCParser(object):
    def __init__(self):
        self.tune_options = ABCOptions()
        self.cur_voice = None
    def parse(self, token_iterator):
        in_header = False
        for token, properties, text in token_iterator:
            if in_header:
                if token == 'field':
                    self.tune_options[properties['field']] = properties['value']
                    if properties['field'] == 'K':
                        in_header = False
                        continue
                elif token == 'newline':
                    pass
                else:
                    print 'warning: expected field here (the K: field marks the beginning of the tune)'
                    in_header = False
            if not in_header:
                if token not in ('space', 'newline'):
                    prop_text = ', '.join('%s=%s' % (k,v or 'None') for (k,v) in properties.items() if v)
                    token_debug = '%s %s %s' % (token.upper().ljust(13), text.ljust(10), prop_text)
                    print token_debug    
        

if __name__ == '__main__':        

    # sample tune:
    abc = '''
X: 1
T: My tune
K: C
(D z [D,F]-[D,F]2) |: {/c}B>B !trill!c2-c2 .d// : [M:3/4] "Cm" "^Test" :|1 C [2 D'''

    abc = 'ABCD AB C2-D2'
    print 'ABC code:', abc
    
    tokens = tokenize_abc(abc)
    parser = ABCParser()
    parser.parse(tokens)
    #for token, properties, text in tokenize_abc(abc):                
    #    if token not in ('space', 'newline'):
    #        prop_text = ', '.join('%s=%s' % (k,v or 'None') for (k,v) in properties.items() if v)
    #        token_debug = '%s %s %s' % (token.upper().ljust(13), text.ljust(10), prop_text)
    #        print token_debug    
    