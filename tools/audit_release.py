"""Check the explicit public source list. This is not an antivirus scanner."""
from pathlib import Path
import json,re,ast

ROOT=Path(__file__).resolve().parents[1]
ALLOWED={'.py','.js','.cjs','.css','.html','.json','.md','.txt','.csv','.yml','.yaml'}
SPECIAL={'LICENSE','.gitignore'}

def release_paths(root=ROOT):
 root=Path(root).resolve()
 data=json.loads((root/'RELEASE_FILES.json').read_text(encoding='utf-8'))
 names=data['files']
 if len(names)!=len(set(names)):raise ValueError('Duplicate release path')
 results=[]
 for name in names:
  p=Path(name)
  if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name:raise ValueError('Unsafe release path')
  path=(root/p).resolve()
  if not path.is_relative_to(root) or not path.is_file():raise ValueError('Missing/escaped release file: '+name)
  if path.suffix not in ALLOWED and path.name not in SPECIAL:raise ValueError('Non-source release entry: '+name)
  if path.stat().st_size>4_000_000:raise ValueError('Unexpectedly large release file: '+name)
  results.append((name,path))
 return results

def audit(root=ROOT):
 paths=release_paths(root);problems=[]
 patterns={
  'private_user_path':re.compile(r'[A-Za-z]:[/\\]Users[/\\][^\s"\']+',re.I),
  'private_workspace_path':re.compile(r'[A-Za-z]:[/\\](?:CodexData|Documents_ChatGPT)[/\\]',re.I),
  'github_token':re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}'),
  'private_key':re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
  'embedded_media':re.compile(r'data:(?:image|audio|video)/[^,]+;base64,[A-Za-z0-9+/]{100,}'),
 }
 for name,path in paths:
  try:text=path.read_text(encoding='utf-8-sig')
  except UnicodeDecodeError:problems.append((name,'non_utf8'));continue
  for label,pattern in patterns.items():
   if pattern.search(text):problems.append((name,label))
  if path.suffix=='.py':
   try:ast.parse(text,filename=name)
   except SyntaxError:problems.append((name,'python_syntax'))
 if problems:raise ValueError(json.dumps(problems,ensure_ascii=False))
 return {'files_checked':len(paths),'binary_payloads':0,'findings':[],
         'scope':'Explicit source list: UTF-8, path containment, selected credential/private-path patterns and Python syntax. Not malware certification.'}

if __name__=='__main__':
 try:print(json.dumps(audit(),ensure_ascii=False,indent=2))
 except (ValueError,OSError,KeyError) as e:raise SystemExit(str(e))
