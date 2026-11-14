"""Validate/copy a local manifest-based media pack. Never fetch or execute it."""
import argparse,json,re,shutil,hashlib,math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ENTRY='entry/assets'
COMBAT='playable/assets-v6'
ENTRY_REQUIRED={'male0','female0','male1','male2','assassin','blade','sea','name-panel','splash','loading-panel','comic0','comic1','comic2','tutorial','home','town','town-dialog','town-after'}
GROUPS={'idle','walk','guard','attack0','attack1','attack2','water0','water1','water2'}|{'cast-'+k for k in 'huniol'}|{'skillfx-'+k for k in 'huniol'}
BORDER=['topbg_e3.jpg','lt.gif','rt.gif','lb.gif','rb.gif','ht.gif','hb.gif','sl.gif','sr.gif']

def within(root,relative):
 root=Path(root).resolve()
 if not isinstance(relative,str) or '\\' in relative or ':' in relative:
  raise ValueError('Invalid asset path')
 p=Path(relative)
 if p.is_absolute() or '..' in p.parts:raise ValueError('Asset path escapes its root')
 resolved=(root/p).resolve()
 if not resolved.is_relative_to(root):raise ValueError('Asset symlink escapes its root')
 return resolved

def safe_name(value):
 if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*',value):
  raise ValueError('Frame name must contain only letters, digits, hyphens or underscores')
 return value

def number(value):
 return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)

def read_manifest(root,relative):
 p=within(root,relative)
 if not p.is_file() or p.stat().st_size>4_000_000:raise ValueError('Missing or oversized manifest: '+relative)
 result=json.loads(p.read_text(encoding='utf-8-sig'))
 if not isinstance(result,dict):raise ValueError('Manifest must be an object')
 return result

def required_files(entry,combat):
 frames=entry.get('frames');animations=entry.get('animations')
 if not isinstance(frames,dict) or not ENTRY_REQUIRED.issubset(frames) or not isinstance(animations,dict):
  raise ValueError('Entry manifest lacks required frames/animations')
 files={ENTRY+'/manifest.json',COMBAT+'/manifest.json',COMBAT+'/arena.webp'}
 for name in frames:files.add(ENTRY+'/'+safe_name(name)+'.webp')
 for name,clip in animations.items():
  if name not in frames or not isinstance(clip,dict):raise ValueError('Invalid entry animation')
  sheets=clip.get('sheets');times=clip.get('times')
  if not isinstance(sheets,list) or not sheets or not isinstance(times,list) or not times:
   raise ValueError('Entry animation needs sheets and times')
  if not all(number(t) and t>=0 for t in times) or times!=sorted(times):raise ValueError('Invalid entry times')
  if len(sheets)!=math.ceil(len(times)/10):raise ValueError('Entry atlas count does not match frame times')
  for i,sheet in enumerate(sheets):
   if not isinstance(sheet,dict):raise ValueError('Invalid sheet record')
   filename=sheet.get('file','')
   if not filename.endswith('.webp'):raise ValueError('Only WebP animation sheets are accepted')
   safe_name(filename[:-5])
   if sheet.get('count')!=min(10,len(times)-i*10):raise ValueError('Invalid sheet frame count')
   files.add(ENTRY+'/'+filename)
 layers=combat.get('layers');clips=combat.get('animations')
 if not isinstance(layers,list) or not layers or not isinstance(clips,dict):raise ValueError('Invalid combat manifest')
 names=set();kinds=set();previous={}
 for row in layers:
  if not isinstance(row,dict):raise ValueError('Invalid layer record')
  name=safe_name(row.get('name'));kind=safe_name(row.get('kind'))
  if name in names:raise ValueError('Duplicate layer name: '+name)
  names.add(name);kinds.add(kind)
  anchor=row.get('anchor');size=row.get('dimensions');at=row.get('at_ms',0 if kind=='guard' else None)
  if not isinstance(anchor,list) or len(anchor)!=2 or not all(number(v) for v in anchor):raise ValueError('Invalid anchor')
  if not isinstance(size,list) or len(size)!=2 or not all(isinstance(v,int) and 0<v<=8192 for v in size):raise ValueError('Invalid layer dimensions')
  if not number(at) or at<0 or at<previous.get(kind,0):raise ValueError('Layer times must be ordered within each group')
  previous[kind]=at
  files.add(COMBAT+'/'+name+'.webp')
 if not GROUPS.issubset(kinds):raise ValueError('Combat manifest lacks required groups: '+', '.join(sorted(GROUPS-kinds)))
 for kind in GROUPS-{'guard'}:
  clip=clips.get(kind)
  if not isinstance(clip,dict) or not number(clip.get('duration_ms')) or clip['duration_ms']<=0 or not isinstance(clip.get('loop',False),bool):
   raise ValueError('Invalid animation timing: '+kind)
 return files

def validate_media(path):
 size=path.stat().st_size
 if size>100_000_000:raise ValueError('Oversized media: '+path.name)
 with path.open('rb') as f:header=f.read(16)
 ext=path.suffix.lower()
 if ext=='.webp':valid=len(header)>=12 and header[:4]==b'RIFF' and header[8:12]==b'WEBP' and int.from_bytes(header[4:8],'little')+8==size
 elif ext=='.jpg':valid=header.startswith(b'\xff\xd8\xff')
 elif ext=='.gif':valid=header.startswith((b'GIF87a',b'GIF89a'))
 else:valid=False
 if not valid:raise ValueError('File header does not match allowed media format: '+path.name)

def plan_import(source,target,replace=False):
 source=Path(source).resolve();target=Path(target).resolve()
 entry=read_manifest(source,ENTRY+'/manifest.json')
 combat=read_manifest(source,COMBAT+'/manifest.json')
 files=required_files(entry,combat)
 for name in BORDER:
  if within(source,ENTRY+'/'+name).is_file():files.add(ENTRY+'/'+name)
 plan=[]
 for relative in sorted(files):
  src=within(source,relative);dst=within(target,relative)
  if not src.is_file():raise ValueError('Missing media: '+relative)
  if src.suffix!='.json':validate_media(src)
  if dst.exists() and (not dst.is_file() or (not replace and hashlib.sha256(src.read_bytes()).digest()!=hashlib.sha256(dst.read_bytes()).digest())):
   raise ValueError('Different target exists; use --replace only if intended: '+relative)
  plan.append((src,dst))
 return plan

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--source',required=True,type=Path)
 parser.add_argument('--check-only',action='store_true')
 parser.add_argument('--replace',action='store_true')
 args=parser.parse_args()
 try:
  plan=plan_import(args.source,ROOT,args.replace)
  if not args.check_only:
   for src,dst in plan:
    if src==dst:continue
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,dst)
  print(json.dumps({'validated_files':len(plan),'copied':0 if args.check_only else len(plan),'check_only':args.check_only}))
 except (ValueError,OSError,KeyError,TypeError) as e:parser.exit(1,str(e)+'\n')

if __name__=='__main__':main()
