"""Remove local document-detection capture gates; retain server/business code."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,zipfile
B=Path(__file__).resolve().parent;ROOT=B.parent.parent;T=ROOT/'tools/apk-patch'
JAVA=T/'java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe'
ANDROID=ROOT/'tools/android-sdk/android-34-ext12/android.jar'
SOURCE=ROOT/'错题本学生端-3.3.2.0-M3e原生-系统相机与相册.apk'
DEST=ROOT/'错题本学生端-3.3.2.0-M3e-取消拍照作业判定.apk'
EXPECTED='036dfe73a74df1e306c106d717caf6b4a96ca5831186b68bfdf8b7dddd7bfd2b'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
def run(args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace')
 if p.stdout:print(p.stdout,flush=True)
 if p.stderr:print(p.stderr,flush=True)
 p.check_returncode()
def write(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.tmp');tmp.write_text(s,'utf-8');os.replace(tmp,p)
def long(p):return '\\\\?\\'+str(p.resolve()) if os.name=='nt' else str(p)
original=ROOT/'apk-analysis/mistakes-md3e-3.3.2.0/work4';work=B/'work4'
if not original.exists():
 original=B/'base-code'
 if not original.exists():
  thin=B/'classes4-input.apk'
  with zipfile.ZipFile(SOURCE) as a,zipfile.ZipFile(thin,'w') as z:
   z.writestr('classes.dex',a.read('classes4.dex'));z.writestr('AndroidManifest.xml',a.read('AndroidManifest.xml'))
  run([JAVA,'-jar',T/'apktool.jar','d','-r','-o',original,thin])
for p in original.rglob('*'):
 if p.relative_to(original).parts[0] in {'build','dist'}:continue
 q=work/p.relative_to(original)
 if p.is_dir():q.mkdir(parents=True,exist_ok=True)
 elif not os.path.exists(long(q)):
  q.parent.mkdir(parents=True,exist_ok=True);os.link(long(p),long(q))
prefix='com/hailiang/xxb/ai/camera/view/';F='Lcom/nice/errorbook/m3e/CameraCapturePolicy;'
changes=[]
def change(file,old,new):
 assert old!=new,file;write(work/'smali'/file,new)
 pat=re.compile(r'^\.method ([^\n]+)\n.*?^\.end method',re.M|re.S)
 a={m[1].strip():m[0] for m in pat.finditer(old)};b={m[1].strip():m[0] for m in pat.finditer(new)};assert a.keys()==b.keys()
 for sig in a:
  if a[sig]!=b[sig]:changes.append({'class':'L'+file[:-6]+';','signature':sig,'before_sha256':hashlib.sha256(a[sig].encode()).hexdigest(),'after_sha256':hashlib.sha256(b[sig].encode()).hexdigest()})
def method(s,signature,fn):
 pat=re.compile(r'^\.method [^\n]*'+re.escape(signature)+r'\n.*?^\.end method',re.M|re.S)
 matches=list(pat.finditer(s));assert len(matches)==1,signature
 m=matches[0];return s[:m.start()]+fn(m[0])+s[m.end():]

file=prefix+'scan/SmartCameraActivity.smali';old=(original/'smali'/file).read_text('utf-8')
def capture(body):
 start=body.index('    .line 189\n');end=body.index('    .line 195\n')
 return body[:start]+'    const/4 v0, 0x0\n\n'+body[end:]
new=method(old,'capture(Lcom/hailiang/xxb/ai/camera/view/data/SmartCameraConfig;)V',capture);change(file,old,new)

file=prefix+'scan/SmartCameraViewModel$saveImage$2.smali';old=(original/'smali'/file).read_text('utf-8')
def save(body):
 start=body.index('    .line 133\n');end=body.index('    :goto_0\n',start)+len('    :goto_0\n')
 body=body[:start]+'    :cond_3\n    const/4 v6, 0x0\n\n    invoke-static {v2}, '+F+'->full(Landroid/graphics/Bitmap;)Lcom/hailiang/xxb/ai/camera/core/scan/EdgeArea;\n\n    move-result-object v7\n\n'+body[end:]
 start=body.index('    .line 159\n');end=body.index('    .line 160\n',start)
 return body[:start]+'    :cond_7\n    move-object v6, v7\n\n'+body[end:]
new=method(old,'invokeSuspend(Ljava/lang/Object;)Ljava/lang/Object;',save);change(file,old,new)

file=prefix+'SmartCameraPreview.smali';old=(original/'smali'/file).read_text('utf-8')
new=method(old,'updateEdgeArea(Lcom/hailiang/xxb/ai/camera/core/scan/EdgeArea;Z)V',lambda body:body.split('\n',1)[0]+'\n    .locals 0\n    invoke-static {p0}, '+F+'->status(Lcom/hailiang/xxb/ai/camera/view/SmartCameraPreview;)V\n    return-void\n.end method');change(file,old,new)
assert len(changes)==3
write(B/'method-changes.json',json.dumps(changes,ensure_ascii=False,indent=2))
api={
 'com/hailiang/xxb/ai/camera/core/scan/EdgeArea.java':'package com.hailiang.xxb.ai.camera.core.scan;import android.graphics.PointF;import java.util.List;public class EdgeArea{public EdgeArea(int w,int h,List<PointF> points){}}',
 'com/hailiang/xxb/ai/camera/view/SmartCameraPreview.java':'package com.hailiang.xxb.ai.camera.view;import android.widget.TextView;public class SmartCameraPreview{public TextView getStatusTv(){return null;}public void clearPoints(){}}',
 'com/nice/errorbook/m3e/Palette.java':'package com.nice.errorbook.m3e;public class Palette{public static final int ON_CONTAINER=6,PRIMARY_CONTAINER=5;public static int argb(int role){return 0;}}'
}
write(B/'compile-api-sources.json',json.dumps(api,indent=2))
for name,source in api.items():write(B/'compile-api'/name,source)
classes=B/'classes';classes.mkdir(exist_ok=True)
run([JAVA,'-jar',T/'ecj.jar','-proc:none','-source','8','-target','8','-encoding','UTF-8','-warn:none','-cp',ANDROID,'-d',classes,*list((B/'src').rglob('*.java')),*list((B/'compile-api').rglob('*.java'))])
jar=B/'camera-policy.jar';lib=B/'compile-api.jar'
with zipfile.ZipFile(jar,'w') as a,zipfile.ZipFile(lib,'w') as s:
 for p in classes.rglob('*.class'):
  name=p.relative_to(classes).as_posix();(a if name=='com/nice/errorbook/m3e/CameraCapturePolicy.class' else s).write(p,name)
helper=B/'helper-dex';helper.mkdir(exist_ok=True)
run([JAVA,'-cp',T/'jadx/lib/jadx-gui-1.5.6-all.jar','com.android.tools.r8.D8','--min-api','29','--lib',JAVA.parent.parent,'--lib',ANDROID,'--lib',lib,'--output',helper,jar])
patched=B/'classes4-patch.apk';run([JAVA,'-jar',T/'apktool.jar','b',work,'-o',patched])
with zipfile.ZipFile(patched) as z:dex=z.read('classes.dex')
def signature(n):return n.startswith('META-INF/') and n.upper().endswith(('.MF','.SF','.RSA','.DSA','.EC'))
unsigned=B/'free-camera-unsigned.apk'
with zipfile.ZipFile(SOURCE) as a,zipfile.ZipFile(unsigned,'w') as out:
 assert 'classes7.dex' not in a.namelist()
 for info in a.infolist():
  if signature(info.filename):continue
  out.writestr(info,dex if info.filename=='classes4.dex' else a.read(info.filename))
 out.writestr('classes7.dex',(helper/'classes.dex').read_bytes(),compress_type=zipfile.ZIP_STORED)
stage=Path(os.environ['LOCALAPPDATA'])/'CodexBuilds/errorbook-free-camera';stage.mkdir(parents=True,exist_ok=True)
shutil.copyfile(unsigned,stage/unsigned.name);signed=stage/'signed';signed.mkdir(exist_ok=True)
result=signed/'free-camera-aligned-signed.apk';result.unlink(missing_ok=True)
run([JAVA,'-jar',T/'uber-apk-signer.jar','-a',stage/unsigned.name,'-o',signed,'--ks',T/'signing/errorbook-md3e-mod.jks','--ksAlias','errorbookmod','--ksPass','android','--ksKeyPass','android'])
shutil.copyfile(result,DEST)
report={'input':SOURCE.name,'input_sha256':EXPECTED,'output':DEST.name,'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'size':DEST.stat().st_size,'modified_existing_dex':['classes4.dex'],'new_dex':'classes7.dex','modified_original_methods':3,'package':'com.nice.errorbook','camera_capture':'no local homework/edge detection required; original full-frame image goes to preview/manual crop and original upload flow','server_and_app_business_dex':'unchanged','android_device_tested':False}
write(B/'build.json',json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
