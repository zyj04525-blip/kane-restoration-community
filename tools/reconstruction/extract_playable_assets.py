"""Recording-derived layers for a real-time prototype; NOT original client assets.

All alpha masks are estimates. Only observed source colors are retained.
No EXE is acquired or run, and no generated character art is substituted.
"""
from pathlib import Path
from research_paths import INPUT_DIR, WORK_ROOT, load_font
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=WORK_ROOT
AUDIT=INPUT_DIR
import av
OUT=ROOT/'playable/assets';OUT.mkdir(parents=True,exist_ok=True)
RESEARCH=ROOT/'research/playable';RESEARCH.mkdir(parents=True,exist_ok=True)
SOURCE=AUDIT/'official-footage-229512.f4v'
cache={}
def frame(t):
    ms=round(t*1000)
    if ms in cache:return cache[ms]
    with av.open(str(SOURCE)) as c:
        s=c.streams.video[0];c.seek(int(t/s.time_base),stream=s)
        for f in c.decode(s):
            if f.time>=t-.0001:
                a=f.to_ndarray(format='rgb24');cache[ms]=a;return a
    raise ValueError(t)

bg=frame(76).copy()
# Same camera position in both observations. At 78s the player has vacated this area.
bg[240:448,0:230]=frame(78)[240:448,0:230]
Image.fromarray(bg).save(OUT/'arena.webp',lossless=True)
records=[]
def shifted_bg(dx):
    return np.roll(bg,-dx,axis=1)

def camera_shift(t):
    a=frame(t).astype(float);b=bg.astype(float);scores=[]
    for dx in range(0,380):
        e=np.abs(a[242:260,0:960-dx:3]-b[242:260,dx:960:3]).mean(axis=2)
        scores.append((float(np.quantile(e,.6)),dx))
    return min(scores)[1]

def layer(t,box,anchor,kind,dx=0,blue_only=False):
    x0,y0,x1,y1=box;rgb=frame(t)[y0:y1,x0:x1].copy()
    back=shifted_bg(dx)[y0:y1,x0:x1].astype(float)
    delta=np.max(np.abs(rgb.astype(float)-back),axis=2)
    if kind=='attack':
        # Permit a 2px background sampling difference caused by camera resampling.
        full=shifted_bg(dx).astype(float);distances=[]
        for oy in [-2,-1,0,1,2]:
            for ox in [-2,-1,0,1,2]:
                distances.append(np.max(np.abs(rgb.astype(float)-full[y0+oy:y1+oy,x0+ox:x1+ox]),axis=2))
        delta=np.min(distances,axis=0)
    mask=delta>30
    if kind=='attack':
        mask[:max(0,214-y0),:max(0,635-x0)]=False
    if blue_only:
        mask &= (rgb[:,:,2].astype(float)-rgb[:,:,0]>28)&(rgb[:,:,1]>100)&(rgb[:,:,2]>rgb[:,:,1]*.88) | ((rgb.min(axis=2)>185)&(delta>45))
    # Close tiny compression holes; this is an estimated silhouette, not an exact matte.
    m=Image.fromarray(np.uint8(mask)*255).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    mask=np.array(m)>0
    # Remove isolated noise components while keeping separated limbs/weapon details.
    seen=np.zeros(mask.shape,bool);keep=np.zeros(mask.shape,bool)
    for yy,xx in zip(*np.where(mask)):
        if seen[yy,xx]:continue
        todo=[(yy,xx)];seen[yy,xx]=True;component=[]
        while todo:
            y,x=todo.pop();component.append((y,x))
            for ny,nx in [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]:
                if 0<=ny<mask.shape[0] and 0<=nx<mask.shape[1] and mask[ny,nx] and not seen[ny,nx]:
                    seen[ny,nx]=True;todo.append((ny,nx))
        if len(component)>=(120 if kind in ['attack','guard'] else 18):
            for y,x in component:keep[y,x]=True
    rgba=np.dstack((rgb,np.uint8(keep)*255))
    if kind=='guard':
        silhouette=Image.new('L',(x1-x0,y1-y0))
        ImageDraw.Draw(silhouette).polygon([(63,5),(77,8),(89,18),(91,40),(84,53),(100,63),(100,80),(94,83),(97,107),(88,121),(95,141),(97,160),(81,164),(70,157),(63,158),(56,152),(40,149),(38,135),(45,115),(28,119),(10,136),(0,140),(0,121),(20,110),(33,104),(11,99),(10,79),(15,62),(36,51),(45,44),(48,24)],fill=255)
        keep &= np.array(silhouette)>0
        rgba[:,:,3]=np.uint8(keep)*255
    rgba[~keep,:3]=0
    index=len([r for r in records if r['kind']==kind]);name=f'{kind}-{index}'
    image=Image.fromarray(rgba,'RGBA');image.save(OUT/(name+'.webp'),lossless=True,exact=True)
    records.append(dict(name=name,kind=kind,source_ms=round(t*1000),source_box=box,
        anchor=[anchor[0]-x0,anchor[1]-y0],camera_shift=dx,alpha='estimated-background-difference',
        dimensions=list(image.size)))
    return image

# Stable camera, no enemy or tutorial text in these body rectangles.
for t in [73.0,73.12,73.24,73.36,73.48,73.60]:
    layer(t,[82,250,192,410],[140,403],'idle')
# Estimate the body's horizontal position from changed pixels in a constrained motion corridor.
positions=[]
for i in range(18):
    t=77.04+i*.04;a=frame(t);guess=300+(t-77)*220;lo=max(0,int(guess)-90);hi=min(505,int(guess)+90)
    patch=a[398:423,lo:hi].astype(float);delta=np.max(np.abs(patch-bg[398:423,lo:hi]),axis=2)
    blue=(patch[:,:,2]>140)&(patch[:,:,1]>110)&(patch[:,:,2]>patch[:,:,0]*1.3)&(patch[:,:,1]>patch[:,:,0]*1.2)&(delta>40)
    xx=np.where(blue)[1]+lo;cx=int((xx.min()+xx.max())/2) if len(xx) else int(guess)
    # A common foot anchor follows the actual body, not the fixed crop origin.
    x0=max(0,cx-80);x1=min(505,cx+85)
    layer(t,[x0,250,x1,410],[cx,403],'walk');positions.append([round(t,2),cx])

# Source attacks at 82-84s use a 136px camera offset; keep the actor separate from targets.
for i in range(20):
    t=92.36+i*.04
    layer(t,[555,185,710,385],[650,372],'attack',camera_shift(t))
layer(85.0,[548,214,651,379],[610,371],'guard',camera_shift(85))
# A visible water burst, separated by a blue-color mask. Its original alpha is unknown.
for t in [87.68,87.76,87.84,87.92,88.0,88.08,88.16,88.24]:
    layer(t,[670,225,895,395],[690,390],'water',camera_shift(t),blue_only=True)

manifest={'source':'https://video.5054399.com/v/v2/video_229512.xml',
 'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'background':{'file':'arena.webp','base_ms':76000,'patch_ms':78000,'patch_box':[0,240,230,448]},
 'layers':records,'walk_anchor_observations':positions,
 'limits':['Alpha, anchors, and hit geometry are estimated, not source game data.',
           'Guard currently has one recovered pose.',
           'Water alpha and animation cycle are not independently verified.',
           'The background retains recording HUD/watermark; it is not a recovered map file.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
tiles=[]
for r in records:
    im=Image.open(OUT/(r['name']+'.webp'));tile=Image.new('RGBA',(200,200),'#34374b');im.thumbnail((180,170));tile.alpha_composite(im,((200-im.width)//2,0));ImageDraw.Draw(tile).text((4,179),r['name']+' '+str(r['source_ms']),fill='white');tiles.append(tile.convert('RGB'))
sheet=Image.new('RGB',(1000,((len(tiles)+4)//5)*200),'#25252c')
for i,tile in enumerate(tiles):sheet.paste(tile,(i%5*200,i//5*200))
sheet.save(RESEARCH/'extracted-layers.jpg')
print(json.dumps({'layers':len(records),'walk_anchors':positions},ensure_ascii=False))
