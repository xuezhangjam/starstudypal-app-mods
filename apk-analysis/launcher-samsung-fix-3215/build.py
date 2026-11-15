"""Narrow Samsung compatibility patch over the exact user-installed launcher mod."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys,zipfile

B=Path(__file__).resolve().parent
R=B.parent.parent
BASE=R/'apk-analysis/launcher-migration-3.2.1.5'
T=R/'tools/apk-patch'
JAVA=T/'java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe'
ANDROID=R/'tools/android-sdk/android-34-ext12/android.jar'
SOURCE=R/'星学伴mod-3.2.1.5-系统图标-更新仅下载.apk'
DEST=R/'星学伴mod-3.2.1.5-三星登录与提示崩溃修复-v2.apk'
EXPECTED='a37fdffe9ab360fb7df278b6870d445e6ed4e6597ad1c8dbacc8e6158fb8f6a2'
OWNER='Lcom/hljzjx/samsung/'
sys.path.insert(0,str(BASE))
from smali_tools import METHOD,methods

def run(args):
    p=subprocess.run(list(map(str,args)),capture_output=True,encoding='utf8',errors='replace')
    if p.stdout:print(p.stdout[-1800:],flush=True)
    if p.stderr:print(p.stderr[-1800:],flush=True)
    p.check_returncode()

def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.tmp')
    tmp.write_text(text,encoding='utf8');os.replace(tmp,path)

def clone(source,target):
    for p in source.rglob('*'):
        rel=p.relative_to(source)
        if rel.parts[0] in {'build','dist'}:continue
        q=target/rel
        if p.is_dir():q.mkdir(parents=True,exist_ok=True)
        elif not q.exists():q.parent.mkdir(parents=True,exist_ok=True);os.link(p,q)

def replace(text,key,body):
    match=next(m for m in METHOD.finditer(text) if m[1].split()[-1]==key)
    return text[:match.start()]+body+text[match.end():]

def signature(n):return n.startswith('META-INF/') and n.upper().endswith(('.MF','.SF','.RSA','.DSA','.EC'))

def main():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
    with zipfile.ZipFile(SOURCE) as z:
        for i in (3,5):
            with zipfile.ZipFile(BASE/f'classes{i}-patch.apk') as baseline:
                assert baseline.read('classes.dex')==z.read(f'classes{i}.dex')
            clone(BASE/f'work{i}',B/f'work{i}')
    changes=[]
    def edit(file,key,transform):
        root=B/'work3/smali';p=root/file
        # Always transform the untouched baseline, making repeat builds idempotent.
        original=(BASE/'work3/smali'/file).read_text('utf8')
        current=p.read_text('utf8')
        old=methods(original)[key];new=transform(old)
        assert old!=new
        write(p,replace(current,key,new))
        changes.append({'dex':'classes3.dex','file':file,'method':key})
    def prefix(body,code):
        return re.sub(r'(    \.locals \d+\n)',lambda m:m[0]+'\n'+code+'\n',body,count=1)
    edit('com/hljzjx/launch/MyApplication.smali','onCreate()V',lambda s:s.replace(
        '    invoke-super {p0}, Lcom/jchou/commonlibrary/base/BaseApplication;->onCreate()V',
        '    invoke-super {p0}, Lcom/jchou/commonlibrary/base/BaseApplication;->onCreate()V\n\n    invoke-static {p0}, '+OWNER+'PageHints;->init(Landroid/app/Application;)V',1))
    def toast(body):
        assert '.locals 1' in body
        body=body.replace('.locals 1','.locals 2',1)
        return prefix(body,'''    invoke-virtual {p2}, Lcom/hailiang/ui/designsystem/toast/ToastConfig;->getMessage()Ljava/lang/String;
    move-result-object v0
    invoke-virtual {p2}, Lcom/hailiang/ui/designsystem/toast/ToastConfig;->getDuration()I
    move-result v1
    invoke-static {p1, v0, v1}, Lcom/hljzjx/samsung/PageHints;->show(Landroid/content/Context;Ljava/lang/String;I)Z
    move-result v0
    if-eqz v0, :samsung_original_toast
    return-void
    :samsung_original_toast''')
    edit('com/hailiang/ui/designsystem/toast/ToastManager.smali','actualToast(Landroid/content/Context;Lcom/hailiang/ui/designsystem/toast/ToastConfig;)V',toast)
    edit('com/hailiang/ui/designsystem/toast/ToastManager.smali','cancel()V',lambda s:prefix(s,'    invoke-static {}, '+OWNER+'PageHints;->cancel()V'))
    def login(body):
        # The vendor reuses p1 for FragmentManager, popup and finally ImageView.
        # Preserve the original Bundle in a dedicated, otherwise unused local.
        assert '.locals 2' in body and not re.search(r'\bv[2-9]\b',body)
        body=body.replace('.locals 2','.locals 3',1)
        body=prefix(body,'    move-object v2, p1')
        clear='    invoke-virtual {p0}, Lcom/hljzjx/launch/ui/login/CommonLoginActivity;->clearLocalInfo()V'
        assert body.count(clear)==1
        body=body.replace(clear,'''    invoke-static {v2}, Lcom/hljzjx/samsung/LoginRecovery;->shouldClearOnCreate(Landroid/os/Bundle;)Z
    move-result v0
    if-eqz v0, :samsung_preserve_restored_session
'''+clear+'''
    :samsung_preserve_restored_session''')
        assert body.count('    return-void')==1
        return body.replace('    return-void','    invoke-static {p0, v2}, '+OWNER+'LoginRecovery;->resumeSavedLogin(Landroid/app/Activity;Landroid/os/Bundle;)V\n\n    return-void')
    edit('com/hljzjx/launch/ui/login/CommonLoginActivity.smali','onCreate(Landroid/os/Bundle;)V',login)
    edit('com/hljzjx/launch/ui/login/helper/LoginHelper.smali','homeIntent(Landroid/app/Activity;Z)Landroid/content/Intent;',lambda s:s.replace(
        '    if-eqz p2, :cond_0','    invoke-static {p0, p2}, '+OWNER+'LoginRecovery;->finishLoginStack(Landroid/content/Intent;Z)V\n\n    if-eqz p2, :cond_0',1))
    # Cover the native Toast calls used by login/camera/file dialogs and the
    # existing mod helpers as well. Preserve their behavior on other devices.
    for i in (3,5):
        base=BASE/f'work{i}/smali'
        for p in base.rglob('*.smali'):
            original=p.read_text('utf8')
            if 'Landroid/widget/Toast;->' not in original:continue
            dest=B/f'work{i}/smali'/p.relative_to(base)
            text=dest.read_text('utf8')
            patched=text.replace('Landroid/widget/Toast;->makeText(',OWNER+'PageHints;->makeText(')
            for method,target in [('show','showNative'),('cancel','cancelNative')]:
                patched=re.sub(r'invoke-virtual(/range)? (\{[^}]+\}), Landroid/widget/Toast;->'+method+r'\(\)V',
                    lambda m:'invoke-static'+(m[1] or '')+' '+m[2]+', '+OWNER+'PageHints;->'+target+'(Landroid/widget/Toast;)V',patched)
            if patched!=text:
                write(dest,patched)
            for key,old in methods(original).items():
                if methods(patched)[key]!=old:changes.append({'dex':f'classes{i}.dex','file':p.relative_to(base).as_posix(),'method':key})
    # Only compile our helper classes, keeping compile-only API declarations out.
    api=B/'api/com/hailiang/opensdk/LauncherData.java'
    write(api,'package com.hailiang.opensdk; public class LauncherData { public static final LauncherData INSTANCE=null; public String getToken(){return null;} }')
    classes=B/'helper-classes';classes.mkdir(exist_ok=True)
    run([JAVA,'-jar',T/'ecj.jar','-proc:none','-source','8','-target','8','-warn:none','-encoding','UTF-8','-cp',ANDROID,'-d',classes,*sorted((B/'src').rglob('*.java')),api])
    with zipfile.ZipFile(B/'helper.jar','w') as jar:
        for p in (classes/'com/hljzjx/samsung').rglob('*.class'):jar.write(p,p.relative_to(classes).as_posix())
    dex=B/'helper-dex';dex.mkdir(exist_ok=True)
    run([JAVA,'-cp',T/'jadx/lib/jadx-gui-1.5.6-all.jar','com.android.tools.r8.D8','--min-api','29','--lib',ANDROID,'--output',dex,B/'helper.jar'])
    replacements={'classes11.dex':(dex/'classes.dex').read_bytes()}
    for i in (3,5):
        out=B/f'classes{i}-patched.apk'
        run([JAVA,'-jar',T/'apktool.jar','b',B/f'work{i}','-o',out])
        with zipfile.ZipFile(out) as z:replacements[f'classes{i}.dex']=z.read('classes.dex')
    stage=Path(os.environ['LOCALAPPDATA'])/'CodexBuilds/launcher-samsung-3215'
    stage.mkdir(parents=True,exist_ok=True)
    unsigned=stage/'samsung-3215-v2.apk'
    with zipfile.ZipFile(SOURCE) as z,zipfile.ZipFile(unsigned,'w') as w:
        assert 'classes11.dex' not in z.namelist()
        for info in z.infolist():
            if not signature(info.filename):w.writestr(info,replacements.pop(info.filename,z.read(info.filename)))
        for key,value in replacements.items():w.writestr(key,value)
    signed=stage/'signed';signed.mkdir(exist_ok=True)
    result=signed/'samsung-3215-v2-aligned-signed.apk';result.unlink(missing_ok=True)
    run([JAVA,'-jar',T/'uber-apk-signer.jar','-a',unsigned,'-o',signed,'--ks',T/'signing/launcher-mod.jks','--ksAlias','launchermod','--ksPass','android','--ksKeyPass','android'])
    shutil.copyfile(result,DEST)
    changes=list({(x['dex'],x['file'],x['method']):x for x in changes}.values())
    meta={'source':SOURCE.name,'source_sha256':EXPECTED,'output':DEST.name,'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'size':DEST.stat().st_size,'changed_methods':changes,'device_installed':False,'device_runtime_tested':False}
    write(B/'build.json',json.dumps(meta,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in meta.items() if k!='changed_methods'},ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__':main()
