"""Signed artifact checks and execution of final DEX control/icon paths."""
from pathlib import Path
import copy,hashlib,importlib.util,json,re,struct,sys,zipfile
from lxml import etree as E
B=Path(__file__).resolve().parent;R=B.parent.parent
sys.path[:0]=[str(R/'apk-analysis/deps'),str(R/'apk-analysis'),str(R/'apk-analysis/precision-md3e-4.0.1.0')]
from loguru import logger
logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX
from canonical_notice_methods import methods
from dex_symbols import Symbols
meta=json.loads((B/'build.json').read_text('utf8'));inputs=meta['inputs']
DEST=R/meta['output']
assert hashlib.sha256(DEST.read_bytes()).hexdigest()==meta['sha256']
for row in inputs:assert hashlib.sha256((R/row['file']).read_bytes()).hexdigest()==row['sha256']
stock,mod,new=[R/x['file'] for x in inputs]
def signature(n):return n.startswith('META-INF/') and n.upper().endswith(('.MF','.SF','.RSA','.DSA','.EC'))
with zipfile.ZipFile(new) as n,zipfile.ZipFile(mod) as m,zipfile.ZipFile(DEST) as z:
 assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
 for k in ['classes.dex','classes2.dex','classes4.dex']:assert n.read(k)==z.read(k)
 for i in [6,7,8]:assert m.read(f'classes{i}.dex')==z.read(f'classes{i}.dex')
 resources={k for k in m.namelist() if k.startswith('res/') or k=='resources.arsc'}
 assert resources=={k for k in z.namelist() if k.startswith('res/') or k=='resources.arsc'}
 for k in resources:assert m.read(k)==z.read(k),k
 assert z.read('classes10.dex')==(B/'helper-dex/classes.dex').read_bytes()
 original=DEX(n.read('classes3.dex'));old5=DEX(m.read('classes5.dex'))
 syms=Symbols();ds={};untouched=[]
 for k in z.namelist():
  if re.fullmatch(r'classes\d*\.dex',k):
   syms.add(z.read(k),k)
   if k not in ['classes.dex','classes2.dex','classes4.dex']:ds[k]=DEX(z.read(k))
 for k in n.namelist():
  if signature(k) or k.startswith('res/') or k in ['AndroidManifest.xml','resources.arsc','classes3.dex']:continue
  assert n.read(k)==z.read(k),k;untouched.append(k)
print('PASS ZIP, native DEX1/2/4 and exact mod resource payloads',len(resources),flush=True)
changes=json.loads((B/'changes.json').read_text('utf8'))
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
def mapping(d):return {(k[0],k[1],k[2].replace(' ','')):v for k,v in methods(d).items()}
def key(x):
 name,desc=x['method'].split('(',1);return 'L'+x['file'][:-6]+';',name,'('+desc
om=mapping(original);nm={**mapping(ds['classes3.dex']),**mapping(ds['classes9.dex'])}
rows=changes['native']+changes['updates'];expected={key(x) for x in rows if x['action']=='changed'};added={key(x) for x in rows if x['action']=='added'}
assert not om.keys()-nm.keys()
assert nm.keys()-om.keys()==added,(nm.keys()-om.keys(),added)
delta={k for k in om if normal(om[k])!=normal(nm[k])}
assert delta==expected,{'unexpected':list(delta-expected),'missing':list(expected-delta)}
raw3=methods(ds['classes3.dex']);raw5=methods(ds['classes5.dex']);ms={**raw3,**raw5}
oldmap,newmap=mapping(old5),mapping(ds['classes5.dex'])
want={('Lcom/hljzjx/md3/LocalAppCatalog;','bindIcon'),('Lcom/hljzjx/md3/ForceLauncher;','openTarget')}
assert not oldmap.keys()-newmap.keys()
assert {(k[0],k[1]) for k in oldmap if normal(oldmap[k])!=normal(newmap[k])}==want
assert all(k[0]=='Lcom/hljzjx/md3/SystemAppIcons;' for k in newmap.keys()-oldmap.keys())
allclasses=[c for d in ds.values() for c in d.get_classes()];defs={c.get_name():c for c in allclasses}
for c in original.get_classes():
 x=defs[c.get_name()];assert (c.get_access_flags(),c.get_superclassname(),c.get_interfaces())==(x.get_access_flags(),x.get_superclassname(),x.get_interfaces())
 assert {(f.get_name(),f.get_descriptor(),f.get_access_flags()) for f in c.get_fields()}=={(f.get_name(),f.get_descriptor(),f.get_access_flags()) for f in x.get_fields()}
assert 'Lcom/hailiang/launcher/core/rom/ClassRoomPackageHelper;' not in syms.classes
assert all(n<=65536 for n in syms.method_counts.values())
owners={k[0] for k in expected|added}
checked=[c for c in allclasses if c.get_name() in owners or syms.classes[c.get_name()]['dex'] in ['classes5.dex','classes6.dex','classes7.dex','classes8.dex','classes10.dex']]
refs,errors=syms.check(checked);assert not errors,errors[:30]
assert all(c.get_name().startswith('Lcom/hljzjx/md3/updates/') for c in ds['classes10.dex'].get_classes()),'compile-only declarations leaked'
assert ('lastNameTime','J') in syms.classes['Lcom/hljzjx/md3/updates/ManualUpdates;']['fields']
print('PASS native methods',len(om)-len(delta),'unchanged; references',refs,flush=True)
for owner,names in {
 'Lcom/hljzjx/launch/ui/main/MainActivity;':['handleClassroom','checkForegroundActivity','onGetClassRoomIdSuccess','logOutResult'],
 'Lcom/hailiang/launcher/common/app/AppLauncher;':['start','openApp'],
 'Lcom/hailiang/launcher/control/ControlManager;':['initRomRules'],
 'Lcom/hailiang/launcher/app/data/repository/AppRepository;':['openClassRoom'],
}.items():
 for name in names:
  for k in om:
   if k[0]==owner and k[1]==name:assert normal(om[k])==normal(nm[k])
update_owner='Lcom/hailiang/launcher/update/LauncherUpdateManager;'
for name in ['checkUpdate','forceCheckUpdate','requestLaunchVersionWithCheckDialog']:
 for k in om:
  if k[0]==update_owner and k[1]==name:assert normal(om[k])==normal(nm[k])
for k,v in nm.items():
 if k[0]=='Lcom/hailiang/launcher/common/download/app/AppUpdateManager;' and k[1] in ['installApp','installApp$lambda$3']:
  assert v[2]==[('return-void',[])]
 if k[0]==update_owner and k[1] in ['showAppUpdateDialog','showCheckUpdateDialog','showDownloadDialog']:
  assert 'ManualUpdates;->offerBean' in str(v) and not any(w in str(v) for w in ['disableGestureMode','showDownloadDialog(','buildAndShow','applicationOverlay'])
full=next(v for k,v in nm.items() if k[0]=='Lcom/hljzjx/launch/ui/main/MainPresenter$5;' and k[1]=='apply' and k[2].startswith('(Lcom/jchou'))
calls=[str(args) for op,args in full[2] if op.startswith('invoke-')]
assert next(i for i,x in enumerate(calls) if 'ManualUpdates;->detectBeans' in x)<next(i for i,x in enumerate(calls) if '->saveAppList(' in x),'optional updates must see the full raw response'
# Remove exactly the three inserted instructions and restore their branch
# indices: the complete new vendor response handler must otherwise be intact.
v=normal(full);seq=v[2];at=next(i for i,x in enumerate(seq) if 'ManualUpdates;->detectBeans' in str(x))
assert 'AppUtilKt;->getApplication' in str(seq[at-2]) and seq[at-1][0]=='move-result-object'
keep=[i for i in range(len(seq)) if i not in [at-2,at-1,at]];idx={i:j for j,i in enumerate(keep)}
for i in range(len(seq)-1,-1,-1):
 if i not in idx and i+1 in idx:idx[i]=idx[i+1]
restored=copy.deepcopy([seq[i] for i in keep])
for op,args in restored:
 for j,(kind,value) in enumerate(args):
  if kind==3:args[j]=(kind,idx.get(value,value))
  elif kind=='targets':args[j]=(kind,[idx.get(t,t) for t in value])
fullkey=next(k for k in nm if nm[k] is full)
assert (v[0],v[1],restored)==normal(om[fullkey]),'vendor response handler changed outside the detection hook'
force=next(v for k,v in nm.items() if k[0]=='Lcom/hailiang/launcher/data/bean/response/AppHtmlListBean;' and k[1]=='forceUpdate')
assert force[2]==[('const/4',[(0,0),(1,0)]),('return',[(0,0)])]
print('PASS new vendor classroom routes retained; original update requests retained; installer callbacks neutralized',flush=True)
# Execute actual final DEX for existing manual launch / original warning behavior.
spec=importlib.util.spec_from_file_location('controlled_final_tests',R/'apk-analysis/launcher-controlled-open/test_flows.py');flows=importlib.util.module_from_spec(spec);spec.loader.exec_module(flows)
encoded={(c.get_name(),m.get_name(),m.get_descriptor()):m for d in ds.values() for c in d.get_classes() for m in c.get_methods()}
flow_report=flows.run(ms,encoded)
negative=flows.Machine({**ms,**methods(old5)},{**encoded,**{(c.get_name(),m.get_name(),m.get_descriptor()):m for c in old5.get_classes() for m in c.get_methods()}})
assert not negative.call('Lcom/hljzjx/md3/LocalAppCatalog;','bindIcon',[flows.O(context=True),flows.O(web=False,packageName='installed.app',logoUrl='https://server/icon'),flows.O()]),'old helper negative control'
from test_icons import run as icons
icon_report=icons(ms,encoded,flows)
print('PASS',json.dumps({**flow_report,**icon_report}),flush=True)
apk=APK(str(DEST));native=APK(str(new));prior=APK(str(mod))
assert apk.get_package()==native.get_package()==prior.get_package()=='com.hljzjx.edu.student.launch'
assert apk.get_androidversion_code()=='32015' and apk.get_androidversion_name()=='3.2.1.5'
assert apk.get_min_sdk_version()==apk.get_target_sdk_version()=='29'
assert apk.is_signed_v2() and apk.is_signed_v3()
cert=(apk.get_certificates_der_v3() or apk.get_certificates_der_v2())[0]
assert cert==(prior.get_certificates_der_v3() or prior.get_certificates_der_v2())[0]
assert hashlib.sha256(cert).hexdigest()=='0262266e6908148d5411f0d6f190818d95cdb4f859556b6d5f53ab7109e244ca'
oldxml=copy.deepcopy(prior.get_android_manifest_xml());a='{http://schemas.android.com/apk/res/android}'
oldxml.set(a+'versionCode','32015');oldxml.set(a+'versionName','3.2.1.5')
assert E.tostring(oldxml)==E.tostring(apk.get_android_manifest_xml()),'manifest changed outside versions'
before=copy.deepcopy(APK(str(stock)).get_android_manifest_xml());before.set(a+'versionCode','32015');before.set(a+'versionName','3.2.1.5')
assert E.tostring(before)==E.tostring(native.get_android_manifest_xml()),'unhandled official manifest change'
report={k:v for k,v in meta.items() if k!='resource_overrides'}
report.update({'unchanged_new_vendor_payloads':len(untouched),'exact_mod_resource_payloads':len(resources),'unchanged_native_dex3_methods':len(om)-len(delta),'changed_native_methods':len(delta),'added_native_methods':len(added),'member_references_checked':refs,'dex_method_id_counts':syms.method_counts,'certificate_sha256':hashlib.sha256(cert).hexdigest(),**flow_report,**icon_report})
tested=json.loads((B/'update-tests.json').read_text('utf8'))
assert tested['source_sha256']==hashlib.sha256((B/'src/com/hljzjx/md3/updates/ManualUpdates.java').read_bytes()).hexdigest()
report['updater_java_tests']=tested
(B/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print('PASS package, version, exact manifest migration, same V2/V3 certificate',flush=True)
