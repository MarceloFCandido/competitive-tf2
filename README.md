# TF2 Competitive Setup — Bazzite/Linux

A reproducible TF2 setup with selectable HUDs, incremental updates, backups and restoration. The current installer is **v1.6.2**.

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

`--update-only` refuses to install a baseline if it cannot recognize the previous setup. HUD-only updates preserve competitive settings. Enabling the MaxiHUD menu adds a startup block and support data to the preview; updates to other HUDs normally report `Configuration files: no changes.` Do not repeat preset, FPS, clarity or viewmodel flags unless you intend to change them. `--replace-hud` permits backing up/replacing existing or customized HUDs; choices are alternatives, not layers.

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

These are the release pins in the v1.6.2 installer, rather than a list of the latest upstream releases:

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

Center HUD, Community HUD Fixes and ToonHUD are installed without their bundled `cfg` directories. MaxiHUD uses the minimal integration described below. Downloading the same ZIP again will not enable those omitted scripts. Initialization, customization aliases and menu features may therefore be incomplete. Center HUD's upstream first-run script writes configuration and uses demo/logging commands. MaxiHUD's full startup script also changes console settings. Those full startup scripts remain excluded.

For Middle Mann, rayshud and budhud, bundled resources are retained but `cfg/valve.rc` is excluded to preserve startup settings. The pinned IDHUD package has no `cfg` directory; its optional recommended console settings are not applied. Arbitrary combinations of other mods and HUD menus can still affect runtime behavior.

Middle Mann expects `cl_hud_minmode 0`. ToonHUD centered mode uses minimal **HUD** mode, which is separate from minimal weapon viewmodels. The installer preserves your current HUD mode; record its value before changing it manually.

## Repair or enable the MaxiHUD v17.5 Settings tabs

Version **1.6.1** fixes the v1.6.0 installation that opened Settings without switching categories. It retains six checksum-reviewed customization files (general, colors, fonts, crosshairs, streamer and reset) and loads their alias definitions through `tf2_competitive_maxihud_menu.cfg`. A separate block is appended to `tf/cfg/overrides/autoexec.cfg`, the mastercomfig startup override. Existing config bytes, binds, sensitivity, preset, FPS cap, visual-clarity settings and viewmodel choices are preserved.

The script creates `tf/cfg/maxihud/` and a minimal menu-data file when needed. Existing customization data and your logging profile are retained. It still excludes `valve.rc`, `joystick.cfg`, the full customization bootstrap and `maxihud_first_run.cfg`; it does not enable demo-recording initialization or `sv_allow_point_servercommand always`.

Only the four reviewed `mat_queue_mode` assignments in the menu's open, close, restart and Apply commands are removed. The remaining menu commands and resource content stay in place. Buttons such as **Reset All** can still change the upstream HUD's console settings when you choose them; registration of aliases does not execute those actions. This is not a guarantee that every optional HUD feature works.

Version **1.6.2** fixes rejection of the official ZIP linked below. Upstream [`.gitattributes`](https://github.com/maxiandrew/maxihud/blob/18fb7f1e2903ebab15e811c9718726ddce51b0f4/.gitattributes) exports `.res` files with CRLF endings, while the reviewed raw-file hashes use LF. Validation converts only CRLF to LF for comparison of `resource/gamemenu.res`, the customization-menu frame and `scripts/hudlayout.res`. The six CFG hashes and every other byte remain strict. The ZIP is used directly and its original digest is recorded; adapted resources retain their original line endings.

Use the unmodified [v17.5 Source code ZIP](https://github.com/maxiandrew/maxihud/archive/refs/tags/v17.5.zip). The six cfg files, two patched menu resources and layout include are checked against [commit 18fb7f1](https://github.com/maxiandrew/maxihud/tree/18fb7f1e2903ebab15e811c9718726ddce51b0f4); missing or changed support files stop the operation before applying game changes. Other resource files and the complete user-selected ZIP are not authenticated by these nine checks.

On the Bazzite PC, use your actual ZIP filename; this example assumes `~/Downloads/maxihud-17.5.zip`:

```bash
python3 setup_tf2_bazzite.py --update-only --hud maxihud --hud-zip "$HOME/Downloads/maxihud-17.5.zip" --replace-hud --dry-run
```

Review the startup block, support files and replacement, then fully close Steam/TF2 and apply:

```bash
python3 setup_tf2_bazzite.py --update-only --hud maxihud --hud-zip "$HOME/Downloads/maxihud-17.5.zip" --replace-hud
```

The old `isolate-cfg-v1` MaxiHUD is recognized as needing replacement. The new menu policy is idempotent: repeating the same options with unchanged files creates no new backup. Switching to another HUD removes only the added startup block; customization data and the logging profile remain for future use. The printed restore command recovers the files affected by this operation.

### Logging behavior and in-game verification

Upstream menu actions write their selected layout into `tf/cfg/maxihud/*.txt` using Source console logging. Each write temporarily uses `con_timestamp 0`, then calls the separate `tf2_setup_maxihud_log_restore` alias. Loading the definitions does not change logging. The default restoration is **`con_logfile console.log; con_timestamp 0`**, matching the upstream unlog convention, rather than an automatic snapshot of your session.

For different logging preferences, edit `tf/cfg/tf2_competitive_maxihud_logging.cfg` before using the menu. For example, to restore a chosen log file with timestamps:

```cfg
alias tf2_setup_maxihud_log_restore "con_logfile tournament.log; con_timestamp 1"
```

That profile is preserved on reapplication. Source aliases cannot capture arbitrary current ConVar values; set the restore profile to your intended values, and close the menu before manually changing logging. Menu writes temporarily redirect console output, and later in-game changes are outside the installer's file-backup guarantee.

After restarting TF2, open **Settings**, try **General/Colors/Fonts**, then **Apply/Close**, and compare `mat_queue_mode` before and after. Check `con_logfile` and `con_timestamp` against your restore profile. The installer and synthetic regression suite were tested with temporary files; actual menu rendering and behavior on TF2/Bazzite still need your verification.

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

Six reviewed customization alias files and a minimal persistent loader enable menu categories. Full startup and first-run scripts stay excluded. The whole ZIP has no pinned release digest; optional features and TF2 rendering still need verification.

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

The [regression suite](test_setup_tf2_bazzite.py) has 125 synthetic tests and five opt-in official-ZIP integration tests. The normal run skips the five official-ZIP cases unless their input path is supplied:

```bash
python3 -m unittest -v test_setup_tf2_bazzite.py
```

To include the official ZIP tests, download the same v17.5 ZIP linked above and supply its actual local path:

```bash
TF2_MAXIHUD_OFFICIAL_ZIP="$HOME/Downloads/maxihud-17.5.zip" python3 -m unittest -v test_setup_tf2_bazzite.py
```

All **130 tests passed**, with all five official-ZIP cases enabled and production hashes unmocked in that suite. HTTP is blocked during tests. The official archive is read as data and remains byte-identical; installation, repeat/no-op and exact restoration run only in artificial TF2 directories. LF/CRLF resources are exercised through both validation entry points; one-byte changes, absent files and changed CFG endings are rejected. Existing migration, alias/loader, menu-edit, backup, rollback and dry-run coverage remains. No HUD CFG was executed or real TF2 installation changed.

## Source and archive records

The installer keeps acquisition/dependency links in `HUD_HELP` and screenshot sources in `GALLERY_ITEMS`. These notes describe the pinned v1.6.2 behavior; upstream hosts and optional requirements may change. Support-file references include [Center HUD](https://github.com/RoseyLemonz/center-hud/tree/v24/cfg), [Community HUD Fixes](https://github.com/CriticalFlaw/tf2hud-fixes/tree/11.0/cfg), [MaxiHud](https://github.com/maxiandrew/maxihud/tree/v17.5/cfg) and the [budhud installation guide](https://github.com/rbjaxter/budhud/wiki/Installation).

Recovery records and tools are indexed in [.agent/ARCHIVE.md](.agent/ARCHIVE.md). Literal historical guides are retained there as source evidence, and previous filenames remain in Git. This root file is the single current README and the source of installation instructions.
