"""3.2.1.5 vendor baseline + narrow 3.2.1.4 mod delta + installed app icons.
No device operations. Hardlink-safe writes; binary resources remain untouched.
"""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys,zipfile
from manifest_version import version
B=Path(__file__).resolve().parent;R=B.parent.parent;T=R/'tools/apk-patch'
JAVA=T/'java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe'
from smali_tools import METHOD,methods,norm
DEST=R/'星学伴mod-3.2.1.5-系统图标-更新仅下载.apk'
P='Lcom/hljzjx/md3/'
def long(p):return Path('\\\\?\\'+str(p.resolve()))
def write(p,s):
 p=long(p);p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.tmp');q.write_text(s,'utf8');os.replace(q,p)
def clone(a,b):
 for p in long(a).rglob('*'):
  rel=p.relative_to(long(a))
  if rel.parts[0] in {'build','dist'}:continue
  q=long(b)/rel
  if p.is_dir():q.mkdir(parents=True,exist_ok=True)
  elif not q.exists():q.parent.mkdir(parents=True,exist_ok=True);os.link(p,q)
def run(args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8',errors='replace');print(p.stdout[-5000:],flush=True)
 if p.stderr:print(p.stderr[-4000:],flush=True)
 p.check_returncode()
def replace(s,key,body):
 m=next(x for x in METHOD.finditer(s) if x[1].split()[-1]==key)
 return s[:m.start()]+body+s[m.end():]
def prefix(s,text):return re.sub(r'(    \.locals \d+\n)',lambda m:m[0]+'\n'+text+'\n',s,count=1)
def synthetic(s):
 mappings={'MainActivity$$ExternalSyntheticLambda19;':'MainActivity$$ExternalSyntheticLambda18;',
 'MainActivity$$ExternalSyntheticLambda20;':'MainActivity$$ExternalSyntheticLambda19;',
 'MainActivity$$ExternalSyntheticLambda13;':'MainActivity$$ExternalSyntheticLambda12;',
 'MainActivity$$ExternalSyntheticLambda16;':'MainActivity$$ExternalSyntheticLambda15;',
 'MainActivity$$ExternalSyntheticLambda17;':'MainActivity$$ExternalSyntheticLambda16;',
 'MainActivity$$ExternalSyntheticLambda18;':'MainActivity$$ExternalSyntheticLambda17;',
 'MainActivity$$ExternalSyntheticLambda15;':'MainActivity$$ExternalSyntheticLambda14;',
 'MainActivity$14;':'MainActivity$15;'}
 return re.sub('|'.join(re.escape(x) for x in mappings),lambda m:mappings[m[0]],s)
RENAMES={'lambda$setListener$8(Landroid/view/View;)V':'lambda$setListener$6(Landroid/view/View;)V',
 'lambda$showOtherApps$14()V':'lambda$showOtherApps$12()V',
 'lambda$showOtherApps$17(Ljava/util/List;Ljava/lang/Runnable;Ljava/lang/Runnable;)V':'lambda$showOtherApps$15(Ljava/util/List;Ljava/lang/Runnable;Ljava/lang/Runnable;)V'}
def merge_method(file,key,old,mod,new):
 target=RENAMES.get(key,key) if file.endswith('/MainActivity.smali') else key
 if target!=key:
  assert norm(synthetic(old.replace(key,target,1)))==norm(new),(key,target)
  return synthetic(mod.replace(key,target,1)),target,'renamed callback'
 if norm(old)==norm(new):return mod,target,'non-conflicting'
 if file.endswith('/MyApplication.smali'):
  assert key=='onCreate()V'
  new=prefix(new,'    invoke-static {p0}, '+P+'SkinController;->init(Landroid/content/Context;)V')
  call='    invoke-super {p0}, Lcom/jchou/commonlibrary/base/BaseApplication;->onCreate()V'
  assert new.count(call)==1
  return new.replace(call,call+'\n    invoke-static {p0}, '+P+'ThemeController;->apply(Landroid/content/Context;)V'),target,'new initialization retained'
 if file.endswith('/ControlManager.smali'):
  assert key=='notifyControlChanged()V'
  needle='    check-cast v5, Ljava/lang/String;';at=new.index(needle)+len(needle)
  assert ':goto_0' in new[:at]
  code='\n    invoke-static {v5}, '+P+'ForceLauncher;->isAllowed(Ljava/lang/String;)Z\n    move-result v7\n    if-nez v7, :goto_0\n'
  return new[:at]+code+new[at:],target,'new package policy retained'
 assert file.endswith('/MainActivity.smali'),(file,key)
 if key=='startApp(Ljava/lang/String;Ljava/lang/String;)V':
  assert 'ClassRoomPackageHelper;' not in new
  return mod,target,'existing warning and unified launch'
 assert norm(synthetic(old))==norm(new),key
 return synthetic(mod),target,'new generated callbacks retained'

def main():
 inputs=json.loads((B/'inputs.json').read_text('utf8'))
 for i in inputs:assert hashlib.sha256((R/i['file']).read_bytes()).hexdigest()==i['sha256']
 stock,mod,new=[R/x['file'] for x in inputs]
 clone(B/'new',B/'work3');root=B/'work3/smali';changes=[]
 plan=json.loads((B/'plan.json').read_text('utf8'));assert not plan['added_classes']
 for x in plan['native']:
  f=x['file'];a,m,n=[(long(B/l/'smali')/f).read_text('utf8') for l in ['old','mod','new']]
  am,mm,nm=methods(a),methods(m),methods(n);out=n
  assert not x['removed']
  for key in x['changed']:
   target=RENAMES.get(key,key) if f.endswith('/MainActivity.smali') else key
   body,target,reason=merge_method(f,key,am[key],mm[key],nm[target]);out=replace(out,target,body)
   changes.append(dict(file=f,old_method=key,method=target,action='changed',merge=reason))
  for key in x['added']:
   assert key not in nm;out+='\n'+mm[key]+'\n';changes.append(dict(file=f,method=key,action='added'))
  if x['outside']:
   # Explicit zero/null field initializers are omitted by the prior assembler.
   defaults=lambda s:re.sub(r'(?m)^(\.field [^\n]+?) = (?:null|false|0x0|0)\s*$',r'\1',s)
   assert norm(defaults(METHOD.sub('',a)))==norm(defaults(METHOD.sub('',m))),f
  if out!=n:write(root/f,out)
 # An installed native shortcut uses its application icon in both skins. Missing
 # packages (including fixed web keys) retain the existing shortcut artwork.
 f='com/hljzjx/launch/ui/main/MainActivity.smali';s=(root/f).read_text('utf8')
 key=next(k for k in methods(s) if k.startswith('setupShortcut('));body=methods(s)[key]
 needle='    iget-object p2, p1, Lcom/hljzjx/launch/databinding/ItemMainShortcutBinding;->ivShortcutIcon:Landroid/widget/ImageView;'
 assert body.count(needle)==1
 injection='''    iget-object v0, p1, Lcom/hljzjx/launch/databinding/ItemMainShortcutBinding;->ivShortcutIcon:Landroid/widget/ImageView;
    invoke-static {p0, p4, v0}, Lcom/hljzjx/md3/SystemAppIcons;->bindInstalled(Landroid/content/Context;Ljava/lang/String;Landroid/widget/ImageView;)Z
'''
 write(root/f,replace(s,key,body.replace(needle,injection+'\n'+needle)))
 # This turn also requests a cancellable, download-only updater.
 from patch_updates import apply as update_patch
 from build_helper import main as build_helper
 updates=update_patch(root,replace,write);build_helper()
 # Free method-id space by relocating the exact vendor observer classes that
 # this official release moved from DEX1 into its nearly full DEX3.
 moved=json.loads((B/'moved-classes.json').read_text('utf8'));relocated=[]
 template=(B/'new/apktool.yml').read_text('utf8')
 write(B/'work9/apktool.yml',template)
 (B/'work9/AndroidManifest.xml').write_bytes((B/'new/AndroidManifest.xml').read_bytes())
 for cls,before,after in moved:
  assert cls.startswith('Lio/reactivex/observers/') and before=='classes.dex' and after=='classes3.dex'
  f=cls[1:-1]+'.smali';s=(long(B/'new/smali')/f).read_text('utf8');write(B/'work9/smali'/f,s)
  (long(root)/f).unlink(missing_ok=True);relocated.append(cls)
 # Preserve the final mod's exact helpers, changing icon binding and removing
 # its now obsolete ClassRoomPackageHelper call instead of restoring old code.
 cache=R/'apk-analysis/launcher-controlled-open'
 cached=False
 if (cache/'classes5-patch.apk').exists():
  with zipfile.ZipFile(mod) as z,zipfile.ZipFile(cache/'classes5-patch.apk') as c:cached=z.read('classes5.dex')==c.read('classes.dex')
 if cached:helper_base=cache/'work5'
 else:
  helper_base=B/'base5'
  if not helper_base.exists():
   with zipfile.ZipFile(mod) as z,zipfile.ZipFile(B/'base5.apk','w') as w:w.writestr('classes.dex',z.read('classes5.dex'));w.writestr('AndroidManifest.xml',z.read('AndroidManifest.xml'))
   run([JAVA,'-jar',T/'apktool.jar','d','-r','-o',helper_base,B/'base5.apk'])
 clone(helper_base,B/'work5')
 f='com/hljzjx/md3/LocalAppCatalog.smali';s=(helper_base/'smali'/f).read_text('utf8');key=next(k for k in methods(s) if k.startswith('bindIcon('))
 body='''.method public static bindIcon(Landroid/content/Context;Lcom/hailiang/launcher/data/bean/response/AppHtmlListBean;Landroid/widget/ImageView;)Z
    .locals 1
    invoke-static {p0, p1, p2}, Lcom/hljzjx/md3/SystemAppIcons;->bindModel(Landroid/content/Context;Lcom/hailiang/launcher/data/bean/response/AppHtmlListBean;Landroid/widget/ImageView;)Z
    move-result v0
    return v0
.end method'''
 write(B/'work5/smali'/f,replace(s,key,body))
 f='com/hljzjx/md3/ForceLauncher.smali';s=(helper_base/'smali'/f).read_text('utf8');key=next(k for k in methods(s) if k.startswith('openTarget('));body=methods(s)[key]
 start=body.index('    if-nez p2, :classroom_enable');end=body.index('    :launch\n',start)
 body=body[:start]+'''    if-nez p2, :launch
    const-string p2, "com.hljzjx.student.classroom.review.MainActivity"

'''+body[end:]
 write(B/'work5/smali'/f,replace(s,key,body));write(B/'work5/smali/com/hljzjx/md3/SystemAppIcons.smali',(B/'SystemAppIcons.smali').read_text('utf8'))
 write(B/'changes.json',json.dumps({'native':changes,'updates':updates,'relocated_native_classes':relocated,'helper_changes':['LocalAppCatalog.bindIcon','ForceLauncher.openTarget'],'added_helper':'SystemAppIcons'},ensure_ascii=False,indent=2))
 replacements={}
 for i in [3,5,9]:
  out=B/f'classes{i}-patch.apk';run([JAVA,'-jar',T/'apktool.jar','b',B/f'work{i}','-o',out])
  with zipfile.ZipFile(out) as z:replacements[f'classes{i}.dex']=z.read('classes.dex')
 def signature(n):return n.startswith('META-INF/') and n.upper().endswith(('.MF','.SF','.RSA','.DSA','.EC'))
 unsigned=B/'launcher-3215-unsigned.apk';overrides=[]
 with zipfile.ZipFile(stock) as o,zipfile.ZipFile(mod) as m,zipfile.ZipFile(new) as n,zipfile.ZipFile(unsigned,'w') as w:
  assert not [k for k in set(o.namelist())-set(m.namelist()) if not k.startswith('res/') and not signature(k)]
  overlay={k:m.read(k) for k in m.namelist() if not signature(k) and k!='AndroidManifest.xml' and not re.fullmatch(r'classes\d*\.dex',k) and (k not in o.namelist() or m.read(k)!=o.read(k))}
  for k in overlay:
   if k in o.namelist():assert o.read(k)==n.read(k),k
  payload={**{k:m.read(k) for k in m.namelist() if k.startswith('res/')},**overlay,**replacements,'classes10.dex':(B/'helper-dex/classes.dex').read_bytes(),'AndroidManifest.xml':version(m.read('AndroidManifest.xml'),32014,32015,'3.2.1.4','3.2.1.5')}
  for k in ['classes6.dex','classes7.dex','classes8.dex']:payload[k]=m.read(k)
  for info in n.infolist():
   if not signature(info.filename) and not info.filename.startswith('res/'):w.writestr(info,payload.pop(info.filename,n.read(info.filename)))
  for k,v in payload.items():w.writestr(m.getinfo(k) if k in m.namelist() else k,v)
  overrides=sorted(overlay)
 stage=Path(os.environ['LOCALAPPDATA'])/'CodexBuilds/launcher-migration-3215';stage.mkdir(parents=True,exist_ok=True);shutil.copyfile(unsigned,stage/unsigned.name)
 signed=stage/'signed';signed.mkdir(exist_ok=True);result=signed/'launcher-3215-aligned-signed.apk';result.unlink(missing_ok=True)
 run([JAVA,'-jar',T/'uber-apk-signer.jar','-a',stage/unsigned.name,'-o',signed,'--ks',T/'signing/launcher-mod.jks','--ksAlias','launchermod','--ksPass','android','--ksKeyPass','android'])
 shutil.copyfile(result,DEST)
 meta={'inputs':inputs,'output':DEST.name,'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'size':DEST.stat().st_size,'native_hooks':len(changes),'relocated_vendor_classes':len(relocated),'resource_overrides':overrides,'android_device_tested':False,'school_server_tested':False}
 write(B/'build.json',json.dumps(meta,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in meta.items() if k not in ['inputs','resource_overrides']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
