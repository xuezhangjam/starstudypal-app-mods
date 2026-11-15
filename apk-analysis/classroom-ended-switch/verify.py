from pathlib import Path
import copy,hashlib,json,re,sys,zipfile
B=Path(__file__).resolve().parent;R=B.parent.parent
sys.path[:0]=[str(R/'apk-analysis/deps'),str(R/'apk-analysis'),str(R/'apk-analysis/precision-md3e-4.0.1.0')]
from loguru import logger
logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX
from canonical_notice_methods import methods
from dex_symbols import Symbols
from test_flow import test,O
meta=json.loads((B/'build.json').read_text('utf8'));source=R/meta['input'];output=R/meta['output']
assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['input_sha256']
assert hashlib.sha256(output.read_bytes()).hexdigest()==meta['sha256']
def signature(k):return k.startswith('META-INF/') and k.upper().endswith(('.MF','.SF','.RSA','.DSA','.EC'))
with zipfile.ZipFile(source) as a,zipfile.ZipFile(output) as z:
 assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
 keys={k for k in a.namelist() if not signature(k)};assert keys=={k for k in z.namelist() if not signature(k)}
 assert {k for k in keys if a.read(k)!=z.read(k)}=={'classes4.dex'}
 original=DEX(a.read('classes4.dex'));final=DEX(z.read('classes4.dex'));symbols=Symbols()
 for k in z.namelist():
  if re.fullmatch(r'classes\d*\.dex',k):symbols.add(z.read(k),k)
print('PASS only DEX4 changed; every other payload preserved',flush=True)
def normal(value):
 access,regs,seq=value;keep=[i for i,x in enumerate(seq) if x[0]!='nop'];mapping={i:j for j,i in enumerate(keep)}
 for i in range(len(seq)-1,-1,-1):
  if i not in mapping and i+1 in mapping:mapping[i]=mapping[i+1]
 result=copy.deepcopy([seq[i] for i in keep])
 for op,args in result:
  for j,(kind,v) in enumerate(args):
   if kind==3:args[j]=(kind,mapping.get(v,v))
   elif kind=='targets':args[j]=(kind,[mapping.get(t,t) for t in v])
 return access,regs,result
old,new=methods(original),methods(final);assert old.keys()==new.keys()
delta={k for k in old if normal(old[k])!=normal(new[k])}
assert {k[1]+k[2].replace(' ','') for k in delta}==set(meta['changed_methods'])
assert {k[0] for k in delta}=={O}
refs,errors=symbols.check([final.get_class(O)]);assert not errors,errors[:20]
assert all(v<=65536 for v in symbols.method_counts.values())
flow=test(original.get_classes(),final.get_classes());print(json.dumps(flow,ensure_ascii=False),flush=True)
# State/transport APIs and the original group-info observer, history refresh,
# membership refresh, ink merge, PiP and collision-aware controls are unchanged.
for k in old:
 if k[0]!=O or k[1] not in ['modRefreshEndedTools','changeGroup','changeGroup$lambda$31$lambda$30']:assert normal(old[k])==normal(new[k])
assert old[next(k for k in old if k[0]==O and k[1]=='modEndedWriteAllowed')]==new[next(k for k in new if k[0]==O and k[1]=='modEndedWriteAllowed')]
a,b=APK(str(source)),APK(str(output))
assert a.get_package()==b.get_package()=='com.hljzjx.edu.student.classroom'
assert a.get_androidversion_code()==b.get_androidversion_code()=='322000'
assert a.get_androidversion_name()==b.get_androidversion_name()=='3.2.2.0'
assert a.get_min_sdk_version()==b.get_min_sdk_version()=='29'
assert a.get_target_sdk_version()==b.get_target_sdk_version()=='30'
assert b.is_signed_v2() and b.is_signed_v3()
cert=(b.get_certificates_der_v3() or b.get_certificates_der_v2())[0]
assert cert==(a.get_certificates_der_v3() or a.get_certificates_der_v2())[0]
assert hashlib.sha256(cert).hexdigest()=='9311b6b4b2b20da0d7366f822dbbc6f3a3bde8fac35f2ca84fefed1a2aa6316e'
report={**meta,**flow,'unchanged_payloads':len(keys)-1,'other_dex4_methods_identical':len(old)-len(delta),'checked_member_references':refs,'dex_method_counts':symbols.method_counts,'certificate_sha256':hashlib.sha256(cert).hexdigest()}
(B/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print('PASS package, SDK, same V2/V3 certificate; native server success/failure remains authoritative',flush=True)
