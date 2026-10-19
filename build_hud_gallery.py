from pathlib import Path
import html
import json

huds = [
 {'id':'middlemann','name':'Middle Mann','group':'TF2-like and centered',
  'caption':'Familiar TF2 panels, with health and ammunition brought inward. This example shows Heavy in combat.',
  'image':'https://static.tf2huds.dev/-Middle-Mann/img/Bki5t1X.png',
  'source':'https://tf2huds.dev/hud/-Middle-Mann',
  'project':'https://github.com/Vexcenot/-middle-mann',
  'install':'Pinned download: v26.1',
  'note':'Normal HUD mode is already centered. Upstream expects cl_hud_minmode 0; the installer does not force it.'},
 {'id':'centerhud','name':'Center HUD','group':'TF2-like and centered',
  'caption':'A centered interpretation of the stock TF2 interface. Compare its panels and meter positions with Middle Mann.',
  'image':'https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/center-hud/centerhudimage.webp',
  'source':'https://comfig.app/huds/page/center-hud/',
  'project':'https://github.com/RoseyLemonz/center-hud',
  'install':'Pinned download: v24; layout-first mode',
  'note':'Automatic first-run/customizer initialization is excluded. Built-in customizer menus may not initialize.'},
 {'id':'maxihud','name':'MaxiHud','group':'TF2-like and centered',
  'caption':'TF2-style artwork with a centered layout and more extensive interface customization. The images below are from the upstream README.',
  'image':'https://images.gamebanana.com/img/ss/mods/6997885801058.jpg',
  'more':['https://images.gamebanana.com/img/ss/mods/6997885854f06.jpg',
          'https://images.gamebanana.com/img/ss/mods/69978859bcdd9.jpg',
          'https://images.gamebanana.com/img/ss/mods/69978856896c8.jpg'],
  'source':'https://github.com/maxiandrew/maxihud/blob/v17.5/README.md#screenshots',
  'project':'https://github.com/maxiandrew/maxihud',
  'install':'Import your trusted upstream ZIP: --hud-zip PATH',
  'note':'Local ZIP import is not a verified pinned download. Startup overrides are excluded; some customization features may not work.'},
 {'id':'rayshud','name':'rayshud','group':'Centered, more minimal styling',
  'caption':'Your existing reference: large health and ammunition figures with little decoration. Shown here in the normal layout.',
  'image':'https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/rayshud/hud.webp',
  'source':'https://comfig.app/huds/page/rayshud/',
  'project':'https://github.com/raysfire/rayshud',
  'install':'Pinned download: 2026.0111',
  'note':'Retained from the previous installer. No automatic switch occurs when you download the updated Python file.'},
 {'id':'budhud','name':'budhud','group':'Centered, more minimal styling',
  'caption':'A redesigned interface with a restrained presentation. Compare the spacing and typography with rayshud.',
  'image':'https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/budhud/budhud-04-player.webp',
  'source':'https://comfig.app/huds/page/budhud/',
  'project':'https://github.com/rbjaxter/budhud',
  'install':'Pinned download: 2511_01',
  'note':'Retained from the previous installer. The upstream catalog also includes Engineer, Medic and scoreboard previews.'},
 {'id':'toonhud','name':'ToonHUD','group':'Theme-dependent; centered mode available',
  'caption':'The official FAQ compares the default layout with centered minimal mode. ToonHUD appearance depends on the theme you choose; this is an example, not a universal theme.',
  'image':'https://i.imgur.com/YBG8NkC.png',
  'source':'https://toonhud.com/faq',
  'project':'https://toonhud.com/',
  'install':'Import a theme ZIP: --hud-zip PATH',
  'note':'The website packages your selected theme into the ZIP. The installer does not change your minimal-HUD setting or download a theme on your behalf.'},
 {'id':'idhud','name':'Improved Default HUD (IDHUD)','group':'Stock-style, corner-based',
  'caption':'Keeps the stock layout while improving readability and fixing interface details. Included for comparison, but not the best match for your centered-information preference.',
  'image':'https://raw.githubusercontent.com/mastercomfig/hud-db/main/hud-resources/improved-default-hud/2-combat.webp',
  'source':'https://comfig.app/huds/page/improved-default-hud/',
  'project':'https://github.com/idhud-tf2/idhud',
  'install':'Pinned download: 4.0.8',
  'note':'Optional recommended console settings are not applied. Your existing configuration remains unchanged by a HUD-only update.'},
 {'id':'communityhudfixes','name':'Community HUD Fixes','group':'Stock-style, corner-based',
  'caption':'Corrections and optional refinements to the default interface. This preview shows its options menu, not an in-match layout.',
  'image':'https://images.gamebanana.com/img/ss/mods/6629977e47754.jpg',
  'source':'https://gamebanana.com/mods/26450',
  'project':'https://github.com/CriticalFlaw/tf2hud-fixes',
  'install':'Pinned download: 11.0; layout-first mode',
  'note':'Startup/customizer initialization is omitted; the options screen is an upstream preview, not a promise that every control works in layout-first mode.'},
]
esc=html.escape
cards=[]
for n,h in enumerate(huds,1):
    command=f"python3 setup_tf2_bazzite.py --update-only --hud {h['id']} --replace-hud"
    if h['id'] in ('maxihud','toonhud'):
        command+=' --hud-zip "/path/to/downloaded-hud.zip"'
    command+=' --dry-run'
    more=''
    if h.get('more'):
        more='<details><summary>More published screenshots</summary>'+''.join(
            f'<a href="{esc(u)}" target="_blank" rel="noopener noreferrer"><img src="{esc(u)}" alt="Additional {esc(h["name"])} screenshot" loading="lazy" referrerpolicy="no-referrer"></a>' for u in h['more'])+'</details>'
    cards.append(f'''<article id="{h['id']}">
      <div class="cardhead"><div class="number">{n:02d}</div><div><p class="eyebrow">{esc(h['group'])}</p><h2>{esc(h['name'])}</h2></div></div>
      <a class="shot" href="{esc(h['image'])}" target="_blank" rel="noopener noreferrer" aria-label="Open full-size {esc(h['name'])} screenshot">
      <img src="{esc(h['image'])}" alt="Published {esc(h['name'])} preview. If the image does not load, use the source gallery link below." loading="{'eager' if n<3 else 'lazy'}" referrerpolicy="no-referrer"></a>
      <div class="body"><p>{esc(h['caption'])}</p>
      <p class="links"><a href="{esc(h['source'])}" target="_blank" rel="noopener noreferrer">Screenshot source / gallery</a> · <a href="{esc(h['project'])}" target="_blank" rel="noopener noreferrer">HUD project</a></p>
      <p class="install"><code>--hud {h['id']}</code><br>{esc(h['install'])}</p>
      <p class="note">{esc(h['note'])}</p>{more}
      <details><summary>Preview installation command (does not apply changes)</summary><pre>{esc(command)}</pre></details>
      </div></article>''')
nav=''.join(f'<a href="#{h["id"]}">{esc(h["name"])}</a>' for h in huds)
page='''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src https:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>TF2 HUD comparison — eight options</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#202120;color:#eceae4;font:17px/1.55 system-ui,-apple-system,sans-serif}header,main,footer{max-width:1500px;margin:auto;padding:28px}header{padding-top:45px}h1{font-size:clamp(28px,4vw,46px);line-height:1.15;margin:7px 0 20px}h2{font-size:25px;margin:0;line-height:1.2}p{margin:0 0 16px}a{color:#edcc9b;text-underline-offset:3px}header p{max-width:1050px}.eyebrow{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#c7beb1;margin:0 0 5px}nav{display:flex;gap:10px;flex-wrap:wrap;margin-top:23px}nav a{border:1px solid #605a52;border-radius:5px;padding:7px 12px;text-decoration:none;font-size:14px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:25px;align-items:start}article{background:#2b2d2b;border:1px solid #4f514c;border-radius:9px;overflow:hidden;scroll-margin-top:20px}.cardhead{display:flex;gap:16px;align-items:center;padding:22px}.number{font-size:23px;font-variant-numeric:tabular-nums;color:#cbb38e}.shot{display:block;background:#131413;min-height:140px}img{width:100%;height:auto;display:block;object-fit:contain}.shot img{aspect-ratio:16/9}.body{padding:22px}.note{font-size:14px;color:#c8c9c3}.install{border-top:1px solid #50524d;padding-top:14px;font-size:14px}code,pre{font:14px/1.55 ui-monospace,monospace}code{color:#f4d3a0}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#171918;padding:14px;border-radius:4px}.links{font-size:14px}details{margin-top:13px}summary{cursor:pointer;color:#edcc9b;font-size:14px}details img{margin-top:12px}.notice{padding:15px 18px;border-left:3px solid #c7aa7f;background:#2c2c28}.small{font-size:14px;color:#c2c4bd}@media(max-width:950px){.grid{grid-template-columns:1fr}header,main,footer{padding:20px}.shot img{aspect-ratio:auto}}@media print{body{background:white;color:black}.grid{grid-template-columns:1fr}article{break-inside:avoid}nav,details{display:none}}
</style></head><body><header><p class="eyebrow">TF2 · Bazzite / Linux · Preview gallery</p><h1>Compare the HUDs before changing anything.</h1>
<p>All eight community HUDs discussed are represented below. For <strong>centered information with TF2's visual style</strong>, compare Middle Mann, Center HUD and MaxiHud first. Rayshud is included as your reference.</p>
<p class="notice"><strong>Published examples, not captures of your PC.</strong> Screenshots may show older versions, different resolutions, classes, themes or settings. Your hidden viewmodels and disabled 3D portrait will not be re-enabled just to match a picture. The Community HUD Fixes image is an options-menu preview.</p>
<p class="small">Open this HTML file in Firefox or another browser. Images load from their original online hosts; an internet connection is required. Click an image for full size. When a host blocks the image, use its source-gallery link. Some image hosts could not be fetched in the authoring environment; the URLs come from the linked project/catalog pages.</p><nav>'''+nav+'''</nav></header><main class="grid">'''+''.join(cards)+'''</main><footer>
<h2>Installer behavior</h2><p>Use <code>setup_tf2_bazzite.py</code> v1.5.0. The old HUD choices and all performance, visual, dry-run and restore options remain in this one cumulative script. <code>--hud keep</code> is still the default; <code>--hud stock</code> removes detected custom HUDs after backup. Only one HUD is active at a time.</p>
<p>Center HUD and Community HUD Fixes are new pinned downloads. MaxiHud and ToonHUD are named local ZIP import options. The latter are not authenticated upstream downloads: their hashes identify the chosen bytes. The four new choices omit automatic startup hooks to protect the earlier setup; this may prevent full in-game customization menus from initializing.</p>
<p>HUD-only incremental updates do not rewrite your existing configuration files. Arbitrary HUD menu actions and other scripts can still change in-game settings; this is not a compatibility guarantee for every mod. Current screenshots are not proof of Bazzite runtime compatibility.</p>
<p class="small">Sources and image ownership: the HUD authors and the project/catalog pages linked on each card. No fonts or HUD assets are bundled in this gallery. Prepared 19 October 2026.</p></footer></body></html>'''
Path('/mnt/data/TF2_HUD_Gallery.html').write_text(page)
Path('/mnt/data/hud_preview_sources.json').write_text(json.dumps(huds,indent=2)+'\n')
print('Created gallery with',len(huds),'labeled HUD cards.')
