"""Re-estimate edge alpha against the recorded clean background, not fan art.

This is a bounded reconstruction, not recovered original transparency. V4 is
kept intact. Opaque body interiors and all pose timestamps remain unchanged.
"""
from pathlib import Path
from research_paths import INPUT_DIR, WORK_ROOT, load_font
import json, shutil, sys
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont

ROOT=WORK_ROOT
BASE=ROOT/'playable/assets-v4'; OUT=ROOT/'playable/assets-v5'
QA=ROOT/'research/locomotion-edges'; OUT.mkdir(parents=True,exist_ok=True); QA.mkdir(parents=True,exist_ok=True)
import av
for p in BASE.glob('*.webp'): shutil.copyfile(p,OUT/p.name)
m=json.loads((BASE/'manifest.json').read_text('utf-8'))
rows=[r for r in m['layers'] if r['kind'] in ['idle','walk']]
wanted={r['source_ms'] for r in rows}; frames={}
with av.open(str(INPUT_DIR/'official-footage-229512.f4v')) as c:
 s=c.streams.video[0]; c.seek(int(min(wanted)/1000/s.time_base),stream=s)
 for f in c.decode(s):
  t=round(f.time*1000)
  if t in wanted: frames[t]=f.to_ndarray(format='rgb24')
  if t>max(wanted): break
assert set(frames)==wanted
bg=np.array(Image.open(BASE/'arena.webp').convert('RGB'),dtype=float)
report=[]
for r in rows:
 a=np.array(Image.open(BASE/(r['name']+'.webp')).convert('RGBA'))
 x0,y0,x1,y1=r['source_box']; rgb=frames[r['source_ms']][y0:y1,x0:x1].astype(float)
 back=bg[y0:y1,x0:x1]; mask=a[:,:,3]>0
 # Preserve all substantial body/aura components and nearby thin crown tips;
 # isolated distant compression flecks have no connection to either.
 seen=np.zeros(mask.shape,bool); components=[]
 for sy,sx in zip(*np.where(mask)):
  if seen[sy,sx]: continue
  todo=[(sy,sx)]; seen[sy,sx]=True; component=[]
  while todo:
   py,px=todo.pop(); component.append((py,px))
   for dy in [-1,0,1]:
    for dx in [-1,0,1]:
     ny,nx=py+dy,px+dx
     if 0<=ny<mask.shape[0] and 0<=nx<mask.shape[1] and mask[ny,nx] and not seen[ny,nx]:
      seen[ny,nx]=True; todo.append((ny,nx))
  components.append(component)
 core=np.zeros(mask.shape,bool)
 for comp in components:
  if len(comp)>=50:
   cy,cx=zip(*comp); core[cy,cx]=True
 near=np.array(Image.fromarray(core.astype('uint8')*255).filter(ImageFilter.MaxFilter(11)))>0
 detached=0
 for comp in components:
  cy,cx=zip(*comp)
  if not near[cy,cx].any(): mask[cy,cx]=False; detached+=len(comp)
 interior=np.array(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MinFilter(3)))>0
 diff=rgb-back
 lower=np.clip(np.max(np.where(diff>=0,diff/np.maximum(255-back,1),-diff/np.maximum(back,1)),axis=2),0,1)
 alpha=mask.astype(float)
 # Only a one-pixel contour is softened; never blur or resample body colours.
 edge=mask&~interior
 alpha[edge]=np.maximum(.35,lower[edge])
 # The floor aura was previously opaque and carried red/brown floor pixels.
 yy=np.arange(y0,y1)[:,None]
 aura=mask&(yy>=397)&(rgb[:,:,2]>rgb[:,:,0]*1.22)&(rgb[:,:,1]>rgb[:,:,0]*1.12)
 alpha[aura]=lower[aura]
 # The source has compression noise; discard only nearly unchanged edge pixels.
 removed=edge&(np.max(abs(diff),axis=2)<15)
 alpha[removed]=0
 front=np.clip(back+diff/np.maximum(alpha[:,:,None],1/255),0,255)
 result=np.dstack([np.rint(front),np.rint(alpha*255)]).astype('uint8')
 result[result[:,:,3]==0]=0
 Image.fromarray(result).save(OUT/(r['name']+'.webp'),lossless=True,exact=True)
 opaque=(result[:,:,3]==255)&interior
 assert np.array_equal(result[:,:,:3][opaque],rgb.astype('uint8')[opaque])
 reproject=result[:,:,:3]*(result[:,:,3:4]/255)+back*(1-result[:,:,3:4]/255)
 selected=(result[:,:,3]>0)
 error=abs(reproject-rgb)[selected]
 report.append({'name':r['name'],'source_ms':r['source_ms'],'edge_pixels':int(edge.sum()),
  'aura_pixels':int(aura.sum()),'removed_near_background_pixels':int(removed.sum()),'detached_flecks_removed':detached,
  'opaque_interior_rgb_unchanged':True,'reprojection_max_rgb_error':float(error.max()),
  'reprojection_mean_rgb_error':float(error.mean())})
 r['alpha']='one-pixel edge and floor-aura alpha estimate against recorded background; opaque interior unchanged'
m['version']=5
m['locomotion_edge_revision']={'frames':len(rows),'pose_timing':'unchanged from v4',
 'source':'same original 4399 guide video, no fan replacement',
 'limits':['Single-background alpha estimate, not original alpha.','Does not fill missing poses or establish the full walk cycle.']}
(OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),'utf-8')
(QA/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
font=load_font(16)
board=Image.new('RGB',(1000,660),'#253141'); d=ImageDraw.Draw(board)
for i,name in enumerate(['idle-0','walk-0','walk-6','walk-10']):
 x=i*250
 for j,folder in enumerate([BASE,OUT]):
  im=Image.open(folder/(name+'.webp')).convert('RGBA').resize((225,260))
  board.paste(im,(x+10,j*320+20),im)
  d.text((x+12,j*320+285),('调整前 ' if j==0 else '调整后 ')+name,font=font,fill='white')
board.save(QA/'走路边缘前后核对.jpg',quality=95)
print(json.dumps({'frames':len(rows),'max_reprojection_error':max(r['reprojection_max_rgb_error'] for r in report),'unchanged_opaque_interiors':True}))
