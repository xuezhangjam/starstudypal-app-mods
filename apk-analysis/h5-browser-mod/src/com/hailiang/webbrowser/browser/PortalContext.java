package com.hailiang.webbrowser.browser;

import android.content.Context;
import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import java.util.HashMap;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;

/** Read only the original launcher's shared H5 context, on a worker thread.
 * No SDK initialization, account persistence, cache updates or token logging.
 */
public final class PortalContext {
    private PortalContext() {}
    public static Map<String, String> values(Context context, Intent intent, JSONObject payload, String url) {
        Map<String, String> out = new HashMap<String, String>();
        Bundle extras = intent.getExtras();
        String client = payload == null ? "" : payload.optString("clientType");
        if (client.isEmpty()) client = extra(extras, "clientType");
        String authority = "Teacher".equals(client) ? "com.hailiang.launcher.tch.provider" : "com.hailiang.launcher.stu.provider";
        String source = BrowserInput.transport(url);
        if (source.contains("${token}")) out.put("token", first(query(context, authority, "token"), extra(extras, "token")));
        if (source.contains("${saasToken}")) out.put("saasToken", first(query(context, authority, "sass_token"), extra(extras, "saasToken"), extra(extras, "sass_token")));
        String json = "";
        for (String field : new String[]{"userId", "classId", "staffId", "campusId", "tenantId", "schoolId"}) if (source.contains("${" + field + "}")) { json = query(context, authority, "hl_user_info"); break; }
        if (json.isEmpty()) json = first(extra(extras, "hl_user_info"), extra(extras, "user_info"));
        JSONObject user = null;
        try { if (!json.isEmpty()) user = new JSONObject(json); } catch (Exception ignored) {}
        for (String field : new String[]{"userId", "classId", "staffId", "campusId", "tenantId", "schoolId"}) {
            String value = user == null ? "" : user.optString(field, "");
            if ("classId".equals(field) && value.isEmpty() && user != null) {
                JSONArray classes = user.optJSONArray("classInfos");
                if (classes != null && classes.length() > 0 && classes.optJSONObject(0) != null) value = classes.optJSONObject(0).optString("classId", "");
            }
            String snake = field.replace("Id", "_id");
            out.put(field, first(value, extra(extras, field), extra(extras, snake)));
        }
        if (source.contains("${deviceId}")) {
            String device = first(extra(extras, "deviceId"), extra(extras, "device_id"));
            if (device.isEmpty()) {
                try {
                    Class<?> sdk = Class.forName("com.hailiang.webbrowser.RomSdk");
                    Object rom = sdk.getConstructor(Context.class).newInstance(context);
                    Object result = sdk.getMethod("getSnCode").invoke(rom);
                    if (result != null) device = String.valueOf(result);
                } catch (Exception unavailable) { device = ""; }
            }
            out.put("deviceId", device);
        }
        return out;
    }
    private static String query(Context context, String authority, String key) {
        try (Cursor cursor = context.getContentResolver().query(Uri.parse("content://" + authority + "/cache"), null, "_key=?", new String[]{key}, null)) {
            if (cursor != null && cursor.moveToFirst()) { int index = cursor.getColumnIndex("_value"); if (index >= 0 && !cursor.isNull(index)) return cursor.getString(index); }
        } catch (Exception unavailable) { /* Continue with the original intent extras. */ }
        return "";
    }
    private static String extra(Bundle extras, String name) {
        if (extras == null) return "";
        try { Object v = extras.get(name); return v == null ? "" : String.valueOf(v); } catch (Exception ignored) { return ""; }
    }
    private static String first(String... values) { for (String s : values) if (s != null && !s.isEmpty() && !"null".equals(s)) return s; return ""; }
}
