from pathlib import Path
p = Path('/mnt/data/setup_tf2_bazzite.py')
s = p.read_text()
s = s.replace("SCRIPT_VERSION = '1.2.0'", "SCRIPT_VERSION = '1.3.0'")
s = s.replace('    python3 setup_tf2_bazzite.py --update-only --hud budhud --replace-hud\n', '''    python3 setup_tf2_bazzite.py --update-only --hud budhud --replace-hud
    python3 setup_tf2_bazzite.py --list-huds
    python3 setup_tf2_bazzite.py --update-only --hud idhud --replace-hud --dry-run
    python3 setup_tf2_bazzite.py --update-only --hud idhud --replace-hud
    python3 setup_tf2_bazzite.py --update-only --hud middlemann --replace-hud
    python3 setup_tf2_bazzite.py --update-only --hud stock --replace-hud
''')
s = s.replace('    --hud rayshud or --hud budhud installs one pinned, checksum-verified HUD.\n', '''    --list-huds prints available choices and notes without any downloads/writes.
    --hud idhud: Improved Default HUD, close to Valve's original corner layout.
    --hud middlemann: Middle Mann, stock styling with centered health/ammo.
    --hud rayshud and --hud budhud remain available, with their existing pins.
    --hud stock removes detected custom HUDs without changing your configuration.
    --hud keep (default) does nothing to your current HUD.
    Only ONE HUD is active. Options are alternatives, not stacked overlays.
    HUDs download only when selected; removed copies remain in undo backups.
    Switching back by name installs the pinned upstream copy, NOT any custom
    edits you made to a previous copy. Use the printed undo command to restore
    the exact previous files, including their customizations.
''')
s = s.replace('Sources checked 2026-10-18:', 'Baseline sources checked 2026-10-18; new HUD sources checked 2026-10-19:')
s = s.replace('    https://github.com/rbjaxter/budhud/blob/2511_01/cfg/valve.rc\n', '''    https://github.com/rbjaxter/budhud/blob/2511_01/cfg/valve.rc
    https://github.com/idhud-tf2/idhud/releases/tag/4.0.8
    https://github.com/idhud-tf2/idhud/blob/4.0.8/README.md
    https://github.com/Vexcenot/-middle-mann/releases/tag/v26.1
    https://github.com/Vexcenot/-middle-mann/blob/v26.1/cfg/valve.rc
''')
s = s.replace("HUDS = {'budhud': BUDHUD, 'rayshud': RAYSHUD}", '''# Pinned release assets and SHA-256 digests from the upstream GitHub release
# API, checked 2026-10-19. Keep existing budhud/rayshud pins unchanged so this
# update does not silently upgrade, replace or restyle an installed HUD.
IDHUD = {
    'version': '4.0.8',
    'url': 'https://github.com/idhud-tf2/idhud/releases/download/4.0.8/idhud.zip',
    'sha256': '3adbeffdee96f5555cd2c862a479e3248a4e62a4da6858200e2e99913e518719',
}
MIDDLEMANN = {
    'version': 'v26.1',
    'url': 'https://github.com/Vexcenot/-middle-mann/releases/download/v26.1/-middle-mann-v26.1.zip',
    'sha256': '4cc9721be700e6530f2cb731fae14ddc1d27b2b4c4aa7b42e69a3621513cf899',
}
HUDS = {'idhud': IDHUD, 'middlemann': MIDDLEMANN, 'rayshud': RAYSHUD, 'budhud': BUDHUD}
HUD_DETAILS = {
    'idhud': {
        'title': 'Improved Default HUD',
        'description': 'Original TF2 styling and corner placement, with readability and UI fixes.',
        'homepage': 'https://github.com/idhud-tf2/idhud',
        'notes': 'Upstream lists Linux support. No bundled cfg startup file; recommended console settings are NOT applied.',
    },
    'middlemann': {
        'title': 'Middle Mann',
        'description': 'Original TF2 styling with health/ammo moved toward the center.',
        'homepage': 'https://github.com/Vexcenot/-middle-mann',
        'notes': 'Designed for cl_hud_minmode 0; your setting is NOT changed. Startup caching/reload tweaks are excluded. In-game Linux rendering has not been tested by this installer author.',
    },
    'rayshud': {
        'title': 'rayshud',
        'description': 'Simplified, bold layout with strong health/ammo color cues.',
        'homepage': 'https://github.com/raysfire/rayshud',
        'notes': 'Existing release pin retained. Menu-dimmer/startup tweaks are excluded.',
    },
    'budhud': {
        'title': 'budhud',
        'description': 'Minimal, configurable layout that differs substantially from stock TF2.',
        'homepage': 'https://github.com/rbjaxter/budhud',
        'notes': 'Existing release pin retained. Bundled startup-enforced HUD settings are excluded.',
    },
}
HUD_CHOICES = ('keep', 'stock', *HUDS)
''')
s = s.replace("def hud_candidates(tf: Path) -> list[Path]:", '''def has_hud_signature(path: Path) -> bool:
    """Recognize common HUD paths despite filename capitalization on Linux.

    Only inspect the relevant shallow directories, not every asset. This does
    not make a Windows-only HUD Linux-compatible or rewrite any filenames.
    """
    if (path / HUD_MARKER).is_file():
        return True
    patterns = (('scripts', 'hudlayout.res'), ('resource', 'clientscheme.res'),
                ('resource', 'ui', 'hudplayerhealth.res'))
    for parts in patterns:
        level = [path]
        for part in parts:
            level = [entry for parent in level if parent.is_dir()
                     for entry in parent.iterdir() if entry.name.casefold() == part]
        if any(entry.is_file() for entry in level):
            return True
    return False


def hud_candidates(tf: Path) -> list[Path]:''')
s = s.replace("    signatures = ('scripts/hudlayout.res', 'resource/clientscheme.res',\n                  'resource/ui/hudplayerhealth.res')\n", '')
s = s.replace("(any((path / rel).is_file() for rel in signatures)\n                           or ('hud' in name and (path / 'info.vdf').is_file()))", "(has_hud_signature(path)\n                           or ('hud' in name and (path / 'info.vdf').is_file()))")
s = s.replace("raise SetupError('--replace-hud requires --hud rayshud or --hud budhud.')", "raise SetupError('--replace-hud requires a HUD name or --hud stock; use --list-huds.')")
s = s.replace("    selected = target_path(tf, 'custom/' + name)\n    candidates = hud_candidates(tf)\n", '''    if name not in HUD_CHOICES:
        raise SetupError('Unknown HUD: ' + name + '. Use --list-huds.')
    candidates = hud_candidates(tf)
    if name == 'stock':
        for path in candidates:
            assert_plain(target_path(tf, path.relative_to(tf).as_posix()))
        if candidates and not replace:
            names = ', '.join(str(p.relative_to(tf)) for p in candidates)
            raise SetupError('Returning to stock would remove detected HUD(s): ' + names
                             + '. Preview again with --replace-hud to authorize backing up '
                             'and removing them; no files have been changed.')
        return False, [path.relative_to(tf).as_posix() for path in candidates]
    selected = target_path(tf, 'custom/' + name)
''')
needle = 'def parser() -> argparse.ArgumentParser:\n'
s = s.replace(needle, '''def list_huds() -> None:
    """Print an offline catalog; do not inspect or modify the game."""
    print(f'TF2 setup {SCRIPT_VERSION} - HUD choices (one active at a time)')
    print('  keep        Leave the active HUD untouched (default).')
    print('  stock       Back up/remove detected custom HUDs; no download or config reset.')
    for name, asset in HUDS.items():
        detail = HUD_DETAILS[name]
        print(f"  {name:<11} {detail['title']} ({asset['version']})")
        print('              ' + detail['description'])
        print('              ' + detail['notes'])
        print('              ' + detail['homepage'])
    print('Switch: --update-only --hud NAME --replace-hud; add --dry-run to preview.')
    print('Previous active HUD files are kept in undo backups, outside tf/custom.')
    print('A switch by name reinstalls the upstream copy; use --restore for exact old customizations.')
    print('This listing makes no network requests, backups, or file changes.')


''' + needle)
s = s.replace("    ap.add_argument('--hud', choices=('keep', 'budhud', 'rayshud'), default='keep',\n                    help='default: keep your HUD')", "    ap.add_argument('--hud', choices=HUD_CHOICES, default='keep',\n                    help='choose one HUD, stock to remove detected custom HUDs, or keep (default)')\n    ap.add_argument('--list-huds', action='store_true',\n                    help='list choices and notes without looking for TF2 or writing/downloading anything')")
s = s.replace("    args = parser().parse_args()\n    if sys.platform", '''    args = parser().parse_args()
    if args.list_huds:
        if (args.restore or args.tf2_dir or args.update_only or args.preset or args.fps_cap
                or args.visual_clarity or args.viewmodels or args.hud != 'keep' or args.replace_hud):
            raise SetupError('--list-huds is a read-only catalog; do not combine it with update/restore options.')
        list_huds()
        return 0
    if sys.platform''')
s = s.replace("            rel = 'custom/' + args.hud\n            guard[rel] = fingerprint(tf, rel)\n", "            if args.hud != 'stock':\n                rel = 'custom/' + args.hud\n                guard[rel] = fingerprint(tf, rel)\n")
s = s.replace("            if hud_install:\n                print(f'HUD install:", "            if args.hud == 'stock':\n                print('HUD: return to stock layout; no HUD download or config reset.')\n                print('Only detected HUD files are removed; other mods may still alter the interface.')\n            elif hud_install:\n                print(f'HUD install:")
s = s.replace("                print('HUD cfg/valve.rc will be excluded to preserve existing startup/settings.')", "                print(HUD_DETAILS[args.hud]['description'])\n                print(HUD_DETAILS[args.hud]['notes'])\n                print('Any bundled HUD cfg/valve.rc will be excluded to preserve existing startup/settings.')")
s = s.replace("            warn('HUD detection cannot prove compatibility", "            print('Only one detected HUD remains active; previous HUD files stay in undo backups.')\n            warn('HUD detection cannot prove compatibility")
p.write_text(s)
