package com.hailiang.handwrite.serialize;
public class PathInfoSerializer {
public String serialize(com.hailiang.handwrite.bean.PathInfo p){return p.userMark+"|"+p.pathID+"|"+p.drawType+"|"+(p.pointsList==null?0:p.pointsList.size());}
public com.hailiang.handwrite.bean.PathInfo deserialize(String s){String[] a=s.split("\\|");com.hailiang.handwrite.bean.PathInfo p=new com.hailiang.handwrite.bean.PathInfo();p.userMark=Long.parseLong(a[0]);p.pathID=Long.parseLong(a[1]);p.drawType=Integer.parseInt(a[2]);p.pointsList=new java.util.ArrayList<Object>();for(int i=0;i<Integer.parseInt(a[3]);i++)p.pointsList.add(new Object());return p;}}
