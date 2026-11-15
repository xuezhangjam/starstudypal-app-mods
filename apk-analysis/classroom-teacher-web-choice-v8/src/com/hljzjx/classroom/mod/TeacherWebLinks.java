package com.hljzjx.classroom.mod;

import android.app.Activity;
import android.app.Dialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.ColorDrawable;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.net.Uri;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import com.hailiang.common.util.AppRuntimeData;
import com.nice.room.ui.roomlive.interaction.impl.ThirdAppInteraction;
import com.nice.room.ui.roomlive.interaction.impl.ThirdAppInteraction.ExternalLinkInfo;
import java.lang.ref.WeakReference;
import java.net.URI;
import java.util.Locale;
import java.util.WeakHashMap;

/** Choice before teacher URL loading. The classroom option calls the original
 * URL/whitelist flow; the external option sends only the exact URL to a browser. */
public final class TeacherWebLinks {
    private static final WeakHashMap<ThirdAppInteraction,Choice> OPEN=new WeakHashMap<ThirdAppInteraction,Choice>();
    private static final WeakHashMap<ThirdAppInteraction,Ticket> LOADING=new WeakHashMap<ThirdAppInteraction,Ticket>();
    private TeacherWebLinks(){}
    private static int dp(Activity a,int value){return Math.round(value*a.getResources().getDisplayMetrics().density);}
    private static GradientDrawable shape(Activity a,int color,int radius){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(a,radius));return d;}
    private static void toast(Activity a,String text){if(a!=null && !a.isFinishing() && !a.isDestroyed())Toast.makeText(a,text,Toast.LENGTH_LONG).show();}

    /** true consumes URL opening until the user chooses a route; native apps
     * (including the existing AI portal) continue through the original code. */
    public static boolean offer(ThirdAppInteraction interaction){
        ExternalLinkInfo info=interaction.getAppInfo();String url=info==null?null:info.getAppId();
        if(url==null || !url.toLowerCase(Locale.ROOT).startsWith("http")){close(interaction);return false;}
        Activity a=interaction.getContext();
        Choice old=OPEN.get(interaction);
        if(old!=null && old.ticket.info==info && old.ticket.valid() && old.dialog.isShowing())return true;
        close(interaction);
        if(!validUrl(url)){toast(a,"网页链接无效，无法打开");return true;}
        try{
            Ticket ticket=new Ticket(interaction,info,a,url);
            if(!ticket.valid())return true;
            // Keep the ordinary teacher toolbar entry available after cancelling
            // or leaving for a browser; the native in-class page removes it.
            interaction.modKeepWebShortcut();
            Choice choice=new Choice(ticket);OPEN.put(interaction,choice);choice.show();
        }catch(RuntimeException unavailable){close(interaction);toast(a,"暂时无法显示打开方式，请从底栏重新打开");}
        return true;
    }
    private static boolean validUrl(String text){
        try{URI u=new URI(text);String scheme=u.getScheme();
            if(!("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme)) || u.isOpaque() || u.getRawAuthority()==null)return false;
            String host=Uri.parse(text).getHost();return host!=null && host.length()>0 && u.getPort()<=65535;
        }catch(Exception malformed){return false;}
    }
    /** Guard the original asynchronous whitelist callback against stale links,
     * ended activity, or another user/room. AI portal URLs use another path. */
    public static boolean allowNative(ThirdAppInteraction interaction,ExternalLinkInfo info){
        Ticket t=LOADING.get(interaction);if(t==null || t.info!=info)return false;
        LOADING.remove(interaction);return t.valid();
    }
    public static void close(ThirdAppInteraction interaction){
        LOADING.remove(interaction);Choice c=OPEN.remove(interaction);if(c!=null)c.dismiss();
    }
    private static final class Ticket {
        final WeakReference<ThirdAppInteraction> interaction;final WeakReference<Activity> owner;final WeakReference<View> decor;
        final ExternalLinkInfo info;final String url;final long user,room;
        Ticket(ThirdAppInteraction i,ExternalLinkInfo data,Activity a,String link){interaction=new WeakReference<ThirdAppInteraction>(i);owner=new WeakReference<Activity>(a);decor=new WeakReference<View>(a==null?null:a.getWindow().getDecorView());info=data;url=link;user=AppRuntimeData.getUserId();room=i.getRoomInfo().getClassroomId();}
        boolean valid(){ThirdAppInteraction i=interaction.get();Activity a=owner.get();View d=decor.get();
            try{return i!=null && a!=null && !a.isFinishing() && !a.isDestroyed() && d!=null && d.isAttachedToWindow()
                && a.getWindow().getDecorView()==d && i.getContext()==a && i.modCanOpenWeb(info) && url.equals(info.getAppId())
                && user>0 && user==AppRuntimeData.getUserId() && room==i.getRoomInfo().getClassroomId();}
            catch(RuntimeException unavailable){return false;}
        }
    }
    private static final class Choice implements DialogInterface.OnDismissListener,View.OnAttachStateChangeListener,View.OnLayoutChangeListener {
        final Ticket ticket;final Dialog dialog;boolean closed;int lastWidth;
        Choice(Ticket t){
            ticket=t;Activity a=t.owner.get();dialog=new Dialog(a);dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
            LinearLayout panel=new LinearLayout(a);panel.setOrientation(LinearLayout.VERTICAL);panel.setPadding(dp(a,24),dp(a,24),dp(a,24),dp(a,16));panel.setBackground(shape(a,0xff303034,28));
            TextView title=new TextView(a);title.setText("网页打开方式");title.setTextSize(23);title.setTextColor(Color.WHITE);title.setTypeface(Typeface.DEFAULT,Typeface.BOLD);panel.addView(title,new LinearLayout.LayoutParams(-1,-2));
            TextView site=new TextView(a);site.setText(Uri.parse(t.url).getHost());site.setSingleLine(true);site.setTextSize(14);site.setTextColor(0xffd6d7dc);LinearLayout.LayoutParams sp=new LinearLayout.LayoutParams(-1,-2);sp.topMargin=dp(a,8);panel.addView(site,sp);
            row(a,panel,"默认浏览器打开","使用系统默认浏览器",new View.OnClickListener(){public void onClick(View v){browser();}});
            row(a,panel,"课堂内打开","在课堂内查看网页",new View.OnClickListener(){public void onClick(View v){inClass();}});
            TextView cancel=new TextView(a);cancel.setText("取消");cancel.setTextSize(15);cancel.setTextColor(0xffd6d7dc);cancel.setGravity(Gravity.CENTER);cancel.setMinHeight(dp(a,48));cancel.setOnClickListener(new View.OnClickListener(){public void onClick(View v){dismiss();}});LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(-1,-2);cp.topMargin=dp(a,10);panel.addView(cancel,cp);
            ScrollView scroll=new ScrollView(a);scroll.addView(panel);dialog.setContentView(scroll);dialog.setOnDismissListener(this);
        }
        boolean current(){ThirdAppInteraction i=ticket.interaction.get();return !closed && i!=null && OPEN.get(i)==this && ticket.valid();}
        void show(){if(!current()){dismiss();return;}dialog.show();Window w=dialog.getWindow();w.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));w.getDecorView().setPadding(0,0,0,0);resize();View d=ticket.decor.get();d.addOnAttachStateChangeListener(this);d.addOnLayoutChangeListener(this);}
        void resize(){Activity a=ticket.owner.get();View d=ticket.decor.get();if(a==null || d==null)return;int width=d.getWidth();if(width<=0)width=a.getResources().getDisplayMetrics().widthPixels;int wanted=Math.min(dp(a,440),Math.max(1,width-dp(a,32)));if(lastWidth!=wanted){lastWidth=wanted;dialog.getWindow().setLayout(wanted,-2);}}
        void inClass(){
            if(!current()){dismiss();return;}ThirdAppInteraction i=ticket.interaction.get();
            LOADING.put(i,ticket);
            try{i.modOpenWebInClass(ticket.info);dismiss();}
            catch(RuntimeException unavailable){LOADING.remove(i);toast(ticket.owner.get(),"暂时无法在课堂内打开，请重试");}
        }
        void browser(){
            if(!current()){dismiss();return;}Activity a=ticket.owner.get();
            try{
                Intent target=new Intent(Intent.ACTION_VIEW,Uri.parse(ticket.url)).addCategory(Intent.CATEGORY_BROWSABLE);
                // Resolve a host-free web intent so a site's verified native app
                // does not replace the user's browser preference.
                ResolveInfo chosen=null;
                try{chosen=a.getPackageManager().resolveActivity(new Intent(Intent.ACTION_VIEW,Uri.parse("https://")).addCategory(Intent.CATEGORY_BROWSABLE),PackageManager.MATCH_DEFAULT_ONLY);}catch(RuntimeException hidden){/* A browser-only selector does not require package visibility. */}
                String pkg=chosen==null || chosen.activityInfo==null?null:chosen.activityInfo.packageName;
                if(pkg!=null && !pkg.equals("android") && !pkg.equals(a.getPackageName()))target.setPackage(pkg);
                else target.setSelector(new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_APP_BROWSER));
                a.startActivity(target);dismiss();
            }catch(RuntimeException missing){toast(a,"默认浏览器暂时无法打开，可选择课堂内打开");}
        }
        void dismiss(){dialog.dismiss();cleanup();}
        void cleanup(){if(closed)return;closed=true;ThirdAppInteraction i=ticket.interaction.get();if(i!=null && OPEN.get(i)==this)OPEN.remove(i);View d=ticket.decor.get();if(d!=null){d.removeOnAttachStateChangeListener(this);d.removeOnLayoutChangeListener(this);}}
        public void onDismiss(DialogInterface ignored){cleanup();}
        public void onViewAttachedToWindow(View view){}
        public void onViewDetachedFromWindow(View view){ThirdAppInteraction i=ticket.interaction.get();if(i!=null)LOADING.remove(i);dismiss();}
        public void onLayoutChange(View v,int l,int t,int r,int b,int ol,int ot,int or,int ob){if(!current())dismiss();else resize();}
    }
    private static void row(Activity a,LinearLayout parent,String name,String detail,View.OnClickListener click){
        LinearLayout row=new LinearLayout(a);row.setOrientation(LinearLayout.VERTICAL);row.setPadding(dp(a,18),dp(a,12),dp(a,18),dp(a,12));row.setMinimumHeight(dp(a,72));row.setBackground(new RippleDrawable(ColorStateList.valueOf(0x33ffffff),shape(a,0xff45454b,20),null));
        TextView title=new TextView(a);title.setText(name);title.setTextColor(Color.WHITE);title.setTextSize(18);title.setTypeface(Typeface.DEFAULT,Typeface.BOLD);row.addView(title,new LinearLayout.LayoutParams(-1,-2));TextView subtitle=new TextView(a);subtitle.setText(detail);subtitle.setTextColor(0xffd6d7dc);subtitle.setTextSize(13);row.addView(subtitle,new LinearLayout.LayoutParams(-1,-2));LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.topMargin=dp(a,14);parent.addView(row,p);row.setContentDescription(name);row.setOnClickListener(click);
    }
}
