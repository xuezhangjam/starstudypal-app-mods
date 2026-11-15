package com.hljzjx.classroom.reviewdraw;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.view.MotionEvent;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;
import com.hailiang.common.util.AppRuntimeData;
import com.hailiang.handwrite.bean.PathInfo;
import com.hailiang.handwrite.serialize.PathInfoSerializer;
import com.hailiang.handwrite.widget.HandwriteView;
import com.hailiang.xxb.room.server.DiscussionRepository;
import com.hailiang.xxb.room.server.Result;
import com.hailiang.xxb.room.server.entity.discussion.DiscussionStroke;
import com.hailiang.xxb.room.server.entity.discussion.GroupDiscussionDetail;
import com.nice.room.ui.roomlive.fragment.discussion.DiscussionFragment;
import com.nice.room.ui.roomlive.fragment.discussion.DiscussionViewModel;
import com.nice.room.ui.roomlive.tool.*;
import com.hljzjx.classroom.mod.DiscussionCoordinates;
import java.lang.ref.WeakReference;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;
import kotlin.Unit;
import kotlin.ResultKt;
import kotlin.coroutines.*;
import kotlin.coroutines.intrinsics.IntrinsicsKt;
import kotlin.jvm.functions.*;
import org.json.*;

/** History editing uses the original canvas, tools, serializers and authenticated repository. */
public final class ReviewDrawing {
 private static final Handler MAIN=new Handler(Looper.getMainLooper());
 private static final WeakHashMap<DiscussionFragment,Session> FRAGMENTS=new WeakHashMap<DiscussionFragment,Session>();
 private static final WeakHashMap<DiscussionViewModel,Session> MODELS=new WeakHashMap<DiscussionViewModel,Session>();
 private static final WeakHashMap<ToolBarState,Session> TOOLS=new WeakHashMap<ToolBarState,Session>();
 private static InkQueue queue;
 private static final PathInfoSerializer SERIALIZER=new PathInfoSerializer();
 private static long user(){return AppRuntimeData.getUserId();}
 private static View find(View root,String name){int id=root.getResources().getIdentifier(name,"id",root.getContext().getPackageName());return id==0?null:root.findViewById(id);}
 private static void init(Context context){
  if(queue!=null)return;
  final SharedPreferences prefs=context.getApplicationContext().getSharedPreferences("mod_review_ink_v1",0);
  queue=new InkQueue(new InkQueue.Scheduler(){public void post(Runnable r,long delay){MAIN.postDelayed(r,delay);}public long user(){return ReviewDrawing.user();}},new NativeTransport(),new InkQueue.Store(){
   public InkQueue.Snapshot load(InkQueue.Key key){try{JSONObject j=new JSONObject(prefs.getString(key.toString(),"{}"));return new InkQueue.Snapshot(decode(j.optJSONArray("pending")),decode(j.optJSONArray("accepted")),decode(j.optJSONArray("unknown")));}catch(Exception bad){return null;}}
   public void save(InkQueue.Key key,InkQueue.Snapshot s){try{JSONObject j=new JSONObject();j.put("pending",encode(s.pending));j.put("accepted",encode(s.accepted));j.put("unknown",encode(s.unknown));if(s.pending.isEmpty()&&s.accepted.isEmpty()&&s.unknown.isEmpty())prefs.edit().remove(key.toString()).apply();else prefs.edit().putString(key.toString(),j.toString()).apply();}catch(JSONException bad){throw new IllegalStateException(bad);}}
  },new InkQueue.ReadListener(){public void readback(InkQueue.Key key,List<InkQueue.Stroke> records){for(Session s:new ArrayList<Session>(FRAGMENTS.values()))if(s.key.equals(key)&&alive(s)){s.server=new ArrayList<InkQueue.Stroke>(records);s.dirty=true;}}public void changed(InkQueue.Key key){for(Session s:new ArrayList<Session>(FRAGMENTS.values()))if(s.key.equals(key)){paint(s,false);status(s);}}});
 }
 private static JSONArray encode(List<InkQueue.Stroke> strokes)throws JSONException{JSONArray a=new JSONArray();for(InkQueue.Stroke s:strokes){JSONObject j=new JSONObject();j.put("id",s.id);j.put("value",s.value);j.put("deleted",s.deleted);a.put(j);}return a;}
 private static List<InkQueue.Stroke> decode(JSONArray a)throws JSONException{ArrayList<InkQueue.Stroke> list=new ArrayList<InkQueue.Stroke>();if(a!=null)for(int i=0;i<a.length();i++){JSONObject j=a.getJSONObject(i);list.add(new InkQueue.Stroke(j.getString("id"),j.getString("value"),j.getBoolean("deleted")));}return list;}
 private static InkQueue.Stroke record(PathInfo p){return new InkQueue.Stroke(p.userMark+"_"+p.pathID,SERIALIZER.serialize(p),p.pointsList==null||p.pointsList.isEmpty());}
 private static List<PathInfo> paths(List<InkQueue.Stroke> records){ArrayList<PathInfo> list=new ArrayList<PathInfo>();for(InkQueue.Stroke r:records)list.add(SERIALIZER.deserialize(r.value));return list;}

 public static void refresh(DiscussionFragment f){
  if(!f.isAdded()||f.getView()==null||!DiscussionFragment.access$isAfterClass(f))return;
  try{
   View root=f.getView();View hv=find(root,"handwrite"),tv=find(root,"handwrite_toolbar");if(!(hv instanceof HandwriteView)||!(tv instanceof RoomToolBarView))return;
   init(root.getContext());
   InkQueue.Key key=new InkQueue.Key(user(),f.modReviewClassroomId(),DiscussionFragment.access$getDiscussionInfo(f).getDiscussionId(),DiscussionFragment.access$getGroupId$p(f));
   if(!key.valid())return;
   Session s=FRAGMENTS.get(f);if(s!=null&&s.key.user!=key.user){gate(s,false);return;}
   if(s==null||!s.key.equals(key)||s.canvas.get()!=hv){
    if(s!=null)release(s);
    s=new Session(f,key,(HandwriteView)hv,(RoomToolBarView)tv);FRAGMENTS.put(f,s);MODELS.put(DiscussionFragment.access$getViewModel(f),s);TOOLS.put(((RoomToolBarView)tv).modGetToolBarState(),s);
    RoomToolBarView toolbar=(RoomToolBarView)tv;Function0<Unit> photo=toolbar.getOnTakePhoto();if(photo instanceof PhotoAction)photo=((PhotoAction)photo).original;if(photo!=null)toolbar.setOnTakePhoto(new PhotoAction(s,photo));
    s.adjusting=true;toolbar.setHideClearOption(false);toolbar.setHideColorOptions(false);toolbar.setHideGraphOptions(false);toolbar.setSelectTool(DrawingTool.DRAG);toolbar.setHandwriteEnable(true);s.adjusting=false;
    gate(s,false);load(s,false);schedulePoll(s,2000);
   }
   RoomToolBarView current=(RoomToolBarView)tv;if(!current.modGetToolBarState().getHandwriteEnabled())current.setHandwriteEnable(true);
   current.setVisibility(View.VISIBLE);gate(s,s.editing);status(s);
  }catch(RuntimeException bad){Context c=f.getContext();if(c!=null)Toast.makeText(c,"回顾工具初始化失败，请重新进入",Toast.LENGTH_LONG).show();}
 }
 private static final class Session {
  final InkQueue.Key key;final WeakReference<DiscussionFragment> fragment;final WeakReference<HandwriteView> canvas;final WeakReference<RoomToolBarView> toolbar;
  final FunctionToolItemInfo start,sync;
  List<InkQueue.Stroke> server=Collections.emptyList(),applied;
  boolean ready,editing,loading,adjusting,closed,wantEdit,photoPending,dirty,applying,interacting,pollScheduled,pollBusy,paintScheduled;
  long lastTouch=-1000,pollDelay=2000;int epoch;
  Session(DiscussionFragment f,InkQueue.Key k,HandwriteView h,RoomToolBarView t){key=k;fragment=new WeakReference<DiscussionFragment>(f);canvas=new WeakReference<HandwriteView>(h);toolbar=new WeakReference<RoomToolBarView>(t);start=FunctionToolItemInfo.modLocalItem("继续画",android.R.drawable.ic_menu_edit,null,new Action(this,false));sync=FunctionToolItemInfo.modLocalItem("同步状态",android.R.drawable.ic_popup_sync,null,new Action(this,true));}
 }
 private static boolean alive(Session s){DiscussionFragment f=s.fragment.get();return !s.closed&&s.key.user==user()&&f!=null&&f.isAdded()&&f.getView()!=null&&DiscussionFragment.access$getGroupId$p(f)==s.key.group;}
 private static void gate(Session s,boolean allow){HandwriteView h=s.canvas.get();RoomToolBarView t=s.toolbar.get();if(h==null||t==null)return;h.setEnabled(!s.loading);h.setCanDraw(allow&&alive(s)&&s.ready&&s.editing&&t.getSelectTool()!=DrawingTool.DRAG);if(!s.editing)h.setImageEditable(false);}
 private static void status(Session s){if(!alive(s))return;DiscussionFragment f=s.fragment.get();View v=find(f.getView(),"tv_countdown");if(v instanceof TextView){v.setVisibility(View.VISIBLE);((TextView)v).setText(s.loading?"正在加载小组笔迹":queue.status(s.key));}}
 private static boolean visible(Session s){DiscussionFragment f=s.fragment.get();HandwriteView h=s.canvas.get();return alive(s)&&f.isResumed()&&h!=null&&h.isShown()&&h.isAttachedToWindow();}
 private static boolean sameRecords(List<InkQueue.Stroke> a,List<InkQueue.Stroke> b){if(a==null||a.size()!=b.size())return false;for(int i=0;i<a.size();i++){InkQueue.Stroke x=a.get(i),y=b.get(i);if(!x.id.equals(y.id)||!x.value.equals(y.value)||x.deleted!=y.deleted)return false;}return true;}
 private static void render(Session s){s.dirty=true;paint(s,true);}
 /** Replace completed records only at a safe idle boundary; never interrupt a stroke. */
 private static void paint(Session s,boolean initial){
  if(!s.dirty||!s.ready||s.applying||!alive(s)||!initial&&!visible(s)||s.interacting||SystemClock.uptimeMillis()-s.lastTouch<150)return;
  HandwriteView h=s.canvas.get();if(h==null||h.isInGeometryEditMode())return;
  List<InkQueue.Stroke> records=queue.overlay(s.key,s.server);if(sameRecords(s.applied,records)){s.dirty=false;return;}
  float scale=h.getHandwriteScale(),x=h.getHandwriteTranslationX(),y=h.getHandwriteTranslationY();s.applying=true;
  try{h.setPathInfoList(DiscussionCoordinates.paths(paths(records)),false);
   if(Float.compare(h.getHandwriteScale(),scale)!=0)h.setHandwriteScale(scale,false);
   if(Float.compare(h.getHandwriteTranslationX(),x)!=0)h.setHandwriteTranslationX(x,false);
   if(Float.compare(h.getHandwriteTranslationY(),y)!=0)h.setHandwriteTranslationY(y,false);
   s.applied=new ArrayList<InkQueue.Stroke>(records);s.dirty=false;
  }catch(RuntimeException bad){s.pollDelay=15000;}finally{s.applying=false;}
 }
 private static void schedulePoll(Session s,long delay){if(s.pollScheduled||!alive(s))return;s.pollScheduled=true;MAIN.postDelayed(new Poll(s),delay);}
 private static final class Poll implements Runnable {
  final WeakReference<Session> session;Poll(Session s){session=new WeakReference<Session>(s);}
  public void run(){final Session s=session.get();if(s==null)return;s.pollScheduled=false;if(!alive(s))return;
   if(visible(s)){paint(s,false);if(s.ready&&!s.loading&&!s.pollBusy){s.pollBusy=true;queue.observe(s.key,new InkQueue.Callback<List<InkQueue.Stroke>>(){public void done(List<InkQueue.Stroke> records,String error){s.pollBusy=false;if(!alive(s))return;s.pollDelay=records==null?Math.min(15000,s.pollDelay*2):2000;paint(s,false);status(s);}});}}
   else{s.interacting=false;}
   schedulePoll(s,s.pollDelay);
  }
 }
 public static void touch(RoomToolBarView toolbar,MotionEvent event){
  Session s=TOOLS.get(toolbar.modGetToolBarState());if(s==null||!alive(s)||event==null)return;
  int action=event.getActionMasked();s.lastTouch=SystemClock.uptimeMillis();
  s.interacting=action!=MotionEvent.ACTION_UP&&action!=MotionEvent.ACTION_CANCEL;
  if(!s.interacting&&!s.paintScheduled){s.paintScheduled=true;MAIN.postDelayed(new IdlePaint(s),180);}
 }
 private static final class IdlePaint implements Runnable {final WeakReference<Session> session;IdlePaint(Session s){session=new WeakReference<Session>(s);}public void run(){Session s=session.get();if(s!=null){s.paintScheduled=false;paint(s,false);}}}
 private static void begin(Session s){if(!alive(s))return;if(s.loading){s.wantEdit=true;return;}if(!s.ready){load(s,true);return;}s.editing=true;RoomToolBarView t=s.toolbar.get();if(t!=null){s.adjusting=true;t.setSelectTool(DrawingTool.BRUSH);s.adjusting=false;}gate(s,true);status(s);}
 private static void load(final Session s,final boolean edit){
  if(!alive(s)||s.loading)return;s.loading=true;gate(s,false);status(s);final int epoch=++s.epoch;
  queue.read(s.key,new InkQueue.Callback<List<InkQueue.Stroke>>(){public void done(List<InkQueue.Stroke> records,String error){
   if(!alive(s)||epoch!=s.epoch)return;s.loading=false;
   if(records==null){s.ready=false;gate(s,false);toast(s,error);status(s);return;}
   s.server=new ArrayList<InkQueue.Stroke>(records);s.ready=true;render(s);if(edit||s.wantEdit){s.wantEdit=false;begin(s);}else gate(s,s.editing);status(s);
  }});
 }
 public static List<PathInfo> merge(DiscussionFragment f,List<PathInfo> incoming){
  if(!DiscussionFragment.access$isAfterClass(f))return incoming;refresh(f);Session s=FRAGMENTS.get(f);if(s==null||!alive(s))return Collections.emptyList();return paths(queue.overlay(s.key,s.server));
 }
 public static boolean capture(DiscussionViewModel model,long discussion,long group,PathInfo path){
  Session s=MODELS.get(model);if(s==null)return false;
  // A registered history model never falls through to the live, shared pending list.
  if(!alive(s)||!s.ready||!s.editing||s.applying||s.key.discussion!=discussion||s.key.group!=group)return true;
  if(path==null||path.userMark!=s.key.user){toast(s,"只能同步自己的笔迹");return true;}
  try{queue.put(s.key,record(path));}catch(RuntimeException bad){toast(s,"笔迹排队失败，请重新进入后重试");}return true;
 }
 public static void append(List<FunctionToolItemInfo> items,ToolBarState state){Session s=TOOLS.get(state);if(s==null||!alive(s))return;if(!items.contains(s.start))items.add(s.start);if(!items.contains(s.sync))items.add(s.sync);}
 public static void tool(RoomToolBarView toolbar,DrawingTool selected){Session s=TOOLS.get(toolbar.modGetToolBarState());if(s==null||s.adjusting||!alive(s))return;if(selected!=DrawingTool.DRAG&&!s.editing)begin(s);gate(s,s.editing);}
 private static final class Action implements Function1<FunctionToolItemInfo,Unit>{final WeakReference<Session> session;final boolean sync;Action(Session s,boolean retry){session=new WeakReference<Session>(s);sync=retry;}public Unit invoke(FunctionToolItemInfo ignored){Session s=session.get();if(s!=null&&alive(s)){if(sync){if(!s.ready){load(s,false);}else if(!s.loading){queue.retry(s.key);queue.read(s.key,null);}toast(s,queue.status(s.key));}else begin(s);}return Unit.INSTANCE;}}
 private static final class PhotoAction implements Function0<Unit>{final WeakReference<Session> session;final Function0<Unit> original;PhotoAction(Session s,Function0<Unit> action){session=new WeakReference<Session>(s);original=action;}public Unit invoke(){Session s=session.get();if(s!=null&&alive(s)){if(s.ready){s.editing=true;s.photoPending=true;gate(s,true);return original.invoke();}load(s,true);toast(s,"请等待小组笔迹加载完成后再拍照");}return Unit.INSTANCE;}}
 public static int photoResult(DiscussionFragment f){if(!DiscussionFragment.access$isAfterClass(f))return 0;Session s=FRAGMENTS.get(f);if(s==null||!alive(s)||!s.ready||!s.photoPending)return -1;s.photoPending=false;return 1;}
 private static void toast(Session s,String message){HandwriteView h=s.canvas.get();if(h!=null&&message!=null)Toast.makeText(h.getContext(),message,Toast.LENGTH_LONG).show();}
 private static void release(Session s){s.closed=true;s.epoch++;gate(s,false);TOOLS.values().removeAll(Collections.singleton(s));MODELS.values().removeAll(Collections.singleton(s));}
 public static void detach(DiscussionFragment f){Session s=FRAGMENTS.remove(f);if(s!=null)release(s);}

 /** Reuses Retrofit authentication and native business-result parsing. No fabricated success. */
 private static final class NativeTransport implements InkQueue.Transport {
  final DiscussionRepository repository=new DiscussionRepository();
  public void append(final InkQueue.Key key,List<InkQueue.Stroke> strokes,final InkQueue.Callback<Boolean> callback){
   if(key.user!=user()){callback.done(false,"账号已切换");return;}
   Map<String,Object> body=new LinkedHashMap<String,Object>();body.put("groupDiscussionId",key.discussion);body.put("groupDiscussionGroupId",key.group);body.put("userId",key.user);body.put("userType",1);List<String> records=new ArrayList<String>();for(InkQueue.Stroke s:strokes)records.add(s.value);body.put("recordValueList",records);
   Bridge bridge=new Bridge(new Response(){public void done(Object value,String error){if(value instanceof Result.Success){Object data=((Result.Success<?>)value).getData();callback.done(Boolean.TRUE.equals(data),Boolean.TRUE.equals(data)?null:"服务器未确认上传");}else if(value instanceof Result.Failure)callback.done(false,((Result.Failure)value).getMsg());else callback.done(null,error==null?"上传结果未知":error);}});
   try{bridge.direct(repository.appendStroke(body,bridge));}catch(Exception bad){bridge.fail("上传异常，请检查网络");}
  }
  public void read(final InkQueue.Key key,final InkQueue.Callback<List<InkQueue.Stroke>> callback){
   if(key.user!=user()){callback.done(null,"账号已切换");return;}
   Bridge bridge=new Bridge(new Response(){public void done(Object value,String error){
    if(value instanceof Result.Success){Object data=((Result.Success<?>)value).getData();if(!(data instanceof GroupDiscussionDetail)||((GroupDiscussionDetail)data).getGroupId()!=key.group){callback.done(null,"小组数据不匹配，请重新进入");return;}
     try{List<InkQueue.Stroke> list=new ArrayList<InkQueue.Stroke>();List<DiscussionStroke> groups=((GroupDiscussionDetail)data).getStrokes();if(groups!=null)for(DiscussionStroke member:groups){List<String> records=member.getCacheRecordList();if(records!=null)for(String json:records)list.add(record(SERIALIZER.deserialize(json)));}callback.done(list,null);}catch(RuntimeException bad){callback.done(null,"笔迹解析失败，未覆盖本地笔迹");}
    }else callback.done(null,value instanceof Result.Failure?((Result.Failure)value).getMsg():error);
   }});
   try{bridge.direct(repository.getGroupDiscussionDetail(key.discussion,key.group,true,bridge));}catch(Exception bad){bridge.fail("回读异常，请检查网络");}
  }
 }
 private interface Response{void done(Object value,String error);}
 private static final class Bridge implements Continuation<Object>{
  final AtomicBoolean completed=new AtomicBoolean();final Response response;Bridge(Response r){response=r;}
  public CoroutineContext getContext(){return EmptyCoroutineContext.INSTANCE;}
  public void resumeWith(Object result){try{ResultKt.throwOnFailure(result);finish(result,null);}catch(Throwable error){finish(null,"网络请求失败，请重试");}}
  void direct(Object value){if(value!=IntrinsicsKt.getCOROUTINE_SUSPENDED())resumeWith(value);}
  void fail(String error){finish(null,error);}
  void finish(final Object value,final String error){if(completed.compareAndSet(false,true))MAIN.post(new Runnable(){public void run(){response.done(value,error);}});}
 }
}
