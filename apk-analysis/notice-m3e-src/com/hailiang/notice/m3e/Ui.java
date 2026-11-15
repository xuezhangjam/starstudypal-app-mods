package com.hailiang.notice.m3e;
import android.app.*;import android.content.*;import android.content.res.*;import android.graphics.*;import android.graphics.drawable.*;import android.view.*;import android.widget.*;import android.animation.TimeInterpolator;

public final class Ui {
 public static int dp(Context c,float n){return Math.round(c.getResources().getDisplayMetrics().density*n);}
 public static final class Colors {
  public final boolean dark;public final int primary,onPrimary,bg,surface,container,ink,muted,outline,tonal;
  public Colors(Context c){dark=(c.getResources().getConfiguration().uiMode&48)==32;
   int p=dark?0xffd0bcff:0xff6750a4;try{int id=c.getResources().getIdentifier(dark?"system_accent1_200":"system_accent1_600","color","android");if(android.os.Build.VERSION.SDK_INT>=31&&id!=0)p=c.getResources().getColor(id);}catch(Exception ignored){}
   primary=p;onPrimary=luminance(p)>.42?0xff201923:0xffffffff;
   bg=dark?0xff141218:mix(p,0xffffffff,.035f);surface=dark?0xff1e1b23:0xffffffff;
   container=dark?mix(p,0xff211e28,.08f):mix(p,0xffffffff,.075f);tonal=dark?mix(p,0xff332b43,.15f):mix(p,0xffffffff,.18f);
   ink=dark?0xfff1edf7:0xff211d29;muted=dark?0xffc9c2d3:0xff625d6a;outline=dark?0xff514a5c:0xffded8e7;
  }
 }
 private static double luminance(int c){return .2126*channel(Color.red(c))+.7152*channel(Color.green(c))+.0722*channel(Color.blue(c));}
 private static double channel(int n){double f=n/255d;return f<=.04045?f/12.92:Math.pow((f+.055)/1.055,2.4);}
 public static int mix(int a,int b,float amount){return Color.rgb(Math.round(Color.red(a)*amount+Color.red(b)*(1-amount)),Math.round(Color.green(a)*amount+Color.green(b)*(1-amount)),Math.round(Color.blue(a)*amount+Color.blue(b)*(1-amount)));}
 public static GradientDrawable shape(Context c,int color,float radius){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(c,radius));return d;}
 public static Drawable ripple(Context c,int color,float radius){Drawable d=shape(c,color,radius);try{return (Drawable)Class.forName("android.graphics.drawable.RippleDrawable").getConstructor(ColorStateList.class,Drawable.class,Drawable.class).newInstance(ColorStateList.valueOf(new Colors(c).primary&0x00ffffff|0x24000000),d,null);}catch(Exception e){return d;}}
 public static TextView text(Context c,CharSequence s,float size,int color,boolean bold){TextView t=new TextView(c);t.setText(s);t.setTextSize(size);t.setTextColor(color);t.setTypeface(Typeface.create(bold?"sans-serif-medium":"sans-serif",Typeface.NORMAL));t.setIncludeFontPadding(false);return t;}
 public static TextView button(Context c,String title,boolean filled,View.OnClickListener click){Colors p=new Colors(c);TextView t=text(c,title,14,filled?p.onPrimary:p.primary,true);t.setGravity(Gravity.CENTER);t.setMinHeight(dp(c,48));t.setPadding(dp(c,18),dp(c,12),dp(c,18),dp(c,12));t.setBackgroundDrawable(ripple(c,filled?p.primary:p.tonal,24));t.setOnClickListener(click);t.setFocusable(true);return t;}
 public static LinearLayout column(Context c){LinearLayout l=new LinearLayout(c);l.setOrientation(LinearLayout.VERTICAL);return l;}
 public static LinearLayout row(Context c){LinearLayout l=new LinearLayout(c);l.setOrientation(LinearLayout.HORIZONTAL);l.setGravity(Gravity.CENTER_VERTICAL);return l;}
 public static ImageView icon(Context c,String name,int color,int size){ImageView i=new ImageView(c);i.setImageDrawable(new Symbol(name,color));i.setLayoutParams(new LinearLayout.LayoutParams(dp(c,size),dp(c,size)));i.setContentDescription(name);return i;}
 public static void inset(Activity a){try{Colors p=new Colors(a);a.getWindow().clearFlags(0x600);int flags=p.dark?0:android.os.Build.VERSION.SDK_INT>=23?0x2000:0;if(!p.dark&&android.os.Build.VERSION.SDK_INT>=26)flags|=0x10;a.getWindow().getDecorView().setSystemUiVisibility(flags);android.view.Window.class.getMethod("setStatusBarColor",int.class).invoke(a.getWindow(),p.bg);android.view.Window.class.getMethod("setNavigationBarColor",int.class).invoke(a.getWindow(),p.bg);Class<?> w=Class.forName("androidx.core.view.WindowCompat");w.getMethod("setDecorFitsSystemWindows",android.view.Window.class,boolean.class).invoke(null,a.getWindow(),true);}catch(Exception ignored){}}
 public static void density(Resources resources){android.util.DisplayMetrics d=resources.getDisplayMetrics(),sys=Resources.getSystem().getDisplayMetrics();d.density=sys.density;d.densityDpi=sys.densityDpi;d.scaledDensity=d.density*resources.getConfiguration().fontScale;}
 public static void animate(View v){v.setAlpha(.6f);v.setTranslationY(dp(v.getContext(),8));v.animate().alpha(1).translationY(0).setDuration(280).setInterpolator(new Spring()).start();}
 private static class Spring implements TimeInterpolator {public float getInterpolation(float t){return t>=1?1:(float)(1-Math.exp(-7*t)*Math.cos(8*t));}}
 public static final class Symbol extends Drawable {
  final Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);final String name;final int color;
  Symbol(String n,int c){name=n;color=c;}
  public void draw(Canvas c){Rect b=getBounds();c.save();c.translate(b.left,b.top);c.scale(b.width()/24f,b.height()/24f);p.setColor(color);p.setStrokeWidth(1.8f);p.setStyle(Paint.Style.STROKE);p.setStrokeCap(Paint.Cap.ROUND);p.setStrokeJoin(Paint.Join.ROUND);
   if(name.equals("搜索")){c.drawCircle(10.5f,10.5f,6,p);c.drawLine(15,15,21,21,p);}
   else if(name.equals("返回")){c.drawLine(19,12,5,12,p);c.drawLine(5,12,11,6,p);c.drawLine(5,12,11,18,p);}
   else if(name.equals("刷新")){c.drawArc(new RectF(4,4,20,20),45,290,false,p);c.drawLine(20,4,20,10,p);c.drawLine(20,10,14,10,p);}
   else if(name.equals("系统")){c.drawRoundRect(new RectF(3,4,21,19),3,3,p);c.drawLine(7,9,17,9,p);c.drawLine(7,14,13,14,p);}
   else if(name.equals("阅读")){c.drawLine(5,12,10,17,p);c.drawLine(10,17,20,6,p);}
   else if(name.equals("附件")){Path q=new Path();q.moveTo(8,9);q.lineTo(8,17);q.cubicTo(8,23,18,23,18,17);q.lineTo(18,7);q.cubicTo(18,1,5,1,5,7);q.lineTo(5,17);c.drawPath(q,p);}
   else {Path q=new Path();q.moveTo(5,17);q.lineTo(7,14);q.lineTo(7,9);q.cubicTo(7,2,17,2,17,9);q.lineTo(17,14);q.lineTo(19,17);q.close();c.drawPath(q,p);c.drawArc(new RectF(9,17,15,22),0,180,false,p);}
   c.restore();
  }
  public void setAlpha(int a){p.setAlpha(a);}public void setColorFilter(ColorFilter f){p.setColorFilter(f);}public int getOpacity(){return PixelFormat.TRANSLUCENT;}
 }
}
