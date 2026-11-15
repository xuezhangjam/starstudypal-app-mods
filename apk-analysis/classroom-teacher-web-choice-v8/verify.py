from pathlib import Path
import copy,hashlib,json,re,sys,zipfile
B=Path(__file__).resolve().parent;ROOT=B.parent.parent;sys.path[:0]=[str(ROOT/'apk-analysis/deps'),str(ROOT/'apk-analysis')]
from loguru import logger
logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX
from canonical_notice_methods import methods
from launcher_dex_linkage import DexLinker
meta=json.loads((B/'build.json').read_text('utf-8'));source=ROOT/meta['input'];output=ROOT/meta['output']
assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['input_sha256'];assert hashlib.sha256(output.read_bytes()).hexdigest()==meta['sha256']
def sig(n):return n.startswith('META-INF/') and n.upper().endswith(('.MF','.SF','.RSA','.DSA','.EC'))
with zipfile.ZipFile(source) as a,zipfile.ZipFile(output) as z:
 assert z.testzip() is None
 before={n for n in a.namelist() if not sig(n)};after={n for n in z.namelist() if not sig(n)}
 assert after-before=={'classes12.dex'} and not before-after
 changed={n for n in before if a.read(n)!=z.read(n)};assert changed=={'classes4.dex'},changed
 assert hashlib.sha256(z.read('classes12.dex')).hexdigest()==meta['helper_dex_sha256']
 old=DEX(a.read('classes4.dex'));dexes={n:DEX(z.read(n)) for n in z.namelist() if re.fullmatch(r'classes\d*\.dex',n)}
om,nm=methods(old),methods(dexes['classes4.dex'])
THIRD='Lcom/nice/room/ui/roomlive/interaction/impl/ThirdAppInteraction;';HELPER='Lcom/hljzjx/classroom/mod/TeacherWebLinks;'
added=set(nm)-set(om);assert {k[1] for k in added}=={'modCanOpenWeb','modKeepWebShortcut','modOpenWebInClass'} and all(k[0]==THIRD for k in added)
assert not set(om)-set(nm)
expected={k for k in om if k[0]==THIRD and k[1] in {'openApp','openApp$lambda$1','end','handleMessage'}};assert len(expected)==4
delta={k for k in om if om[k]!=nm[k]};assert expected<=delta
def strip(seq,removed):
 mapping={i:n for n,i in enumerate(i for i in range(len(seq)) if i not in removed)};kept=copy.deepcopy([x for i,x in enumerate(seq) if i not in removed])
 for op,args in kept:
  for j,(kind,value) in enumerate(args):
   if kind==3:args[j]=(kind,mapping[value])
   elif kind=='targets':args[j]=(kind,[mapping[v] for v in value])
 return kept
def nn(seq):return strip(seq,{i for i,(op,args) in enumerate(seq) if op=='nop'})
for k in delta-expected:assert om[k][:2]==nm[k][:2] and nn(om[k][2])==nn(nm[k][2]),k
for k in expected:
 seq=nm[k][2]
 if k[1]=='openApp':
  assert [x[0] for x in seq[:6]]==['iget-boolean','if-nez','invoke-static','move-result','if-eqz','return-void'];removed=set(range(6))
  assert any(HELPER+'->offer(' in str(v) for kind,v in seq[2][1])
 elif k[1]=='openApp$lambda$1':
  assert [x[0] for x in seq[:5]]==['invoke-static','move-result','if-nez','sget-object','return-object'];removed=set(range(5))
  assert any(HELPER+'->allowNative(' in str(v) for kind,v in seq[0][1])
 elif k[1]=='end':
  assert seq[0][0]=='invoke-static' and any(HELPER+'->close(' in str(v) for kind,v in seq[0][1]);removed={0}
 else:
  calls=[i for i,(op,args) in enumerate(seq) if op=='invoke-static' and any(HELPER+'->close(' in str(v) for kind,v in args)];assert len(calls)==1;removed=set(calls)
  assert seq[calls[0]-1][0]=='iput-boolean' and any('->classroomEnded Z' in str(v) for kind,v in seq[calls[0]-1][1])
 assert om[k][:2]==nm[k][:2] and nn(om[k][2])==nn(strip(seq,removed)),k
# Make sure the native original URL-opening body and its whitelist/browser
# fragment code were not replaced by a simulated implementation.
PAT=re.compile(r'^\.method ([^\n]+)\n.*?^\.end method',re.M|re.S)
FILE='com/nice/room/ui/roomlive/interaction/impl/ThirdAppInteraction.smali'
base_text=(B/'base4/smali'/FILE).read_text('utf-8');work_text=(B/'work4/smali'/FILE).read_text('utf-8')
assert 'TeacherWebLinks;' not in base_text
assert '.catchall {:mod_try_start .. :mod_try_end} :mod_open_failed' in work_text
bridge=[m[0] for m in PAT.finditer(work_text) if ' modOpenWebInClass(' in m[1]][0]
assert bridge.count('->modWebChoiceBypass:Z')==3 and '->openApp()V' in bridge and 'throw v1' in bridge
old_fields={(f.get_name(),f.get_descriptor(),f.get_access_flags()) for f in old.get_class(THIRD).get_fields()}
new_fields={(f.get_name(),f.get_descriptor(),f.get_access_flags()) for f in dexes['classes4.dex'].get_class(THIRD).get_fields()}
assert new_fields-old_fields=={('modWebChoiceBypass','Z',2)} and not old_fields-new_fields
classes=[c for d in dexes.values() for c in d.get_classes()];assert len(classes)==len({c.get_name() for c in classes})
helpers=list(dexes['classes12.dex'].get_classes());assert all(c.get_name().startswith(HELPER[:-1]) for c in helpers)
refs,errors=DexLinker(dexes.values()).check(helpers+[dexes['classes4.dex'].get_class(THIRD)]);assert not errors,errors[:30]
base,apk=APK(str(source)),APK(str(output));assert base.get_package()==apk.get_package()=='com.hljzjx.edu.student.classroom'
assert base.get_androidversion_code()==apk.get_androidversion_code()=='321000' and base.get_androidversion_name()==apk.get_androidversion_name()=='3.2.1.0'
assert apk.get_min_sdk_version()==base.get_min_sdk_version()=='29' and apk.get_target_sdk_version()==base.get_target_sdk_version()=='30'
assert apk.is_signed_v2() and apk.is_signed_v3();cert=(apk.get_certificates_der_v3() or apk.get_certificates_der_v2())[0];assert cert==(base.get_certificates_der_v3() or base.get_certificates_der_v2())[0]
tests=json.loads((B/'tests.json').read_text('utf-8'));assert tests['passed']
assert tests['source_sha256']==meta['source_sha256']==hashlib.sha256((B/'src/com/hljzjx/classroom/mod/TeacherWebLinks.java').read_bytes()).hexdigest()
report={**meta,'preserved_payloads':len(before)-1,'other_native_methods_identical':len(om)-len(delta),'alignment_only_methods':len(delta-expected),'changed_native_methods':[k[1] for k in sorted(expected)],'added_native_methods':[k[1] for k in sorted(added)],'original_method_tails_preserved':True,'all_v7_dex9_10_11_resources_manifest_identical':True,'checked_member_references':refs,'certificate_sha256':hashlib.sha256(cert).hexdigest(),'tests':tests,'limitations':'Authored Java with observable Android/native fixtures and DEX instruction/reference checks, not a Pixel Tablet/browser resolver/real teacher-dispatch integration test. No classroom HTTP/MQTT, installation or data clearing.'}
(B/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
