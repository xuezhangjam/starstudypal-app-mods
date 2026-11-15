"""Port the recovered native M3e UI onto the official 1.0.7 business code."""
from pathlib import Path
import copy, hashlib, json, os, re, shutil, xml.etree.ElementTree as E, zipfile

R=Path(__file__).resolve().parent
ROOT=R.parent
B=R/'notice-m3e-1.0.7'
N=B/'official'
CODE=B/'official-code/smali'
W=B/'work'
OLD=R/'notice-m3e-1.0.6/original-package/decoded'
HOOKS=R/'notice-m3e-1.0.6/system-fix/decoded/smali_classes3'
OLD_APK=ROOT/'班级通知学生端-1.0.6-M3e-系统消息修复-原版包名.apk'
OFFICIAL=ROOT/'班级通知学生端1.0.7原版.apk'
A='{http://schemas.android.com/apk/res/android}'
E.register_namespace('android',A[1:-1])
PAT=re.compile(r'^\.method ([^\n]+)\n.*?^\.end method',re.M|re.S)

def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.107-tmp')
    temp.write_bytes(data if isinstance(data,bytes) else data.encode('utf-8'))
    os.replace(temp,path)

def xmlwrite(path,root):
    E.indent(root,space='    ')
    write(path,E.tostring(root,encoding='utf-8',xml_declaration=True))

def ext(path):
    text=str(path.resolve())
    return '\\\\?\\'+text if os.name=='nt' and not text.startswith('\\\\?\\') else text

def clone(source,target):
    for path in source.rglob('*'):
        dest=target/path.relative_to(source)
        if path.is_dir():dest.mkdir(parents=True,exist_ok=True)
        else:
            dest.parent.mkdir(parents=True,exist_ok=True)
            if not os.path.exists(ext(dest)):os.link(ext(path),ext(dest))

clone(N,W)
clone(CODE,W/'smali_classes3')
(W/'classes3.dex').unlink(missing_ok=True)

public=E.parse(N/'res/values/public.xml').getroot()
current={(e.get('type'),e.get('name')):int(e.get('id'),16) for e in public}
maximum={}
for (kind,_),rid in current.items():maximum[kind]=max(maximum.get(kind,rid),rid)
old_public=E.parse(OLD/'res/values/public.xml').getroot()
for e in old_public:
    k=e.get('type'),e.get('name')
    if k not in current:
        maximum[k[0]]+=1
        current[k]=maximum[k[0]]
        E.SubElement(public,'public',type=k[0],name=k[1],id=f'0x{current[k]:08x}')
xmlwrite(W/'res/values/public.xml',public)
remap={int(e.get('id'),16):current[(e.get('type'),e.get('name'))] for e in old_public}

def old_method(relative,signature):
    text=(HOOKS/relative).read_text('utf-8')
    found=[m for m in PAT.finditer(text) if m[1].strip().endswith(signature)]
    assert len(found)==1,(relative,signature)
    return re.sub(r'0x7f[0-9a-fA-F]{6}\b',lambda m:f'0x{remap.get(int(m[0],16),int(m[0],16)):08x}',found[0][0])

hooks={
 'com/hailiang/notice/MainActivity.smali':['onCreate(Landroid/os/Bundle;)V'],
 'com/hailiang/notice/MainActivity$onBackPressedCallback$1.smali':['handleOnBackPressed()V'],
 'com/hailiang/notice/NoticeAdapter.smali':[
  '<init>(Landroid/content/Context;Ljava/util/List;Lkotlin/jvm/functions/Function1;Lkotlin/jvm/functions/Function1;)V',
  'updateNotices(Ljava/util/List;)V',
  'onBindViewHolder(Lcom/hailiang/notice/NoticeAdapter$ViewHolder;I)V'],
 'com/hailiang/notice/fragment/BaseMegListFragment.smali':['newNoticeEvent(Lcom/hailiang/notice/event/NewNoticeEvent;)V'],
 'com/hailiang/notice/fragment/InformFragment.smali':['onItemClick(Lcom/hailiang/notice/model/NoticeItem;)V'],
 'com/hailiang/notice/ui/BaseActivity.smali':['getResources()Landroid/content/res/Resources;'],
 'com/hailiang/notice/detail/NoticeDetailActivity.smali':['onCreate(Landroid/os/Bundle;)V','onDestroy()V'],
}
additions={
 'com/hailiang/notice/MainActivity.smali':['onSaveInstanceState(Landroid/os/Bundle;)V','onDestroy()V','onConfigurationChanged(Landroid/content/res/Configuration;)V','refreshImmersive()V'],
 'com/hailiang/notice/detail/NoticeDetailActivity.smali':['onConfigurationChanged(Landroid/content/res/Configuration;)V','refreshImmersive()V'],
}
changed=[]
for relative,signatures in hooks.items():
    source=CODE/relative
    text=source.read_text('utf-8')
    for signature in signatures:
        found=[m for m in PAT.finditer(text) if m[1].strip().endswith(signature)]
        assert len(found)==1,(relative,signature)
        m=found[0]
        text=text[:m.start()]+old_method(relative,signature)+text[m.end():]
        changed.append([relative,signature])
    for signature in additions.get(relative,[]):
        assert not any(m[1].strip().endswith(signature) for m in PAT.finditer(text)),signature
        text+='\n'+old_method(relative,signature)+'\n'
    if relative in additions:
        marker='.super Lcom/hailiang/notice/ui/BaseActivity;'
        assert marker in text
        text=text.replace(marker,marker+'\n.implements Lme/jessyan/autosize/internal/CancelAdapt;',1)
    write(W/'smali_classes3'/relative,text)

config=W/'smali_classes3/com/hailiang/notice/BuildConfig.smali'
text=(CODE/'com/hailiang/notice/BuildConfig.smali').read_text('utf-8')
text,count=re.subn(r'(?m)^(\.field public static final VERSION_CODE:I = )0x7$',r'\g<1>0x8',text)
assert count==1
assert '"1.0.7"' in text
write(config,text.replace('"1.0.7"','"1.0.7-m3e.1"'))

manifest=E.parse(N/'AndroidManifest.xml').getroot()
assert manifest.get('package')=='com.hailiang.notice.student'
for activity in manifest.iter('activity'):
    if activity.get(A+'name') in ('com.hailiang.notice.MainActivity','com.hailiang.notice.detail.NoticeDetailActivity'):
        activity.set(A+'screenOrientation','unspecified')
        activity.set(A+'resizeableActivity','true')
        activity.set(A+'configChanges','density|keyboardHidden|orientation|screenLayout|screenSize|smallestScreenSize|uiMode')
xmlwrite(W/'AndroidManifest.xml',manifest)
text=(N/'apktool.yml').read_text('utf-8')
text=re.sub(r'(?m)^  versionCode: 7$','  versionCode: 8',text)
text=text.replace('  versionName: 1.0.7','  versionName: 1.0.7-m3e.1')
write(W/'apktool.yml',text)

for relative in ('layout/item_notice.xml','layout/fragment_base_list.xml','drawable/m3e_notice_card.xml'):
    write(W/'res'/relative,(OLD/'res'/relative).read_bytes())
labels=E.parse(N/'res/values/strings.xml').getroot()
for element in labels:
    if element.tag=='string' and element.get('name') in ('app_name','otter_app_name'):
        element.text='班级通知 M3e'
xmlwrite(W/'res/values/strings.xml',labels)

with zipfile.ZipFile(OLD_APK) as old:
    write(W/'classes5.dex',old.read('classes5.dex'))
    # 1.0.7's main DEX has capacity for all official Gson code. Keep it there
    # and place the helper in classes6 so runtime multidex names stay contiguous.
    write(W/'classes6.dex',old.read('classes7.dex'))

metadata={'official_sha256':hashlib.sha256(OFFICIAL.read_bytes()).hexdigest(),
 'native_baseline_sha256':hashlib.sha256(OLD_APK.read_bytes()).hexdigest(),
 'package':'com.hailiang.notice.student','version':'1.0.7-m3e.1','version_code':8,
 'changed_methods':changed,'added_methods':[[p,s] for p,ss in additions.items() for s in ss],
 'native_ui_dex':'classes5.dex','native_navigation_dex':'classes6.dex',
 'resource_ids_remapped':sum(k!=v for k,v in remap.items()),
 'official_gson_not_relocated':True,'android_device_tested':False}
(B/'migration-manifest.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(metadata,ensure_ascii=False,indent=2))
