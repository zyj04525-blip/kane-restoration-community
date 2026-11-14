"""Reproducible, explicitly approximate mattes from the two official recordings.

No client assets or executable are used. Occluded pixels are NOT generated.
All six clips retain their source PTS and a 40 ms sample hold.
"""
from pathlib import Path
from research_paths import INPUT_DIR, WORK_ROOT, load_font
import sys,json,hashlib,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=WORK_ROOT
AUDIT=INPUT_DIR
import av
OUT=ROOT/'playable/assets-v3';OUT.mkdir(parents=True,exist_ok=True)
QA=ROOT/'research/skills';QA.mkdir(parents=True,exist_ok=True)
SOURCES={'wolf':QA/'ocean-wolf-228847.f4v','guide':AUDIT/'official-footage-229512.f4v'}
cache={}
def frame(src,t):
    key=(src,round(t*25))
    if key not in cache:
        with av.open(str(SOURCES[src])) as c:
            s=c.streams.video[0];c.seek(int(t/s.time_base),stream=s)
            for f in c.decode(s):
                if f.time>=t-.0001:cache[key]=(np.array(f.to_image()).astype(float),f.time);break
    return cache[key]
def segment(xs):
    groups=np.split(xs,np.where(np.diff(xs)>24)[0]+1)
    return max(groups,key=len)
def anchor(a,guess):
    # The player's green nameplate is independent of the boss's red nameplate.
    r,g,b=a.transpose(2,0,1);mask=(g>r*1.3)&(g>b*1.35)&(g>65)
    gx,gy=guess;mask[:int(gy+6)]=False;mask[int(min(477,gy+40)):]=False
    mask[:,:int(max(0,gx-145))]=False;mask[:,int(min(960,gx+145)):]=False
    y=int(mask.sum(1).argmax());xs=np.where(mask[max(0,y-1):y+2])[1]
    if len(xs)<10:return guess
    xs=segment(np.unique(xs));return [round((xs.min()+xs.max())/2),y-18]
def ellipse(w,h,cx,cy,rx,ry):
    yy,xx=np.mgrid[:h,:w];return ((xx-cx)/rx)**2+((yy-cy)/ry)**2<1
def remove_specks(mask,minimum=45):
    # Connected-component filtering, including diagonals, preserves fine edges
    # attached to the effect while rejecting isolated stars and armour flecks.
    seen=np.zeros(mask.shape,bool);out=np.zeros(mask.shape,bool);h,w=mask.shape
    for y,x in zip(*np.where(mask)):
        if seen[y,x]:continue
        todo=[(y,x)];seen[y,x]=True;group=[]
        while todo:
            py,px=todo.pop();group.append((py,px))
            for ny,nx in ((py-1,px),(py+1,px),(py,px-1),(py,px+1)):
                if 0<=ny<h and 0<=nx<w and mask[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;todo.append((ny,nx))
        if len(group)>=minimum:
            ys,xs=zip(*group);out[ys,xs]=True
    return out
def save(a,alpha,name,kind,src,t,at,box,anc,flip=False):
    x0,y0,x1,y1=box
    rgba=np.dstack([np.clip(a,0,255),np.clip(alpha*255,0,255)]).astype('uint8')
    rgba[rgba[:,:,3]==0,:3]=0
    im=Image.fromarray(rgba,'RGBA');ax=anc[0]-x0;ay=anc[1]-y0
    if flip:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT);ax=im.width-ax
    im.save(OUT/(name+'.webp'),lossless=True,exact=True)
    rec={'name':name,'kind':kind,'at_ms':round(at*1000),'source_ms':round(t*1000),'source':src,
         'source_box':box,'anchor':[ax,ay],'dimensions':list(im.size),'flipped_to_face_right':flip,
         'alpha':'recording-derived colour/background matte; occlusions remain missing'}
    manifest['layers'].append(rec)
    return im

only=sys.argv[1] if len(sys.argv)>1 else None
base=ROOT/'playable/assets-v2';manifest=json.loads(((OUT if only else base)/'manifest.json').read_text(encoding='utf-8'))
manifest['version']=3
if only:manifest['layers']=[r for r in manifest['layers'] if r['kind'] not in ('cast-'+only,'skillfx-'+only,'icon-'+only)]
else:
    for f in base.glob('*.webp'):shutil.copyfile(f,OUT/f.name)
# Decontaminate only the outermost opaque walk/idle boundary, preserving the
# silhouette and all interior pixels. No blur across the whole sprite.
bg=frame('guide',76)[0].copy();bg[240:448,:230]=frame('guide',78)[0][240:448,:230]
edge_report=[]
for rec in manifest['layers']:
    if only:continue
    if rec['kind'] not in ('idle','walk'):continue
    im=Image.open(OUT/(rec['name']+'.webp')).convert('RGBA');a=np.array(im).astype(float)
    opaque=a[:,:,3]>0;inside=np.array(Image.fromarray(np.uint8(opaque)*255).filter(ImageFilter.MinFilter(3)))>0
    edge=opaque&~inside;x0,y0,x1,y1=rec['source_box'];back=np.roll(bg,-rec.get('camera_shift',0),axis=1)[y0:y1,x0:x1]
    diff=a[:,:,:3]-back;alpha=np.clip(np.max(np.where(diff>=0,diff/np.maximum(255-back,1),-diff/np.maximum(back,1)),axis=2),0,1)
    a[edge,3]=np.maximum(alpha[edge],.12)*255
    a[edge,:3]=np.clip(back+diff/np.maximum(alpha[:,:,None],.12),0,255)[edge]
    Image.fromarray(a.astype('uint8'),'RGBA').save(OUT/(rec['name']+'.webp'),lossless=True,exact=True)
    edge_report.append({'name':rec['name'],'boundary_pixels':int(edge.sum()),'interior_unchanged':True})

# Anchors and envelopes are hand audited against the saved contact sheets.
# N: use the wolf recording; the guide's turquoise crescent belongs to the boss.
clips=[
 dict(key='h',name='冰霜拳',src='wolf',start=80.64,end=82.24,body=.56,guess=[390,344],face=1,box=[-65,-215,405,70]),
 dict(key='u',name='水幕天华',src='guide',start=161.60,end=162.48,body=.72,guess=[310,410],face=1,box=[-25,-195,415,35]),
 dict(key='n',name='冰河时代',src='wolf',start=73.28,end=76.16,body=.68,guess=[610,402],face=-1,box=[-490,-260,100,65]),
 dict(key='i',name='绝对零度',src='wolf',start=70.80,end=74.08,body=.40,guess=[535,402],face=-1,box=[-255,-85,160,65]),
 dict(key='o',name='冰晶爆裂',src='wolf',start=67.12,end=68.84,body=.64,guess=[535,402],face=-1,box=[-340,-215,65,40]),
 dict(key='l',name='究级波浪',src='wolf',start=150.96,end=155.72,body=1.08,guess=[445,380],face=-1,box=[-360,-380,345,100]),
]
for c in clips:
    if only and c['key']!=only:continue
    src=c['src'];start=c['start'];key=c['key'];count=round((c['end']-start)*25)
    # A pre-cast frame suppresses static blue floor and stars, not hidden art.
    background=frame(src,start-.24)[0];preview=[];guess=c['guess'][:]
    for j in range(count):
        t=round(start+j*.04,2);full,pts=frame(src,t)
        if key=='u':anc=[310,410]
        elif key=='i':anc=[535,402]
        else:
            found=anchor(full,guess)
            # Nameplate movement tracks camera displacement. Limit isolated UI noise.
            if abs(found[0]-guess[0])<70 and abs(found[1]-guess[1])<32:guess=found
            anc=guess[:]
        x,y=anc;dx0,dy0,dx1,dy1=c['box']
        box=[max(0,x+dx0),max(25,y+dy0),min(960,x+dx1),min(477,y+dy1)]
        x0,y0,x1,y1=box;a=full[y0:y1,x0:x1];b=background[y0:y1,x0:x1]
        r,g,bl=a.transpose(2,0,1);delta=np.max(abs(a-b),axis=2)
        # Cyan ice and neutral white water; reject the wolf's yellow/orange effects.
        cyan=(g>r*1.12)&(bl>r*1.24)&(g>85)&(bl<g*1.65)
        white=(np.min(a,axis=2)>155)&(np.max(a,axis=2)-np.min(a,axis=2)<55)&(g>=r*.99)&(bl>=r*1.01)
        mask=(cyan|white)&(delta>26)
        yy,xx=np.mgrid[y0:y1,x0:x1]
        # Nameplates, source captions, HUD and watermarks never become sprites.
        mask&=~((xx>778)&(yy>373))
        if key=='h':mask&=(xx>x+65)&(yy>y-205)
        if key=='u':
            mask&=(xx>x+105)
        if key=='n':
            mask&=(xx<x-48)&(yy>180)
        if key=='i':
            mask&=ellipse(x1-x0,y1-y0,x-x0-55,y-y0+2,215,62)
            # Actual ground mist occupies this low ellipse. Palette filtering
            # removes warm armour; hidden pixels are left transparent.
        if key=='o':mask&=(xx<x-53)&(yy>y-210)
        if key=='l':
            # Remove the dark scene's horizontal speed-lines by row baseline.
            baseline=np.percentile(full[y0:y1,780:930],55,axis=1)[:,None,:]
            mask&=np.max(a-baseline,axis=2)>18
            mask&=~ellipse(x1-x0,y1-y0,x-x0,y-y0-80,40,75)
        mask=remove_specks(mask,60 if key!='l' else 100)
        # Feather subpixel colour transitions, without invented in-between frames.
        strength=np.clip((delta-22)/75,0,1)
        alpha=mask*strength
        alpha=np.array(Image.fromarray(np.uint8(alpha*255)).filter(ImageFilter.GaussianBlur(.32)))/255
        im=save(a,alpha,'skillfx-'+key+'-'+str(j),'skillfx-'+key,src,pts,j*.04,box,anc,c['face']==-1)
        if j%max(1,count//8)==0:preview.append((im,j))
        if j<round(c['body']*25):
            bb=[max(0,x-82),max(0,y-172),min(960,x+82),min(477,y+8)]
            bx,by,br,bt=bb;body=full[by:bt,bx:br];rr,gg,bbv=body.transpose(2,0,1)
            yy2,xx2=np.mgrid[by:bt,bx:br]
            shape=ellipse(br-bx,bt-by,x-bx,y-by-76,69,96)
            # Palette envelope includes crown, hair, red bodice, gold and boots.
            blue=(gg>rr*1.16)&(bbv>rr*1.3)&(gg>68)&(bbv<gg*1.65)
            gold=(rr>100)&(gg>80)&(bbv<gg*.82)
            red=(rr>90)&(rr>gg*1.25)&(rr>bbv*1.1)
            boot=(np.min(body,axis=2)>135)&(np.max(body,axis=2)-np.min(body,axis=2)<65)
            m=(blue|gold|red|boot)&shape
            # Exclude the floor ring; its own effect belongs below the feet.
            m&=(yy2<y-11)
            if key in ('n','o','i'):m&=xx2>x-57
            if key=='h':m&=xx2<x+53
            if key=='u':m&=xx2<x+58
            al=np.array(Image.fromarray(np.uint8(m)*255).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(.35)))/255
            save(body,al,'cast-'+key+'-'+str(j),'cast-'+key,src,pts,j*.04,bb,anc,c['face']==-1)
    manifest['animations']['skillfx-'+key]={'duration_ms':count*40}
    manifest['animations']['cast-'+key]={'duration_ms':round(c['body']*1000)}
    board=Image.new('RGB',(1200,600),'#323644')
    for k,(im,j) in enumerate(preview[:8]):
        tile=Image.new('RGBA',(300,300),'#323644');im=im.copy();im.thumbnail((295,270));tile.alpha_composite(im,((300-im.width)//2,5));ImageDraw.Draw(tile).text((8,282),f'{key.upper()} {start+j*.04:.2f}s',fill='white');board.paste(tile.convert('RGB'),(k%4*300,k//4*300))
    board.save(QA/(key+'-matte-review.jpg'))
    print(key,len(manifest['layers']),flush=True)

# Recovered original five skill icons; no fabricated sixth original icon.
a,_=frame('wolf',70.64)
for i,k in enumerate('hunio'):
    if only and k!=only:continue
    if k=='o':a,_=frame('wolf',67.0)
    x0=332+i*36;im=Image.fromarray(a[502:535,x0:x0+32].astype('uint8'));im.save(OUT/('icon-'+k+'.webp'),lossless=True)
    manifest['layers'].append({'name':'icon-'+k,'kind':'icon-'+k,'anchor':[0,0],'at_ms':0,'source':'wolf','source_ms':67000 if k=='o' else 70640,'source_box':[x0,502,x0+32,535],'dimensions':[32,33]})
manifest['skill_sources']={'clips':clips,'sources':{k:{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'file':p.name} for k,p in SOURCES.items()},'limits':['Occluded source pixels remain missing; mattes are not original transparent assets.','L enemy/name overlays and horizontal streaks are masked, leaving incomplete regions.','Numeric cooldowns, costs and hit geometry are provisional; guide/wolf use different character levels.','Only recorded cast poses are available; I and N footage overlaps the persistent freeze field.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
if not only:(QA/'edge-refinement.json').write_text(json.dumps(edge_report,indent=2),encoding='utf-8')
print(json.dumps({'layers':len(manifest['layers']),'edge_sprites':len(edge_report)}))
