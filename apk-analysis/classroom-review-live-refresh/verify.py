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
from check_flow import check,photo
from test_photo_limit import test as photo_test
meta=json.loads((B/'build.json').read_text('utf8'));source=R/meta['input'];output=R/meta['output']
assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['input_sha256']
assert hashlib.sha256(output.read_bytes()).hexdigest()==meta['sha256']
for name,value in meta['own_source_sha256'].items():assert hashlib.sha256((B/name).read_bytes()).hexdigest()==value
def signature(k):return k.startswith('META-INF/') and k.upper().endswith(('.MF','.SF','.RSA','.DSA','.EC'))
with zipfile.ZipFile(source) as a,zipfile.ZipFile(output) as z:
 assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
 keys={k for k in a.namelist() if not signature(k)};assert keys=={k for k in z.namelist() if not signature(k)}
 assert {k for k in keys if a.read(k)!=z.read(k)}=={'classes4.dex','classes14.dex'}
 olddex=DEX(a.read('classes4.dex'));newdex=DEX(z.read('classes4.dex'));helper=DEX(z.read('classes14.dex'));symbols=Symbols()
 for name in z.namelist():
  if re.fullmatch(r'classes\d*\.dex',name):symbols.add(z.read(name),name)
 assert all(v<=65536 for v in symbols.method_counts.values())
def normalized(value,remove=None):
 access,regs,seq=value;keep=[i for i,x in enumerate(seq) if x[0]!='nop' and i!=remove];mapping={i:j for j,i in enumerate(keep)}
 for i in range(len(seq)-1,-1,-1):
  if i not in mapping and i+1 in mapping:mapping[i]=mapping[i+1]
 result=copy.deepcopy([seq[i] for i in keep])
 for op,args in result:
  for j,(kind,v) in enumerate(args):
   if kind==3:args[j]=(kind,mapping.get(v,v))
   elif kind=='targets':args[j]=(kind,[mapping.get(t,t) for t in v])
 return access,regs,result
old,new=methods(olddex),methods(newdex);assert old.keys()==new.keys()
delta={k for k in old if normalized(old[k])!=normalized(new[k])};assert len(delta)==2,delta
key=next(k for k in delta if k[1]=='handlePenWriteEvent$lambda$23');assert key[0]=='Lcom/nice/room/ui/roomlive/tool/RoomToolBarView;'
assert new[key][2][0]==('invoke-static',[(0,1),(0,4),(256,'Lcom/hljzjx/classroom/reviewdraw/ReviewDrawing;->touch(Lcom/nice/room/ui/roomlive/tool/RoomToolBarView; Landroid/view/MotionEvent;)V')])
assert normalized(new[key],0)==normalized(old[key]),'the native event handler must only gain a prefix call'
# The photo entry keeps exactly the native picker/listener suffix, without
# the previous count/filter/limit-toast prefix.
pk=next(k for k in delta if k[1]=='takePhoto');assert pk[0]=='Lcom/nice/room/ui/roomlive/fragment/discussion/DiscussionFragment;'
orig_photo=normalized(old[pk]);new_photo=normalized(new[pk])
start=next(i for i,(op,args) in enumerate(orig_photo[2]) if op=='new-instance' and (259,'Lcom/nice/room/ui/roomlive/fragment/ask/TakePhotoFragment;') in args)
assert orig_photo[:2]==new_photo[:2] and orig_photo[2][start:]==new_photo[2]
# The prior entry-crash fix and every other native method remain exact.
for k in old:
 if k not in delta:assert normalized(old[k])==normalized(new[k])
tool=newdex.get_class(key[0]);touch=next(m for m in tool.get_methods() if m.get_name()==key[1])
frag=newdex.get_class(pk[0]);entry=next(m for m in frag.get_methods() if m.get_name()=='takePhoto')
old_entry=next(m for m in olddex.get_class(pk[0]).get_methods() if m.get_name()=='takePhoto')
limit=photo_test(old_entry,entry)
flow={'photo_callback':check(photo(newdex)),'touch_hook':check(touch),'photo_entry':check(entry)}
assert not any(x['uninitialized_reads'] for x in flow.values())
assert all(c.get_name().startswith('Lcom/hljzjx/classroom/reviewdraw/') for c in helper.get_classes()),'test/API classes in APK'
original_resolve=symbols.resolve
object_methods={('<init>','()V'),('toString','()Ljava/lang/String;'),('hashCode','()I'),('equals','(Ljava/lang/Object;)Z'),('getClass','()Ljava/lang/Class;'),('clone','()Ljava/lang/Object;'),('finalize','()V')}
def strict(owner,name,desc,field=False,seen=None):
 if owner=='Ljava/lang/Object;':return not field and (name,desc) in object_methods
 return original_resolve(owner,name,desc,field,seen)
symbols.resolve=strict
refs,errors=symbols.check([tool,frag]+helper.get_classes());assert not errors,errors[:30]
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
report={**meta,'unchanged_payloads':len(keys)-2,'other_dex4_methods_identical':len(old)-2,'checked_member_references':refs,'helper_classes':len(helper.get_classes()),'dex_method_counts':symbols.method_counts,'certificate_sha256':hashlib.sha256(cert).hexdigest(),'flow':flow,'photo_limit_test':limit}
(B/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
