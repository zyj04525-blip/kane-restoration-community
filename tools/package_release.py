"""Package only allowlisted source files; never publish or upload."""
from pathlib import Path
import hashlib,json,zipfile
from audit_release import ROOT,audit,release_paths

def package(root=ROOT):
 root=Path(root).resolve()
 audit(root)
 paths=release_paths(root)
 sums=''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+n+'\n' for n,p in paths if n!='SHA256SUMS.txt')
 (root/'SHA256SUMS.txt').write_text(sums,encoding='utf-8',newline='\n')
 result=audit(root)
 out=root/'dist';out.mkdir(exist_ok=True)
 archive=out/'kane-restoration-community-v0.1.0-source.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,path in release_paths(root):
   info=zipfile.ZipInfo('kane-restoration-community/'+name,date_time=(2026,11,13,0,0,0))
   info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
   z.writestr(info,path.read_bytes())
 digest=hashlib.sha256(archive.read_bytes()).hexdigest()
 archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n',encoding='utf-8')
 with zipfile.ZipFile(archive) as z:
  if z.testzip() is not None:raise ValueError('ZIP integrity check failed')
  expected={'kane-restoration-community/'+n for n,_ in release_paths(root)}
  if set(z.namelist())!=expected:raise ValueError('ZIP file list differs from allowlist')
 return {**result,'archive':str(archive),'bytes':archive.stat().st_size,'sha256':digest}

if __name__=='__main__':print(json.dumps(package(),ensure_ascii=False,indent=2))
