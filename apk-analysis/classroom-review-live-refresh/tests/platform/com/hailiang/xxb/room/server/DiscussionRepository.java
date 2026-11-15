package com.hailiang.xxb.room.server;
import java.util.*;import kotlin.coroutines.Continuation;public class DiscussionRepository {
public static final List<Call> reads=new ArrayList<Call>(),appends=new ArrayList<Call>();public static Object direct;public static boolean fail;
public static class Call {public long d,g;public boolean history;public Object body;public Continuation c;public void finish(Object value){c.resumeWith(value);}}
public Object appendStroke(Object body,Continuation<? super Result<Boolean>> c){if(fail)throw new RuntimeException("offline");Call call=new Call();call.body=body;call.c=c;appends.add(call);return direct==null?kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED():direct;}
public Object getGroupDiscussionDetail(long d,long g,boolean a,Continuation<? super Result<com.hailiang.xxb.room.server.entity.discussion.GroupDiscussionDetail>> c){Call call=new Call();call.d=d;call.g=g;call.history=a;call.c=c;reads.add(call);return direct==null?kotlin.coroutines.intrinsics.IntrinsicsKt.getCOROUTINE_SUSPENDED():direct;}}
