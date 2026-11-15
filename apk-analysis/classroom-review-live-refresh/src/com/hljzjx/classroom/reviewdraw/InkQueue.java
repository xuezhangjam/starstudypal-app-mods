package com.hljzjx.classroom.reviewdraw;
import java.util.*;

/** Group-scoped automatic uploads. Acceptance and historical readback differ. */
public final class InkQueue {
 public interface Scheduler {void post(Runnable r,long delay);long user();}
 public interface Callback<T>{void done(T value,String error);}
 public interface Transport {void append(Key key,List<Stroke> batch,Callback<Boolean> cb);void read(Key key,Callback<List<Stroke>> cb);}
 public interface Store {Snapshot load(Key key);void save(Key key,Snapshot s);}
 public interface Listener {void changed(Key key);}
 public interface ReadListener extends Listener {void readback(Key key,List<Stroke> strokes);}
 public static final class Key {
  public final long user,room,discussion,group;
  public Key(long u,long r,long d,long g){user=u;room=r;discussion=d;group=g;}
  public boolean valid(){return user>0&&room>0&&discussion>0&&group>0;}
  public String toString(){return user+"_"+room+"_"+discussion+"_"+group;}
  public boolean equals(Object o){return o instanceof Key&&toString().equals(o.toString());}
  public int hashCode(){return toString().hashCode();}
 }
 public static final class Stroke {
  public final String id;public final String value;public final boolean deleted;
  public Stroke(String i,String v,boolean d){id=i;value=v;deleted=d;}
 }
 public static final class Snapshot {
  public final List<Stroke> pending,accepted,unknown;
  public Snapshot(List<Stroke> p,List<Stroke> a,List<Stroke> u){pending=p;accepted=a;unknown=u;}
 }
 private static final class Draft {
  final LinkedHashMap<String,Stroke> pending=new LinkedHashMap<String,Stroke>(),accepted=new LinkedHashMap<String,Stroke>(),unknown=new LinkedHashMap<String,Stroke>();
  final Map<String,Stroke> latest=new HashMap<String,Stroke>(),known=new HashMap<String,Stroke>();
  final List<Callback<List<Stroke>>> waiting=new ArrayList<Callback<List<Stroke>>>();
  Ticket busy;int generation,readGeneration;boolean reading,passiveRead,confirmed;String error="";
 }
 private static final class Ticket {final List<Stroke> batch;boolean done;Ticket(List<Stroke> b){batch=b;}}
 private final Map<Key,Draft> drafts=new HashMap<Key,Draft>();
 private final Scheduler scheduler;private final Transport transport;private final Store store;private final Listener listener;
 public InkQueue(Scheduler s,Transport t,Store p,Listener l){scheduler=s;transport=t;store=p;listener=l;}
 private Draft draft(Key k){Draft d=drafts.get(k);if(d==null){d=new Draft();Snapshot x=store.load(k);if(x!=null){add(d.pending,x.pending);add(d.accepted,x.accepted);add(d.unknown,x.unknown);}add(d.latest,new ArrayList<Stroke>(d.accepted.values()));add(d.latest,new ArrayList<Stroke>(d.unknown.values()));add(d.latest,new ArrayList<Stroke>(d.pending.values()));drafts.put(k,d);}return d;}
 private static void add(Map<String,Stroke> m,List<Stroke> list){if(list!=null)for(Stroke x:list)if(x!=null)m.put(x.id,x);}
 private static boolean same(Stroke a,Stroke b){return a!=null&&b!=null&&a.id.equals(b.id)&&a.deleted==b.deleted&&a.value.equals(b.value);}
 private void changed(Key k,Draft d){LinkedHashMap<String,Stroke> uncertain=new LinkedHashMap<String,Stroke>(d.unknown);if(d.busy!=null)for(Stroke x:d.busy.batch)uncertain.put(x.id,x);store.save(k,new Snapshot(new ArrayList<Stroke>(d.pending.values()),new ArrayList<Stroke>(d.accepted.values()),new ArrayList<Stroke>(uncertain.values())));listener.changed(k);}
 public void put(final Key k,Stroke stroke){if(!k.valid()||k.user!=scheduler.user()||stroke==null)return;Draft d=draft(k);d.pending.put(stroke.id,stroke);d.latest.put(stroke.id,stroke);d.error="";d.confirmed=false;changed(k,d);schedule(k,2000);}
 private void schedule(final Key k,long delay){final Draft d=draft(k);final int gen=++d.generation;scheduler.post(new Runnable(){public void run(){if(gen==d.generation)send(k);}},delay);}
 public void retry(Key k){if(k.user!=scheduler.user())return;Draft d=draft(k);d.error="";d.unknown.clear();changed(k,d);send(k);if(!d.accepted.isEmpty())read(k,null);}
 private void send(final Key k){
  final Draft d=draft(k);if(k.user!=scheduler.user()||d.busy!=null)return;
  ArrayList<Stroke> list=new ArrayList<Stroke>();for(Stroke x:d.pending.values())if(!d.unknown.containsKey(x.id)){list.add(x);if(list.size()==128)break;}
  if(list.isEmpty()){listener.changed(k);return;}
  final Ticket ticket=new Ticket(Collections.unmodifiableList(list));d.busy=ticket;changed(k,d);
  scheduler.post(new Runnable(){public void run(){if(ticket.done)return;for(Stroke x:ticket.batch)d.unknown.put(x.id,x);if(d.busy==ticket)d.busy=null;d.error="上传结果待确认";changed(k,d);read(k,null);}},30000);
  try{transport.append(k,ticket.batch,new Callback<Boolean>(){public void done(final Boolean accepted,final String error){scheduler.post(new Runnable(){public void run(){
   if(ticket.done)return;ticket.done=true;if(d.busy==ticket)d.busy=null;
   boolean current=false;for(Stroke x:ticket.batch)if(same(d.latest.get(x.id),x)&&!same(d.known.get(x.id),x)&&!same(d.accepted.get(x.id),x))current=true;
   if(!current){for(Stroke x:ticket.batch)if(same(d.unknown.get(x.id),x))d.unknown.remove(x.id);changed(k,d);if(!d.pending.isEmpty())schedule(k,0);return;}
   if(Boolean.TRUE.equals(accepted)){
    for(Stroke x:ticket.batch){if(same(d.pending.get(x.id),x))d.pending.remove(x.id);if(same(d.unknown.get(x.id),x))d.unknown.remove(x.id);if(same(d.latest.get(x.id),x)&&!same(d.known.get(x.id),x))d.accepted.put(x.id,x);}
    d.error="";changed(k,d);read(k,null);if(!d.pending.isEmpty())schedule(k,0);
   }else{
    if(accepted==null)for(Stroke x:ticket.batch)d.unknown.put(x.id,x);
    else for(Stroke x:ticket.batch)if(same(d.unknown.get(x.id),x))d.unknown.remove(x.id);
    d.error=error==null?"上传失败，点击同步重试":error;changed(k,d);
    if(accepted==null)read(k,null);
   }
  }},0);}});}catch(Exception e){ticket.done=true;if(d.busy==ticket)d.busy=null;for(Stroke x:ticket.batch)d.unknown.put(x.id,x);d.error="上传结果待确认";changed(k,d);read(k,null);}
 }
 public void read(final Key k,final Callback<List<Stroke>> callback){
  read(k,callback,false);
 }
 /** Observation must not turn a rejected upload into a write-retry loop. */
 public void observe(final Key k,final Callback<List<Stroke>> callback){
  read(k,callback,true);
 }
 private void read(final Key k,final Callback<List<Stroke>> callback,boolean passive){
  final Draft d=draft(k);if(k.user!=scheduler.user()){if(callback!=null)callback.done(null,"账号已切换");return;}
  if(callback!=null)d.waiting.add(callback);if(d.reading){if(!passive)d.passiveRead=false;return;}
  final int gen=++d.readGeneration;d.reading=true;d.passiveRead=passive;listener.changed(k);
  scheduler.post(new Runnable(){public void run(){if(d.reading&&d.readGeneration==gen){d.reading=false;d.readGeneration++;String error="回读超时，笔迹仍保留";if(!d.passiveRead)d.error=error;listener.changed(k);completeRead(d,null,error);}}},30000);
  try{transport.read(k,new Callback<List<Stroke>>(){public void done(final List<Stroke> strokes,final String error){scheduler.post(new Runnable(){public void run(){
   if(gen!=d.readGeneration||!d.reading)return;d.reading=false;
   if(k.user!=scheduler.user()){completeRead(d,null,"账号已切换");return;}
   if(strokes==null){String reason=error==null?"回读失败":error;if(!d.passiveRead)d.error=reason;listener.changed(k);completeRead(d,null,reason);return;}
   Map<String,Stroke> server=new HashMap<String,Stroke>();add(server,strokes);d.known.clear();d.known.putAll(server);if(listener instanceof ReadListener)((ReadListener)listener).readback(k,strokes);
   confirm(d.pending,server,d.latest);confirm(d.accepted,server,d.latest);confirm(d.unknown,server,d.latest);
   d.confirmed=d.pending.isEmpty()&&d.accepted.isEmpty()&&d.unknown.isEmpty();if(!d.passiveRead||d.confirmed)d.error="";changed(k,d);
   completeRead(d,strokes,null);
   if(!d.passiveRead&&!d.pending.isEmpty())schedule(k,0);
  }},0);}});}catch(Exception e){d.reading=false;String error="回读失败，笔迹仍保留";if(!d.passiveRead)d.error=error;listener.changed(k);completeRead(d,null,error);}
 }
 private static void completeRead(Draft d,List<Stroke> strokes,String error){List<Callback<List<Stroke>>> callbacks=new ArrayList<Callback<List<Stroke>>>(d.waiting);d.waiting.clear();for(Callback<List<Stroke>> cb:callbacks)cb.done(strokes,error);}
 private static void confirm(Map<String,Stroke> map,Map<String,Stroke> server,Map<String,Stroke> latest){Iterator<Stroke> it=map.values().iterator();while(it.hasNext()){Stroke x=it.next(),s=server.get(x.id);if(same(x,s)||same(latest.get(x.id),s))it.remove();}}
 public List<Stroke> overlay(Key k,List<Stroke> source){Draft d=draft(k);LinkedHashMap<String,Stroke> merged=new LinkedHashMap<String,Stroke>();add(merged,source);add(merged,new ArrayList<Stroke>(d.accepted.values()));add(merged,new ArrayList<Stroke>(d.unknown.values()));add(merged,new ArrayList<Stroke>(d.pending.values()));ArrayList<Stroke> result=new ArrayList<Stroke>();for(Stroke x:merged.values())if(!x.deleted&&(d.latest.get(x.id)==null||same(x,d.latest.get(x.id))||!d.pending.containsKey(x.id)&&!d.accepted.containsKey(x.id)&&!d.unknown.containsKey(x.id)))result.add(x);return result;}
 public String status(Key k){Draft d=draft(k);if(d.busy!=null)return "笔迹上传中";if(d.reading&&!d.passiveRead)return "正在回读确认";if(!d.error.isEmpty())return d.error;if(!d.unknown.isEmpty())return d.unknown.size()+" 笔上传结果待确认";if(!d.pending.isEmpty())return d.pending.size()+" 笔待自动上传";if(!d.accepted.isEmpty())return "上传已接收 · 回顾尚未回读";return d.confirmed?"笔迹已在服务器回读确认":"回顾 · 可继续画";}
}
