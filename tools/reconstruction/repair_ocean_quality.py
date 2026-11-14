"""Restore clipped ice height and dark water from verified original video pixels.

N combines two casts at the same 25 fps phase. No generated/inpainted pixels.
V3 is retained as a comparison baseline; V4 records all replacement provenance.
"""
from pathlib import Path
from research_paths import INPUT_DIR, WORK_ROOT, load_font
import sys,json,shutil
import numpy as np
from PIL import Image,ImageFilter,ImageDraw
ROOT=WORK_ROOT
import av
OUT=ROOT/'playable/assets-v4';OUT.mkdir(parents=True,exist_ok=True)
BASE=ROOT/'playable/assets-v3';QA=ROOT/'research/quality-pass'
for f in BASE.glob('*.webp'):shutil.copyfile(f,OUT/f.name)
m=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'));m['version']=4
frames={}
def load(start,end):
 with av.open(str(ROOT/'research/skills/ocean-wolf-228847.f4v')) as c:
  s=c.streams.video[0];c.seek(int(start/s.time_base),stream=s)
  for f in c.decode(s):
   if f.time<start-.001:continue
   if f.time>end+.001:break
   frames[round(f.time*25)]=np.asarray(f.to_image()).astype(np.float32)
def at(t):return frames[round(t*25)]
def save(im,rec):
 im.save(OUT/(rec['name']+'.webp'),lossless=True,exact=True)
 rec['dimensions']=list(im.size)
def cold(a):
 r,g,b=a.transpose(2,0,1)
 return ((b>r*1.19)&(g>r*1.06)&(b>65))|((a.min(2)>175)&(a.max(2)-a.min(2)<48))
def matte(a,b,gate):
 d=np.max(abs(a-b),2)
 keep=cold(a)&(d>26)&gate
 # Preserve deep-blue interiors; feather only the boundary, not the whole image.
 inside=np.array(Image.fromarray(np.uint8(keep)*255).filter(ImageFilter.MinFilter(3)))>0
 alpha=np.where(inside,1,np.clip((d-22)/65,0,1))*keep
 rgba=np.dstack([a,alpha*255]).astype('uint8');rgba[~keep,:3]=0
 return rgba
load(62.64,65.80);load(135.76,138.88);load(150.96,155.72)
nrecords=[r for r in m['layers'] if r['kind']=='skillfx-n']
preview=[]
for j,r in enumerate(nrecords):
 a=at(62.88+j*.04);b=at(136+j*.04)
 yy,xx=np.mgrid[:560,:960]
 # First cast: core largely clear, but subtitle across its upper half.
 pa=matte(a,at(62.64),(xx<550)&(xx>35)&(yy<475)&(yy>145))
 # Second cast: opposite direction, clear upper spire, lower half obscured by boss.
 pb=matte(b,at(135.76),(xx>640)&(xx<950)&(yy>30)&(yy<275))
 # Text/armour warm pixels have cold compression fringes. Remove only their
 # immediate neighbours rather than deleting complete horizontal bands.
 for arr,source in [(pa,a),(pb,b)]:
  rr,gg,bb=source.transpose(2,0,1)
  warm=(rr>85)&(rr>bb*1.12)&(rr>gg*.94)
  fringe=np.array(Image.fromarray(np.uint8(warm)*255).filter(ImageFilter.MaxFilter(7)))>0
  arr[fringe,3]=0
 # Common actor-relative coordinates. Body anchors are measured from the
 # persistent nameplate/feet, not enemy or camera positions.
 layer=Image.new('RGBA',(650,520));donor=Image.new('RGBA',(650,520))
 im=Image.fromarray(pa,'RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 layer.alpha_composite(im,(80-(960-551),440-380))
 donor.alpha_composite(Image.fromarray(pb,'RGBA'),(80-610-5,440-450))
 # Upper source is used only where its own alpha is supported by source pixels.
 layer.alpha_composite(donor)
 r.update(source_ms=round((62.88+j*.04)*1000),source_box=[0,0,960,560],anchor=[80,440],
   flipped_to_face_right=True,alpha='two original casts, full-height background-difference matte; occlusions remain',
   contributors=[{'source_ms':round((62.88+j*.04)*1000),'anchor':[551,380],'face':-1},
                 {'source_ms':round((136+j*.04)*1000),'anchor':[610,450],'face':1,'x_alignment':-5,'region':'upper spire'}])
 save(layer,r)
 if j in [8,20,28,34,42,55]:preview.append((layer.copy(),j))
# L: retain all blue hues rather than cutting blue when B/G exceeds 1.65.
# Estimate the actual dark backdrop from the far side of each source row.
for r in [r for r in m['layers'] if r['kind']=='skillfx-l']:
 a=at(r['source_ms']/1000);x0,y0,x1,y1=r['source_box'];part=a[y0:y1,x0:x1]
 back=np.percentile(a[y0:y1,885:945],50,axis=1)[:,None,:]
 yy,xx=np.mgrid[y0:y1,x0:x1];ax=x1-r['anchor'][0];ay=y0+r['anchor'][1]
 gate=(yy<477)&~((xx>778)&(yy>373))&~((xx<225)&(yy<160))
 # Use the recovered cast silhouette, not an oversized ellipse that punched
 # a conspicuous oval hole through the water behind the player.
 body_rec=next(q for q in m['layers'] if q['name']=='cast-l-'+str(min(26,r['at_ms']//40)))
 body=Image.open(BASE/(body_rec['name']+'.webp')).convert('RGBA').getchannel('A')
 body=body.transpose(Image.Transpose.FLIP_LEFT_RIGHT).filter(ImageFilter.MaxFilter(3))
 body_mask=Image.new('L',(960,560));body_mask.paste(body,(round(ax-(body.width-body_rec['anchor'][0])),round(ay-body_rec['anchor'][1])))
 gate&=np.array(body_mask)[y0:y1,x0:x1]<32
 arr=matte(part,back,gate)
 # Remove surviving thin, detached scan-line streaks without touching pillar
 # interiors: a pixel needs a vertically connected feature within 5 rows.
 solid=arr[:,:,3]>45
 support=sum(np.roll(solid,k,axis=0) for k in [-3,-2,-1,1,2,3])
 arr[(support<2)&solid,3]=0
 im=Image.fromarray(arr,'RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 r['alpha']='full blue spectrum and row-background difference; original pillar shadows retained'
 save(im,r)
# Character edge repair: constrain changes to a one-pixel silhouette boundary.
# Internal palette colours and frame timing remain untouched.
edge_report=[]
for r in m['layers']:
 if not (r['kind'].startswith('cast-') or r['kind'].startswith('attack')):continue
 im=Image.open(OUT/(r['name']+'.webp')).convert('RGBA');a=np.array(im);mask=a[:,:,3]>48
 # Fill one-pixel alpha cracks only when all four direct neighbours are opaque.
 four=np.roll(mask,1,0)&np.roll(mask,-1,0)&np.roll(mask,1,1)&np.roll(mask,-1,1)
 holes=four&~mask;holes[[0,-1],:]=False;holes[:,[0,-1]]=False
 # Recover the actual source RGB for these previously omitted pixels.
 t=r.get('source_ms',0)/1000
 src=ROOT/'research/skills/ocean-wolf-228847.f4v' if r.get('source')=='wolf' else (INPUT_DIR/'official-footage-229512.f4v')
 if holes.any():
  with av.open(str(src)) as c:
   s=c.streams.video[0];c.seek(int(t/s.time_base),stream=s)
   for f in c.decode(s):
    if f.time>=t-.001:full=np.asarray(f.to_image());break
  x0,y0,x1,y1=r['source_box'];original=full[y0:y1,x0:x1]
  if r.get('flipped_to_face_right'):original=original[:,::-1]
  if original.shape[:2]==a.shape[:2]:a[holes,:3]=original[holes];a[holes,3]=255
 # Eliminate nearly transparent background fringes while retaining antialiasing.
 fringe=(a[:,:,3]>0)&(a[:,:,3]<18);a[fringe]=0
 save(Image.fromarray(a,'RGBA'),r)
 edge_report.append({'name':r['name'],'source_pixel_cracks_recovered':int(holes.sum()),'faint_fringe_pixels_removed':int(fringe.sum())})
m['quality_revision']={'n':'upper spire recovered from opposite-facing repeat at 136.00s; no synthetic fill',
 'l':'removed erroneous B/G upper bound that deleted blue pillar shadows',
 'body':'source-pixel restoration of isolated one-pixel cracks; low-alpha fringe trim',
 'limits':['Not original alpha. Boss occlusions remain.','N donor is aligned by measured anchors with a 5px horizontal adjustment.','L background streak separation remains imperfect.']}
(OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
(QA/'body-edge-repair.json').write_text(json.dumps(edge_report,indent=2),encoding='utf-8')
board=Image.new('RGB',(1200,720),'#343843')
for k,(im,j) in enumerate(preview):
 im.thumbnail((390,330));tile=Image.new('RGBA',(400,360),'#343843');tile.alpha_composite(im,((400-im.width)//2,0));ImageDraw.Draw(tile).text((10,340),f'N phase {j*.04:.2f}s',fill='white');board.paste(tile.convert('RGB'),(k%3*400,k//3*360))
board.save(QA/'n-v4-review.jpg')
print(json.dumps({'layers':len(m['layers']),'body_frames_repaired':len(edge_report),'cracks':sum(r['source_pixel_cracks_recovered'] for r in edge_report)}))
