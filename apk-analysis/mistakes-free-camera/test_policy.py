"""Exercise real photo policy on JVM fixtures, without claiming Android rendering."""
from pathlib import Path
import subprocess,json
B=Path(__file__).resolve().parent;ROOT=B.parent.parent;T=ROOT/'tools/apk-patch'
JAVA=T/'java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe'
sources={
'android/graphics/Bitmap.java':'package android.graphics;public class Bitmap{int w,h;public Bitmap(int x,int y){w=x;h=y;}public int getWidth(){return w;}public int getHeight(){return h;}}',
'android/graphics/PointF.java':'package android.graphics;public class PointF{public final float x,y;public PointF(float a,float b){x=a;y=b;}}',
'android/graphics/drawable/Drawable.java':'package android.graphics.drawable;public class Drawable{public Drawable mutate(){return this;}public void setTint(int value){}}',
'android/widget/TextView.java':'package android.widget;import android.graphics.drawable.Drawable;public class TextView{public void setText(String text){}public void setTextColor(int color){}public Drawable getBackground(){return null;}}',
'com/hailiang/xxb/ai/camera/core/scan/EdgeArea.java':'package com.hailiang.xxb.ai.camera.core.scan;import android.graphics.PointF;import java.util.List;public class EdgeArea{public final int w,h;public final List<PointF> points;public EdgeArea(int width,int height,List<PointF> list){w=width;h=height;points=list;}}',
'com/hailiang/xxb/ai/camera/view/SmartCameraPreview.java':'package com.hailiang.xxb.ai.camera.view;import android.widget.TextView;public class SmartCameraPreview{public TextView getStatusTv(){return new TextView();}public void clearPoints(){}}',
'com/nice/errorbook/m3e/Palette.java':'package com.nice.errorbook.m3e;public class Palette{public static final int ON_CONTAINER=6,PRIMARY_CONTAINER=5;public static int argb(int role){return 0;}}',
'CameraPolicyTest.java':'''import android.graphics.*;import com.hailiang.xxb.ai.camera.core.scan.EdgeArea;import com.nice.errorbook.m3e.CameraCapturePolicy;public class CameraPolicyTest{
static int count,cases;static void ok(boolean value){count++;if(!value)throw new AssertionError("check "+count);}public static void main(String[] args){
int[][] sizes={{1,1},{2,3},{3,2},{320,240},{240,320},{800,1066},{1066,800},{1280,800},{1920,1080},{1080,1920},{4032,3024},{3024,4032},{8000,6000},{6000,8000},{16000,1000},{1000,16000}};
for(int[] size:sizes){int w=size[0],h=size[1];EdgeArea e=CameraCapturePolicy.full(new Bitmap(w,h));cases++;ok(e.w==w);ok(e.h==h);ok(e.points.size()==4);float[][] wanted={{0,0},{w,0},{w,h},{0,h}};for(int i=0;i<4;i++){ok(e.points.get(i).x==wanted[i][0]);ok(e.points.get(i).y==wanted[i][1]);}float area=0;for(int i=0;i<4;i++){PointF a=e.points.get(i),b=e.points.get((i+1)%4);area+=a.x*b.y-b.x*a.y;}ok(area==2f*w*h);}
for(int[] size:new int[][]{{0,1},{1,0},{-1,10},{10,-1}}){boolean threw=false;try{CameraCapturePolicy.full(new Bitmap(size[0],size[1]));}catch(IllegalArgumentException e){threw=true;}ok(threw);}boolean threw=false;try{CameraCapturePolicy.full(null);}catch(IllegalArgumentException e){threw=true;}ok(threw);
System.out.println("PASS "+count+" assertions; "+cases+" full-frame photo scenarios and invalid input rejection; JVM fixtures, no Android device");}}
'''
}
api=B/'test-api'
for name,source in sources.items():
 p=api/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(source,'utf-8')
classes=B/'test-classes';classes.mkdir(exist_ok=True)
commands=[ [JAVA,'-jar',T/'ecj.jar','-proc:none','-source','8','-target','8','-warn:none','-encoding','UTF-8','-d',classes,*list(api.rglob('*.java')),*list((B/'src').rglob('*.java'))], [JAVA,'-cp',classes,'CameraPolicyTest'] ]
for cmd in commands:
 p=subprocess.run(list(map(str,cmd)),capture_output=True,text=True,encoding='utf-8',errors='replace');p.check_returncode()
 if p.stdout:print(p.stdout,end='')
(B/'policy-test-results.txt').write_text(p.stdout,'utf-8')
