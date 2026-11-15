from pathlib import Path
import hashlib,json,subprocess
B=Path(__file__).resolve().parent;ROOT=B.parent.parent;T=ROOT/'tools/apk-patch';JAVA=T/'java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe'
def run(args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=150);assert p.returncode==0,p.stdout+p.stderr;return p.stdout
classes=B/'test-classes';classes.mkdir(exist_ok=True)
print(run([JAVA,'-jar',T/'ecj.jar','-proc:none','-source','8','-target','8','-warn:none','-encoding','UTF-8','-d',classes,*list((B/'src').rglob('*.java')),*list((B/'tests').rglob('*.java'))]),end='')
out=run([JAVA,'-cp',classes,'TeacherWebLinksTest']);print(out,end='');(B/'test-results.txt').write_text(out,'utf-8')
meta={'passed':True,'result':out.strip(),'source_sha256':hashlib.sha256((B/'src/com/hljzjx/classroom/mod/TeacherWebLinks.java').read_bytes()).hexdigest(),'device_tested':False,'server_tested':False}
(B/'tests.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),'utf-8')
