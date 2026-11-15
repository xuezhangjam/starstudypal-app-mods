"""Verify the native M3e migration against the actual official 1.0.7 APK."""
from pathlib import Path
import hashlib, json, re, sys, zipfile, xml.etree.ElementTree as E
R=Path(__file__).resolve().parent
ROOT=R.parent
B=R/'notice-m3e-1.0.7'
sys.path[:0]=[str(R/'deps'),str(R)]
from loguru import logger
logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX
from androguard.core.axml import AXMLPrinter
from canonical_notice_methods import methods
from launcher_dex_linkage import DexLinker

official=ROOT/'班级通知学生端1.0.7原版.apk'
native_baseline=ROOT/'班级通知学生端-1.0.6-M3e-系统消息修复-原版包名.apk'
candidate=Path(sys.argv[1]) if len(sys.argv)>1 else B/'notice-107-unsigned.apk'
def signature(name):return name.startswith('META-INF/') and name.upper().endswith(('.MF','.SF','.RSA','.DSA','.EC'))
if len(sys.argv)==1:
    with zipfile.ZipFile(official) as a,zipfile.ZipFile(B/'rebuilt.apk') as b,zipfile.ZipFile(candidate,'w') as out:
        for info in b.infolist():
            if signature(info.filename):continue
            protected=info.filename in ('classes.dex','classes2.dex','classes4.dex') or info.filename.startswith(('assets/','lib/'))
            out.writestr(info,a.read(info.filename) if protected else b.read(info.filename))

base,apk,previous=APK(str(official)),APK(str(candidate)),APK(str(native_baseline))
meta=json.loads((B/'migration-manifest.json').read_text('utf-8'))
assert apk.get_package()==base.get_package()==meta['package']=='com.hailiang.notice.student'
assert apk.get_androidversion_name()==meta['version']=='1.0.7-m3e.1'
assert int(apk.get_androidversion_code())==meta['version_code']==8
assert int(apk.get_androidversion_code())>int(previous.get_androidversion_code())
assert apk.get_min_sdk_version()==base.get_min_sdk_version()=='21'
assert apk.get_target_sdk_version()==base.get_target_sdk_version()=='29'
assert set(apk.get_permissions())==set(base.get_permissions())
assert apk.get_android_resources().get_packages_names()==['com.hailiang.notice.student']
with zipfile.ZipFile(official) as a,zipfile.ZipFile(candidate) as b:
    assert b.testzip() is None
    preserved=[n for n in a.namelist() if n in ('classes.dex','classes2.dex','classes4.dex') or n.startswith(('assets/','lib/'))]
    assert all(a.read(n)==b.read(n) for n in preserved)
assert apk.get_file('classes5.dex')==previous.get_file('classes5.dex')
assert apk.get_file('classes6.dex')==previous.get_file('classes7.dex')
dexes={n:DEX(apk.get_file(n)) for n in apk.get_files() if re.fullmatch(r'classes\d*\.dex',n)}
assert set(dexes)=={'classes.dex',*[f'classes{i}.dex' for i in range(2,7)]}
assert all(len(d.get_methods())<65536 for d in dexes.values())
official3=DEX(base.get_file('classes3.dex'))
om,nm=methods(official3),methods(dexes['classes3.dex'])
assert set(om)<=set(nm),'Official 1.0.7 method removed'
allowed={('L'+p.removesuffix('.smali')+';',s) for p,s in meta['changed_methods']}
added={('L'+p.removesuffix('.smali')+';',s) for p,s in meta['added_methods']}
delta=[k for k in om if om[k]!=nm[k]]
actual={(c,n+d.replace(' ','')) for c,n,d in delta}
assert actual==allowed,(actual-allowed,allowed-actual)
assert {(c,n+d.replace(' ','')) for c,n,d in set(nm)-set(om)}==added
defs=[c for dex in dexes.values() for c in dex.get_classes()]
assert len(defs)==len({c.get_name() for c in defs})
native=[c for name,dex in dexes.items() if name in ('classes5.dex','classes6.dex') for c in dex.get_classes()]
assert all(c.get_name().startswith('Lcom/hailiang/notice/m3e/') for c in native)
changed_classes={c for c,_ in allowed|added}
linker=DexLinker(dexes.values())
refs,errors=linker.check(native+[c for c in defs if c.get_name() in changed_classes])
assert not errors,errors[:25]
assert any(c.get_name().startswith('Lcom/google/gson/') for c in dexes['classes3.dex'].get_classes())
resource_count=0
resources=apk.get_android_resources()
for element in E.parse(B/'official/res/values/public.xml').getroot():
    assert resources.get_res_id_by_key(apk.get_package(),element.get('type'),element.get('name'))==int(element.get('id'),16)
    resource_count+=1
A='{http://schemas.android.com/apk/res/android}'
manifest=apk.get_android_manifest_xml()
assert 'com.hailiang.notice.student.m3e' not in E.tostring(manifest,encoding='unicode')
for name in ('com.hailiang.notice.MainActivity','com.hailiang.notice.detail.NoticeDetailActivity'):
    activity=next(e for e in manifest.iter('activity') if e.get(A+'name')==name)
    assert activity.get(A+'screenOrientation') in ('unspecified','-1') and activity.get(A+'resizeableActivity')=='true'
    cls=next(c for c in dexes['classes3.dex'].get_classes() if c.get_name()=='L'+name.replace('.','/')+';')
    assert 'Lme/jessyan/autosize/internal/CancelAdapt;' in cls.get_interfaces()
def xmlkey(e):return (e.tag,tuple(sorted(e.attrib.items())),(e.text or '').strip(),tuple(xmlkey(c) for c in e))
for name in ('item_notice','fragment_base_list'):
    path='res/layout/'+name+'.xml'
    assert xmlkey(AXMLPrinter(apk.get_file(path)).get_xml_obj())==xmlkey(AXMLPrinter(previous.get_file(path)).get_xml_obj())
# Original 1.0.7's web-domain policy and API/model additions stay bytecode
# equivalent. The native reader itself remains the prior native UI module.
policy=[k for k in om if k[0].startswith('Lcom/hailiang/notice/webview/') or 'White' in k[0] or k[1]=='requestWhiteUrlList' or k[1]=='loadAllowDomains']
assert policy and all(om[k]==nm[k] for k in policy)
report={'apk':str(candidate),'package':apk.get_package(),'version':apk.get_androidversion_name(),'version_code':apk.get_androidversion_code(),
 'official_sha256':hashlib.sha256(official.read_bytes()).hexdigest(),'sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
 'changed_official_methods':len(delta),'added_lifecycle_methods':len(added),'preserved_official_methods':len(om)-len(delta),
 'checked_references':refs,'protected_official_payloads':len(preserved),'checked_official_resource_ids':resource_count,
 'native_ui_and_navigation_dex_identical_to_fixed_106':True,'native_layouts_match_fixed_106':True,
 'preserved_webview_domain_and_api_methods':len(policy),'official_gson_location_preserved':True,
 'dex_method_references':{n:len(d.get_methods()) for n,d in dexes.items()},
 'signed_v2':apk.is_signed_v2(),'signed_v3':apk.is_signed_v3(),'android_device_tested':False}
if apk.is_signed_v2() or apk.is_signed_v3():
    cert=(apk.get_certificates_der_v3() or apk.get_certificates_der_v2())[0]
    before=(previous.get_certificates_der_v3() or previous.get_certificates_der_v2())[0]
    assert cert==before,'Retain the approved local notice signing certificate'
    with zipfile.ZipFile(B/'notice-107-unsigned.apk') as a,zipfile.ZipFile(candidate) as b:
        assert {n:a.read(n) for n in a.namelist() if not signature(n)}=={n:b.read(n) for n in b.namelist() if not signature(n)}
    report['previous_mod_signature_matches']=True
    report['certificate_sha256']=hashlib.sha256(cert).hexdigest()
    report['signing_preserves_verified_payload']=True
filename='signed-verification.json' if apk.is_signed_v2() or apk.is_signed_v3() else 'build-verification.json'
(B/filename).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
