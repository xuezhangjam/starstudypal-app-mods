package com.hailiang.notice.m3e;

import android.app.Activity;
import android.view.View;
import androidx.viewpager2.widget.ViewPager2;
import java.lang.ref.WeakReference;
import java.util.Map;
import java.util.WeakHashMap;

/** Typed, immediate navigation; no detached TabLayout or reflection calls. */
public final class PageNavigator {
    private static final Map<View, ViewPager2.OnPageChangeCallback> callbacks =
            new WeakHashMap<View, ViewPager2.OnPageChangeCallback>();

    private PageNavigator() {}

    public static void select(View view, int index) {
        ((ViewPager2) view).setCurrentItem(index, false);
    }

    public static int current(View view) {
        return ((ViewPager2) view).getCurrentItem();
    }

    public static void install(Activity activity, View view) {
        detach(view);
        final WeakReference<Activity> owner = new WeakReference<Activity>(activity);
        ViewPager2.OnPageChangeCallback callback = new ViewPager2.OnPageChangeCallback() {
            @Override public void onPageSelected(int position) {
                Activity activity = owner.get();
                if (activity != null) NoticeShell.pageSelected(activity, position);
            }
        };
        callbacks.put(view, callback);
        ViewPager2 pager = (ViewPager2) view;
        pager.registerOnPageChangeCallback(callback);
        NoticeShell.pageSelected(activity, pager.getCurrentItem());
    }

    public static void detach(View view) {
        ViewPager2.OnPageChangeCallback callback = callbacks.remove(view);
        if (callback != null) ((ViewPager2) view).unregisterOnPageChangeCallback(callback);
    }
}
