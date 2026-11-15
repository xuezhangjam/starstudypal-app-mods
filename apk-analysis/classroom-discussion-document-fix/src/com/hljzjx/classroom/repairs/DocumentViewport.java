package com.hljzjx.classroom.repairs;

import android.util.Log;
import android.view.View;
import android.widget.ScrollView;
import com.alibaba.fastjson.JSONObject;
import com.hailiang.document.DocumentType;
import com.hailiang.handwrite.bean.PathInfo;
import com.hailiang.handwrite.bean.PointInfo;
import com.nice.room.R;
import com.nice.room.ui.roomlive.RoomLiveDocumentManager;
import com.nice.room.ui.roomlive.interaction.impl.FreeBrowseInteraction;
import java.lang.ref.WeakReference;
import java.util.List;
import java.util.WeakHashMap;

/** PDF-only length conversion. PPT source-canvas fit and document DOM remain untouched. */
public final class DocumentViewport {
    private static final WeakHashMap<View,State> STATES=new WeakHashMap<View,State>();
    private static final class State implements View.OnLayoutChangeListener,Runnable {
        final WeakReference<View> root;
        WeakReference<RoomLiveDocumentManager> manager;
        long document=-1;int sourceWidth,sourceHeight,scrollY;JSONObject raw;boolean queued,hasScroll;
        State(View v){root=new WeakReference<View>(v);}
        void schedule(){View v=root.get();if(v!=null&&!queued){queued=v.postDelayed(this,32);}}
        public void run(){
            queued=false;View v=root.get();RoomLiveDocumentManager m=manager==null?null:manager.get();
            if(v==null||m==null||!v.isAttachedToWindow()||!pdf(m)||document!=m.modRoomInfo().getDocumentId())return;
            if(raw!=null)m.setPptLayout(copy(raw));
            if(hasScroll&&m.getCanUpdateHandwriteLayout()&&!FreeBrowseInteraction.Companion.getInFreeBrowsing()){
                View area=v.findViewById(R.id.courseware_sv),doc=v.findViewById(R.id.document_container);
                if(area instanceof ScrollView&&doc!=null)((ScrollView)area).scrollTo(0,Math.round(DocumentGeometry.translation(scrollY,doc.getWidth(),sourceWidth)));
            }
        }
        public void onLayoutChange(View v,int l,int t,int r,int b,int ol,int ot,int or,int ob){if(r-l!=or-ol)schedule();}
    }
    private DocumentViewport(){}
    private static JSONObject copy(JSONObject input){JSONObject result=new JSONObject();result.putAll(input);return result;}
    private static boolean finite(float x){return !Float.isInfinite(x)&&!Float.isNaN(x);}
    private static boolean pdf(RoomLiveDocumentManager m){return m.modDocumentType()==DocumentType.PDF;}
    private static State state(RoomLiveDocumentManager m){
        View document=m.getActivity().findViewById(R.id.document_container);
        if(document==null)return null;
        View root=document.getRootView();State s=STATES.get(root);
        if(s==null){s=new State(root);STATES.put(root,s);document.addOnLayoutChangeListener(s);}
        s.manager=new WeakReference<RoomLiveDocumentManager>(m);
        long id=m.modRoomInfo().getDocumentId();
        if(s.document!=id){s.document=id;s.sourceWidth=0;s.sourceHeight=0;s.raw=null;s.hasScroll=false;}
        return s;
    }
    public static void loaded(RoomLiveDocumentManager m){try{state(m);}catch(RuntimeException ignored){}}
    public static JSONObject adjust(RoomLiveDocumentManager m,JSONObject input){
        if(input==null)return null;
        try{
            State s=state(m);if(s==null||!pdf(m))return input;
            Float scale=input.getFloat("scale"),x=input.getFloat("translationX"),y=input.getFloat("translationY");
            if(scale==null||x==null||y==null||!finite(scale)||scale<=0||!finite(x)||!finite(y))return input;
            s.raw=copy(input);
            View document=m.getActivity().findViewById(R.id.document_container);
            if(document==null||document.getWidth()<=0||s.sourceWidth<=0)return input;
            JSONObject local=copy(input);
            local.put("translationX",DocumentGeometry.translation(x,document.getWidth(),s.sourceWidth));
            local.put("translationY",DocumentGeometry.translation(y,document.getWidth(),s.sourceWidth));
            Log.i("DocumentViewport","pdf source="+s.sourceWidth+"x"+s.sourceHeight+" localWidth="+document.getWidth());
            return local;
        }catch(RuntimeException ignored){return input;}
    }
    public static JSONObject message(RoomLiveDocumentManager m,JSONObject input){
        if(input==null)return null;
        try{
            State s=state(m);if(s==null||!pdf(m)||!input.containsKey("scrollY"))return input;
            s.scrollY=input.getIntValue("scrollY");s.hasScroll=true;
            View doc=m.getActivity().findViewById(R.id.document_container);
            if(doc==null||doc.getWidth()<=0||s.sourceWidth<=0)return input;
            JSONObject local=copy(input);local.put("scrollY",Math.round(DocumentGeometry.translation(s.scrollY,doc.getWidth(),s.sourceWidth)));return local;
        }catch(RuntimeException ignored){return input;}
    }
    public static boolean isPdfFrame(View view){
        try{State s=STATES.get(view.getRootView());RoomLiveDocumentManager m=s==null||s.manager==null?null:s.manager.get();return m!=null&&pdf(m);}
        catch(RuntimeException ignored){return false;}
    }
    private static void source(View core,PointInfo p){
        if(p==null||!DocumentGeometry.validSource(p.phoneWidth,p.phoneHeight)||!(core.getParent() instanceof View))return;
        if(((View)core.getParent()).getId()!=R.id.view_handwrite_teacher)return;
        State s=STATES.get(core.getRootView());RoomLiveDocumentManager m=s==null||s.manager==null?null:s.manager.get();
        if(m==null||!pdf(m))return;
        // Clear dimensions on a document change before accepting fresh teacher data.
        s=state(m);if(s==null||s.sourceWidth==p.phoneWidth&&s.sourceHeight==p.phoneHeight)return;
        s.sourceWidth=p.phoneWidth;s.sourceHeight=p.phoneHeight;s.schedule();
    }
    public static void point(View core,PointInfo p){try{source(core,p);}catch(RuntimeException ignored){}}
    public static void path(View core,PathInfo p){
        if(p==null||p.pointsList==null)return;
        for(PointInfo point:p.pointsList)if(point!=null&&DocumentGeometry.validSource(point.phoneWidth,point.phoneHeight)){point(core,point);return;}
    }
    public static void paths(View core,List<PathInfo> paths){
        if(paths==null)return;
        for(int i=paths.size()-1;i>=0;i--){PathInfo p=paths.get(i);if(p==null||p.pointsList==null)continue;
            for(PointInfo point:p.pointsList)if(point!=null&&DocumentGeometry.validSource(point.phoneWidth,point.phoneHeight)){point(core,point);return;}}
    }
}
