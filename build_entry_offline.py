"""Bundle the interface and its referenced images into an offline HTML file."""
from pathlib import Path
import base64, hashlib, json, re
root=Path(__file__).resolve().parent
entry=root/'entry';assets=entry/'assets'
manifest=json.loads((assets/'manifest.json').read_text(encoding='utf-8'))
files={name+'.webp' for name in manifest['frames']}
for sequence in manifest['animations'].values():
    files.update(s['file'] for s in sequence['sheets'])
images={name:'data:image/webp;base64,'+base64.b64encode((assets/name).read_bytes()).decode('ascii') for name in sorted(files)}
combat_root=root/'playable/assets-v6'
combat_manifest=json.loads((combat_root/'manifest.json').read_text(encoding='utf-8'))
for name in ['arena']+[r['name'] for r in combat_manifest['layers']]:
    images['combat/'+name+'.webp']='data:image/webp;base64,'+base64.b64encode((combat_root/(name+'.webp')).read_bytes()).decode('ascii')
audio={} # Rejected recording/BGM samples are not shipped.
payload=json.dumps({'manifest':manifest,'combatManifest':combat_manifest,'images':images,'audio':audio},ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
js='\n'.join((root/p).read_text(encoding='utf-8') for p in ['playable/engine.js','playable/arena.js','entry/app.js'])
style=(entry/'style.css').read_text(encoding='utf-8')
for name in ['name-panel.webp','loading-panel.webp']:
    style=style.replace('assets/'+name,images[name])
for name in ['topbg_e3.jpg','lt.gif','rt.gif','lb.gif','rb.gif','ht.gif','hb.gif','sl.gif','sr.gif']:
    mime='image/jpeg' if name.endswith('.jpg') else 'image/gif'
    style=style.replace('assets/'+name,'data:'+mime+';base64,'+base64.b64encode((assets/name).read_bytes()).decode('ascii'))
html=(entry/'index.html').read_text(encoding='utf-8')
sha=base64.b64encode(hashlib.sha256(js.encode()).digest()).decode()
html=re.sub(r'<meta http-equiv="Content-Security-Policy"[^>]+>',
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; script-src \'sha256-'+sha+'\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">',html)
html=html.replace('<link rel="stylesheet" href="style.css">','<style>'+style+'</style>')
html=html.replace('<script src="../playable/engine.js"></script>','').replace('<script src="../playable/arena.js"></script>','')
html=html.replace('<script src="../playable/audio.js"></script>','')
html=html.replace('<script src="app.js"></script>','<script id="entry-data" type="application/json">'+payload+'</script><script>'+js+'</script>')
html=html.replace('href="assets/manifest.json" target="_blank"','href="data:application/json;base64,'+base64.b64encode(json.dumps(manifest,ensure_ascii=False,indent=2).encode()).decode()+'" download="画面来源记录.json"')
target=root/'凯恩战记-创建角色与入场界面.html';target.write_text(html,encoding='utf-8')
(root/'凯恩战记-可玩复原版.html').write_text(html,encoding='utf-8')
print(json.dumps({'file':str(target),'bytes':target.stat().st_size,'embedded_images':len(images)},ensure_ascii=False))
