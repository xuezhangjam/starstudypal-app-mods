package android.content.pm;

import android.content.Intent;
import java.util.*;
public class PackageManager {
    public static final int MATCH_DISABLED_COMPONENTS=512;
    public static class NameNotFoundException extends Exception {}
    public final Map<String,ApplicationInfo> apps=new HashMap<>();
    public final Set<String> privateActivities=new HashSet<>();
    public final Set<String> withoutDesktop=new HashSet<>(), suspended=new HashSet<>();
    public final Map<String,String> routes=new HashMap<>();
    public ApplicationInfo getApplicationInfo(String name,int flags) throws NameNotFoundException {
        if(!apps.containsKey(name)) throw new NameNotFoundException();
        return apps.get(name);
    }
    public CharSequence getApplicationLabel(ApplicationInfo app){return app.label;}
    public boolean isPackageSuspended(String target) throws NameNotFoundException {return suspended.contains(target);}
    public Intent getLaunchIntentForPackage(String target){
        return apps.containsKey(target) && !withoutDesktop.contains(target)?new Intent(target):null;
    }
    public ResolveInfo resolveActivity(Intent intent,int flags){
        if(intent.activity!=null && !intent.activity.equals(routes.get(intent.target)))return null;
        ResolveInfo r=new ResolveInfo();
        r.activityInfo.packageName=intent.target;
        r.activityInfo.exported=!privateActivities.contains(intent.target);
        return r;
    }
}