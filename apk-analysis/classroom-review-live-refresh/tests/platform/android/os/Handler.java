package android.os;
import java.util.*;public class Handler {
static class Job implements Comparable<Job>{long at;int seq;Runnable r;public int compareTo(Job j){int n=Long.compare(at,j.at);return n==0?Integer.compare(seq,j.seq):n;}}
static PriorityQueue<Job> jobs=new PriorityQueue<Job>();public static long now;static int seq;public Handler(Looper l){} public boolean post(Runnable r){return postDelayed(r,0);}public boolean postDelayed(Runnable r,long d){Job j=new Job();j.at=now+d;j.seq=seq++;j.r=r;jobs.add(j);return true;}
public static void tick(long n){long end=now+n;int loops=0;while(!jobs.isEmpty()&&jobs.peek().at<=end){if(loops++>5000)throw new AssertionError("runaway jobs");Job j=jobs.remove();now=j.at;j.r.run();}now=end;}}
