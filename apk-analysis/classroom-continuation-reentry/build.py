"""Build the classroom continuation re-entry patch."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,zipfile
B=Path(__file__).resolve().parent;R=B.parent.parent;T=R/'tools/apk-patch'
JAVA=T/'java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe'
ANDROID=R/'tools/android-sdk/android-34-ext12/android.jar'
SOURCE=R/'学生端课堂-3.2.2.0-结束后图片上传-文档同步偏移修复.apk'
EXPECTED='d91ba79c5469d511485ca2cd3cd258751e314ab6e32ca7dd67ae89e553f9e2ba'
DEST=R/'学生端课堂-3.2.2.0-重进继续作答修复.apk'
PAT=re.compile(r'^\.method ([^\n]+)\n.*?^\.end method',re.M|re.S)
def long(p):return Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p
def write(p,s):
 p=long(p);p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.tmp');q.write_text(s,'utf8');os.replace(q,p)
def run(args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8',errors='replace')
 if p.stdout:print(p.stdout[-1800:],flush=True)
 if p.stderr:print(p.stderr[-2200:],flush=True)
 p.check_returncode()
def clone(a,b):
 for p in long(a).rglob('*'):
  f=p.relative_to(long(a))
  if f.parts[0] in ['build','dist']:continue
  q=long(b)/f
  if p.is_dir():q.mkdir(parents=True,exist_ok=True)
  elif not q.exists():q.parent.mkdir(parents=True,exist_ok=True);os.link(p,q)
def main():
 assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
 cache=R/'apk-analysis/classroom-discussion-document-fix'
 with zipfile.ZipFile(SOURCE) as a,zipfile.ZipFile(cache/'classes4-patch.apk') as c:
  assert a.read('classes4.dex')==c.read('classes.dex')
  base4=cache/'work4'
  base10=B/'base10'
  if not base10.exists():
   with zipfile.ZipFile(B/'base10.apk','w') as z:
    z.writestr('classes.dex',a.read('classes10.dex'))
    z.writestr('AndroidManifest.xml',a.read('AndroidManifest.xml'))
   run([JAVA,'-jar',T/'apktool.jar','d','-r','-o',base10,B/'base10.apk'])
 clone(base4,B/'work4')
 clone(base10,B/'work10')
 from patch_native import patch
 from make_api import generate
 patch(base4,base10)
 generate()
 classes=B/'classes';classes.mkdir(exist_ok=True)
 run([JAVA,'-jar',T/'ecj.jar','-proc:none','-source','8','-target','8','-encoding','UTF-8','-warn:none','-cp',ANDROID,'-d',classes,*list((B/'src').rglob('*.java')),*list((B/'compile-api').rglob('*.java'))])
 jar=B/'repairs.jar';api=B/'compile-api.jar'
 with zipfile.ZipFile(jar,'w') as z,zipfile.ZipFile(api,'w') as lib:
  for p in classes.rglob('*.class'):
   name=p.relative_to(classes).as_posix();(z if name.startswith('com/hljzjx/classroom/reentry/') else lib).write(p,name)
 helper=B/'helper16';helper.mkdir(exist_ok=True)
 run([JAVA,'-cp',T/'jadx/lib/jadx-gui-1.5.6-all.jar','com.android.tools.r8.D8','--min-api','29','--lib',JAVA.parent.parent,'--lib',ANDROID,'--lib',api,'--output',helper,jar])
 replacements={}
 for dex in (4,10):
  patched=B/f'classes{dex}-patch.apk'
  run([JAVA,'-jar',T/'apktool.jar','b',B/f'work{dex}','-o',patched])
  with zipfile.ZipFile(patched) as c:replacements[f'classes{dex}.dex']=c.read('classes.dex')
 def signature(k):return k.startswith('META-INF/') and k.upper().endswith(('.MF','.SF','.RSA','.DSA','.EC'))
 unsigned=B/'repairs-unsigned.apk'
 with zipfile.ZipFile(SOURCE) as a,zipfile.ZipFile(unsigned,'w') as z:
  assert 'classes16.dex' not in a.namelist()
  for info in a.infolist():
   if not signature(info.filename):z.writestr(info,replacements.get(info.filename,a.read(info.filename)))
  z.writestr('classes16.dex',(helper/'classes.dex').read_bytes())
 stage=Path(os.environ['LOCALAPPDATA'])/'CodexBuilds/classroom-continuation-reentry';stage.mkdir(parents=True,exist_ok=True);shutil.copyfile(unsigned,stage/unsigned.name)
 signed=stage/'signed';signed.mkdir(exist_ok=True);result=signed/'repairs-aligned-signed.apk';result.unlink(missing_ok=True)
 run([JAVA,'-jar',T/'uber-apk-signer.jar','-a',stage/unsigned.name,'-o',signed,'--ks',T/'signing/classroom-mod.jks','--ksAlias','classroommod','--ksPass','android','--ksKeyPass','android'])
 shutil.copyfile(result,DEST)
 meta={'input':SOURCE.name,'input_sha256':EXPECTED,'output':DEST.name,'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'bytes':DEST.stat().st_size,'changed_payloads':list(replacements),'added_payloads':['classes16.dex'],'own_source_sha256':{p.relative_to(B).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (B/'src').rglob('*.java')},'android_art_executed':False,'pixel_tested':False,'server_tested':False}
 write(B/'build.json',json.dumps(meta,ensure_ascii=False,indent=2));print(json.dumps(meta,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
