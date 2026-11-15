from pathlib import Path
import hashlib,json,os,subprocess,sys,zipfile
B=Path(__file__).resolve().parent;R=B.parent.parent;T=R/'tools/apk-patch';D=R/'tools/precision-compose'
JAVA=T/'java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe';ANDROID=R/'tools/android-sdk/android-34-ext12/android.jar'
def run(args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8',errors='replace');print(p.stdout,p.stderr,flush=True);p.check_returncode()
def main():
 run([sys.executable,B/'make_api.py'])
 api=B/'api-classes';api.mkdir(exist_ok=True);classes=B/'classes';classes.mkdir(exist_ok=True)
 # Only clear generated classfiles in these two verified local output folders.
 # A removed Kotlin lambda/file must not survive into the next ui.jar.
 for directory in [api,classes]:
  assert directory.resolve().is_relative_to(B.resolve())
  for compiled in directory.rglob('*.class'):compiled.unlink()
 jars=[p for p in D.glob('*.jar') if not any(x in p.name for x in ['compiler','daemon','reflect','sources','script-runtime'])]
 run([JAVA,'-jar',T/'ecj.jar','-proc:none','-source','8','-target','8','-warn:none','-encoding','UTF-8','-cp',os.pathsep.join(map(str,[ANDROID,*jars])),'-d',api,*list((B/'compile-api').rglob('*.java'))])
 compiler_names=['kotlin-compiler-embeddable-2.3.0.jar','kotlin-stdlib-2.3.0.jar','kotlin-script-runtime-2.3.0.jar','kotlin-reflect-1.6.10.jar','kotlin-daemon-embeddable-2.3.0.jar','kotlinx-coroutines-core-jvm-1.8.0.jar','annotations-13.0.jar']
 compiler=os.pathsep.join(str(D/n) for n in compiler_names)
 jars=[p for p in D.glob('*.jar') if not any(x in p.name for x in ['compiler','daemon','reflect','sources','script-runtime'])]
 cp=os.pathsep.join(map(str,[ANDROID,api,*jars]))
 run([JAVA,'-Xmx2g','-cp',compiler,'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler','-no-stdlib','-no-reflect','-jvm-target','1.8','-classpath',cp,'-Xplugin='+str(D/'kotlin-compose-compiler-plugin-embeddable-2.3.0.jar'),'-P','plugin:androidx.compose.compiler.plugins.kotlin:generateFunctionKeyMetaClasses=false','-module-name','precision_md3e_v3','-d',classes,*list((B/'src').rglob('*.kt'))])
 with zipfile.ZipFile(B/'ui.jar','w',compression=zipfile.ZIP_DEFLATED) as z:
  for p in classes.rglob('*.class'):
   name=p.relative_to(classes).as_posix();assert name.startswith('com/hailiang/workcloud/student/md3e/v3/');z.write(p,name)
 with zipfile.ZipFile(B/'api.jar','w') as z:
  for p in api.rglob('*.class'):z.write(p,p.relative_to(api).as_posix())
 helper=B/'helper11';helper.mkdir(exist_ok=True)
 libs=[ANDROID,B/'api.jar',*jars]
 cmd=[JAVA,'-cp',T/'jadx/lib/jadx-gui-1.5.6-all.jar','com.android.tools.r8.D8','--min-api','29','--lib',JAVA.parent.parent]
 for p in libs:cmd+=['--lib',p]
 cmd+=['--output',helper,B/'ui.jar'];run(cmd)
 (B/'compile.json').write_text(json.dumps({'kotlin':'2.3.0','compose':'1.11.2','material3':'1.5.0-alpha17','ui_jar_sha256':hashlib.sha256((B/'ui.jar').read_bytes()).hexdigest()},indent=2),'utf8')
if __name__=='__main__':main()
