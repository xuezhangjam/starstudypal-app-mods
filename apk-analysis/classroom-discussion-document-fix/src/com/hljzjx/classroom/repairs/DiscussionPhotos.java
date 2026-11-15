package com.hljzjx.classroom.repairs;

import android.app.Activity;
import com.hailiang.xxb.room.server.entity.discussion.DiscussionInfo;
import com.hailiang.common.util.AppRuntimeData;
import com.nice.room.ui.roomlive.fragment.discussion.DiscussionFragment;
import java.util.WeakHashMap;

/** Keep the native picker/upload protocol; scope a returned crop to its original group. */
public final class DiscussionPhotos {
    private static final WeakHashMap<DiscussionFragment,Scope> PICKING=new WeakHashMap<DiscussionFragment,Scope>();
    private static final WeakHashMap<DiscussionFragment,Scope> UPLOADING=new WeakHashMap<DiscussionFragment,Scope>();
    private static final class Scope {
        final long user,classroom,discussion,group;
        Scope(DiscussionFragment f){
            DiscussionInfo info=DiscussionFragment.access$getDiscussionInfo(f);
            user=AppRuntimeData.getUserId();classroom=f.modReviewClassroomId();
            discussion=info.getDiscussionId();group=DiscussionFragment.access$getGroupId$p(f);
        }
        boolean matches(DiscussionFragment f){
            if(!f.isAdded()||f.getView()==null||user<=0||classroom<=0||discussion<=0||group<=0)return false;
            Scope current=new Scope(f);
            return user==current.user&&classroom==current.classroom&&discussion==current.discussion&&group==current.group;
        }
    }
    private DiscussionPhotos(){}
    public static void begin(DiscussionFragment f){
        try{PICKING.put(f,new Scope(f));}catch(RuntimeException e){PICKING.remove(f);}
    }
    /** -1 reject stale result; 0 native state check; 1 eligible review/ended continuation. */
    public static int result(DiscussionFragment f,int reviewResult,int resultCode){
        try{
            Scope scope=PICKING.remove(f);
            if(reviewResult<0)return -1;
            if(scope!=null&&!scope.matches(f))return -1;
            if(scope!=null&&resultCode==Activity.RESULT_OK)UPLOADING.put(f,scope);
            if(reviewResult>0)return 1;
            if(scope!=null&&f.modCanImportAfterEnd())return 1;
            return 0;
        }catch(RuntimeException e){return -1;}
    }
    public static boolean keepUpload(DiscussionFragment f){
        try{Scope s=UPLOADING.get(f);return s!=null&&s.matches(f)&&f.modCanImportAfterEnd();}
        catch(RuntimeException e){return false;}
    }
}
