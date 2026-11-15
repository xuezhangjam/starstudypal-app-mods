"""Inspect the final signed APK and compare every original DEX4 method symbolically."""
from pathlib import Path
import copy,hashlib,json,re,sys,zipfile
B=Path(__file__).resolve().parent;R=B.parent.parent
sys.path[:0]=[str(R/'apk-analysis/deps'),str(R/'apk-analysis'),str(R/'apk-analysis/precision-md3e-4.0.1.0'),str(R/'apk-analysis/classroom-review-entry-fix')]
from loguru import logger
logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX
from canonical_notice_methods import methods
from dex_symbols import Symbols
import check_flow
from test_behavior import test

meta=json.loads((B/'build.json').read_text('utf8'));source=R/meta['input'];output=R/meta['output']
assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['input_sha256']
assert hashlib.sha256(output.read_bytes()).hexdigest()==meta['sha256']
for name,value in meta['own_source_sha256'].items():assert hashlib.sha256((B/name).read_bytes()).hexdigest()==value
def signature(k):return k.startswith('META-INF/') and k.upper().endswith(('.MF','.SF','.RSA','.DSA','.EC'))
with zipfile.ZipFile(source) as a,zipfile.ZipFile(output) as z:
 assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
 keys={k for k in a.namelist() if not signature(k)};newkeys={k for k in z.namelist() if not signature(k)}
 assert newkeys-keys=={'classes15.dex'} and not keys-newkeys
 assert {k for k in keys if a.read(k)!=z.read(k)}=={'classes4.dex'}
 olddex=DEX(a.read('classes4.dex'));newdex=DEX(z.read('classes4.dex'));helper=DEX(z.read('classes15.dex'));symbols=Symbols()
 for name in z.namelist():
  if re.fullmatch(r'classes\d*\.dex',name):symbols.add(z.read(name),name)
 assert all(v<=65536 for v in symbols.method_counts.values())

def norm(value,remove=()):
 access,regs,seq=value;keep=[i for i,x in enumerate(seq) if x[0]!='nop' and i not in remove];mapping={i:j for j,i in enumerate(keep)}
 for i in range(len(seq)-1,-1,-1):
  if i not in mapping and i+1 in mapping:mapping[i]=mapping[i+1]
 result=copy.deepcopy([seq[i] for i in keep])
 for op,args in result:
  for j,(kind,v) in enumerate(args):
   if kind==3:args[j]=(kind,mapping.get(v,v))
   elif kind=='targets':args[j]=(kind,[mapping.get(t,t) for t in v])
 return access,regs,result

old,new=methods(olddex),methods(newdex)
added=set(new)-set(old);assert not set(old)-set(new)
assert {(k[0].split('/')[-1],k[1],k[2]) for k in added}=={
 ('DiscussionFragment;','modCanImportAfterEnd','()Z'),('RoomLiveDocumentManager;','modDocumentType','()Lcom/hailiang/document/DocumentType;')}
delta={k for k in old if norm(old[k])!=norm(new[k])}
expected={(Path(x['file']).name[:-6],x['method']) for x in meta['changed_native_methods']}
assert {(k[0].split('/')[-1][:-1],k[1]+k[2].replace(' ','')) for k in delta}==expected
assert len(delta)==10

prefix='Lcom/hljzjx/classroom/repairs/'
removals={
 'takePhoto':(0,1),
 'onActivityResult':(-1,4),
 'endDiscussion':(0,3),
 'setPptLayout':(0,2),
 'handleMqttPPTMessage':(0,2),
 'onDocumentLoaded':(0,1),
 'restorePath':(0,1),'restorePathPoint':(0,1),'setPathInfoList':(0,1),
 'modTeacherDisplayY':(0,4)
}
for k in delta:
 seq=new[k][2]
 hooks=[i for i,(op,args) in enumerate(seq) if op.startswith('invoke') and any(kind==256 and val.startswith(prefix) for kind,val in args)]
 assert len(hooks)==1,(k,hooks)
 offset,count=removals[k[1]];start=hooks[0]+offset
 remove=set(range(start,start+count))
 assert norm(new[k],remove)==norm(old[k]),('unexpected native instruction change',k)

# Exact bridges delegate to the existing live-ended eligibility gate / document SDK.
for k in added:
 seq=new[k][2]
 assert len(seq)==(3 if k[1]=='modCanImportAfterEnd' else 4)
 target='modEndedWriteAllowed()Z' if k[1]=='modCanImportAfterEnd' else 'getDocumentType()Lcom/hailiang/document/DocumentType;'
 assert any(kind==256 and target in val.replace(' ','') for op,args in seq for kind,val in args)
assert all(c.get_name().startswith(prefix) for c in helper.get_classes()),'API/fixture code must not enter the APK'

# Real final-DEX callback CFG check, retaining the prior v4 initialization fix.
original_effect=check_flow.effect
def effect(ins):
 op=ins.get_name();regs=[a[1] for a in ins.get_operands() if int(a[0])==0]
 if op=='instance-of':return {regs[1]},{regs[0]}
 if op in ('cmpg-float','cmpl-float'):return set(regs[1:]),{regs[0]}
 if op in ('int-to-float','float-to-int'):return {regs[1]},{regs[0]}
 if op.startswith(('add-float','sub-float','mul-float','div-float')):
  return set(regs if '/2addr' in op else regs[1:]),{regs[0]}
 return original_effect(ins)
check_flow.effect=effect
focus={'onActivityResult','endDiscussion','modTeacherDisplayY','modCanImportAfterEnd','modDocumentType','takePhoto'}
flow={}
for c in newdex.get_classes():
 for method in c.get_methods():
  key=(c.get_name(),method.get_name(),method.get_descriptor())
  if key in delta|added and method.get_name() in focus:flow[method.get_name()]=check_flow.check(method)
assert len(flow)==6 and not any(v['uninitialized_reads'] for v in flow.values()),flow

original_resolve=symbols.resolve
object_methods={('<init>','()V'),('toString','()Ljava/lang/String;'),('hashCode','()I'),('equals','(Ljava/lang/Object;)Z'),('getClass','()Ljava/lang/Class;'),('clone','()Ljava/lang/Object;'),('finalize','()V')}
def strict(owner,name,desc,field=False,seen=None):
 if owner=='Ljava/lang/Object;':return not field and (name,desc) in object_methods
 return original_resolve(owner,name,desc,field,seen)
symbols.resolve=strict
touched=[newdex.get_class(owner) for owner in sorted({k[0] for k in delta|added})]
refs,errors=symbols.check(touched+helper.get_classes());assert not errors,errors[:30]

# Ensure native fields (including upload state) and all prior helpers/resources stay intact.
for c in olddex.get_classes():
 nc=newdex.get_class(c.get_name());assert nc is not None
 fields=lambda cls:{(f.get_name(),f.get_descriptor(),f.get_access_flags()) for f in cls.get_fields()}
 assert fields(c)==fields(nc)
a,b=APK(str(source)),APK(str(output))
assert a.get_package()==b.get_package()=='com.hljzjx.edu.student.classroom'
assert a.get_androidversion_code()==b.get_androidversion_code()=='322000'
assert a.get_androidversion_name()==b.get_androidversion_name()=='3.2.2.0'
assert a.get_min_sdk_version()==b.get_min_sdk_version()=='29'
assert a.get_target_sdk_version()==b.get_target_sdk_version()=='30'
assert set(a.get_permissions())==set(b.get_permissions())
assert b.is_signed_v2() and b.is_signed_v3()
cert=(b.get_certificates_der_v3() or b.get_certificates_der_v2())[0]
assert cert==(a.get_certificates_der_v3() or a.get_certificates_der_v2())[0]
behavior=test()
report={**meta,'other_payloads_identical':len(keys)-1,'existing_native_methods_unchanged':len(old)-len(delta),
 'native_edits_reduced_exactly_to_baseline':len(delta),'new_native_bridges':len(added),
 'checked_member_references':refs,'helper_classes':len(helper.get_classes()),'dex_method_counts':symbols.method_counts,
 'certificate_sha256':hashlib.sha256(cert).hexdigest(),'flow':flow,'behavior_tests':behavior,
 'scope':'final signed APK, symbolic native equivalence, member linkage, register CFG, and JVM API fixtures; no Android ART/device/service execution'}
(B/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
