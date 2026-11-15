from pathlib import Path
import json,subprocess,sys
B=Path(__file__).resolve().parent;R=B.parent.parent
JAVA=R/'tools/apk-patch/java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe'
ANDROID=R/'tools/android-sdk/android-34-ext12/android.jar'
def run(args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8',errors='replace');print(p.stdout,p.stderr);p.check_returncode();return p.stdout.strip()
run([sys.executable,B/'tests/make_platform.py'])
reports={}
for suite,files,target in [
 ('InkQueueTest',[B/'src/com/hljzjx/classroom/reviewdraw/InkQueue.java',B/'tests/InkQueueTest.java'],B/'test-classes'),
 ('ReviewDrawingTest',[*list((B/'tests/platform').rglob('*.java')),*list((B/'src').rglob('*.java')),B/'tests/ReviewDrawingTest.java'],B/'adapter-test-classes'),
 ('LiveRefreshTest',[*list((B/'tests/platform').rglob('*.java')),*list((B/'src').rglob('*.java')),B/'tests/LiveRefreshTest.java'],B/'adapter-test-classes')]:
 run([JAVA,'-jar',R/'tools/apk-patch/ecj.jar','-proc:none','-source','8','-target','8','-encoding','UTF-8','-warn:none','-cp',ANDROID,'-d',target,*files])
 reports[suite]=run([JAVA,'-cp',target,'com.hljzjx.classroom.reviewdraw.'+suite])
reports['android_device_tested']=False;reports['server_tested']=False
(B/'tests.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),'utf8')
