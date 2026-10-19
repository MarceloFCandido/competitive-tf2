# TF2 Competitive Setup — Bazzite/Linux

A reproducible TF2 setup with selectable HUDs, incremental updates, backups and restoration. The current installer is **v1.6.0**.

## Motivation

Configure TF2 for competitive play on Bazzite/Linux without rebuilding a personal setup whenever you try another HUD. The script pins and checks downloads for its automatic HUD choices, keeps one active HUD at a time, and backs up affected files before applying changes. Updates to an existing script-managed installation preserve unspecified settings.

A HUD-only update keeps the managed gameplay configuration in place: no mastercomfig reinstall, preset/FPS reset, or rewrite of sensitivity and keybinds. First installation is broader: it installs the baseline and migrates standard configs. Preview the appropriate mode before applying it.

## Requirements and working directory

- Use native Linux TF2 on Bazzite in Desktop Mode, with TF2 already installed through Steam.
- Use **Python 3.9+** as your normal desktop user. Only the standard library is needed; no `sudo`, `pip` or OS package installation.
- Fully exit **TF2 and Steam** before applying an installation, update or restoration. Information and dry-run modes do not apply game changes.
- Internet is needed for remote release downloads and screenshots. Local HUD ZIPs are also supported.

Run commands from the repository root on the gaming PC, with installer and tests together. Adjust the path if you copied the repository elsewhere:

```bash
cd ~/code/git/personal/games/competitive-tf2
python3 setup_tf2_bazzite.py --hud-info all
```

The script discovers normal and Flatpak Steam libraries, including additional locations in `libraryfolders.vdf`. If it finds zero or multiple installations, choose the **Team Fortress 2 game folder**, available through Steam → Properties → Installed Files → Browse:

```bash
python3 setup_tf2_bazzite.py --tf2-dir "/path/to/Team Fortress 2" --dry-run
```

The installation must contain `tf/gameinfo.txt`. Add `--tf2-dir` to the install/update commands below when automatic discovery is ambiguous.

## First installation

Preview the baseline, then apply the same options after reviewing it and closing Steam/TF2:

```bash
python3 setup_tf2_bazzite.py --preset medium --fps-cap 300 --dry-run
python3 setup_tf2_bazzite.py --preset medium --fps-cap 300
```

A first install defaults to Medium, a 300 FPS cap, minimal visible viewmodels and keeping the existing HUD. It backs up `tf/cfg`, migrates standard autoexec/class configs into `cfg/overrides`, and installs pinned mastercomfig data. Existing custom config content can still override settings; review your files and the [configuration examples](#configuration-examples).

The apply command asks for confirmation. A recognized earlier script-managed setup automatically uses incremental mode instead of reinstalling the baseline. `--dry-run` previews actions/diffs without downloads, game-file writes or backups.

## Change only the HUD

For an existing script-managed setup, preview and then apply one HUD choice:

```bash
python3 setup_tf2_bazzite.py --update-only --hud middlemann --replace-hud --dry-run
python3 setup_tf2_bazzite.py --update-only --hud middlemann --replace-hud
```

`--update-only` refuses to install a baseline if it cannot recognize the previous setup. A HUD-only update should report `Configuration files: no changes.` Do not repeat preset, FPS, clarity or viewmodel flags unless you intend to change them. `--replace-hud` permits backing up/replacing existing or customized HUDs; choices are alternatives, not layers.

| Option | Behavior |
|---|---|
| `--list-huds` / `--hud-info all` | Show catalog or acquisition/dependency notes without game discovery or writes. |
| `--hud keep` | Keep the active HUD; the default. |
| `--hud stock --replace-hud` | Back up/remove detected custom HUDs, preserving other settings. |
| `--preset medium`, `low` or `high` | Select a baseline preset, or explicitly change it during an update. |
| `--fps-cap 240` | Explicitly change the FPS cap; 240 is a supported value. |
| `--visual-clarity` | Add cosmetic-motion reductions while keeping the existing `effects` module level. |
| `--viewmodels minimal` or `hidden` | Show minimal weapons or hide weapon/hands; firing/reload timing is unchanged. |
| `--hud-zip PATH` | Import a ZIP. Automatic choices require the pinned checksum; MaxiHud/ToonHUD use your selected archive. |

### Acquire and import HUD packages

These are the release pins in the v1.6.0 installer, rather than a list of the latest upstream releases:

| HUD choice | Package |
|---|---|
| `middlemann` | Complete v26.1 release ZIP; pinned SHA-256. |
| `centerhud` | Complete v24 release ZIP; pinned SHA-256. |
| `idhud` | Complete 4.0.8 release ZIP; pinned SHA-256. |
| `hudfixes` | Complete 11.0 release ZIP; pinned SHA-256. |
| `rayshud` | Complete 2026.0111 release ZIP; pinned SHA-256. |
| `budhud` | Complete 2511_01 release ZIP; pinned SHA-256. |
| `maxihud` | Your selected **Source code (zip)** from [release v17.5](https://github.com/maxiandrew/maxihud/releases/tag/v17.5); no trusted digest is pinned. |
| `toonhud` | Your exported theme ZIP from the [theme editor](https://toonhud.com/); a theme page or screenshot is not the package. |

For an automatic HUD, a local ZIP must match its built-in release checksum. An optional `--hud-sha256 HEX_DIGEST` checks an independently obtained expected hash; it cannot bypass a pinned checksum. For MaxiHud/ToonHUD, a hash calculated from your own file records its contents but does not authenticate the publisher.

Read the requirements before importing an exported ToonHUD theme:

```bash
python3 setup_tf2_bazzite.py --hud-info toonhud
python3 setup_tf2_bazzite.py --update-only --hud toonhud --hud-zip "/path/to/toonhud.zip" --replace-hud --dry-run
```

For MaxiHud, use `--hud maxihud` with the actual downloaded ZIP path. These two choices require a local ZIP. The installer checks archive size, paths and structure; packed VPKs are refused for these isolated HUD imports. The [MaxiHud installation notes](https://github.com/maxiandrew/maxihud/blob/v17.5/README.md) describe optional add-ons that this script does not install automatically.

For a ToonHUD **Custom** font, obtain the chosen font from its publisher, install it yourself and enter its actual family name in the editor, or choose a bundled font. There is no universal extra-font package for every theme. The installer copies font resources supplied in the ZIP but does not install system fonts. See the [export/Linux guide](https://toonhud.com/guide) and [font/centered-mode FAQ](https://toonhud.com/faq).

### HUD configuration compatibility

Center HUD, Community HUD Fixes, MaxiHud and ToonHUD are installed without their bundled `cfg` directories. Downloading the same ZIP again will not enable those omitted scripts. Initialization, customization aliases and menu features may therefore be incomplete. Center HUD's upstream first-run script writes configuration and uses demo/logging commands; MaxiHud's startup script changes console settings. The installer does not enable those scripts automatically.

For Middle Mann, rayshud and budhud, bundled resources are retained but `cfg/valve.rc` is excluded to preserve startup settings. The pinned IDHUD package has no `cfg` directory; its optional recommended console settings are not applied. Arbitrary combinations of other mods and HUD menus can still affect runtime behavior.

Middle Mann expects `cl_hud_minmode 0`. ToonHUD centered mode uses minimal **HUD** mode, which is separate from minimal weapon viewmodels. The installer preserves your current HUD mode; record its value before changing it manually.

## Backups and restoration

Affected files and a manifest are saved under `$XDG_STATE_HOME/tf2-competitive-backups`, or `~/.local/state/tf2-competitive-backups` when unset, before game-file changes. The script attempts rollback if applying a transaction fails.

Use the exact `--restore` command printed after an operation. Replace the example path below with its actual backup directory, and preview first:

```bash
python3 setup_tf2_bazzite.py --restore "/path/printed/after/apply" --dry-run
python3 setup_tf2_bazzite.py --restore "/path/printed/after/apply"
```

Restoration backs up the currently affected files first. Do not combine `--restore` with install/update options. A backup can recover a customized prior HUD; selecting its name again installs a clean pinned copy. Manual Steam launch options and later in-game console changes are outside this file backup.

## Download-only mode and offline images

Save a complete pinned ZIP without installing the HUD:

```bash
python3 setup_tf2_bazzite.py --fetch-hud middlemann --output "$HOME/Downloads/tf2-huds" --dry-run
python3 setup_tf2_bazzite.py --fetch-hud middlemann --output "$HOME/Downloads/tf2-huds"
```

The download command saves the complete original package, including support scripts, without extracting it, scanning Steam or enabling the HUD. A matching existing ZIP is reused; a different existing file is refused. For example, Middle Mann is saved as `middlemann-v26.1.zip` and can later be previewed locally:

```bash
python3 setup_tf2_bazzite.py --update-only --hud middlemann --hud-zip "$HOME/Downloads/tf2-huds/middlemann-v26.1.zip" --replace-hud --dry-run
```

Information, download-only and gallery modes are separate from installation options; do not combine them with `--hud`, `--update-only` or `--tf2-dir`. Steam may remain open for these resource-only modes.

To embed one screenshot per HUD into an offline comparison, choose a **new output filename**:

```bash
python3 setup_tf2_bazzite.py --build-gallery "$HOME/Downloads/TF2_HUD_Offline.html"
```

Once all eight screenshots are obtained, the generated HTML embeds the image bytes and works offline without external images, fonts, scripts or stylesheets. Source/project links still require internet. The builder validates raster headers, uses HTTPS and size limits, and has a GitHub API fallback for GitHub-hosted images. It refuses an existing output file and HTML/login responses; it does not change TF2 or install a HUD.

By default, a missing screenshot stops creation without writing a gallery and reports the image/source-gallery URLs. `--gallery-partial` explicitly permits marked missing previews and returns status 2; that is not a complete gallery.

For a blocked host, save the actual screenshot from its source gallery and name it after the HUD choice, such as `middlemann.png`, `centerhud.webp` or `maxihud.jpg`:

```bash
python3 setup_tf2_bazzite.py --build-gallery "$HOME/Downloads/TF2_HUD_Offline.html" --gallery-images "$HOME/Downloads/hud-screenshots"
```

Use lowercase `.png`, `.jpg`, `.jpeg` or `.webp` extensions and one file per HUD name. Missing local previews still try their online sources. User-supplied previews are labelled as such. `--dry-run` is supported for download/gallery previews with no network or writes. No completed offline image bundle is supplied in this repository.

## HUD comparison

Published upstream/gallery examples, **not captures of this installer running on Bazzite**. Release, resolution, class, theme and HUD mode can change appearance. Images may show weapons, portraits or effects hidden by your settings.

**These Markdown images need internet and access to their original hosts.** If a preview is unavailable, open its source gallery. Click an image for its original size. Screenshots and HUD designs belong to their creators and Valve; inclusion does not imply endorsement.


### Middle Mann

Centered, TF2-styled · Vexcenot

Default-style health and ammo panels moved toward the center.

`--hud middlemann` — Pinned automatic release.

Upstream expects cl_hud_minmode 0; the installer does not force it.

[![Middle Mann — published example 1](https://static.tf2huds.dev/-Middle-Mann/img/Bki5t1X.png)](https://static.tf2huds.dev/-Middle-Mann/img/Bki5t1X.png)

[Source screenshot gallery](https://tf2huds.dev/hud/-Middle-Mann) · [Upstream project / installation](https://github.com/Vexcenot/-middle-mann)

### Center HUD

Centered, TF2-styled · RoseyLemonz

Critical information moved centrally while retaining the default HUD style.

`--hud centerhud` — Pinned automatic release; bundled cfg scripts omitted.

Installer omits bundled cfg scripts; script-dependent customization menus may not work.

[![Center HUD — published example 1](https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/center-hud/centerhudimage.webp)](https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/center-hud/centerhudimage.webp)

[Source screenshot gallery](https://comfig.app/huds/page/center-hud/) · [Upstream project / installation](https://github.com/RoseyLemonz/center-hud)

### MaxiHud

Centered, TF2-styled · maxiandrew and contributors

A centered vanilla-inspired interface with more menu and customization features. The author notes that some screenshots show older versions.

`--hud maxihud` — Import a selected upstream ZIP with --hud-zip.

Import your chosen upstream ZIP. No independently verified release digest is provided. Bundled cfg scripts are omitted; optional scripted features may not work.

[![MaxiHud — published example 1](https://images.gamebanana.com/img/ss/mods/6997885801058.jpg)](https://images.gamebanana.com/img/ss/mods/6997885801058.jpg)

[![MaxiHud — published example 2](https://images.gamebanana.com/img/ss/mods/6997885854f06.jpg)](https://images.gamebanana.com/img/ss/mods/6997885854f06.jpg)

[![MaxiHud — published example 3](https://images.gamebanana.com/img/ss/mods/69978859bcdd9.jpg)](https://images.gamebanana.com/img/ss/mods/69978859bcdd9.jpg)

[![MaxiHud — published example 4](https://images.gamebanana.com/img/ss/mods/69978856896c8.jpg)](https://images.gamebanana.com/img/ss/mods/69978856896c8.jpg)

[Source screenshot gallery](https://github.com/maxiandrew/maxihud#screenshots) · [Upstream project / installation](https://github.com/maxiandrew/maxihud/releases/tag/v17.5)

### rayshud

Centered, simplified · raysfire and contributors

A simplified layout with prominent health/ammo numbers and little decoration.

`--hud rayshud` — Pinned automatic release.

Second image is the gallery minimal-mode example. The installer preserves your current HUD mode.

[![rayshud — published example 1](https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/rayshud/hud.webp)](https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/rayshud/hud.webp)

[![rayshud — published example 2](https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/rayshud/hud-minmode.webp)](https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/rayshud/hud-minmode.webp)

[Source screenshot gallery](https://comfig.app/huds/page/rayshud/) · [Upstream project / installation](https://github.com/raysfire/rayshud)

### budhud

Centered, simplified · Whisker and contributors

Another redesigned HUD, inspired by yahud and rayshud; not a stock-art-style restoration.

`--hud budhud` — Pinned automatic release.

The additional image shows the Medic layout. Screenshots are examples, not this installer running on Bazzite.

[![budhud — published example 1](https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/budhud/budhud-04-player.webp)](https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/budhud/budhud-04-player.webp)

[![budhud — published example 2](https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/budhud/budhud-07-medic.webp)](https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/budhud/budhud-07-medic.webp)

[Source screenshot gallery](https://comfig.app/huds/page/budhud/) · [Upstream project / installation](https://github.com/rbjaxter/budhud)

### Improved Default HUD

Stock-style, corner layout · Eniere; maintained by Tiagoquix

Retains the original layout with damage-text, target-ID and other UI improvements. Not a centered rayshud replacement.

`--hud idhud` — Pinned automatic release.

Stock-style corner placement rather than a centered layout. The pinned package has no startup cfg scripts.

[![Improved Default HUD — published example 1](https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/improved-default-hud/2-combat.webp)](https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/improved-default-hud/2-combat.webp)

[![Improved Default HUD — published example 2](https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/improved-default-hud/3-scoreboard.webp)](https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/improved-default-hud/3-scoreboard.webp)

[Source screenshot gallery](https://comfig.app/huds/page/improved-default-hud/) · [Upstream project / installation](https://github.com/idhud-tf2/idhud)

### Community HUD Fixes

Stock-style, corner layout · CriticalFlaw and contributors

Default-style interface repairs and quality-of-life changes, rather than a centralized redesign.

`--hud hudfixes` — Pinned automatic release; bundled cfg scripts omitted.

Bundled cfg scripts are omitted. Its scripted customization menu may not work with this conservative installation.

[![Community HUD Fixes — published example 1](https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/hud-fixes/hud.webp)](https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/hud-fixes/hud.webp)

[![Community HUD Fixes — published example 2](https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/hud-fixes/hud-minmode.webp)](https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/hud-fixes/hud-minmode.webp)

[Source screenshot gallery](https://comfig.app/huds/page/hud-fixes/) · [Upstream project / installation](https://github.com/CriticalFlaw/tf2hud-fixes)

### ToonHUD

Theme-dependent · Griever

An example only: you choose the fonts, colors and theme. ToonHUD has default and centered modes.

`--hud toonhud` — Import an exported theme ZIP with --hud-zip.

The export you choose determines the appearance. Full current TF2/Bazzite compatibility is unverified. Bundled cfg scripts are omitted.

[![ToonHUD — published example 1](https://static.tf2huds.dev/ToonHUD/img/VkMCo8g.jpg)](https://static.tf2huds.dev/ToonHUD/img/VkMCo8g.jpg)

[Source screenshot gallery](https://tf2huds.dev/hud/ToonHUD) · [Upstream project / installation](https://toonhud.com/guide)

## Configuration examples

These CFGs preserve the initial conversation guide. They are reference examples for manual adaptation, rather than files generated by the current installer:

- [Personal configuration](examples/tf/cfg/overrides/autoexec.cfg)
- [Performance modules](examples/tf/cfg/overrides/modules.cfg)
- [Medic alternative](examples/medic/tf/cfg/overrides/autoexec.cfg), with additional autoheal and target-marker options.

All three files retain their original bytes.

## Tests

The [regression suite](test_setup_tf2_bazzite.py) has 103 test methods using synthetic archives/images and temporary directories. To run it manually:

```bash
python3 -m unittest -v test_setup_tf2_bazzite.py
```

The installer and tests were not executed during this documentation/repository reorganization. Commands were checked against the v1.6.0 argument declarations and code.

## Source and archive records

The installer keeps acquisition/dependency links in `HUD_HELP` and screenshot sources in `GALLERY_ITEMS`. These notes describe the pinned v1.6.0 behavior; upstream hosts and optional requirements may change. Support-file references include [Center HUD](https://github.com/RoseyLemonz/center-hud/tree/v24/cfg), [Community HUD Fixes](https://github.com/CriticalFlaw/tf2hud-fixes/tree/11.0/cfg), [MaxiHud](https://github.com/maxiandrew/maxihud/tree/v17.5/cfg) and the [budhud installation guide](https://github.com/rbjaxter/budhud/wiki/Installation).

Recovery records and tools are indexed in [.agent/ARCHIVE.md](.agent/ARCHIVE.md). Literal historical guides are retained there as source evidence, and previous filenames remain in Git. This root file is the single current README and the source of installation instructions.
