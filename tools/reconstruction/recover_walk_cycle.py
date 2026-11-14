"""Recover all five observed running poses from the original guide at 98.40s.

The recording samples one 520ms cycle at 25 fps. Its lower floor ring is covered
by an editor caption, so that decorative ring uses a separately recorded clean
frame; that limitation is retained in the manifest, not hidden as original art.
"""
from pathlib import Path
from research_paths import INPUT_DIR, WORK_ROOT, load_font
import sys,json,shutil
import numpy as np
from PIL import Image,ImageFilter,ImageDraw,ImageFont
ROOT=WORK_ROOT;BASE=ROOT/'playable/assets-v5';OUT=ROOT/'playable/assets-v6'
QA=ROOT/'research/cycle-recovery';OUT.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
import av
for p in BASE.glob('*.webp'):shutil.copyfile(p,OUT/p.name)
m=json.loads((BASE/'manifest.json').read_text('utf-8'));m['version']=6
m['layers']=[r for r in m['layers'] if r['kind']!='walk']
frames={}
with av.open(str(INPUT_DIR/'official-footage-229512.f4v')) as c:
 s=c.streams.video[0];c.seek(int(98.4/s.time_base),stream=s)
 for f in c.decode(s):
  ms=round(f.time*1000)
  if ms>=98400:frames[ms]=f.to_ndarray(format='rgb24').astype(float)
  if ms>=98960:break
bg=np.array(Image.open(BASE/'arena.webp').convert('RGB')).astype(float)
old=json.loads((BASE/'manifest.json').read_text('utf-8'))
ringrec=next(r for r in old['layers'] if r['name']=='walk-0')
ring=np.array(Image.open(BASE/'walk-0.webp').convert('RGBA'))
rr,gg,bb=ring[:,:,:3].astype(float).transpose(2,0,1)
yy=np.arange(ring.shape[0])[:,None]+245
ring[~((yy>=391)&(bb>rr*1.25)&(gg>rr*1.12))]=0
poses=[(98400,98520),(98520,98600),(98600,98720),(98720,98800),(98800,98920)]
report=[]
for index,ms in enumerate(range(98400,98920,40)):
 pose=next(i for i,(lo,hi) in enumerate(poses) if lo<=ms<hi)
 # Fixed stage, successive observed 36px world steps; don't recenter each pose.
 anchor_x=168+36*pose;box=[anchor_x-100,245,anchor_x+70,418]
 x0,y0,x1,y1=box;rgb=frames[ms][y0:y1,x0:x1];back=bg[y0:y1,x0:x1]
 delta=np.max(abs(rgb-back),2);near=np.min([np.max(abs(rgb-bg[y0+dy:y1+dy,x0+dx:x1+dx]),2) for dy in [-1,0,1] for dx in [-1,0,1]],axis=0)
 mask=near>22
 mask=np.array(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3)))>0
 yy,xx=np.mgrid[y0:y1,x0:x1];r,g,b=rgb.transpose(2,0,1)
 # Below the boots is editor text and an occluded ring, never character art.
 mask&=yy<403
 mask&=~((yy>=390)&((xx<anchor_x-8)|(xx>anchor_x+37)))
 # Body is connected; preserve tiny detached tips only near that silhouette.
 seen=np.zeros(mask.shape,bool);comps=[]
 for sy,sx in zip(*np.where(mask)):
  if seen[sy,sx]:continue
  todo=[(sy,sx)];seen[sy,sx]=True;comp=[]
  while todo:
   py,px=todo.pop();comp.append((py,px))
   for dy in [-1,0,1]:
    for dx in [-1,0,1]:
     ny,nx=py+dy,px+dx
     if 0<=ny<mask.shape[0] and 0<=nx<mask.shape[1] and mask[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;todo.append((ny,nx))
  comps.append(comp)
 core=np.zeros(mask.shape,bool);cy,cx=zip(*max(comps,key=len));core[cy,cx]=True
 around=np.array(Image.fromarray(core.astype('uint8')*255).filter(ImageFilter.MaxFilter(7)))>0
 keep=core.copy()
 for comp in comps:
  cy,cx=zip(*comp)
  if around[cy,cx].any():keep[cy,cx]=True
 interior=np.array(Image.fromarray(keep.astype('uint8')*255).filter(ImageFilter.MinFilter(3)))>0
 diff=rgb-back;minimum=np.clip(np.max(np.where(diff>=0,diff/np.maximum(255-back,1),-diff/np.maximum(back,1)),2),0,1)
 alpha=keep.astype(float);alpha[keep&~interior]=np.maximum(.35,minimum[keep&~interior])
 fg=np.clip(back+diff/np.maximum(alpha[:,:,None],1/255),0,255)
 rgba=np.dstack([np.rint(fg),np.rint(alpha*255)]).astype('uint8');rgba[rgba[:,:,3]==0]=0
 body=Image.fromarray(rgba);layer=Image.new('RGBA',body.size)
 layer.alpha_composite(Image.fromarray(ring),(100-ringrec['anchor'][0],158-ringrec['anchor'][1]))
 layer.alpha_composite(body)
 name=f'walk-{index}';layer.save(OUT/(name+'.webp'),lossless=True,exact=True)
 m['layers'].append({'name':name,'kind':'walk','source':'guide','source_ms':ms,'at_ms':ms-98400,
  'source_box':box,'anchor':[100,158],'dimensions':list(layer.size),'pose':pose,
  'alpha':'recorded-background difference with edge estimate',
  'contributors':[{'source_ms':ms,'part':'body'},{'source_ms':77120,'part':'floor ring, clean prior observation; exact ring phase unverified'}]})
 report.append({'name':name,'ms':ms,'pose':pose,'anchor_x':anchor_x,'body_pixels':int(keep.sum())})
m['animations']['walk']={'duration_ms':520,'loop':True}
m['walk_cycle_revision']={'source_interval_ms':[98400,98920],'observed_pose_count':5,'pose_holds_ms':[120,80,120,80,120],
 'comparison_return_ms':98920,'limits':['25fps recording samples, not original client frame times.','Decorative floor ring comes from 77.12s because caption covers this segment.','Anchors measured/estimated from stage displacement; original pivot unavailable.']}
(OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),'utf-8')
(QA/'walk-cycle-frames.json').write_text(json.dumps(report,indent=2),'utf-8')
font=load_font(16)
board=Image.new('RGB',(1000,430),'#263442');d=ImageDraw.Draw(board)
for i,(ms,end) in enumerate(poses):
 rec=next(r for r in m['layers'] if r['kind']=='walk' and r['source_ms']==ms)
 im=Image.open(OUT/(rec['name']+'.webp')).convert('RGBA');board.paste(im,(i*200+15,30),im)
 d.text((i*200+15,220),f'姿势 {i+1} · {end-ms} ms',font=font,fill='white')
 d.text((i*200+15,250),f'录像 {ms/1000:.2f}s',font=font,fill='#9bcede')
board.save(QA/'完整走路五姿势核对.jpg',quality=95)
print(json.dumps({'frames':len(report),'poses':5,'duration_ms':520}))
