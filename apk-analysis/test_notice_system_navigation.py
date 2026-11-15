"""Execute the real shell/navigation Java with UI doubles, not Android pixels."""
from pathlib import Path
import subprocess

R = Path(__file__).resolve().parent
ROOT = R.parent
B = R/'notice-m3e-1.0.6/system-fix'
JAVA = ROOT/'tools/apk-patch/java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe'

# Reuse the prior Android UI doubles, without running the old build commands.
prefix = (R/'test_notice_m3e.py').read_text('utf-8').split("files['com/hailiang/notice/m3e/Test.java']=r'''")[0]
scope = {'__file__': str(R/'test_notice_m3e.py')}
exec(compile(prefix, '<notice-ui-doubles>', 'exec'), scope)
files = scope['files']
files['android/view/View.java'] = files['android/view/View.java'].replace('public void setSelected(boolean b){}', 'public boolean selected;public void setSelected(boolean b){selected=b;}')
files['android/view/View.java'] = files['android/view/View.java'].replace('public class View {', 'public class View {public static final int VISIBLE=0,GONE=8;')
files.update({
 'android/app/Application.java': 'package android.app;public class Application extends android.content.Context {}',
 'android/text/Editable.java': 'package android.text;public interface Editable extends CharSequence {}',
 'android/text/TextWatcher.java': 'package android.text;public interface TextWatcher {void beforeTextChanged(CharSequence s,int st,int count,int after);void onTextChanged(CharSequence s,int st,int before,int count);void afterTextChanged(Editable e);}',
 'android/view/Gravity.java': 'package android.view;public class Gravity {public static final int TOP=48,CENTER=17,CENTER_HORIZONTAL=1;}',
 'android/util/Log.java': 'package android.util;public class Log {public static int e(String tag,String msg,Throwable error){error.printStackTrace();return 0;}}',
 'android/content/DialogInterface.java': 'package android.content;public interface DialogInterface {interface OnClickListener {void onClick(DialogInterface d,int which);}}',
 'android/view/Window.java': 'package android.view;public class Window {public void setBackgroundDrawable(android.graphics.drawable.Drawable d){}}',
 'android/app/AlertDialog.java': '''package android.app;import android.content.*;import android.view.*;import android.widget.*;public class AlertDialog {
 public void show(){}public Window getWindow(){return new Window();}public TextView getButton(int i){return new TextView(new Context());}
 public static class Builder {public Builder(Context c){}public Builder setCustomTitle(View v){return this;}public Builder setView(View v){return this;}public Builder setNegativeButton(String s,DialogInterface.OnClickListener l){return this;}public Builder setPositiveButton(String s,DialogInterface.OnClickListener l){return this;}public AlertDialog create(){return new AlertDialog();}}}''',
})
files['androidx/viewpager2/widget/ViewPager2.java'] = '''package androidx.viewpager2.widget;
import android.view.View;import android.content.Context;import java.util.*;
public final class ViewPager2 extends View {
 public int current,smoothCalls,immediateCalls;public boolean user=true;
 public final List<OnPageChangeCallback> callbacks=new ArrayList<OnPageChangeCallback>();
 public ViewPager2(Context c){super(c);}public int getCurrentItem(){return current;}
 public void setUserInputEnabled(boolean b){user=b;}
 public void setCurrentItem(int n){setCurrentItem(n,true);}
 public void setCurrentItem(int n,boolean smooth){if(smooth)smoothCalls++;else immediateCalls++;current=n;for(OnPageChangeCallback cb:new ArrayList<OnPageChangeCallback>(callbacks))cb.onPageSelected(n);}
 public void registerOnPageChangeCallback(OnPageChangeCallback c){callbacks.add(c);}
 public void unregisterOnPageChangeCallback(OnPageChangeCallback c){callbacks.remove(c);}
 public abstract static class OnPageChangeCallback {public void onPageSelected(int n){}}
}'''
files['com/hailiang/notice/m3e/NavigationTest.java'] = r'''package com.hailiang.notice.m3e;
import android.view.*;import android.widget.*;import android.os.Bundle;import androidx.viewpager2.widget.ViewPager2;
import com.hailiang.notice.MainActivity;import java.util.*;
public class NavigationTest {
 static int checks;static void ok(boolean b,String why){checks++;if(!b)throw new AssertionError(why);}
 static Object shell(MainActivity a)throws Exception{java.lang.reflect.Field f=NoticeShell.class.getDeclaredField("pages");f.setAccessible(true);return ((Map<?,?>)f.get(null)).get(a);}
 static Object field(Object o,String n){return Data.field(o,n);}
 static TextView text(Object p,String n){return (TextView)field(p,n);}
 static void click(Object p,String n){TextView v=text(p,n);v.click.onClick(v);}
 static MainActivity activity(int page){MainActivity a=new MainActivity();a.root=new ViewGroup(a);ViewPager2 pager=new ViewPager2(a);pager.id=301;pager.current=page;View tabs=new View(a);tabs.id=302;View clear=new View(a);clear.id=303;a.mBinding.tabHeader=tabs;a.mBinding.ivClearMeg=clear;a.root.addView(pager);a.root.addView(tabs);a.root.addView(clear);return a;}
 public static class Item {public String getNoticeId(){return "1";}public String getTitle(){return "通知";}public String getPublisher(){return "教学处";}public String getContent(){return "内容";}}
 public static void main(String[] args)throws Exception{
  MainActivity a=activity(1);ViewPager2 pager=(ViewPager2)a.findViewById(301);NoticeShell.install(a,null);a.root.flush();Object p=shell(a);
  ok(text(p,"title").getText().toString().equals("系统消息"),"Initial SDK-selected page must set title before painting");
  ok(pager.callbacks.size()==1,"Exactly one page callback");
  LinearLayout body=(LinearLayout)field(p,"body"),reader=(LinearLayout)field(p,"readerHost"),list=(LinearLayout)field(p,"list");
  for(int i=0;i<40;i++){
   int page=i%2;click(p,page==0?(i%4==0?"navNotice":"railNotice"):(i%4==1?"navSystem":"railSystem"));
   body.resize(i%3==0?600:1280);
   ok(pager.current==page,"Click must change actual page");
   ok(text(p,"title").getText().toString().equals(page==0?"通知":"系统消息"),"Title must match actual page");
   ok(text(p,"navSystem").selected==(page==1)&&text(p,"railSystem").selected==(page==1),"Both navigation controls must match page");
   if(page==1)ok(reader.visibility==8&&list.visibility==0&&list.lp.width==0,"System page must use full-width list without reader");
  }
  ok(pager.smoothCalls==0&&pager.immediateCalls>0,"All shell changes must be immediate");
  click(p,"navNotice");body.resize(600);ok(NoticeShell.open(a,new Item()),"Reader opens");
  ok(reader.visibility==0&&list.visibility==8,"Compact reader shown");
  pager.setCurrentItem(1,false);ok(field(p,"selectedItem")==null&&reader.visibility==8&&list.visibility==0,"SDK-driven page changes must close obsolete reader and sync layout");
  TextView refresh=(TextView)((LinearLayout)a.root.getChildAt(0)).getChildAt(1);refresh.click.onClick(refresh);
  ok(a.fragments.get(1).refreshes==1&&a.fragments.get(0).refreshes==0,"Refresh must target system category");
  Bundle saved=new Bundle();NoticeShell.save(a,saved);ok(saved.getInt("m3e_section",-1)==1,"Saved actual page");
  a.resources.config.uiMode=32;NoticeShell.configuration(a);p=shell(a);a.root.flush();
  ok(pager.callbacks.size()==1&&pager.current==1&&text(p,"title").getText().toString().equals("系统消息"),"Theme rebuild must keep system page without duplicate listeners");
  NoticeShell.destroy(a);ok(pager.callbacks.isEmpty(),"Destroy must unregister callback");
  MainActivity restored=activity(0);ViewPager2 pager2=(ViewPager2)restored.findViewById(301);NoticeShell.install(restored,saved);restored.root.flush();Object p2=shell(restored);
  ok(pager2.current==1&&text(p2,"title").getText().toString().equals("系统消息"),"Saved system page must restore");NoticeShell.destroy(restored);
  Bundle savedZero=new Bundle();savedZero.putInt("m3e_section",0);MainActivity restoredZero=activity(1);ViewPager2 pagerZero=(ViewPager2)restoredZero.findViewById(301);NoticeShell.install(restoredZero,savedZero);restoredZero.root.flush();
  ok(pagerZero.current==0&&text(shell(restoredZero),"title").getText().toString().equals("通知"),"Saved notice page must override initial SDK system page");NoticeShell.destroy(restoredZero);
  System.out.println("Passed "+checks+" category navigation, initial state, resize, reader, refresh, restore and callback checks; Android rendering untested.");
 }
}'''
src = B/'tests/src'
out = B/'tests/classes'
out.mkdir(parents=True, exist_ok=True)
for name, value in files.items():
    path = src/name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding='utf-8')
sources = list(src.rglob('*.java')) + [R/'notice-m3e-src/com/hailiang/notice/m3e'/name for name in ('Data.java', 'LayoutPolicy.java', 'NoticeShell.java', 'PageNavigator.java')]
subprocess.run([str(JAVA), '-jar', str(ROOT/'tools/apk-patch/ecj.jar'), '-proc:none', '-source', '8', '-target', '8', '-encoding', 'UTF-8', '-nowarn', '-d', str(out)] + list(map(str, sources)), check=True)
result = subprocess.run([str(JAVA), '-cp', str(out), 'com.hailiang.notice.m3e.NavigationTest'], capture_output=True, text=True, encoding='utf-8')
print(result.stdout)
print(result.stderr)
result.check_returncode()
(B/'navigation-test-results.txt').write_text(result.stdout, encoding='utf-8')
