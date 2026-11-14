import unittest,tempfile,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from import_assets import within,required_files,plan_import,ENTRY,COMBAT,ENTRY_REQUIRED,GROUPS

def manifest_pair():
 entry={'frames':{k:{} for k in ENTRY_REQUIRED},'animations':{}}
 combat={'layers':[{'name':k+'-0','kind':k,'anchor':[8,16],'dimensions':[16,16],'at_ms':0} for k in sorted(GROUPS)],'animations':{k:{'duration_ms':400} for k in GROUPS if k!='guard'}}
 return entry,combat

class AssetImportTest(unittest.TestCase):
 def test_path_escape_and_windows_absolute_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   for name in ['../escape','/escape','Z:/escape','a\\..\\escape']:
    with self.subTest(name=name),self.assertRaises(ValueError):within(d,name)

 def test_manifest_cannot_request_executable_or_parent_file(self):
  for name in ['../outside','payload.exe','x/y']:
   a,b=manifest_pair();b['layers'][0]['name']=name
   with self.subTest(name=name),self.assertRaises(ValueError):required_files(a,b)

 def test_legacy_guard_and_nonlooping_animation_are_accepted(self):
  a,b=manifest_pair()
  next(r for r in b['layers'] if r['kind']=='guard').pop('at_ms')
  self.assertIn(COMBAT+'/guard-0.webp',required_files(a,b))

 def test_reversed_layer_times_rejected(self):
  a,b=manifest_pair();b['layers'].append({'name':'walk-1','kind':'walk','anchor':[1,2],'dimensions':[3,4],'at_ms':-1})
  with self.assertRaises(ValueError):required_files(a,b)

 def test_missing_input_leaves_target_untouched(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'src';dst=Path(d)/'dst';a,b=manifest_pair()
   for directory,data in [(ENTRY,a),(COMBAT,b)]:
    p=src/directory;p.mkdir(parents=True);(p/'manifest.json').write_text(json.dumps(data),encoding='utf-8')
   with self.assertRaises(ValueError):plan_import(src,dst)
   self.assertFalse(dst.exists())

 def test_wrong_media_signature_rejected_before_copy(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'src';dst=Path(d)/'dst';a,b=manifest_pair()
   for directory,data in [(ENTRY,a),(COMBAT,b)]:
    p=src/directory;p.mkdir(parents=True);(p/'manifest.json').write_text(json.dumps(data),encoding='utf-8')
   for name in required_files(a,b):
    if name.endswith('.webp'):(src/name).write_bytes(b'MZnot-an-image')
   with self.assertRaises(ValueError):plan_import(src,dst)
   self.assertFalse(dst.exists())

if __name__=='__main__':unittest.main()
