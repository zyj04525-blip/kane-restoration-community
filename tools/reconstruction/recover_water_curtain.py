"""Restore visible U-wave pixels discarded by the old crop and palette key.

Only verified unoccluded lower/outer regions are added. Enemy-covered upper
water remains unresolved. No mirror filling, generated art, or video audio.
"""
from pathlib import Path
from research_paths import INPUT_DIR, WORK_ROOT, load_font
import sys,json
import numpy as np
from PIL import Image,ImageFilter,ImageDraw,ImageFont
ROOT=WORK_ROOT;OUT=ROOT/'playable/assets-v6';BASE=ROOT/'playable/assets-v5';QA=ROOT/'research/cycle-recovery'
import av
m=json.loads((OUT/'manifest.json').read_text('utf-8'));rows=[r for r in m['layers'] if r['kind']=='skillfx-u'];frames={}
with av.open(str(INPUT_DIR/'official-footage-229512.f4v')) as c:
 s=c.streams.video[0];c.seek(int(161.36/s.time_base),stream=s)
 for f in c.decode(s):
  ms=round(f.time*1000)
  if ms>=161360:frames[ms]=f.to_ndarray(format='rgb24').astype(float)
  if ms>=162480:break
box=[285,210,955,445];x0,y0,x1,y1=box;yy,xx=np.mgrid[y0:y1,x0:x1];report=[]
for record in rows:
 old=Image.open(BASE/(record['name']+'.webp')).convert('RGBA');layer=Image.new('RGBA',(x1-x0,y1-y0))
 ox,oy,_,_=record['source_box'];layer.alpha_composite(old,(ox-x0,oy-y0));before=np.array(layer)
 rgb=frames[record['source_ms']][y0:y1,x0:x1];back=frames[161360][y0:y1,x0:x1];r,g,b=rgb.transpose(2,0,1)
 delta=np.max(abs(rgb-back),2)
 cold=((g>r*1.025)&(b>r*1.06)&(g>75))|((rgb.min(2)>155)&(rgb.max(2)-rgb.min(2)<48)&(b>=r))
 # Full-size frames show the guard/nameplate above this lower strip. On the
 # left and far right, the wave can also be recovered above that strip.
 # Audited lower sword edge in the full-size reference frames. Recover the
 # water underneath it instead of introducing a rectangular cutoff at y=330.
 keys=[161800,161920,162040,162160,162280,162400]
 left_edge=float(np.interp(record['source_ms'],keys,[269,269,269,245,232,198]))
 right_edge=float(np.interp(record['source_ms'],keys,[341,341,341,347,307,270]))
 below_sword=yy>left_edge+(xx-725)/230*(right_edge-left_edge)+4
 outer=(xx>=725)&below_sword
 gate=(xx>415)&(yy<435)&((yy>=368)|((xx<550)&(yy>=315))|outer)
 # The spell is absent during the first cast wind-up; do not retain weapon glow.
 if record['source_ms']<161800:gate[:]=False
 mask=cold&(delta>26)&gate
 # Keep particles near the known existing effect, or in its visible lower band.
 connected=np.array(Image.fromarray(before[:,:,3]).filter(ImageFilter.MaxFilter(15)))>0
 mask&=connected|((yy>=368)&(xx>=415))|outer
 # Detached weapon glints must not become wave particles. New outer pixels
 # need an actual connected path to the visible lower water in this frame.
 seen=np.zeros(mask.shape,bool);supported=np.zeros(mask.shape,bool)
 for sy,sx in zip(*np.where(mask)):
  if seen[sy,sx]:continue
  todo=[(sy,sx)];seen[sy,sx]=True;component=[];touches=False
  while todo:
   py,px=todo.pop();component.append((py,px));touches|=(py+y0>=368)
   for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
    ny,nx=py+dy,px+dx
    if 0<=ny<mask.shape[0] and 0<=nx<mask.shape[1] and mask[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;todo.append((ny,nx))
  if touches and len(component)>=45:
   cy,cx=zip(*component);supported[cy,cx]=True
 mask&=supported|~outer
 alpha=np.clip((delta-22)/75,0,1)*mask
 add=(alpha*255>before[:,:,3].astype(float)+2)&mask
 result=before.copy();result[add,:3]=rgb[add].astype('uint8');result[add,3]=np.rint(alpha[add]*255).astype('uint8')
 Image.fromarray(result).save(OUT/(record['name']+'.webp'),lossless=True,exact=True)
 report.append({'name':record['name'],'source_ms':record['source_ms'],'recovered_visible_pixels':int(add.sum()),'beyond_old_right_crop':int((add&(xx>=725)).sum()),'source_rgb_exact':bool(np.array_equal(result[add,:3],rgb[add].astype('uint8')))})
 record.update(source_box=box,anchor=[310-x0,410-y0],dimensions=[x1-x0,y1-y0],alpha='expanded original-frame lower/outer water matte; upper enemy occlusion remains')
m['water_curtain_revision']={'source_interval_ms':[161600,162480],'old_right_crop':725,'new_right_crop':955,
 'limits':['Adds visible source pixels only; guard-covered upper region remains incomplete.','Alpha remains estimated.','No change to provisional combat hitbox or damage values.']}
(OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),'utf-8')
(QA/'water-curtain-validation.json').write_text(json.dumps(report,indent=2),'utf-8')
board=Image.new('RGB',(1200,660),'#273443');d=ImageDraw.Draw(board);font=load_font(17)
for i,idx in enumerate([8,12,15]):
 for j,base in enumerate([BASE,OUT]):
  im=Image.open(base/f'skillfx-u-{idx}.webp').convert('RGBA')
  # Same world scale for before and after; pad to the new common crop.
  if j==0:
   pad=Image.new('RGBA',(670,235));pad.alpha_composite(im,(0,5));im=pad
  im=im.resize((603,212));board.paste(im,(j*600,i*220+8),im)
  d.text((j*600+12,i*220+195),('原裁切 ' if j==0 else '补回可见水浪 ')+f'{161.6+idx*.04:.2f}s',font=font,fill='white')
board.save(QA/'水幕天华缺口前后.jpg',quality=95)
print(json.dumps({'frames':len(report),'added_pixels':sum(r['recovered_visible_pixels'] for r in report),'outside_old_crop':sum(r['beyond_old_right_crop'] for r in report)}))
