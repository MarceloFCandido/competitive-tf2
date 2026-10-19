#!/usr/bin/env python3
"""Reversible TF2 setup and incremental updates for Bazzite/Linux (Python 3.9+).

Run as your normal user in Desktop Mode, with TF2 and Steam fully exited.
No sudo, pip, package installs, Steam-account edits, or OS tuning.
Downloads only pinned upstream game data; never executes downloaded programs.

Already applied an earlier version? Use:
    python3 setup_tf2_bazzite.py --update-only --dry-run --visual-clarity --hud rayshud --replace-hud
    python3 setup_tf2_bazzite.py --update-only --visual-clarity --hud rayshud --replace-hud

Other examples:
    python3 setup_tf2_bazzite.py --update-only --viewmodels hidden --dry-run
    python3 setup_tf2_bazzite.py --update-only --viewmodels minimal
    python3 setup_tf2_bazzite.py --update-only --hud budhud --replace-hud
    python3 setup_tf2_bazzite.py --dry-run
    python3 setup_tf2_bazzite.py --preset low --fps-cap 240
    python3 setup_tf2_bazzite.py --tf2-dir '/path/to/Team Fortress 2'
    python3 setup_tf2_bazzite.py --restore '/path/printed/after/apply'

Update behavior:
    Existing script-managed installations automatically use incremental mode.
    --update-only additionally refuses to run without a recognized installation.
    Unspecified settings stay as they are: no preset/FPS reset, base redownload,
    class-config migration, or changes to binds, sensitivity, or Steam settings.
    Only explicitly requested keys are edited. Repeated settings are no-ops.
    Ambiguous duplicate/scripted settings in edited files cause a safe stop.
    Arbitrary class scripts, other mods and in-game binds are not rewritten;
    they can still override these settings. Review warnings and test in-game.

Visual options:
    --visual-clarity reduces cosmetic motion, first-person tracers, Pyrovision
    vignette, bloom/HDR and the 3D HUD portrait. It PRESERVES the effects module:
    it never raises your existing low/very_low particle/impact-effects setting.
    --viewmodels hidden hides your first-person weapon/hands and their visual
    firing/reload animations. Timing, camera recoil and screen shake remain.
    Without --viewmodels, updates preserve your current weapon visibility/FOV.
    No replacement animation/particle mods or sv_cheats commands are installed.
    Not every flame, explosion, flash or status overlay can be disabled.

HUDs:
    --hud rayshud or --hud budhud installs one pinned, checksum-verified HUD.
    --replace-hud permits backing up/replacing detected existing HUDs, including
    a customized copy of the chosen HUD. Otherwise conflicts stop installation.
    Bundled cfg/valve.rc files are excluded to preserve your startup/settings;
    this also omits their automatic HUD-specific tweaks (e.g. menu dimmer fix).
    Detection is conservative; arbitrary packed/renamed mods may go undetected.

Dry runs never download, write game files, or create backups. Incremental dry
runs show config diffs and planned HUD replacements. Backups from older script
versions remain restorable. The program prints an undo command after changes.

Sources checked 2026-10-18:
    https://docs.comfig.app/latest/setup/install/
    https://docs.comfig.app/latest/customization/custom_configs/
    https://docs.comfig.app/latest/customization/modules/
    https://docs.comfig.app/latest/tf2/cvarlist_linux/
    https://github.com/ValveSoftware/source-sdk-2013/blob/master/src/game/client/viewrender.cpp
    https://github.com/mastercomfig/mastercomfig/releases/tag/9.100.1
    https://github.com/raysfire/rayshud/releases/tag/2026.0111
    https://github.com/raysfire/rayshud/blob/2026.0111/cfg/valve.rc
    https://github.com/rbjaxter/budhud/releases/tag/2511_01
    https://github.com/rbjaxter/budhud/blob/2511_01/cfg/valve.rc
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import stat
import struct
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile

SCRIPT_VERSION = '1.2.0'

COMFIG = {
    'version': '9.100.1',
    'url': 'https://github.com/mastercomfig/mastercomfig/releases/download/9.100.1/mastercomfig-base.vpk',
    'sha256': 'cdabc8251864a1ab2ef7f7ffed1b44f52810956e476d62183b8d7e3e960d8650',
}
BUDHUD = {
    'version': '2511_01',
    'url': 'https://github.com/rbjaxter/budhud/releases/download/2511_01/budhud.zip',
    'sha256': 'f42f2af1d6469c80a01f093930a0db32f901e0a03bad5aaa1dbe7e17749335c2',
}
RAYSHUD = {
    'version': '2026.0111',
    'url': 'https://github.com/raysfire/rayshud/releases/download/2026.0111/rayshud.zip',
    'sha256': '09c695faa1243d649dff5636d1ccb0c831a6f4f6d118380b2e40d451f6dbd014',
}
HUDS = {'budhud': BUDHUD, 'rayshud': RAYSHUD}
HUD_MARKER = '.tf2-competitive-setup-hud.json'
HUD_POLICY = 'preserve-startup-v1'
MANAGED_FILES = ('cfg/overrides/setup_hook.cfg', 'cfg/overrides/autoexec.cfg',
                 'cfg/overrides/modules.cfg')
FPS_CAPS = ('60', '75', '120', '144', '160', '165', '180', '200', '240',
            '300', '360', '400', '1000')
MIGRATE = ('autoexec.cfg', 'listenserver.cfg', 'scout.cfg', 'soldier.cfg',
           'pyro.cfg', 'demoman.cfg', 'heavyweapons.cfg', 'engineer.cfg',
           'medic.cfg', 'sniper.cfg', 'spy.cfg', 'modules.cfg')
BEGIN = '// BEGIN TF2-COMPETITIVE-SETUP'
END = '// END TF2-COMPETITIVE-SETUP'
LAUNCH = '-novid -nojoy -nosteamcontroller -nohltv -particles 1'
PERSONAL_COMMON = '''// No sensitivity or keybind changes.
m_rawinput 1
m_customaccel 0
m_filter 0
hud_fastswitch 1
cl_autoreload 1

// Damage numbers and built-in hit/kill feedback.
hud_combattext 1
hud_combattext_batching 1
hud_combattext_batching_window 0.2
tf_dingalingaling 1
tf_dingalingaling_lasthit 1

// Medic convenience; these do not change your attack binds.
tf_medigun_autoheal 1
hud_medichealtargetmarker 1
hud_medicautocallers 1
hud_medicautocallersthreshold 75

con_enable 1
echo "TF2 competitive baseline loaded"
'''

# Deliberately leave the effects module alone. Raising Low to Medium would
# re-enable impact cues/particles; the user requested an additive update.
# These descriptions are upstream intentions, not guarantees for every effect.
CLARITY_MODULES = (
    ('tracers', 'low', 'Hide first-person bullet tracers (not all world/projectile trails)'),
    ('post_processing', 'off', 'Disable standard bloom/HDR post-processing'),
    ('pyrovision', 'low', 'Remove Pyrovision vignette and depth-of-field effects, not all Pyroland assets'),
    ('jigglebones', 'off', 'Disable cosmetic cloth/item jiggle physics'),
    ('sheens_speed', 'off', 'Stop updating killstreak weapon sheen animation'),
    ('hud_player_model', 'off', 'Disable the live 3D class portrait in the HUD'),
)



class SetupError(Exception):
    """An actionable failure, shown without a Python traceback."""


def warn(message: str) -> None:
    print('WARNING: ' + message, file=sys.stderr)


def exists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def assert_plain(path: Path) -> None:
    """Never follow dotfile symlinks, devices, or FIFOs during backup/edit."""
    if not exists(path):
        return
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        raise SetupError(f'Symlink requires manual handling; nothing will follow it: {path}')
    if stat.S_ISDIR(mode):
        for child in path.iterdir():
            assert_plain(child)
    elif not stat.S_ISREG(mode):
        raise SetupError(f'Not an ordinary file or directory: {path}')


def target_path(tf: Path, rel: str) -> Path:
    """Allow only paths in tf/cfg or tf/custom; reject symlink ancestors."""
    p = PurePosixPath(rel)
    if (p.is_absolute() or not p.parts or '..' in p.parts or '\\' in rel
            or p.parts[0] not in ('cfg', 'custom') or p == PurePosixPath('custom')):
        raise SetupError(f'Unsafe target in operation/backup: {rel!r}')
    current = tf
    for part in p.parts:
        current = current / part
        if current.is_symlink():
            raise SetupError(f'Symlink requires manual handling: {current}')
    return current


def validate_game(game: Path) -> Path:
    game = game.expanduser().resolve()
    if game.name == 'tf' and (game / 'gameinfo.txt').is_file():
        game = game.parent
    tf = game / 'tf'
    if tf.is_symlink() or not (tf / 'gameinfo.txt').is_file():
        raise SetupError(f'Not a TF2 installation (expected tf/gameinfo.txt): {game}')
    return game


def vdf_values(text: str, key: str) -> list[str]:
    """Read quoted scalar fields, not modify Steam's VDF files."""
    # Strip line comments outside quoted strings; preserve URLs inside strings.
    text = re.sub(r'"(?:\\.|[^"\\])*"|//[^\r\n]*',
                  lambda m: '' if m.group().startswith('//') else m.group(), text)
    values = re.findall(r'"' + re.escape(key) + r'"\s*"((?:\\.|[^"\\])*)"',
                        text, flags=re.I)
    return [re.sub(r'\\([\\"])', r'\1', value) for value in values]


def discover_games(home: Path | None = None) -> list[Path]:
    home = home or Path.home()
    roots = [home / '.local/share/Steam', home / '.steam/steam', home / '.steam/root',
             home / '.var/app/com.valvesoftware.Steam/.local/share/Steam',
             home / '.var/app/com.valvesoftware.Steam/data/Steam']
    if home == Path.home() and os.environ.get('XDG_DATA_HOME'):
        roots.append(Path(os.environ['XDG_DATA_HOME']) / 'Steam')
    libraries = {root.resolve() for root in roots if root.is_dir()}
    for root in list(libraries):
        for vdf in (root / 'steamapps/libraryfolders.vdf', root / 'config/libraryfolders.vdf'):
            if vdf.is_file():
                text = vdf.read_text(encoding='utf-8-sig', errors='surrogateescape')
                paths = vdf_values(text, 'path')
                # Support the older libraryfolders.vdf layout as well.
                paths += re.findall(r'"\d+"\s*"(/[^"\r\n]+)"', text)
                libraries.update(Path(p).expanduser().resolve() for p in paths if p.startswith('/'))
    found = set()
    for lib in libraries:
        manifest = lib / 'steamapps/appmanifest_440.acf'
        names = ['Team Fortress 2']
        if manifest.is_file():
            names = vdf_values(manifest.read_text(encoding='utf-8-sig',
                                                  errors='surrogateescape'), 'installdir') or names
        for name in names:
            if Path(name).name != name or name in ('.', '..'):
                continue
            game = lib / 'steamapps/common' / name
            if (game / 'tf/gameinfo.txt').is_file():
                found.add(game.resolve())
    return sorted(found)


def require_closed() -> None:
    names = {'steam', 'steamwebhelper', 'hl2_linux', 'tf_linux', 'tf_linux64',
             'hl2.exe', 'tf_win64.exe', 'tf.exe'}
    running = set()
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():
            continue
        try:
            if entry.stat().st_uid == os.getuid():
                name = (entry / 'comm').read_text().strip().lower()
                if name in names:
                    running.add(name)
        except (OSError, UnicodeError):
            continue
    if running:
        raise SetupError('Fully exit TF2 and Steam (Steam menu > Exit), then retry. '
                         'Still running: ' + ', '.join(sorted(running)))


def strip_managed(text: str) -> str:
    if text.count(BEGIN) != text.count(END) or text.count(BEGIN) > 1:
        raise SetupError('An existing config has malformed/duplicate managed-block markers.')
    if BEGIN in text and text.index(END) < text.index(BEGIN):
        raise SetupError('An existing config has reversed managed-block markers.')
    return re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END), '', text, flags=re.S).rstrip()


def read_cfg(path: Path) -> str:
    return path.read_bytes().decode('utf-8-sig', errors='surrogateescape') if path.is_file() else ''


def managed_file(path: Path, body: str) -> None:
    old = strip_managed(read_cfg(path))
    result = (old + '\n\n' if old else '') + BEGIN + '\n' + body.rstrip() + '\n' + END + '\n'
    path.write_bytes(result.encode('utf-8', errors='surrogateescape'))


def personal_config(viewmodels: str = 'minimal') -> str:
    """Generate a render-only weapon choice; never bind keys or change timing."""
    if viewmodels not in ('minimal', 'hidden'):
        raise SetupError('Unknown viewmodel mode: ' + viewmodels)
    visible = int(viewmodels == 'minimal')
    comment = ('// World FOV and minimal, visible first-person weapon.' if visible else
               '// World FOV; hide first-person weapon/hands and their animations.\n'
               '// This only hides rendering; firing, reload timing and camera movement remain.')
    return (comment + '\n'
            'fov_desired 90\n'
            'viewmodel_fov 70\n'
            'tf_use_min_viewmodels 1\n'
            f'r_drawviewmodel {visible}\n\n' + PERSONAL_COMMON)


def module_config(cap: str, visual_clarity: bool = False) -> str:
    body = f'''motion_blur=off
vsync=off
ragdolls=off
gibs=off
anti_aliasing=off
packet_rate=standard
snapshot_buffer=auto
fpscap={cap}
'''
    if visual_clarity:
        body += '\n// Optional visual clarity. Some effects may ignore these settings.\n'
        for name, value, description in CLARITY_MODULES:
            body += f'// {description}.\n{name}={value}\n'
    return body


def stage_cfg(tf: Path, dest: Path, preset: str, cap: str,
              visual_clarity: bool = False, viewmodels: str = 'minimal') -> None:
    cfg = tf / 'cfg'
    assert_plain(cfg)
    if cfg.exists():
        shutil.copytree(cfg, dest)
    else:
        dest.mkdir()
    overrides = dest / 'overrides'
    overrides.mkdir(exist_ok=True)
    for name in MIGRATE:
        src, dst = dest / name, overrides / name
        if not src.is_file():
            continue
        a, b = strip_managed(read_cfg(src)), strip_managed(read_cfg(dst))
        if a and a.strip() != b.strip():
            text = '// Migrated from tf/cfg/' + name + '\n' + a + '\n'
            if b:
                text += '\n// Existing override follows.\n' + b + '\n'
        else:
            text = b + '\n'
        dst.write_bytes(text.encode('utf-8', errors='surrogateescape'))
        src.unlink()  # Only deletes the staged copy; the real original is backed up.
    managed_file(overrides / 'setup_hook.cfg', f'preset={preset}')
    managed_file(overrides / 'autoexec.cfg', personal_config(viewmodels))
    managed_file(overrides / 'modules.cfg', module_config(cap, visual_clarity))



def download(asset: dict, dest: Path, maximum: int) -> None:
    print(f"Downloading {dest.name} (pinned upstream release {asset['version']})...", flush=True)
    req = urllib.request.Request(asset['url'], headers={'User-Agent': 'tf2-competitive-setup/' + SCRIPT_VERSION})
    digest = hashlib.sha256()
    total = 0
    try:
        with urllib.request.urlopen(req, timeout=40) as response, dest.open('wb') as output:
            if urllib.parse.urlparse(response.geturl()).scheme != 'https':
                raise SetupError('Refusing a non-HTTPS download redirect.')
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > maximum:
                    raise SetupError('Download exceeds the expected size limit.')
                output.write(chunk)
                digest.update(chunk)
    except (OSError, urllib.error.URLError) as exc:
        raise SetupError(f'Download failed; check your connection and retry. {exc}') from exc
    if digest.hexdigest() != asset['sha256']:
        raise SetupError(f'SHA-256 mismatch for {dest.name}; refusing to install it.')
    print('  SHA-256 verified.')


def validate_vpk(path: Path) -> None:
    with path.open('rb') as stream:
        header = stream.read(12)
    if len(header) != 12:
        raise SetupError('Truncated VPK.')
    magic, version, tree_length = struct.unpack('<III', header)
    header_length = 28 if version == 2 else 12
    if magic != 0x55AA1234 or version not in (1, 2) or path.stat().st_size < header_length + tree_length:
        raise SetupError('Invalid VPK header; refusing to install.')


def extract_hud(archive: Path, dest: Path) -> Path:
    """Extract data without trusting ZIP paths, symlinks, or oversized archives."""
    dest.mkdir()
    with zipfile.ZipFile(archive) as zf:
        items = zf.infolist()
        if len(items) > 20000 or sum(i.file_size for i in items) > 200 * 1024 * 1024:
            raise SetupError('Unexpectedly large HUD archive.')
        for item in items:
            p = PurePosixPath(item.filename)
            mode = item.external_attr >> 16
            if (p.is_absolute() or '..' in p.parts or '\\' in item.filename
                    or (stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR))
                    or item.flag_bits & 1):
                raise SetupError('Unsafe HUD archive member: ' + item.filename)
            if not p.parts:
                continue
            out = dest.joinpath(*p.parts)
            if item.is_dir():
                out.mkdir(parents=True, exist_ok=True)
            else:
                out.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(item) as src, out.open('xb') as dst:
                    shutil.copyfileobj(src, dst)
    roots = [p.parent for p in dest.rglob('info.vdf')
             if (p.parent / 'resource').is_dir() and (p.parent / 'scripts').is_dir()]
    if len(roots) != 1:
        raise SetupError('Cannot uniquely identify the HUD root in this archive.')
    return roots[0]


def copy_item(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)


def remove_item(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif exists(path):
        path.unlink()


def tree_hash(path: Path, ignore_root: tuple[str, ...] = ()) -> str:
    h = hashlib.sha256()
    if path.is_dir():
        for entry in sorted(path.rglob('*')):
            if entry.relative_to(path).parts[0] in ignore_root:
                continue
            rel = entry.relative_to(path).as_posix().encode('utf-8', errors='surrogateescape')
            h.update((b'D' if entry.is_dir() else b'F') + rel + b'\0')
            if entry.is_file():
                with entry.open('rb') as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                        h.update(chunk)
    else:
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(chunk)
    return h.hexdigest()


def save_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def transact(tf: Path, ops: dict[str, Path | None], state: Path, label: str) -> Path:
    """Back up every affected item before the first game-file change."""
    keys = list(ops)
    for rel in keys:
        target = target_path(tf, rel)
        assert_plain(target)
        if ops[rel] is not None:
            assert_plain(ops[rel])
        if any(other != rel and other.startswith(rel + '/') for other in keys):
            raise SetupError('Overlapping transaction targets.')
    stamp = dt.datetime.now().strftime('%Y%m%d-%H%M%S-')
    backup = Path(tempfile.mkdtemp(prefix=stamp + label + '-', dir=state))
    manifest = {'format': 'tf2-competitive-setup-v1', 'tf': str(tf),
                'status': 'backing-up', 'label': label, 'entries': []}
    for rel in keys:
        target = target_path(tf, rel)
        entry = {'path': rel, 'existed': target.exists()}
        if target.exists():
            saved = backup / 'originals' / rel
            copy_item(target, saved)
            entry['sha256'] = tree_hash(saved)
        manifest['entries'].append(entry)
    manifest['status'] = 'backed-up'
    save_json(backup / 'manifest.json', manifest)
    print('Backup: ' + str(backup), flush=True)
    touched = []
    try:
        for rel, source in ops.items():
            touched.append(rel)
            target = target_path(tf, rel)
            remove_item(target)
            if source is not None:
                copy_item(source, target)
        manifest['status'] = 'complete'
        save_json(backup / 'manifest.json', manifest)
    except BaseException:
        warn('Applying changes failed. Attempting rollback from ' + str(backup))
        try:
            for rel in reversed(touched):
                target = target_path(tf, rel)
                remove_item(target)
                saved = backup / 'originals' / rel
                if saved.exists():
                    copy_item(saved, target)
            manifest['status'] = 'rolled-back'
            save_json(backup / 'manifest.json', manifest)
        except BaseException as exc:
            warn(f'Rollback could not finish: {exc}. Keep the backup for recovery.')
        raise
    return backup


def load_restore(backup: Path) -> tuple[Path, dict[str, Path | None]]:
    assert_plain(backup)
    m = json.loads((backup / 'manifest.json').read_text(encoding='utf-8'))
    if m.get('format') != 'tf2-competitive-setup-v1' or m.get('status') == 'backing-up':
        raise SetupError('Not a complete backup from this script.')
    tf = validate_game(Path(m['tf']).parent) / 'tf'
    if str(tf) != m['tf'] or not m.get('entries'):
        raise SetupError('Backup installation path is invalid or has moved.')
    ops = {}
    for entry in m['entries']:
        rel = entry['path']
        target_path(tf, rel)
        if rel in ops or type(entry.get('existed')) is not bool:
            raise SetupError('Invalid backup entry.')
        saved = backup / 'originals' / rel
        if entry['existed']:
            if not saved.exists() or tree_hash(saved) != entry['sha256']:
                raise SetupError(f'Backup missing or changed: {saved}')
            ops[rel] = saved
        else:
            ops[rel] = None
    return tf, ops


def old_presets(tf: Path) -> list[Path]:
    custom = tf / 'custom'
    if not custom.is_dir():
        return []
    return sorted(p for p in custom.iterdir()
                  if re.fullmatch(r'mastercomfig-[\w.-]+-preset(?:_dir)?\.vpk', p.name))


def confirm(yes: bool) -> bool:
    if yes:
        return True
    if not sys.stdin.isatty():
        raise SetupError('Run interactively, or use --yes after reviewing --dry-run.')
    return input('Apply these changes? [y/N] ').strip().lower() in ('y', 'yes')



def active_line(line: str) -> str:
    """Strip // comments, respecting quoted strings; never evaluate CFG code."""
    quoted = escaped = False
    for i, char in enumerate(line):
        if escaped:
            escaped = False
        elif char == '\\' and quoted:
            escaped = True
        elif char == '"':
            quoted = not quoted
        elif not quoted and line[i:i + 2] == '//':
            return line[:i]
    return line.rstrip('\r\n')


def managed_bounds(text: str, label: str) -> tuple[list[str], int, int]:
    """Recognize the old and new script's exact, single managed block."""
    lines = text.splitlines(keepends=True)
    begin = [i for i, line in enumerate(lines) if line.strip() == BEGIN]
    end = [i for i, line in enumerate(lines) if line.strip() == END]
    if (len(begin) != 1 or len(end) != 1 or begin[0] >= end[0]
            or text.count(BEGIN) != 1 or text.count(END) != 1):
        raise SetupError(f'{label}: missing, duplicate, or malformed managed markers. '
                         'No incremental changes will be guessed.')
    return lines, begin[0], end[0]


def recognized_install(tf: Path) -> bool:
    """Partial script installations are errors, not invitations to overwrite."""
    texts = [read_cfg(target_path(tf, rel)) for rel in MANAGED_FILES]
    if not any(BEGIN in text or END in text for text in texts):
        return False
    for rel, text in zip(MANAGED_FILES, texts):
        managed_bounds(text, rel)
    base = target_path(tf, 'custom/mastercomfig-base.vpk')
    assert_plain(base)
    if not base.is_file():
        raise SetupError('Managed settings exist but mastercomfig-base.vpk is missing. '
                         'Restore it before applying an incremental update.')
    validate_vpk(base)
    if old_presets(tf):
        raise SetupError('Both the managed base and old preset VPKs exist. '
                         'Resolve that existing mastercomfig conflict first.')
    return True


def scalar_occurrences(text: str, key: str, sep: str, label: str) -> list[tuple[int, re.Match]]:
    """Accept only one simple unconditional definition, anywhere in the file.

    Refuse alias/bind/semicolon expressions involving the requested key instead
    of silently overriding them. Untargeted commands remain byte-for-byte intact.
    """
    boundary = re.compile(r'(?<![\w])' + re.escape(key) + r'(?![\w])', re.I)
    between = '=' if sep == '=' else r'[ \t]+'
    pattern = re.compile(r'(?P<prefix>[ \t]*' + re.escape(key) + between + r')'
                         r'(?P<value>"?[\w.+-]+"?)(?P<space>[ \t]*)$', re.I)
    found = []
    for i, line in enumerate(text.splitlines(keepends=True)):
        active = active_line(line)
        if not boundary.search(active):
            continue
        match = pattern.fullmatch(active)
        if match is None:
            raise SetupError(f'{label}:{i + 1}: scripted or ambiguous use of {key}. '
                             'Resolve it manually; no files have been changed.')
        found.append((i, match))
    if len(found) > 1:
        raise SetupError(f'{label}: multiple active definitions of {key}. '
                         'Resolve this existing conflict first; no files have been changed.')
    return found


def patch_scalar(text: str, key: str, value: str, sep: str, label: str) -> str:
    lines, _, end = managed_bounds(text, label)
    matches = scalar_occurrences(text, key, sep, label)
    if matches:
        index, match = matches[0]
        old = match.group('value')
        if old.strip('"') == value:
            return text
        replacement = '"' + value + '"' if old.startswith('"') else value
        # Replace only the value, preserving comments, whitespace and line ends.
        line = lines[index]
        lines[index] = line[:match.start('value')] + replacement + line[match.end('value'):]
    else:
        newline = '\r\n' if lines[end].endswith('\r\n') else '\n'
        lines.insert(end, key + sep + value + newline)
    return ''.join(lines)


def plan_update(tf: Path, args: argparse.Namespace) -> dict[str, bytes]:
    """Build a delta in memory; no downloads, temporary files or disk writes."""
    originals = {rel: target_path(tf, rel).read_bytes() for rel in MANAGED_FILES}
    texts = {rel: data.decode('utf-8', errors='surrogateescape') for rel, data in originals.items()}
    # A UTF-8 BOM cannot occur at the managed marker in an old-script file.
    # Preserve it and all other existing bytes on update.
    edits: dict[str, list[tuple[str, str, str]]] = {}
    if args.preset is not None:
        edits.setdefault(MANAGED_FILES[0], []).append(('preset', args.preset, '='))
    if args.fps_cap is not None:
        edits.setdefault(MANAGED_FILES[2], []).append(('fpscap', args.fps_cap, '='))
    if args.visual_clarity:
        edits.setdefault(MANAGED_FILES[2], []).extend((key, value, '=')
                                                     for key, value, _ in CLARITY_MODULES)
    if args.viewmodels is not None:
        edits.setdefault(MANAGED_FILES[1], []).append(
            ('r_drawviewmodel', '0' if args.viewmodels == 'hidden' else '1', ' '))
        if args.viewmodels == 'minimal':
            edits[MANAGED_FILES[1]].append(('tf_use_min_viewmodels', '1', ' '))
    changed = {}
    for rel, operations in edits.items():
        text = texts[rel]
        for key, value, sep in operations:
            text = patch_scalar(text, key, value, sep, rel)
        data = text.encode('utf-8', errors='surrogateescape')
        if data != originals[rel]:
            changed[rel] = data
    return changed


def warn_other_scripts(tf: Path, args: argparse.Namespace) -> None:
    keys = []
    if args.visual_clarity:
        keys += [key for key, _, _ in CLARITY_MODULES]
        keys += ['r_drawtracers_firstperson', 'r_jiggle_bones', 'tf_sheen_framerate',
                 'cl_hud_playerclass_use_playermodel', 'mat_postprocessing_combine']
    if args.viewmodels:
        keys += ['r_drawviewmodel', 'tf_use_min_viewmodels']
    if not keys:
        return
    expression = re.compile(r'(?<!\w)(?:' + '|'.join(map(re.escape, keys)) + r')(?!\w)', re.I)
    hits = []
    for path in sorted((tf / 'cfg/overrides').rglob('*.cfg')):
        if path.relative_to(tf).as_posix() in MANAGED_FILES:
            continue
        for number, line in enumerate(read_cfg(path).splitlines(), 1):
            if expression.search(active_line(line)):
                hits.append(f'{path.relative_to(tf)}:{number}')
    if hits:
        warn('Other scripts reference the requested visual settings and are NOT rewritten: '
             + ', '.join(hits[:12]) + (', ...' if len(hits) > 12 else '')
             + '. Class changes or binds may override the selection. Review these before applying.')


def hud_candidates(tf: Path) -> list[Path]:
    custom = tf / 'custom'
    if not custom.is_dir():
        return []
    found = []
    signatures = ('scripts/hudlayout.res', 'resource/clientscheme.res',
                  'resource/ui/hudplayerhealth.res')
    for path in sorted(custom.iterdir()):
        name = path.name.lower()
        if name.startswith('mastercomfig-'):
            continue
        looks_like_hud = (path.is_dir() and
                          (any((path / rel).is_file() for rel in signatures)
                           or ('hud' in name and (path / 'info.vdf').is_file())))
        if looks_like_hud or (path.suffix.lower() == '.vpk' and 'hud' in name):
            found.append(path)
    return found


def hud_is_current(path: Path, name: str) -> bool:
    marker = path / HUD_MARKER
    if not marker.is_file():
        return False
    try:
        saved = json.loads(marker.read_text(encoding='utf-8'))
        return (saved.get('hud') == name and saved.get('archive_sha256') == HUDS[name]['sha256']
                and saved.get('policy') == HUD_POLICY
                and saved.get('tree_sha256') == tree_hash(path, (HUD_MARKER,)))
    except (ValueError, OSError, AttributeError):
        return False


def plan_hud(tf: Path, name: str, replace: bool) -> tuple[bool, list[str]]:
    if name == 'keep':
        if replace:
            raise SetupError('--replace-hud requires --hud rayshud or --hud budhud.')
        return False, []
    selected = target_path(tf, 'custom/' + name)
    candidates = hud_candidates(tf)
    if exists(selected) and selected not in candidates:
        candidates.append(selected)
    for path in candidates:
        assert_plain(target_path(tf, path.relative_to(tf).as_posix()))
    same = selected.is_dir() and hud_is_current(selected, name)
    other = [path for path in candidates if path != selected]
    conflicts = other + ([selected] if exists(selected) and not same else [])
    if conflicts and not replace:
        names = ', '.join(str(p.relative_to(tf)) for p in conflicts)
        raise SetupError('Existing HUD or customized HUD would be replaced: ' + names
                         + '. Preview again with --replace-hud to authorize backing up '
                         'and replacing these items; no files have been changed.')
    # The chosen directory is replaced by its source operation, not a second delete.
    return not same, [path.relative_to(tf).as_posix() for path in other]


def prepare_hud(archive: Path, dest: Path, name: str) -> Path:
    root = extract_hud(archive, dest)
    startup = root / 'cfg/valve.rc'
    if startup.is_file():
        startup.unlink()
        print('  Excluded HUD cfg/valve.rc; preserving existing startup and graphics settings.')
    # These are not in the pinned releases. Refuse a surprise startup override.
    for rel in ('cfg/autoexec.cfg', 'cfg/config.cfg', 'cfg/overrides'):
        if exists(root / rel):
            raise SetupError('Unexpected HUD startup override: ' + rel)
    if (root / 'cfg').is_dir() and not any((root / 'cfg').iterdir()):
        (root / 'cfg').rmdir()
    if exists(root / HUD_MARKER):
        raise SetupError('Unexpected installer metadata in upstream HUD archive.')
    save_json(root / HUD_MARKER, {'hud': name, 'version': HUDS[name]['version'],
                                'archive_sha256': HUDS[name]['sha256'], 'policy': HUD_POLICY,
                                'tree_sha256': tree_hash(root, (HUD_MARKER,))})
    return root


def fingerprint(tf: Path, rel: str) -> str | None:
    path = target_path(tf, rel)
    assert_plain(path)
    return tree_hash(path) if path.exists() else None


def print_diff(tf: Path, changes: dict[str, bytes]) -> None:
    if not changes:
        print('Configuration files: no changes.')
    for rel, data in changes.items():
        old = target_path(tf, rel).read_bytes().decode('utf-8', errors='surrogateescape')
        new = data.decode('utf-8', errors='surrogateescape')
        print(''.join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                         fromfile=rel + ' (current)', tofile=rel + ' (planned)')), end='')
        if not new.endswith('\n'):
            print()


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tf2-dir', type=Path, help='Team Fortress 2 folder; auto-detected by default')
    ap.add_argument('--update-only', action='store_true',
                    help='require an existing script-managed setup; never reinstall the baseline')
    ap.add_argument('--preset', choices=('medium', 'low', 'high'),
                    help='new installs: medium; updates: keep unless explicitly supplied')
    ap.add_argument('--fps-cap', choices=FPS_CAPS,
                    help='new installs: 300; updates: keep unless explicitly supplied')
    ap.add_argument('--hud', choices=('keep', 'budhud', 'rayshud'), default='keep',
                    help='default: keep your HUD')
    ap.add_argument('--replace-hud', action='store_true',
                    help='back up and replace detected old HUD(s); required for customized/existing copies')
    ap.add_argument('--visual-clarity', action='store_true',
                    help='add cosmetic-motion reductions without changing your effects level')
    ap.add_argument('--viewmodels', choices=('minimal', 'hidden'),
                    help='minimal visible or hidden weapons; updates keep the current choice by default')
    ap.add_argument('--dry-run', action='store_true', help='preview diffs/actions only; no downloads or writes')
    ap.add_argument('--version', action='version', version='%(prog)s ' + SCRIPT_VERSION)
    ap.add_argument('--restore', type=Path, help='restore an old or new backup; save current affected files first')
    ap.add_argument('--yes', action='store_true', help='skip the interactive confirmation after previewing')
    return ap


def main() -> int:
    args = parser().parse_args()
    if sys.platform != 'linux':
        raise SetupError('This script is intended for Linux.')
    if os.geteuid() == 0:
        raise SetupError('Run as your normal desktop user, not with sudo/root.')
    state = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state')))
    state = (state.expanduser() / 'tf2-competitive-backups').resolve()
    changes: dict[str, bytes] = {}
    guard: dict[str, str | None] = {}
    hud_install = False
    hud_remove: list[str] = []
    update = False
    if args.restore:
        if (args.tf2_dir or args.update_only or args.preset or args.fps_cap or args.visual_clarity
                or args.viewmodels or args.hud != 'keep' or args.replace_hud):
            raise SetupError('--restore cannot be combined with installation/update options.')
        tf, restore_ops = load_restore(args.restore.expanduser().resolve())
        print(f'Restore to: {tf}\nRestore affected items: ' + ', '.join(restore_ops))
        print('Your current affected files will be backed up before restoration.')
    else:
        if args.tf2_dir:
            game = validate_game(args.tf2_dir)
        else:
            games = discover_games()
            if len(games) != 1:
                found = '\n'.join('  ' + str(p) for p in games) or '  None detected.'
                raise SetupError('Cannot choose one TF2 installation.\n' + found
                                 + '\nUse --tf2-dir with the folder from Steam > Properties > Installed Files > Browse.')
            game = validate_game(games[0])
        tf = game / 'tf'
        assert_plain(target_path(tf, 'cfg'))
        target_path(tf, 'custom/mastercomfig-base.vpk')
        update = recognized_install(tf)
        if args.update_only and not update:
            raise SetupError('--update-only did not find the earlier script-managed setup. '
                             'Check --tf2-dir; no baseline will be installed.')
        hud_install, hud_remove = plan_hud(tf, args.hud, args.replace_hud)
        print(f'TF2 setup {SCRIPT_VERSION}\nTF2: {game}\nMode: ' +
              ('incremental update (existing setup preserved)' if update else 'first-time baseline install'))
        if update:
            # Capture guards before computing the preview; reject stale plans later.
            guard = {rel: fingerprint(tf, rel) for rel in MANAGED_FILES}
            guard['custom/mastercomfig-base.vpk'] = fingerprint(tf, 'custom/mastercomfig-base.vpk')
            changes = plan_update(tf, args)
            print('Unspecified settings stay unchanged. No mastercomfig download or config migration.')
            print('Preset: ' + (args.preset or 'keep') + '; FPS cap: ' + (args.fps_cap or 'keep')
                  + '; weapon visibility: ' + (args.viewmodels or 'keep'))
            print_diff(tf, changes)
        else:
            args.preset = args.preset or 'medium'
            args.fps_cap = args.fps_cap or '300'
            args.viewmodels = args.viewmodels or 'minimal'
            guard = {'cfg': fingerprint(tf, 'cfg'),
                     'custom/mastercomfig-base.vpk': fingerprint(tf, 'custom/mastercomfig-base.vpk')}
            print(f'mastercomfig: {COMFIG["version"]}; preset: {args.preset}; cap: {args.fps_cap} FPS')
            print('Back up tf/cfg; migrate standard autoexec/class files into cfg/overrides.')
            print('Baseline: FOV 90, minimal weapons, raw mouse input, hit feedback, auto-reload.')
            print('Baseline modules: motion blur, VSync, ragdolls, gibs and anti-aliasing off; '
                  'standard packet rate; automatic snapshot buffering.')
            for old in old_presets(tf):
                rel = old.relative_to(tf).as_posix()
                guard[rel] = fingerprint(tf, rel)
                print('Back up and remove old preset: ' + rel)
            if any((tf / 'cfg' / n).is_file() for n in MIGRATE):
                warn('Existing config content will be migrated; arbitrary old FPS/class scripts '
                     'are not automatically sanitized. Inspect their settings before first install.')
        if args.visual_clarity:
            print('Requested clarity options (already-set values are not duplicated):')
            for key, value, description in CLARITY_MODULES:
                print(f'  {key}={value}: {description}.')
            print('  effects module is unchanged, including any stricter low/very_low setting.')
        if args.viewmodels == 'hidden':
            print('Hidden viewmodels remove visible weapon/hands and their animations, NOT reload timing.')
            print('Camera recoil/shake and some world/status effects remain; weapon/reload cues are lost.')
            print('Session-only recovery in the TF2 console: r_drawviewmodel 1')
        warn_other_scripts(tf, args)
        if args.hud != 'keep':
            rel = 'custom/' + args.hud
            guard[rel] = fingerprint(tf, rel)
            for rel in hud_remove:
                guard[rel] = fingerprint(tf, rel)
                print('HUD replacement: back up and remove ' + rel)
            if hud_install:
                print(f'HUD install: {args.hud} {HUDS[args.hud]["version"]} '
                      '(pinned release; SHA-256 checked before any game-file changes).')
                print('HUD cfg/valve.rc will be excluded to preserve existing startup/settings.')
                print('This omits automatic HUD-specific tweaks; layout may need adjustment for nondefault HUD settings.')
                if exists(tf / 'custom' / args.hud):
                    print('The existing chosen HUD directory will be backed up, then replaced.')
            else:
                print(f'HUD: unchanged {args.hud} release already installed; no download.')
            warn('HUD detection cannot prove compatibility with every renamed/packed custom mod.')
        else:
            print('HUD: keep existing files.')
        print('No edits to keybinds, sensitivity, crosshair commands, resolution, Steam settings, or the OS.')
    if state == tf or tf in state.parents:
        raise SetupError('The backup directory must be outside the game tf directory.')
    if args.dry_run:
        print('Preview only. No files changed, downloaded, or backed up.')
        return 0
    if update and not changes and not hud_install and not hud_remove:
        print('Already configured for these options. No writes, downloads, or new backup needed.')
        return 0
    require_closed()
    if not confirm(args.yes):
        print('Cancelled. No files changed.')
        return 0
    state.mkdir(parents=True, exist_ok=True)
    with (state / '.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise SetupError('Another copy of this script is running.') from exc
        if args.restore:
            # Re-validate the backup after confirmation, not only before it.
            tf, restore_ops = load_restore(args.restore.expanduser().resolve())
            backup = transact(tf, restore_ops, state, 'before-restore')
            print('Restoration complete. Steam launch options, if changed manually, are not restored.')
        else:
            with tempfile.TemporaryDirectory(prefix='tf2-setup-') as tmpdir:
                tmp = Path(tmpdir)
                if update:
                    ops: dict[str, Path | None] = {}
                    for rel, data in changes.items():
                        staged = tmp / rel
                        staged.parent.mkdir(parents=True, exist_ok=True)
                        staged.write_bytes(data)
                        ops[rel] = staged
                else:
                    base = tmp / 'mastercomfig-base.vpk'
                    download(COMFIG, base, 20 * 1024 * 1024)
                    validate_vpk(base)
                    cfg = tmp / 'cfg'
                    stage_cfg(tf, cfg, args.preset, args.fps_cap,
                              visual_clarity=args.visual_clarity, viewmodels=args.viewmodels)
                    ops = {'cfg': cfg, 'custom/mastercomfig-base.vpk': base}
                    for old in old_presets(tf):
                        ops['custom/' + old.name] = None
                if hud_install:
                    archive = tmp / (args.hud + '.zip')
                    download(HUDS[args.hud], archive, 50 * 1024 * 1024)
                    ops['custom/' + args.hud] = prepare_hud(archive, tmp / 'hud-unpacked', args.hud)
                for rel in hud_remove:
                    ops[rel] = None
                require_closed()
                for rel, before in guard.items():
                    if fingerprint(tf, rel) != before:
                        raise SetupError(f'{rel} changed after the preview. No game files were changed; preview again.')
                # Stop if another HUD appeared while the download/confirmation was in progress.
                if args.hud != 'keep' and plan_hud(tf, args.hud, args.replace_hud) != (hud_install, hud_remove):
                    raise SetupError('Installed HUDs changed after the preview. Run the preview again.')
                backup = transact(tf, ops, state, 'update' if update else 'install')
            print('\nUpdate applied. Restart Steam/TF2.' if update else '\nBaseline installed. Restart Steam/TF2.')
            if not update:
                print('For keyboard/mouse, manually set TF2 Launch Options to:\n  ' + LAUNCH)
                print('Use native Linux TF2, not Proton or Legacy OpenGL.')
                print('For a controller, omit -nojoy and -nosteamcontroller.')
            print('Verify in the TF2 console: version_comfig; preset_level; fps_max; r_drawviewmodel')
            if args.visual_clarity:
                print('Check selected clarity modules in the TF2 console: module_levels')
            if args.viewmodels == 'hidden':
                print('Persistent visible weapons: rerun with --update-only --viewmodels minimal.')
            print('Settings: ' + str(tf / 'cfg/overrides'))
        command = ['python3', str(Path(__file__).resolve()), '--restore', str(backup)]
        print('\nTo undo ONLY this operation after fully exiting TF2 and Steam:\n  ' + shlex.join(command))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (SetupError, OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print('\nCancelled.', file=sys.stderr)
        sys.exit(130)
