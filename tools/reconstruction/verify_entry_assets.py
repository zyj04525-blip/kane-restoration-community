"""Verify the exported pixels against hashes and independently decoded source frames."""
from pathlib import Path
from research_paths import INPUT_DIR, WORK_ROOT, load_font
import json, hashlib, sys
from PIL import Image
ROOT=WORK_ROOT
ASSETS=ROOT/'entry/assets'
manifest=json.loads((ASSETS/'manifest.json').read_text(encoding='utf-8'))
checks=[]
for name,row in manifest['frames'].items():
    im=Image.open(ASSETS/(name+'.webp'));im.load()
    checks.append({'name':name,'pixel_hash_match':hashlib.sha256(im.tobytes()).hexdigest()==row['sha256'],
                   'size_match':list(im.size)==row['size']})
audit=INPUT_DIR
import av
wanted={round(t*1000):(key,i) for key,v in manifest['animations'].items() for i,t in enumerate(v['times'])}
atlases={key:[Image.open(ASSETS/s['file']) for s in v['sheets']] for key,v in manifest['animations'].items()}
animation=[]
with av.open(str(audit/'official-footage-229512.f4v')) as c:
    s=c.streams.video[0];c.seek(int(20/s.time_base),stream=s)
    for f in c.decode(s):
        ms=round(f.time*1000)
        if ms>41800:break
        if ms not in wanted:continue
        key,i=wanted[ms];col=i%10%5;row=i%10//5
        exported=atlases[key][i//10].crop((col*960,row*560,(col+1)*960,(row+1)*560)).convert('RGB')
        animation.append({'key':key,'ms':ms,'pixel_identical_to_decoded_source':exported.tobytes()==f.to_image().convert('RGB').tobytes()})
assert len(animation)==sum(len(v['times']) for v in manifest['animations'].values())
assert all(x['pixel_hash_match'] and x['size_match'] for x in checks)
assert all(x['pixel_identical_to_decoded_source'] for x in animation)
report={'scope':'Extraction fidelity only; not original-client or complete-game equivalence',
        'frames':checks,'animation_frames':animation,
        'browser_checks_observed_separately':['gender selection','spirit selection and carousel labels',
            'empty-name rejection','cancel retains selection','valid name to loading to comic',
            'three-page progression to tutorial','home and town dialogue navigation',
            'reload exposes saved local profile','standalone bundle loaded without console warnings or errors']}
(ROOT/'research/entry-flow/界面核对结果.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'images_verified':len(checks),'animation_frames_verified':len(animation),'pixel_mismatches':0}))
