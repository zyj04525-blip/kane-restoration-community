"""Remove detached matte debris, preserving the source silhouette and RGB."""
from pathlib import Path
from research_paths import INPUT_DIR, WORK_ROOT, load_font
import json
import numpy as np
from PIL import Image,ImageFilter
root=WORK_ROOT;assets=root/'playable/assets-v4'
m=json.loads((assets/'manifest.json').read_text(encoding='utf-8'));report=[]
for r in m['layers']:
 if not (r['kind'].startswith('attack') or r['kind'].startswith('cast-')):continue
 path=assets/(r['name']+'.webp');a=np.array(Image.open(path).convert('RGBA'));mask=a[:,:,3]>24
 if r['kind']=='cast-u':
  # Its detached crown tips cannot reliably be distinguished from debris in
  # this compressed clip. Preserve those original pixels rather than erase them.
  a=np.array(Image.open(root/'playable/assets-v3'/(r['name']+'.webp')).convert('RGBA'))
  a[a[:,:,3]<18]=0;Image.fromarray(a,'RGBA').save(path,lossless=True,exact=True)
  report.append({'name':r['name'],'detached_pixels_removed':0,'retained_body_pixels':int((a[:,:,3]>24).sum()),'note':'crown tips preserved; no component trim'})
  continue
 visited=np.zeros(mask.shape,bool);groups=[];h,w=mask.shape
 for y,x in zip(*np.where(mask)):
  if visited[y,x]:continue
  stack=[(y,x)];visited[y,x]=True;group=[]
  while stack:
   yy,xx=stack.pop();group.append((yy,xx))
   for dy,dx in [(0,1),(0,-1),(1,0),(-1,0),(-1,-1),(-1,1),(1,-1),(1,1)]:
    ny,nx=yy+dy,xx+dx
    if 0<=ny<h and 0<=nx<w and mask[ny,nx] and not visited[ny,nx]:visited[ny,nx]=True;stack.append((ny,nx))
  groups.append(group)
 if not groups:continue
 groups.sort(key=len,reverse=True);core=np.zeros(mask.shape,bool)
 yy,xx=zip(*groups[0]);core[yy,xx]=True
 near=np.array(Image.fromarray(core.astype('uint8')*255).filter(ImageFilter.MaxFilter(11)))>0
 keep=core.copy();removed=0
 for group in groups[1:]:
  yy,xx=zip(*group)
  # Keep separate boots, fingers and thin hair within five source pixels of
  # the body. Distant detached islands are screenshot debris, not movement.
  if len(group)>=12 and near[yy,xx].any():keep[yy,xx]=True
  else:removed+=len(group)
 envelope=np.array(Image.fromarray(keep.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0
 a[~envelope]=0
 Image.fromarray(a,'RGBA').save(path,lossless=True,exact=True)
 report.append({'name':r['name'],'detached_pixels_removed':removed,'retained_body_pixels':int(keep.sum())})
(root/'research/quality-pass/detached-body-trim.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'frames':len(report),'removed_detached_pixels':sum(r['detached_pixels_removed'] for r in report)}))
