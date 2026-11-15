package com.hljzjx.teachermod;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.Toast;

/** Inspect and open the teacher home's installed shortcuts. */
public final class InstalledApps {
    private static final String WEB_HOST = "com.hailiang.xxb.web.app";
    private static final String OLD_HOMEWORK = "com.nice.workcloudguider";
    private static final String HOMEWORK = "com.hailiang.workcloud.teacher";
    private static final String STATUS_BUTTON = "mod_local_app_status";
    private static final Shortcut[] SHORTCUTS = {
        new Shortcut("教师课堂", "com.hljzjx.edu.teacher.classroom", "com.hljzjx.teacher.classroom.MainActivity"),
        new Shortcut("教师作业", HOMEWORK, "com.hailiang.workcloud.teacher.MainActivity"),
        new Shortcut("教师作业（旧版）", OLD_HOMEWORK, "com.nice.workcloudguider.ui.MainActivity"),
        new Shortcut("教师错题本", "com.nice.tcherrorbook", "com.nice.tcherrorbook.ui.check.WrongQuestionStatisticActivity"),
        new Shortcut("教师通知", "com.hailiang.notice.teacher", null),
        new Shortcut("应用管控", "com.hailiang.app.control", null),
        new Shortcut("自适应学习", "com.hailiang.xxb.ai.app", null),
        new Shortcut("投屏", "com.hailiang.screencast", null),
        new Shortcut("星动力", "com.hailiang.studentmotivationapp", null),
        new Shortcut("AI 问问", "com.hailiang.webbrowser", null),
    };

    private InstalledApps() {}

    public static boolean offer(Object owner, String requested) {
        if (!(owner instanceof Activity)) return false;
        Activity activity = (Activity) owner;
        if (activity.isFinishing() || activity.isDestroyed()) return false;
        if (WEB_HOST.equals(requested)) {
            showInfo(activity, "网页应用需要平台下发访问链接。");
            return true;
        }
        Shortcut shortcut = find(requested);
        if (shortcut == null) return false;
        PackageManager packages = activity.getPackageManager();
        Probe target = inspect(packages, shortcut);
        if (OLD_HOMEWORK.equals(requested) && target.intent == null) {
            Probe alternate = inspect(packages, find(HOMEWORK));
            if (alternate.intent != null) target = alternate;
        }
        if (target.intent == null) {
            showInfo(activity, target.shortcut.label + " · " + target.status + "\n" + target.shortcut.packageName);
            return true;
        }
        Shortcut destination = target.shortcut;
        new AlertDialog.Builder(activity)
                .setTitle("本机应用")
                .setMessage("「" + destination.label + "」已安装，可以在本机打开。")
                .setNegativeButton("取消", null)
                .setPositiveButton("仍然打开", (dialog, button) -> open(activity, destination))
                .show();
        return true;
    }

    public static void bindStatusButton(Activity activity, LinearLayout emptyState) {
        if (emptyState.findViewWithTag(STATUS_BUTTON) != null) return;
        Button button = new Button(activity);
        button.setText("查看本机应用状态");
        button.setTag(STATUS_BUTTON);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-2, -2);
        params.gravity = Gravity.CENTER_HORIZONTAL;
        emptyState.addView(button, params);
        button.setOnClickListener(view -> showCatalog(activity));
    }

    private static void showCatalog(Activity activity) {
        PackageManager packages = activity.getPackageManager();
        StringBuilder text = new StringBuilder();
        for (Shortcut shortcut : SHORTCUTS) {
            Probe probe = inspect(packages, shortcut);
            text.append(shortcut.label).append(" · ").append(probe.status).append('\n');
        }
        showInfo(activity, text.toString().trim());
    }

    private static void showInfo(Activity activity, String text) {
        new AlertDialog.Builder(activity)
                .setTitle("本机应用状态")
                .setMessage(text)
                .setPositiveButton("知道了", null)
                .show();
    }

    static Probe inspect(PackageManager packages, Shortcut shortcut) {
        String target = shortcut.packageName;
        try {
            ApplicationInfo app = packages.getApplicationInfo(target, PackageManager.MATCH_DISABLED_COMPONENTS);
            if (!app.enabled) return new Probe(shortcut, "已安装，系统已停用", null);
            if (packages.isPackageSuspended(target)) return new Probe(shortcut, "已安装，系统已暂停", null);
            Intent launch = null;
            if (shortcut.activity != null) {
                launch = new Intent().setComponent(new ComponentName(target, shortcut.activity));
            }
            if (!isLaunchable(packages, launch, target)) launch = packages.getLaunchIntentForPackage(target);
            if (isLaunchable(packages, launch, target)) return new Probe(shortcut, "已安装，可打开", launch);
            return new Probe(shortcut, "已安装，无可用启动入口", null);
        } catch (PackageManager.NameNotFoundException ex) {
            return new Probe(shortcut, "本机未找到对应 APK", null);
        } catch (SecurityException ex) {
            return new Probe(shortcut, "系统限制访问", null);
        }
    }

    private static boolean isLaunchable(PackageManager packages, Intent intent, String target) {
        if (intent == null) return false;
        ResolveInfo resolved = packages.resolveActivity(intent, 0);
        return resolved != null && resolved.activityInfo != null && resolved.activityInfo.enabled
                && resolved.activityInfo.exported && target.equals(resolved.activityInfo.packageName);
    }

    private static void open(Activity activity, Shortcut target) {
        if (activity.isFinishing() || activity.isDestroyed()) return;
        Probe current = inspect(activity.getPackageManager(), target);
        if (current.intent != null) {
            try {
                activity.startActivity(current.intent);
                return;
            } catch (ActivityNotFoundException | SecurityException ignored) {
                // The installed state or device policy may have changed since confirmation.
            }
        }
        Toast.makeText(activity, "当前无法打开此应用", Toast.LENGTH_SHORT).show();
    }

    private static Shortcut find(String packageName) {
        for (Shortcut shortcut : SHORTCUTS) {
            if (shortcut.packageName.equals(packageName)) return shortcut;
        }
        return null;
    }

    static final class Shortcut {
        final String label, packageName, activity;

        Shortcut(String label, String packageName, String activity) {
            this.label = label;
            this.packageName = packageName;
            this.activity = activity;
        }
    }

    static final class Probe {
        final Shortcut shortcut;
        final String status;
        final Intent intent;

        Probe(Shortcut shortcut, String status, Intent intent) {
            this.shortcut = shortcut;
            this.status = status;
            this.intent = intent;
        }
    }
}
