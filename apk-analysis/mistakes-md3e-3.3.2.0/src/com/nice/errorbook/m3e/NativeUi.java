package com.nice.errorbook.m3e;

import android.app.Activity;
import android.app.Dialog;
import android.content.Context;
import android.content.res.ColorStateList;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.os.Build;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.widget.LinearLayout;
import android.widget.TextView;

public final class NativeUi {
    public static int dp(Context c,float n){return Math.round(n*c.getResources().getDisplayMetrics().density);}
    public static GradientDrawable shape(Context c,int color,int radius) {
        GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(c,radius));return d;
    }
    public static TextView text(Context c,String value,int size,int color,boolean bold){
        TextView t=new TextView(c);t.setText(value);t.setTextSize(size);t.setTextColor(color);if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;
    }
    public static TextView button(Context c,String value,boolean filled){
        TextView t=text(c,value,16,Palette.argb(filled?Palette.ON_PRIMARY:Palette.ON_CONTAINER),true);
        t.setGravity(Gravity.CENTER);t.setPadding(dp(c,22),dp(c,12),dp(c,22),dp(c,12));t.setMinHeight(dp(c,52));
        t.setBackground(new RippleDrawable(ColorStateList.valueOf(0x306750a4),shape(c,Palette.argb(filled?Palette.PRIMARY:Palette.PRIMARY_CONTAINER),28),null));
        t.setClickable(true);t.setFocusable(true);return t;
    }
    public static void window(Activity a){
        Window w=a.getWindow();w.setStatusBarColor(Palette.argb(Palette.SURFACE));w.setNavigationBarColor(Palette.argb(Palette.SURFACE));
        int flags=w.getDecorView().getSystemUiVisibility();int bits=View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR|View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
        w.getDecorView().setSystemUiVisibility(Palette.dark()?flags&~bits:flags|bits);
    }
    public static LinearLayout column(Context c,int padding){LinearLayout l=new LinearLayout(c);l.setOrientation(1);l.setPadding(dp(c,padding),dp(c,padding),dp(c,padding),dp(c,padding));return l;}
    public static void row(LinearLayout parent,View view,int margin){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.topMargin=dp(parent.getContext(),margin);parent.addView(view,p);}
    public static void appearance(final Activity a){
        final Dialog dialog=new Dialog(a);LinearLayout body=column(a,28);body.setBackground(shape(a,Palette.argb(Palette.HIGH),32));
        row(body,text(a,"原生 MD3e 外观",26,Palette.argb(Palette.ON_SURFACE),true),0);
        row(body,text(a,"浅色与深色跟随系统；界面和弹窗使用同一套颜色。",15,Palette.argb(Palette.VARIANT),false),12);
        row(body,text(a,Build.VERSION.SDK_INT>=31?"可从系统壁纸提取主题色。":"当前系统使用默认紫色配色。",15,Palette.argb(Palette.VARIANT),false),8);
        if(Build.VERSION.SDK_INT>=31){
            TextView toggle=button(a,Palette.dynamic()?"壁纸取色：已开启":"壁纸取色：已关闭",false);row(body,toggle,24);
            toggle.setOnClickListener(new View.OnClickListener(){public void onClick(View v){a.getSharedPreferences("m3e",0).edit().putBoolean("dynamic",!Palette.dynamic()).apply();dialog.dismiss();a.recreate();}});
        }
        TextView close=button(a,"完成",true);row(body,close,24);close.setOnClickListener(new View.OnClickListener(){public void onClick(View v){dialog.dismiss();}});
        dialog.setContentView(body);dialog.show();Window w=dialog.getWindow();w.setBackgroundDrawableResource(android.R.color.transparent);
        w.setLayout(Math.min(dp(a,520),a.getResources().getDisplayMetrics().widthPixels-dp(a,48)),ViewGroup.LayoutParams.WRAP_CONTENT);
    }
}
