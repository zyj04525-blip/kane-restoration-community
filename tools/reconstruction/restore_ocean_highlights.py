"""Retain neutral clipped-white source highlights lost by the cyan-only key."""
from pathlib import Path
from research_paths import INPUT_DIR, WORK_ROOT, load_font
import json,sys
import numpy as np
from PIL import Image,ImageFilter
ROOT=WORK_ROOT;OUT=ROOT/'playable/assets-v3'
import av
m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'));report=[]
for k in 'huniol':
 rs=[r for r in m['layers'] if r['kind']=='skillfx-'+k]
 src=ROOT/'research/skills/ocean-wolf-228847.f4v' if rs[0]['source']=='wolf' else (INPUT_DIR/'official-footage-229512.f4v')
 with av.open(str(src)) as c:
  s=c.streams.video[0];c.seek(int(rs[0]['source_ms']/1000/s.time_base),stream=s);idx=0;changed=0
  for f in c.decode(s):
   if idx>=len(rs):break
   r=rs[idx]
   if f.time<r['source_ms']/1000-.001:continue
   im=Image.open(OUT/(r['name']+'.webp')).convert('RGBA')
   if r.get('flipped_to_face_right'):im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
   a=np.array(im);rgb=np.array(f.to_image().crop(r['source_box']))
   near=np.array(Image.fromarray(a[:,:,3]).filter(ImageFilter.BoxBlur(32)))>1
   white=(rgb.min(2)>210)&((rgb.max(2).astype(int)-rgb.min(2))<13)
   x0,y0,x1,y1=r['source_box'];yy,xx=np.mgrid[y0:y1,x0:x1]
   ui=((xx>778)&(yy>373))|((xx<220)&(yy<145))
   white&=~ui
   add=near&white&(a[:,:,3]<235);changed+=int(add.sum());a[add,:3]=rgb[add];a[add,3]=255
   a[ui]=0
   im=Image.fromarray(a,'RGBA')
   if r.get('flipped_to_face_right'):im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
   im.save(OUT/(r['name']+'.webp'),lossless=True,exact=True);idx+=1
 report.append({'skill':k,'restored_source_white_pixels':changed})
(ROOT/'research/skills/highlight-recovery.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
