from pathlib import Path
B=Path(__file__).resolve().parent/'platform'
files={
'android/content/Intent.java':'''package android.content;public class Intent{
 public static final String ACTION_VIEW="android.intent.action.VIEW",ACTION_MAIN="android.intent.action.MAIN",CATEGORY_BROWSABLE="android.intent.category.BROWSABLE",CATEGORY_APP_BROWSER="android.intent.category.APP_BROWSER",ACTION_OPEN_DOCUMENT="OPEN_DOCUMENT",ACTION_GET_CONTENT="GET_CONTENT",CATEGORY_OPENABLE="OPENABLE",EXTRA_ALLOW_MULTIPLE="MULTIPLE";
 public static final int FLAG_GRANT_READ_URI_PERMISSION=1;public String action,type,category,pkg;public boolean multiple;public int flags;public android.net.Uri uri;public Intent selector;
 public Intent(String s){action=s;}public Intent(String s,android.net.Uri u){action=s;uri=u;}
 public Intent setPackage(String s){pkg=s;return this;}public void setSelector(Intent s){selector=s;}
 public Intent setType(String s){type=s;return this;}public Intent addCategory(String s){category=s;return this;}public Intent putExtra(String n,boolean v){multiple=v;return this;}public Intent addFlags(int f){flags|=f;return this;}public android.net.Uri getData(){return uri;}public ClipData getClipData(){return null;}
}''',
'android/content/pm/ActivityInfo.java':'package android.content.pm;public class ActivityInfo{public String packageName;}',
'android/content/pm/ResolveInfo.java':'package android.content.pm;public class ResolveInfo{public ActivityInfo activityInfo;}',
'android/widget/ScrollView.java':'package android.widget;public class ScrollView extends FrameLayout{public ScrollView(android.content.Context c){super(c);}public void addView(android.view.View v){super.addView(v,new FrameLayout.LayoutParams(-1,-2,0));}}',
'com/jchou/commonlibrary/base/AbsActivity.java':'package com.jchou.commonlibrary.base;public class AbsActivity extends android.app.Activity{}',
'com/hailiang/common/util/AppRuntimeData.java':'package com.hailiang.common.util;public class AppRuntimeData{public static long user=17;public static long getUserId(){return user;}}',
'com/nice/room/ui/roomlive/RoomInfo.java':'package com.nice.room.ui.roomlive;public class RoomInfo{public long room=78;public long getClassroomId(){return room;}}',
'com/nice/room/ui/roomlive/interaction/impl/ThirdAppInteraction.java':'''package com.nice.room.ui.roomlive.interaction.impl;
public class ThirdAppInteraction{
 public com.jchou.commonlibrary.base.AbsActivity activity=new com.jchou.commonlibrary.base.AbsActivity();public com.nice.room.ui.roomlive.RoomInfo room=new com.nice.room.ui.roomlive.RoomInfo();
 public ExternalLinkInfo info;public boolean ended,failOpen;public int nativeRequests,nativePages,shortcuts;public ExternalLinkInfo lastRequested;
 public com.jchou.commonlibrary.base.AbsActivity getContext(){return activity;}
 public com.nice.room.ui.roomlive.RoomInfo getRoomInfo(){return room;}
 public ExternalLinkInfo getAppInfo(){return info;}
 public boolean modCanOpenWeb(ExternalLinkInfo expected){return expected!=null && info==expected && !ended;}
 public void modKeepWebShortcut(){shortcuts++;}
 public void modOpenWebInClass(ExternalLinkInfo expected){if(!modCanOpenWeb(expected))return;if(failOpen)throw new IllegalStateException();nativeRequests++;lastRequested=expected;}
 public void whitelistReturned(ExternalLinkInfo request){if(com.hljzjx.classroom.mod.TeacherWebLinks.allowNative(this,request))nativePages++;}
 public static class ExternalLinkInfo{public String app;public ExternalLinkInfo(String url){app=url;}public String getAppId(){return app;}}
}'''
}
for name,text in files.items():
 p=B/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text+'\n','utf-8')
