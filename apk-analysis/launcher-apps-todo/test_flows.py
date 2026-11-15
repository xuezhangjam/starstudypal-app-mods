"""Execute selected final DEX control flows with observable platform services."""
from functools import cmp_to_key
import itertools

F='Lcom/hljzjx/md3/ForceLauncher;';P='Lcom/hljzjx/launch/ui/main/MainPresenter;';A='Lcom/hljzjx/launch/ui/main/MainActivity;'
T='Lcom/hljzjx/md3/TodoModel;';W='Lcom/hljzjx/md3/TodoPanel$4;';R='Lcom/hljzjx/md3/TodoPanel$4$1;'
C='Lcom/hailiang/launcher/control/ControlManager;';TP='Lcom/hljzjx/md3/TodoPanel;'
class O:
 def __init__(self,kind='Object',**fields):self.kind=kind;self.fields=fields
class It:
 def __init__(self,x):self.values=list(x);self.pos=0
class Failure(Exception):pass
def ref(args):return next((v for _,v in args if isinstance(v,str) and '->' in v),'')
def regs(args):return [v for k,v in args if k==0]
class Machine:
 def __init__(self,ms,encoded):
  self.ms=ms;self.encoded=encoded;self.allowed=None;self.installed={'app.test','com.hljzjx.edu.student.classroom'};self.policy=True
  self.enabled=[];self.launched=[];self.requests=[];self.posted=[];self.token='fixture';self.page=O(items=[],total=0);self.failure=None
  self.current=True;self.rendered=0;self.disabled=['app.test','app.other'];self.platform_info=[]
 def key(self,c,n):
  result=[k for k in self.ms if k[0]==c and k[1]==n];assert len(result)==1,result;return result[0]
 def call(self,c,n,values,stop=None):return self.execute(self.key(c,n),values,stop)
 def execute(self,key,values,stop=None):
  info=self.ms[key];rr={};first=info[1]-len(values);rr.update({first+i:v for i,v in enumerate(values)});seq=info[2];pc=0;result=None;exception=None
  raw=self.encoded[key];pcs=[p//2 for p,_ in raw.get_instructions_idx()];index={p:i for i,p in enumerate(pcs)}
  for steps in range(5000):
   op,args=seq[pc];r=regs(args);target=ref(args);nextpc=pc+1
   if stop and stop(pc,op,args):return 'ORIGINAL'
   try:
    if op=='nop' or op=='check-cast':pass
    elif op.startswith('const'):rr[r[0]]=args[1][1]
    elif op=='move-exception':rr[r[0]]=exception
    elif op.startswith('move-result'):rr[r[0]]=result
    elif op.startswith('move'):rr[r[0]]=rr[r[1]]
    elif op.startswith('iget'):
     value=rr[r[1]].fields[target.split('->')[1].split()[0]];rr[r[0]]=value
     if op=='iget-wide':rr[r[0]+1]=0
    elif op.startswith('iput'):rr[r[1]].fields[target.split('->')[1].split()[0]]=rr[r[0]]
    elif op.startswith('sget'):rr[r[0]]=self.allowed if 'allowedPackage' in target else O(target)
    elif op.startswith('sput'):
     assert 'allowedPackage' in target;self.allowed=rr[r[0]] or None
    elif op=='instance-of':
     cls=args[-1][1];v=rr[r[1]];rr[r[0]]=bool(isinstance(v,O) and (cls=='Landroid/content/Context;' and v.fields.get('context') or cls.endswith('AuthFailure;') and v.kind=='AuthFailure'))
    elif op=='new-instance':rr[r[0]]=O(args[-1][1])
    elif op=='cmp-long':rr[r[0]]=(rr[r[1]]>rr[r[2]])-(rr[r[1]]<rr[r[2]])
    elif op.startswith('goto'):nextpc=args[0][1]
    elif op.startswith('if-'):
     x=rr[r[0]];y=rr[r[1]] if len(r)>1 else 0
     if x is None:x=0
     if y is None:y=0
     mode=op[3:].rstrip('z');take={'eq':lambda:x==y,'ne':lambda:x!=y,'lt':lambda:x<y,'ge':lambda:x>=y,'gt':lambda:x>y,'le':lambda:x<=y}[mode]()
     if take:nextpc=args[-1][1]
    elif op.startswith('invoke-'):result=self.invoke(target,[rr.get(x) for x in r])
    elif op.startswith('return'):return None if op=='return-void' else rr[r[0]]
    else:raise AssertionError((key,pc,op,args))
   except Failure as e:
    exception=e;code=raw.get_code();handlers=code.get_handlers();hit=False
    for item in code.get_tries():
     if item.get_start_addr()<=pcs[pc]<item.get_start_addr()+item.get_insn_count():
      handler=next(h for h in handlers.get_list() if h.get_off()-handlers.get_off()==item.get_handler_off())
      nextpc=index[handler.get_handlers()[0].get_addr()];hit=True;break
    if not hit:raise
   pc=nextpc
  raise AssertionError(('nonterminating DEX',key))
 def invoke(self,target,v):
  owner,name=target.split('->');name=name.split('(')[0]
  if owner==F:return self.call(owner,name,v)
  if owner==P and name=='needDelete':return v[0].fields['deleted']
  if name=='needDelete':return v[0].fields['deleted']
  if name=='getPackageManager':return O('PackageManager')
  if name=='getPackageInfo':
   self.platform_info.append((v[1],v[2]))
   if v[1] not in self.installed:raise Failure('not installed')
   return O('PackageInfo')
  if name=='getApplicationPolicy':return O('Policy')
  if name=='setPackageEnabled':
   if not self.policy:raise Failure('policy unavailable')
   self.enabled.append((v[1],bool(v[2])));return True
  if name=='setClassRoomEnabled':self.enabled.append(('com.hljzjx.edu.student.classroom',True));return None
  if name=='equals':return v[0]==v[1]
  if name=='length':return len(v[0])
  if name=='toString':return v[0].fields.get('text','') if isinstance(v[0],O) else str(v[0])
  if name=='compareTo':return (v[0]>v[1])-(v[0]<v[1])
  if name=='valueOf':return 'null' if v[0] is None else str(v[0])
  if name=='getMessage':return str(v[0])
  if name=='append':v[0].fields['text']+=str(v[1]);return v[0]
  if name=='<init>':
   obj=v[0]
   if owner==R:return self.call(R,'<init>',v)
   if owner=='Ljava/lang/StringBuilder;':obj.fields['text']=str(v[1]) if len(v)>1 else ''
   elif owner=='Ljava/util/LinkedHashMap;':obj.fields['map']={}
   elif owner=='Ljava/util/ArrayList;':obj.fields['items']=list(v[1]) if len(v)>1 else []
   return None
  if name=='put':return v[0].fields['map'].setdefault(v[1],v[2])
  if name=='containsKey':return v[1] in v[0].fields['map']
  if name=='values':return list(v[0].fields['map'].values())
  if name=='iterator':return It(v[0].fields['items'] if isinstance(v[0],O) else v[0])
  if name=='hasNext':return v[0].pos<len(v[0].values)
  if name=='next':it=v[0];result=it.values[it.pos];it.pos+=1;return result
  if name=='sort':
   items=v[0].fields['items'];cmp=next(k for k in self.ms if k[0]==T[:-1]+'$1;' and k[1]=='compare' and 'TodoModel$Item;' in k[2])
   items.sort(key=cmp_to_key(lambda a,b:self.execute(cmp,[v[1],a,b])));return None
  if name=='isEmpty':return not (v[0].fields['items'] if isinstance(v[0],O) else v[0])
  if name=='emptyList':return []
  if name=='get' and isinstance(v[0],O) and 'value' in v[0].fields:return v[0].fields['value']
  if name=='get':return v[0].fields['map'].get(v[1])
  if owner==TP:
   if name=='access$6':return self.current
   if name=='access$13':return self.token
   if name=='access$14':
    self.requests.append(v[1]);assert v[1]=='pendingSubmit','correction request must be unreachable'
    if self.failure:raise Failure(self.failure)
    return 'fixture-json'
   if name=='access$15':return '登录状态已失效，请重新登录星学伴' if str(v[0])=='AUTH' else '作业加载失败 · 点击刷新重试'
   if name=='access$2':return O('Handler')
   if name=='access$9':return O('WeakReference',value=v[0].fields.get('activity'))
   read={'access$20':'homework','access$21':'submitCount','access$22':'correctionCount'}
   write={'access$16':'busy','access$17':'homework','access$18':'correctionCount','access$19':'submitCount','access$23':'state'}
   if name in read:return v[0].fields[read[name]]
   if name in write:v[0].fields[write[name]]=v[1];return None
   if name=='access$12':self.rendered+=1;return None
  if owner==W and name=='access$0':return v[0].fields['this$0']
  if owner==T and name=='parse':assert v[1]=='pendingSubmit';return self.page
  if owner==T and name=='homework':return self.call(T,name,v).fields['items']
  if name=='post':self.posted.append(v[1]);return True
  if owner.endswith('/MainView;') and name=='startApp':self.launched.append(tuple(v[1:]));return None
  raise AssertionError(('unmodeled platform call',target,v))

def run(ms,encoded):
 checks=0;cases=0
 def ok(value,message):
  nonlocal checks;checks+=1;assert value,message
 # Final native preparation code: disabled apps included; unavailable ROM APIs
 # do not crash; absent apps cannot gain the local launch exception.
 for installed,policy in itertools.product([False,True],repeat=2):
  for pkg in ['app.test','com.hljzjx.edu.student.classroom','',None]:
   vm=Machine(ms,encoded);vm.installed={pkg} if installed and pkg else set();vm.policy=policy;vm.allowed='previous.app'
   result=vm.call(F,'prepare',[O(context=True),pkg]);wanted=bool(installed and pkg)
   ok(bool(result)==wanted,'prepare needs a real installed package');ok(vm.allowed==(pkg if wanted else None),'precise one-package exception')
   if pkg:ok(vm.platform_info==[(pkg,512)],'lookup includes disabled installed apps')
   ok(vm.enabled==([(pkg,True)] if wanted and policy else []),'ROM policy remains scoped to selected package');cases+=1
 vm=Machine(ms,encoded);ok(vm.call(F,'prepare',[None,'app.test'])==0 and vm.allowed is None,'null Context cannot launch')
 # Execute the injected presenter fallback, stopping at the original path for
 # normal issued apps, absent packages or a detached presenter view.
 key=next(k for k in ms if k[0]==P and k[1]=='checkApp' and k[2]=='(Ljava/lang/String;)V')
 boundary=next(i for i,(op,args) in enumerate(ms[key][2]) if op.startswith('const') and (1,0x7f120214) in args)
 for cached,deleted,installed,context in itertools.product([False,True],repeat=4):
  for pkg in ['app.test','com.hljzjx.edu.student.classroom']:
   vm=Machine(ms,encoded);vm.installed={pkg} if installed else set();view=O(context=context)
   presenter=O(iView=view,cachedAppMap=O(map={pkg:O(deleted=deleted)} if cached else {}))
   vm.execute(key,[presenter,pkg],lambda pc,op,args:pc==boundary)
   target='com.hljzjx.student.classroom.review.MainActivity' if pkg.endswith('.classroom') else 0
   ok(bool(vm.launched)==(bool((not cached or deleted) and installed and context)),'only installed missing/deleted entries use fallback')
   if vm.launched:ok(vm.launched==[(pkg,target)],'original classroom review target preserved')
   cases+=1
 # Old code included early corrections ahead of unsubmitted tasks. Execute the
 # final merge and real DEX comparator: corrections disappear, unknown deadline
 # remains last, duplicate submission IDs are collapsed, inputs remain intact.
 item=lambda id,title,when:O(id=id,title=title,when=when)
 submissions=[item('late','Z',900),item('soon','B',100),item('unknown','X',2**63-1),item('same','A',100)]
 for count in range(12):
  vm=Machine(ms,encoded);corrections=[item('correct'+str(i),'Correction',-100-i) for i in range(count)]
  result=vm.call(T,'homework',[O(items=submissions,total=4),O(items=corrections,total=count)]).fields['items']
  ok([x.fields['id'] for x in result]==['same','soon','late','unknown'],'only unsubmitted, earliest deadline first')
  ok(len(submissions)==4 and len(corrections)==count,'server response arrays untouched');cases+=1
 vm=Machine(ms,encoded);ok(vm.call(T,'homework',[None,O(items=[item('c','C',1)],total=1)]).fields['items']==[],'corrections alone never fill home preview')
 # Execute the actual worker and its actual UI callback for successful/empty
 # results, login expiry, failures and stale account generations; no HTTP is run.
 for valid,token,failure,total in itertools.product([False,True],['','fixture'],[None,'AUTH','network'],[0,4]):
  vm=Machine(ms,encoded);vm.current=valid;vm.token=token;vm.failure=failure
  vm.page=O(items=submissions if total else [],total=total)
  panel=O(activity=O('Activity'),homework=[],submitCount=0,correctionCount=0,busy=True,state='loading')
  worker=O(**{'this$0':panel,'val$gen':1,'val$requestUser':42})
  vm.call(W,'run',[worker]);ok(vm.requests==(['pendingSubmit'] if valid and token else []),'at most one pending-submit request')
  if valid:
   ok(len(vm.posted)==1,'one UI completion');vm.call(R,'run',[vm.posted[0]])
   ok(panel.fields['busy']==0 and vm.rendered==1,'busy state completes once')
   if token and not failure:
    ok(panel.fields['submitCount']==total and panel.fields['correctionCount']==0,'only pending submissions counted')
    ok(panel.fields['state']==('待提交 4' if total else '暂无待提交作业'),'summary omits corrections')
   elif not token or failure=='AUTH':ok(not panel.fields['homework'] and '登录' in panel.fields['state'],'auth expiry stays visible')
   else:ok('加载失败' in panel.fields['state'],'network failure is not reported as an empty success')
  else:ok(not vm.posted,'stale worker cannot overwrite new account')
  cases+=1
 return {'final_dex_flow_scenarios':cases,'final_dex_flow_assertions':checks,'scope':'final DEX execution with modeled Android, package policy, HTTP and handler services; no device or server activity'}
