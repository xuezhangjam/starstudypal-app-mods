"""Small authored SMALI method utilities; ignore debug/label spelling only."""
import re
METHOD=re.compile(r'^\.method ([^\n]+)\n.*?^\.end method',re.M|re.S)
def methods(s):return {m[1].split()[-1]:m[0] for m in METHOD.finditer(s)}
def norm(body):
 lines=[x.strip().replace('const-string/jumbo','const-string') for x in body.splitlines() if x.strip() and x.strip()!='nop' and not re.match(r'\s*(#|\.(line|local|end local|restart local|param|end param|prologue)\b)',x)]
 labels={x:':label_'+str(i) for i,x in enumerate(x for x in lines if re.fullmatch(r':[\w]+',x))}
 for i,line in enumerate(lines):
  if not line.startswith('const-string'):lines[i]=re.sub(r':[\w]+',lambda m:labels.get(m[0],m[0]),line)
 return '\n'.join(lines)
