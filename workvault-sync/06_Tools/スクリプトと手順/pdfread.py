# -*- coding: utf-8 -*-
"""Read-only minimal PDF text extractor (FlateDecode + ToUnicode CMap).
Does not modify the source file. No external dependencies."""
import re, sys, zlib, codecs

def load(path):
    with open(path, 'rb') as f:
        return f.read()

def find_objects(data):
    objs = {}
    for m in re.finditer(rb'(\d+)\s+(\d+)\s+obj\b', data):
        num = int(m.group(1))
        start = m.end()
        e = data.find(b'endobj', start)
        objs[num] = data[start:e if e != -1 else len(data)]
    return objs

def get_stream(body):
    m = re.search(rb'stream\r?\n', body)
    if not m:
        return None
    start = m.end()
    e = body.rfind(b'endstream')
    if e == -1:
        e = len(body)
    raw = body[start:e]
    if b'FlateDecode' in body[:m.start()]:
        try:
            return zlib.decompress(raw)
        except Exception:
            try:
                return zlib.decompressobj().decompress(raw)
            except Exception:
                return None
    return raw

def parse_cmap(txt):
    """Parse ToUnicode CMap -> dict of code(int)->str"""
    cmap = {}
    for blk in re.findall(rb'beginbfchar(.*?)endbfchar', txt, re.S):
        for a, b in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', blk):
            src = int(a, 16)
            dsth = b.decode('ascii')
            s = ''.join(chr(int(dsth[i:i+4], 16)) for i in range(0, len(dsth), 4))
            try:
                s = codecs.decode(bytes.fromhex(dsth), 'utf-16-be')
            except Exception:
                pass
            cmap[src] = s
    for blk in re.findall(rb'beginbfrange(.*?)endbfrange', txt, re.S):
        for a, b, c in re.findall(rb'<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>', blk):
            lo, hi, dst = int(a, 16), int(b, 16), int(c, 16)
            for i in range(lo, min(hi, lo + 65535) + 1):
                try:
                    cmap[i] = chr(dst + (i - lo))
                except Exception:
                    pass
    return cmap

def main(path, want_pages=None):
    data = load(path)
    objs = find_objects(data)
    # page objects in order
    pages = []
    for num, body in objs.items():
        if re.search(rb'/Type\s*/Page\b', body) and not re.search(rb'/Type\s*/Pages\b', body):
            pages.append((num, body))
    # order pages by /Kids tree if possible, else by object number
    kid_order = []
    for num, body in objs.items():
        if re.search(rb'/Type\s*/Pages\b', body):
            for k in re.findall(rb'(\d+)\s+\d+\s+R', body[body.find(b'/Kids'):body.find(b'/Kids')+4000] if b'/Kids' in body else b''):
                kid_order.append(int(k))
    pagenums = [n for n in kid_order if any(n == p[0] for p in pages)]
    if not pagenums:
        pagenums = sorted(n for n, _ in pages)
    print('TOTAL_PAGES=%d' % len(pagenums))
    bodymap = dict(pages)
    for idx, pnum in enumerate(pagenums, start=1):
        if want_pages and idx not in want_pages:
            continue
        body = bodymap[pnum]
        # font cmaps for this page
        cmaps = {}
        res = body
        for fm in re.finditer(rb'/(F\d+|TT\d+|C2_\d+|[A-Za-z0-9#]+)\s+(\d+)\s+\d+\s+R', res):
            fo = int(fm.group(2))
            fb = objs.get(fo, b'')
            tm = re.search(rb'/ToUnicode\s+(\d+)\s+\d+\s+R', fb)
            if tm:
                cs = get_stream(objs.get(int(tm.group(1)), b''))
                if cs:
                    cmaps[fm.group(1).decode('latin1')] = parse_cmap(cs)
        cont = []
        cm = re.search(rb'/Contents\s+(\d+)\s+\d+\s+R', body)
        if cm:
            cont.append(int(cm.group(1)))
        else:
            cm2 = re.search(rb'/Contents\s*\[([^\]]*)\]', body)
            if cm2:
                cont = [int(x) for x in re.findall(rb'(\d+)\s+\d+\s+R', cm2.group(1))]
        buf = b''
        for c in cont:
            s = get_stream(objs.get(c, b''))
            if s:
                buf += s + b'\n'
        out = []
        curfont = None
        for m in re.finditer(rb'/([A-Za-z0-9#]+)\s+[\d.]+\s+Tf|<([0-9A-Fa-f]+)>\s*Tj|\(((?:[^()\\]|\\.)*)\)\s*Tj|\[(.*?)\]\s*TJ|(T\*|ET)', buf, re.S):
            if m.group(1):
                curfont = m.group(1).decode('latin1')
            elif m.group(2):
                h = m.group(2).decode('ascii')
                cmp_ = cmaps.get(curfont, {})
                t = ''
                for i in range(0, len(h) - 1, 4):
                    code = int(h[i:i+4], 16)
                    t += cmp_.get(code, '')
                out.append(t)
            elif m.group(3) is not None:
                out.append(m.group(3).decode('latin1'))
            elif m.group(4):
                seg = m.group(4)
                cmp_ = cmaps.get(curfont, {})
                t = ''
                for hm in re.finditer(rb'<([0-9A-Fa-f]+)>|\(((?:[^()\\]|\\.)*)\)', seg):
                    if hm.group(1):
                        h = hm.group(1).decode('ascii')
                        for i in range(0, len(h) - 1, 4):
                            t += cmp_.get(int(h[i:i+4], 16), '')
                    else:
                        t += hm.group(2).decode('latin1')
                out.append(t)
            else:
                out.append('\n')
        txt = ''.join(out)
        txt = re.sub(r'\n{3,}', '\n\n', txt)
        print('=== PAGE %d (obj %d) ===' % (idx, pnum))
        print(txt.strip())

if __name__ == '__main__':
    p = sys.argv[1]
    wp = None
    if len(sys.argv) > 2:
        wp = set()
        for part in sys.argv[2].split(','):
            if '-' in part:
                a, b = part.split('-')
                wp.update(range(int(a), int(b) + 1))
            else:
                wp.add(int(part))
    main(p, wp)
