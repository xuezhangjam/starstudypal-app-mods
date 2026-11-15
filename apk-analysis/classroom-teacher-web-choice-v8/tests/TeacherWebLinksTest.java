import android.app.*;import android.content.*;import android.view.*;import android.widget.*;
import com.hljzjx.classroom.mod.TeacherWebLinks;
import com.hailiang.common.util.AppRuntimeData;
import com.nice.room.ui.roomlive.interaction.impl.ThirdAppInteraction;
import com.nice.room.ui.roomlive.interaction.impl.ThirdAppInteraction.ExternalLinkInfo;
public class TeacherWebLinksTest{
 static int checks;static void ok(boolean b,String m){checks++;if(!b)throw new AssertionError(m);}
 static View named(View v,String label){if(label.equals(v.description))return v;if(v instanceof TextView && label.equals(((TextView)v).text))return v;if(v instanceof ViewGroup)for(View x:((ViewGroup)v).children){View found=named(x,label);if(found!=null)return found;}return null;}
 static ThirdAppInteraction page(String url){AppRuntimeData.user=17;ThirdAppInteraction i=new ThirdAppInteraction();i.info=new ExternalLinkInfo(url);i.activity.getWindow().getDecorView().attach();return i;}
 static Dialog offer(ThirdAppInteraction i){ok(TeacherWebLinks.offer(i),"web dispatch consumed");Dialog d=Dialog.last;ok(d!=null && d.isShowing(),"choice visible");return d;}
 static void click(Dialog d,String label){View b=named(d.content,label);ok(b!=null,"route exists: "+label);b.performClick();}
 static void finish(ThirdAppInteraction i){TeacherWebLinks.close(i);i.activity.getWindow().getDecorView().detach();AppRuntimeData.user=17;}
 public static void main(String[] args){
  String url="https://example.test/lesson?q=a%2Bb&token=x%26y#part2";
  ThirdAppInteraction i=page(url);Dialog d=offer(i);
  ok(i.nativeRequests==0 && i.activity.started.isEmpty(),"no fetch or navigation before choice");ok(i.shortcuts==1,"teacher toolbar entry remains available");
  TeacherWebLinks.offer(i);ok(Dialog.last==d && i.shortcuts==1,"repeated click does not stack choices");
  click(d,"默认浏览器打开");ok(i.activity.started.size()==1 && i.nativeRequests==0 && !d.isShowing(),"browser route launches only a browser");
  Intent out=i.activity.started.get(0);ok(Intent.ACTION_VIEW.equals(out.action) && Intent.CATEGORY_BROWSABLE.equals(out.category) && url.equals(out.uri.toString()),"complete original URL preserved");
  ok("browser.default".equals(out.pkg) && out.selector==null,"system default browser selected");ok("https://".equals(i.activity.manager.probe.uri.toString()),"host-free preference avoids a site-specific native app");
  click(d,"课堂内打开");ok(i.nativeRequests==0,"stale double click cannot launch the other route");
  d=offer(i);click(d,"课堂内打开");ok(i.nativeRequests==1 && i.lastRequested==i.info && i.activity.started.size()==1,"classroom route forwards the original object only");
  i.whitelistReturned(i.info);ok(i.nativePages==1,"matching async whitelist can open original page");i.whitelistReturned(i.info);ok(i.nativePages==1,"duplicate callback ignored");finish(i);
  for(String browser:new String[]{null,"android","com.hljzjx.edu.student.classroom"}){
   i=page(url);i.activity.manager.browser=browser;d=offer(i);click(d,"默认浏览器打开");out=i.activity.started.get(0);
   ok(out.pkg==null && out.selector!=null && Intent.ACTION_MAIN.equals(out.selector.action) && Intent.CATEGORY_APP_BROWSER.equals(out.selector.category),"unset/resolver/self uses browser-only selector");ok(url.equals(out.uri.toString()),"selector retains URL");finish(i);
  }
  i=page(url);i.activity.manager.queryThrows=true;d=offer(i);click(d,"默认浏览器打开");ok(i.activity.started.get(0).selector!=null,"package visibility failure retains browser selection");finish(i);
  for(boolean denied:new boolean[]{false,true}){
   i=page(url);i.activity.missingBrowser=!denied;i.activity.deniedBrowser=denied;d=offer(i);click(d,"默认浏览器打开");
   ok(d.isShowing() && i.activity.started.isEmpty() && i.nativeRequests==0,"missing/denied browser retains choice");click(d,"课堂内打开");ok(i.nativeRequests==1,"classroom remains usable after browser failure");finish(i);
  }
  i=page(url);d=offer(i);click(d,"取消");ok(!d.isShowing() && i.nativeRequests==0 && i.activity.started.isEmpty(),"cancel does not navigate");d=offer(i);d.dismiss();ok(i.activity.getWindow().getDecorView().listeners.isEmpty() && i.activity.getWindow().getDecorView().layoutListeners.isEmpty(),"back/outside dismissal releases listeners");finish(i);
  i=page(url);d=offer(i);ExternalLinkInfo old=i.info;i.info=new ExternalLinkInfo("https://next.test/");Dialog next=offer(i);ok(!d.isShowing(),"new teacher link dismisses old choice");click(d,"默认浏览器打开");ok(i.activity.started.isEmpty(),"old choice cannot open replaced link");click(next,"课堂内打开");i.whitelistReturned(old);ok(i.nativePages==0,"old whitelist does not consume new ticket");i.whitelistReturned(i.info);ok(i.nativePages==1,"new matching callback succeeds");finish(i);
  for(int change=0;change<7;change++){
   i=page(url);d=offer(i);old=i.info;click(d,"课堂内打开");
   if(change==0)AppRuntimeData.user=88;else if(change==1)i.room.room++;else if(change==2)i.info=new ExternalLinkInfo(url);else if(change==3){i.ended=true;TeacherWebLinks.close(i);}else if(change==4)i.activity.finishing=true;else if(change==5)i.activity.destroyed=true;else i.activity.getWindow().getDecorView().detach();
   i.whitelistReturned(old);ok(i.nativePages==0,"account/room/link/end/activity/detach invalidates async callback "+change);finish(i);
  }
  for(int change=0;change<5;change++){
   i=page(url);d=offer(i);if(change==0)AppRuntimeData.user=88;else if(change==1)i.room.room++;else if(change==2)i.info=new ExternalLinkInfo(url);else if(change==3){i.ended=true;TeacherWebLinks.close(i);}else i.activity.getWindow().getDecorView().detach();
   click(d,"默认浏览器打开");ok(i.activity.started.isEmpty() && !d.isShowing(),"stale UI cannot launch browser "+change);finish(i);
  }
  i=page(url);i.failOpen=true;d=offer(i);click(d,"课堂内打开");ok(d.isShowing() && !TeacherWebLinks.allowNative(i,i.info),"native exception removes pending request and retains choice");i.failOpen=false;click(d,"课堂内打开");ok(i.nativeRequests==1,"explicit retry works");finish(i);
  for(String app:new String[]{"com.hailiang.h5.ai_portal","com.yangcong345.zhike","some.other.app",""}){i=page(app);ok(!TeacherWebLinks.offer(i) && i.nativeRequests==0 && i.activity.started.isEmpty(),"native app/AI original flow retained");finish(i);}
  for(String bad:new String[]{"https://","httpx://bad.test","https://bad.test/a b","https:///x","https://bad.test:70000/"}){i=page(bad);ok(TeacherWebLinks.offer(i) && i.shortcuts==0 && i.nativeRequests==0 && i.activity.started.isEmpty(),"invalid HTTP link not launched");finish(i);}
  i=page(url);i.room=null;ok(TeacherWebLinks.offer(i) && i.activity.started.isEmpty(),"missing room does not crash dispatch");finish(i);
  i=page(url);d=offer(i);View decor=i.activity.getWindow().getDecorView();decor.resize(320,500);ok(d.getWindow().width==288,"choice fits narrow window");decor.resize(320,500);ok(d.getWindow().width==288,"stable window remains stable");decor.detach();ok(!d.isShowing() && decor.listeners.isEmpty() && decor.layoutListeners.isEmpty(),"detach closes choice and releases listeners");finish(i);
  i=page(url);AppRuntimeData.user=0;ok(TeacherWebLinks.offer(i) && i.shortcuts==0,"logged-out session does not open teacher link");finish(i);
  System.out.println("PASS "+checks+" teacher-link route/URL/lifecycle/async/browser failure assertions");
 }
}
