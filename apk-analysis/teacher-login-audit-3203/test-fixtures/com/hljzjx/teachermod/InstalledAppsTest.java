package com.hljzjx.teachermod;

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
}