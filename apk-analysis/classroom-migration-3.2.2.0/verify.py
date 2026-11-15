"""Verify the signed migration, vendor preservation, ABI and resource identities."""
from pathlib import Path
import copy, hashlib, json, re, struct, sys, zipfile
from lxml import etree as E
B=Path(__file__).resolve().parent; ROOT=B.parent.parent
sys.path[:0]=[str(ROOT/'apk-analysis/deps'),str(ROOT/'apk-analysis')]
from loguru import logger
logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX
from canonical_notice_methods import methods
from launcher_dex_linkage import DexLinker
from migrate import INPUT_HASHES, NEW, MOD, DEST, A, sem, publics

meta=json.loads((B/'build.json').read_text('utf-8'))
assert hashlib.sha256(DEST.read_bytes()).hexdigest()==meta['sha256']
for p,h in INPUT_HASHES.items(): assert hashlib.sha256(p.read_bytes()).hexdigest()==h
with zipfile.ZipFile(NEW) as src, zipfile.ZipFile(MOD) as mod, zipfile.ZipFile(DEST) as out:
    assert out.testzip() is None
    assert len(out.namelist())==len(set(out.namelist()))
    for i in [1,2,3,5]:
        name='classes'+('' if i==1 else str(i))+'.dex'
        assert src.read(name)==out.read(name),name
    for i in range(6,13):assert mod.read(f'classes{i}.dex')==out.read(f'classes{i}.dex')
    # All vendor assets, native libraries, annotations and auxiliary files survive.
    untouched=[]
    for n in src.namelist():
        if n.startswith(('META-INF/','res/')) or n in ('AndroidManifest.xml','resources.arsc','classes4.dex'):continue
        assert src.read(n)==out.read(n),n
        untouched.append(n)
    original=DEX(src.read('classes4.dex'))
    ds={n:DEX(out.read(n)) for n in out.namelist() if re.fullmatch(r'classes\d*\.dex',n)}
    counts={n:struct.unpack_from('<I',out.read(n),88)[0] for n in ds}
    assert all(x<=65536 for x in counts.values())
print('PASS ZIP, unchanged official payloads and helper DEX6-12',flush=True)
allclasses=[c for d in ds.values() for c in d.get_classes()]
assert len(allclasses)==len({c.get_name() for c in allclasses})
defs={c.get_name():c for c in allclasses}
def method_map(d):return {(k[0],k[1],k[2].replace(' ','')):v for k,v in methods(d).items()}
om=method_map(original); nm={}
for n in ['classes4.dex','classes13.dex']:nm.update(method_map(ds[n]))
merge=json.loads((B/'native-merge.json').read_text('utf-8'))
def key(row):
    name,desc=row['method'].split('(',1)
    return ('L'+row['file'][:-6]+';',name,'('+desc)
expected_changed={key(r) for r in merge if r['action'] in ('ported','adapted')}
expected_added={key(r) for r in merge if r['action']=='added'}
assert not om.keys()-nm.keys()
extra={k for k in nm.keys()-om.keys() if not k[0].startswith('Lcom/hljzjx/classroom/mod/')}
assert extra==expected_added,(extra-expected_added,expected_added-extra)

def normal(value):
    access,regs,seq=value
    keep=[i for i,x in enumerate(seq) if x[0]!='nop']
    mapping={i:j for j,i in enumerate(keep)}
    for i in range(len(seq)-1,-1,-1):
        if i not in mapping and i+1 in mapping:mapping[i]=mapping[i+1]
    result=copy.deepcopy([seq[i] for i in keep])
    for op,args in result:
        for j,(kind,v) in enumerate(args):
            if kind==3:args[j]=(kind,mapping.get(v,v))
            elif kind=='targets':args[j]=(kind,[mapping.get(t,t) for t in v])
    return access,regs,result

delta={k for k in om if normal(om[k])!=normal(nm[k])}
assert delta==expected_changed,{'unexpected':list(delta-expected_changed)[:10],'missing':list(expected_changed-delta)[:10]}
for cls in original.get_classes():
    other=defs[cls.get_name()]
    assert cls.get_access_flags()==other.get_access_flags()
    assert cls.get_superclassname()==other.get_superclassname()
    assert cls.get_interfaces()==other.get_interfaces()
    fields={(f.get_name(),f.get_descriptor(),f.get_access_flags()) for f in cls.get_fields()}
    newer={(f.get_name(),f.get_descriptor(),f.get_access_flags()) for f in other.get_fields()}
    assert fields<=newer
    assert all(f[0].startswith('mod') for f in newer-fields)
print('PASS all original DEX4 methods preserved except the 76 planned hooks; official split classes unchanged',flush=True)
owned=[c for c in allclasses if c.get_name().startswith('Lcom/hljzjx/classroom/mod/')]
native=[defs[c] for c in {k[0] for k in expected_changed|expected_added}]
linker=DexLinker(ds.values());refs=0;errors=[]
for cls in owned+native:
    for method in cls.get_methods():
        for instruction in method.get_instructions():
            for op in instruction.get_operands():
                # Only typed method/field operands, never a string literal that
                # happens to contain an arrow (e.g. a log message or JavaScript).
                if len(op)<3 or int(op[0]) not in (256,258):continue
                owner,target=op[2].split('->',1)
                if int(op[0])==256:
                    name,desc=target.split('(',1);desc='('+desc.replace(' ','');field=False
                else:name,desc=target.split(' ',1);desc=desc.replace(' ','');field=True
                if not linker.resolve(owner,name,desc,field):errors.append((cls.get_name(),method.get_name(),op[2]))
                refs+=1
assert not errors,errors[:50]
print('PASS',refs,'modified-class/helper member references',flush=True)
# Verify critical official 3.2.2.0 behavior remains inside adapted methods.
submit=next(v for k,v in nm.items() if k[0].endswith('/QuestionAskAnswerBaseFragment;') and k[1]=='submit')
assert 'computeSubmitElapsedSeconds' in str(submit) and 'sortedWith' in str(submit)
image=next(v for k,v in nm.items() if k[0].endswith('/QuestionAskHandwriteAnswerView;') and k[1]=='update$lambda$6')
assert 'guardImages' in str(image) and 'loadImageIntoHandwriteView(' in str(image)
assert 'loadImageIntoHandwriteView$default' not in str(image)
assert not any(k[0]=='Lcom/hljzjx/student/classroom/review/MainActivity;' and k[1]=='onStop' for k in nm)
activity=next(v for k,v in nm.items() if k[0]=='Lcom/nice/room/ui/RoomLiveActivity;' and k[1]=='initView')
assert 'setHandwriteEnable' in str(activity) and 'LocalApps;->install' in str(activity)
apk=APK(str(DEST));source=APK(str(NEW));oldmod=APK(str(MOD))
assert apk.get_package()==source.get_package()=='com.hljzjx.edu.student.classroom'
assert apk.get_androidversion_code()==source.get_androidversion_code()=='322000'
assert apk.get_androidversion_name()==source.get_androidversion_name()=='3.2.2.0'
assert apk.get_min_sdk_version()==source.get_min_sdk_version()=='29'
assert apk.get_target_sdk_version()==source.get_target_sdk_version()=='30'
assert apk.is_signed_v2() and apk.is_signed_v3()
cert=(apk.get_certificates_der_v3() or apk.get_certificates_der_v2())[0]
assert cert==(oldmod.get_certificates_der_v3() or oldmod.get_certificates_der_v2())[0]
ar=apk.get_android_resources()
pub=E.fromstring(ar.get_public_resources(apk.get_package()))
outputpub={(x.get('type'),x.get('name')):int(x.get('id'),16) for x in pub.findall('public')}
officialpub=publics('resources-new')
assert officialpub.items()<=outputpub.items()
assert len(outputpub)-len(officialpub)==15
assert ('string','audio_connecting_hint') in outputpub and ('string','report_text') in outputpub
manifest=apk.get_android_manifest_xml()
room=next(x for x in manifest.findall('application/activity') if x.get(A+'name')=='com.nice.room.ui.RoomLiveActivity')
assert room.get(A+'supportsPictureInPicture')=='true' and room.get(A+'resizeableActivity')=='true'
main=next(x for x in manifest.findall('application/activity') if x.get(A+'name')=='com.hljzjx.student.classroom.review.MainActivity')
assert any(x.get(A+'name')=='android.intent.category.LAUNCHER' for x in main.findall('intent-filter/category'))
assert not any(x.get(A+'name')=='com.hailiang.classroom.action.ROUTE' for x in main.findall('intent-filter/action'))
report={**meta,'passed':True,'preserved_official_payloads':len(untouched),
        'unaltered_original_dex4_methods':len(om)-len(delta),'modified_native_methods':len(delta),
        'added_native_bridge_methods':len(expected_added),'new_official_resource_ids_preserved':len(officialpub),
        'new_resources':len(outputpub)-len(officialpub),'helper_dex6_to_12_byte_identical':True,
        'new_dex13_original_library_methods_unchanged':True,'method_ids_per_dex':counts,
        'checked_member_references':refs,'duplicate_classes':False,
        'certificate_sha256':hashlib.sha256(cert).hexdigest(),
        'limits':'Static DEX/resource checks and JVM fixture regressions; no Pixel Tablet or school service integration acceptance.'}
(B/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
