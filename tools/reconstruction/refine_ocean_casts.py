"""Audited pose envelopes: remove floor, wolf claws and watermarks from casts."""
from pathlib import Path
from research_paths import INPUT_DIR, WORK_ROOT, load_font
import json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=WORK_ROOT;OUT=ROOT/'playable/assets-v3'
import av
m=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
guide_background=np.array(Image.open(ROOT/'playable/assets-v2/arena.webp')).astype(float)
stand=[(68,14),(78,26),(89,15),(96,45),(91,60),(107,69),(111,91),(101,108),(106,127),(99,145),(102,164),(91,170),(83,143),(76,167),(64,171),(65,144),(58,139),(44,149),(38,139),(42,116),(49,102),(52,79),(64,61)]
npose=[(74,25),(83,37),(93,31),(99,58),(122,68),(124,85),(104,92),(106,102),(141,109),(141,127),(111,141),(93,139),(106,162),(99,173),(83,158),(71,141),(66,165),(56,174),(49,169),(57,143),(45,129),(41,105),(29,92),(36,79),(61,72),(65,51)]
lean=[(32,20),(43,39),(57,46),(58,67),(79,79),(99,104),(97,115),(66,98),(71,116),(82,130),(76,143),(50,142),(43,160),(29,164),(28,145),(14,146),(19,128),(22,101),(11,91),(12,75),(27,69)]
polys={}
for r in m['layers']:
 if not r['kind'].startswith('cast-'):continue
 k=r['kind'][-1];ix=r['at_ms']//40
 src=ROOT/'research/skills/ocean-wolf-228847.f4v' if r['source']=='wolf' else (INPUT_DIR/'official-footage-229512.f4v')
 box=r['source_box'][:];anc=[box[2]-r['anchor'][0] if r.get('flipped_to_face_right') else box[0]+r['anchor'][0],box[1]+r['anchor'][1]]
 if k=='u':box=[228,238,448,418];anc=[310,410]
 with av.open(str(src)) as c:
  s=c.streams.video[0];c.seek(int(r['source_ms']/1000/s.time_base),stream=s)
  for f in c.decode(s):
   if f.time>=r['source_ms']/1000-.001:full=np.array(f.to_image()).astype(float);a=full[box[1]:box[3],box[0]:box[2]];break
 h,w=a.shape[:2];rr,g,b=a.transpose(2,0,1)
 if k=='h':
  poly=stand if ix<4 else [(25,30),(39,42),(55,24),(64,34),(68,51),(83,56),(100,47),(109,52),(95,68),(82,77),(85,111),(92,128),(80,144),(80,165),(69,172),(58,151),(46,167),(37,163),(44,138),(34,126),(29,120),(29,100),(35,78),(28,66)]
  if ix>=8:poly=[(x+9,y-32) for x,y in stand]
 elif k=='u':
  poly=stand if ix<4 or ix>=16 else [(132,64),(144,69),(151,94),(173,78),(184,83),(178,102),(188,118),(183,139),(165,141),(163,153),(181,164),(181,174),(163,175),(148,160),(139,171),(112,176),(89,170),(82,165),(107,157),(123,146),(103,143),(85,133),(77,114),(69,90),(77,86),(90,98),(100,115),(118,123),(132,119),(126,94),(124,77)]
 elif k=='n':poly=npose
 elif k=='i':poly=lean if ix<3 else stand
 elif k=='o':poly=stand
 else:
  poly=stand if ix<3 or ix>=17 else [(35,5),(85,5),(102,22),(98,48),(113,60),(116,83),(131,101),(149,119),(145,131),(123,126),(110,121),(104,143),(95,151),(84,139),(78,124),(60,121),(49,113),(51,102),(66,98),(67,79),(56,67),(48,52),(31,36)]
 mask=Image.new('L',(w,h));ImageDraw.Draw(mask).polygon(poly,fill=255);inside=np.array(mask)>0
 blue=(g>rr*1.12)&(b>rr*1.2)&(g>60)&(b<g*1.8)
 gold=(rr>90)&(g>60)&(b<g*.9);red=(rr>80)&(rr>g*1.2)&(rr>b*1.05)
 pale=(np.min(a,axis=2)>110)&(np.max(a,axis=2)-np.min(a,axis=2)<90)
 if k=='n':
  yy,xx=np.mgrid[:h,:w];blue&=(rr<110);pale&=(yy>123)&(xx>46)&(xx<108)
 if k=='u' and 4<=ix<16:
  yy,xx=np.mgrid[:h,:w];red&=(yy>130);gold&=(yy>90)
 keep=(blue|gold|red|pale)&inside
 if k=='u':
  scores=[]
  for shift in range(380):
   error=np.abs(full[242:260,:960-shift:4]-guide_background[242:260,shift:960:4]).mean(2)
   scores.append(float(np.quantile(error,.6)))
  shift=int(np.argmin(scores));back=np.roll(guide_background,-shift,axis=1)[box[1]:box[3],box[0]:box[2]]
  keep&=np.max(abs(a-back),axis=2)>35
 # Small holes in outlines are closed inside the audited silhouette only.
 keep=(np.array(Image.fromarray(np.uint8(keep)*255).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3)))>0)&inside
 alpha=np.array(Image.fromarray(np.uint8(keep)*255).filter(ImageFilter.GaussianBlur(.3)))
 rgba=np.dstack([a,alpha]).astype('uint8');rgba[rgba[:,:,3]==0,:3]=0;im=Image.fromarray(rgba,'RGBA');ax=anc[0]-box[0]
 if r.get('flipped_to_face_right'):im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT);ax=w-ax
 im.save(OUT/(r['name']+'.webp'),lossless=True,exact=True)
 r.update(source_box=box,anchor=[ax,anc[1]-box[1]],dimensions=list(im.size),alpha='hand-audited pose envelope and palette matte; not original alpha')
 polys[r['name']]=poly
(OUT/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'research/skills/cast-envelopes.json').write_text(json.dumps(polys,indent=2),encoding='utf-8')
print('refined',len(polys),'cast frames')
