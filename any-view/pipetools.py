
import re
import pipe
from pipe import tee, where, select

def cat(*paths):
    for path in paths:
        with open(path) as f:
            for l in f.readlines():
                l = re.sub(r'\n$', '', l)
                yield l

def do(iterable):
    for i in iterable:
        pass
def is_not_empty(o): return sum(1 for i in o) > 0
def is_not_None(o): return o is not None

@pipe.Pipe
def sed(iterable, regexp, repl):
    for l in iterable:
        yield re.sub(regexp, repl, l)

@pipe.Pipe
def grep(iterable, regexp, flags=0):
    if type(regexp) == str:
        regexp = re.compile(regexp, flags=flags)
    for l in iterable:
        if regexp.search(l):
            yield l

igrep = grep(flags=re.IGNORECASE)

@pipe.Pipe
def grep_gr(iterable, regexp, flags=0):
    if type(regexp) == str:
        regexp = re.compile(regexp, flags=flags)
    for l in iterable:
        m = regexp.match(l)
        if m is not None:
            yield [m.group(0), *m.groups(), l]

@pipe.Pipe
def json(iterable):
    import json
    for l in iterable:
        yield json.loads(l)
