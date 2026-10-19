# TF2 setup v1.3.0 — stock-style HUD choices

This update adds **Improved Default HUD** and **Middle Mann** as alternatives to
rayshud and budhud. It does not install several active HUDs at once.

## Existing installation: preview, then apply

Save the new `setup_tf2_bazzite.py`, replacing the old downloaded script. On
Bazzite, use a terminal as your normal user, not sudo/root.

```bash
python3 setup_tf2_bazzite.py --update-only --hud idhud --replace-hud --dry-run
```

Check that the preview says `Configuration files: no changes.` and lists only
HUD paths for replacement. Fully exit TF2 and Steam before applying:

```bash
python3 setup_tf2_bazzite.py --update-only --hud idhud --replace-hud
```

This asks for confirmation. The HUD-only command leaves the installed
mastercomfig VPK, preset, FPS cap, effects modules, viewmodel settings, binds,
sensitivity, and other configuration files unchanged. Do not add baseline or
visual options just to switch the HUD.

No packages, OS settings, Steam account files, Proton selection, launch options,
or system fonts are modified. The selected upstream HUD package can contain its
own bundled assets; none of its updater programs are executed.

## Choices

```bash
python3 setup_tf2_bazzite.py --list-huds
```

| `--hud` value | What it does |
| --- | --- |
| `keep` | Leave the current HUD alone; this remains the default. |
| `idhud` | Improved Default HUD 4.0.8. Original TF2 styling and corner placement, with readability/UI fixes. |
| `middlemann` | Middle Mann v26.1. TF2 styling with health/ammo moved toward the center. |
| `rayshud` | Existing pinned rayshud 2026.0111 option. |
| `budhud` | Existing pinned budhud 2511_01 option. |
| `stock` | Back up and remove detected custom HUDs; no HUD download or configuration reset. |

Replace `idhud` in the preview/apply command with another choice to switch.
No HUD is downloaded just because its name is listed in the script.

All downloaded HUD ZIPs use fixed upstream release URLs and SHA-256 digests.
Existing rayshud, budhud, and mastercomfig release pins are unchanged.

## Safety and restoration

The script detects common unpacked HUD layouts, including mixed-case resource
filenames, installer-marked HUDs, and VPKs whose names contain `hud`.
`--replace-hud` is required to remove a different or customized HUD. Review the
exact paths in the preview. Arbitrary renamed/packed mods can escape detection;
this is not a guarantee against every possible mod conflict.

Backups are outside the game's `tf` folder, under
`$XDG_STATE_HOME/tf2-competitive-backups` or
`~/.local/state/tf2-competitive-backups`. An undo command is printed after every
applied operation. It restores the exact affected files, including custom edits
in the prior HUD. A switch back by HUD name installs its pinned upstream copy,
not your previous personalized copy. Use the printed `--restore` command for the
latter. Keep backup folders until you no longer need them.

Dry runs and `--list-huds` do not download, write files, or create backups.
Reapplying an unchanged HUD is a no-op; changed/customized copies require consent.
Older script backups are still readable.

## Compatibility notes

Improved Default HUD explicitly lists Linux support. Its pinned source has no
`cfg` startup override; the installer does not apply its optional recommended
console settings.

Middle Mann's pinned startup file says it is designed for `cl_hud_minmode 0`.
The installer does not force this setting. It excludes bundled `cfg/valve.rc`
files as before, avoiding startup-enforced cvars and caching/reload tricks.
Consequently, some upstream HUD workarounds are omitted. Its optional vignette
customizations are disabled in the pinned source. Do not enable unrelated HUD
screen overlays or visual options unless you actually want those changes.

HUD-only updates preserve configuration bytes; layouts, colors, text sizes, and
built-in UI animations can naturally differ between HUDs. Other scripts/binds,
server restrictions, display settings, or future TF2 changes can still affect
rendering. Restart TF2 when switching. Installing a HUD is not a promise of an
FPS increase.

## Verification performed

48 offline automated tests passed in a Linux container, covering HUD switching,
exact backup restoration, rollback, no-op updates, dry runs, preservation of
existing effects/viewmodel/preset settings, ZIP safety, and checksum handling.
Tests use temporary directories and synthetic archives/network responses.
The two new release URLs and SHA-256 values were read from GitHub's release API;
live binary downloads were unavailable in the development environment. Neither
HUD rendering nor installation on Bazzite/TF2 hardware was tested here.

The optional test file belongs next to the installer and can be run with:

```bash
python3 -m unittest -v test_setup_tf2_bazzite.py
```

## Upstream references

- Improved Default HUD: https://github.com/idhud-tf2/idhud
- Pinned IDHUD release: https://github.com/idhud-tf2/idhud/releases/tag/4.0.8
- Middle Mann: https://github.com/Vexcenot/-middle-mann
- Pinned Middle Mann release: https://github.com/Vexcenot/-middle-mann/releases/tag/v26.1
- Middle Mann startup config: https://github.com/Vexcenot/-middle-mann/blob/v26.1/cfg/valve.rc
- Middle Mann optional vignette: https://github.com/Vexcenot/-middle-mann/blob/v26.1/customizations/vignette.res
- rayshud: https://github.com/raysfire/rayshud
- budhud: https://github.com/rbjaxter/budhud

These are community HUDs. This script is an independent installer, not an
upstream HUD release or an official Valve/Bazzite tool.
