
import re
import datetime

a_monday = datetime.datetime.strptime('2019-08-19', '%Y-%m-%d')

class Line:
    def __init__(self, date, l, sticky, attrs):
        self.date = date
        self.full = l
        self.dist = None
        self.dur = None
        self.d_pos = None
        self.d_neg = None
        self.shoes = None
        if 'shoes' in sticky: self.shoes = sticky['shoes']
        if 'shoes' in attrs: self.shoes = attrs['shoes']

        def derive_date(o):
            date = datetime.datetime.strptime(o.date, '%Y-%m-%d')
            delta = date - a_monday
            wd = delta.days % 7
            o.weekday = wd
            o.week = datetime.datetime.strftime(date - datetime.timedelta(wd), '%Y-%m-%d')
            o.month = datetime.datetime.strftime(date, '%Y-%m')
        derive_date(self)

        
        for e in l.split(' '):
            g = []
            def pat(reg):
                groups = re.fullmatch(reg, e)
                g[:] = []
                if groups is None:
                    return False
                else:
                    g[:] = groups.groups()
                return True
            if e.endswith(','):
                e = e[:-1]
            if e.startswith('~'):
                e = e[1:]
            if False: pass
            elif pat(r'([0-9.]+)km?'):
                self.set_dist(float(g[0]))
            elif pat(r'([0-9]+)min'):
                self.set_dur(int(g[0]))
            elif pat(r'([0-9][0-9]?):([0-9][0-9]?)'):
                self.set_dur(int(g[0]) + int(g[1])/60)
            elif pat(r'([0-9][0-9]?):([0-9][0-9]?):([0-9][0-9]?)'):
                self.set_dur(int(g[0])*60 + int(g[1]) + int(g[2])/60)
            elif pat(r'([0-9][0-9]?)h([0-9][0-9]?)'):
                self.set_dur(int(g[0])*60 + int(g[1]))
            elif pat(r'([0-9]+)D[+]'):
                self.set_d_pos(int(g[0]))
            elif pat(r'([0-9]+)D[-]'):
                self.set_d_neg(int(g[0]))
        if self.d_neg is None and self.d_pos is not None:
            self.d_neg = self.d_pos

    def set_dist(self, d):
        if self.dist is not None: raise Exception(f'set_dist({d}): dist already set to {self.dist} // {self.full}')
        self.dist = d

    def set_dur(self, d):
        if self.dur is not None: raise Exception(f'set_dur({d}): dur already set to {self.dur} // {self.full}')
        self.dur = d

    def set_d_pos(self, d):
        if self.d_pos is not None: raise Exception(f'set_d_pos({d}): d_pos already set to {self.d_pos} // {self.full}')
        self.d_pos = d
        
    def set_d_neg(self, d):
        if self.d_neg is not None: raise Exception(f'set_d_neg({d}): d_pos already set to {self.d_eng} // {self.full}')
        self.d_neg = d

    def __str__(self):
        return f'Line({self.dist}, {self.dur}, {self.d_pos}, {self.d_neg}, {self.full})'


def parse_logdown(fname):
    with open(fname, 'r') as f:
        content = '\n#'.join(reversed(f.read().split('\n#')))
        
        entries = []
        sticky = {}
        date = ""
        attrs = {}
        for l in content.split('\n'):
            l = l.rstrip()
            if l.startswith('# '):
                attrs = {}
                date = re.sub('[:,]', ' ', l).split(' ')[1]
            g = re.fullmatch(r'# #SET +(.+) *: *(.+)', l)
            if g is not None:
                sticky[g[1]] = g[2]
            elif re.match('- total[0-9]*:.*', l):
                l = Line(date, l, sticky, attrs)
                entries.append(l)
                print(l)
            elif l.startswith('- shoes: '):
                attrs['shoes'] = l.split(' ')[2]

        return entries

def print_shoes_stats(entries):
    print(set((l.shoes for l in entries)))
    
    for sh in 'addidas roclite roclite2 merrell terraultra'.split(' '):
        print()
        print('#', sh)
        subset = [e for e in entries if e.shoes == sh]
        print('Distance:', sum([l.dist for l in subset if l.dist]))
        print('D+:', sum([l.d_pos for l in subset if l.d_pos]))
        print('D-:', sum([l.d_neg for l in subset if l.d_neg]))

def main():
    entries = parse_logdown('course-journal.md')
    print_shoes_stats(entries)

    
if __name__== "__main__": main()
