"""Run the actual recovery Java against controlled process/activity states."""
from pathlib import Path
import json
from build import B,T,JAVA,run,write

STUBS={
'android/os/Build.java':'''package android.os; public class Build {public static String MANUFACTURER="samsung"; public static class VERSION {public static int SDK_INT=37;}}''',
'android/os/Bundle.java':'package android.os; public class Bundle {}',
'android/content/Intent.java':'''package android.content; public class Intent {public static final int FLAG_ACTIVITY_NEW_TASK=0x10000000,FLAG_ACTIVITY_CLEAR_TASK=0x8000; public int flags;public String pkg,cls;public Intent setFlags(int value){flags=value;return this;} public Intent setClassName(String p,String c){pkg=p;cls=c;return this;}}''',
'android/app/Activity.java':'''package android.app; public class Activity {public boolean finishing,destroyed,throwStart; public int starts;public android.content.Intent intent; public boolean isFinishing(){return finishing;}public boolean isDestroyed(){return destroyed;}public String getPackageName(){return "com.hljzjx.edu.student.launch";}public void startActivity(android.content.Intent value){if(throwStart)throw new IllegalStateException();starts++;intent=value;}public void finish(){finishing=true;}}''',
'android/util/Log.java':'''package android.util; public class Log {public static int i(String t,String m){return 0;}public static int w(String t,String m){return 0;}}''',
'com/hailiang/opensdk/LauncherData.java':'''package com.hailiang.opensdk; public class LauncherData {public static final LauncherData INSTANCE=new LauncherData();public static String token="";public static boolean readFails;public static int reads;public String getToken(){reads++;if(readFails)throw new IllegalStateException();return token;}}''',
'RecoveryHarness.java':'''import android.app.Activity;import android.content.Intent;import android.os.*;import com.hailiang.opensdk.LauncherData;import com.hljzjx.samsung.*;
public class RecoveryHarness {
 static int checks;static void check(boolean value,String name){if(!value)throw new AssertionError(name);checks++;}
 static void reset(){Build.MANUFACTURER="samsung";Build.VERSION.SDK_INT=37;LauncherData.token="synthetic-session";LauncherData.readFails=false;LauncherData.reads=0;}
 public static void main(String[] args){
  reset();check(LoginRecovery.shouldClearOnCreate(null),"fresh login keeps original clear");
  check(!LoginRecovery.shouldClearOnCreate(new Bundle()),"restored page preserves credentials");
  Activity a=new Activity();LoginRecovery.resumeSavedLogin(a,new Bundle());check(a.starts==1&&a.finishing,"restored valid session opens home");
  check(a.intent.flags==0x10008000&&a.intent.cls.equals("com.hljzjx.launch.ui.main.MainActivity"),"recovery clears stale login stack");
  check(LauncherData.token.equals("synthetic-session"),"recovery never overwrites token");
  reset();LauncherData.token="";a=new Activity();LoginRecovery.resumeSavedLogin(a,new Bundle());check(a.starts==0&&!a.finishing,"expired session remains at login");
  reset();LauncherData.token=null;a=new Activity();LoginRecovery.resumeSavedLogin(a,new Bundle());check(a.starts==0,"missing session remains at login");
  reset();a=new Activity();LoginRecovery.resumeSavedLogin(a,null);check(a.starts==0&&LauncherData.reads==0,"fresh login never auto-skips");
  reset();Build.MANUFACTURER="Google";check(LoginRecovery.shouldClearOnCreate(new Bundle()),"non Samsung behavior retained");a=new Activity();LoginRecovery.resumeSavedLogin(a,new Bundle());check(a.starts==0&&LauncherData.reads==0,"non Samsung recovery unchanged");
  Intent i=new Intent();i.flags=0x24000000;LoginRecovery.finishLoginStack(i,true);check(i.flags==0x24000000,"non Samsung task flags retained");
  reset();i=new Intent();i.flags=0x24000000;LoginRecovery.finishLoginStack(i,false);check(i.flags==0x24000000,"normal home flags retained");LoginRecovery.finishLoginStack(i,true);check(i.flags==0x10008000,"successful Samsung login clears stale login pages");
  reset();a=new Activity();a.destroyed=true;LoginRecovery.resumeSavedLogin(a,new Bundle());check(a.starts==0,"destroyed page not launched");a=new Activity();a.finishing=true;LoginRecovery.resumeSavedLogin(a,new Bundle());check(a.starts==0,"finishing page not launched");
  reset();LauncherData.readFails=true;a=new Activity();LoginRecovery.resumeSavedLogin(a,new Bundle());check(a.starts==0&&LauncherData.token.equals("synthetic-session"),"read failure does not erase session");
  reset();a=new Activity();a.throwStart=true;LoginRecovery.resumeSavedLogin(a,new Bundle());check(!a.finishing&&LauncherData.token.equals("synthetic-session"),"launch failure does not erase session or close login");
  reset();Build.MANUFACTURER="SAMSUNG";check(!LoginRecovery.shouldClearOnCreate(new Bundle()),"case insensitive vendor");Build.VERSION.SDK_INT=28;check(LoginRecovery.shouldClearOnCreate(new Bundle()),"older SDK untouched");
  System.out.println("PASS recovery assertions: "+checks);
 }
}'''
}
def main():
    src=B/'tests/recovery-stubs';classes=B/'tests/recovery-classes';classes.mkdir(parents=True,exist_ok=True)
    for name,text in STUBS.items():write(src/name,text)
    own=B/'src/com/hljzjx/samsung'
    run([JAVA,'-jar',T/'ecj.jar','-proc:none','-source','8','-target','8','-warn:none','-encoding','UTF-8','-d',classes,*sorted(src.rglob('*.java')),own/'SamsungDevice.java',own/'LoginRecovery.java'])
    run([JAVA,'-cp',classes,'RecoveryHarness'])
    write(B/'login-tests.json',json.dumps({'actual_helper_java_executed':True,'assertions':19,'android_runtime':False,'real_server':False},indent=2))
if __name__=='__main__':main()
