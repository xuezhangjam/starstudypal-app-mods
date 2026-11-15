"""Audit native presentation changes, original business code, platform camera and signatures."""
from pathlib import Path
import ast,copy,hashlib,json,re,sys,zipfile
B=Path(__file__).resolve().parent;ROOT=B.parent.parent
sys.path[:0]=[str(ROOT/'apk-analysis/deps'),str(ROOT/'apk-analysis')]
from loguru import logger
logger.remove()
from androguard.core.apk import APK
from androguard.core.axml import AXMLPrinter
from androguard.core.dex import DEX
from canonical_notice_methods import methods
from launcher_dex_linkage import DexLinker
meta=json.loads((B/'build.json').read_text('utf-8'));source=ROOT/meta['input'];output=ROOT/meta['output']
assert hashlib.sha256(source.read_bytes()).hexdigest()==meta['input_sha256']
policy=ast.parse((B/'build.py').read_text('utf-8'))
roles=next(ast.literal_eval(n.value) for n in policy.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='roles' for t in n.targets))
def signature(n):return n.startswith('META-INF/') and n.upper().endswith(('.MF','.SF','.RSA','.DSA','.EC'))
def tree(node):
    compiler={'platformBuildVersionCode','platformBuildVersionName','{http://schemas.android.com/apk/res/android}compileSdkVersion','{http://schemas.android.com/apk/res/android}compileSdkVersionCodename'}
    return node.tag,tuple(sorted((k,v) for k,v in node.attrib.items() if k not in compiler)),(node.text or '').strip(),tuple(tree(x) for x in node)
A='{http://schemas.android.com/apk/res/android}'
with zipfile.ZipFile(source) as a,zipfile.ZipFile(output) as b:
    assert b.testzip() is None
    before={n for n in a.namelist() if not signature(n)};after={n for n in b.namelist() if not signature(n)}
    assert after-before=={'classes6.dex'} and not before-after
    delta={n for n in before if a.read(n)!=b.read(n)}
    assert delta=={'classes4.dex','classes5.dex','AndroidManifest.xml',*meta['compiled_layouts']},delta
    assert a.read('resources.arsc')==b.read('resources.arsc')
    original_manifest=AXMLPrinter(a.read('AndroidManifest.xml')).get_xml_obj();manifest=AXMLPrinter(b.read('AndroidManifest.xml')).get_xml_obj()
    app=manifest.find('application');added=[x for x in app.findall('activity') if x.get(A+'name')=='com.nice.errorbook.m3e.PhotoSourceActivity']
    assert len(added)==1 and added[0].get(A+'exported')=='false';app.remove(added[0])
    assert tree(original_manifest)==tree(manifest),'Unexpected manifest change'
    layout_report={}
    for path in meta['compiled_layouts']:
        x=AXMLPrinter(a.read(path)).get_xml_obj();y=AXMLPrinter(b.read(path)).get_xml_obj()
        oldnodes=list(x.iter());newnodes=list(y.iter());assert len(oldnodes)==len(newnodes)
        for old,new in zip(oldnodes,newnodes):
            assert old.tag==new.tag
            assert old.get(A+'id')==new.get(A+'id')
        layout_report[path]={'nodes':len(oldnodes),'all_original_ids_and_tags_preserved':True}
    print('PASS ZIP payloads, original resource table, manifest and layout identities',flush=True)
    originals={n:DEX(a.read(n)) for n in ['classes4.dex','classes5.dex']}
    dexes={n:DEX(b.read(n)) for n in b.namelist() if re.fullmatch(r'classes\d*\.dex',n)}
print('Loaded original and final DEX files',flush=True)
P='Lcom/nice/errorbook/m3e/Palette;';SHAPE='Lcom/nice/errorbook/m3e/ShapeBridge;';THEME='Lcom/nice/errorbook/m3e/Theme;'
def regs(args):return [v[1] for v in args if v[0]==0]
def ref(args):return next((v[1] for v in args if isinstance(v[1],str) and '->' in v[1]),None)
def normalize(old,new,key):
    assert old[:2]==new[:2],('register or access changes',key)
    oseq,nseq=old[2],copy.deepcopy(new[2]);i=j=0;normalized=[];mapping={}
    while i<len(oseq):
        op,args=oseq[i];np,nargs=nseq[j];r=ref(args);nr=ref(nargs)
        if np=='invoke-static' and nr and nr.startswith(THEME):
            method=nr.split('->')[1].split('(')[0]
            if method=='begin':assert key[1]=='initView' and i==0 and regs(nargs)==[old[1]-1]
            elif method in {'dialog','dialogWindow'}:assert key[0]=='Lcom/nice/errorbook/dialog/CommonDialog;' and key[1]=='onCreateDialog' and regs(nargs)==[0]
            else:raise AssertionError(('Unexpected UI hook',key,nr))
            mapping[j]=i;j+=1;continue
        if op=='sget-wide' and np=='invoke-static' and nr and nr.startswith(P):
            assert r.startswith('Lcom/nice/errorbook/ui/')
            field=r.split('->')[1].split(' ')[0];assert field in roles
            assert nr==P+'->'+roles[field]+'()J' and not regs(nargs)
            assert nseq[j+1][0]=='move-result-wide' and regs(nseq[j+1][1])==regs(args)
            mapping[j]=mapping[j+1]=i;normalized.append(copy.deepcopy(oseq[i]));i+=1;j+=2;continue
        translated=False
        if op.startswith('invoke-') and np.startswith('invoke-') and r and nr and r!=nr:
            if r.startswith('Landroidx/compose/ui/graphics/ColorKt;->Color('):
                assert nr==r.replace('Landroidx/compose/ui/graphics/ColorKt;->Color',P+'->color') and regs(args)==regs(nargs) and op==np;translated=True
            elif r.startswith('Landroidx/compose/ui/graphics/Color$Companion;->getWhite-') or r.startswith('Landroidx/compose/ui/graphics/Color$Companion;->getBlack-'):
                assert np=='invoke-static' and not regs(nargs) and nr.startswith(P)
                assert nr.split('->')[1] in {'surface()J','container()J','onSurface()J','onPrimary()J','primary()J','paperWhite()J','paperBlack()J'};translated=True
            elif r.startswith('Landroidx/compose/foundation/shape/RoundedCornerShapeKt;->RoundedCornerShape-0680j_4('):
                assert nr==r.replace('Landroidx/compose/foundation/shape/RoundedCornerShapeKt;->RoundedCornerShape-0680j_4',SHAPE+'->rounded') and regs(args)==regs(nargs) and op==np;translated=True
        mapping[j]=i
        normalized.append(copy.deepcopy(oseq[i]) if translated else nseq[j]);i+=1;j+=1
    assert j==len(nseq),(key,j,len(nseq))
    for index,(op,args) in enumerate(normalized):
        for pos,arg in enumerate(args):
            if arg[0]==3:args[pos]=(3,mapping[arg[1]])
            elif arg[0]=='targets':args[pos]=('targets',[mapping[t] for t in arg[1]])
    assert normalized==oseq,('Changes beyond audited presentation hooks',key)
changes=json.loads((B/'method-changes.json').read_text('utf-8'))
expected={(x['dex'],'L'+x['class'].replace('.','/')+';',x['signature'].split()[-1]) for x in changes}
changed=[];untouched=0;added_classes=set()
for name,original in originals.items():
    number=int(name[7]);old,new=methods(original),methods(dexes[name]);assert not old.keys()-new.keys()
    for key in old:
        if old[key]==new[key]:untouched+=1;continue
        changed.append((number,key));assert (number,key[0],key[1]+key[2].replace(' ','')) in expected,key
        if number==4 and key[0]=='Lcom/hailiang/xxb/ai/camera/view/scan/SmartCameraActivity$Companion;':
            assert key[1]=='start' and [op for op,args in new[key][2]]==['invoke-static','return-void']
            assert regs(new[key][2][0][1])==[1,2,3]
            assert 'Lcom/nice/errorbook/m3e/PhotoSources;->open' in ref(new[key][2][0][1])
        else:normalize(old[key],new[key],key)
    extra=new.keys()-old.keys()
    if number==4:assert not extra
    else:assert extra=={(SHAPE,'rounded','(F)Landroidx/compose/foundation/shape/RoundedCornerShape;')}
    added_classes|={c.get_name() for c in dexes[name].get_classes()}-{c.get_name() for c in original.get_classes()}
assert len(changed)==len(changes)==meta['modified_original_methods']
print('PASS audited UI method changes and all remaining original instructions',flush=True)
assert added_classes=={SHAPE}
helper_classes=list(dexes['classes6.dex'].get_classes())
compiler_annotations={'Lcom/android/tools/r8/annotations/LambdaMethod;'}
assert all(c.get_name().startswith('Lcom/nice/errorbook/m3e/') or c.get_name() in compiler_annotations for c in helper_classes)
for c in helper_classes:
    if c.get_name() in compiler_annotations:
        assert c.get_access_flags()&0x2000
        assert {(m.get_name(),m.get_descriptor()) for m in c.get_methods()}=={(n,'()Ljava/lang/String;') for n in ['holder','method','proto']}
        assert all(not m.get_code() for m in c.get_methods())
allclasses=[c for d in dexes.values() for c in d.get_classes()];assert len(allclasses)==len({c.get_name() for c in allclasses})
assert all(len(d.get_methods())<65536 for d in dexes.values())
linker=DexLinker(dexes.values());audited=[c for n in ['classes4.dex','classes5.dex'] for c in dexes[n].get_classes() if c.get_name() in {k[0] for num,k in changed}|{SHAPE}]+helper_classes
references,errors=linker.check(audited);assert not errors,errors[:25]
print('PASS member references:',references,flush=True)
photo=dexes['classes6.dex'].get_class('Lcom/nice/errorbook/m3e/PhotoSourceActivity;')
camera=next(m for m in photo.get_methods() if m.get_name()=='camera');camera_ops='\n'.join(i.get_output() for i in camera.get_instructions())
assert 'android.media.action.IMAGE_CAPTURE' in camera_ops and 'FileProvider;->getUriForFile' in camera_ops and 'output' in camera_ops and 'setClipData' in camera_ops
assert 'SmartCameraActivity;' not in camera_ops
receive=next(m for m in photo.get_methods() if m.get_name()=='onActivityResult');assert any('importUris' in i.get_output() for i in receive.get_instructions())
preview_calls=[(m.get_name(),i.get_output()) for m in photo.get_methods() for i in m.get_instructions() if 'SmartCamera;->previewCaptures$camera_view_release' in i.get_output()]
assert preview_calls
oldapk,apk=APK(str(source)),APK(str(output))
assert apk.get_package()==oldapk.get_package()=='com.nice.errorbook'
assert apk.get_main_activity()==oldapk.get_main_activity()=='com.nice.errorbook.ui.MainActivity'
assert apk.get_androidversion_name()==oldapk.get_androidversion_name()=='3.3.2.0'
assert apk.get_androidversion_code()==oldapk.get_androidversion_code()=='3320'
assert apk.get_min_sdk_version()==oldapk.get_min_sdk_version()=='29' and apk.get_target_sdk_version()==oldapk.get_target_sdk_version()=='30'
assert set(apk.get_permissions())==set(oldapk.get_permissions())
assert apk.is_signed_v2() and apk.is_signed_v3()
cert=(apk.get_certificates_der_v3() or apk.get_certificates_der_v2())[0]
oldcert=(oldapk.get_certificates_der_v3() or oldapk.get_certificates_der_v2() or oldapk.get_certificates_der_v1())[0]
assert cert!=oldcert
test=(B/'policy-test-results.txt').read_text('utf-8');assert test.startswith('PASS 1860 assertions; 256 photo dimension scenarios')
report={**meta,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'preserved_payloads':len(before)-len(delta),'changed_existing_payloads':sorted(delta),'new_payloads':['classes6.dex'],'other_existing_methods_in_dex4_5_identical':untouched,'UI_method_normalization':'only audited color/shape calls and native UI hooks; all remaining original instructions and branches identical','original_three_other_dex_assets_native_libraries_and_resource_table':'byte-identical','new_manifest_component':'one non-exported photo source Activity only','new_theme_bridge_classes':len(added_classes),'new_java_helper_classes':len(helper_classes),'checked_member_references':references,'layout_checks':layout_report,'system_camera_intent_and_full_size_output':'verified in final DEX; no embedded-camera call in camera route','signed_v2':True,'signed_v3':True,'certificate_sha256':hashlib.sha256(cert).hexdigest(),'official_certificate_sha256':hashlib.sha256(oldcert).hexdigest(),'can_overwrite_official_signature':False,'policy_assertions':1860,'photo_sizing_scenarios':256,'android_device_tested':False,'real_camera_gallery_recognition_upload_tested':False}
(B/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
