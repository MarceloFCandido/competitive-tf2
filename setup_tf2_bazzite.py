#!/usr/bin/env python3
"""Reversible TF2 competitive-style baseline for Bazzite/Linux (Python 3.9+).

Run as your normal user in Desktop Mode, with TF2 and Steam fully exited.
No sudo, pip, package installs, Steam-account edits, or OS tuning.
Downloads only pinned upstream game data; never executes downloaded programs.

Examples:
    python3 setup_tf2_bazzite.py --dry-run
    python3 setup_tf2_bazzite.py
    python3 setup_tf2_bazzite.py --preset low --fps-cap 240 --hud budhud
    python3 setup_tf2_bazzite.py --tf2-dir '/path/to/Team Fortress 2'
    python3 setup_tf2_bazzite.py --restore '/path/printed/after/install'

Sources checked 2026-10-17:
    https://docs.comfig.app/latest/setup/install/
    https://docs.comfig.app/latest/customization/custom_configs/
    https://docs.comfig.app/latest/customization/modules/
    https://github.com/mastercomfig/mastercomfig/releases/tag/9.100.1
    https://github.com/rbjaxter/budhud/releases/tag/2511_01
    https://github.com/rbjaxter/budhud/wiki/Installation
"""
from __future__ import annotations

import argparse
import datetime as dt
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
FPS_CAPS = ('60', '75', '120', '144', '160', '165', '180', '200', '240',
            '300', '360', '400', '1000')
MIGRATE = ('autoexec.cfg', 'listenserver.cfg', 'scout.cfg', 'soldier.cfg',
           'pyro.cfg', 'demoman.cfg', 'heavyweapons.cfg', 'engineer.cfg',
           'medic.cfg', 'sniper.cfg', 'spy.cfg', 'modules.cfg')
BEGIN = '// BEGIN TF2-COMPETITIVE-SETUP'
END = '// END TF2-COMPETITIVE-SETUP'
LAUNCH = '-novid -nojoy -nosteamcontroller -nohltv -particles 1'
PERSONAL = '''// World FOV and minimal, visible first-person weapon.
fov_desired 90
viewmodel_fov 70
tf_use_min_viewmodels 1
r_drawviewmodel 1

// No sensitivity or keybind changes.
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


def stage_cfg(tf: Path, dest: Path, preset: str, cap: str) -> None:
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
    managed_file(overrides / 'autoexec.cfg', PERSONAL)
    managed_file(overrides / 'modules.cfg', f'''motion_blur=off
vsync=off
ragdolls=off
gibs=off
anti_aliasing=off
packet_rate=standard
snapshot_buffer=auto
fpscap={cap}
''')


def download(asset: dict, dest: Path, maximum: int) -> None:
    print(f"Downloading {dest.name} (pinned upstream release {asset['version']})...", flush=True)
    req = urllib.request.Request(asset['url'], headers={'User-Agent': 'tf2-competitive-setup/1.0'})
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
                    or stat.S_ISLNK(mode) or item.flag_bits & 1):
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


def tree_hash(path: Path) -> str:
    h = hashlib.sha256()
    if path.is_dir():
        for entry in sorted(path.rglob('*')):
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


def check_hud_conflicts(tf: Path) -> None:
    custom = tf / 'custom'
    if not custom.is_dir():
        return
    conflicts = []
    for p in custom.iterdir():
        if p.name == 'budhud':
            continue
        # Conservative detection; packed/renamed HUDs cannot all be recognized.
        is_hud = p.is_dir() and ((p / 'info.vdf').is_file() and
                                 ((p / 'resource').is_dir() or (p / 'scripts/hudlayout.res').is_file()))
        if is_hud or (p.suffix.lower() == '.vpk' and 'hud' in p.name.lower()):
            conflicts.append(p.name)
    if conflicts:
        raise SetupError('Another possible HUD is installed: ' + ', '.join(conflicts)
                         + '. Move it outside tf/custom first, or omit --hud budhud.')


def confirm(yes: bool) -> bool:
    if yes:
        return True
    if not sys.stdin.isatty():
        raise SetupError('Run interactively, or use --yes after reviewing --dry-run.')
    return input('Apply these changes? [y/N] ').strip().lower() in ('y', 'yes')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tf2-dir', type=Path, help='Team Fortress 2 folder; auto-detected by default')
    ap.add_argument('--preset', choices=('medium', 'low', 'high'), default='medium')
    ap.add_argument('--fps-cap', choices=FPS_CAPS, default='300', help='in-game cap; default: 300')
    ap.add_argument('--hud', choices=('keep', 'budhud'), default='keep', help='default: keep your HUD')
    ap.add_argument('--dry-run', action='store_true', help='preview only; no downloads or writes')
    ap.add_argument('--restore', type=Path, help='restore a backup; save current affected files first')
    ap.add_argument('--yes', action='store_true', help='skip the interactive confirmation')
    args = ap.parse_args()
    if sys.platform != 'linux':
        raise SetupError('This script is intended for Linux.')
    if os.geteuid() == 0:
        raise SetupError('Run as your normal desktop user, not with sudo/root.')
    state = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state')))
    state = (state.expanduser() / 'tf2-competitive-backups').resolve()
    if args.restore:
        if args.tf2_dir:
            raise SetupError('--restore uses its recorded installation; omit --tf2-dir.')
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
        target_path(tf, 'cfg')
        target_path(tf, 'custom/mastercomfig-base.vpk')
        assert_plain(tf / 'cfg')
        if args.hud == 'budhud':
            check_hud_conflicts(tf)
        print(f'TF2: {game}\nmastercomfig: {COMFIG["version"]}; preset: {args.preset}; '
              f'cap: {args.fps_cap} FPS; HUD: {args.hud}')
        print('Back up tf/cfg and affected custom items; keep unrelated custom mods.')
        print('Migrate standard autoexec/class scripts into cfg/overrides; append the baseline.')
        print('Leave sensitivity, binds, crosshair, resolution, Steam settings, and the OS alone.')
        for old in old_presets(tf):
            print('Back up and remove old preset: ' + old.name)
        if any((tf / 'cfg' / n).is_file() for n in MIGRATE) or (tf / 'cfg/overrides').exists():
            warn('Existing script content will be kept. Old FPS/network commands or class configs '
                 'may conflict; this does not automatically sanitize arbitrary existing configs.')
        extras = [p.name for p in (tf / 'custom').glob('*.vpk')
                  if 'addon' in p.name.lower() or p.name.startswith('comfig-')]
        if extras:
            warn('Existing addons left unchanged; check their compatibility: ' + ', '.join(extras))
    if state == tf or tf in state.parents:
        raise SetupError('The backup directory must be outside the game tf directory.')
    if args.dry_run:
        print('Preview only. No files changed or downloaded.')
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
            backup = transact(tf, restore_ops, state, 'before-restore')
            print('Restoration complete. Steam launch options must be reverted manually.')
        else:
            with tempfile.TemporaryDirectory(prefix='tf2-setup-') as tmpdir:
                tmp = Path(tmpdir)
                base = tmp / 'mastercomfig-base.vpk'
                download(COMFIG, base, 20 * 1024 * 1024)
                validate_vpk(base)
                cfg = tmp / 'cfg'
                stage_cfg(tf, cfg, args.preset, args.fps_cap)
                ops = {'cfg': cfg, 'custom/mastercomfig-base.vpk': base}
                for old in old_presets(tf):
                    ops['custom/' + old.name] = None
                if args.hud == 'budhud':
                    archive = tmp / 'budhud.zip'
                    download(BUDHUD, archive, 50 * 1024 * 1024)
                    ops['custom/budhud'] = extract_hud(archive, tmp / 'hud-unpacked')
                require_closed()  # Check again in case Steam was restarted during download.
                backup = transact(tf, ops, state, 'install')
            print('\nInstalled. Restart Steam. For keyboard/mouse, set TF2 Launch Options to:')
            print('  ' + LAUNCH)
            print('Use native Linux TF2; do not force Proton. Do not choose Legacy OpenGL.')
            print('Keep controller launch options enabled when you use a controller.')
            print('Verify in the TF2 console: version_comfig; preset_level; fov_desired; fps_max')
            print('Settings: ' + str(tf / 'cfg/overrides'))
        command = ['python3', str(Path(__file__).resolve()), '--restore', str(backup)]
        print('\nTo undo this operation after fully exiting TF2 and Steam:\n  ' + shlex.join(command))
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
