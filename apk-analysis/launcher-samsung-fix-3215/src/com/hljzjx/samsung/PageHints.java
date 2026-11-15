package com.hljzjx.samsung;

import android.app.Activity;
import android.app.Application;
import android.content.Context;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.util.Log;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.TextView;
import android.widget.Toast;
import java.lang.ref.WeakReference;
import java.util.Map;
import java.util.WeakHashMap;

/** Samsung-only foreground hints; no framework Toast presenter or overlay permission. */
public final class PageHints {
    private static final Handler MAIN = new Handler(Looper.getMainLooper());
    private static final Map<Toast, CharSequence> TEXT = new WeakHashMap<Toast, CharSequence>();
    private static WeakReference<Activity> resumed = new WeakReference<Activity>(null);
    private static WeakReference<TextView> visible = new WeakReference<TextView>(null);
    private static boolean installed;
    private static String pending;
    private static int pendingDuration;
    private static long pendingUntil;
    private static long revision;

    private PageHints() {}

    public static void init(Application app) {
        if (!SamsungDevice.enabled() || installed) return;
        installed = true;
        app.registerActivityLifecycleCallbacks(new Application.ActivityLifecycleCallbacks() {
            public void onActivityCreated(Activity a, Bundle b) {}
            public void onActivityStarted(Activity a) {}
            public void onActivityStopped(Activity a) {}
            public void onActivitySaveInstanceState(Activity a, Bundle b) {}
            public void onActivityResumed(final Activity a) {
                resumed = new WeakReference<Activity>(a);
                // Wait until content inflation and the decor layout are complete.
                MAIN.post(new Runnable() { public void run() {
                    if (resumed.get() == a && pending != null && SystemClock.uptimeMillis() <= pendingUntil) {
                        String text = pending;
                        int duration = pendingDuration;
                        pending = null;
                        render(a, text, duration);
                    } else if (SystemClock.uptimeMillis() > pendingUntil) {
                        pending = null;
                    }
                }});
            }
            public void onActivityPaused(Activity a) {
                if (resumed.get() == a) {
                    resumed.clear();
                    removeVisible();
                }
            }
            public void onActivityDestroyed(Activity a) {
                if (resumed.get() == a) {
                    resumed.clear();
                    removeVisible();
                }
            }
        });
    }

    public static boolean show(Context ignored, final String message, final int duration) {
        if (!SamsungDevice.enabled()) return false;
        if (message == null || message.length() == 0) return true;
        MAIN.post(new Runnable() { public void run() {
            Activity a = resumed.get();
            if (a == null || a.isFinishing() || a.isDestroyed()) {
                // Keep only the latest transient hint while the app changes pages.
                pending = message;
                pendingDuration = duration;
                pendingUntil = SystemClock.uptimeMillis() + 10000;
                return;
            }
            pending = null;
            render(a, message, duration);
        }});
        return true;
    }

    private static int dp(Activity a, int value) {
        return Math.round(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, value, a.getResources().getDisplayMetrics()));
    }

    private static void render(Activity a, String message, int duration) {
        if (a.isFinishing() || a.isDestroyed() || resumed.get() != a || a.getWindow() == null) return;
        try {
            View decor = a.getWindow().getDecorView();
            if (!(decor instanceof FrameLayout) || !decor.isAttachedToWindow()) return;
            removeVisible();
            TextView hint = new TextView(a);
            hint.setText(message);
            hint.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
            hint.setTextColor(Color.WHITE);
            hint.setGravity(Gravity.CENTER);
            hint.setMaxWidth(Math.max(dp(a, 160), Math.min(dp(a, 560), decor.getWidth() - dp(a, 32))));
            hint.setMaxLines(5);
            hint.setPadding(dp(a, 20), dp(a, 12), dp(a, 20), dp(a, 12));
            GradientDrawable background = new GradientDrawable();
            background.setColor(0xF032302F);
            background.setCornerRadius(dp(a, 24));
            hint.setBackground(background);
            hint.setElevation(dp(a, 6));
            hint.setClickable(false);
            hint.setFocusable(false);
            hint.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);
            FrameLayout.LayoutParams params = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT,
                Gravity.BOTTOM | Gravity.CENTER_HORIZONTAL);
            params.bottomMargin = dp(a, 88);
            params.leftMargin = params.rightMargin = dp(a, 16);
            ((FrameLayout) decor).addView(hint, params);
            visible = new WeakReference<TextView>(hint);
            final long current = ++revision;
            MAIN.postDelayed(new Runnable() { public void run() {
                if (current == revision) removeVisible();
            }}, duration == Toast.LENGTH_LONG ? 3500 : 2200);
        } catch (RuntimeException error) {
            Log.w("SamsungLoginFix", "Page hint unavailable");
        }
    }

    private static void removeVisible() {
        TextView hint = visible.get();
        visible.clear();
        ++revision;
        if (hint != null && hint.getParent() instanceof ViewGroup) {
            ((ViewGroup) hint.getParent()).removeView(hint);
        }
    }

    public static void cancel() {
        if (!SamsungDevice.enabled()) return;
        MAIN.post(new Runnable() { public void run() {
            pending = null;
            removeVisible();
        }});
    }

    public static Toast makeText(Context context, CharSequence message, int duration) {
        Toast toast = Toast.makeText(context, message, duration);
        if (SamsungDevice.enabled()) synchronized (TEXT) { TEXT.put(toast, message == null ? "" : message.toString()); }
        return toast;
    }

    public static Toast makeText(Context context, int resId, int duration) {
        return makeText(context, context.getText(resId), duration);
    }

    public static void showNative(Toast toast) {
        if (!SamsungDevice.enabled()) {
            toast.show();
            return;
        }
        CharSequence text;
        synchronized (TEXT) { text = TEXT.get(toast); }
        if (text == null) text = readText(toast.getView());
        show(null, text == null ? "" : text.toString(), toast.getDuration());
    }

    public static void cancelNative(Toast toast) {
        if (SamsungDevice.enabled()) cancel();
        else toast.cancel();
    }

    private static CharSequence readText(View view) {
        if (view instanceof TextView) return ((TextView) view).getText();
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++) {
                CharSequence text = readText(group.getChildAt(i));
                if (text != null && text.length() != 0) return text;
            }
        }
        return null;
    }
}
