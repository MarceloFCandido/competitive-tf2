# TF2 Bazzite setup — cumulative HUD update v1.5.0

Replace the earlier `setup_tf2_bazzite.py` with this version. It retains every
previous HUD, performance, visual-clarity, dry-run and restore option.
`--hud keep` remains the default. Downloading the new script changes no game files.

## Look before choosing

Open `TF2_HUD_Gallery.html` in a browser. It contains labeled published previews
and source-gallery links for all eight community HUDs discussed. The pictures
load online, so an internet connection is required. Some full-size image hosts
could not be fetched in the authoring environment; links were obtained from the
associated project/catalog pages. They are examples, not screenshots from your
Bazzite installation or exact representations of the installer result. Resolution,
class, theme, game/HUD version and disabled visual effects can change the result.
The Community HUD Fixes picture is an options-menu preview, not gameplay.

## All choices in the same script

| CLI name | Installation method |
|---|---|
| `rayshud` | Existing pinned 2026.0111 release |
| `budhud` | Existing pinned 2511_01 release |
| `idhud` | Existing pinned 4.0.8 release |
| `middlemann` | Existing pinned v26.1 release |
| `centerhud` | New pinned v24 release |
| `communityhudfixes` | New pinned 11.0 release |
| `maxihud` | New named local ZIP import |
| `toonhud` | New named local theme ZIP import |
| `keep` | Do nothing to the current HUD (default) |
| `stock` | Back up/remove detected custom HUDs; use built-in HUD files |

```bash
python3 setup_tf2_bazzite.py --list-huds
```

Only one HUD is made active. The previous one is backed up outside `tf/custom`,
not stacked with the new one. Merely selecting a previously used name installs
its upstream release again; it does not retrieve local customizations from an
old backup. The printed `--restore` command retrieves the exact previous files.

## Preview a HUD-only switch

```bash
python3 setup_tf2_bazzite.py --update-only \
  --hud centerhud --replace-hud --dry-run
```

Substitute `middlemann`, `rayshud`, `budhud`, `idhud`, `communityhudfixes`, or `stock`
as desired. The preview should report `Configuration files: no changes.`
Nothing is downloaded, extracted, written or backed up by the dry run.

Fully exit TF2 and Steam before applying. Run as your normal Bazzite user, without
sudo, and remove `--dry-run` from the reviewed command. It asks for confirmation.
The HUD-only update does not rewrite your config, reinstall mastercomfig, reset
your FPS cap or preset, or re-enable hidden weapons/3D portraits. Do not repeat
old visual/performance flags unless you intend to change them.

## Local ZIP imports: MaxiHud and ToonHUD

MaxiHud's checked v17.5 release has no separately published ZIP asset with a
verified SHA-256 digest available here. Download the ZIP from its upstream
project: https://github.com/maxiandrew/maxihud

ToonHUD creates a ZIP containing your chosen theme in the browser. Choose and
download a theme at https://toonhud.com/ — https://toonhud.com/guide explains it.

```bash
python3 setup_tf2_bazzite.py --update-only --hud toonhud \
  --hud-zip "$HOME/Downloads/toonhud.zip" --replace-hud --dry-run
```

For MaxiHud, use `--hud maxihud` and the actual path to your downloaded ZIP.
These two options require `--hud-zip`. They perform no HUD network download.
The script checks the ZIP structure, size, dangerous paths and source stability,
prints its SHA-256, and can compare an optional `--hud-sha256 EXPECTED_DIGEST`.
A digest computed from a local file does NOT authenticate its publisher.
Use only archives you trust. Packed VPKs inside these new HUD ZIPs are refused.

## Startup compatibility and limitations

The original startup policy and pinned versions for rayshud, budhud, IDHUD and
Middle Mann remain unchanged. HUD startup `cfg/valve.rc` is omitted as before.

Center HUD, Community HUD Fixes, MaxiHud and ToonHUD use **layout-first mode**.
The installer omits standard automatic engine startup/configuration hooks,
including `valve.rc` and `joystick.cfg`, rather than enabling a new HUD's first-run
settings over your applied configuration. It does not initialize their built-in
customization aliases, first-run scripts or automatic workarounds. Consequently
some customizer-menu controls and features may not work without further review.
This is a deliberate trade-off, not a claim of complete upstream functionality.
Other HUD resource/menu code remains installed: manually using menu controls or
other existing scripts can still change game settings. Arbitrary combinations
of mods cannot be guaranteed conflict-free.

Middle Mann expects `cl_hud_minmode 0` and is centered in normal mode. ToonHUD's
FAQ says its minimal mode is the centered mode. The installer does not silently
change this global preference, so record your old value before changing it.
Minimal HUD mode and minimal weapon viewmodels are different settings.

## Restore

After a real update the script prints a command such as:

```bash
python3 /path/to/setup_tf2_bazzite.py --restore /path/to/printed/backup
```

It restores only files affected by that operation and first backs up their
current state. It does not undo unrelated earlier baseline/visual settings or
manual in-game setting changes made afterward. Earlier backup formats remain
supported. Keep backups outside the TF2 `tf` folder.

## Validation

73 offline tests passed on 19 October 2026. They cover preservation of existing
settings, prior CLI choices, pinned downloads, local ZIP imports, idempotence,
no-op previews, conflict checks, backup, exact restore and rollback. Test archives
are artificial. No running TF2/Bazzite session or actual new HUD release ZIP was
tested. This environment could not download the live HUD binaries.

```bash
python3 -m unittest -v test_setup_tf2_bazzite.py
```

The script and test suite should be in the same directory.

## Sources for the new install methods

- https://github.com/RoseyLemonz/center-hud/releases/tag/v24
- https://github.com/RoseyLemonz/center-hud/tree/v24/cfg
- https://github.com/CriticalFlaw/tf2hud-fixes/releases/tag/11.0
- https://github.com/CriticalFlaw/tf2hud-fixes/tree/11.0/cfg
- https://github.com/maxiandrew/maxihud/releases/tag/v17.5
- https://github.com/maxiandrew/maxihud/tree/v17.5/cfg
- https://toonhud.com/guide
- https://toonhud.com/faq

Each gallery card includes the image source and the HUD project link.
