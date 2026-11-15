package com.hailiang.notice.m3e;
import android.app.Activity;import java.util.*;import java.lang.reflect.*;
public final class Data {
 private static final Map<Activity,Object> readers=new WeakHashMap<Activity,Object>();
 public static Object call(Object o,String method,Object...args){try{for(Method m:o.getClass().getMethods())if(m.getName().equals(method)&&m.getParameterTypes().length==args.length)return m.invoke(o,args);}catch(Exception ignored){}return null;}
 public static String str(Object o,String method){Object v=o==null?null:call(o,method);return v==null?"":v.toString();}
 public static int number(Object o,String method){Object v=o==null?null:call(o,method);return v instanceof Number?((Number)v).intValue():0;}
 public static List<?> list(Object o,String method){Object v=call(o,method);return v instanceof List?(List<?>)v:Collections.emptyList();}
 public static Object field(Object o,String name){if(o==null)return null;try{Field f=o.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(o);}catch(Exception e){return null;}}
 public static Object model(Activity a){try{Class<?> cls=Class.forName("com.hailiang.notice.MainActivity");return cls.getMethod("access$getViewModel",cls).invoke(null,a);}catch(Exception e){return null;}}
 public static void read(Activity a,Object item){Object model=model(a);if(model==null){model=readers.get(a);if(model==null)try{model=Class.forName("com.hailiang.notice.viewModel.NoticeListViewModel").getConstructor(android.app.Application.class).newInstance(a.getApplication());readers.put(a,model);}catch(Exception ignored){}}String id=str(item,"getNoticeId");if(model!=null&&!id.isEmpty())call(model,"readNotice",Collections.singletonList(id));}
 public static void dispose(Activity a){Object model=readers.remove(a);if(model!=null)try{Method clear=Class.forName("androidx.lifecycle.ViewModel").getDeclaredMethod("clear");clear.setAccessible(true);clear.invoke(model);}catch(Exception ignored){}}
 public static String identity(android.content.Context c){return "com.hailiang.notice.student";}
 public static Object local(String id){try{
  Object repo=Class.forName("com.hailiang.notice.data.NoticeRepository").newInstance();Method get=repo.getClass().getDeclaredMethod("getNoticeDao");get.setAccessible(true);Object dao=get.invoke(repo);
  for(Object row:list(dao,"getAll"))if(id.equals(str(row,"getId"))){Class<?> converter=Class.forName("com.hailiang.notice.tools.DataBaseToolsKt");return converter.getMethod("convertToNoticeItem",row.getClass()).invoke(null,row);}
 }catch(Exception ignored){}return null;}
}
