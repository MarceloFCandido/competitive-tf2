# Centered TF2-style HUD option — installer v1.4.0

This revision adds `--hud middlemann`. The existing `rayshud`, `budhud`,
`idhud`, `stock`, and `keep` choices remain available. Nothing is published
online, and nothing on your gaming PC changes until you run the installer there.

Middle Mann preserves TF2-style panels and moves health, ammo and other HUD
information toward the center. IDHUD is still an option, but retains the stock
corner placement. Center HUD is another centered, stock-styled recommendation;
it is **not** an installation choice in this script.

## Preview, then apply

Save the updated `setup_tf2_bazzite.py` in place of the old downloaded script.
Run as your regular Bazzite desktop user, without sudo:

```bash
python3 setup_tf2_bazzite.py --version
python3 setup_tf2_bazzite.py --update-only --hud middlemann --replace-hud --dry-run
```

Version should report **1.4.0**. For this HUD-only command the preview reports
`Configuration files: no changes.` It lists the detected old HUDs that would be
backed up and replaced. Dry-run does not download, write files or create backups.

Fully exit TF2 and Steam, then apply:

```bash
python3 setup_tf2_bazzite.py --update-only --hud middlemann --replace-hud
```

The script asks for confirmation. It verifies the pinned upstream download's
SHA-256 before changing game files. It backs up the detected current HUD outside
`tf/custom`; HUDs are alternatives rather than layers.

No need to repeat your preset, FPS cap, `--visual-clarity`, or viewmodel options.
A HUD-only update does not edit `tf/cfg`, reinstall mastercomfig, or reset your
sensitivity, binds, graphics, visual-clarity modules or weapon visibility.
The default remains `--hud keep`, so updating the script alone never switches HUDs.
An unchanged script-installed HUD is a no-op when selected again.

Use `--tf2-dir '/your/actual/Team Fortress 2'` if library discovery is ambiguous.
Use `--list-huds` to display all installer choices without scanning game files.

## Middle Mann's HUD-mode requirement

The pinned upstream startup script says `cl_hud_minmode 0`; its normal layout
already has centered information. It does not support minimal HUD mode.

This installer does **not** change `cl_hud_minmode` automatically. After installing,
query your current value in the TF2 developer console:

```text
cl_hud_minmode
```

If it is `1`, record that old value, then use:

```text
cl_hud_minmode 0
```

This is a HUD layout preference, separate from minimal weapon viewmodels
(`tf_use_min_viewmodels`). It does not require you to re-enable first-person
weapons, the 3D class portrait, bloom, ragdolls or other visual effects.
Manual console preference changes are not included in the installer's backup;
restore your recorded value yourself when changing back to a HUD that needs it.
If an existing autoexec/class config sets this value, it may reset it later;
the installer does not rewrite those files for a HUD-only switch.

## Preserving startup behavior

The installer removes the HUD's bundled `cfg/valve.rc` from the staged copy.
That file otherwise disables HUD resource caching and schedules a delayed HUD
reload, in addition to setting HUD mode. Those commands are not added to your
existing config. This also means the upstream reload workaround is not applied;
rendering quirks that depended on it may remain.

For Middle Mann, unexpected other files inside the upstream `cfg` directory
cause installation to stop before changing game files. The generic archive
path/symlink/size checks, hash verification, transaction backups and rollback
remain in place. The script does not enable optional extra hitmarkers,
custom crosshairs, vignettes or transparent-viewmodel customizations.

HUD detection cannot identify every arbitrary renamed or packed mod. Review the
preview. HUD menu actions and other custom scripts can still affect runtime
behavior; compatibility with every installation is not guaranteed.

## Undo the switch

Use the full `--restore` command printed after applying the change. It restores
only files affected by that operation and first backs up their current contents.
For a HUD-only switch, that recovers the exact previous HUD, including local
edits, without undoing the earlier performance setup. Restore multiple operations
in reverse order.

Selecting `--hud rayshud` again instead downloads a clean pinned rayshud copy;
it does not retrieve a customized rayshud from a backup.

## Validation

All **56 offline regression tests passed**. They use temporary TF2-shaped folders
and synthetic ZIP files, not installed TF2 or downloaded HUD assets. Tests cover
configuration preservation, Middle Mann staging/startup exclusion, replacement,
exact restoration, existing minimum-HUD preference preservation, dry-run, repeat
runs and the earlier safety/regression cases.

Run the tests beside the updated installer:

```bash
python3 -m unittest -v test_setup_tf2_bazzite.py
```

The Middle Mann release URL, digest and startup source were checked using
GitHub on 2026-10-19. This environment could not retrieve the real ZIP, so live
download/extraction and actual Bazzite/TF2 rendering remain untested here. The
installer verifies the pinned archive on your PC before game-file changes.

## Pinned asset and primary references

- Middle Mann project: https://github.com/Vexcenot/-middle-mann
- Pinned release: https://github.com/Vexcenot/-middle-mann/releases/tag/v26.1
- Startup source: https://github.com/Vexcenot/-middle-mann/blob/v26.1/cfg/valve.rc
- Archive SHA-256: `4cc9721be700e6530f2cb731fae14ddc1d27b2b4c4aa7b42e69a3621513cf899`
- Center HUD (recommendation only): https://github.com/RoseyLemonz/center-hud

Existing mastercomfig, rayshud, budhud and IDHUD pins and startup-policy markers
were retained. This revision does not silently update them.
