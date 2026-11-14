"""Independent decode check; these checks do NOT prove original alpha/physics."""
from pathlib import Path
from research_paths import INPUT_DIR, WORK_ROOT, load_font
import sys,json
import numpy as np
from PIL import Image
ROOT=WORK_ROOT;A=ROOT/'playable/assets-v2'
import av
m=json.loads((A/'manifest.json').read_text(encoding='utf-8'))
records=[r for r in m['layers'] if r['kind']!='guard'];wanted={r['source_ms'] for r in records};frames={}
with av.open(str(INPUT_DIR/'official-footage-229512.f4v')) as c:
 s=c.streams.video[0];c.seek(int(min(wanted)/1000/s.time_base),stream=s)
 for f in c.decode(s):
  ms=round(f.time*1000)
  if ms in wanted:frames[ms]=f.to_ndarray(format='rgb24')
  if ms>max(wanted):break
assert set(frames)==wanted
results=[]
for r in records:
 rgba=np.array(Image.open(A/(r['name']+'.webp')).convert('RGBA'));x0,y0,x1,y1=r['source_box'];src=frames[r['source_ms']][y0:y1,x0:x1]
 assert rgba.shape[:2]==src.shape[:2]
 opaque=rgba[:,:,3]==255
 error=int(abs(rgba[:,:,:3].astype(int)-src.astype(int))[opaque].max()) if opaque.any() else 0
 assert error<=1,(r['name'],error)
 results.append({'name':r['name'],'source_ms':r['source_ms'],'opaque_max_rgb_error':error,'horizontal_edge_alpha_pixels':int(np.count_nonzero(rgba[:,[0,-1],3]))})
for kind,a in m['animations'].items():
 rows=[r for r in records if r['kind']==kind]
 assert [r['at_ms'] for r in rows]==list(range(0,a['duration_ms'],40))
 assert all(b['source_ms']-a['source_ms']==40 for a,b in zip(rows,rows[1:]))
walk=[r for r in results if r['name'].startswith('walk-')]
report={'source_frame_count':len(frames),'layer_count_checked':len(results),'opaque_source_rgb_max_error':max(r['opaque_max_rgb_error'] for r in results),'source_timestamps_and_40ms_holds':'pass','walk_horizontal_edge_pixels':{r['name']:r['horizontal_edge_alpha_pixels'] for r in walk},'results':results,'limits':['Source colors checked only where estimated alpha is fully opaque.','This is not a measure of whole-game or silhouette accuracy.','Alpha, effect clipping, input timing and damage require more independent evidence.']}
(ROOT/'research/alignment/逐帧核对结果.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='results'},ensure_ascii=False))
