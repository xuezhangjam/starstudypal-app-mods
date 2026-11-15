package com.nice.room.ui.roomlive.fragment.discussion;
public class DiscussionFragment extends androidx.fragment.app.Fragment {
public boolean history=true,added=true,resumed=false;public android.view.View root;public long room=10,group=30;public DiscussionViewModel model=new DiscussionViewModel();public com.hailiang.xxb.room.server.entity.discussion.DiscussionInfo info=new com.hailiang.xxb.room.server.entity.discussion.DiscussionInfo();
public boolean isResumed(){return resumed;}public boolean isAdded(){return added;}public android.view.View getView(){return root;}public android.content.Context getContext(){return root==null?null:root.getContext();}
public static boolean access$isAfterClass(DiscussionFragment f){return f.history;}public static long access$getGroupId$p(DiscussionFragment f){return f.group;}
public static com.hailiang.xxb.room.server.entity.discussion.DiscussionInfo access$getDiscussionInfo(DiscussionFragment f){return f.info;}public static DiscussionViewModel access$getViewModel(DiscussionFragment f){return f.model;}public long modReviewClassroomId(){return room;}}
