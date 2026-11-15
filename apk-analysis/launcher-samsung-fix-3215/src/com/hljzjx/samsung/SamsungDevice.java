package com.hljzjx.samsung;

import android.os.Build;

public final class SamsungDevice {
    private SamsungDevice() {}
    public static boolean enabled() {
        return Build.VERSION.SDK_INT >= 29 && "samsung".equalsIgnoreCase(Build.MANUFACTURER);
    }
}
