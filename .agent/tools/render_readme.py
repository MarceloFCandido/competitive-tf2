"""Render the actual README with installed Pandoc for local visual inspection."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
PREVIEW = ROOT / '.agent/preview'
PREVIEW.mkdir(exist_ok=True)
HEADER = PREVIEW / 'header.html'
HEADER.write_text("""<base href="http://127.0.0.1:8765/">
<style>
body{font-family:system-ui,sans-serif;max-width:1050px!important;margin:0 auto!important;padding:95px 30px 40px!important;line-height:1.5;color:#20232a;background:#fff}
pre,code{background:#f1f3f5;border-radius:4px}pre{padding:14px;overflow:auto}table{border-collapse:collapse;width:100%}th,td{border:1px solid #d8dee4;padding:8px;text-align:left}
h2{border-bottom:1px solid #ddd;margin-top:40px}h3{margin-top:30px}a{color:#0969da}
img{max-width:100%;max-height:420px;object-fit:contain;display:block}
#image-verification{position:fixed;top:0;left:0;right:0;z-index:999;background:#e9f7ed;color:#143a22;padding:10px 20px;border-bottom:2px solid #176b37;font-size:14px}
#image-verification details{max-height:300px;overflow:auto}#image-verification p{margin:2px 0}
</style>
<script>
window.addEventListener('load', async function(){
 const images=Array.from(document.querySelectorAll('img'));
 images.forEach(function(img){img.setAttribute('referrerpolicy','no-referrer');});
 await Promise.all(images.map(function(img){return img.decode().catch(function(){});}));
 const ok=images.filter(function(img){return img.complete&&img.naturalWidth>0&&img.naturalHeight>0;});
 const banner=document.createElement('div');banner.id='image-verification';
 const title=document.createElement('strong');
 title.textContent='Rendered README image check: '+ok.length+'/'+images.length+' decoded';
 banner.appendChild(title);
 const details=document.createElement('details');const summary=document.createElement('summary');
 summary.textContent='Image dimensions and status';details.appendChild(summary);
 images.forEach(function(img){
  const row=document.createElement('p');
  row.textContent=img.alt+': '+(img.complete&&img.naturalWidth>0?'loaded '+img.naturalWidth+' × '+img.naturalHeight:'FAILED');
  details.appendChild(row);
 });
 banner.appendChild(details);document.body.insertBefore(banner,document.body.firstChild);
 document.title='README — '+ok.length+'/'+images.length+' images decoded';
});
</script>""")
subprocess.run(['pandoc', str(ROOT / 'README.md'), '--from=gfm', '--to=html5',
                '--standalone', '--metadata=pagetitle:TF2 README preview',
                '--include-in-header=' + str(HEADER), '--output=' + str(PREVIEW / 'README.html')],
               check=True)
print(str(PREVIEW / 'README.html'))
