package com.nice.room.ui.roomlive.interaction.impl;
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
}
