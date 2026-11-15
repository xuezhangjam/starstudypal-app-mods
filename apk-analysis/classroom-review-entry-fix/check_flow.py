"""Definite register initialization on the real, exception-free photo callback CFG.

This is a focused control-flow check, not a replacement for ART verification.
"""
from collections import deque

OWNER='Lcom/nice/room/ui/roomlive/fragment/discussion/DiscussionFragment;'
def photo(dex):
 return next(m for m in dex.get_class(OWNER).get_methods() if m.get_name()=='onActivityResult' and m.get_descriptor().replace(' ','')=='(IILandroid/content/Intent;)V')

def effect(ins):
 op=ins.get_name();args=ins.get_operands();r=[a[1] for a in args if int(a[0])==0]
 reads=set();writes=set()
 if op.startswith(('const','new-instance','sget','move-result','move-exception')):
  writes.add(r[0])
  if 'wide' in op:writes.add(r[0]+1)
 elif op.startswith('move'):
  writes.add(r[0]);reads.add(r[1])
  if 'wide' in op:writes.add(r[0]+1);reads.add(r[1]+1)
 elif op.startswith('iget'):
  writes.add(r[0]);reads.add(r[1])
  if 'wide' in op:writes.add(r[0]+1)
 elif op.startswith(('iput','sput','invoke','if-','check-cast','return','throw')):
  reads.update(r)
  if 'wide' in op and not op.startswith('invoke') and r:reads.add(r[0]+1)
 elif op.startswith('goto') or op=='nop':pass
 else:raise AssertionError(('unsupported opcode in focused check',op))
 return reads,writes

def check(method):
 code=method.get_code();assert code.get_tries_size()==0,'exception edges not modeled'
 nodes=dict(method.get_instructions_idx());pcs=list(nodes);indices={p:i for i,p in enumerate(pcs)}
 initial=set(range(code.get_registers_size()-code.get_ins_size(),code.get_registers_size()))
 incoming={pcs[0]:initial};pending=deque([pcs[0]])
 while pending:
  pc=pending.popleft();ins=nodes[pc];op=ins.get_name();reads,writes=effect(ins);out=incoming[pc]|writes
  nxt=pcs[indices[pc]+1] if indices[pc]+1<len(pcs) else None
  if op.startswith(('return','throw')):successors=[]
  elif op.startswith('goto'):successors=[pc+next(a[1] for a in ins.get_operands() if int(a[0])==3)*2]
  elif op.startswith('if-'):successors=[nxt,pc+next(a[1] for a in ins.get_operands() if int(a[0])==3)*2]
  else:successors=[] if nxt is None else [nxt]
  for target in successors:
   assert target in nodes,(pc,target)
   merged=out if target not in incoming else incoming[target]&out
   if target not in incoming or merged!=incoming[target]:incoming[target]=set(merged);pending.append(target)
 errors=[];uses=0
 for pc,known in incoming.items():
  reads,_=effect(nodes[pc]);uses+=len(reads)
  for reg in sorted(reads-known):errors.append({'offset_bytes':pc,'register':reg,'opcode':nodes[pc].get_name(),'instruction':nodes[pc].get_output()})
 return {'instructions':len(nodes),'reachable_instructions':len(incoming),'checked_register_reads':uses,'uninitialized_reads':errors}

def test(broken,fixed,original):
 bad,good,native=check(photo(broken)),check(photo(fixed)),check(photo(original))
 assert len(bad['uninitialized_reads'])==1 and bad['uninitialized_reads'][0]['register']==4,bad
 assert 'checkNotNullExpressionValue' in bad['uninitialized_reads'][0]['instruction'],bad
 assert not good['uninitialized_reads'],good
 assert not native['uninitialized_reads'],native
 vm=fixed.get_class('Lcom/nice/room/ui/roomlive/fragment/discussion/DiscussionViewModel;')
 upload=check(next(m for m in vm.get_methods() if m.get_name()=='appendStroke'))
 assert not upload['uninitialized_reads'],upload
 return {'broken_negative_control':bad,'fixed':good,'pre_feature_original':native,'other_new_native_branch':upload,'scope':'actual DEX callback control flow and register initialization; no ART/device/backend execution'}
