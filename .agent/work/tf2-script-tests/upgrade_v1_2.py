from pathlib import Path
p=Path('/mnt/data/setup_tf2_bazzite.py')
s=p.read_text()
start=s.index('"""Reversible')
end=s.index('"""',start+3)+3
s=s[:start]+'''"""Reversible TF2 setup and incremental updates for Bazzite/Linux (Python 3.9+).

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
"""'''+s[end:]
s=s.replace('import datetime as dt\n','import datetime as dt\nimport difflib\n',1)
s=s.replace("SCRIPT_VERSION = '1.1.0'", "SCRIPT_VERSION = '1.2.0'",1)
at=s.index('FPS_CAPS = ')
s=s[:at]+'''RAYSHUD = {
    'version': '2026.0111',
    'url': 'https://github.com/raysfire/rayshud/releases/download/2026.0111/rayshud.zip',
    'sha256': '09c695faa1243d649dff5636d1ccb0c831a6f4f6d118380b2e40d451f6dbd014',
}
HUDS = {'budhud': BUDHUD, 'rayshud': RAYSHUD}
HUD_MARKER = '.tf2-competitive-setup-hud.json'
HUD_POLICY = 'preserve-startup-v1'
MANAGED_FILES = ('cfg/overrides/setup_hook.cfg', 'cfg/overrides/autoexec.cfg',
                 'cfg/overrides/modules.cfg')
'''+s[at:]
at=s.index('# Keep impact effects')
end=s.index('CLARITY_MODULES = (',at)
s=s[:at]+'''# Deliberately leave the effects module alone. Raising Low to Medium would
# re-enable impact cues/particles; the user requested an additive update.
# These descriptions are upstream intentions, not guarantees for every effect.
'''+s[end:]
s=s.replace("    ('effects', 'medium', 'Reduce supported weather, muzzle flashes, casings and particle density; keep impact effects'),\n",'',1)
s=s.replace("def tree_hash(path: Path) -> str:\n", "def tree_hash(path: Path, ignore_root: tuple[str, ...] = ()) -> str:\n",1)
s=s.replace("        for entry in sorted(path.rglob('*')):\n            rel = entry.relative_to(path).as_posix().encode('utf-8', errors='surrogateescape')", "        for entry in sorted(path.rglob('*')):\n            if entry.relative_to(path).parts[0] in ignore_root:\n                continue\n            rel = entry.relative_to(path).as_posix().encode('utf-8', errors='surrogateescape')",1)
# Tighten archive handling for unexpected member types.
s=s.replace("or stat.S_ISLNK(mode) or item.flag_bits & 1):", "or (stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR))\n                    or item.flag_bits & 1):",1)
# Drop old HUD handler and main; new implementations are appended below.
a=s.index('\ndef check_hud_conflicts(')
b=s.index('\ndef confirm(',a)
s=s[:a]+s[b:]
a=s.index('\ndef main()')
s=s[:a]
p.write_text(s)
