from pathlib import Path
p=Path('/mnt/data/setup_tf2_bazzite.py')
s=p.read_text()
s=s.replace("SCRIPT_VERSION = '1.2.0'", "SCRIPT_VERSION = '1.3.0'")
s=s.replace('    python3 setup_tf2_bazzite.py --update-only --dry-run --visual-clarity --hud rayshud --replace-hud\n    python3 setup_tf2_bazzite.py --update-only --visual-clarity --hud rayshud --replace-hud', '    python3 setup_tf2_bazzite.py --update-only --dry-run --hud idhud --replace-hud\n    python3 setup_tf2_bazzite.py --update-only --hud idhud --replace-hud')
s=s.replace('Other examples:\n', 'Other examples:\n    python3 setup_tf2_bazzite.py --list-huds\n    python3 setup_tf2_bazzite.py --update-only --hud rayshud --replace-hud\n    python3 setup_tf2_bazzite.py --update-only --hud stock --replace-hud --dry-run\n')
s=s.replace('HUDs:\n    --hud rayshud or --hud budhud installs one pinned, checksum-verified HUD.', '''HUDs:
    --hud idhud installs Improved Default HUD: original TF2 style/positions with
    readability and UI fixes. --hud rayshud and --hud budhud remain available.
    --list-huds lists the installer choices without scanning or changing files.
    --hud stock backs up/removes detected custom HUDs; no download. It preserves
    your other settings, including minimal-HUD mode and hidden 3D portraits.
    --hud keep (default) leaves the active HUD alone.
    Choices are alternatives, NOT layered HUDs. Only the selected HUD is added
    to tf/custom. Old HUDs are backed up outside tf/custom before replacement.
    Use the printed --restore command to recover your exact previous HUD,
    including local customizations. Selecting its name again installs a clean
    pinned copy instead; it does NOT retrieve a customized backup.
    Custom HUD downloads are pinned and SHA-256 checked before installation.''')
s=s.replace('    this also omits their automatic HUD-specific tweaks (e.g. menu dimmer fix).', '    this also omits their automatic HUD-specific tweaks (e.g. menu dimmer fix).\n    The pinned IDHUD package contains no cfg folder; no startup patch is needed.\n    IDHUD\'s optional recommended ConVars are NOT applied by the installer.')
s=s.replace('Sources checked 2026-10-18:', 'Baseline sources checked 2026-10-18; IDHUD addition checked 2026-10-19:')
s=s.replace('    https://github.com/rbjaxter/budhud/blob/2511_01/cfg/valve.rc\n', '    https://github.com/rbjaxter/budhud/blob/2511_01/cfg/valve.rc\n    https://github.com/idhud-tf2/idhud/releases/tag/4.0.8\n    https://github.com/idhud-tf2/idhud/blob/4.0.8/README.md\n')
s=s.replace("HUDS = {'budhud': BUDHUD, 'rayshud': RAYSHUD}", '''IDHUD = {
    'version': '4.0.8',
    'url': 'https://github.com/idhud-tf2/idhud/releases/download/4.0.8/idhud.zip',
    'sha256': '3adbeffdee96f5555cd2c862a479e3248a4e62a4da6858200e2e99913e518719',
}
# Do not silently upgrade the HUDs or mastercomfig from the earlier installer.
HUDS = {'idhud': IDHUD, 'rayshud': RAYSHUD, 'budhud': BUDHUD}
HUD_CHOICES = ('keep', 'stock', *HUDS)
HUD_DESCRIPTIONS = {
    'idhud': 'Improved Default HUD: original TF2 style and corner layout; readability/UI fixes.',
    'rayshud': 'Simplified, bold redesign; the HUD offered in the previous installer.',
    'budhud': 'A more extensively redesigned HUD inspired by yahud and rayshud.',
}
HUD_PAGES = {
    'idhud': 'https://github.com/idhud-tf2/idhud',
    'rayshud': 'https://github.com/raysfire/rayshud',
    'budhud': 'https://github.com/rbjaxter/budhud',
}''')
old='''    if name == 'keep':
        if replace:
            raise SetupError('--replace-hud requires --hud rayshud or --hud budhud.')
        return False, []
    selected = target_path(tf, 'custom/' + name)
    candidates = hud_candidates(tf)
'''
new='''    if name not in HUD_CHOICES:
        raise SetupError('Unsupported HUD selection: ' + name)
    if name == 'keep':
        if replace:
            raise SetupError('--replace-hud requires an explicit --hud choice other than keep. '
                             'See --list-huds.')
        return False, []
    candidates = hud_candidates(tf)
    if name == 'stock':
        for path in candidates:
            assert_plain(target_path(tf, path.relative_to(tf).as_posix()))
        if candidates and not replace:
            names = ', '.join(str(p.relative_to(tf)) for p in candidates)
            raise SetupError('Restoring stock HUD would remove these custom HUDs: ' + names
                             + '. Preview again with --replace-hud to authorize backing up '
                             'and removing them; no files have been changed.')
        return False, [path.relative_to(tf).as_posix() for path in candidates]
    selected = target_path(tf, 'custom/' + name)
'''
assert old in s
s=s.replace(old,new)
# Reject unexpected startup scripts in the newly pinned data-only HUD; preserve
# the old HUD policy/version so an unchanged rayshud install remains a no-op.
s=s.replace("    startup = root / 'cfg/valve.rc'\n", "    if name == 'idhud' and exists(root / 'cfg'):\n        raise SetupError('Unexpected cfg directory in the pinned IDHUD package; refusing startup changes.')\n    startup = root / 'cfg/valve.rc'\n")
s=s.replace('def parser() -> argparse.ArgumentParser:\n', '''def print_hud_catalog() -> None:
    """Read-only catalog; no game discovery, network, or backup operations."""
    print('TF2 setup ' + SCRIPT_VERSION + ' - HUD choices')
    print('keep    Leave the current HUD alone (default).')
    print('stock   Remove detected custom HUDs after backup; no HUD download.')
    for name, asset in HUDS.items():
        print(f'{name:<8}{HUD_DESCRIPTIONS[name]}')
        print(f'        Pinned release: {asset["version"]}; {HUD_PAGES[name]}')
    print('\\nChoose one HUD at a time. Switching backs up the current HUD outside tf/custom.')
    print('Preview: python3 setup_tf2_bazzite.py --update-only --hud idhud --replace-hud --dry-run')
    print('Omitted preset/FPS/visual options keep your earlier setup unchanged on updates.')
    print('To recover local HUD customizations, use the printed --restore command, not --hud NAME.')


def parser() -> argparse.ArgumentParser:
''')
s=s.replace("    ap.add_argument('--hud', choices=('keep', 'budhud', 'rayshud'), default='keep',\n                    help='default: keep your HUD')", "    ap.add_argument('--hud', choices=HUD_CHOICES, default='keep',\n                    help='one HUD at a time; stock removes detected HUDs; default: keep your HUD')\n    ap.add_argument('--list-huds', action='store_true',\n                    help='show the supported HUD catalog and exit without scanning or changing files')")
s=s.replace("    args = parser().parse_args()\n    if sys.platform", "    args = parser().parse_args()\n    if args.list_huds:\n        print_hud_catalog()\n        return 0\n    if sys.platform")
old='''        if args.hud != 'keep':
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
'''
new='''        if args.hud != 'keep':
            if args.hud in HUDS:
                rel = 'custom/' + args.hud
                guard[rel] = fingerprint(tf, rel)
            for rel in hud_remove:
                guard[rel] = fingerprint(tf, rel)
                print('HUD replacement: back up and remove ' + rel)
            if args.hud == 'stock':
                print('HUD: use built-in stock HUD files; no HUD download.')
                print('Other settings (including minimal HUD mode and 3D portrait visibility) stay unchanged.')
            elif hud_install:
                print(f'HUD install: {args.hud} {HUDS[args.hud]["version"]} '
                      '(pinned release; SHA-256 checked before any game-file changes).')
                if args.hud == 'idhud':
                    print('IDHUD: original TF2 style; pinned package has no startup cfg scripts.')
                    print('Optional recommended ConVars are not applied; existing settings are preserved.')
                else:
                    print('HUD cfg/valve.rc will be excluded to preserve existing startup/settings.')
                    print('This omits automatic HUD-specific tweaks; layout may need adjustment for nondefault HUD settings.')
                if exists(tf / 'custom' / args.hud):
                    print('The existing chosen HUD directory will be backed up, then replaced.')
            else:
                print(f'HUD: unchanged {args.hud} release already installed; no download.')
            if hud_remove or (args.hud in HUDS and exists(tf / 'custom' / args.hud) and hud_install):
                print('The printed --restore command recovers the previous HUD, including local customizations.')
                print('Selecting a HUD name again downloads a clean pinned copy, not its customized backup.')
            warn('HUD detection cannot prove compatibility with every renamed/packed custom mod.')
'''
assert old in s
s=s.replace(old,new)
p.write_text(s)
print('Wrote',p, len(s),'characters')
