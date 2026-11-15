"""Execute selected real DEX instructions with modeled views and transport."""
import copy,itertools
O='Lcom/nice/room/ui/roomlive/fragment/discussion/DiscussionFragment;'
class Model:
 def __init__(self,state='ENDED',history=False,added=True,view=True,group=10,tool='BRUSH',kind=1):
  self.state=state;self.history=history;self.added=added;self.view=object() if view else None;self.groupId=group;self.kind=kind;self.hasChangeGroup=False
  self.binding={'tvSwitchGroup':{'visibility':8},'handwriteToolbar':{'visibility':8,'selected':tool},'handwrite':{'enabled':False,'canDraw':False,'paths':['old group ink']},'tvCountdown':{'text':'已结束'},'tvTitle':{'text':'第1组'}}
  self.events=[]
def get(obj,field):return obj[field] if isinstance(obj,dict) else getattr(obj,field)
def put(obj,field,value):
 if isinstance(obj,dict):obj[field]=value
 else:setattr(obj,field,value)
class Machine:
 def __init__(self,classes):
  self.methods={m.get_name():m for c in classes if c.get_name()==O for m in c.get_methods()}
 def run(self,name,values):
  method=self.methods[name];code=list(method.get_instructions_idx());indices={pc:i for i,(pc,ins) in enumerate(code)}
  regs={method.get_code().get_registers_size()-len(values)+i:v for i,v in enumerate(values)};result=None;index=0
  for steps in range(2000):
   pc,ins=code[index];op=ins.get_name();args=ins.get_operands();r=[a[1] for a in args if a[0]==0];ref=next((a[2] for a in args if len(a)>2),None);nextpc=index+1
   if op.startswith('invoke-'):
    target=ref.split('->',1)[1].split('(',1)[0];v=[regs.get(x) for x in r];obj=v[0] if v else None
    if target.startswith('mod'):result=self.run(target,v)
    elif target=='getViewModel' and name=='changeGroup':return 'NATIVE_CHOOSER'
    elif target=='isAdded':result=obj.added
    elif target=='getView':result=obj.view
    elif target=='isAfterClass':result=obj.history
    elif target=='getDiscussionInfo':result=obj
    elif target=='getDiscussionState':result=obj.state
    elif target=='getGroupType':result=obj.kind
    elif target=='getBinding':result=obj.binding
    elif target=='getGroupId':result=obj['groupId']
    elif target=='getSelectTool':result=obj['selected']
    elif target=='get':result=obj[v[1]]
    elif target in ['setVisibility','setEnabled','setCanDraw','setText']:
     field={'setVisibility':'visibility','setEnabled':'enabled','setCanDraw':'canDraw','setText':'text'}[target];obj[field]=v[1];result=None
    elif target=='clear':obj['paths']=[];result=None
    elif target in ['unsubscribeGroup','subscribeGroup']:obj.events.append((target,v[1]));result=None
    elif target=='publishJoinGroup':obj.events.append((target,v[1],v[3]));result=None
    elif target=='getString':result='换组失败'
    elif target=='show$default':
     values[0].events.append(('toast',v[1]));result=None
    elif target=='checkNotNullExpressionValue':result=None
    else:raise AssertionError(('unexpected invocation',name,target))
   elif op.startswith('move-result'):
    regs[r[0]]=result
    if op=='move-result-wide':regs[r[0]+1]=0
   elif op.startswith('move'):regs[r[0]]=regs[r[1]]
   elif op.startswith('iget'):regs[r[0]]=get(regs[r[1]],ref.split('->')[1].split(' ')[0]);
   elif op.startswith('iput'):put(regs[r[1]],ref.split('->')[1].split(' ')[0],regs[r[0]])
   elif op.startswith('sget'):regs[r[0]]=ref.split('->')[1].split(' ')[0]
   elif op.startswith('const-string'):regs[r[0]]=ref
   elif op.startswith('const'):regs[r[0]]=args[-1][1]
   elif op=='cmp-long':regs[r[0]]=(regs[r[1]]>regs[r[2]])-(regs[r[1]]<regs[r[2]])
   elif op in ['check-cast','nop']:pass
   elif op.startswith('if-'):
    a=regs[r[0]];b=regs[r[1]] if len(r)>1 else 0
    if a is None:a=0
    if b is None:b=0
    mode=op[3:].rstrip('z')
    if {'eq':lambda:a==b,'ne':lambda:a!=b,'le':lambda:a<=b,'lt':lambda:a<b,'ge':lambda:a>=b,'gt':lambda:a>b}[mode]():nextpc=indices[pc+args[-1][1]*2]
   elif op.startswith('goto'):nextpc=indices[pc+args[-1][1]*2]
   elif op.startswith('return'):return None if op=='return-void' else regs[r[0]]
   else:raise AssertionError((name,op,args))
   # wide field values occupy two register slots in the real VM.
   if op=='iget-wide':regs[r[0]+1]=0
   index=nextpc
  raise AssertionError(('nonterminating DEX fixture',name))
def test(oldclasses,newclasses):
 before,after=Machine(oldclasses),Machine(newclasses);checks=0;cases=0
 def ok(b,msg):
  nonlocal checks;checks+=1;assert b,msg
 # Reproduce the screenshot's missing switch button in the exact prior APK.
 baseline=Model();before.run('modRefreshEndedTools',[baseline]);ok(baseline.binding['tvSwitchGroup']['visibility']==8,'negative control reproduces missing ended button')
 baseline.kind=2;ok(before.run('changeGroup',[baseline]) is None,'previous assigned-group guard blocks the chooser after end')
 for state,history,added,view,group,tool,kind in itertools.product(['DISCUSSING','ENDED','PRESENTING','FINISHED'],[False,True],[False,True],[False,True],[0,10,2**40],['DRAG','BRUSH','ERASER'],[1,2]):
  cases+=1;m=Model(state,history,added,view,group,tool,kind);prior=copy.deepcopy(m.binding);allowed=state=='ENDED' and not history and added and view and group>0
  after.run('modRefreshEndedTools',[m]);ok((m.binding['tvSwitchGroup']['visibility']==0)==allowed,'ended visibility guarded by live fragment and current group')
  if allowed:
   ok(m.binding['handwrite']['enabled'] and m.binding['handwriteToolbar']['visibility']==0,'ended writing retained')
   ok(bool(m.binding['handwrite']['canDraw'])==(tool!='DRAG'),'drag does not accidentally write')
   ok(m.binding['tvCountdown']['text']=='已结束 · 可继续书写','ended status retained')
  else:ok(m.binding==prior,'other states and history unchanged')
  reached=after.run('changeGroup',[m]);ok((reached=='NATIVE_CHOOSER')==(kind!=2 or allowed),'assigned groups only relax after this live discussion has ended')
  ok((m.state,m.groupId,m.history,m.hasChangeGroup)==(state,group,history,False),'UI does not fake a running discussion or membership')
 # Only a successful native callback can change group/title, clear the old
 # canvas, switch subscriptions and publish membership; errors keep all intact.
 for success,tool in itertools.product([False,True],['DRAG','BRUSH','ERASER']):
  cases+=1;m=Model(tool=tool);m.binding['tvSwitchGroup']['visibility']=0;prior=copy.deepcopy(m.binding)
  after.run('changeGroup$lambda$31$lambda$30',[m,['第1组','第2组'],1,{'groupId':22},success])
  if success:
   ok(m.groupId==22 and m.binding['tvTitle']['text']=='第2组','accepted group and title update')
   ok(m.events==[('unsubscribeGroup',10),('subscribeGroup',22),('publishJoinGroup',10,22)],'original transport order retained')
   ok(m.binding['handwrite']['paths']==[] and m.binding['handwrite']['enabled'],'old ink cleared and ended tools restored')
   ok(bool(m.binding['handwrite']['canDraw'])==(tool!='DRAG'),'selected tool retained after switch')
  else:
   ok(m.groupId==10 and m.binding==prior,'server failure does not mutate group or canvas')
   ok(m.events==[('toast','换组失败')],'native failure remains visible')
  ok(m.state=='ENDED' and not m.hasChangeGroup,'no fake resume or one-switch quota')
 m=Model()
 for i in range(20):
  old=m.groupId;target=100+i;after.run('changeGroup$lambda$31$lambda$30',[m,['next'],0,{'groupId':target},True]);after.run('modRefreshEndedTools',[m]);
  ok(m.groupId==target and m.binding['tvSwitchGroup']['visibility']==0 and m.state=='ENDED','repeated ended switching remains available')
  ok(m.events[-3:]==[('unsubscribeGroup',old),('subscribeGroup',target),('publishJoinGroup',old,target)],'every switch uses the native accepted route')
 return {'state_scenarios':cases,'final_dex_assertions':checks,'negative_controls':2,'repeated_switches':20,'scope':'actual DEX helpers, guards and accepted/failed callback instructions with modeled Android views and transport; no device/server activity'}
