"""Compile-only Android view surface, also instrumented for picker UI assertions.

These classes are excluded from the APK; the device supplies real Android APIs.
"""
CUSTOM_VIEW_STUBS={
'android/content/Context.java':'''package android.content;import android.content.res.*;
public class Context {public Resources resources=new Resources();public AssetManager assets=new AssetManager();
public Resources getResources(){return resources;}public AssetManager getAssets(){return assets;}}''',
'android/content/res/AssetManager.java':'''package android.content.res;import java.io.*;
public class AssetManager {public boolean fail;public InputStream open(String name)throws IOException {
if(fail)throw new IOException();return new ByteArrayInputStream(name.getBytes("UTF-8"));}}''',
'android/util/DisplayMetrics.java':'''package android.util; public class DisplayMetrics {
public float density=1f; public int widthPixels=1280,heightPixels=800;}''',
'android/content/res/Resources.java':'''package android.content.res; import android.util.DisplayMetrics;
public class Resources {public DisplayMetrics metrics=new DisplayMetrics(); public DisplayMetrics getDisplayMetrics(){return metrics;}}''',
'android/content/res/ColorStateList.java':'''package android.content.res; public class ColorStateList {public int color;
public static ColorStateList valueOf(int c){ColorStateList s=new ColorStateList();s.color=c;return s;}}''',
'android/graphics/Typeface.java':'''package android.graphics; public class Typeface {public static final int NORMAL=0;
public String family; public static Typeface create(String f,int s){Typeface t=new Typeface();t.family=f;return t;}}''',
'android/graphics/drawable/Drawable.java':'''package android.graphics.drawable;import java.io.InputStream;
public class Drawable {public String source;public static Drawable createFromStream(InputStream s,String name){
Drawable d=new Drawable();d.source=name;return d;}}''',
'android/graphics/drawable/ColorDrawable.java':'''package android.graphics.drawable; public class ColorDrawable extends Drawable {
public int color;public ColorDrawable(int c){color=c;}}''',
'android/graphics/drawable/GradientDrawable.java':'''package android.graphics.drawable; public class GradientDrawable extends Drawable {
public int color,strokeWidth,strokeColor;public float radius;public void setColor(int c){color=c;}
public void setCornerRadius(float r){radius=r;}public void setStroke(int w,int c){strokeWidth=w;strokeColor=c;}}''',
'android/graphics/drawable/RippleDrawable.java':'''package android.graphics.drawable; import android.content.res.ColorStateList;
public class RippleDrawable extends Drawable {public ColorStateList color;public Drawable mask;
public RippleDrawable(ColorStateList c,Drawable d,Drawable m){color=c;mask=m;}}''',
'android/view/Gravity.java':'''package android.view;public class Gravity {public static final int CENTER=17,CENTER_VERTICAL=16,END=8388613;}''',
'android/view/View.java':'''package android.view;import android.content.Context;import android.graphics.drawable.Drawable;
public class View {public static final int IMPORTANT_FOR_ACCESSIBILITY_NO=2;public interface OnClickListener {void onClick(View v);}public Context context;public Drawable background,foreground;
public int width=1280,height=800,minimumHeight;public int[] padding;public boolean clip,focusable,forceDark=true;public CharSequence description;
public OnClickListener click;public View(Context c){context=c;}public void setBackground(Drawable d){background=d;}
public void setForeground(Drawable d){foreground=d;}public void setPadding(int l,int t,int r,int b){padding=new int[]{l,t,r,b};}
public void setMinimumHeight(int h){minimumHeight=h;}public void setClipToOutline(boolean c){clip=c;}
public void setForceDarkAllowed(boolean b){forceDark=b;}
public void setImportantForAccessibility(int mode){}
public void setContentDescription(CharSequence s){description=s;}public void setFocusable(boolean f){focusable=f;}
public void setOnClickListener(OnClickListener l){click=l;}public int getWidth(){return width;}public int getHeight(){return height;}
public boolean performClick(){if(click==null)return false;click.onClick(this);return true;}}''',
'android/view/ViewGroup.java':'''package android.view;import android.content.Context;import java.util.*;
public class ViewGroup extends View {public List<View> children=new ArrayList<View>();public List<LayoutParams> params=new ArrayList<LayoutParams>();
public ViewGroup(Context c){super(c);}public static class LayoutParams {public int width,height;public LayoutParams(int w,int h){width=w;height=h;}}
public void addView(View v,LayoutParams p){children.add(v);params.add(p);}}''',
'android/widget/LinearLayout.java':'''package android.widget;import android.content.Context;import android.view.*;
public class LinearLayout extends ViewGroup {public static final int VERTICAL=1;public int orientation,gravity;
public LinearLayout(Context c){super(c);}public void setOrientation(int o){orientation=o;}public void setGravity(int g){gravity=g;}
public static class LayoutParams extends ViewGroup.LayoutParams {public int leftMargin,bottomMargin;public float weight;
public LayoutParams(int w,int h){super(w,h);}public LayoutParams(int w,int h,float f){super(w,h);weight=f;}}}''',
'android/widget/TextView.java':'''package android.widget;import android.content.Context;import android.graphics.Typeface;import android.view.View;
public class TextView extends View {public CharSequence text;public float textSize;public int textColor,gravity;public Typeface typeface;
public TextView(Context c){super(c);}public void setText(CharSequence t){text=t;}public void setTextSize(float s){textSize=s;}
public void setTextColor(int c){textColor=c;}public void setTypeface(Typeface t){typeface=t;}public void setGravity(int g){gravity=g;}}''',
'android/widget/ImageView.java':'''package android.widget;import android.content.Context;import android.content.res.ColorStateList;
import android.graphics.drawable.Drawable;import android.view.View;
public class ImageView extends View {public enum ScaleType {FIT_CENTER}public Drawable image;public ScaleType scale;
public ColorStateList tint;public ImageView(Context c){super(c);}public void setImageDrawable(Drawable d){image=d;}
public void setScaleType(ScaleType s){scale=s;}public void setImageTintList(ColorStateList c){tint=c;}}''',
'android/widget/ScrollView.java':'''package android.widget;import android.content.Context;import android.view.ViewGroup;
public class ScrollView extends ViewGroup {public boolean fill;public ScrollView(Context c){super(c);}public void setFillViewport(boolean f){fill=f;}}''',
'android/view/WindowManager.java':'''package android.view;public interface WindowManager {public static class LayoutParams {public static final int FLAG_DIM_BEHIND=2;}}''',
'android/view/Window.java':'''package android.view;import android.graphics.drawable.Drawable;
public class Window {public static final int FEATURE_NO_TITLE=1;public Drawable background;public int flags,gravity,width,height;public float dim;
public View decor=new View(null);public View getDecorView(){return decor;}public void setBackgroundDrawable(Drawable d){background=d;}
public void addFlags(int f){flags|=f;}public void setDimAmount(float d){dim=d;}public void setGravity(int g){gravity=g;}
public void setLayout(int w,int h){width=w;height=h;}}''',
'android/app/Dialog.java':'''package android.app;import android.content.Context;import android.view.*;import java.util.*;
public class Dialog {public static List<Dialog> shown=new ArrayList<Dialog>();public Window window=new Window();public View content;
public boolean noTitle,outside,dismissed;public Dialog(Context c){}public boolean requestWindowFeature(int f){noTitle=f==Window.FEATURE_NO_TITLE;return true;}
public void setCanceledOnTouchOutside(boolean b){outside=b;}public void setContentView(View v){content=v;}
public Window getWindow(){return window;}public void show(){shown.add(this);}public void dismiss(){dismissed=true;}}''',
'android/app/Activity.java':'''package android.app;import android.content.*;import android.content.pm.*;import android.view.Window;
public class Activity extends Context {public Window window=new Window();public boolean isFinishing(){return false;}public boolean isDestroyed(){return false;}
public Window getWindow(){return window;}public PackageManager getPackageManager(){return null;}public void startActivity(Intent i){}}''',
'com/hljzjx/md3/ThemeController.java':'''package com.hljzjx.md3;import android.content.Context;
public class ThemeController {public static int testNight=0x10;public static int night(Context c){return testNight;}public static Context wrap(Context c){return c;}}''',
'com/hljzjx/md3/SkinController.java':'''package com.hljzjx.md3;import android.content.Context;
public class SkinController {public static int testSkin=0;public static int mode(Context c){return testSkin;}}''',
}
