"""Exercise the installed-app fallback without contacting school services."""
import subprocess

from build import B, JAVA, T

FIXTURES = {
    'android/content/Intent': '''
public class Intent {
    public String target, activity;
    public Intent(){}
    public Intent(String target){this.target=target;}
    public Intent setComponent(ComponentName name){target=name.target; activity=name.activity;return this;}
}''',
    'android/content/ComponentName': '''
public class ComponentName {
    public final String target, activity;
    public ComponentName(String target,String activity){this.target=target;this.activity=activity;}
}''',
    'android/content/ActivityNotFoundException': 'public class ActivityNotFoundException extends RuntimeException {}',
    'android/content/DialogInterface': '''
public interface DialogInterface {
    interface OnClickListener {void onClick(DialogInterface dialog,int which);}
}''',
    'android/content/pm/ApplicationInfo': '''
public class ApplicationInfo {public boolean enabled=true; public String label;}
''',
    'android/content/pm/ActivityInfo': '''
public class ActivityInfo {public boolean enabled=true,exported=true;public String packageName;}
''',
    'android/content/pm/ResolveInfo': 'public class ResolveInfo {public ActivityInfo activityInfo=new ActivityInfo();}',
    'android/content/pm/PackageManager': '''
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
}''',
    'android/app/Activity': '''
import android.content.Intent;
import android.content.pm.PackageManager;
public class Activity {
    public final PackageManager pm=new PackageManager();
    public boolean stopped;
    public Intent opened;
    public boolean isFinishing(){return stopped;}
    public boolean isDestroyed(){return false;}
    public PackageManager getPackageManager(){return pm;}
    public void startActivity(Intent intent){opened=intent;}
}''',
    'android/app/AlertDialog': '''
import android.content.DialogInterface;
public class AlertDialog {
    public static DialogInterface.OnClickListener confirm;
    public static String message;
    public static class Builder {
        public Builder(Activity activity){}
        public Builder setTitle(CharSequence title){return this;}
        public Builder setMessage(CharSequence value){message=value.toString();return this;}
        public Builder setNegativeButton(CharSequence label,DialogInterface.OnClickListener click){return this;}
        public Builder setPositiveButton(CharSequence label,DialogInterface.OnClickListener click){confirm=click;return this;}
        public AlertDialog show(){return new AlertDialog();}
    }
}''',
    'android/view/View': '''
public class View {
    private Object tag;
    public OnClickListener listener;
    public interface OnClickListener {void onClick(View view);}
    public void setTag(Object value){tag=value;}
    public Object getTag(){return tag;}
    public void setOnClickListener(OnClickListener value){listener=value;}
}''',
    'android/view/Gravity': 'public class Gravity {public static final int CENTER_HORIZONTAL=1;}',
    'android/widget/Button': '''
public class Button extends android.view.View {
    public Button(android.app.Activity activity){}
    public void setText(CharSequence text){}
}''',
    'android/widget/LinearLayout': '''
public class LinearLayout extends android.view.View {
    public final java.util.List<android.view.View> children=new java.util.ArrayList<>();
    public static class LayoutParams {
        public int gravity;
        public LayoutParams(int width,int height){}
    }
    public android.view.View findViewWithTag(Object tag){
        for(android.view.View v:children) if(tag.equals(v.getTag()))return v;
        return null;
    }
    public void addView(android.view.View view,LayoutParams params){children.add(view);}
}''',
    'android/widget/Toast': '''
public class Toast {
    public static final int LENGTH_SHORT=0;
    public static int errors;
    public static Toast makeText(android.app.Activity activity,CharSequence text,int length){return new Toast();}
    public void show(){errors++;}
}''',
    'com/hljzjx/teachermod/InstalledAppsTest': '''
import android.app.*;
import android.content.pm.ApplicationInfo;
import android.widget.Toast;
public class InstalledAppsTest {
    private static void check(boolean passed,String reason){if(!passed)throw new AssertionError(reason);}
    public static void main(String[] args){
        Activity activity=new Activity();
        Object owner=activity;
        String classroom="com.hljzjx.edu.teacher.classroom", homework="com.hailiang.workcloud.teacher";
        check(InstalledApps.offer(owner,classroom) && AlertDialog.confirm==null
            && AlertDialog.message.contains("本机未找到"),"missing APK shows its reason and no launch");
        check(!InstalledApps.offer(new Object(),classroom),"presenter cannot host the prompt");
        ApplicationInfo app=new ApplicationInfo(); app.label="课堂";
        activity.pm.apps.put(classroom,app);
        activity.pm.withoutDesktop.add(classroom);
        String route="com.hljzjx.teacher.classroom.MainActivity";
        activity.pm.routes.put(classroom,route);
        check(InstalledApps.offer(owner,classroom) && activity.opened==null,"wait for confirmation");
        AlertDialog.confirm.onClick(null,0);
        check(activity.opened!=null && classroom.equals(activity.opened.target) && route.equals(activity.opened.activity),
            "original teacher classroom route works without a desktop icon");
        activity.opened=null;
        InstalledApps.offer(owner,classroom);
        app.enabled=false;
        AlertDialog.confirm.onClick(null,0);
        check(activity.opened==null && Toast.errors==1 && InstalledApps.offer(owner,classroom)
            && AlertDialog.confirm==null && AlertDialog.message.contains("停用"),"recheck device state");
        app.enabled=true;
        activity.pm.privateActivities.add(classroom);
        check(InstalledApps.offer(owner,classroom) && AlertDialog.confirm==null
            && AlertDialog.message.contains("无可用启动入口"),"private activities remain unavailable");
        activity.pm.privateActivities.clear();
        activity.pm.suspended.add(classroom);
        check(InstalledApps.offer(owner,classroom) && AlertDialog.confirm==null
            && AlertDialog.message.contains("暂停"),"suspended packages stay unavailable");
        activity.pm.apps.put(homework,app);
        check(InstalledApps.offer(owner,"com.nice.workcloudguider"),"recognize current teacher homework package");
        AlertDialog.confirm.onClick(null,0);
        check(homework.equals(activity.opened.target),"only the equivalent homework APK is used");
        activity.pm.apps.put("unrelated.app",app);
        check(!InstalledApps.offer(owner,"unrelated.app"),"fallback limited to known shortcuts");
        android.widget.LinearLayout empty=new android.widget.LinearLayout();
        InstalledApps.bindStatusButton(activity,empty);
        InstalledApps.bindStatusButton(activity,empty);
        check(empty.children.size()==1,"status button added only once");
        android.view.View button=empty.children.get(0);
        button.listener.onClick(button);
        check(AlertDialog.message.contains("教师课堂 · 已安装，系统已暂停")
            && AlertDialog.message.contains("教师作业 · 已安装，可打开"),"catalog shows the actual states");
        activity.stopped=true;
        check(!InstalledApps.offer(owner,homework),"no prompt after host closes");
        System.out.println("Passed installed-only launch, confirmation, revalidation, and native package tests.");
    }
}''',
}


def main():
    source, compiled = B / 'test-fixtures', B / 'test-classes'
    compiled.mkdir(exist_ok=True)
    files = []
    for name, code in FIXTURES.items():
        path = source / (name + '.java')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('package ' + name.rsplit('/', 1)[0].replace('/', '.') + ';\n' + code, 'utf8')
        files.append(path)
    subprocess.run([JAVA, '-jar', T / 'ecj.jar', '-proc:none', '-source', '8', '-target', '8',
                    '-encoding', 'UTF-8', '-d', compiled, *files, *list((B / 'src').rglob('*.java'))], check=True)
    subprocess.run([JAVA, '-cp', compiled, 'com.hljzjx.teachermod.InstalledAppsTest'], check=True)


if __name__ == '__main__':
    main()
