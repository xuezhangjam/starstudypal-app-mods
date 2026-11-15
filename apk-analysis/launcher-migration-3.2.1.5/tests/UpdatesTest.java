package com.hljzjx.md3.updates;
import android.app.*;import android.content.*;import android.os.*;import android.view.*;import android.widget.*;
import com.hljzjx.launch.ui.main.MainActivity;import com.hljzjx.launch.ui.personcenter.PersonCenterActivity;
import com.hailiang.launcher.data.bean.response.AppHtmlListBean;import com.hailiang.launcher.common.download.app.AppUpdateTask;
import com.jchou.commonlibrary.model.UserData;import com.hailiang.launcher.update.LauncherUpdateManager;
import java.util.*;
public class UpdatesTest {
 static int checks;
 static void ok(boolean b,String msg){checks++;if(!b)throw new AssertionError(checks+": "+msg);}
 static Dialog latest(){return Dialog.shown.get(Dialog.shown.size()-1);}
 static TextView find(View v,String value){if(v instanceof TextView&&value.equals(((TextView)v).text))return (TextView)v;if(v instanceof ViewGroup)for(View c:((ViewGroup)v).children){TextView got=find(c,value);if(got!=null)return got;}return null;}
 static void click(String value){TextView v=find(latest().content,value);ok(v!=null,"button present "+value);v.performClick();Handler.drain();}
 static boolean has(String value){return !Dialog.shown.isEmpty()&&find(latest().content,value)!=null;}
 static ManualUpdates.Offer offer(String url){return new ManualUpdates.Offer("app.test","../坏/名字\\测试","2.0",2,url,42);}
 public static void main(String[] args){
  String url="https://host.test/update.apk?sig=a%2Bb%2F1&x=2#fragment";
  for(String good:new String[]{url,"http://host.test/a.apk","HTTPS://host.test/x?x=%22"})ok(ManualUpdates.validUrl(good),"HTTP(S) signed link accepted");
  for(String bad:new String[]{null,"","javascript:alert(1)","file:///a.apk","data:x","content://x","https:///x","https://u:p@host/a"," https://host/a","https://host/a ","https://host/has space"})ok(!ManualUpdates.validUrl(bad),"invalid URI rejected");
  String filename=ManualUpdates.filename(offer(url),123);ok(filename.endsWith("-2-123.apk")&&!filename.contains("/")&&!filename.contains("\\")&&!filename.startsWith("."),"safe filename");
  Context c=new Context();ManualUpdates.Offer o=offer(url);
  ok(ManualUpdates.download(c,o),"enqueue succeeds");ok(c.downloads.enqueued.size()==1,"one download");DownloadManager.Request request=c.downloads.enqueued.get(0);
  ok(request.uri.toString().equals(url),"preserve URL query escaping and fragment");ok(request.dir.equals("Download")&&request.name.endsWith(".apk"),"public Download destination");
  ok(request.mime.equals("application/vnd.android.package-archive")&&request.visibility==1,"APK MIME and completion notification");ok(Toast.last.startsWith("已加入系统下载"),"queue acceptance is not completion");
  ok(ManualUpdates.download(c,o)&&c.downloads.enqueued.size()==1,"repeat pending no duplicate");ok(c.downloads.closed==1,"query cursor closed");
  c.downloads.states.put(100L,DownloadManager.STATUS_SUCCESSFUL);ok(ManualUpdates.download(c,o)&&c.downloads.enqueued.size()==1&&Toast.last.contains("已下载"),"completed retained");
  c.downloads.states.put(100L,DownloadManager.STATUS_FAILED);ok(ManualUpdates.download(c,o)&&c.downloads.enqueued.size()==2,"failed can retry");ok(!request.name.equals(c.downloads.enqueued.get(1).name),"retry never overwrites prior destination");
  c.downloads.failQuery=true;ok(!ManualUpdates.download(c,o)&&c.downloads.enqueued.size()==2,"query failure no blind duplicate");
  Context denied=new Context();denied.downloads.fail=true;ok(!ManualUpdates.download(denied,o)&&denied.downloads.enqueued.isEmpty(),"enqueue refusal visible");
  denied.downloads=null;ok(!ManualUpdates.download(denied,o),"missing system downloader handled");ok(!ManualUpdates.download(new Context(),offer("file:///tmp.apk")),"invalid URI never enqueued");
  Activity browser=new Activity();ok(ManualUpdates.browser(browser,url),"browser launch");Intent intent=browser.started.get(0);
  ok(intent.data.toString().equals(url)&&intent.categories.contains(Intent.CATEGORY_BROWSABLE),"browser gets original link");ok(intent.selector.categories.contains(Intent.CATEGORY_APP_BROWSER),"system browser selector");
  browser.failBrowser=true;ok(!ManualUpdates.browser(browser,url),"missing or blocked browser handled");ok(!ManualUpdates.browser(browser,"javascript:a"),"browser scheme guard");
  Application app=new Application();ManualUpdates.init(app);ManualUpdates.init(app);MainActivity main=new MainActivity();main.pm.versions.put("app.test",1L);app.callbacks.onActivityResumed(main);Handler.drain();
  AppHtmlListBean b=new AppHtmlListBean();b.url=url;ManualUpdates.detectBeans(main,Arrays.asList(b));b.name="mutated";Handler.drain();
  ok(latest().cancelable&&latest().touch,"update prompt is dismissible");ok(main.downloads.enqueued.isEmpty(),"detection does not download or install");ok(has("测试应用  2.0"),"capture immutable original model");
  click("测试应用  2.0");ok(has("下载 APK")&&has("浏览器打开下载链接")&&has("稍后更新"),"three choices");click("稍后更新");ok(main.downloads.enqueued.isEmpty(),"skip has no download side effect");
  int before=Dialog.shown.size();b.name="测试应用";ManualUpdates.detectBeans(main,Arrays.asList(b));Handler.drain();ok(Dialog.shown.size()==before,"same automatic update not repeatedly shown");
  AppHtmlListBean web=new AppHtmlListBean();web.web=true;web.pkg="web";main.pm.versions.put("web",0L);
  AppHtmlListBean deleted=new AppHtmlListBean();deleted.deleted=true;deleted.pkg="gone";main.pm.versions.put("gone",0L);
  AppHtmlListBean missing=new AppHtmlListBean();missing.pkg="absent";
  AppHtmlListBean current=new AppHtmlListBean();current.pkg="current";main.pm.versions.put("current",2L);
  ManualUpdates.detectBeans(main,Arrays.asList(web,deleted,missing,current));Handler.drain();ok(Dialog.shown.size()==before,"skip H5/deleted/missing/up-to-date background offers");
  b.code=3;b.version="3";ManualUpdates.detectBeans(main,Arrays.asList(b));Handler.drain();ok(Dialog.shown.size()==before+1,"newer version prompts again");click("测试应用  3");
  TextView stale=find(latest().content,"下载 APK");UserData.id=99;stale.performClick();Handler.drain();ok(main.downloads.enqueued.isEmpty(),"stale account button cannot enqueue");
  UserData.id=42;app.callbacks.onActivityResumed(main);Handler.drain();b.code=4;b.version="4";ManualUpdates.detectBeans(main,Arrays.asList(b));UserData.id=99;Handler.drain();ok(!latest().visible,"stale account queued results discarded");
  UserData.id=42;app.callbacks.onActivityResumed(main);Handler.drain();ManualUpdates.offerBean(main,b,true);Handler.drain();ok(has("下载 APK"),"explicit app selection can reopen offer");
  stale=find(latest().content,"下载 APK");app.callbacks.onActivityPaused(main);stale.performClick();Handler.drain();ok(main.downloads.enqueued.isEmpty(),"paused screen stale button blocked");
  app.callbacks.onActivityResumed(main);Handler.drain();ManualUpdates.offerBean(main,b,true);Handler.drain();click("下载 APK");ok(main.downloads.enqueued.size()==1&&!latest().visible,"download accepted closes optional prompt");
  PersonCenterActivity profile=new PersonCenterActivity();profile.views.put(1,new View(profile));profile.views.put(2,new TextView(profile));ManualUpdates.bindSettings(profile);
  ok(((TextView)profile.views.get(2)).text.equals("应用更新（仅下载）"),"settings entry visible");app.callbacks.onActivityPaused(main);app.callbacks.onActivityResumed(profile);Handler.drain();profile.views.get(1).performClick();Handler.drain();
  click("刷新应用更新");ok(main.refreshes==1&&LauncherUpdateManager.checks==1,"refresh reuses original app list and self-update requests");
  profile.failBrowser=true;ManualUpdates.offerBean(profile,b,true);Handler.drain();click("浏览器打开下载链接");ok(latest().visible,"blocked browser retains choice");
  profile.failBrowser=false;click("浏览器打开下载链接");ok(profile.started.size()==1&&!latest().visible,"successful browser opens exact link without installer");
  AppUpdateTask t=new AppUpdateTask();profile.pm.versions.put("task.app",1L);ManualUpdates.detectTasks(profile,Arrays.asList(t));Handler.drain();ok(has("Task  3"),"central task update captured");click("稍后更新");
  int dialogs=Dialog.shown.size();t.code=4;t.type=2;ManualUpdates.detectTasks(profile,Arrays.asList(t));Handler.drain();ok(Dialog.shown.size()==dialogs,"withdrawal is not an APK update offer");
  app.callbacks.onActivityDestroyed(profile);ok(!latest().visible,"activity destruction removes window");
  System.out.println("PASS "+checks+" actual updater Java assertions; mocked Android only, no HTTP/device");
 }
}
