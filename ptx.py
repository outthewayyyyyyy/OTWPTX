"""Read a Pro Tools .ptx session and package it for a mix engineer.

Decryption is ported from ptformat (https://github.com/zamaudio/ptformat, LGPL-2.1+).
"""
import os
import struct
import sys
import unicodedata
import zipfile

AUDIO_EXT = ('.wav', '.aif', '.aiff', '.mxf')
SKIP_DIRS = {'Session File Backups'}


def decrypt(data):
    """Return the decrypted session bytes, or None if the format is unknown."""
    if len(data) < 0x14:
        return None
    xor_type, xor_value = data[0x12], data[0x13]
    if xor_type == 0x01:    # PT 5-9
        mul, neg = 53, False
    elif xor_type == 0x05:  # PT 10+
        mul, neg = 11, True
    else:
        return None
    delta = next((i for i in range(256) if (i * mul) & 0xff == xor_value), 0)
    if neg:
        delta = -delta & 0xff
    key = bytes((i * delta) & 0xff for i in range(256))
    out = bytearray(data)
    if xor_type == 0x01:
        for i in range(0x14, len(out)):
            out[i] ^= key[i & 0xff]
    else:
        # key byte changes every 4096 bytes, so xor whole chunks at once
        for start in [0x14] + list(range(0x1000, len(out), 0x1000)):
            end = min((start | 0xfff) + 1, len(out))
            k = key[(start >> 12) & 0xff]
            out[start:end] = out[start:end].translate(bytes(i ^ k for i in range(256)))
    return bytes(out)


def _blocks(b, pos, end):
    """Yield (content_type, body_start, body_end) for blocks at one level."""
    while pos + 9 <= end:
        if b[pos] != 0x5a:
            pos += 1
            continue
        size, ctype = struct.unpack_from('<IH', b, pos + 3)
        if size < 2 or pos + 7 + size > end:
            pos += 1
            continue
        yield ctype, pos + 9, pos + 7 + size
        pos += 7 + size


def _s(raw):
    try:
        return unicodedata.normalize('NFC', raw.decode('utf-8'))
    except UnicodeDecodeError:
        return raw.decode('latin-1')


def file_table(plain):
    """Parse the audio file table (block 0x1004 > 0x103a).

    Returns (files, session_path): files is a list of (name, original_dir_parts),
    session_path is the parts of the folder the session was saved in.
    Each table entry is <u8 kind><u32 parent><u32 len><name><4cc>;
    kind 0 = volume, 1 = folder, 2 = file.
    """
    for ct, s, e in _blocks(plain, 0x14, len(plain)):
        if ct != 0x1004:
            continue
        for ct2, s2, e2 in _blocks(plain, s, e):
            if ct2 != 0x103a:
                continue
            count, = struct.unpack_from('<I', plain, s2)
            pos, entries = s2 + 4, []
            for _ in range(count):
                kind, parent, n = struct.unpack_from('<BII', plain, pos)
                pos += 9
                entries.append((kind, parent, _s(plain[pos:pos + n])))
                pos += n + 4
                if pos > e2:
                    raise ValueError('file table overruns its block')

            def path(i):
                parts = []
                while 0 <= i < len(entries) and len(parts) < 64:
                    parts.append(entries[i][2])
                    i = entries[i][1]
                return parts[::-1]

            files, seen = [], set()
            for kind, parent, name in entries:
                if kind == 2 and name.lower().endswith(AUDIO_EXT) and name not in seen:
                    seen.add(name)
                    files.append((name, path(parent)))
            # the session folder is the one 'Audio Files' sits in
            session = next((path(p) for k, p, n in entries if k == 1 and n == 'Audio Files'), [])
            return files, session
    raise ValueError('no audio file table found')


def _real_path(parts):
    """Turn stored [volume, folder, ...] into a path on this computer."""
    if not parts:
        return None
    vol, rest = parts[0], parts[1:]
    if os.name == 'nt':
        root = vol if vol.endswith(('\\', ':')) else None
        return os.path.join(root, *rest) if root else None
    # /Volumes/<boot disk> is a link to / on macOS
    return os.path.join('/Volumes', vol, *rest)


def _index(folder, skip=SKIP_DIRS):
    """Map NFC filename -> path for every file under folder."""
    found = {}
    for root, dirs, names in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in skip and not d.startswith('.')]
        for n in names:
            found.setdefault(unicodedata.normalize('NFC', n), os.path.join(root, n))
    return found


def resolve(session_dir, files, session_parts, extra_dirs=()):
    """Find each audio file on disk. Returns (found {name: path}, missing [names])."""
    audio_dir = os.path.join(session_dir, 'Audio Files')
    local = _index(audio_dir) if os.path.isdir(audio_dir) else {}
    whole = None
    extra = [_index(d, skip=()) for d in extra_dirs]
    found, missing = {}, []
    for name, parts in files:
        cands = []
        # stored relative to the session folder (session may have moved)
        n = len(session_parts)
        if session_parts and parts[:n] == session_parts:
            cands.append(os.path.join(session_dir, *parts[n:], name))
        cands.append(local.get(name))
        real = _real_path(parts)
        if real:
            cands.append(os.path.join(real, name))
        hit = next((c for c in cands if c and os.path.isfile(c)), None)
        if not hit:
            if whole is None:
                whole = _index(session_dir)
            # ponytail: name-only match outside the stored path; add size/length check if wrong files get picked
            hit = whole.get(name) or next((x[name] for x in extra if name in x), None)
        if hit:
            found[name] = hit
        else:
            missing.append(name)
    return found, missing


def scan(ptx_path, extra_dirs=()):
    """Return (found, missing, ok). ok=False means the session couldn't be read
    and found holds the whole Audio Files folder instead."""
    session_dir = os.path.dirname(os.path.abspath(ptx_path))
    with open(ptx_path, 'rb') as f:
        plain = decrypt(f.read())
    try:
        if plain is None:
            raise ValueError('unknown encryption')
        files, session_parts = file_table(plain)
        if not files:
            raise ValueError('no audio files listed')
    except (ValueError, struct.error):
        audio_dir = os.path.join(session_dir, 'Audio Files')
        allf = _index(audio_dir) if os.path.isdir(audio_dir) else {}
        return {k: v for k, v in allf.items() if not k.startswith('.')}, [], False
    found, missing = resolve(session_dir, files, session_parts, extra_dirs)
    return found, missing, True


def build_zip(ptx_path, found, out_path, progress=lambda done, total: None):
    """Write <Session>/<Session>.ptx, Audio Files/ and Bounced Files/ into a zip."""
    session_dir = os.path.dirname(os.path.abspath(ptx_path))
    top = os.path.splitext(os.path.basename(ptx_path))[0]
    items = [(ptx_path, f'{top}/{os.path.basename(ptx_path)}')]
    items += [(p, f'{top}/Audio Files/{name}') for name, p in sorted(found.items())]
    bounced = os.path.join(session_dir, 'Bounced Files')
    for rel_name, p in sorted(_index(bounced, skip=()).items()) if os.path.isdir(bounced) else []:
        rel = os.path.relpath(p, bounced).replace(os.sep, '/')
        items.append((p, f'{top}/Bounced Files/{rel}'))
    total = sum(os.path.getsize(p) for p, _ in items) or 1
    done, tmp = 0, out_path + '.part'
    try:
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_STORED, allowZip64=True) as z:
            for src, arc in items:
                with open(src, 'rb') as fi, z.open(arc, 'w', force_zip64=True) as fo:
                    while chunk := fi.read(1 << 20):
                        fo.write(chunk)
                        done += len(chunk)
                        progress(done, total)
        os.replace(tmp, out_path)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


if __name__ == '__main__':
    # self-check: python ptx.py <session.ptx> ...
    for p in sys.argv[1:]:
        found, missing, ok = scan(p)
        print(f'{os.path.basename(p)}: ok={ok} found={len(found)} missing={len(missing)} {missing[:5]}')
        assert ok, 'session could not be read'
        assert 'com.wav' not in found
        if p.endswith('j1hunnit side missions 1.ptx'):
            assert len(found) == 204, len(found)  # 209 on disk, 5 unused
            assert not {'INPUT_114.wav', 'INPUT_140.wav', 'INPUT_208.wav'} & set(found)
    print('ok')
