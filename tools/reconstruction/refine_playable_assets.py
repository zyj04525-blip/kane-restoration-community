"""Second-pass, source-timed sprites. Video-derived estimates, not client assets."""
from pathlib import Path
from research_paths import INPUT_DIR, WORK_ROOT, load_font
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=WORK_ROOT
AUDIT=INPUT_DIR
import av
SOURCE=AUDIT/'official-footage-229512.f4v'
OUT=ROOT/'playable/assets-v2';OUT.mkdir(parents=True,exist_ok=True)
QA=ROOT/'research/alignment';QA.mkdir(parents=True,exist_ok=True)
cache={}
def frame(t):
    n=round(t*25)
    if n not in cache:
        with av.open(str(SOURCE)) as c:
            s=c.streams.video[0];c.seek(int(n/25/s.time_base),stream=s)
            for f in c.decode(s):
                if f.time>=n/25-.00001:cache[n]=f.to_ndarray(format='rgb24');break
    return cache[n]

bg=frame(76).copy();bg[240:448,:230]=frame(78)[240:448,:230]
Image.fromarray(bg).save(OUT/'arena.webp',lossless=True)
records=[];shifts={}
# Hand-traced silhouettes for the nine distinct observed poses. Coordinates in
# the 550,180 actor crop; these are reconstruction masks, not source geometry.
POSES=[
[(51,27),(66,27),(73,47),(71,57),(91,43),(110,38),(97,63),(101,74),(91,88),(82,85),(81,98),(74,108),(68,127),(59,141),(52,138),(57,119),(44,124),(30,125),(17,115),(19,96),(28,85),(28,71),(38,62),(44,40)],
[(49,30),(74,24),(83,29),(81,44),(94,43),(121,20),(127,20),(127,50),(106,64),(91,74),(87,108),(78,118),(70,144),(61,154),(54,149),(59,129),(49,137),(37,139),(24,136),(28,112),(35,96),(19,100),(6,93),(6,83),(27,81),(40,71),(45,50)],
[(47,31),(73,25),(82,35),(84,50),(92,67),(99,80),(96,103),(91,110),(79,117),(75,139),(65,141),(62,120),(47,126),(32,127),(20,115),(21,93),(16,73),(28,63),(43,54)],
[(63,26),(83,28),(89,40),(85,58),(114,60),(119,74),(94,80),(89,92),(81,108),(71,128),(60,139),(53,135),(56,121),(40,119),(35,111),(17,111),(6,102),(13,88),(30,78),(48,71),(59,50)],
[(63,25),(79,8),(83,22),(94,24),(94,43),(89,63),(93,88),(90,102),(80,118),(70,137),(60,151),(53,144),(60,121),(48,113),(26,113),(23,98),(39,86),(53,73),(59,46)],
[(89,20),(98,3),(104,20),(110,35),(104,52),(116,63),(112,79),(104,88),(101,107),(91,123),(76,136),(70,127),(70,117),(60,114),(57,102),(38,108),(21,109),(17,99),(31,86),(40,69),(61,62),(78,50)],
[(83,6),(98,10),(104,23),(110,40),(119,42),(126,53),(118,67),(109,81),(96,90),(84,109),(69,129),(55,130),(48,116),(38,115),(27,110),(18,102),(9,99),(5,85),(15,72),(30,60),(52,50),(75,45)],
[(77,14),(86,1),(92,15),(97,13),(108,31),(105,47),(113,65),(109,80),(96,93),(94,113),(82,132),(69,140),(54,143),(48,138),(64,120),(60,117),(50,109),(35,99),(17,98),(12,84),(28,74),(33,50),(44,41),(54,30)]
]
def shift(t):
    n=round(t*25)
    if n not in shifts:
        a=frame(t).astype(float);b=bg.astype(float);scores=[]
        for dx in range(380):
            e=np.abs(a[242:260,:960-dx:3]-b[242:260,dx:960:3]).mean(axis=2)
            scores.append((float(np.quantile(e,.6)),dx))
        shifts[n]=min(scores)[1]
    return shifts[n]

def clean(mask,minarea=20,fill=False):
    seen=np.zeros(mask.shape,bool);keep=np.zeros(mask.shape,bool)
    for yy,xx in zip(*np.where(mask)):
        if seen[yy,xx]:continue
        todo=[(yy,xx)];seen[yy,xx]=True;component=[]
        while todo:
            y,x=todo.pop();component.append((y,x))
            for ny,nx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                if 0<=ny<mask.shape[0] and 0<=nx<mask.shape[1] and mask[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;todo.append((ny,nx))
        if len(component)>=minarea:
            for y,x in component:keep[y,x]=True
    if fill:
        # Fill only enclosed compression holes, never the exterior between limbs.
        holes=~keep;outside=np.zeros(mask.shape,bool);todo=[]
        for y,x in [(0,x) for x in range(mask.shape[1])]+[(mask.shape[0]-1,x) for x in range(mask.shape[1])]+[(y,0) for y in range(mask.shape[0])]+[(y,mask.shape[1]-1) for y in range(mask.shape[0])]:
            if holes[y,x] and not outside[y,x]:outside[y,x]=True;todo.append((y,x))
        while todo:
            y,x=todo.pop()
            for ny,nx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                if 0<=ny<mask.shape[0] and 0<=nx<mask.shape[1] and holes[ny,nx] and not outside[ny,nx]:outside[ny,nx]=True;todo.append((ny,nx))
        keep|=holes&~outside
    return keep

def layer(t,box,anchor,kind,at,fx=False,dx=None):
    x0,y0,x1,y1=box;rgb=frame(t)[y0:y1,x0:x1].astype(float)
    dx=shift(t) if dx is None else dx;full=np.roll(bg,-dx,axis=1).astype(float)
    back=full[y0:y1,x0:x1];delta=np.max(abs(rgb-back),axis=2)
    # Background resampling is not foreground; tolerate one pixel registration noise.
    near=np.min([np.max(abs(rgb-full[y0+oy:y1+oy,x0+ox:x1+ox]),axis=2) for oy in (-1,0,1) for ox in (-1,0,1)],axis=0)
    mask=near>(17 if fx else 23)
    if kind.startswith('attack'):
        # Tutorial label is outside the actor except for the unverified crown edge.
        mask[:max(0,205-y0),:max(0,610-x0)]=False
    mask=np.array(Image.fromarray(np.uint8(mask)*255).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3)))>0
    keep=clean(mask,35 if fx else 50,fill=False)
    if fx or kind.startswith('attack'):
        # Minimum feasible alpha from C = alpha F + (1-alpha)B. This is an
        # explicit single-background estimate; it cannot recover original alpha.
        diff=rgb-back
        lower=np.where(diff>=0,diff/np.maximum(255-back,1),-diff/np.maximum(back,1))
        alpha=np.clip(np.max(lower,axis=2),0,1)*keep
        alpha[delta<22]=0
        if kind.startswith('attack'):
            pi=(0 if at<.12 else 1 if at<.32 else 2) if kind=='attack0' else (3 if at<.12 else 4) if kind=='attack1' else (5 if at<.12 else 6 if at<.32 else 7)
            poly=Image.new('L',(x1-x0,y1-y0));ImageDraw.Draw(poly).polygon(POSES[pi],fill=255)
            interior=np.array(poly)>0
            # Fill compression holes only within the hand traced body. Keep the
            # aura/ring translucent, and do not fill its enclosed floor region.
            alpha[interior & keep]=1
            cyan=(rgb[:,:,2]>rgb[:,:,0]+35)&(rgb[:,:,1]>rgb[:,:,0]+25)
            alpha[~interior & ~cyan]=0
            alpha[:24,:60]=0
            alpha[168:]=0
        if fx:
            # The name label occupies the bottom-left corner of this effect crop.
            alpha[max(0,343-y0):max(0,371-y0),:max(0,710-x0)]=0
        front=np.clip(back+diff/np.maximum(alpha[:,:,None],1/255),0,255)
    else:
        alpha=keep.astype(float);front=rgb
        if kind=='walk':
            # Remove disconnected backdrop fragments above/next to the crown.
            alpha[:15]=0
            alpha[:65,-15:]=0
    rgba=np.dstack((front,np.round(alpha*255))).astype('uint8');rgba[rgba[:,:,3]==0,:3]=0
    name=kind+'-'+str(sum(r['kind']==kind for r in records));im=Image.fromarray(rgba,'RGBA');im.save(OUT/(name+'.webp'),lossless=True,exact=True)
    records.append({'name':name,'kind':kind,'source_ms':round(t*1000),'at_ms':round(at*1000),'source_box':box,'anchor':[anchor[0]-x0,anchor[1]-y0],'camera_shift':dx,'dimensions':list(im.size),'alpha':'minimum-feasible-single-background-estimate' if fx else 'estimated-silhouette-with-compression-hole-fill'})
    return im

for i in range(18):layer(73+i*.04,[76,245,205,418],[140,403],'idle',i*.04,dx=0)
walk=[]
# Only the uninterrupted leaning motion, no standing frames or clipped crop.
for i in range(11):
    t=77.12+i*.04;a=frame(t)[398:420,180:580].astype(float)
    blue=(a[:,:,2]>140)&(a[:,:,1]>110)&(a[:,:,2]>a[:,:,0]*1.3)&(a[:,:,1]>a[:,:,0]*1.2)
    xx=np.where(blue)[1]+180;cx=round((int(xx.min())+int(xx.max()))/2)
    # The last clean interval ends before the actor overlaps the tutorial bubble.
    layer(t,[cx-85,245,cx+65,418],[cx+4,403],'walk',i*.04,dx=0);walk.append([round(t,2),cx+4])

# Observe three successive distinct gestures. Keep source sample holds at 40ms.
clips=[('attack0',103.40,10),('attack1',103.80,10),('attack2',104.20,13)]
for kind,start,count in clips:
    for i in range(count):
        t=start+i*.04
        # Player is held at the camera follow point during this uninterrupted chain.
        layer(t,[550,180,678,352],[610,337],kind,i*.04)

# Each strike has its own water appearance; the third burst outlives the gesture.
for kind,start,count in [('water0',103.40,10),('water1',103.80,10),('water2',104.20,23)]:
    for i in range(count):layer(start+i*.04,[678,184,850,405],[610,337],kind,i*.04,fx=True)

# Retain the existing guard pose unchanged until a verified sequence is available.
old=json.loads((ROOT/'playable/assets/manifest.json').read_text(encoding='utf-8'))
for r in old['layers']:
    if r['kind']=='guard':
        (OUT/(r['name']+'.webp')).write_bytes((ROOT/'playable/assets'/(r['name']+'.webp')).read_bytes());records.append(r)
manifest={'version':2,'source':'https://video.5054399.com/v/v2/video_229512.xml','source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'layers':records,'walk_anchor_observations':walk,
 'animations':{'idle':{'duration_ms':720,'loop':True},'walk':{'duration_ms':440,'loop':True},'attack0':{'duration_ms':400},'attack1':{'duration_ms':400},'attack2':{'duration_ms':520},'water0':{'duration_ms':400},'water1':{'duration_ms':400},'water2':{'duration_ms':920}},
 'limits':['Recording-derived, not original client assets.','The 25fps recording cannot establish unseen intermediate poses.','Crown edge near tutorial text, effect alpha and cropped effect tails remain uncertain.','Movement speed, input windows and damage geometry remain reconstruction estimates.','Water colors and alpha use a single-background estimate; no 1:1 claim.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
for group in ['walk','attack0','attack1','attack2','water0','water1','water2']:
    rs=[r for r in records if r['kind']==group];tiles=[]
    for r in rs:
        im=Image.open(OUT/(r['name']+'.webp'));tile=Image.new('RGBA',(210,250),'#404353');tile.alpha_composite(im,((210-im.width)//2,4));ImageDraw.Draw(tile).text((5,231),r['name']+' '+str(r['source_ms']),fill='white');tiles.append(tile.convert('RGB'))
    out=Image.new('RGB',(210*5,250*((len(tiles)+4)//5)),'#252730')
    for i,im in enumerate(tiles):out.paste(im,(i%5*210,i//5*250))
    out.save(QA/(group+'-v2.jpg'))
print(json.dumps({'layers':len(records),'walk_anchors':walk,'camera_shifts':sorted(set(shifts.values()))}))
