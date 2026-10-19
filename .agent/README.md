# Agent archive and recovery records

The current installer, product tests, usage guide and illustrated HUD comparison are reached through the [main README](../README.md). Original configuration examples are in [examples](../examples/README.md).

| Area | Contents |
|---|---|
| [docs](docs/REVISIONS.md) | Revision and attachment inventories, uploads, gaps and access records. |
| [provenance](provenance/capture.json) | Original captured messages, events, manifests and recovery receipts. |
| [work](work/) | Historical patches, generators, older tests and working copies used to prepare artifacts. |
| [reconstructions](reconstructions/incomplete-v1.5.0/README.md) | Incomplete historical candidates, kept separate from uploaded originals. |
| [history](history/case-variants/TF2_HUD_UPDATE_README.md) | Earlier documentation, including the uppercase filename variant. |
| [manifests](manifests/layout.json) | Old-to-current path mapping, integrity checks and documentation verification. |
| [tools](tools/check_layout.py) | The read-only layout verifier and the local README preview helper. |

## Recovery index

- [Uploaded originals](docs/UPLOADS.md)
- [Revisions and source commits](docs/REVISIONS.md)
- [Attachments delivered in the conversation](docs/ATTACHMENTS.md)
- [Remaining gaps and recovery limits](docs/GAPS.md)
- [Shared-link rechecks](docs/REFRESH.md)
- [Historical browser-access records](docs/BROWSER_ACCESS.md)

There are 52 artifact revision records: 18 literal bodies, 22 static reconstructions, two incomplete candidates and ten uploaded originals. These are not 52 distinct binary versions, and do not establish recovery of every historical attachment.

## Historical paths and integrity

Captured evidence, archived code, receipts and historical manifests were moved without changing their bytes. Fields such as `repo_path`, `/mnt/data/` paths and old computer paths describe their source or source commit. Use the [layout map](manifests/layout.json) to locate current files.

The original comparison HTML was removed from the working tree after all 15 images across eight HUDs were visibly confirmed in the rendered README in Safari. Its unchanged original remains in Git:

```bash
git show 618beb0913ab4670bdc0a035e4fa7fe376a99963:TF2_HUD_Visual_Comparison.html
```

[Visual verification](manifests/visual-comparison.json) records the source images, HTTP preflight, browser decoding, visible inspection and limits. The README references the original remote images; it is not an offline image bundle. [Command verification](manifests/readme-command-audit.json) records static inspection of the v1.6.0 options and relevant behavior.

The historical [final-files manifest](provenance/final-files.sha256.json) belongs to the snapshot before organization. The [current manifest](manifests/files.sha256.json) covers all current files declared by this organization except itself. The [validation receipt](manifests/validation.json) records the checks before the organization commit.

```bash
python3 .agent/tools/check_layout.py
```

This verifier only reads files, Git objects, hashes and links. It does not import the installer, execute product tests or access the network. Historical scripts in `work/` and `provenance/tools/` retain old paths and assumptions; they are archived evidence.

## Optional local README preview

With Pandoc installed, run `python3 .agent/tools/render_readme.py` from the repository root, then `python3 -m http.server 8765 --bind 127.0.0.1`. Open `http://127.0.0.1:8765/.agent/preview/README.html` in a browser. This helper only renders the README and adds an image-load diagnostic; it does not execute the installer or archived scripts. Generated previews are ignored by Git. Stop the local server when finished.
