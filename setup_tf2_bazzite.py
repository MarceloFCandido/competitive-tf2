#!/usr/bin/env python3
"""Reversible TF2 setup and incremental updates for Bazzite/Linux (Python 3.9+).

Run as your normal user in Desktop Mode, with TF2 and Steam fully exited.
No sudo, pip, package installs, Steam-account edits, or OS tuning.
Downloads only pinned upstream game data; never executes downloaded programs.

Already applied an earlier version? Use:
    python3 setup_tf2_bazzite.py --update-only --dry-run --hud middlemann --replace-hud
    python3 setup_tf2_bazzite.py --update-only --hud middlemann --replace-hud

Other examples:
    python3 setup_tf2_bazzite.py --list-huds
    python3 setup_tf2_bazzite.py --update-only --hud rayshud --replace-hud
    python3 setup_tf2_bazzite.py --update-only --hud stock --replace-hud --dry-run
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

Acquisition and screenshots (do not install/change the active HUD):
    --hud-info all lists exact downloads, external requirements and limitations.
    --hud-info toonhud explains where to export a theme and obtain custom fonts.
    --fetch-hud middlemann --output ~/Downloads/tf2-huds saves the complete pinned
    release ZIP with SHA-256 verification, WITHOUT installing it or stripping cfg.
    --hud-zip now also accepts the exact pinned ZIP for any automatic HUD choice;
    it must match the built-in upstream digest, even without --hud-sha256.
    MaxiHud/ToonHUD remain user-selected ZIPs; acquisition links are printed.
    --build-gallery ~/Downloads/TF2_HUD_Offline.html downloads one published
    example per HUD and embeds the images directly into a single offline HTML.
    --gallery-images DIR can supply NAME.png/jpg/webp locally instead.
    Without --gallery-partial, a missing image stops creation; it does not produce
    another gallery full of broken external image tags. Existing files are never
    overwritten by the download/gallery helpers. --dry-run never downloads/writes.
    No additional Python packages, system fonts or root privileges are required.

HUDs:
    v1.5 adds --hud centerhud and --hud hudfixes (pinned release downloads).
    --hud maxihud --hud-zip /path/to/maxihud.zip imports your upstream ZIP.
    --hud toonhud --hud-zip /path/to/toonhud.zip imports your exported theme.
    --hud-sha256 optionally checks a local ZIP against a hash you supply.
    Local ZIP hashes track content; they do NOT authenticate its publisher.
    Center HUD, HUD Fixes and ToonHUD exclude bundled cfg scripts. MaxiHUD
    v17.5 keeps six checksum-reviewed alias files with a minimal menu loader,
    excludes valve.rc/first-run, and removes four menu mat_queue_mode writes.
    Menu file writes use a configurable explicit logging-restore profile.
    Existing options, pins, and gameplay config are unchanged on HUD-only updates.
    An installer cannot guarantee compatibility with every runtime HUD/UI command.
    --hud middlemann installs Middle Mann: TF2-styled panels with centered
    health/ammo. Its normal (cl_hud_minmode 0) layout is already centered.
    The installer DOES NOT change cl_hud_minmode or re-enable the 3D portrait.
    With cl_hud_minmode 1, its layout may not work correctly. See printed notes.
    Middle Mann's bundled startup script is excluded; its cache-disabling and
    delayed HUD-reload commands are not run. Runtime rendering is untested here.
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
    Custom HUD downloads are pinned and SHA-256 checked before installation.
    --replace-hud permits backing up/replacing detected existing HUDs, including
    a customized copy of the chosen HUD. Otherwise conflicts stop installation.
    Bundled cfg/valve.rc files are excluded to preserve your startup/settings;
    this also omits their automatic HUD-specific tweaks (e.g. menu dimmer fix).
    The pinned IDHUD package contains no cfg folder; no startup patch is needed.
    IDHUD's optional recommended ConVars are NOT applied by the installer.
    Detection is conservative; arbitrary packed/renamed mods may go undetected.

Dry runs never download, write game files, or create backups. Incremental dry
runs show config diffs and planned HUD replacements. Backups from older script
versions remain restorable. The program prints an undo command after changes.

Baseline sources checked 2026-10-18; HUD additions checked 2026-10-19:
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
    https://github.com/idhud-tf2/idhud/releases/tag/4.0.8
    https://github.com/idhud-tf2/idhud/blob/4.0.8/README.md
    https://github.com/Vexcenot/-middle-mann/releases/tag/v26.1
    https://github.com/Vexcenot/-middle-mann/blob/v26.1/cfg/valve.rc
"""
from __future__ import annotations

import argparse
import base64
import html
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

SCRIPT_VERSION = '1.6.2'

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
CENTERHUD = {
    'version': 'v24',
    'url': 'https://github.com/RoseyLemonz/center-hud/releases/download/v24/center-hud.zip',
    'sha256': '948346882585929f16aa4e37510ec560595e4eae58dc7727df126dae6551ff16',
}
HUDFIXES = {
    'version': '11.0',
    'url': 'https://github.com/CriticalFlaw/tf2hud-fixes/releases/download/11.0/tf2hud-fixes-r11.zip',
    'sha256': '84fa26905d00d91fd45640e992b480b79ac9ed1fc836ce4caa7a6405603b2ea1',
}
# Existing pins and policies stay unchanged. Extra choices do not select themselves.
HUDS = {'middlemann': MIDDLEMANN, 'centerhud': CENTERHUD, 'idhud': IDHUD,
        'hudfixes': HUDFIXES, 'rayshud': RAYSHUD, 'budhud': BUDHUD}
# These need an archive explicitly chosen by the user, not an unverified download.
LOCAL_HUDS = ('maxihud', 'toonhud')
ISOLATED_HUDS = ('centerhud', 'hudfixes', *LOCAL_HUDS)
HUD_CHOICES = ('keep', 'stock', *HUDS, *LOCAL_HUDS)
HUD_FOLDERS = {'centerhud': 'center-hud', 'hudfixes': 'tf2hud-fixes'}
HUD_DESCRIPTIONS = {
    'centerhud': 'Center HUD: TF2-style central layout; customization scripts omitted.',
    'hudfixes': 'Community HUD Fixes: stock-style layout fixes; customization scripts omitted.',
    'maxihud': 'MaxiHud: centered TF2-style UI; reviewed v17.5 ZIP; minimal menu support.',
    'toonhud': 'ToonHUD: your exported theme ZIP; scripts omitted; compatibility unverified.',
    'middlemann': 'Middle Mann: TF2-styled panels with health/ammo toward the center.',
    'idhud': 'Improved Default HUD: original TF2 style and corner layout; readability/UI fixes.',
    'rayshud': 'Simplified, bold redesign; the HUD offered in the previous installer.',
    'budhud': 'A more extensively redesigned HUD inspired by yahud and rayshud.',
}
HUD_PAGES = {
    'centerhud': 'https://github.com/RoseyLemonz/center-hud',
    'hudfixes': 'https://github.com/CriticalFlaw/tf2hud-fixes',
    'maxihud': 'https://github.com/maxiandrew/maxihud/releases/tag/v17.5',
    'toonhud': 'https://toonhud.com/guide',
    'middlemann': 'https://github.com/Vexcenot/-middle-mann',
    'idhud': 'https://github.com/idhud-tf2/idhud',
    'rayshud': 'https://github.com/raysfire/rayshud',
    'budhud': 'https://github.com/rbjaxter/budhud',
}

# Acquisition notes are independent of the current HUD and never enable settings.
# Read 2026-10-19. Use the exact pinned archive when importing an automatic choice.
HUD_HELP = {
    'middlemann': {
        'notes': ['Use the complete release ZIP, not only resource/ or a screenshot.',
                  'Normal mode is already centered; upstream expects cl_hud_minmode 0.',
                  'The installer excludes cfg/valve.rc and its cache/reload workaround; downloading more files will not activate it.'],
        'links': [('Installation and customization', 'https://github.com/Vexcenot/-middle-mann'),
                  ('Excluded startup file', 'https://github.com/Vexcenot/-middle-mann/blob/v26.1/cfg/valve.rc')]},
    'centerhud': {
        'notes': ['The release ZIP contains center_hud_* support scripts and a joystick.cfg bootstrap.',
                  'Those cfg files are already in the download; this installer deliberately excludes them.',
                  'Without them, initialization and scripted customization can be incomplete. A second download alone does not fix that.',
                  'Upstream first-run code writes tf/cfg data and uses demo/logging commands. It is not enabled automatically.'],
        'links': [('Installation/customization', 'https://github.com/RoseyLemonz/center-hud/wiki'),
                  ('Bundled support files', 'https://github.com/RoseyLemonz/center-hud/tree/v24/cfg')]},
    'idhud': {
        'notes': ['Use the complete idhud.zip release; the pinned package has no cfg directory.',
                  'IDHUD supports Linux and retains corner placement. Its optional recommended console settings are not applied.'],
        'links': [('Requirements and recommendations', 'https://github.com/idhud-tf2/idhud/blob/4.0.8/README.md')]},
    'hudfixes': {
        'notes': ['Keep the complete release, including _fixes, _tf2hud and _extras; do not download only the resource folder.',
                  'The release includes its own customization scripts. This installer excludes cfg, so scripted options can fail.',
                  'No separate HUD should be layered over this installation to try to supply missing files.'],
        'links': [('Installation and optional features', 'https://github.com/CriticalFlaw/tf2hud-fixes'),
                  ('Bundled support files', 'https://github.com/CriticalFlaw/tf2hud-fixes/tree/11.0/cfg')]},
    'rayshud': {
        'notes': ['The pinned rayshud.zip is the package to acquire; bundled resources, materials and fonts are copied as supplied.',
                  'This installer only excludes cfg/valve.rc and does not run its startup workaround.'],
        'links': [('Installation and screenshots', 'https://github.com/raysfire/rayshud')]},
    'budhud': {
        'notes': ['Obtain budhud.zip under release Assets, not a single folder or screenshot.',
                  'The installer preserves other bundled resources and cfg files but excludes cfg/valve.rc.',
                  'Use the project wiki for chosen custom fonts or optional features rather than installing unrelated packages.'],
        'links': [('Installation and required file layout', 'https://github.com/rbjaxter/budhud/wiki/Installation'),
                  ('Customization and troubleshooting', 'https://github.com/rbjaxter/budhud/wiki')]},
    'maxihud': {
        'notes': ['Acquire Source code (zip) from release v17.5. That release does not publish a separate release asset with a digest.',
                  'The installer imports your ZIP; it does not claim upstream authentication for that archive.',
                  'The installed folder is named maxihud as required by the project.',
                  'The persistent loader is appended to overrides/autoexec.cfg without rewriting existing settings.',
                  'Menu writes temporarily require con_timestamp 0. Logging restoration is explicit in tf2_competitive_maxihud_logging.cfg; runtime state is not auto-captured.',
                  'The default restores con_logfile console.log and con_timestamp 0 after a menu write. Edit that profile for your own logging settings.',
                  'The project lists optional add-ons; they are not automatically installed as dependencies.',
                  'This installer loads six reviewed customization alias files, omits first-run/startup cfgs and removes the four menu mat_queue_mode changes. Optional add-ons remain manual.'],
        'links': [('Release and Source code (zip)', 'https://github.com/maxiandrew/maxihud/releases/tag/v17.5'),
                  ('Direct source ZIP (no trusted digest pinned here)', 'https://github.com/maxiandrew/maxihud/archive/refs/tags/v17.5.zip'),
                  ('Installation, compatibility, optional add-ons', 'https://github.com/maxiandrew/maxihud/blob/v17.5/README.md')]},
    'toonhud': {
        'notes': ['Choose/save a theme on ToonHUD and use its Download button. The browser builds a ZIP with your selected theme.',
                  'A theme page or screenshot is not the exported ZIP. Import the exported toonhud.zip, not an HTML download page.',
                  'For a Custom font, the official FAQ says to install that font separately and use its actual family name in the editor.',
                  'Obtain the chosen font from its legitimate publisher or choose a bundled font instead. No universal extra-font download applies to all themes.',
                  'This script does not install system fonts or OS packages. It copies resources provided inside your theme ZIP.',
                  'ToonHUD centered mode uses the minimal HUD option. Your current value is preserved.',
                  'The conservative installer excludes cfg scripts; some menu features may not work.'],
        'links': [('Theme editor / download', 'https://toonhud.com/'),
                  ('Export and Linux installation guide', 'https://toonhud.com/guide'),
                  ('Custom fonts and centered mode', 'https://toonhud.com/faq')]},
}

GALLERY_ITEMS = ({'name': 'middlemann', 'title': 'Middle Mann', 'image': 'https://static.tf2huds.dev/-Middle-Mann/img/Bki5t1X.png', 'gallery': 'https://tf2huds.dev/hud/-Middle-Mann', 'description': 'Default-style health and ammo panels moved toward the center. A first candidate for your preference.'}, {'name': 'centerhud', 'title': 'Center HUD', 'image': 'https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/center-hud/centerhudimage.webp', 'gallery': 'https://comfig.app/huds/page/center-hud/', 'description': 'Critical information moved centrally while retaining the default HUD style.'}, {'name': 'maxihud', 'title': 'MaxiHud', 'image': 'https://images.gamebanana.com/img/ss/mods/6997885801058.jpg', 'gallery': 'https://github.com/maxiandrew/maxihud#screenshots', 'description': 'A centered vanilla-inspired interface with more menu and customization features. The author notes that some screenshots show older versions.'}, {'name': 'rayshud', 'title': 'rayshud', 'image': 'https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/rayshud/hud.webp', 'gallery': 'https://comfig.app/huds/page/rayshud/', 'description': 'Your current reference: prominent health/ammo numbers and little decoration.'}, {'name': 'budhud', 'title': 'budhud', 'image': 'https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/budhud/budhud-04-player.webp', 'gallery': 'https://comfig.app/huds/page/budhud/', 'description': 'Another redesigned HUD, inspired by yahud and rayshud; not a stock-art-style restoration.'}, {'name': 'idhud', 'title': 'Improved Default HUD', 'image': 'https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/improved-default-hud/2-combat.webp', 'gallery': 'https://comfig.app/huds/page/improved-default-hud/', 'description': 'Retains the original layout with damage-text, target-ID and other UI improvements. Not a centered rayshud replacement.'}, {'name': 'hudfixes', 'title': 'Community HUD Fixes', 'image': 'https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/hud-fixes/hud.webp', 'gallery': 'https://comfig.app/huds/page/hud-fixes/', 'description': 'Default-style interface repairs and quality-of-life changes, rather than a centralized redesign.'}, {'name': 'toonhud', 'title': 'ToonHUD', 'image': 'https://static.tf2huds.dev/ToonHUD/img/VkMCo8g.jpg', 'gallery': 'https://tf2huds.dev/hud/ToonHUD', 'description': 'An example only: you choose the fonts, colors and theme. ToonHUD has default and centered modes.'})


# Reviewed v17.5 commit 18fb7f1e2903ebab15e811c9718726ddce51b0f4.
MAXIHUD_ALIAS_FILES = ('cfg/maxihud_customization_general.cfg',
 'cfg/maxihud_customization_colors.cfg',
 'cfg/maxihud_customization_fonts.cfg',
 'cfg/maxihud_customization_crosshairs.cfg',
 'cfg/maxihud_customization_streamer.cfg',
 'cfg/maxihud_customization_reset.cfg')
MAXIHUD_REVIEWED_SHA256 = {'cfg/maxihud_customization_general.cfg': '106e0b445a283da35b1e4f2fdba138cdceb7e1c42ce3fb752e55ba58935c5de8',
 'cfg/maxihud_customization_colors.cfg': '2874760f46e47eba485482a54856ede0477ddeee489a94e41a4552b8524c7d40',
 'cfg/maxihud_customization_fonts.cfg': '6d5d8700fd4fa4908daa9b92730b5e52b9c4178209edd47c35ce08635e728e32',
 'cfg/maxihud_customization_crosshairs.cfg': '62f859f791eacbdec4c5cee873a4dd617d0676f2b7068ee908cce2675b1aee13',
 'cfg/maxihud_customization_streamer.cfg': 'b272041a2779e0945d16943e756e57b4ca026c39c435fbce295bd2eeb7596bd5',
 'cfg/maxihud_customization_reset.cfg': '26fbe600861d566e23e9400e80a0ea7f01f1b914cba056c77f85f1114e9634a3',
 'resource/gamemenu.res': 'be223080e0b0c7be85ef85529de39945b4ed258daf8652d5c7609e9db75f8e68',
 'resource/ui/customizations/#customization_menu/hud_customization_frame.res': 'a9961efb0981626cf93cb17fd437bf823385b8212c51f336f7108ede9c05055c',
 'scripts/hudlayout.res': 'acdefa793bc561816ab911eb462288c2f331164c73134b997c885b1ca5d3a558'}
MAXIHUD_MENU_FRAME = 'resource/ui/customizations/#customization_menu/hud_customization_frame.res'
# GitHub archives honor upstream *.res eol=crlf; raw Git blobs use LF.
# Normalize only these reviewed resource paths for comparison, never archive bytes.
MAXIHUD_CRLF_FILES = ('resource/gamemenu.res', MAXIHUD_MENU_FRAME, 'scripts/hudlayout.res')
MAXIHUD_LOADER = 'tf2_competitive_maxihud_menu.cfg'
MAXIHUD_LOG_ALIAS = 'tf2_setup_maxihud_log_restore'
MAXIHUD_LOG_DEFAULT = 'alias tf2_setup_maxihud_log_restore "con_logfile console.log; con_timestamp 0"\n'
MAXIHUD_HOOK = b'\n// BEGIN TF2-COMPETITIVE-MAXIHUD-MENU\nexec tf2_competitive_maxihud_menu.cfg\n// END TF2-COMPETITIVE-MAXIHUD-MENU\n'

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
        raise SetupError(f'Download failed; check your connection and retry. {exc}\n'
                         f'Exact file: {asset["url"]}\n'
                         'For HUD acquisition instructions: --hud-info NAME; you can import the exact ZIP with --hud-zip.') from exc
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
    begin = [i for i, line in enumerate(lines) if line.strip().lstrip('\ufeff') == BEGIN]
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



def hud_relative(name: str) -> str:
    """Preserve old directory names; honor explicit names required by new HUDs."""
    return 'custom/' + HUD_FOLDERS.get(name, name)


def hud_policy(name: str) -> str:
    if name == 'maxihud':
        return 'maxihud-menu-v1'
    return 'isolate-cfg-v1' if name in ISOLATED_HUDS else HUD_POLICY


def local_hud_asset(args: argparse.Namespace) -> dict | None:
    """Read/hash a user-selected ZIP without downloads, extraction, or file writes.

    Recording its hash is NOT upstream authentication. An optional expected hash
    can detect a wrong file, but only a trusted source can establish provenance.
    """
    if args.hud not in (*HUDS, *LOCAL_HUDS):
        if args.hud_zip or args.hud_sha256:
            raise SetupError('--hud-zip/--hud-sha256 require --hud with a custom HUD name.')
        return None
    if args.hud in HUDS and not args.hud_zip:
        if args.hud_sha256:
            raise SetupError('--hud-sha256 requires --hud-zip; automatic downloads use the built-in digest.')
        return None
    if not args.hud_zip:
        raise SetupError('--hud ' + args.hud + ' requires --hud-zip /path/to/your.zip. '
                         'Choose it from ' + HUD_PAGES[args.hud] + '; nothing has changed.')
    path = args.hud_zip.expanduser().absolute()
    assert_plain(path)
    if not path.is_file() or path.stat().st_size > 50 * 1024 * 1024:
        raise SetupError('HUD ZIP must be a regular file, no larger than 50 MiB.')
    digest = tree_hash(path)
    if args.hud_sha256:
        if not re.fullmatch(r'[0-9a-fA-F]{64}', args.hud_sha256):
            raise SetupError('--hud-sha256 must be exactly 64 hexadecimal digits.')
        if digest != args.hud_sha256.lower():
            raise SetupError('Local HUD SHA-256 mismatch; nothing has changed.')
    if args.hud in HUDS and digest != HUDS[args.hud]['sha256']:
        raise SetupError('Pinned HUD SHA-256 mismatch. The ZIP must be the exact '
                         + HUDS[args.hud]['version'] + ' release; no files have changed.\n'
                         'Acquire: ' + HUDS[args.hud]['url'] + '\n'
                         'Details: python3 setup_tf2_bazzite.py --hud-info ' + args.hud)
    with zipfile.ZipFile(path) as zf:
        items = zf.infolist()
        if len(items) > 20000 or sum(i.file_size for i in items) > 200 * 1024 * 1024:
            raise SetupError('Unexpectedly large HUD archive.')
        names = set()
        for item in items:
            rel = PurePosixPath(item.filename)
            mode = item.external_attr >> 16
            if (rel.is_absolute() or '..' in rel.parts or '\\' in item.filename
                    or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)
                    or item.flag_bits & 1):
                raise SetupError('Unsafe HUD archive member: ' + item.filename)
            if item.is_dir():
                continue
            key = rel.as_posix()
            if key in names:
                raise SetupError('Duplicate HUD archive file: ' + key)
            if rel.suffix.lower() == '.vpk':
                raise SetupError('Packed VPKs are not supported in local HUD ZIP imports.')
            names.add(key)
        roots = []
        for name in names:
            if PurePosixPath(name).name != 'info.vdf':
                continue
            root = str(PurePosixPath(name).parent)
            prefix = '' if root == '.' else root + '/'
            if (any(n.startswith(prefix + 'resource/') for n in names)
                    and any(n.startswith(prefix + 'scripts/') for n in names)):
                roots.append(prefix)
        if len(roots) != 1:
            raise SetupError('Cannot uniquely identify the HUD root in this archive.')
        # These are identity checks only, not signatures or authenticity checks.
        prefix = roots[0]
        if args.hud == 'maxihud' and prefix + 'cfg/maxihud_customization.cfg' not in names:
            raise SetupError('ZIP does not have the expected MaxiHud layout.')
        if args.hud == 'maxihud':
            maxihud_menu_files({rel: zf.read(prefix + rel) for rel in MAXIHUD_REVIEWED_SHA256
                                if prefix + rel in names})
        if args.hud == 'toonhud' and 'toonhud' not in prefix.lower():
            raise SetupError('ToonHUD ZIP must contain its exported toonhud folder.')
    if args.hud in HUDS:
        return dict(HUDS[args.hud], local_path=str(path))
    return {'version': 'user-selected ZIP', 'sha256': digest, 'local_path': str(path),
            'url': HUD_PAGES[args.hud]}


def hud_is_current(path: Path, name: str, asset: dict | None = None) -> bool:
    asset = asset or HUDS.get(name)
    if asset is None:
        return False
    marker = path / HUD_MARKER
    if not marker.is_file():
        return False
    try:
        saved = json.loads(marker.read_text(encoding='utf-8'))
        return (saved.get('hud') == name and saved.get('archive_sha256') == asset['sha256']
                and saved.get('policy') == hud_policy(name)
                and saved.get('tree_sha256') == tree_hash(path, (HUD_MARKER,)))
    except (ValueError, OSError, AttributeError):
        return False


def plan_hud(tf: Path, name: str, replace: bool, asset: dict | None = None) -> tuple[bool, list[str]]:
    if name not in HUD_CHOICES:
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
    selected = target_path(tf, hud_relative(name))
    if exists(selected) and selected not in candidates:
        candidates.append(selected)
    for path in candidates:
        assert_plain(target_path(tf, path.relative_to(tf).as_posix()))
    same = selected.is_dir() and hud_is_current(selected, name, asset)
    other = [path for path in candidates if path != selected]
    conflicts = other + ([selected] if exists(selected) and not same else [])
    if conflicts and not replace:
        names = ', '.join(str(p.relative_to(tf)) for p in conflicts)
        raise SetupError('Existing HUD or customized HUD would be replaced: ' + names
                         + '. Preview again with --replace-hud to authorize backing up '
                         'and replacing these items; no files have been changed.')
    # The chosen directory is replaced by its source operation, not a second delete.
    return not same, [path.relative_to(tf).as_posix() for path in other]


def maxihud_menu_files(source: dict[str, bytes]) -> dict[str, bytes]:
    """Adapt only reviewed v17.5 data; never run HUD cfgs or the first-run loader."""
    for rel, expected in MAXIHUD_REVIEWED_SHA256.items():
        compared = source.get(rel, b'')
        if rel in MAXIHUD_CRLF_FILES:
            compared = compared.replace(b'\r\n', b'\n')
        if rel not in source or hashlib.sha256(compared).hexdigest() != expected:
            raise SetupError('MaxiHUD menu support requires the reviewed v17.5 files: ' + rel
                             + '. Obtain the unmodified v17.5 source ZIP; nothing was applied.')
    result = {}
    for rel in MAXIHUD_ALIAS_FILES:
        text = source[rel].decode('utf-8')
        # Upstream has one uncommented separator, not an engine command.
        text = re.sub(r'(?m)^=+\s*$', '// separator', text)
        text = re.sub(r'\bconsole_unlog\b', MAXIHUD_LOG_ALIAS, text)
        # Timestamp only during a menu file write, not at startup. The last
        # command restores the user's explicit logging profile, inline.
        text = re.sub(r'\bcon_logfile (?=cfg/maxihud/)',
                      'con_timestamp 0; con_logfile ', text)
        result[rel] = text.encode('utf-8')
    commands = {
        'resource/gamemenu.res': [
            'engine toggle cl_mainmenu_safemode; mat_queue_mode 0'],
        MAXIHUD_MENU_FRAME: [
            'engine cl_mainmenu_safemode 0; mat_queue_mode -1; gameui_allowescape',
            'engine gameui_allowescape; mat_queue_mode -1; gamemenucommand RestartWithNewLanguage',
            'engine cl_mainmenu_safemode 0; gameui_allowescape; mat_queue_mode -1; hud_reloadscheme'],
    }
    for rel, values in commands.items():
        text = source[rel].decode('utf-8')
        for value in values:
            quoted = '"' + value + '"'
            if text.count(quoted) != 1:
                raise SetupError('Unexpected MaxiHUD menu command; refusing a broad resource edit: ' + rel)
            replacement = re.sub(r'; mat_queue_mode (?:0|-1)', '', value)
            text = text.replace(quoted, '"' + replacement + '"')
        if re.search(r'\bmat_queue_mode\b', text):
            raise SetupError('Unexpected MaxiHUD queue-mode command remains: ' + rel)
        result[rel] = text.encode('utf-8')
    loader = ('// Minimal MaxiHUD v17.5 menu: definitions only; no first-run configuration.\n'
              + MAXIHUD_LOG_DEFAULT + 'exec tf2_competitive_maxihud_logging.cfg\n'
              + ''.join('exec ' + PurePosixPath(rel).name + '\n' for rel in MAXIHUD_ALIAS_FILES))
    result['cfg/' + MAXIHUD_LOADER] = loader.encode()
    return result


def plan_maxihud_support(cfg: Path, hud: str,
                         changes: dict[str, bytes]) -> dict[str, bytes]:
    """Append/remove our own startup block; retain every other config byte."""
    if hud == 'keep':
        return changes
    result = dict(changes)
    auto_rel = 'cfg/overrides/autoexec.cfg'
    auto = cfg / 'overrides/autoexec.cfg'
    old = result.get(auto_rel, auto.read_bytes() if auto.is_file() else b'')
    begin = MAXIHUD_HOOK.splitlines()[1]
    end = MAXIHUD_HOOK.splitlines()[-1]
    if old.count(begin) != old.count(end) or old.count(begin) > 1:
        raise SetupError('Malformed/duplicate MaxiHUD menu startup block; no config overwritten.')
    if begin in old and old.count(MAXIHUD_HOOK) != 1:
        raise SetupError('The MaxiHUD menu startup block was edited; review it before updating.')
    desired = old if hud == 'maxihud' else old.replace(MAXIHUD_HOOK, b'')
    if hud == 'maxihud' and begin not in old:
        desired += MAXIHUD_HOOK
    if desired != old:
        result[auto_rel] = desired
    if hud != 'maxihud':
        return result
    profile = cfg / 'tf2_competitive_maxihud_logging.cfg'
    assert_plain(profile)
    if profile.exists() and not profile.is_file():
        raise SetupError('MaxiHUD logging profile must be a regular cfg file.')
    if not profile.exists():
        result['cfg/' + profile.name] = (
            '// Used only after a menu write. Change this alias to match your logging preferences.\n'
            '// Source aliases cannot automatically snapshot arbitrary runtime ConVars.\n'
            + MAXIHUD_LOG_DEFAULT).encode()
    data = cfg / 'maxihud'
    assert_plain(data)
    if data.exists() and not data.is_dir():
        raise SetupError('tf/cfg/maxihud must be an ordinary directory.')
    menu = data / 'maxihud_customization_menu.txt'
    if not menu.exists():
        result['cfg/maxihud/maxihud_customization_menu.txt'] = b'"X" {}\n'
    elif not menu.is_file():
        raise SetupError('MaxiHUD customization menu data must be a regular file.')
    return result


def prepare_hud(archive: Path, dest: Path, name: str, asset: dict | None = None) -> Path:
    asset = asset or HUDS.get(name)
    if not asset:
        raise SetupError('A local HUD ZIP must be validated before preparing it.')
    root = extract_hud(archive, dest)
    menu_files = {}
    if name == 'maxihud':
        menu_files = maxihud_menu_files({rel: (root / rel).read_bytes()
                                      for rel in MAXIHUD_REVIEWED_SHA256 if (root / rel).is_file()})
    if name in ISOLATED_HUDS:
        # Avoid joystick.cfg bootstrap, autoexec/class scripts, first-run resets,
        # and optional customization aliases writing settings outside this HUD.
        if exists(root / 'cfg'):
            remove_item(root / 'cfg')
        if any(p.suffix.lower() == '.vpk' for p in root.rglob('*')):
            raise SetupError('Packed HUD data could contain startup scripts; refusing it.')
        if name != 'maxihud':
            print('  Omitted the new HUD cfg directory; optional scripted menus may not work.')
        print('  No claim of exact upstream behavior or complete runtime isolation is made.')
    for rel, data in menu_files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    if name == 'idhud' and exists(root / 'cfg'):
        raise SetupError('Unexpected cfg directory in the pinned IDHUD package; refusing startup changes.')
    if name == 'middlemann' and exists(root / 'cfg'):
        # The pinned source has only valve.rc here. Refuse extra auto-loaded
        # scripts rather than letting a new HUD change the existing setup.
        cfg = root / 'cfg'
        if not cfg.is_dir() or any(p.name != 'valve.rc' or not p.is_file()
                                   for p in cfg.iterdir()):
            raise SetupError('Unexpected cfg contents in the pinned Middle Mann package; '
                             'refusing startup changes.')
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
    save_json(root / HUD_MARKER, {'hud': name, 'version': asset['version'],
                                'archive_sha256': asset['sha256'], 'policy': hud_policy(name),
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
        path = target_path(tf, rel)
        old = (path.read_bytes() if path.is_file() else b'').decode('utf-8', errors='surrogateescape')
        new = data.decode('utf-8', errors='surrogateescape')
        print(''.join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                         fromfile=rel + ' (current)', tofile=rel + ' (planned)')), end='')
        if not new.endswith('\n'):
            print()


def print_middlemann_notes() -> None:
    """Explain the required HUD mode without changing any user configuration."""
    print('Middle Mann: normal HUD mode is centered; upstream expects cl_hud_minmode 0.')
    print('This installer preserves your current cl_hud_minmode. Query it in the TF2 console; '
          'if it is 1, use cl_hud_minmode 0 for this HUD and record the old value first.')
    print('Minimal HUD mode is separate from minimal weapon viewmodels; neither is changed here.')
    print('No extra HUD crosshair, hitmarker, vignette, or transparent-viewmodel option is enabled by this script.')
    print('Upstream cache/reload startup workarounds are omitted. Actual in-game rendering is not tested here.')


def print_hud_catalog() -> None:
    """Read-only catalog; no game discovery, network, or backup operations."""
    print('TF2 setup ' + SCRIPT_VERSION + ' - HUD choices')
    print('keep    Leave the current HUD alone (default).')
    print('stock   Remove detected custom HUDs after backup; no HUD download.')
    for name, asset in HUDS.items():
        print(f'{name:<12}{HUD_DESCRIPTIONS[name]}')
        print(f'            Pinned release: {asset["version"]}; {HUD_PAGES[name]}')
    for name in LOCAL_HUDS:
        print(f'{name:<12}{HUD_DESCRIPTIONS[name]}')
        print(f'            Import with --hud-zip /path/to/archive.zip; {HUD_PAGES[name]}')
    print('New Center HUD/HUD Fixes/MaxiHud/ToonHUD choices omit all bundled cfg scripts.')
    print('Their scripted customization menus/first-run tweaks are not enabled; test in-game.')
    print('ToonHUD imports your theme, not a preset chosen by this installer.')
    print('\nChoose one HUD at a time. Switching backs up the current HUD outside tf/custom.')
    print('Preview: python3 setup_tf2_bazzite.py --update-only --hud middlemann --replace-hud --dry-run')
    print('Omitted preset/FPS/visual options keep your earlier setup unchanged on updates.')
    print('To recover local HUD customizations, use the printed --restore command, not --hud NAME.')
    print_middlemann_notes()
    print('Acquisition and required-file notes: --hud-info NAME (or all).')
    print('Save the original ZIP without installation: --fetch-hud NAME --output DIRECTORY.')
    print('Build an offline screenshot page: --build-gallery OUTPUT.html.')


def print_hud_info(name: str) -> None:
    """Built-in acquisition/dependency notes; does not scan the PC or use a network."""
    names = (*HUDS, *LOCAL_HUDS) if name == 'all' else (name,)
    for selected in names:
        if selected not in HUD_HELP:
            raise SetupError('No custom-HUD acquisition entry for ' + selected)
        print('\n' + selected.upper() + ' — ' + HUD_DESCRIPTIONS[selected])
        print('Project: ' + HUD_PAGES[selected])
        if selected in HUDS:
            asset = HUDS[selected]
            print('Automatic package: ' + asset['version'])
            print('Exact ZIP: ' + asset['url'])
            print('Expected SHA-256: ' + asset['sha256'])
            print('Download only: python3 setup_tf2_bazzite.py --fetch-hud ' + selected
                  + ' --output ~/Downloads/tf2-huds')
        else:
            print('Acquisition: user-selected archive; not an automatically verified download.')
        print('Requirements, bundled support files and optional extras:')
        for note in HUD_HELP[selected]['notes']:
            print('  - ' + note)
        for label, url in HUD_HELP[selected]['links']:
            print('  ' + label + ': ' + url)
        print('Local ZIP preview: python3 setup_tf2_bazzite.py --update-only --hud '
              + selected + ' --hud-zip /path/to/download.zip --replace-hud --dry-run')
    print('\nReading these notes changes nothing. Downloads do not enable omitted cfg scripts.')
    print('Support files already bundled in a release are different from optional add-ons or custom system fonts.')


def write_new_file(path: Path, data: bytes) -> None:
    """Publish a complete file without overwriting an existing file or symlink."""
    path = path.expanduser().absolute()
    if exists(path):
        raise SetupError('Output already exists; choose another filename: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix='.tf2-hud-', dir=path.parent, delete=False) as out:
            temporary = Path(out.name)
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        # Same filesystem, exclusive creation: a racing existing file is not replaced.
        os.link(temporary, path)
    except FileExistsError as exc:
        raise SetupError('Output appeared during processing; it was not overwritten: ' + str(path)) from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def fetch_hud_package(name: str, output: Path, dry_run: bool = False) -> int:
    """Save the original archive, not an installed/stripped HUD. No game discovery."""
    if name not in HUDS:
        print_hud_info(name)
        if dry_run:
            print('Manual acquisition required; preview only. Nothing downloaded or written.')
            return 0
        raise SetupError('This HUD requires a user-selected ZIP; use the acquisition links above. '
                         'No automatic download, install or game changes were made.')
    asset = HUDS[name]
    target = output.expanduser().absolute() / (name + '-' + asset['version'] + '.zip')
    print('Download-only mode: the complete upstream archive, including bundled support files.')
    print('Source: ' + asset['url'])
    print('Expected SHA-256: ' + asset['sha256'])
    print('Save as: ' + str(target))
    if dry_run:
        print('Preview only. No network, file writes, game discovery or backups.')
        return 0
    if exists(target):
        assert_plain(target)
        if target.is_file() and tree_hash(target) == asset['sha256']:
            print('The complete verified ZIP is already present. No download needed.')
            return 0
        raise SetupError('A different file already exists; choose a different output directory: ' + str(target))
    with tempfile.TemporaryDirectory(prefix='tf2-hud-download-') as temporary:
        archive = Path(temporary) / target.name
        download(asset, archive, 50 * 1024 * 1024)
        if tree_hash(archive) != asset['sha256']:
            raise SetupError('Downloaded package failed the final SHA-256 check.')
        # Copy the complete package verbatim. No extraction, code execution, font
        # installation, or omitted-script policy is applied by this command.
        write_new_file(target, archive.read_bytes())
    print('Saved and checksum-verified. No HUD installed and no game files changed.')
    print('Preview a later install from this file:')
    print('  ' + shlex.join(['python3', 'setup_tf2_bazzite.py', '--update-only', '--hud', name,
                             '--hud-zip', str(target), '--replace-hud', '--dry-run']))
    return 0


class HTTPSOnlyRedirect(urllib.request.HTTPRedirectHandler):
    """Gallery fetches never follow a redirect down to HTTP or a local URL."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parts = urllib.parse.urlsplit(newurl)
        if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password:
            raise SetupError('Refusing an unsafe screenshot redirect: ' + newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def gallery_read_url(url: str, maximum: int, accept: str = 'image/*') -> bytes:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password:
        raise SetupError('Screenshot URL must be public HTTPS without credentials.')
    request = urllib.request.Request(url, headers={
        'User-Agent': 'tf2-hud-gallery/' + SCRIPT_VERSION,
        'Accept': accept,
    })
    opener = urllib.request.build_opener(HTTPSOnlyRedirect())
    with opener.open(request, timeout=20) as response:
        if urllib.parse.urlsplit(response.geturl()).scheme != 'https':
            raise SetupError('Screenshot response was not HTTPS.')
        chunks = []
        total = 0
        while True:
            chunk = response.read(min(65536, maximum + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > maximum:
                raise SetupError('Screenshot response exceeds the size limit.')
            chunks.append(chunk)
    return b''.join(chunks)


def image_mime(data: bytes) -> str:
    """Reject HTML error pages/SVG/scripts; only embed supported raster formats.

    Header validation is not a complete image decoder. Browser decode success
    still depends on the published file, not merely its claimed Content-Type.
    """
    if len(data) < 24:
        raise SetupError('Screenshot response was empty or truncated.')
    if data.startswith(b'\x89PNG\r\n\x1a\n') and data[12:16] == b'IHDR':
        width, height = struct.unpack('>II', data[16:24])
        if width and height and b'IEND' in data[-16:]:
            return 'image/png'
    if data.startswith(b'\xff\xd8\xff') and data.rstrip().endswith(b'\xff\xd9'):
        return 'image/jpeg'
    if (data[:4] == b'RIFF' and data[8:12] == b'WEBP'
            and data[12:16] in (b'VP8 ', b'VP8L', b'VP8X')
            and struct.unpack('<I', data[4:8])[0] + 8 == len(data)):
        return 'image/webp'
    raise SetupError('Not a supported raster image (possibly an HTML error/login page).')


def fetch_gallery_image(item: dict, local_dir: Path | None = None) -> tuple[bytes, str, str]:
    """Fetch one curated screenshot, with GitHub API fallback for raw URLs."""
    maximum = 8 * 1024 * 1024
    if local_dir is not None:
        matches = [local_dir / (item['name'] + suffix)
                   for suffix in ('.png', '.jpg', '.jpeg', '.webp')
                   if exists(local_dir / (item['name'] + suffix))]
        if len(matches) > 1:
            raise SetupError('Multiple local previews for ' + item['name'] + '; keep only one.')
        if matches:
            path = matches[0]
            assert_plain(path)
            if not path.is_file() or path.stat().st_size > maximum:
                raise SetupError('Local screenshot is not a regular file below 8 MiB: ' + str(path))
            data = path.read_bytes()
            return data, image_mime(data), 'User-supplied local preview: ' + path.name
    url = item['image']
    failures = []
    try:
        data = gallery_read_url(url, maximum)
        return data, image_mime(data), url
    except (SetupError, OSError, ValueError) as exc:
        failures.append(str(exc))
    parts = urllib.parse.urlsplit(url)
    if parts.hostname == 'raw.githubusercontent.com':
        tokens = parts.path.lstrip('/').split('/', 3)
        if len(tokens) == 4:
            owner, repo, ref, filepath = tokens
            api = (f'https://api.github.com/repos/{owner}/{repo}/contents/{filepath}'
                   + '?ref=' + urllib.parse.quote(ref, safe=''))
            try:
                body = gallery_read_url(api, 12 * 1024 * 1024, 'application/vnd.github+json')
                payload = json.loads(body)
                if not isinstance(payload, dict) or payload.get('encoding') != 'base64':
                    raise SetupError('GitHub did not return base64 image content.')
                content = ''.join(payload['content'].split())
                data = base64.b64decode(content, validate=True)
                if len(data) > maximum:
                    raise SetupError('Decoded screenshot exceeds the size limit.')
                # Check the Git blob identifier if supplied by the API.
                blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
                if payload.get('sha') and blob != payload['sha']:
                    raise SetupError('GitHub screenshot blob checksum mismatch.')
                return data, image_mime(data), url
            except (SetupError, OSError, ValueError, KeyError, TypeError) as exc:
                failures.append('GitHub fallback: ' + str(exc))
    raise SetupError('; '.join(failures) + '\nImage: ' + url + '\nGallery: ' + item['gallery'])


def render_offline_gallery(results: list[tuple[dict, bytes | None, str, str]]) -> bytes:
    """No external image/style/font/script dependencies; link citations stay online."""
    e = html.escape
    missing = sum(data is None for _, data, _, _ in results)
    label = f'PARTIAL: {missing} preview(s) missing' if missing else 'All eight previews embedded'
    body = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
            'img-src data:; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">',
            '<title>TF2 HUD comparison — offline images</title>',
            '<style>body{font:17px/1.6 system-ui,sans-serif;margin:0;background:#202020;color:#eee8da}'
            'main{max-width:1320px;margin:auto;padding:26px}h1{line-height:1.2}h2{margin-top:0}'
            'section{margin:30px 0;padding:24px;background:#303030;border-radius:8px}'
            'a{color:#eed49e}code{font-family:ui-monospace,monospace;background:#191919;padding:3px 6px}'
            'nav a{display:inline-block;margin:5px 16px 5px 0}.viewport{overflow:auto;margin-top:10px}'
            'img{display:block;max-width:100%;height:auto}.zoom:checked~.viewport img{max-width:none}'
            '.notice{border-left:4px solid #dab378;padding:10px 18px;background:#35312b}'
            '.small,figcaption{font-size:14px;color:#cdc6b8;overflow-wrap:anywhere}'
            '.missing{padding:24px;border:2px solid #d49176;white-space:pre-wrap;overflow-wrap:anywhere}'
            'figure{margin:12px 0}label{cursor:pointer}summary{cursor:pointer}</style></head><body><main>',
            '<h1>TF2 HUD comparison</h1>',
            '<p class="notice"><strong>' + e(label) + '</strong>. Images in this file do not need '
            'an internet connection. Source/project links still do.</p>',
            '<p>Published examples, not screenshots of your installation. Release version, theme, '
            'class, aspect ratio and HUD mode can change the appearance. No HUD is installed by this gallery.</p>',
            '<nav>' + ''.join('<a href="#' + e(item['name']) + '">' + e(item['title']) + '</a>'
                             for item, _, _, _ in results) + '</nav>']
    for item, data, mime, source in results:
        name = item['name']
        body.extend(['<section id="' + e(name) + '"><h2>' + e(item['title']) + '</h2>',
                     '<p><code>--hud ' + e(name) + '</code></p>',
                     '<p>' + e(item['description']) + '</p>'])
        if data is not None:
            uri = 'data:' + mime + ';base64,' + base64.b64encode(data).decode('ascii')
            body.append('<figure><input class="zoom" type="checkbox" id="zoom-' + e(name) + '"> '
                        '<label for="zoom-' + e(name) + '">Show original pixel size (scroll to inspect)</label>'
                        '<div class="viewport"><img src="' + uri + '" alt="' + e(item['title'])
                        + ' example screenshot"></div><figcaption>' + e(source) + '</figcaption></figure>')
        else:
            body.append('<div class="missing"><strong>Screenshot unavailable — not embedded.</strong>\n'
                        + e(source) + '</div>')
        body.append('<p><a href="' + e(item['gallery'], quote=True) + '">Original screenshot gallery</a> · '
                    '<a href="' + e(HUD_PAGES[name], quote=True) + '">Official HUD project / acquisition</a></p>')
        body.append('<details><summary>Installation and dependency notes</summary>')
        for note in HUD_HELP[name]['notes']:
            body.append('<p>' + e(note) + '</p>')
        body.append('</details></section>')
    body.append('<p class="small">Screenshots and HUD designs belong to their creators and Valve. '
                'This comparison is not affiliated with those projects. Built with installer '
                + e(SCRIPT_VERSION) + '. No fonts, tracking, JavaScript or game configuration are embedded.</p>'
                '</main></body></html>')
    return ''.join(body).encode('utf-8')


def build_gallery(output: Path, dry_run: bool = False, partial: bool = False,
                  local_dir: Path | None = None) -> int:
    output = output.expanduser().absolute()
    if output.suffix.lower() not in ('.html', '.htm'):
        raise SetupError('The gallery output must have an .html or .htm extension.')
    if exists(output):
        raise SetupError('Gallery output exists; use a new filename: ' + str(output))
    if local_dir is not None:
        local_dir = local_dir.expanduser().absolute()
        if not local_dir.is_dir():
            raise SetupError('--gallery-images must point to an existing directory.')
    if dry_run:
        print('Would download/embed one screenshot for each HUD into: ' + str(output))
        for item in GALLERY_ITEMS:
            print('  ' + item['name'] + ': ' + item['image'])
        print('Preview only. No network, writes, game discovery or backups.')
        return 0
    results = []
    errors = []
    for item in GALLERY_ITEMS:
        print('Screenshot: ' + item['title'], flush=True)
        try:
            data, mime, source = fetch_gallery_image(item, local_dir)
            results.append((item, data, mime, source))
        except (SetupError, OSError, ValueError) as exc:
            error = item['name'] + ': ' + str(exc)
            errors.append(error)
            warn(error)
            results.append((item, None, '', str(exc)))
    if errors and not partial:
        raise SetupError(f'{len(errors)} of {len(GALLERY_ITEMS)} screenshots could not be obtained. '
                         'No gallery was written.\n' + '\n'.join(errors)
                         + '\nSave missing previews as NAME.png/jpg/webp in a folder and use '
                         '--gallery-images FOLDER, or explicitly choose --gallery-partial. '
                         'No game files were changed.')
    data = render_offline_gallery(results)
    write_new_file(output, data)
    print(f'Created {output} ({len(data):,} bytes); '
          f'{len(results) - len(errors)}/{len(results)} screenshots embedded. Open it in a browser.')
    if errors:
        print('PARTIAL gallery: missing screenshots are explicitly marked; exit status 2.')
        return 2
    print('All eight image sources are embedded data, not remote links. Game files were not touched.')
    return 0


def resource_mode(args: argparse.Namespace) -> int | None:
    """Explicit non-installation operations cannot accidentally fall into setup."""
    modes = (bool(args.list_huds), bool(args.hud_info), bool(args.fetch_hud), bool(args.build_gallery))
    if sum(modes) > 1:
        raise SetupError('Choose only one of --list-huds, --hud-info, --fetch-hud or --build-gallery.')
    if args.output and not args.fetch_hud:
        raise SetupError('--output requires --fetch-hud.')
    if (args.gallery_partial or args.gallery_images) and not args.build_gallery:
        raise SetupError('--gallery-partial/--gallery-images require --build-gallery.')
    if not any(modes):
        return None
    if (args.tf2_dir or args.update_only or args.preset or args.fps_cap or args.visual_clarity
            or args.viewmodels or args.hud != 'keep' or args.replace_hud or args.restore
            or args.hud_zip or args.hud_sha256):
        raise SetupError('Acquisition/gallery/info modes cannot be combined with game installation options.')
    if args.list_huds:
        print_hud_catalog()
        return 0
    if args.hud_info:
        print_hud_info(args.hud_info)
        return 0
    if sys.platform != 'linux':
        raise SetupError('This script is intended for Linux.')
    if os.geteuid() == 0:
        raise SetupError('Run as your normal desktop user, not with sudo/root.')
    if args.fetch_hud:
        return fetch_hud_package(args.fetch_hud, args.output or Path('tf2-hud-downloads'), args.dry_run)
    return build_gallery(args.build_gallery, args.dry_run, args.gallery_partial, args.gallery_images)


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tf2-dir', type=Path, help='Team Fortress 2 folder; auto-detected by default')
    ap.add_argument('--update-only', action='store_true',
                    help='require an existing script-managed setup; never reinstall the baseline')
    ap.add_argument('--preset', choices=('medium', 'low', 'high'),
                    help='new installs: medium; updates: keep unless explicitly supplied')
    ap.add_argument('--fps-cap', choices=FPS_CAPS,
                    help='new installs: 300; updates: keep unless explicitly supplied')
    ap.add_argument('--hud', choices=HUD_CHOICES, default='keep',
                    help='one HUD at a time; stock removes detected HUDs; default: keep your HUD')
    ap.add_argument('--hud-zip', type=Path,
                    help='local HUD ZIP; automatic HUDs require the exact pinned checksum; ToonHUD needs a theme export')
    ap.add_argument('--hud-sha256',
                    help='optional independently obtained expected hash for a local ZIP')
    ap.add_argument('--list-huds', action='store_true',
                    help='show the supported HUD catalog and exit without scanning or changing files')
    ap.add_argument('--hud-info', choices=('all', *HUDS, *LOCAL_HUDS),
                    help='show exact acquisition links, bundled scripts and optional dependency notes; no network/writes')
    ap.add_argument('--fetch-hud', choices=(*HUDS, *LOCAL_HUDS),
                    help='download-only: save a complete verified release ZIP; manual HUDs print acquisition steps')
    ap.add_argument('--output', type=Path,
                    help='directory for --fetch-hud; default: ./tf2-hud-downloads')
    ap.add_argument('--build-gallery', type=Path, metavar='OUTPUT.html',
                    help='download screenshots and embed them into a standalone offline comparison; no HUD install')
    ap.add_argument('--gallery-images', type=Path, metavar='DIR',
                    help='prefer local NAME.png/jpg/jpeg/webp screenshots when building the gallery')
    ap.add_argument('--gallery-partial', action='store_true',
                    help='explicitly permit missing previews, mark them clearly, and return exit status 2')
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
    auxiliary = resource_mode(args)
    if auxiliary is not None:
        return auxiliary
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
    asset = None
    if args.restore:
        if (args.tf2_dir or args.update_only or args.preset or args.fps_cap or args.visual_clarity
                or args.viewmodels or args.hud != 'keep' or args.replace_hud or args.hud_zip or args.hud_sha256):
            raise SetupError('--restore cannot be combined with installation/update options.')
        tf, restore_ops = load_restore(args.restore.expanduser().resolve())
        print(f'Restore to: {tf}\nRestore affected items: ' + ', '.join(restore_ops))
        print('Your current affected files will be backed up before restoration.')
    else:
        asset = local_hud_asset(args) or HUDS.get(args.hud)
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
        hud_install, hud_remove = plan_hud(tf, args.hud, args.replace_hud, asset)
        print(f'TF2 setup {SCRIPT_VERSION}\nTF2: {game}\nMode: ' +
              ('incremental update (existing setup preserved)' if update else 'first-time baseline install'))
        if update:
            # Capture guards before computing the preview; reject stale plans later.
            guard = {rel: fingerprint(tf, rel) for rel in MANAGED_FILES}
            guard['custom/mastercomfig-base.vpk'] = fingerprint(tf, 'custom/mastercomfig-base.vpk')
            if args.hud == 'maxihud':
                for rel in ('cfg/maxihud', 'cfg/tf2_competitive_maxihud_logging.cfg'):
                    guard[rel] = fingerprint(tf, rel)
            changes = plan_maxihud_support(tf / 'cfg', args.hud, plan_update(tf, args))
            print('Unspecified settings stay unchanged. No mastercomfig download or config migration.')
            print('Preset: ' + (args.preset or 'keep') + '; FPS cap: ' + (args.fps_cap or 'keep')
                  + '; weapon visibility: ' + (args.viewmodels or 'keep'))
            print_diff(tf, changes)
        else:
            plan_maxihud_support(tf / 'cfg', args.hud, {})  # Read-only validation before preview.
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
            if args.hud != 'stock':
                print('Required files and acquisition details: --hud-info ' + args.hud)
            if args.hud in HUDS or args.hud in LOCAL_HUDS:
                rel = hud_relative(args.hud)
                guard[rel] = fingerprint(tf, rel)
            for rel in hud_remove:
                guard[rel] = fingerprint(tf, rel)
                print('HUD replacement: back up and remove ' + rel)
            if args.hud == 'stock':
                print('HUD: use built-in stock HUD files; no HUD download.')
                print('Other settings (including minimal HUD mode and 3D portrait visibility) stay unchanged.')
            elif hud_install:
                if 'local_path' in asset:
                    print(f'HUD import: {args.hud}; local ZIP {asset["local_path"]}')
                    print('SHA-256: ' + asset['sha256'])
                    if args.hud in HUDS:
                        print('Local ZIP matches the built-in pinned upstream SHA-256.')
                    else:
                        print('Local content is NOT authenticated against an upstream release digest.')
                else:
                    print(f'HUD install: {args.hud} {asset["version"]} '
                          '(pinned release; SHA-256 checked before any game-file changes).')
                if args.hud == 'maxihud':
                    print('MaxiHUD: six reviewed alias files and a minimal persistent menu loader.')
                    print('No valve.rc, first-run cfg, demo recording or server-command permission changes.')
                    print('Four reviewed menu mat_queue_mode assignments are removed; other UI actions remain upstream.')
                    print('Menu writes use con_timestamp 0 then the explicit tf2_competitive_maxihud_logging.cfg profile.')
                    print('Default restoration: con_logfile console.log; con_timestamp 0. Adjust the profile for custom logging.')
                elif args.hud in ISOLATED_HUDS:
                    print('All bundled HUD cfg scripts are omitted to avoid first-run/startup resets.')
                    print('Scripted customization menus may not work. Upstream screenshots may differ.')
                    print('Gameplay configuration files are preserved; runtime UI compatibility is untested.')
                    if args.hud == 'toonhud':
                        print('ToonHUD: exact appearance depends on your theme and cl_hud_minmode.')
                elif args.hud == 'idhud':
                    print('IDHUD: original TF2 style; pinned package has no startup cfg scripts.')
                    print('Optional recommended ConVars are not applied; existing settings are preserved.')
                else:
                    print('HUD cfg/valve.rc will be excluded to preserve existing startup/settings.')
                    print('This omits automatic HUD-specific tweaks; layout may need adjustment for nondefault HUD settings.')
                if exists(tf / hud_relative(args.hud)):
                    print('The existing chosen HUD directory will be backed up, then replaced.')
            else:
                print(f'HUD: unchanged {args.hud} release already installed; no download.')
            if args.hud == 'middlemann':
                print_middlemann_notes()
            if hud_remove or ((args.hud in HUDS or args.hud in LOCAL_HUDS) and exists(tf / hud_relative(args.hud)) and hud_install):
                print('The printed --restore command recovers the previous HUD, including local customizations.')
                print('Selecting a HUD name again downloads a clean pinned copy, not its customized backup.')
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
                    new_maxi_data = not exists(tf / 'cfg/maxihud')
                    for rel, data in changes.items():
                        staged = tmp / rel
                        staged.parent.mkdir(parents=True, exist_ok=True)
                        staged.write_bytes(data)
                        target = target_path(tf, rel)
                        staged.chmod(stat.S_IMODE(target.stat().st_mode) if target.exists() else 0o644)
                        if new_maxi_data and rel.startswith('cfg/maxihud/'):
                            ops['cfg/maxihud'] = tmp / 'cfg/maxihud'
                        else:
                            ops[rel] = staged
                else:
                    base = tmp / 'mastercomfig-base.vpk'
                    download(COMFIG, base, 20 * 1024 * 1024)
                    validate_vpk(base)
                    cfg = tmp / 'cfg'
                    stage_cfg(tf, cfg, args.preset, args.fps_cap,
                              visual_clarity=args.visual_clarity, viewmodels=args.viewmodels)
                    for rel, data in plan_maxihud_support(cfg, args.hud, {}).items():
                        staged = cfg / PurePosixPath(rel).relative_to('cfg')
                        staged.parent.mkdir(parents=True, exist_ok=True)
                        staged.write_bytes(data)
                    ops = {'cfg': cfg, 'custom/mastercomfig-base.vpk': base}
                    for old in old_presets(tf):
                        ops['custom/' + old.name] = None
                if hud_install:
                    archive = tmp / (args.hud + '.zip')
                    if 'local_path' in asset:
                        source = Path(asset['local_path'])
                        assert_plain(source)
                        if not source.is_file() or source.stat().st_size > 50 * 1024 * 1024:
                            raise SetupError('Local HUD ZIP changed after preview; nothing applied.')
                        shutil.copyfile(source, archive)
                        if tree_hash(archive) != asset['sha256']:
                            raise SetupError('Local HUD ZIP changed after preview; nothing applied.')
                    else:
                        download(asset, archive, 50 * 1024 * 1024)
                    ops[hud_relative(args.hud)] = prepare_hud(archive, tmp / 'hud-unpacked', args.hud, asset)
                for rel in hud_remove:
                    ops[rel] = None
                require_closed()
                for rel, before in guard.items():
                    if fingerprint(tf, rel) != before:
                        raise SetupError(f'{rel} changed after the preview. No game files were changed; preview again.')
                # Stop if another HUD appeared while the download/confirmation was in progress.
                if args.hud != 'keep' and plan_hud(tf, args.hud, args.replace_hud, asset) != (hud_install, hud_remove):
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
