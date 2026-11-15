package com.hailiang.notice.m3e;
public final class LayoutPolicy {
 public static boolean twoPane(float widthDp){return widthDp>=840;}
 public static int listWidth(float widthDp){return Math.round(Math.max(320,Math.min(400,(widthDp-112)*.34f)));}
 public static boolean matches(String title,String publisher,String content,String query){
  String q=query==null?"":query.trim().toLowerCase(java.util.Locale.ROOT);if(q.isEmpty())return true;
  String all=(title+" "+publisher+" "+content).toLowerCase(java.util.Locale.ROOT);
  for(String word:q.split("\\s+"))if(!all.contains(word))return false;return true;
 }
 public static String safeName(String name){String n=name==null?"附件":name.replaceAll("[\\\\/:*?\"<>|\\p{Cntrl}]","_").trim();if(n.isEmpty()||n.equals(".")||n.equals(".."))n="附件";return n.length()>180?n.substring(0,180):n;}
}
