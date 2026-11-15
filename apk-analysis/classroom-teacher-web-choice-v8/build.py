"""Add a teacher-web-link route picker on the released v7 baseline."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,zipfile
B=Path(__file__).resolve().parent;ROOT=B.parent.parent;T=ROOT/'tools/apk-patch'
JAVA=T/'java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe';ANDROID=ROOT/'tools/android-sdk/android-34-ext12/android.jar'
SOURCE=ROOT/'学生端课堂-3.2.1.0-续答结果显示修复-v7.apk';DEST=ROOT/'学生端课堂-3.2.1.0-网页打开方式选择-v8.apk'
EXPECTED='1f4655e8f61163f1980d295cfd44992a6ed4b712c7fbd9ba802badcad8429396'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
def run(args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace')
 if p.stdout:print(p.stdout,flush=True)
 if p.stderr:print(p.stderr,flush=True)
 p.check_returncode()
def write(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.tmp');q.write_text(s,'utf-8');os.replace(q,p)
def long(p):return '\\\\?\\'+str(p.resolve()) if os.name=='nt' else str(p)
base=B/'base4';work=B/'work4';cache=ROOT/'apk-analysis/classroom-continuation-results-v7'
if not base.exists():
 reuse=False
 if (cache/'classes4-patch.apk').exists():
  with zipfile.ZipFile(SOURCE) as a,zipfile.ZipFile(cache/'classes4-patch.apk') as c:reuse=a.read('classes4.dex')==c.read('classes.dex')
 if reuse:
  base.mkdir()
  for p in (cache/'work4').rglob('*'):
   rel=p.relative_to(cache/'work4')
   if rel.parts[0] in {'build','dist'}:continue
   q=base/rel
   if p.is_dir():q.mkdir(parents=True,exist_ok=True)
   else:q.parent.mkdir(parents=True,exist_ok=True);os.link(long(p),long(q))
 else:
  thin=B/'input-classes4.apk'
  with zipfile.ZipFile(SOURCE) as a,zipfile.ZipFile(thin,'w') as z:z.writestr('classes.dex',a.read('classes4.dex'));z.writestr('AndroidManifest.xml',a.read('AndroidManifest.xml'))
  run([JAVA,'-jar',T/'apktool.jar','d','-r','-o',base,thin])
for p in base.rglob('*'):
 rel=p.relative_to(base)
 if rel.parts[0] in {'build','dist'}:continue
 q=work/rel
 if p.is_dir():q.mkdir(parents=True,exist_ok=True)
 elif not os.path.exists(long(q)):q.parent.mkdir(parents=True,exist_ok=True);os.link(long(p),long(q))
PAT=re.compile(r'^\.method ([^\n]+)\n.*?^\.end method',re.M|re.S)
HELPER='Lcom/hljzjx/classroom/mod/TeacherWebLinks;'
def edit(file,signature,fn):
 s=(work/'smali'/file).read_text('utf-8');m=[m for m in PAT.finditer(s) if m[1].strip().endswith(signature)];assert len(m)==1
 m=m[0];updated=fn(m[0]);assert updated!=m[0];write(work/'smali'/file,s[:m.start()]+updated+s[m.end():])
# Native hooks are generated in patch_native.py.
exec((B/'patch_native.py').read_text('utf-8'))
classes=B/'classes';classes.mkdir(exist_ok=True)
run([JAVA,'-jar',T/'ecj.jar','-proc:none','-source','8','-target','8','-encoding','UTF-8','-warn:none','-cp',ANDROID,'-d',classes,*list((B/'src').rglob('*.java')),*list((B/'compile-api').rglob('*.java'))])
jar=B/'teacher-web-links.jar'
with zipfile.ZipFile(jar,'w') as z:
 for p in classes.rglob('*.class'):
  if p.relative_to(classes).as_posix().startswith('com/hljzjx/classroom/mod/'):
   z.write(p,p.relative_to(classes).as_posix())
api=B/'compile-api.jar'
with zipfile.ZipFile(api,'w') as z:
 for p in classes.rglob('*.class'):
  if not p.relative_to(classes).as_posix().startswith('com/hljzjx/classroom/mod/'):
   z.write(p,p.relative_to(classes).as_posix())
helper=B/'helper12';helper.mkdir(exist_ok=True)
run([JAVA,'-cp',T/'jadx/lib/jadx-gui-1.5.6-all.jar','com.android.tools.r8.D8','--min-api','29','--lib',JAVA.parent.parent,'--lib',ANDROID,'--lib',api,'--output',helper,jar])
patched=B/'classes4-patch.apk';run([JAVA,'-jar',T/'apktool.jar','b',work,'-o',patched])
with zipfile.ZipFile(patched) as z:replacement={'classes4.dex':z.read('classes.dex'),'classes12.dex':(helper/'classes.dex').read_bytes()}
unsigned=B/'teacher-web-links-unsigned.apk'
def sig(n):return n.startswith('META-INF/') and n.upper().endswith(('.MF','.SF','.RSA','.DSA','.EC'))
with zipfile.ZipFile(SOURCE) as a,zipfile.ZipFile(unsigned,'w') as z:
 assert 'classes12.dex' not in a.namelist()
 for info in a.infolist():
  if not sig(info.filename):z.writestr(info,replacement.get(info.filename) or a.read(info.filename))
 z.writestr('classes12.dex',replacement['classes12.dex'])
stage=Path(os.environ['LOCALAPPDATA'])/'CodexBuilds/classroom-teacher-web-choice-v8';stage.mkdir(parents=True,exist_ok=True)
shutil.copyfile(unsigned,stage/unsigned.name);signed=stage/'signed';signed.mkdir(exist_ok=True);result=signed/'teacher-web-links-aligned-signed.apk';result.unlink(missing_ok=True)
run([JAVA,'-jar',T/'uber-apk-signer.jar','-a',stage/unsigned.name,'-o',signed,'--ks',T/'signing/classroom-mod.jks','--ksAlias','classroommod','--ksPass','android','--ksKeyPass','android'])
shutil.copyfile(result,DEST)
meta={'input':SOURCE.name,'input_sha256':EXPECTED,'output':DEST.name,'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'size':DEST.stat().st_size,'changed_payloads':['classes4.dex'],'added_payloads':['classes12.dex'],'device_tested':False,'classroom_server_tested':False,'source_sha256':hashlib.sha256((B/'src/com/hljzjx/classroom/mod/TeacherWebLinks.java').read_bytes()).hexdigest(),'helper_dex_sha256':hashlib.sha256((helper/'classes.dex').read_bytes()).hexdigest()}
write(B/'build.json',json.dumps(meta,ensure_ascii=False,indent=2));print(json.dumps(meta,ensure_ascii=False,indent=2))
