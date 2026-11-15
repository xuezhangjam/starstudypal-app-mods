"""Rebuild the handwriting and answer-pane patch over the verified v11 APK."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,sys,zipfile
B=Path(__file__).resolve().parent;R=B.parent.parent;T=R/'tools/apk-patch';PREV=R/'apk-analysis/precision-pending-edit-v11'
JAVA=T/'java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe'
SOURCE=R/'精准作业-4.0.1.0-半对图标-未批改答案修改-v11.apk'
EXPECTED='9bc1b9457f319eccf60050353feab26b62d8bc1945643bd438ed1529e0bfb9bd'
DEST=R/'精准作业-4.0.1.0-手写优化-作答区联动-v12.apk'
OWN='Lcom/hailiang/workcloud/student/md3e/v3/'
PAT=re.compile(r'^\.method ([^\n]+)\n.*?^\.end method',re.M|re.S)
REF='com/hailiang/workcloud/student/mod/ReferenceAnswers'
ANALYSIS='com/hailiang/workcloud/student/shareui/work/review/components/detail/AnalysisRichView_androidKt'
def long(p):return Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p
def write(p,s):
 p=long(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.tmp');tmp.write_text(s,'utf8');os.replace(tmp,p)
def run(args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8',errors='replace')
 if p.stdout:print(p.stdout[-1600:],flush=True)
 if p.stderr:print(p.stderr[-1800:],flush=True)
 p.check_returncode()
def clone(a,b):
 for p in long(a).rglob('*'):
  rel=p.relative_to(long(a))
  if rel.parts[0] in ['build','dist']:continue
  q=long(b)/rel
  if p.is_dir():q.mkdir(parents=True,exist_ok=True)
  elif not q.exists():q.parent.mkdir(parents=True,exist_ok=True);os.link(p,q)
def types(desc):return re.findall(r'\[*L[^;]+;|\[*[ZBCSIJFDV]',desc)
def main():
 assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
 if '--reuse-compiled' not in sys.argv:run([sys.executable,'-X','utf8',B/'compile.py'])
 bases={}
 with zipfile.ZipFile(SOURCE) as z:
  for n in [5,11]:
   cache_root=PREV
   base=cache_root/f'work{n}';cache=cache_root/f'classes{n}-patch.apk';match=False
   if cache.exists():
    with zipfile.ZipFile(cache) as c:match=c.read('classes.dex')==z.read(f'classes{n}.dex')
   if not match:
    base=B/f'base{n}'
    if not base.exists():
     with zipfile.ZipFile(B/f'base{n}.apk','w') as a:a.writestr('classes.dex',z.read(f'classes{n}.dex'));a.writestr('AndroidManifest.xml',z.read('AndroidManifest.xml'))
     run([JAVA,'-jar',T/'apktool.jar','d','-r','-o',base,B/f'base{n}.apk'])
   bases[n]=base
 clone(bases[5],B/'work5')
 from patch_native import patch
 patch(bases[5])
 with zipfile.ZipFile(SOURCE) as z,zipfile.ZipFile(B/'helper.apk','w') as a:a.writestr('classes.dex',(B/'helper11/classes.dex').read_bytes());a.writestr('AndroidManifest.xml',z.read('AndroidManifest.xml'))
 run([JAVA,'-jar',T/'apktool.jar','d','-r','-f','-o',B/'work11',B/'helper.apk'])
 retained=[]
 for p in long(bases[11]/'smali').rglob('*.smali'):
  rel=p.relative_to(long(bases[11]/'smali'))
  if rel.as_posix().startswith(('com/hailiang/workcloud/student/md3e/v3/','com/android/tools/r8/annotations/')):continue
  q=long(B/'work11/smali')/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);retained.append(rel.as_posix())
 write(B/'retained-native11.json',json.dumps(retained,indent=2))
 replacements={}
 for n in [5,11]:
  run([JAVA,'-jar',T/'apktool.jar','b',B/f'work{n}','-o',B/f'classes{n}-patch.apk'])
  with zipfile.ZipFile(B/f'classes{n}-patch.apk') as z:replacements[f'classes{n}.dex']=z.read('classes.dex')
 unsigned=B/'precision-v12-unsigned.apk'
 with zipfile.ZipFile(SOURCE) as z,zipfile.ZipFile(unsigned,'w') as a:
  for info in z.infolist():
   if not(info.filename.startswith('META-INF/') and info.filename.upper().endswith(('.MF','.SF','.RSA','.DSA','.EC'))):a.writestr(info,replacements.get(info.filename,z.read(info.filename)))
 stage=Path(os.environ['LOCALAPPDATA'])/'CodexBuilds/precision-handwriting-v12';stage.mkdir(parents=True,exist_ok=True);shutil.copyfile(unsigned,stage/unsigned.name)
 signed=stage/'signed';signed.mkdir(exist_ok=True);result=signed/'precision-v12-aligned-signed.apk';result.unlink(missing_ok=True)
 run([JAVA,'-jar',T/'uber-apk-signer.jar','-a',stage/unsigned.name,'-o',signed,'--ks',T/'signing/precision-md3e-mod.jks','--ksAlias','precisionmd3e','--ksPass','android','--ksKeyPass','android'])
 shutil.copyfile(result,DEST)
 meta={'input':SOURCE.name,'input_sha256':EXPECTED,'output':DEST.name,'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'bytes':DEST.stat().st_size,'changed_payloads':['classes5.dex','classes11.dex'],'own_source_sha256':{p.relative_to(B).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (B/'src').glob('*.kt')},'android_device_tested':False,'school_server_tested':False}
 write(B/'build.json',json.dumps(meta,ensure_ascii=False,indent=2));print(json.dumps(meta,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
