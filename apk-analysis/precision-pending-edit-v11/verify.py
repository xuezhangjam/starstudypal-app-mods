"""Final APK: preserve original request coroutine, native code, and narrow edit hooks."""
import copy,hashlib,json,re,sys,zipfile
from build import B,R,SOURCE,DEST,EXPECTED,OWN
from patch_native import VM,HOME,REPO,SELECT,PHOTO,CARD,SUBMIT
sys.path[:0]=[str(R/'apk-analysis/deps'),str(R/'apk-analysis'),str(R/'apk-analysis/precision-md3e-4.0.1.0'),str(R/'apk-analysis/classroom-review-entry-fix')]
from loguru import logger
logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX
from canonical_notice_methods import methods
from dex_symbols import Symbols
from check_flow import check
OBJECT_METHODS={('<init>','()V'),('equals','(Ljava/lang/Object;)Z'),('hashCode','()I'),('toString','()Ljava/lang/String;'),('getClass','()Ljava/lang/Class;'),('clone','()Ljava/lang/Object;'),('finalize','()V'),('notify','()V'),('notifyAll','()V'),('wait','()V'),('wait','(J)V'),('wait','(JI)V')}
class StrictSymbols(Symbols):
 def resolve(self,owner,name,desc,field=False,seen=None):
  if owner=='Ljava/lang/Object;':return not field and (name,desc) in OBJECT_METHODS
  return super().resolve(owner,name,desc,field,seen)
def signature(n):return n.startswith('META-INF/') and n.upper().endswith(('.MF','.SF','.RSA','.DSA','.EC'))
def mmap(d):return{(k[0],k[1],k[2].replace(' ','')):v for k,v in methods(d).items()}
def norm(value,remove=()):
 flags,regs,seq=value;keep=[i for i,x in enumerate(seq) if x[0]!='nop' and i not in remove];mapping={i:j for j,i in enumerate(keep)}
 for i in range(len(seq)-1,-1,-1):
  if i not in mapping and i+1 in mapping:mapping[i]=mapping[i+1]
 result=copy.deepcopy([seq[i] for i in keep])
 for op,args in result:
  for j,(kind,v) in enumerate(args):
   if kind==3:args[j]=(kind,mapping.get(v,v))
   elif kind=='targets':args[j]=(kind,[mapping.get(t,t) for t in v])
 return flags,regs,result
def main():
 meta=json.loads((B/'build.json').read_text('utf8'));assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
 assert hashlib.sha256(DEST.read_bytes()).hexdigest()==meta['sha256']
 assert meta['own_source_sha256']=={p.relative_to(B).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (B/'src').glob('*.kt')}
 symbols=StrictSymbols();before={};after={}
 with zipfile.ZipFile(SOURCE) as a,zipfile.ZipFile(DEST) as z:
  assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
  names={n for n in a.namelist() if not signature(n)};assert names=={n for n in z.namelist() if not signature(n)}
  assert {n for n in names if a.read(n)!=z.read(n)}=={'classes5.dex','classes11.dex'}
  for n in z.namelist():
   if re.fullmatch(r'classes\d*\.dex',n):symbols.add(z.read(n),n)
  for n in [5,11]:before[n]=DEX(a.read(f'classes{n}.dex'));after[n]=DEX(z.read(f'classes{n}.dex'))
 own=lambda name:name.startswith(OWN) or name=='Lcom/android/tools/r8/annotations/LambdaMethod;'
 old={k:v for d in before.values() for k,v in mmap(d).items() if not own(k[0])};new={k:v for d in after.values() for k,v in mmap(d).items() if not own(k[0])}
 assert set(old)<=set(new)
 added=set(new)-set(old);assert len(added)==7,added
 assert {k[1] for k in added}=={'modRevisionGroupId','modRevisionRepository','modRevisionHandlers','modRevisionRefresh','modBeginRevision','modSubmitWorkGroupOriginal'}
 delta={k for k in old if norm(old[k])!=norm(new[k])};assert len(delta)==6,delta
 def key(owner,name):return next(k for k in old if k[0]=='L'+owner+';' and k[1]==name)
 nav=key(HOME,'registerEntries$lambda$0$0$0$0');ctor=key(VM,'<init>');submit=key(REPO,'submitWorkGroup');resume=key(REPO+'$submitWorkGroup$1','invokeSuspend');mark=key(CARD,'MarkIcon')
 state=key(VM,'isSubmittedByApi')
 assert delta=={nav,ctor,submit,resume,mark,state}
 assert norm(old[state])==norm(new[state],range(7))
 assert norm(old[nav])==norm(new[nav],range(5))
 seq=new[ctor][2];hook=next(i for i,(op,args) in enumerate(seq) if any(k==256 and 'PendingEdits;->attach(' in v for k,v in args))
 assert seq[hook-1][0]=='move-object/from16' and norm(old[ctor])==norm(new[ctor],[hook-1,hook])
 renamed=('L'+REPO+';','modSubmitWorkGroupOriginal',SUBMIT)
 assert norm(old[submit])==norm(new[renamed]),'entire original HTTP coroutine remains unchanged'
 rs=copy.deepcopy(new[resume]);count=0
 for op,args in rs[2]:
  for i,(kind,v) in enumerate(args):
   if kind==256 and 'modSubmitWorkGroupOriginal' in v:args[i]=(kind,v.replace('modSubmitWorkGroupOriginal','submitWorkGroup'));count+=1
 assert count==1 and norm(rs)==norm(old[resume]),'continuation resumes original coroutine without repeating wrapper'
 for k in [submit,mark]:assert len(new[k][2])==(3 if k==submit else 2)
 for d in before.values():
  for c in d.get_classes():
   if own(c.get_name()):continue
   nc=next((dd.get_class(c.get_name()) for dd in after.values() if dd.get_class(c.get_name())),None);assert nc
   fields=lambda cl:{(f.get_name(),f.get_descriptor(),f.get_access_flags()) for f in cl.get_fields()}
   assert fields(c)==fields(nc) and c.get_superclassname()==nc.get_superclassname() and c.get_interfaces()==nc.get_interfaces()
 compiled=mmap(DEX((B/'helper11/classes.dex').read_bytes()));hm=mmap(after[11])
 assert {k:norm(v) for k,v in hm.items() if k[0].startswith(OWN)}=={k:norm(v) for k,v in compiled.items() if k[0].startswith(OWN)}
 controllers=[OWN+n+';' for n in ['AnswerVisibility','InkHistory','InkJournal']]
 original_helper=mmap(before[11])
 assert {k:norm(v) for k,v in original_helper.items() if k[0] in controllers}=={k:norm(v) for k,v in hm.items() if k[0] in controllers}
 selected=[c for c in after[11].get_classes() if c.get_name().startswith(OWN)]+[after[5].get_class('L'+rel+';') for rel in [VM,HOME,REPO,REPO+'$submitWorkGroup$1',SELECT,PHOTO,CARD]]
 refs,errors=symbols.check(selected);assert not errors,errors[:30]
 assert all(n<=65536 for n in symbols.method_counts.values())
 flow={}
 for c in after[5].get_classes():
  for m in c.get_methods():
   k=(c.get_name(),m.get_name(),m.get_descriptor().replace(' ',''))
   if k in added or k in [submit,mark]:
    if k==renamed:continue
    flow[c.get_name()+'->'+m.get_name()]=check(m)
 assert not any(v['uninitialized_reads'] for v in flow.values())
 apk,base=APK(str(DEST)),APK(str(SOURCE));assert apk.get_package()==base.get_package()=='com.hailiang.workcloud.student'
 assert apk.get_androidversion_name()==base.get_androidversion_name()=='4.0.1.0' and apk.get_androidversion_code()==base.get_androidversion_code()=='400100'
 assert apk.get_min_sdk_version()==base.get_min_sdk_version()=='29' and apk.get_target_sdk_version()==base.get_target_sdk_version()=='36'
 assert set(apk.get_permissions())==set(base.get_permissions()) and apk.is_signed_v2() and apk.is_signed_v3()
 cert=(apk.get_certificates_der_v3() or apk.get_certificates_der_v2())[0];assert cert==(base.get_certificates_der_v3() or base.get_certificates_der_v2())[0]
 report={**meta,'passed':True,'native_methods_changed':6,'new_bridges_and_preserved_http_method':7,'other_native_methods_identical':len(old)-6,'other_payloads_identical':len(names)-2,'original_http_coroutine_identical':True,'native_reply_and_error_paths_preserved':True,'checked_member_references':refs,'flow':flow,'method_ids_per_dex':symbols.method_counts,'certificate_sha256':hashlib.sha256(cert).hexdigest(),'scope':'Final signed APK, symbolic native preservation, register and linkage checks; no ART, Pixel, school requests or real submission.'}
 (B/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
