package com.hljzjx.samsung;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import com.hailiang.opensdk.LauncherData;

/** No credential writes, saved credentials, network calls, or authentication bypass. */
public final class LoginRecovery {
    private LoginRecovery() {}

    public static boolean shouldClearOnCreate(Bundle savedState) {
        // A fresh login still takes the original clear path. A reconstructed
        // page must not destroy a session established after that page opened.
        return !SamsungDevice.enabled() || savedState == null;
    }

    public static void finishLoginStack(Intent homeIntent, boolean fromLogin) {
        if (SamsungDevice.enabled() && fromLogin) {
            homeIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        }
    }

    public static void resumeSavedLogin(Activity activity, Bundle savedState) {
        if (!SamsungDevice.enabled() || savedState == null || activity.isFinishing() || activity.isDestroyed()) {
            return;
        }
        try {
            String token = LauncherData.INSTANCE.getToken();
            if (token == null || token.length() == 0) {
                return;
            }
            // Normal home requests retain all existing server-side validation.
            // A fresh or auth-expired login is not eligible for this path.
            Intent home = new Intent();
            home.setClassName(activity.getPackageName(), "com.hljzjx.launch.ui.main.MainActivity");
            home.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
            activity.startActivity(home);
            activity.finish();
            Log.i("SamsungLoginFix", "Restored login page returned to existing session");
        } catch (RuntimeException error) {
            // Never clear credentials merely because recovery failed.
            Log.w("SamsungLoginFix", "Login page recovery unavailable");
        }
    }
}
