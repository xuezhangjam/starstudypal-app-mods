from pathlib import Path
import difflib,json,re,sys
B=Path(__file__).resolve().parent;R=B.parent.parent
from smali_tools import METHOD,methods,norm
def long(p):return Path('\\\\?\\'+str(p.resolve()))
def main():
 old,mod,new=[long(B/x/'smali') for x in ['old','mod','new']]
 plan={'native':[],'added_classes':[],'conflicts':[]}
 for p in mod.rglob('*.smali'):
  f=p.relative_to(mod);m=p.read_text('utf8')
  if not (old/f).exists():plan['added_classes'].append(f.as_posix());continue
  a=(old/f).read_text('utf8');am,mm=methods(a),methods(m)
  changed=[k for k in am.keys()&mm.keys() if norm(am[k])!=norm(mm[k])]
  added=list(mm.keys()-am.keys());removed=list(am.keys()-mm.keys())
  outside=norm(METHOD.sub('',a))!=norm(METHOD.sub('',m))
  if not (changed or added or removed or outside):continue
  n=(new/f).read_text('utf8') if (new/f).exists() else '';nm=methods(n)
  x={'file':f.as_posix(),'changed':sorted(changed),'added':sorted(added),'removed':sorted(removed),'outside':outside}
  plan['native'].append(x)
  for k in changed:
   if k not in nm or norm(am[k])!=norm(nm[k]):
    plan['conflicts'].append({'file':f.as_posix(),'method':k,'same_mod':k in nm and norm(mm[k])==norm(nm[k])})
    name=f.stem+'-'+k.split('(')[0].replace('<','').replace('>','')+'.diff'
    (B/name).write_text(''.join(difflib.unified_diff(am[k].splitlines(True),nm.get(k,'').splitlines(True),fromfile='old',tofile='new')),'utf8')
  if outside:
   (B/(f.stem+'-fields.diff')).write_text(''.join(difflib.unified_diff(METHOD.sub('',a).splitlines(True),METHOD.sub('',m).splitlines(True),fromfile='old',tofile='mod')),'utf8')
 (B/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),'utf8')
 print(json.dumps(plan,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
