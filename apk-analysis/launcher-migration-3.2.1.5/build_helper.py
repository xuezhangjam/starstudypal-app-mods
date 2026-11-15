from pathlib import Path
import json,os,subprocess,zipfile
B=Path(__file__).resolve().parent;R=B.parent.parent;T=R/'tools/apk-patch'
JAVA=T/'java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe'
ANDROID=R/'tools/android-sdk/android-34-ext12/android.jar'
API={
 'com/hailiang/launcher/data/bean/response/AppHtmlListBean.java':'package com.hailiang.launcher.data.bean.response;public class AppHtmlListBean {public boolean isWeb(){return false;}public boolean needDelete(){return false;}public long getVersionCode(){return 0;}'+''.join('public String '+n+'(){return null;}' for n in ['getPackageName','getAppName','getVersionName','getDownloadUrl'])+'}',
 'com/hailiang/launcher/common/download/app/AppUpdateTask.java':'package com.hailiang.launcher.common.download.app;public class AppUpdateTask {public int getDispenseType(){return 0;}public long getVersionCode(){return 0;}'+''.join('public String '+n+'(){return null;}' for n in ['getPackageName','getAppName','getVersionName','getDownloadUrl'])+'}',
 'com/hailiang/launcher/update/LauncherUpdateManager.java':'package com.hailiang.launcher.update;public class LauncherUpdateManager {public static void requestLaunchVersionWithCheckDialog(){}}',
 'com/hljzjx/launch/ui/main/MainActivity.java':'package com.hljzjx.launch.ui.main;public class MainActivity extends android.app.Activity {public void requestAppListAndControl(boolean f){}}',
 'com/jchou/commonlibrary/model/UserData.java':'package com.jchou.commonlibrary.model;public class UserData {public static long getUserId(){return 0;}}',
 'com/hljzjx/md3/SkinController.java':'package com.hljzjx.md3;public class SkinController {public static int mode(android.content.Context c){return 0;}}',
 'com/hljzjx/md3/ThemeController.java':'package com.hljzjx.md3;public class ThemeController {public static int night(android.content.Context c){return 0;}}',
}
def run(args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,encoding='utf8',errors='replace')
 if p.stdout:print(p.stdout[-2000:],flush=True)
 if p.stderr:print(p.stderr[-3000:],flush=True)
 p.check_returncode()
def main():
 for f,s in API.items():p=B/'compile-api'/f;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,'utf8')
 classes=B/'helper-classes';classes.mkdir(exist_ok=True)
 run([JAVA,'-jar',T/'ecj.jar','-proc:none','-source','8','-target','8','-warn:none','-encoding','UTF-8','-cp',ANDROID,'-d',classes,*list((B/'src').rglob('*.java')),*list((B/'compile-api').rglob('*.java'))])
 with zipfile.ZipFile(B/'updates.jar','w') as own,zipfile.ZipFile(B/'api.jar','w') as api:
  for p in classes.rglob('*.class'):
   f=p.relative_to(classes).as_posix();(own if f.startswith('com/hljzjx/md3/updates/') else api).write(p,f)
 out=B/'helper-dex';out.mkdir(exist_ok=True)
 run([JAVA,'-cp',T/'jadx/lib/jadx-gui-1.5.6-all.jar','com.android.tools.r8.D8','--min-api','29','--lib',JAVA.parent.parent,'--lib',ANDROID,'--lib',B/'api.jar','--output',out,B/'updates.jar'])
 (B/'api-sources.json').write_text(json.dumps(API,indent=2),'utf8')
if __name__=='__main__':main()
