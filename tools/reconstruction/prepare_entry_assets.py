"""Extract observed UI states. No generated art, guessed inpainting or target execution.

Source frames are compressed recording evidence, not recovered client sprites.
The manifest retains source timestamps and visible obstructions for each state.
"""
from pathlib import Path
from research_paths import INPUT_DIR, WORK_ROOT, load_font
import hashlib, json, sys
from PIL import Image, ImageDraw

AUDIT = INPUT_DIR
import av

ROOT = WORK_ROOT
OUT = ROOT/'entry'/'assets'
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = AUDIT/'official-footage-229512.f4v'
records = {}

def frame(t):
    with av.open(str(SOURCE)) as c:
        stream = c.streams.video[0]
        c.seek(int(t/stream.time_base), stream=stream)
        for f in c.decode(stream):
            if f.time >= t - .0001:
                return f.to_image().convert('RGB'), round(f.time, 3)
    raise ValueError(t)

def save(name, t, obstruction='', crop=None):
    im, actual = frame(t)
    if crop: im = im.crop(crop)
    im.save(OUT/(name+'.webp'), lossless=True)
    records[name] = dict(time=actual, crop=crop, obstruction=obstruction,
                         sha256=hashlib.sha256(im.tobytes()).hexdigest(), size=list(im.size))
    return im

save('male0', 20.8)
save('female0', 25.8)
save('male1', 29.72, '原录像教程字幕遮挡人物下半部')
save('male2', 31.0, '原录像教程字幕遮挡人物下半部')
save('assassin', 37.0, '原录像教程字幕遮挡人物脚部及属性')
save('blade', 39.16)
save('sea', 41.32)
panel=save('name-panel', 45.12, crop=(348,205,614,354)).convert('RGBA')
# Remove the outer rectangle belonging to the recorded scene; retain the panel pixels.
# Boundary tracing is a reconstruction choice, recorded separately from the raw crop.
mask=Image.new('L',panel.size)
ImageDraw.Draw(mask).polygon([(10,2),(251,2),(264,12),(248,135),(239,146),(26,146),(16,135),(1,14)],fill=255)
panel.putalpha(mask);panel.save(OUT/'name-panel.webp',lossless=True,exact=True)
records['name-panel']['extraction']='manually-traced-outer-panel-boundary'
records['name-panel']['sha256']=hashlib.sha256(panel.tobytes()).hexdigest()
save('splash', 69.0)
save('loading-panel', 52.0, crop=(325,233,635,318))
save('comic0', 60.0)
save('comic1', 64.0)
save('comic2', 68.0)
save('tutorial', 72.0)
save('home', 254.0)
save('town', 265.0)
save('town-dialog', 266.0)
save('town-after', 290.0)

# Only the unoccluded default selection is animated. Each frame remains original size.
# A full frame is retained so no guessed alpha layer or regenerated background is used.
animations = {}
for key,start,end in [('male0',20.0,21.0),('sea',41.0,41.8),('blade',39.0,39.6)]:
    images=[]; times=[]
    with av.open(str(SOURCE)) as c:
        stream=c.streams.video[0];c.seek(int(start/stream.time_base),stream=stream)
        for f in c.decode(stream):
            if f.time > end+.0001:break
            if f.time>=start-.0001:
                images.append(f.to_image().convert('RGB'));times.append(round(f.time,3))
    # 5 columns; browser draws only one unscaled 960x560 cell at a time.
    sheets=[]
    for offset in range(0,len(images),10):
        batch=images[offset:offset+10]
        atlas=Image.new('RGB',(960*5,560*((len(batch)+4)//5)))
        for i,im in enumerate(batch):atlas.paste(im,((i%5)*960,(i//5)*560))
        name=f'{key}-animation-{offset//10}.webp';atlas.save(OUT/name,lossless=True)
        sheets.append(dict(file=name,count=len(batch)))
    animations[key]=dict(times=times,sheets=sheets,fps=25,loop='recorded-excerpt-loop-not-original-cycle')

manifest=dict(source='https://video.5054399.com/v/v2/video_229512.xml',
              source_file_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              source_dimensions=[960,560],frames=records,animations=animations,
              limitations=['Video compression and recording watermark remain.',
                          'Login/server-selection screen is not documented by this clip.',
                          'Female appearances 2 and 3 are not available as full previews.',
                          'Recorded animation excerpt looping is not verified as the original cycle.',
                          'Post-creation battle is a reference screen, not implemented gameplay.'])
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'screens':len(records),'animation_frames':{k:len(v['times']) for k,v in animations.items()},
                  'asset_bytes':sum(p.stat().st_size for p in OUT.iterdir())},ensure_ascii=False))
