# TF2 Bazzite setup — v1.5.0 HUD options and preview guide

This is an extension of the existing setup_tf2_bazzite.py, not a separate installer.
Existing rayshud, budhud, IDHUD, Middle Mann and mastercomfig pins are unchanged.
Downloading the new script does not itself change anything on your gaming PC.

## Visual comparison

Open TF2_HUD_Visual_Comparison.html in a browser. It has all eight choices, links
 to original screenshots, and source galleries. It loads images from the original
hosts and needs internet. Some image hosts could not be rendered from the
preparation environment. The source gallery links provide an alternative.
Screenshots are representative: release, theme, class, resolution, HUD mode,
and previously applied config can affect appearance. They are not Bazzite test
captures and are not guarantees of the conservative installer's exact appearance.

## Choices in this version

| --hud option | Installation |
| --- | --- |
| middlemann | Existing pinned release v26.1 |
| centerhud | New pinned release v24 |
| idhud | Existing pinned release 4.0.8 |
| hudfixes | New pinned Community HUD Fixes release 11.0 |
| rayshud | Existing pinned release 2026.0111 |
| budhud | Existing pinned release 2511_01 |
| maxihud | New import of an upstream ZIP you provide with --hud-zip |
| toonhud | New import of your exported theme ZIP with --hud-zip |
| keep | Default: no HUD file changes |
| stock | Remove detected custom HUDs after backing up; keep other settings |

For centered information with TF2 styling, compare Middle Mann and Center HUD
first. MaxiHud is another centered option. IDHUD and HUD Fixes are more
stock-layout-oriented alternatives, kept available rather than removed.

List choices without scanning the game, writing files or using the network:

```bash
python3 setup_tf2_bazzite.py --list-huds
```

## Preview then install a pinned HUD

```bash
python3 setup_tf2_bazzite.py --update-only --hud centerhud --replace-hud --dry-run
python3 setup_tf2_bazzite.py --update-only --hud centerhud --replace-hud
```

Replace centerhud with any pinned option. For a HUD-only incremental operation,
the preview should report `Configuration files: no changes.` Do not repeat your
old preset, FPS cap, viewmodel or clarity options unless you intend to change them.
The script keeps omitted values as they are. Close Steam and TF2 before applying;
run in Bazzite Desktop Mode as the normal user, without sudo.

## Local ZIP imports

MaxiHud's checked v17.5 release had no attached ZIP asset with a publisher digest.
Get its source ZIP from the release page and supply that file. ToonHUD exports a
ZIP with the theme you select; the script does not select a theme for you.

```bash
python3 setup_tf2_bazzite.py --update-only --hud maxihud --hud-zip "$HOME/Downloads/maxihud-17.5.zip" --replace-hud --dry-run
python3 setup_tf2_bazzite.py --update-only --hud toonhud --hud-zip "$HOME/Downloads/toonhud.zip" --replace-hud --dry-run
```

Use your actual file path. Remove `--dry-run` to apply after reviewing.
Optional `--hud-sha256 HEX_DIGEST` checks a local file against a hash you obtain
independently. Without that argument, the content hash is recorded to recognize
the same archive and detect a change after preview; it is NOT upstream
cryptographic authentication. Only import a ZIP from a source you trust.

Local archive checks run read-only, including on a dry run: ordinary file,
compressed/expanded size limits, one HUD root, expected package naming/layout,
no path traversal, encrypted entries, symlinks, duplicate files or packed VPKs.
No new HUD is installed merely because it was added to the option list.

## Startup preservation and limitations

The original four options retain their previous startup handling (exclude
cfg/valve.rc where present, with the earlier checks). The four NEW options—
Center HUD, HUD Fixes, MaxiHud, ToonHUD—omit the entire bundled cfg directory.
This avoids their joystick.cfg initialization, first-run resets, and optional
customization scripts altering existing settings. It also means script-dependent
customization menus, aliases, first-run tweaks and some workarounds may not work.
This integration must not be described as unmodified upstream/full-featured.

The installer does not change cl_hud_minmode, the 3D player portrait preference,
weapon visibility, keybinds, sensitivity, crosshair commands, effects modules,
networking, Steam launch options or OS settings during a HUD-only update. That
preservation concerns files touched by the installer: arbitrary UI commands,
other mods or class configs can still change runtime behavior. In particular,
clicking a HUD options menu is not necessarily a configuration-neutral action.
Full current ToonHUD and imported archive compatibility is unverified.

Middle Mann expects cl_hud_minmode 0 upstream. Query the old value before
changing it in the TF2 console. Minimal HUD mode is not minimal viewmodel mode.
ToonHUD has default and centered modes; its website explains the distinction.

## Backups and recovery

Only one detected HUD is active at a time. --replace-hud authorizes backing up
and replacing detected previous HUDs; it does not layer their files together.
Backups are outside tf/custom under $XDG_STATE_HOME/tf2-competitive-backups or
~/.local/state/tf2-competitive-backups. They include a manifest and hashes.
The printed --restore command recovers the exact files touched by that operation,
including earlier HUD customizations. Choosing --hud rayshud again installs a
clean pinned rayshud, not the personalized copy in a backup. Runtime cvars changed
manually or through HUD menus are not automatically restored by file rollback.

## Tests and scope

75 offline tests passed after this change. They cover the preceding 56 cases,
new choices, canonical new folder names, local import validation, dry runs,
checksum failures, changed local ZIP detection, no-op repeat runs, cfg preservation,
exact restoration, and rollback. Fixtures are synthetic archives and temporary
TF2 directories; no test ran TF2 or Steam, and no live HUD rendering was tested.
The environment could not download the real release ZIPs. Upstream release
metadata and startup source were inspected via GitHub.

Run tests beside the script:

```bash
python3 -m unittest -v test_setup_tf2_bazzite.py
```

## Upstream references

- https://github.com/RoseyLemonz/center-hud/releases/tag/v24
- https://github.com/RoseyLemonz/center-hud/blob/v24/cfg/center_hud_init.cfg
- https://github.com/CriticalFlaw/tf2hud-fixes/releases/tag/11.0
- https://github.com/maxiandrew/maxihud/releases/tag/v17.5
- https://github.com/maxiandrew/maxihud/blob/v17.5/cfg/valve.rc
- https://toonhud.com/guide
- https://toonhud.com/faq
- https://github.com/Vexcenot/-middle-mann
- https://github.com/idhud-tf2/idhud
- https://github.com/raysfire/rayshud
- https://github.com/rbjaxter/budhud
