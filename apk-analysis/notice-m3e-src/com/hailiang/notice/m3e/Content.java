package com.hailiang.notice.m3e;
import java.util.*;import java.util.regex.*;import org.json.*;
public final class Content {
 public static final class Attachment {final String name,url,type;Attachment(String n,String u,String t){name=n;url=u;type=t;}public String getName(){return name;}public String getUrl(){return url;}public String getType(){return type;}public Long getDuration(){return 0L;}}
 public static List<Object> files(String value){List<Object> out=new ArrayList<Object>();if(value==null)return out;try{String s=value.trim();JSONArray list=null;if(s.startsWith("["))list=new JSONArray(s);else if(s.startsWith("{")){JSONObject o=new JSONObject(s);list=o.optJSONArray("fileList");if(list==null)list=o.optJSONArray("files");}if(list!=null)for(int i=0;i<list.length();i++){JSONObject row=list.optJSONObject(i);if(row==null)continue;String url=row.optString("url","");if(url(url))out.add(new Attachment(row.optString("name","附件"),url,row.optString("type","文件")));}}catch(Exception ignored){}return out;}
 public static String html(String content){if(content==null)return "";String s=content.trim();try{if(s.startsWith("{")){JSONObject json=new JSONObject(s);s=json.optString("html",json.optString("content",json.optString("text",s)));}}catch(Exception ignored){}
  s=s.replaceAll("(?is)<(script|style)[^>]*>.*?</\\1>","");if(!s.contains("<"))s=escape(s).replace("\n","<br>");return s;
 }
 public static String escape(String s){return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\"","&quot;");}
 public static boolean url(String value){try{java.net.URI u=new java.net.URI(value);return ("https".equalsIgnoreCase(u.getScheme())||"http".equalsIgnoreCase(u.getScheme()))&&u.getHost()!=null&&u.getUserInfo()==null;}catch(Exception e){return false;}}
 public static List<String[]> table(String html){List<String[]> rows=new ArrayList<String[]>();Matcher tr=Pattern.compile("(?is)<tr\\b[^>]*>(.*?)</tr>").matcher(html);while(tr.find()){List<String> cells=new ArrayList<String>();Matcher td=Pattern.compile("(?is)<t[dh]\\b[^>]*>(.*?)</t[dh]>").matcher(tr.group(1));while(td.find())cells.add(td.group(1));if(!cells.isEmpty())rows.add(cells.toArray(new String[cells.size()]));}return rows;}
}
