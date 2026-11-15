"""Run production helper Java against observable API fixtures, without a tablet/server.

Fixtures model lifecycle, incoming protocol payloads and native width-fit coordinates.
They do not replace APK/ART, UI, MQTT, or server acceptance tests.
"""
from pathlib import Path
import json, subprocess
B=Path(__file__).resolve().parent;T=B.parent.parent/'tools/apk-patch'
JAVA=T/'java21/zulu21.52.203-ca-jre21.0.12.1-win_x64/bin/java.exe'

FIXTURES = {
'android/view/View.java': r'''
package android.view;
import java.util.*;
public class View {
 public interface OnLayoutChangeListener {void onLayoutChange(View v,int l,int t,int r,int b,int ol,int ot,int or,int ob);}
 public int id,width=1280,height=800;public View parent;public boolean attached=true;
 public Map<Integer,View> children=new HashMap<Integer,View>();
 public List<OnLayoutChangeListener> listeners=new ArrayList<OnLayoutChangeListener>();
 public List<Runnable> pending=new ArrayList<Runnable>();
 public int getId(){return id;}public int getWidth(){return width;}public int getHeight(){return height;}
 public Object getParent(){return parent;}public View getRootView(){return parent==null?this:parent.getRootView();}
 public boolean isAttachedToWindow(){return getRootView().attached;}
 @SuppressWarnings("unchecked") public <V extends View> V findViewById(int key){if(id==key)return(V)this;return(V)children.get(key);}
 public void addOnLayoutChangeListener(OnLayoutChangeListener l){listeners.add(l);}
 public boolean postDelayed(Runnable r,long delay){pending.add(r);return true;}
 public void resize(int w){int old=width;width=w;for(OnLayoutChangeListener l:listeners)l.onLayoutChange(this,0,0,w,height,0,0,old,height);}
 public void drain(){int rounds=0;while(!pending.isEmpty()){if(++rounds>20)throw new AssertionError("replay loop");List<Runnable> p=new ArrayList<Runnable>(pending);pending.clear();for(Runnable r:p)r.run();}}
}
''',
'android/widget/ScrollView.java': r'''
package android.widget; public class ScrollView extends android.view.View {public int x,y,calls;public void scrollTo(int x,int y){this.x=x;this.y=y;calls++;}}
''',
'android/app/Activity.java': r'''
package android.app; public class Activity {public static final int RESULT_OK=-1;public android.view.View root;public <V extends android.view.View> V findViewById(int id){return root.findViewById(id);}}
''',
'android/util/Log.java': r'''package android.util; public class Log {public static int i(String tag,String text){return 0;}}''',
'androidx/fragment/app/Fragment.java': r'''
package androidx.fragment.app;public class Fragment {public boolean added=true;public android.view.View view=new android.view.View();public boolean isAdded(){return added;}public android.view.View getView(){return view;}}
''',
'com/nice/room/ui/RoomLiveActivity.java': r'''package com.nice.room.ui;public class RoomLiveActivity extends android.app.Activity {}''',
'com/alibaba/fastjson/JSONObject.java': r'''
package com.alibaba.fastjson;public class JSONObject extends java.util.HashMap<String,Object>{public Float getFloat(String key){Object v=get(key);return v==null?null:Float.valueOf(v.toString());}public int getIntValue(String key){Object v=get(key);return v==null?0:Integer.parseInt(v.toString());}}
''',
'com/hailiang/common/util/AppRuntimeData.java': r'''package com.hailiang.common.util;public class AppRuntimeData {public static long user=7;public static long getUserId(){return user;}}''',
'com/hailiang/xxb/room/server/entity/discussion/DiscussionInfo.java': r'''package com.hailiang.xxb.room.server.entity.discussion;public class DiscussionInfo {public long id=20;public long getDiscussionId(){return id;}}''',
'com/nice/room/ui/roomlive/fragment/discussion/DiscussionFragment.java': r'''
package com.nice.room.ui.roomlive.fragment.discussion;
import com.hailiang.xxb.room.server.entity.discussion.DiscussionInfo;
public class DiscussionFragment extends androidx.fragment.app.Fragment {
 public DiscussionInfo info=new DiscussionInfo();public long group=3,classroom=10;public boolean ended,history;
 public static DiscussionInfo access$getDiscussionInfo(DiscussionFragment f){return f.info;}
 public static long access$getGroupId$p(DiscussionFragment f){return f.group;}
 public long modReviewClassroomId(){return classroom;}
 public boolean modCanImportAfterEnd(){return added&&view!=null&&!history&&ended&&group>0;}
}
''',
'com/nice/room/R.java': r'''package com.nice.room;public class R {public static class id {public static int document_container=101,view_handwrite_teacher=102,courseware_sv=103;}}''',
'com/hailiang/document/DocumentType.java': r'''package com.hailiang.document;public enum DocumentType {PDF,PPT,UNKNOWN}''',
'com/hailiang/handwrite/bean/PointInfo.java': r'''package com.hailiang.handwrite.bean;public class PointInfo {public int phoneWidth,phoneHeight;public PointInfo(int w,int h){phoneWidth=w;phoneHeight=h;}}''',
'com/hailiang/handwrite/bean/PathInfo.java': r'''package com.hailiang.handwrite.bean;public class PathInfo {public java.util.List<PointInfo> pointsList;}''',
'com/nice/room/ui/roomlive/RoomInfo.java': r'''package com.nice.room.ui.roomlive;public class RoomInfo {public long document=100;public long getDocumentId(){return document;}}''',
'com/nice/room/ui/roomlive/interaction/impl/FreeBrowseInteraction.java': r'''
package com.nice.room.ui.roomlive.interaction.impl;public class FreeBrowseInteraction {public static Companion Companion=new Companion();public static class Companion {public boolean free;public boolean getInFreeBrowsing(){return free;}}}
''',
'com/nice/room/ui/roomlive/RoomLiveDocumentManager.java': r'''
package com.nice.room.ui.roomlive;
import com.alibaba.fastjson.JSONObject;import com.hailiang.document.DocumentType;
public class RoomLiveDocumentManager {
 public com.nice.room.ui.RoomLiveActivity activity=new com.nice.room.ui.RoomLiveActivity();public RoomInfo info=new RoomInfo();
 public boolean can=true;public DocumentType type=DocumentType.PDF;public JSONObject last;public int layouts,applied;
 public com.nice.room.ui.RoomLiveActivity getActivity(){return activity;}public RoomInfo modRoomInfo(){return info;}
 public DocumentType modDocumentType(){return type;}public boolean getCanUpdateHandwriteLayout(){return can;}
 public void setPptLayout(JSONObject raw){last=com.hljzjx.classroom.repairs.DocumentViewport.adjust(this,raw);layouts++;if(can&&!com.nice.room.ui.roomlive.interaction.impl.FreeBrowseInteraction.Companion.free)applied++;}
}
''',
'BehaviorTest.java': r'''
import android.view.View;import android.widget.ScrollView;import com.alibaba.fastjson.JSONObject;
import com.hailiang.common.util.AppRuntimeData;import com.hailiang.document.DocumentType;
import com.hailiang.handwrite.bean.*;import com.nice.room.R;
import com.nice.room.ui.roomlive.*;import com.nice.room.ui.roomlive.fragment.discussion.DiscussionFragment;
import com.nice.room.ui.roomlive.interaction.impl.FreeBrowseInteraction;
import com.hljzjx.classroom.repairs.*;
public class BehaviorTest {
 static int assertions,affineCases;static void yes(boolean b,String why){assertions++;if(!b)throw new AssertionError(why);}
 static void eq(double a,double b,String why){yes(Math.abs(a-b)<0.004,why+": "+a+" != "+b);}
 static JSONObject layout(float scale,float x,float y){JSONObject j=new JSONObject();j.put("scale",scale);j.put("translationX",x);j.put("translationY",y);j.put("extra","keep");return j;}
 static void photos(){
  DiscussionFragment f=new DiscussionFragment();f.ended=true;
  eq(DiscussionPhotos.result(f,0,-1),0,"ended requires captured picker session");
  DiscussionPhotos.begin(f);eq(DiscussionPhotos.result(f,0,-1),1,"same-group ended crop enters native saveImage");
  yes(DiscussionPhotos.keepUpload(f),"eligible upload survives end callback");
  f.group++;yes(!DiscussionPhotos.keepUpload(f),"changed group does not keep old upload alive");
  for(int kind=0;kind<7;kind++){
   f=new DiscussionFragment();DiscussionPhotos.begin(f);
   if(kind==0)f.group++;if(kind==1)f.info.id++;if(kind==2)f.classroom++;
   if(kind==3)AppRuntimeData.user++;if(kind==4)f.added=false;if(kind==5)f.view=null;if(kind==6)f.group=0;
   eq(DiscussionPhotos.result(f,0,-1),-1,"reject stale scope "+kind);yes(!DiscussionPhotos.keepUpload(f),"stale result not uploading");AppRuntimeData.user=7;
  }
  f=new DiscussionFragment();DiscussionPhotos.begin(f);eq(DiscussionPhotos.result(f,0,-1),0,"active state stays in native state check");f.ended=true;yes(DiscussionPhotos.keepUpload(f),"upload started while active survives end");
  f=new DiscussionFragment();f.ended=true;DiscussionPhotos.begin(f);eq(DiscussionPhotos.result(f,0,0),1,"cancelled crop can reach native resultCode guard");yes(!DiscussionPhotos.keepUpload(f),"cancelled result never starts upload");
  f=new DiscussionFragment();f.history=true;DiscussionPhotos.begin(f);eq(DiscussionPhotos.result(f,1,-1),1,"valid review result preserved");yes(!DiscussionPhotos.keepUpload(f),"review has separate upload lifecycle");
  f=new DiscussionFragment();f.ended=true;DiscussionPhotos.begin(f);eq(DiscussionPhotos.result(f,-1,-1),-1,"review stale gate takes priority");
 }
 static class Screen {
  RoomLiveDocumentManager m=new RoomLiveDocumentManager();View root=new View(),doc=new View(),teacher=new View(),core=new View();ScrollView scroll=new ScrollView();
  Screen(){m.activity.root=root;doc.id=R.id.document_container;doc.parent=root;teacher.id=R.id.view_handwrite_teacher;teacher.parent=root;core.parent=teacher;scroll.parent=root;root.children.put(doc.id,doc);root.children.put(R.id.courseware_sv,scroll);DocumentViewport.loaded(m);}
  void source(int w){DocumentViewport.point(core,new PointInfo(w,1200));root.drain();}
 }
 static void geometry(){
  int[] locals={320,854,1280,1920,2560};int[] sources={800,1920,2560,3840};float[] scales={0.5f,1f,1.7f,3f};
  for(int local:locals)for(int source:sources)for(float scale:scales)for(int tx:new int[]{-600,0,320}){
   double point=137.25;
   // Independent affine invariant: map teacher final coordinates into local width.
   double expected=(point*scale+tx)*local/source;
   double actual=(point*local/source)*scale+DocumentGeometry.translation(tx,local,source);
   eq(actual,expected,"document and ink must share width-fit frame");affineCases++;
  }
  yes(Math.abs((137.25*1280/1920*2+300)-(137.25*2+300)*1280/1920)>99,"old raw-pixel translation fails negative control");
  yes(!DocumentGeometry.validSource(0,1200)&&!DocumentGeometry.validSource(1920,0)&&!DocumentGeometry.validSource(20000,1200),"bad source dimensions rejected");
  Screen s=new Screen();JSONObject raw=layout(2,300,150);s.m.setPptLayout(raw);
  yes(s.m.last==raw,"no invented sender width before source observation");
  PointInfo original=new PointInfo(1920,1200);DocumentViewport.point(s.core,original);s.root.drain();
  eq(s.m.last.getFloat("translationX"),200,"pending raw x replayed after teacher point");eq(s.m.last.getFloat("translationY"),100,"pending raw y replayed");
  eq(s.m.last.getFloat("scale"),2,"dimensionless scale unchanged");eq(raw.getFloat("translationX"),300,"incoming layout is immutable");
  yes("keep".equals(s.m.last.get("extra")),"unknown layout keys preserved");yes(original.phoneWidth==1920&&original.phoneHeight==1200,"teacher point unmodified");
  s.m.setPptLayout(raw);eq(s.m.last.getFloat("translationX"),200,"no double conversion on repeated packet");
  JSONObject msg=new JSONObject();msg.put("scrollY",600);msg.put("msgType","page");msg.put("slide",3);
  JSONObject local=DocumentViewport.message(s.m,msg);eq(local.getIntValue("scrollY"),400,"PDF scroll uses same width ratio");eq(msg.getIntValue("scrollY"),600,"raw message unmodified");yes("page".equals(local.get("msgType"))&&local.getIntValue("slide")==3,"page semantics retained");
  s.doc.resize(960);s.root.drain();eq(s.m.last.getFloat("translationX"),150,"resize recomputes from raw sender x");eq(s.scroll.y,300,"resize recomputes raw sender scroll");
  int before=s.scroll.calls,applied=s.m.applied;FreeBrowseInteraction.Companion.free=true;s.doc.resize(640);s.root.drain();yes(s.scroll.calls==before&&s.m.applied==applied,"free browse suppresses visible replay");
  FreeBrowseInteraction.Companion.free=false;s.m.can=false;s.doc.resize(800);s.root.drain();yes(s.scroll.calls==before&&s.m.applied==applied,"native manipulation guard suppresses replay");s.m.can=true;
  s.root.attached=false;s.doc.resize(1000);int count=s.m.layouts;s.root.drain();yes(s.m.layouts==count,"detached screen is not replayed");s.root.attached=true;
  s.m.info.document++;DocumentViewport.loaded(s.m);s.m.setPptLayout(raw);yes(s.m.last==raw,"document switch clears cached dimensions");before=s.scroll.calls;s.doc.resize(1100);s.root.drain();yes(s.scroll.calls==before,"document switch clears stale scroll");
  s.m.type=DocumentType.PPT;yes(DocumentViewport.adjust(s.m,raw)==raw&&DocumentViewport.message(s.m,msg)==msg,"PPT packets untouched");yes(!DocumentViewport.isPdfFrame(s.core),"PPT does not bypass teacher offset path");
  s.m.type=DocumentType.UNKNOWN;yes(DocumentViewport.adjust(s.m,raw)==raw,"unknown document unchanged");s.m.type=DocumentType.PDF;
  View unrelated=new View();unrelated.parent=s.root;DocumentViewport.point(unrelated,new PointInfo(2560,1600));yes(DocumentViewport.adjust(s.m,raw)==raw,"student or discussion point ignored");
  s.source(1920);yes(DocumentViewport.isPdfFrame(s.core),"registered PDF bypasses old teacher-only margin subtraction");
  PathInfo p=new PathInfo();p.pointsList=java.util.Arrays.asList(new PointInfo(2560,1600));DocumentViewport.path(s.core,p);s.root.drain();eq(DocumentViewport.adjust(s.m,raw).getFloat("translationX"),300*1100f/2560,"path dimensions observed");
  PathInfo newest=new PathInfo();newest.pointsList=java.util.Arrays.asList(new PointInfo(3840,2400));DocumentViewport.paths(s.core,java.util.Arrays.asList(p,newest));s.root.drain();eq(DocumentViewport.adjust(s.m,raw).getFloat("translationX"),300*1100f/3840,"latest valid path dimensions selected");
 }
 public static void main(String[] args){photos();geometry();System.out.println("{\"assertions\":"+assertions+",\"affine_cases\":"+affineCases+",\"runtime\":\"JVM with API fixtures\",\"device_tested\":false,\"server_tested\":false}");}
}
'''
}

def test():
    root=B/'test-fixtures';classes=B/'test-classes'
    for name,source in FIXTURES.items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source,'utf8')
    classes.mkdir(exist_ok=True)
    sources=[*root.rglob('*.java'),*(B/'src').rglob('*.java')]
    compiled=subprocess.run([str(JAVA),'-jar',str(T/'ecj.jar'),'-proc:none','-source','8','-target','8','-encoding','UTF-8','-warn:none','-d',str(classes),*map(str,sources)],capture_output=True,text=True,encoding='utf8',errors='replace')
    if compiled.returncode:raise AssertionError(compiled.stdout+compiled.stderr)
    result=subprocess.run([str(JAVA),'-cp',str(classes),'BehaviorTest'],capture_output=True,text=True,encoding='utf8',errors='replace')
    if result.returncode:raise AssertionError(result.stdout+result.stderr)
    report=json.loads(result.stdout);(B/'behavior-tests.json').write_text(json.dumps(report,indent=2),'utf8');return report

if __name__=='__main__':print(json.dumps(test(),indent=2))
