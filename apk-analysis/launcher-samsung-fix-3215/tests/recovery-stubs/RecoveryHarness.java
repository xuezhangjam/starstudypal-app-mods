import android.app.Activity;import android.content.Intent;import android.os.*;import com.hailiang.opensdk.LauncherData;import com.hljzjx.samsung.*;
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
}