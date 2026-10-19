# TF2 Bazzite setup — v1.6.0: acquisition, dependencies and offline previews

This updates the same `setup_tf2_bazzite.py`. All eight HUD options, their release
pins, startup-preservation policies, backups and existing gameplay options remain.
Downloading the new script does not apply it to your game.

## What is new

- `--hud-info NAME` (or `all`) prints exact acquisition links, bundled support-file
  notes, optional requirements, and compatibility limitations. It is a built-in
  reference, not a scan that can diagnose every missing file in your installation.
- `--fetch-hud NAME --output DIRECTORY` saves the **complete original release ZIP**
  for any of the six automatic choices. It checks the pinned SHA-256 but does not
  extract/install it, strip its scripts, scan Steam, or modify the active HUD.
- `--hud-zip FILE` now also works with the six automatic choices. Those imports
  **must match the built-in pinned digest**; supplying your own hash cannot bypass
  the check. MaxiHud and ToonHUD retain their user-selected-archive behaviour.
- `--build-gallery OUTPUT.html` fetches one published example of every HUD and
  embeds all eight as data images in a single HTML file, with no external image,
  font, JavaScript or stylesheet dependency. This is a replacement workflow for
  the earlier remotely linked comparison page, not a claim that page was offline.

All helper commands run in Desktop Mode as your normal user, without `sudo`.
No `pip`, system-font installation, OS package changes or new Python modules are
required. Steam can remain open for information, download-only and gallery modes.
An actual HUD installation/update still requires Steam and TF2 to be closed.

## Where to get each HUD's files

```bash
python3 setup_tf2_bazzite.py --hud-info all
python3 setup_tf2_bazzite.py --hud-info toonhud
```

| Choice | Acquisition |
| --- | --- |
| `middlemann` | Automatic, complete v26.1 release ZIP, checksum-verified. |
| `centerhud` | Automatic, complete v24 release ZIP, checksum-verified. |
| `idhud` | Automatic, complete 4.0.8 release ZIP, checksum-verified. |
| `hudfixes` | Automatic, complete 11.0 release ZIP, checksum-verified. |
| `rayshud` | Automatic, complete 2026.0111 release ZIP, checksum-verified. |
| `budhud` | Automatic, complete 2511_01 release ZIP, checksum-verified. |
| `maxihud` | User downloads Source code (zip) from the v17.5 release page. The checked release had no attached asset digest. The script prints a direct source ZIP link and imports your chosen archive. |
| `toonhud` | User chooses/saves a theme on ToonHUD and uses its Download button. Import the generated theme ZIP, not a theme page or screenshot. |

`--hud keep` is still the default. `--hud stock` still backs up/removes detected
custom HUDs while preserving other settings. No additional HUD is selected
merely because it is present in the catalog.

### Download a complete package without installing it

```bash
python3 setup_tf2_bazzite.py --fetch-hud middlemann \
  --output "$HOME/Downloads/tf2-huds" --dry-run

python3 setup_tf2_bazzite.py --fetch-hud middlemann \
  --output "$HOME/Downloads/tf2-huds"
```

The second command saves `middlemann-v26.1.zip`. It does not enable the HUD or any
of its support scripts. A matching existing ZIP is reused; a different existing
file is never overwritten. Failed downloads are not published as final files.

Preview installation from that ZIP later:

```bash
python3 setup_tf2_bazzite.py --update-only --hud middlemann \
  --hud-zip "$HOME/Downloads/tf2-huds/middlemann-v26.1.zip" \
  --replace-hud --dry-run
```

After reviewing the preview and closing Steam/TF2, remove `--dry-run` to install.
A HUD-only incremental command should report `Configuration files: no changes.`
Do not repeat your earlier FPS, preset, clarity or viewmodel flags unless you
intend to change them. An online install without `--hud-zip` continues to work.

### MaxiHud, ToonHUD and custom fonts

Official acquisition pages:

- MaxiHud release: https://github.com/maxiandrew/maxihud/releases/tag/v17.5
- MaxiHud source ZIP: https://github.com/maxiandrew/maxihud/archive/refs/tags/v17.5.zip
- MaxiHud installation and optional add-ons: https://github.com/maxiandrew/maxihud/blob/v17.5/README.md
- ToonHUD theme editor: https://toonhud.com/
- ToonHUD export/Linux guide: https://toonhud.com/guide
- ToonHUD custom-font and centered-mode FAQ: https://toonhud.com/faq

```bash
python3 setup_tf2_bazzite.py --update-only --hud toonhud \
  --hud-zip "$HOME/Downloads/toonhud.zip" --replace-hud --dry-run
```

Use the actual filename on your PC. Local MaxiHud/ToonHUD hashes record content
and detect changes, but are **not upstream authentication**. An independently
obtained expected hash can be checked with `--hud-sha256 HEX_DIGEST`.

ToonHUD's FAQ says a **Custom** font must be installed on your computer and its
actual family name entered in the editor. No single extra-font package applies
to every theme. Obtain that selected font from its legitimate publisher or
choose a bundled font in the editor. The script does not install system fonts
or redistribute fonts. Font files already provided in an upstream HUD ZIP are
copied as part of that package, not separately fetched from arbitrary websites.

## Important: missing downloads versus intentionally omitted cfg files

Some missing-file errors can be caused by the **installer's existing policy**,
not by an unavailable external dependency. Center HUD, Community HUD Fixes,
MaxiHud and ToonHUD are installed without their bundled `cfg` directories.
The downloaded upstream archives already include those scripts; downloading the
same archive again will not make the conservative install use them.

This can break initialization, customization menus, aliases or other features.
For example, Center HUD's first-run script writes files under `tf/cfg` and uses
demo/logging commands; MaxiHud's startup script runs customization and changes
other console variables. Those are not enabled automatically in this update.
The dependency notes point to the exact official support-file directories.
This update does **not** claim to repair every script-dependent HUD feature or
to provide unmodified/full-featured upstream installations for those four HUDs.

The other four HUDs retain their previous policy: exclude `cfg/valve.rc` where
present; the pinned IDHUD contains no `cfg` directory. Middle Mann still expects
`cl_hud_minmode 0`, which the installer does not force. ToonHUD centered mode uses
minimal HUD mode, which is separate from minimal weapon viewmodels.

A HUD-only update does not rewrite your mastercomfig settings, effects/animation
reductions, weapon visibility, binds, sensitivity, crosshair commands or Steam
launch options. File preservation cannot guarantee runtime behaviour of every
HUD menu, class script or unrelated mod. Restoring a file backup does not undo
console settings changed later by a HUD menu or manually in the game.

## Build an offline image comparison on your gaming PC

The former comparison page depended on external image hosts. This command instead
embeds the actual image bytes in the finished file:

```bash
python3 setup_tf2_bazzite.py \
  --build-gallery "$HOME/Downloads/TF2_HUD_Offline.html"
```

Open that file in Firefox/Chrome. Once **all eight images have been obtained**, the
images display without an internet connection. Each card includes the original
source gallery, project page, dependency notes, and an original-pixel-size toggle.
Sources remain online hyperlinks. The screenshots are published examples, not
captures from your Bazzite installation; versions and your settings may differ.

The builder uses HTTPS, size limits, raster-header validation, and a GitHub API
fallback for GitHub-hosted screenshots. It refuses HTML/login/error responses
instead of embedding them as pictures. It never executes downloaded code.
It does not modify TF2, a HUD, Steam, or game backups. Use a new output filename;
it deliberately refuses to overwrite an existing comparison file.

If any screenshot cannot be obtained, **the default is to stop without writing a
new gallery**, print the failed image URL and original-gallery link, and avoid
pretending every preview worked. To save the available images with explicit
missing-preview panels, add `--gallery-partial`; it returns exit status 2.

For a blocked host, save the screenshot yourself from the listed source gallery.
Name it after the choice (`middlemann.png`, `centerhud.webp`, `maxihud.jpg`, etc.)
and provide that folder; missing local previews still try their online sources:

```bash
python3 setup_tf2_bazzite.py \
  --build-gallery "$HOME/Downloads/TF2_HUD_Offline.html" \
  --gallery-images "$HOME/Downloads/hud-screenshots"
```

Supported extensions are lowercase `.png`, `.jpg`, `.jpeg`, and `.webp`. Keep one
file per HUD name. User-supplied previews are labelled as such. `--dry-run` on
any builder/download command performs **no network requests or writes**.

**Preparation limitation:** screenshot binary downloads were unavailable in the
authoring environment. No completed eight-screenshot offline gallery is being
claimed or supplied here; the new command builds it on your internet-connected PC.
Browser tests use tiny synthetic images to check embedding/rendering, not actual
HUD appearances. The original online-only HTML is not the repaired offline file.

## Backups and tests

Existing transactional backups and `--restore` are unchanged. Use the undo
command printed after an actual installation to recover the exact prior HUD,
including personal edits. Selecting `--hud rayshud` installs a clean pinned copy;
it does not retrieve an old customized copy from backup.

103 offline regression tests pass. They exercise the existing preservation,
restore, rollback and archive-safety behaviour plus the new download-only mode,
source guide, exact-pinned local imports, gallery embedding, API fallback,
partial-image reporting and refusal to overwrite files. Tests use synthetic
archives/images and temporary directories, not real TF2 or live HTTP downloads.

```bash
python3 -m unittest -v test_setup_tf2_bazzite.py
```

## Source notes checked on October 19, 2026

- https://github.com/RoseyLemonz/center-hud/tree/v24/cfg
- https://github.com/RoseyLemonz/center-hud/blob/v24/cfg/center_hud_firstrun.cfg
- https://github.com/CriticalFlaw/tf2hud-fixes/tree/11.0/cfg
- https://github.com/maxiandrew/maxihud/blob/v17.5/cfg/valve.rc
- https://github.com/rbjaxter/budhud/wiki/Installation
- https://toonhud.com/guide
- https://toonhud.com/faq

Image URLs and their original-gallery links are kept in `GALLERY_ITEMS` in the
script. Screenshot hosts can change; the builder reports failures rather than
automatically searching for or inventing replacements.
