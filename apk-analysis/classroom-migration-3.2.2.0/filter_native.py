from pathlib import Path
import json,re
B=Path(__file__).resolve().parent;ROOT=B.parent.parent
def absolute(p):return Path('\\\\?\\'+str(p.resolve()))
OLD=absolute(B/'old-stock4/smali');MOD=absolute(ROOT/'apk-analysis/classroom-teacher-web-choice-v8/work4/smali');NEW=absolute(B/'new-original4/smali')
METHOD=re.compile(r'^\.method ([^\n]+)\n.*?^\.end method',re.M|re.S)
def methods(s):return {m[1].split()[-1]:m[0] for m in METHOD.finditer(s)}
def norm(body):
 lines=[x.strip().replace('const-string/jumbo','const-string') for x in body.splitlines() if x.strip() and x.strip()!='nop' and not re.match(r'\s*(#|\.(line|local|end local|restart local|param|end param|prologue)\b)',x)]
 labels={x:':label_'+str(i) for i,x in enumerate(x for x in lines if re.fullmatch(r':[\w]+',x))}
 for i,line in enumerate(lines):
  if not line.startswith('const-string'):
   lines[i]=re.sub(r':[\w]+',lambda m:labels.get(m[0],m[0]),line)
 return '\n'.join(lines)
def main():
 r=json.loads((B/'analysis.json').read_text('utf-8'));out={'native':[],'conflicts':[],'added_mod_classes':r['added_mod_classes']}
 for x in r['native']:
  file=x['file'];a=(OLD/file).read_text('utf-8');m=(MOD/file).read_text('utf-8');n=(NEW/file).read_text('utf-8') if (NEW/file).exists() else ''
  am,mm,nm=methods(a),methods(m),methods(n)
  changed=sorted(k for k in am.keys()&mm.keys() if norm(am[k])!=norm(mm[k]));added=sorted(mm.keys()-am.keys());removed=sorted(am.keys()-mm.keys())
  if not changed and not added and not removed and not x['class_body_changed']:continue
  y={**x,'changed':changed,'added':added,'removed':removed};out['native'].append(y)
  for k in changed:
   if k not in nm:out['conflicts'].append({'file':file,'method':k,'reason':'missing'})
   elif norm(am[k])!=norm(nm[k]):out['conflicts'].append({'file':file,'method':k,'reason':'changed','matches_mod':norm(mm[k])==norm(nm[k])})
  for k in added:
   if k in nm:out['conflicts'].append({'file':file,'method':k,'reason':'collision'})
 (B/'native-plan.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),'utf-8')
 print(json.dumps({'classes':len(out['native']),'methods':sum(len(x['changed']) for x in out['native']),'added_methods':sum(len(x['added']) for x in out['native']),'conflicts':out['conflicts']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
