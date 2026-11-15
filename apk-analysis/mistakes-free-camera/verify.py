"""Audit the final signed APK, capture guards, full-frame policy and untouched code."""
from pathlib import Path
import copy,hashlib,itertools,json,re,sys,zipfile
B=Path(__file__).resolve().parent;ROOT=B.parent.parent
sys.path[:0]=[str(ROOT/'apk-analysis/deps'),str(ROOT/'apk-analysis')]
from loguru import logger
logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX
from canonical_notice_methods import methods
from launcher_dex_linkage import DexLinker
meta=json.loads((B/'build.json').read_text('utf-8'));source=ROOT/meta['input'];output=ROOT/meta['output']
assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['input_sha256']
assert hashlib.sha256(output.read_bytes()).hexdigest()==meta['sha256']
def signature(n):return n.startswith('META-INF/') and n.upper().endswith(('.MF','.SF','.RSA','.DSA','.EC'))
with zipfile.ZipFile(source) as a,zipfile.ZipFile(output) as b:
 assert b.testzip() is None
 before={n for n in a.namelist() if not signature(n)};after={n for n in b.namelist() if not signature(n)}
 assert after-before=={'classes7.dex'} and not before-after
 delta={n for n in before if a.read(n)!=b.read(n)};assert delta=={'classes4.dex'},delta
 print('PASS ZIP payloads: only DEX4 modified, DEX7 added',flush=True)
 original=DEX(a.read('classes4.dex'))
 dexes={n:DEX(b.read(n)) for n in b.namelist() if re.fullmatch(r'classes\d*\.dex',n)}
 print('Loaded final DEX files',flush=True)
old,new=methods(original),methods(dexes['classes4.dex']);assert old.keys()==new.keys()
changed={k for k in old if old[k]!=new[k]}
P='Lcom/hailiang/xxb/ai/camera/view/';H='Lcom/nice/errorbook/m3e/CameraCapturePolicy;'
capture=(P+'scan/SmartCameraActivity;','capture','(Lcom/hailiang/xxb/ai/camera/view/data/SmartCameraConfig;)V')
save=(P+'scan/SmartCameraViewModel$saveImage$2;','invokeSuspend','(Ljava/lang/Object;)Ljava/lang/Object;')
preview=(P+'SmartCameraPreview;','updateEdgeArea','(Lcom/hailiang/xxb/ai/camera/core/scan/EdgeArea; Z)V')
assert changed=={capture,save,preview},changed
assert old[capture][:2]==new[capture][:2] and old[save][:2]==new[save][:2]
def regs(args):return [x[1] for x in args if x[0]==0]
def ref(args):return next((x[1] for x in args if isinstance(x[1],str) and '->' in x[1]),'')
def restore(oseq,nseq,cuts):
 i=j=0;rebuilt=[];mapping={};copied=[]
 for oa,ob,na,nb in cuts+[(len(oseq),len(oseq),len(nseq),len(nseq))]:
  assert oa-i==na-j,(oa,ob,na,nb,i,j)
  while i<oa:
   mapping[j]=i;rebuilt.append(copy.deepcopy(nseq[j]));copied.append(False);i+=1;j+=1
  for pos in range(na,nb):mapping[pos]=oa
  rebuilt.extend(copy.deepcopy(oseq[oa:ob]));copied.extend([True]*(ob-oa));i=ob;j=nb
 for copied_original,(op,args) in zip(copied,rebuilt):
  if copied_original:continue
  for pos,arg in enumerate(args):
   if arg[0]==3:args[pos]=(3,mapping[arg[1]])
   elif arg[0]=='targets':args[pos]=('targets',[mapping[x] for x in arg[1]])
 assert rebuilt==oseq,'Instructions outside the reviewed local capture changes differ'

o,n=old[capture][2],new[capture][2]
start=next(i for i,(op,args) in enumerate(o) if op=='iget-boolean' and '->isCapturing ' in ref(args))
assert n[0]==('const/4',[(0,0),(1,0)])
restore(o,n,[(0,start,0,1)])
assert not any('tipScanFailed' in ref(args) or 'getLastlyEdge' in ref(args) for op,args in n)

o,n=old[save][2],new[save][2]
oa=next(i for i,(op,args) in enumerate(o) if op=='iget-object' and '->$scanner ' in ref(args))
ob=next(i for i in range(oa,len(o)) if o[i]==('const/4',[(0,4),(1,2)]))
helper=next(i for i,(op,args) in enumerate(n) if '->full(' in ref(args))
assert n[helper-1]==('const/4',[(0,6),(1,0)]) and regs(n[helper][1])==[2] and n[helper+1]==('move-result-object',[(0,7)])
fixed=next(i for i in range(ob,len(o)) if '->access$getFixedEdgeArea$p(' in ref(o[i][1]))
replacement=next(i for i in range(helper+2,len(n)) if n[i]==('move-object',[(0,6),(0,7)]))
restore(o,n,[(oa,ob,helper-1,helper+2),(fixed-1,fixed+2,replacement,replacement+1)])
assert [op for op,args in new[preview][2]]==['invoke-static','return-void']
assert ref(new[preview][2][0][1])==H+'->status('+P+'SmartCameraPreview;)V'
assert regs(new[preview][2][0][1])==[0]
print('PASS all original methods except the three reviewed local camera changes',flush=True)

# Execute the final capture method against sixteen scanner/edge/busy/provider
# combinations. The mock stops at camera submission, without opening a camera.
def run_capture(scanner,edge,busy,provider):
 seq=new[capture][2];registers={6:'activity',7:'config'};pc=0;last=None;calls=[];capturing=busy
 for steps in range(120):
  op,args=seq[pc];rr=regs(args);target=next((x[1] for x in args if x[0]==3),None);reference=ref(args);nextpc=pc+1
  if op.startswith('const-string'):registers[rr[0]]=args[1][1]
  elif op.startswith('const'):registers[rr[0]]=args[1][1]
  elif op.startswith('move-result'):registers[rr[0]]=last
  elif op.startswith('move-object'):registers[rr[0]]=registers.get(rr[1])
  elif op=='new-instance':registers[rr[0]]='object'
  elif op.startswith('sget-object'):registers[rr[0]]='singleton'
  elif op.startswith('iget-'):
   field=reference.split('->')[1].split(' ')[0]
   registers[rr[0]]=capturing if field=='isCapturing' else ('provider' if provider else None) if field=='smartCameraProvider' else ('scanner' if scanner else None) if field=='scanner' else 'field'
  elif op=='iput-boolean':capturing=registers[rr[0]]
  elif op in {'if-eqz','if-nez'}:
   value=registers.get(rr[0]);zero=value is None or value==0
   if zero==(op=='if-eqz'):nextpc=target
  elif op=='check-cast':pass
  elif op.startswith('invoke-'):
   values=[registers.get(r) for r in rr]
   if 'CameraProvider;->capture(' in reference:calls.append(values);last=None
   elif 'CameraActivity$capture$1$1;-><init>' in reference:assert values[2] in (None,0)
   elif 'createImageUuid' in reference:last='test-photo'
   elif 'getCaptureDirectory' in reference:last='/private/camera'
   elif 'StringBuilder;->append' in reference:last=values[0]
   elif 'StringBuilder;->toString' in reference:last='HL_IMG_test-photo'
   else:last=None
  elif op=='return-void':return calls,capturing
  else:raise AssertionError(op)
  pc=nextpc
 raise AssertionError('Capture did not return')
capture_cases=0
for scanner,edge,busy,provider in itertools.product([False,True],repeat=4):
 calls,flag=run_capture(scanner,edge,busy,provider);capture_cases+=1
 assert len(calls)==(0 if busy or not provider else 1)
 assert bool(flag)
print('PASS final DEX capture control flow:',capture_cases,'cases',flush=True)
helper_classes=list(dexes['classes7.dex'].get_classes());assert [c.get_name() for c in helper_classes]==[H]
allclasses=[c for d in dexes.values() for c in d.get_classes()];assert len(allclasses)==len({c.get_name() for c in allclasses})
linker=DexLinker(dexes.values());audited=[c for c in dexes['classes4.dex'].get_classes() if c.get_name() in {k[0] for k in changed}]+helper_classes
references,errors=linker.check(audited);assert not errors,errors[:20]
base,apk=APK(str(source)),APK(str(output))
assert apk.get_package()==base.get_package()=='com.nice.errorbook'
assert apk.get_main_activity()==base.get_main_activity() and apk.get_androidversion_code()==base.get_androidversion_code()=='3320'
assert apk.get_androidversion_name()==base.get_androidversion_name()=='3.3.2.0'
assert apk.is_signed_v2() and apk.is_signed_v3()
cert=(apk.get_certificates_der_v3() or apk.get_certificates_der_v2())[0]
assert cert==(base.get_certificates_der_v3() or base.get_certificates_der_v2())[0]
assert hashlib.sha256(cert).hexdigest()=='7b128cdc8d4ff2fb798cbca4d79aa3b26e8edb192cf56f42290b02ae46cbfe4f'
policy=(B/'policy-test-results.txt').read_text('utf-8');assert policy.startswith('PASS 197 assertions; 16 full-frame photo scenarios')
report={**meta,'preserved_payloads':len(before)-1,'changed_existing_payloads':['classes4.dex'],'other_original_dex4_methods_identical':len(old)-len(changed),'reviewed_changes':['capture without detected edge while preserving busy guard','save full photo instead of rejecting missing document boundary','replace document status with free capture label'],'capture_control_flow_cases':capture_cases,'photo_policy_assertions':197,'full_frame_size_scenarios':16,'checked_member_references':references,'new_classes':len(helper_classes),'certificate_sha256':hashlib.sha256(cert).hexdigest(),'same_signature_as_previous_mod':True,'can_overwrite_previous_mod':True,'all_other_original_dex_manifest_resources_assets_native_libraries':'byte-identical','real_camera_and_server_upload_tested':False}
(B/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
