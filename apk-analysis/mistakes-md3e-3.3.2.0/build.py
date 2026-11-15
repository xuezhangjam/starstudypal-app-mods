"""Native MD3e presentation and platform photo sources; original package/business retained."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys,zipfile,xml.etree.ElementTree as E
B=Path(__file__).resolve().parent;ROOT=B.parent.parent;T=ROOT/'tools/apk-patch'
JAVA=T/'java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe'
ANDROID=ROOT/'tools/android-sdk/android-34-ext12/android.jar'
SOURCE=ROOT/'错题本学生端3.3.2.0原版.apk'
DEST=ROOT/'错题本学生端-3.3.2.0-M3e原生-系统相机与相册.apk'
EXPECTED='195d1e19c1b9b39c32ca09257eafba0f0c4892c8d9398e58c232a01969da6fbd'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
def run(args):
    p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace')
    if p.stdout:print(p.stdout,flush=True)
    if p.stderr:print(p.stderr,flush=True)
    p.check_returncode();return p
def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.m3e-tmp');tmp.write_text(s,'utf-8');os.replace(tmp,p)
def long(p):
    s=str(p.resolve());return '\\\\?\\'+s if os.name=='nt' and not s.startswith('\\\\?\\') else s
def clone(a,b):
    for p in a.rglob('*'):
        q=b/p.relative_to(a)
        if p.is_dir():q.mkdir(parents=True,exist_ok=True)
        else:
            q.parent.mkdir(parents=True,exist_ok=True)
            if not os.path.exists(long(q)):os.link(long(p),long(q))
resources=B/'resources'
if not resources.exists():run([JAVA,'-jar',T/'apktool.jar','d','-s','-o',resources,SOURCE])
for number,folder in [(4,'code'),(5,'app-code')]:
    code=B/folder
    if not code.exists():
        thin=B/f'classes{number}-input.apk'
        with zipfile.ZipFile(SOURCE) as a,zipfile.ZipFile(thin,'w') as z:
            z.writestr('classes.dex',a.read(f'classes{number}.dex'));z.writestr('AndroidManifest.xml',a.read('AndroidManifest.xml'))
        run([JAVA,'-jar',T/'apktool.jar','d','-r','-o',code,thin])
W4=B/'work4';W5=B/'work5';clone(B/'code',W4);clone(B/'app-code',W5)
PAT=re.compile(r'^\.method ([^\n]+)\n.*?^\.end method',re.M|re.S)
changes=[]
def record(path,old,new,number):
    om={m[1].strip():m[0] for m in PAT.finditer(old)};nm={m[1].strip():m[0] for m in PAT.finditer(new)}
    assert om.keys()<=nm.keys()
    for sig in om:
        if om[sig]!=nm[sig]:changes.append({'dex':number,'class':path[:-6].replace('/','.'),'signature':sig,'before_sha256':hashlib.sha256(om[sig].encode()).hexdigest(),'after_sha256':hashlib.sha256(nm[sig].encode()).hexdigest()})
def patch_method(text,signature,change):
    matches=[m for m in PAT.finditer(text) if m[1].strip().endswith(signature)];assert len(matches)==1,signature
    m=matches[0];return text[:m.start()]+change(m[0])+text[m.end():]
P='Lcom/nice/errorbook/m3e/Palette;'
roles={
 'TitleText':'onSurface','PrimaryText':'onSurface','WaitingTitleText':'onSurface','TextBlack':'onSurface','TabIcon':'onSurface',
 'SubText':'variant','SecondaryText':'variant','PlaceholderText':'variant','WaitingSubText':'variant','RetryText':'variant','TextGray':'variant','LegendTextColor':'variant','DisabledButtonText':'variant',
 'White':'surface','CardBg':'container','BgGray':'container','PanelBg':'surface','TabUnselectedBg':'container','DialogGrayBoxColor':'container','DisabledButtonBg':'high',
 'BorderGray':'outline','BorderColor':'outline','HomeCardYellow':'outline','DialogOutlineBorderColor':'outline',
 'AccentBlue':'primary','SemesterProgressFill':'primary','SemesterProgressTrack':'high','SemesterItemBg':'container',
 'PrimaryYellow':'primaryContainer','PrimaryYellowBg':'container','LightYellow':'primaryContainer','SelectedBg':'primaryContainer','DialogPrimaryButtonColor':'primaryContainer','DialogCloseColor':'variant','TodayPurple':'primary'
}
def white_role(relative,method,ordinal):
    if 'ImagePreviewOverlay' in relative or 'ImagePreviewOverlay' in method:return 'paperWhite'
    if 'WeeklyClearBubbleItem' in relative:return 'paperWhite'
    if 'MainFragmentKt$KnowledgeGraphSection$2' in relative:return 'onSurface' if ordinal==1 else 'paperWhite'
    if method.startswith('KnowledgeMapDetailPageContent('):return 'paperWhite'
    if method.startswith('PhotoUploadSection('):return 'onPrimary'
    if method.startswith('ManageBottomBar('):return 'surface' if ordinal==1 else 'onPrimary'
    if method.startswith(('TextActionButton(','AiLectureButton(')):return 'onPrimary'
    if 'HomeYellowBorderCard' in relative:return 'container'
    return 'surface'
def style(relative,source):
    def method_change(match):
        body=match[0];method=match[1].split()[-1];ordinal=0
        if 'ImagePreviewOverlay' in relative or 'ImagePreviewOverlay' in method or any(x in relative for x in ['KnowledgeGraphLegendKt','KnowledgeMapGraphComposeKt']) or method.startswith('KnowledgeMapDetailPageContent('):return body
        # Timeouts, IDs, counters and model code are never candidates: reads must
        # be named color fields on the audited UI palette owners.
        def field(m):
            register,owner,name=m.groups()
            if name not in roles or not any(s in owner for s in ['Colors;','DialogKt;','PickerDialogKt;','FilterButtonKt;','DropdownKt;','YellowBorderCardKt;','SemesterMistakeCardKt;','KnowledgeGraphLegendKt;']):return m[0]
            return '    invoke-static {}, '+P+'->'+roles[name]+'()J\n\n    move-result-wide '+register
        body=re.sub(r'    sget-wide ([vp]\d+), (Lcom/nice/errorbook/ui/[^;]+;)->(\w+):J',field,body)
        if 'MainFragmentKt$KnowledgeGraphSection$2' not in relative:
            body=body.replace('Landroidx/compose/ui/graphics/ColorKt;->Color(I)J',P+'->color(I)J').replace('Landroidx/compose/ui/graphics/ColorKt;->Color(J)J',P+'->color(J)J')
        def white(m):
            nonlocal ordinal
            ordinal+=1;return '    invoke-static {}, '+P+'->'+white_role(relative,method,ordinal)+'()J'
        body=re.sub(r'    invoke-virtual(?:/range)? \{[^}]+\}, Landroidx/compose/ui/graphics/Color\$Companion;->getWhite-0d7_KjU\(\)J',white,body)
        black='primary' if method.startswith('PhotoUploadSection(') else 'paperBlack' if any(x in relative for x in ['MainFragmentKt$KnowledgeGraphSection$2','WeeklyClearBubbleItem']) else 'onSurface'
        body=re.sub(r'    invoke-virtual(?:/range)? \{[^}]+\}, Landroidx/compose/ui/graphics/Color\$Companion;->getBlack-0d7_KjU\(\)J','    invoke-static {}, '+P+'->'+black+'()J',body)
        body=body.replace('Landroidx/compose/foundation/shape/RoundedCornerShapeKt;->RoundedCornerShape-0680j_4(F)Landroidx/compose/foundation/shape/RoundedCornerShape;','Lcom/nice/errorbook/m3e/ShapeBridge;->rounded(F)Landroidx/compose/foundation/shape/RoundedCornerShape;')
        return body
    return PAT.sub(method_change,source)
appbase=B/'app-code/smali'
for file in (appbase/'com/nice/errorbook/ui').rglob('*.smali'):
    relative=file.relative_to(appbase).as_posix();old=file.read_text('utf-8');new=style(relative,old)
    if relative in ['com/nice/errorbook/ui/MainActivity.smali','com/nice/errorbook/ui/record/RecordErrorActivity.smali','com/nice/errorbook/ui/work/DoWorkActivity.smali','com/nice/errorbook/ui/work/push/PushQuestionActivity.smali']:
        def hook(body):
            m=re.search(r'    \.locals \d+\n',body);assert m
            body=body[:m.end()]+'\n    invoke-static {p0}, Lcom/nice/errorbook/m3e/Theme;->begin(Landroid/app/Activity;)V\n'+body[m.end():]
            # Kotlin reuses p0 in RecordErrorActivity.initView. The entry call
            # posts native styling itself; never pass a repurposed p0 at return.
            return body
        new=patch_method(new,'initView()V',hook)
    destination=W5/'smali'/relative
    if destination.read_text('utf-8')!=new:write(destination,new)
    if new!=old:record(relative,old,new,5)
write(W5/'smali/com/nice/errorbook/m3e/ShapeBridge.smali','''.class public final Lcom/nice/errorbook/m3e/ShapeBridge;
.super Ljava/lang/Object;
.method public static rounded(F)Landroidx/compose/foundation/shape/RoundedCornerShape;
    .locals 0
    invoke-static {p0}, Lcom/nice/errorbook/m3e/Palette;->corner(F)F
    move-result p0
    invoke-static {p0}, Landroidx/compose/foundation/shape/RoundedCornerShapeKt;->RoundedCornerShape-0680j_4(F)Landroidx/compose/foundation/shape/RoundedCornerShape;
    move-result-object p0
    return-object p0
.end method
''')
relative='com/hailiang/xxb/ai/camera/view/scan/SmartCameraActivity$Companion.smali'
old=(B/'code/smali'/relative).read_text('utf-8')
sig='start(Landroid/content/Context;Lcom/hailiang/xxb/ai/camera/view/data/SmartCameraConfig;Ljava/util/List;)V'
new=patch_method(old,sig,lambda body:body.split('\n',1)[0]+'''\n    .locals 0
    invoke-static {p1, p2, p3}, Lcom/nice/errorbook/m3e/PhotoSources;->open(Landroid/content/Context;Lcom/hailiang/xxb/ai/camera/view/data/SmartCameraConfig;Ljava/util/List;)V
    return-void
.end method''')
write(W4/'smali'/relative,new);record(relative,old,new,4)
relative='com/nice/errorbook/dialog/CommonDialog.smali';old=(B/'code/smali'/relative).read_text('utf-8')
def dialog(body):
    needle='    invoke-direct {p0, v0}, Lcom/nice/errorbook/dialog/CommonDialog;->setupContent(Landroid/view/View;)V';assert needle in body
    body=body.replace(needle,needle+'\n\n    invoke-static {v0}, Lcom/nice/errorbook/m3e/Theme;->dialog(Landroid/view/View;)V')
    assert body.count('    return-object v0')==1
    return body.replace('    return-object v0','    invoke-static {v0}, Lcom/nice/errorbook/m3e/Theme;->dialogWindow(Landroid/app/Dialog;)V\n\n    return-object v0')
new=patch_method(old,'onCreateDialog(Landroid/os/Bundle;)Landroid/app/Dialog;',dialog)
write(W4/'smali'/relative,new);record(relative,old,new,4)
write(B/'method-changes.json',json.dumps(changes,ensure_ascii=False,indent=2));print('Modified UI methods:',len(changes),flush=True)

# No resource IDs are added or repurposed. Only three compiled layouts and the
# manifest are taken from the resource build; the original table is preserved.
stage=Path(os.environ['LOCALAPPDATA'])/'CodexBuilds/errorbook-md3e-3320';stage.mkdir(parents=True,exist_ok=True)
work=stage/'resources';work.mkdir(exist_ok=True);shutil.copytree(resources/'res',work/'res',dirs_exist_ok=True)
for name in ['AndroidManifest.xml','apktool.yml']:shutil.copyfile(resources/name,work/name)
A='{http://schemas.android.com/apk/res/android}';APP='{http://schemas.android.com/apk/res-auto}'
E.register_namespace('android',A[1:-1]);E.register_namespace('app',APP[1:-1])
manifest=E.parse(work/'AndroidManifest.xml');root=manifest.getroot();assert root.get('package')=='com.nice.errorbook'
app=root.find('application');assert not any(e.get(A+'name')=='com.nice.errorbook.m3e.PhotoSourceActivity' for e in app.findall('activity'))
E.SubElement(app,'activity',{A+'name':'com.nice.errorbook.m3e.PhotoSourceActivity',A+'exported':'false',A+'screenOrientation':'landscape',A+'configChanges':'keyboardHidden|orientation|screenLayout|screenSize|smallestScreenSize|uiMode',A+'theme':'@android:style/Theme.Material.Light.NoActionBar'})
E.indent(manifest);manifest.write(work/'AndroidManifest.xml',encoding='utf-8',xml_declaration=True)
layouts=['activity_main.xml','item_subject_tab.xml','dialog_common.xml'];changed_resources=[]
for name in layouts:
    p=work/'res/layout'/name;tree=E.parse(p);r=tree.getroot()
    if name=='activity_main.xml':
        r.set(A+'background','#fffffbfe')
        for x in r.iter():
            if x.get(A+'id') in {'@id/tv_name','@id/tv_empty','@id/tv_version'}:x.set(A+'textColor','#ff1d1b20')
    elif name=='item_subject_tab.xml':
        r.set(A+'minWidth','88.0dp')
        image=next(x for x in r.iter() if x.get(A+'id')=='@id/iv_tab_selected')
        image.set(A+'layout_width','0.0dp');image.set(A+'layout_height','48.0dp');image.set(APP+'layout_constraintStart_toStartOf','parent');image.set(APP+'layout_constraintEnd_toEndOf','parent')
        text=next(x for x in r.iter() if x.get(A+'id')=='@id/tv_tab_name')
        for k,v in {'textColor':'#ff49454f','textSize':'18.0sp','gravity':'center','layout_height':'48.0dp','layout_marginTop':'0.0dp','layout_marginStart':'0.0dp','paddingStart':'16.0dp','paddingEnd':'16.0dp'}.items():text.set(A+k,v)
    else:
        r.set(APP+'cornerRadius','32.0dp')
        for x in r.iter():
            if x.get(A+'id') in {'@id/dialog_cancel','@id/dialog_confirm'}:x.set(A+'layout_height','48.0dp')
    E.indent(tree);tree.write(p,encoding='utf-8',xml_declaration=True);changed_resources.append('res/layout/'+name)
resource_apk=stage/'resources.apk';run([JAVA,'-jar',T/'apktool.jar','b',work,'-o',resource_apk])
# The official table points at shortened ZIP paths. Resolve each unchanged ID
# in both tables instead of assuming apktool's readable path exists upstream.
sys.path.insert(0,str(ROOT/'apk-analysis/deps'))
from loguru import logger
logger.remove()
from androguard.core.apk import APK
original_table=APK(str(SOURCE)).get_android_resources()
rebuilt_table=APK(str(resource_apk)).get_android_resources()
public=E.parse(resources/'res/values/public.xml').getroot()
resource_map={}
for name in layouts:
    rid=int(next(x.get('id') for x in public if x.get('type')=='layout' and x.get('name')==Path(name).stem),16)
    old={c.get_qualifier():v for c,v in original_table.get_resolved_res_configs(rid)}
    new={c.get_qualifier():v for c,v in rebuilt_table.get_resolved_res_configs(rid)}
    assert old and old.keys()==new.keys(),(name,old,new)
    resource_map.update({path:new[qualifier] for qualifier,path in old.items()})
assert len(resource_map)==len(layouts),resource_map
changed_resources=list(resource_map)

# API-only declarations are generated separately and never included in helper DEX.
apis=json.loads((B/'compile-api-sources.json').read_text('utf-8'))
api=B/'compile-api'
for name,source in apis.items():write(api/name,source)
classes=B/'classes';classes.mkdir(exist_ok=True)
run([JAVA,'-jar',T/'ecj.jar','-proc:none','-source','8','-target','8','-encoding','UTF-8','-warn:none','-cp',ANDROID,'-d',classes,*list((B/'src').rglob('*.java')),*list(api.rglob('*.java'))])
jar=B/'m3e.jar';lib=B/'compile-api.jar'
with zipfile.ZipFile(jar,'w') as out,zipfile.ZipFile(lib,'w') as stubs:
    for p in classes.rglob('*.class'):
        name=p.relative_to(classes).as_posix();(out if name.startswith('com/nice/errorbook/m3e/') else stubs).write(p,name)
helper=B/'helper-dex';helper.mkdir(exist_ok=True)
run([JAVA,'-cp',T/'jadx/lib/jadx-gui-1.5.6-all.jar','com.android.tools.r8.D8','--min-api','29','--lib',JAVA.parent.parent,'--lib',ANDROID,'--lib',lib,'--output',helper,jar])
rebuilt={}
for number,folder in [(4,W4),(5,W5)]:
    p=B/f'classes{number}-patch.apk';run([JAVA,'-jar',T/'apktool.jar','b',folder,'-o',p])
    with zipfile.ZipFile(p) as z:rebuilt[f'classes{number}.dex']=z.read('classes.dex')
def signature(n):return n.startswith('META-INF/') and n.upper().endswith(('.MF','.SF','.RSA','.DSA','.EC'))
unsigned=B/'errorbook-m3e-unsigned.apk'
with zipfile.ZipFile(SOURCE) as a,zipfile.ZipFile(resource_apk) as r,zipfile.ZipFile(unsigned,'w') as out:
    assert 'classes6.dex' not in a.namelist()
    for info in a.infolist():
        n=info.filename
        if signature(n):continue
        payload=rebuilt[n] if n in rebuilt else r.read(resource_map[n]) if n in resource_map else r.read(n) if n=='AndroidManifest.xml' else a.read(n)
        out.writestr(info,payload)
    out.writestr('classes6.dex',(helper/'classes.dex').read_bytes(),compress_type=zipfile.ZIP_STORED)
key=T/'signing/errorbook-md3e-mod.jks'
if not key.exists():run([JAVA.parent/'keytool.exe','-genkeypair','-keystore',key,'-storetype','PKCS12','-alias','errorbookmod','-storepass','android','-keypass','android','-keyalg','RSA','-keysize','2048','-validity','10000','-dname','CN=Errorbook M3e Mod, OU=Personal Development, O=Local Mod, C=CN'])
signinput=stage/unsigned.name;shutil.copyfile(unsigned,signinput);signed=stage/'signed';signed.mkdir(exist_ok=True)
result=signed/'errorbook-m3e-aligned-signed.apk';result.unlink(missing_ok=True)
run([JAVA,'-jar',T/'uber-apk-signer.jar','-a',signinput,'-o',signed,'--ks',key,'--ksAlias','errorbookmod','--ksPass','android','--ksKeyPass','android'])
assert result.is_file();shutil.copyfile(result,DEST)
report={'input':SOURCE.name,'input_sha256':EXPECTED,'output':DEST.name,'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'size':DEST.stat().st_size,'package':'com.nice.errorbook','modified_existing_dex':['classes4.dex','classes5.dex'],'new_dex':'classes6.dex','compiled_layouts':changed_resources,'resource_table':'original byte-identical','modified_original_methods':len(changes),'camera':'platform ACTION_IMAGE_CAPTURE with full-resolution FileProvider output','gallery':'system OPEN_DOCUMENT image/* multi-select with GET_CONTENT fallback, original per-entry quota retained','photo_processing':'original SDK preview, manual crop, enhancement, upload, and SmartCamera callback','native_ui':'native Views and existing Compose widgets, semantic dynamic colors and expressive rounded shapes','android_device_tested':False}
report['layout_path_map']=resource_map
write(B/'build.json',json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
