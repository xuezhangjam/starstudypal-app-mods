package com.hljzjx.md3.updates;

import android.app.*;
import android.content.*;
import android.content.pm.*;
import android.database.Cursor;
import android.graphics.Color;
import android.graphics.drawable.*;
import android.net.Uri;
import android.os.*;
import android.view.*;
import android.widget.*;
import com.hailiang.launcher.data.bean.response.AppHtmlListBean;
import com.hailiang.launcher.common.download.app.AppUpdateTask;
import com.hailiang.launcher.update.LauncherUpdateManager;
import com.hljzjx.launch.ui.main.MainActivity;
import com.hljzjx.md3.SkinController;
import com.hljzjx.md3.ThemeController;
import com.jchou.commonlibrary.model.UserData;
import java.lang.ref.WeakReference;
import java.net.URI;
import java.security.MessageDigest;
import java.util.*;

/** Download-only updates: immutable offers, public Downloads, no installer. */
public final class ManualUpdates {
    private static final Handler UI = new Handler(Looper.getMainLooper());
    private static final LinkedHashMap<String,Offer> OFFERS = new LinkedHashMap<String,Offer>();
    private static final Set<String> SEEN = new HashSet<String>();
    private static WeakReference<Activity> host = new WeakReference<Activity>(null);
    private static WeakReference<MainActivity> main = new WeakReference<MainActivity>(null);
    private static Dialog current;
    private static boolean initialized;
    private static long owner = Long.MIN_VALUE;
    private static long revision;
    private static long lastNameTime;
    private ManualUpdates() {}

    static final class Offer {
        final String pkg,name,version,url;
        final long code,user;
        Offer(String p,String n,String v,long c,String u,long who) {
            pkg=p==null?"":p; name=n==null||n.length()==0?pkg:n;
            version=v==null?"":v;code=c;url=u==null?"":u;user=who;
        }
        String key(){return pkg+"\n"+code+"\n"+url;}
    }
    static boolean validUrl(String value) {
        if(value==null || !value.equals(value.trim()))return false;
        try {URI u=new URI(value);return ("https".equalsIgnoreCase(u.getScheme())||"http".equalsIgnoreCase(u.getScheme()))
                &&u.getHost()!=null&&u.getHost().length()>0&&u.getRawUserInfo()==null;}
        catch(Exception invalid){return false;}
    }
    static String filename(Offer o,long when) {
        String n=o.name.replaceAll("[\\\\/:*?\"<>|\\p{Cntrl}]","_").replaceAll("^[. ]+|[. ]+$","");
        if(n.length()==0)n="应用更新";
        if(n.length()>20)n=n.substring(0,20);
        return n+"-"+Math.max(0,o.code)+"-"+when+".apk";
    }
    private static String digest(String s) {
        try {byte[] b=MessageDigest.getInstance("SHA-256").digest(s.getBytes("UTF-8"));StringBuilder out=new StringBuilder();
            for(byte v:b)out.append(String.format(Locale.ROOT,"%02x",v&255));return out.toString();}
        catch(Exception impossible){throw new IllegalStateException(impossible);}
    }
    private static boolean active(Activity a){return a!=null&&!a.isFinishing()&&!a.isDestroyed();}
    private static void account() {
        long id=UserData.getUserId();
        if(owner!=id){owner=id;OFFERS.clear();SEEN.clear();revision++;close();}
    }
    private static void close(){Dialog d=current;current=null;if(d!=null)d.dismiss();}
    private static boolean newer(Context c,Offer o,boolean missing) {
        if(o.pkg.length()==0||o.code<0||!validUrl(o.url))return false;
        try{return c.getPackageManager().getPackageInfo(o.pkg,512).getLongVersionCode()<o.code;}
        catch(PackageManager.NameNotFoundException absent){return missing;}
        catch(Exception unavailable){return false;}
    }
    public static void init(Application app) {
        if(initialized||app==null)return;initialized=true;
        app.registerActivityLifecycleCallbacks(new Application.ActivityLifecycleCallbacks(){
            public void onActivityCreated(Activity a,Bundle b){}
            public void onActivityStarted(Activity a){}
            public void onActivityStopped(Activity a){}
            public void onActivitySaveInstanceState(Activity a,Bundle b){}
            public void onActivityResumed(Activity a){
                account();String name=a.getClass().getName();
                if(a instanceof MainActivity)main=new WeakReference<MainActivity>((MainActivity)a);
                if(a instanceof MainActivity||name.equals("com.hljzjx.launch.ui.personcenter.PersonCenterActivity")) {
                    host=new WeakReference<Activity>(a);schedulePrompt();
                }
            }
            public void onActivityPaused(Activity a){if(host.get()==a){host.clear();close();}}
            public void onActivityDestroyed(Activity a){if(host.get()==a){host.clear();close();}if(main.get()==a)main.clear();}
        });
    }
    private static Offer bean(AppHtmlListBean b,long user) {
        if(b==null||b.isWeb()||b.needDelete())return null;
        return new Offer(b.getPackageName(),b.getAppName(),b.getVersionName(),b.getVersionCode(),b.getDownloadUrl(),user);
    }
    public static void detectBeans(Context c,List<AppHtmlListBean> list) {
        if(c==null||list==null)return;long user=UserData.getUserId();ArrayList<Offer> result=new ArrayList<Offer>();
        for(AppHtmlListBean b:list){Offer o=bean(b,user);if(o!=null&&newer(c,o,false))result.add(o);}
        publish(c,result,user);
    }
    public static void detectTasks(Context c,List<AppUpdateTask> list) {
        if(c==null||list==null)return;long user=UserData.getUserId();ArrayList<Offer> result=new ArrayList<Offer>();
        for(AppUpdateTask t:list)if(t!=null&&t.getDispenseType()!=2){
            Offer o=new Offer(t.getPackageName(),t.getAppName(),t.getVersionName(),t.getVersionCode(),t.getDownloadUrl(),user);
            if(newer(c,o,false))result.add(o);
        }
        publish(c,result,user);
    }
    private static void publish(final Context c,final List<Offer> found,final long user) {
        UI.post(new Runnable(){public void run(){account();if(user!=owner)return;
            for(Offer o:found){OFFERS.put(o.pkg,o);}schedulePrompt();}});
    }
    private static void schedulePrompt(){UI.post(new Runnable(){public void run(){
        account();Activity a=host.get();if(!active(a)||current!=null||owner<=0)return;
        boolean fresh=false;
        for(Offer o:OFFERS.values())if(newer(a,o,false)&&!SEEN.contains(o.key())){fresh=true;break;}
        if(fresh)showCenter(a,false);
    }});}
    public static void offerBean(final Context c,AppHtmlListBean b,final boolean explicit) {
        if(c==null)return;final long user=UserData.getUserId();final Offer o=bean(b,user);
        if(o==null)return;
        UI.post(new Runnable(){public void run(){account();if(user!=owner)return;
            if(!validUrl(o.url)){if(explicit)toast(c,"更新没有有效的 HTTP/HTTPS 下载链接");return;}
            if(!newer(c,o,true)){if(explicit)toast(c,"当前已是最新版本");return;}
            OFFERS.put(o.pkg,o);
            Activity a=host.get();
            if(active(a)&&explicit){showOffer(a,o);}else schedulePrompt();
        }});
    }
    public static void bindSettings(final Activity a) {
        int row=a.getResources().getIdentifier("btn_check_update","id",a.getPackageName());
        View v=a.findViewById(row);
        if(v!=null)v.setOnClickListener(new View.OnClickListener(){public void onClick(View w){account();showCenter(a,true);}});
        int label=a.getResources().getIdentifier("tv_check_update","id",a.getPackageName());
        View text=a.findViewById(label);if(text instanceof TextView)((TextView)text).setText("应用更新（仅下载）");
    }
    private static int dp(Activity a,int n){return Math.round(n*a.getResources().getDisplayMetrics().density);}
    private static int color(Activity a,String name,int fallback){int id=a.getResources().getIdentifier(name,"color",a.getPackageName());return id==0?fallback:a.getColor(id);}
    private static final class Palette {
        final int bg,row,text,muted,accent,onAccent;
        Palette(Activity a){boolean stock=SkinController.mode(a)==1;boolean dark=stock||ThemeController.night(a)==32;
            bg=stock?0xff303747:color(a,"md3_surface_container",dark?0xff2b2930:0xfff3edf7);
            row=stock?0xff353a49:color(a,"md3_surface_container_high",dark?0xff36343b:0xffe8e0eb);
            text=stock?0xfff5f6fa:color(a,"md3_on_surface",dark?0xffe6e0e9:0xff1d1b20);
            muted=stock?0xffc7cdd8:color(a,"md3_on_surface_variant",dark?0xffcac4d0:0xff49454f);
            accent=stock?0xffffdf92:color(a,"md3_primary",dark?0xffd0bcff:0xff6750a4);
            onAccent=stock?0xff352900:color(a,"md3_on_primary",dark?0xff381e72:0xffffffff);
        }
    }
    private static GradientDrawable shape(Activity a,int color,int radius){GradientDrawable g=new GradientDrawable();g.setColor(color);g.setCornerRadius(dp(a,radius));return g;}
    private static TextView text(Activity a,String s,int size,int color){TextView t=new TextView(a);t.setText(s);t.setTextSize(size);t.setTextColor(color);return t;}
    private static void button(Activity a,LinearLayout box,String title,Palette p,boolean filled,final Runnable action){
        TextView v=text(a,title,16,filled?p.onAccent:p.text);v.setGravity(Gravity.CENTER_VERTICAL);v.setPadding(dp(a,18),dp(a,10),dp(a,18),dp(a,10));
        v.setMinHeight(dp(a,48));v.setBackground(shape(a,filled?p.accent:p.row,24));
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.topMargin=dp(a,8);box.addView(v,lp);
        v.setOnClickListener(new View.OnClickListener(){public void onClick(View w){action.run();}});
    }
    private static LinearLayout panel(final Activity a,String title,Palette p){
        close();Dialog d=new Dialog(a);d.requestWindowFeature(Window.FEATURE_NO_TITLE);d.setCancelable(true);d.setCanceledOnTouchOutside(true);
        ScrollView scroll=new ScrollView(a);LinearLayout box=new LinearLayout(a);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(a,24),dp(a,24),dp(a,24),dp(a,20));box.setBackground(shape(a,p.bg,28));scroll.addView(box);
        TextView heading=text(a,title,24,p.text);heading.setPadding(0,0,0,dp(a,12));box.addView(heading);d.setContentView(scroll);current=d;d.show();
        Window w=d.getWindow();if(w!=null){w.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));w.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);WindowManager.LayoutParams lp=w.getAttributes();lp.dimAmount=.32f;w.setAttributes(lp);
            int width=Math.min(dp(a,560),Math.max(dp(a,240),a.getWindow().getDecorView().getWidth()-dp(a,32)));
            w.setLayout(width,ViewGroup.LayoutParams.WRAP_CONTENT);}
        d.setOnDismissListener(new DialogInterface.OnDismissListener(){public void onDismiss(DialogInterface d){if(current==d)current=null;}});
        return box;
    }
    private static boolean still(Activity a,Offer o){account();return active(a)&&o.user==owner&&host.get()==a;}
    private static void showCenter(final Activity a,boolean manual){
        if(!active(a))return;final long user=owner;final long gen=++revision;Palette p=new Palette(a);LinearLayout box=panel(a,"应用更新",p);
        ArrayList<Offer> list=new ArrayList<Offer>();for(Offer o:OFFERS.values())if(o.user==user&&newer(a,o,false))list.add(o);
        for(final Offer o:list){SEEN.add(o.key());button(a,box,o.name+"  "+o.version,p,false,new Runnable(){public void run(){if(still(a,o)&&gen==revision)showOffer(a,o);}});}
        if(list.isEmpty())box.addView(text(a,"暂无已检测到的应用更新",16,p.muted));
        box.addView(text(a,"APK 保存到系统 Download 文件夹，安装由你手动决定。",14,p.muted));
        button(a,box,"刷新应用更新",p,true,new Runnable(){public void run(){
            account();if(owner!=user||gen!=revision||host.get()!=a||!active(a))return;close();MainActivity m=main.get();if(active(m))m.requestAppListAndControl(true);
            LauncherUpdateManager.requestLaunchVersionWithCheckDialog();toast(a,"正在检查更新");
        }});
        button(a,box,"查看系统下载",p,false,new Runnable(){public void run(){try{a.startActivity(new Intent(DownloadManager.ACTION_VIEW_DOWNLOADS));}catch(Exception e){toast(a,"请在文件应用中打开下载文件夹");}}});
        button(a,box,manual?"关闭":"稍后更新",p,false,new Runnable(){public void run(){close();}});
    }
    private static void showOffer(final Activity a,final Offer o){
        if(!active(a))return;SEEN.add(o.key());final long gen=++revision;Palette p=new Palette(a);LinearLayout box=panel(a,o.name+" 更新",p);
        box.addView(text(a,"新版本："+o.version+"（"+o.code+"）",16,p.text));
        box.addView(text(a,"下载到 Download 文件夹后，可自行选择何时安装。",14,p.muted));
        button(a,box,"下载 APK",p,true,new Runnable(){public void run(){if(still(a,o)&&gen==revision&&download(a,o))close();}});
        button(a,box,"浏览器打开下载链接",p,false,new Runnable(){public void run(){if(still(a,o)&&gen==revision&&browser(a,o.url))close();}});
        button(a,box,"稍后更新",p,false,new Runnable(){public void run(){close();}});
    }
    static synchronized boolean download(Context c,Offer o){
        if(!validUrl(o.url)) {toast(c,"下载链接无效");return false;}
        try {
            DownloadManager dm=(DownloadManager)c.getSystemService(Context.DOWNLOAD_SERVICE);if(dm==null)throw new IllegalStateException();
            SharedPreferences saved=c.getSharedPreferences("mod_apk_downloads",0);String key=digest(o.key());long old=saved.getLong(key,-1);
            if(old>=0){Cursor cursor=dm.query(new DownloadManager.Query().setFilterById(old));
                if(cursor!=null){try{if(cursor.moveToFirst()){int s=cursor.getInt(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS));
                    if(s!=DownloadManager.STATUS_FAILED){toast(c,s==DownloadManager.STATUS_SUCCESSFUL?"此版本已下载，可在系统下载中查看":"此版本正在系统下载队列中");return true;}
                }}finally{cursor.close();}}
            }
            long when=Math.max(System.currentTimeMillis(),lastNameTime+1);lastNameTime=when;
            String name=filename(o,when);DownloadManager.Request request=new DownloadManager.Request(Uri.parse(o.url));
            request.setTitle(o.name+" "+o.version);request.setDescription("APK 仅下载，安装由你手动决定");
            request.setMimeType("application/vnd.android.package-archive");request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS,name);
            long id=dm.enqueue(request);saved.edit().putLong(key,id).apply();toast(c,"已加入系统下载：Download/"+name);return true;
        } catch(Exception unavailable){toast(c,"无法加入系统下载，请使用浏览器打开下载链接");return false;}
    }
    static boolean browser(Activity a,String url){
        if(!validUrl(url)){toast(a,"下载链接无效");return false;}
        try{Intent web=new Intent(Intent.ACTION_VIEW,Uri.parse(url));web.addCategory(Intent.CATEGORY_BROWSABLE);
            web.setSelector(new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_APP_BROWSER));a.startActivity(web);return true;}
        catch(Exception unavailable){toast(a,"未找到可用浏览器，或系统禁止打开链接");return false;}
    }
    private static void toast(Context c,String s){Toast.makeText(c,s,Toast.LENGTH_LONG).show();}
}
