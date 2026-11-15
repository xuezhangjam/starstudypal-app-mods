package com.nice.errorbook.m3e;

import android.content.Context;
import android.content.res.Configuration;
import android.os.Build;
import androidx.compose.ui.graphics.ColorKt;

/** Native View and Compose share one system-derived, contrast-paired palette. */
public final class Palette {
    private static Context context;
    private static int cacheKey = -1;
    private static int[] colors;
    public static final int SURFACE=0, CONTAINER=1, HIGH=2, PRIMARY=3, ON_PRIMARY=4,
            PRIMARY_CONTAINER=5, ON_CONTAINER=6, ON_SURFACE=7, VARIANT=8, OUTLINE=9;
    public static void init(Context ctx) { context=ctx.getApplicationContext(); cacheKey=-1; }
    public static boolean dark() { return context!=null && (context.getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK)==Configuration.UI_MODE_NIGHT_YES; }
    public static boolean dynamic() { return Build.VERSION.SDK_INT>=31 && (context==null || context.getSharedPreferences("m3e",0).getBoolean("dynamic",true)); }
    private static int system(String name,int fallback) {
        if(context==null || Build.VERSION.SDK_INT<31)return fallback;
        int id=context.getResources().getIdentifier(name,"color","android");
        return id==0?fallback:context.getResources().getColor(id,context.getTheme());
    }
    public static synchronized int argb(int role) {
        boolean night=dark(),dyn=dynamic();int key=((night?1:0)|(dyn?2:0))*31+(dyn?system("system_accent1_600",0):0);
        if(colors==null || key!=cacheKey) {
            colors=night?new int[]{0xff141218,0xff211f26,0xff2b2930,0xffd0bcff,0xff381e72,0xff4f378b,0xffeaddff,0xffe6e0e9,0xffcac4d0,0xff49454f}
                        :new int[]{0xfffffbfe,0xfff3edf7,0xffece6f0,0xff6750a4,0xffffffff,0xffeaddff,0xff21005d,0xff1d1b20,0xff49454f,0xffcac4d0};
            if(dyn) {
                String[] tones=night?new String[]{"neutral1_900","neutral1_800","neutral2_800","accent1_200","accent1_800","accent1_700","accent1_100","neutral1_100","neutral2_200","neutral2_700"}
                                    :new String[]{"neutral1_10","neutral1_50","neutral2_100","accent1_600","accent1_0","accent1_100","accent1_900","neutral1_900","neutral2_700","neutral2_200"};
                for(int i=0;i<colors.length;i++)colors[i]=system("system_"+tones[i],colors[i]);
            }
            cacheKey=key;
        }
        return colors[role];
    }
    private static long packed(int role) { return ColorKt.Color(argb(role)); }
    public static long surface(){return packed(SURFACE);} public static long container(){return packed(CONTAINER);}
    public static long high(){return packed(HIGH);} public static long primary(){return packed(PRIMARY);}
    public static long onPrimary(){return packed(ON_PRIMARY);} public static long primaryContainer(){return packed(PRIMARY_CONTAINER);}
    public static long onContainer(){return packed(ON_CONTAINER);} public static long onSurface(){return packed(ON_SURFACE);}
    public static long variant(){return packed(VARIANT);} public static long outline(){return packed(OUTLINE);}
    public static long paperWhite(){return ColorKt.Color(0xffffffff);}
    public static long paperBlack(){return ColorKt.Color(0xff000000);}
    public static long color(long value) {return value<Integer.MIN_VALUE || value>0xffffffffL?ColorKt.Color(value):color((int)value);}
    public static long color(int value) {return ColorKt.Color(map(value));}
    public static int map(int value) {
        int alpha=value>>>24,r=(value>>>16)&255,g=(value>>>8)&255,b=value&255;
        if(alpha==0)return value;
        int role=-1;
        if(value==0xffffe411 || value==0xfffde24f || value==0xffffec00 || value==0xfffff9e1)role=PRIMARY_CONTAINER;
        else if(value==0xff6968ff || value==0xff6868ff || value==0xff4f63ff)role=PRIMARY;
        else if(value==0xff8e9aaf)role=VARIANT;
        else if(r==g && g==b) {
            if(r==0 && alpha<255)return value; // preserve photo/dialog scrims
            role=r<70?ON_SURFACE:r<180?VARIANT:r<233?OUTLINE:r<255?CONTAINER:SURFACE;
        }
        if(role<0)return value; // semantic success/error and subject colors stay intact
        return (argb(role)&0x00ffffff)|(alpha<<24);
    }
    public static float corner(float value) {
        if(value<=2 || value>40)return value;
        return value<=8?12:value<=12?20:value<=16?24:value<=20?28:Math.max(value,32f);
    }
}
