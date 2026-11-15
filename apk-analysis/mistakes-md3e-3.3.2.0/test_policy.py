"""Run real palette/photo policy code on JVM API fixtures; no Android rendering."""
from pathlib import Path
import json,subprocess
B=Path(__file__).resolve().parent;ROOT=B.parent.parent;T=ROOT/'tools/apk-patch'
JAVA=T/'java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe'
sources={
'android/os/Build.java':'''package android.os;public class Build{public static class VERSION{public static int SDK_INT=29;}}''',
'android/content/res/Configuration.java':'''package android.content.res;public class Configuration{public static final int UI_MODE_NIGHT_MASK=48,UI_MODE_NIGHT_YES=32;public int uiMode=16;}''',
'android/content/SharedPreferences.java':'''package android.content;public interface SharedPreferences{boolean getBoolean(String key,boolean fallback);}''',
'android/content/res/Resources.java':'''package android.content.res;import java.util.*;public class Resources{public static class Theme{}public Configuration config=new Configuration();public Map<String,Integer> ids=new HashMap<String,Integer>();public Map<Integer,Integer> colors=new HashMap<Integer,Integer>();public Configuration getConfiguration(){return config;}public int getIdentifier(String s,String t,String p){return ids.containsKey(s)?ids.get(s):0;}public int getColor(int id,Theme t){return colors.get(id);}public void color(String name,int color){int id=ids.containsKey(name)?ids.get(name):ids.size()+1;ids.put(name,id);colors.put(id,color);}}''',
'android/content/Context.java':'''package android.content;import android.content.res.Resources;public class Context{public Resources resources=new Resources();public boolean enabled=true;public Context getApplicationContext(){return this;}public Resources getResources(){return resources;}public Resources.Theme getTheme(){return new Resources.Theme();}public SharedPreferences getSharedPreferences(String key,int mode){return new SharedPreferences(){public boolean getBoolean(String key,boolean fallback){return enabled;}};}}''',
'androidx/compose/ui/graphics/ColorKt.java':'''package androidx.compose.ui.graphics;public class ColorKt{public static long Color(int value){return ((long)value&0xffffffffL)<<32;}public static long Color(long value){return (value&0xffffffffL)<<32;}}''',
'PolicyTest.java':'''import com.nice.errorbook.m3e.*;import android.content.Context;import android.os.Build;public class PolicyTest{
static int checks,cases;static void ok(boolean v){checks++;if(!v)throw new AssertionError("check "+checks);}static double linear(double s){s/=255d;return s<=.04045?s/12.92:Math.pow((s+.055)/1.055,2.4);}static double luminance(int c){return .2126*linear(c>>16&255)+.7152*linear(c>>8&255)+.0722*linear(c&255);}static double ratio(int a,int b){double x=luminance(a),y=luminance(b);return(Math.max(x,y)+.05)/(Math.min(x,y)+.05);}static int rgb(long c){return(int)(c>>>32);}
public static void main(String[] args){
Context c=new Context();Build.VERSION.SDK_INT=29;
for(int mode:new int[]{16,32}){c.resources.config.uiMode=mode;Palette.init(c);ok(Palette.dark()==(mode==32));ok(!Palette.dynamic());
for(int[] pair:new int[][]{{Palette.SURFACE,Palette.ON_SURFACE},{Palette.CONTAINER,Palette.ON_SURFACE},{Palette.HIGH,Palette.ON_SURFACE},{Palette.PRIMARY,Palette.ON_PRIMARY},{Palette.PRIMARY_CONTAINER,Palette.ON_CONTAINER},{Palette.SURFACE,Palette.VARIANT}})ok(ratio(Palette.argb(pair[0]),Palette.argb(pair[1]))>=4.5);
ok(rgb(Palette.onSurface())==Palette.argb(Palette.ON_SURFACE));ok(rgb(Palette.primaryContainer())==Palette.argb(Palette.PRIMARY_CONTAINER));
for(int semantic:new int[]{0xff00ac77,0xffff4757,0xffffb800,0xff87ceeb,0xffdda0dd,0})ok(Palette.map(semantic)==semantic);
ok(Palette.map(0x80000000)==0x80000000);ok(Palette.map(0x33000000)==0x33000000);
ok(Palette.map(0xffffe411)==Palette.argb(Palette.PRIMARY_CONTAINER));ok(Palette.map(0xff6968ff)==Palette.argb(Palette.PRIMARY));ok(Palette.map(0xff000000)==Palette.argb(Palette.ON_SURFACE));ok(Palette.map(0xffffffff)==Palette.argb(Palette.SURFACE));}
// Wallpaper/resource overlay changes must invalidate the cached palette even
// while mode and the dynamic-color preference stay the same.
Build.VERSION.SDK_INT=31;c.resources.config.uiMode=16;c.resources.color("system_accent1_600",0xff006a6a);Palette.init(c);ok(Palette.dynamic());ok(Palette.argb(Palette.PRIMARY)==0xff006a6a);
c.resources.color("system_accent1_600",0xff7d5260);ok(Palette.argb(Palette.PRIMARY)==0xff7d5260);c.enabled=false;ok(Palette.argb(Palette.PRIMARY)==0xff6750a4);
for(float radius:new float[]{0,1,2,8,12,16,20,24,28,40,48,999}){float actual=Palette.corner(radius);ok(actual>=0);ok(radius>40?actual==radius:actual>=radius);}
int[] dimensions={1,2,63,800,1280,1920,2048,2736,3072,4000,4096,4097,6000,12000,65535,Integer.MAX_VALUE};
for(int w:dimensions)for(int h:dimensions){cases++;int[] s=PhotoPolicy.target(w,h);ok(s[0]>0&&s[1]>0);ok(s[0]<=w&&s[1]<=h);ok(s[0]<=4096&&s[1]<=4096);ok((long)s[0]*s[1]<=8000000L);ok(Math.abs((double)s[0]*h-(double)s[1]*w)<=(double)w+h+1);int[] rot=PhotoPolicy.target(h,w);ok(s[0]==rot[1]&&s[1]==rot[0]);if(w<=4096&&h<=4096&&(long)w*h<=8000000L)ok(s[0]==w&&s[1]==h);}
for(int[] invalid:new int[][]{{0,1},{1,0},{-1,100},{100,-1}}){boolean rejected=false;try{PhotoPolicy.target(invalid[0],invalid[1]);}catch(IllegalArgumentException good){rejected=true;}ok(rejected);}
for(int max:new int[]{0,1,3,9})for(int have=0;have<12;have++){int left=PhotoPolicy.remaining(max,have);ok(left>=0);ok(left<=max);ok(left+Math.min(have,max)==max);}
ok(PhotoPolicy.remaining(Integer.MIN_VALUE,Integer.MAX_VALUE)==0);ok(PhotoPolicy.remaining(3,-1)==3);
System.out.println("PASS "+checks+" assertions; "+cases+" photo dimension scenarios, palette contrast, dynamic color refresh, semantic colors, corners and quotas");
}}
'''
}
api=B/'test-api'
for name,text in sources.items():p=api/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,'utf-8')
classes=B/'test-classes';classes.mkdir(exist_ok=True)
subprocess.run([str(JAVA),'-jar',str(T/'ecj.jar'),'-proc:none','-source','8','-target','8','-warn:none','-encoding','UTF-8','-d',str(classes),*map(str,api.rglob('*.java')),str(B/'src/com/nice/errorbook/m3e/Palette.java'),str(B/'src/com/nice/errorbook/m3e/PhotoPolicy.java')],check=True)
r=subprocess.run([str(JAVA),'-cp',str(classes),'PolicyTest'],capture_output=True,text=True,encoding='utf-8');print(r.stdout);print(r.stderr);r.check_returncode()
(B/'policy-test-results.txt').write_text(r.stdout,'utf-8')
