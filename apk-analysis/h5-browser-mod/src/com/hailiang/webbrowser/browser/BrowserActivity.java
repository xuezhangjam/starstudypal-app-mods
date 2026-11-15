package com.hailiang.webbrowser.browser;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.content.res.Configuration;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.ColorFilter;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PixelFormat;
import android.graphics.RectF;
import android.graphics.drawable.Drawable;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.net.http.SslError;
import android.os.Bundle;
import android.os.Environment;
import android.os.Message;
import android.text.InputType;
import android.text.TextUtils;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputMethodManager;
import android.webkit.CookieManager;
import android.webkit.GeolocationPermissions;
import android.webkit.PermissionRequest;
import android.webkit.SslErrorHandler;
import android.webkit.URLUtil;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.Locale;
import org.json.JSONArray;
import org.json.JSONObject;

/** Standalone browser entry. Uses only Android APIs and the system WebView. */
public final class BrowserActivity extends Activity {
    private static final int FILE_PICKER = 4101, SITE_PERMISSION = 4102, MAX_TABS = 12;
    private static final String[] ENGINES = {"必应", "百度", "Google", "DuckDuckGo"};
    private static final String[] SEARCH = {"https://www.bing.com/search?q=", "https://www.baidu.com/s?wd=", "https://www.google.com/search?q=", "https://duckduckgo.com/?q="};
    private static final String DESKTOP_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";
    private final ArrayList<Tab> tabs = new ArrayList<>();
    private SharedPreferences prefs;
    private LinearLayout root;
    private FrameLayout content;
    private EditText address;
    private ImageButton back, forward, reload;
    private TextView tabCount;
    private ProgressBar progress;
    private int current = -1, bg, surface, ink, muted, accent, accentBg;
    private boolean dark, destroyed;
    private int launchRequest;
    private ValueCallback<Uri[]> fileCallback;
    private PermissionRequest mediaRequest;
    private String geoOrigin;
    private GeolocationPermissions.Callback geoCallback;
    private View customView;
    private WebChromeClient.CustomViewCallback customCallback;
    private int oldSystemUi;

    private final class Tab {
        WebView web;
        String url = "", title = "新标签页", error = "";
        boolean home = true, desktop = false;
        int loading;
    }

    @Override public void onCreate(Bundle state) {
        prefs = getSharedPreferences("standalone_browser", MODE_PRIVATE);
        int mode = prefs.getInt("theme", 0);
        dark = mode == 2 || (mode == 0 && (getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES);
        setTheme(dark ? android.R.style.Theme_Material_NoActionBar : android.R.style.Theme_Material_Light_NoActionBar);
        super.onCreate(state);
        bg = Color.parseColor(dark ? "#15131B" : "#FAF8FF");
        surface = Color.parseColor(dark ? "#282530" : "#EEEBF5");
        ink = Color.parseColor(dark ? "#E9E1F2" : "#211D29");
        muted = Color.parseColor(dark ? "#BDB4CA" : "#696174");
        accent = systemColor(dark ? "system_accent1_200" : "system_accent1_600", dark ? 0xFFD0BCFF : 0xFF6750A4);
        accentBg = systemColor(dark ? "system_accent1_800" : "system_accent1_100", dark ? 0xFF49376C : 0xFFEADDFF);
        getWindow().setStatusBarColor(bg);
        getWindow().setNavigationBarColor(bg);
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
        getWindow().getDecorView().setSystemUiVisibility(dark ? 0 : View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        CookieManager.getInstance().setAcceptCookie(true);
        buildChrome();
        if (state != null) restoreTabs(state);
        if (tabs.isEmpty()) newTab(null, true);
        if (state == null) handleIntent(getIntent());
    }

    private int systemColor(String name, int fallback) {
        int id = getResources().getIdentifier(name, "color", "android");
        return id == 0 ? fallback : getColor(id);
    }
    private int dp(float n) { return (int) (n * getResources().getDisplayMetrics().density + .5f); }
    private GradientDrawable shape(int color, int radius) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color); drawable.setCornerRadius(dp(radius)); return drawable;
    }
    private TextView text(String value, int size, int color) {
        TextView view = new TextView(this); view.setText(value); view.setTextSize(size); view.setTextColor(color); return view;
    }
    private ImageButton button(String icon, String label, View.OnClickListener click) {
        ImageButton b = new ImageButton(this);
        b.setImageDrawable(new Glyph(icon, ink)); b.setContentDescription(label);
        b.setBackground(shape(Color.TRANSPARENT, 22)); b.setPadding(dp(10), dp(10), dp(10), dp(10));
        b.setOnClickListener(click); b.setTooltipText(label);
        b.setLayoutParams(new LinearLayout.LayoutParams(dp(44), dp(44))); return b;
    }

    private void buildChrome() {
        root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setBackgroundColor(bg);
        LinearLayout bar = new LinearLayout(this); bar.setGravity(Gravity.CENTER_VERTICAL); bar.setPadding(dp(6), dp(6), dp(6), dp(6));
        back = button("back", "后退", v -> goBack()); bar.addView(back);
        if (getResources().getConfiguration().screenWidthDp >= 600) {
            forward = button("forward", "前进", v -> { if (tab().web.canGoForward()) { tab().home = false; showTab(); tab().web.goForward(); } }); bar.addView(forward);
            bar.addView(button("home", "主页", v -> home()));
        }
        LinearLayout field = new LinearLayout(this); field.setGravity(Gravity.CENTER_VERTICAL); field.setBackground(shape(surface, 26));
        LinearLayout.LayoutParams fp = new LinearLayout.LayoutParams(0, dp(48), 1); fp.setMargins(dp(3), 0, dp(3), 0); bar.addView(field, fp);
        address = new EditText(this); address.setSingleLine(true); address.setTextSize(15); address.setTextColor(ink); address.setHintTextColor(muted);
        address.setHint("搜索或输入网址"); address.setBackgroundColor(Color.TRANSPARENT); address.setPadding(dp(16), 0, dp(4), 0);
        address.setSelectAllOnFocus(true); address.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        address.setImeOptions(EditorInfo.IME_ACTION_GO);
        address.setOnEditorActionListener((v, action, event) -> {
            if (action == EditorInfo.IME_ACTION_GO || action == EditorInfo.IME_ACTION_SEARCH || (event != null && event.getKeyCode() == KeyEvent.KEYCODE_ENTER && event.getAction() == KeyEvent.ACTION_DOWN)) {
                navigate(address.getText().toString()); return true;
            } return false;
        });
        field.addView(address, new LinearLayout.LayoutParams(0, -1, 1));
        reload = button("reload", "刷新／停止", v -> { if (address.hasFocus()) navigate(address.getText().toString()); else if (tab().loading > 0 && tab().loading < 100) tab().web.stopLoading(); else if (!tab().home) { tab().error = ""; showTab(); tab().web.reload(); } });
        field.addView(reload);
        tabCount = text("1", 15, ink); tabCount.setGravity(Gravity.CENTER); tabCount.setBackground(shape(surface, 14)); tabCount.setContentDescription("标签页"); tabCount.setTooltipText("标签页");
        tabCount.setOnClickListener(v -> showTabs());
        LinearLayout.LayoutParams tp = new LinearLayout.LayoutParams(dp(38), dp(38)); tp.setMargins(dp(5), 0, dp(2), 0); bar.addView(tabCount, tp);
        bar.addView(button("menu", "更多选项", v -> menu()));
        root.addView(bar, new LinearLayout.LayoutParams(-1, dp(60)));
        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal); progress.setMax(100); progress.setProgressTintList(android.content.res.ColorStateList.valueOf(accent)); progress.setVisibility(View.INVISIBLE);
        root.addView(progress, new LinearLayout.LayoutParams(-1, dp(2)));
        content = new FrameLayout(this); content.setBackgroundColor(bg); content.setFocusableInTouchMode(true);
        root.addView(content, new LinearLayout.LayoutParams(-1, 0, 1)); setContentView(root); content.requestFocus();
    }

    private Tab tab() { return tabs.get(current); }
    private boolean isCurrent(Tab t) { return !destroyed && current >= 0 && current < tabs.size() && tabs.get(current) == t; }
    private void newTab(String url, boolean select) {
        ++launchRequest;
        if (tabs.size() >= MAX_TABS) { toast("最多同时打开 12 个标签页"); return; }
        Tab t = new Tab(); t.desktop = prefs.getBoolean("desktop", false); t.web = createWebView(t); tabs.add(t);
        if (select || current < 0) { current = tabs.size() - 1; showTab(); }
        if (url != null && !url.isEmpty()) load(t, url);
        updateChrome();
    }

    private WebView createWebView(final Tab t) {
        WebView web = new WebView(this); web.setBackgroundColor(dark ? 0xFF161616 : Color.WHITE);
        WebSettings s = web.getSettings(); s.setJavaScriptEnabled(true); s.setDomStorageEnabled(true); s.setDatabaseEnabled(true);
        s.setLoadWithOverviewMode(true); s.setUseWideViewPort(true); s.setSupportZoom(true); s.setBuiltInZoomControls(true); s.setDisplayZoomControls(false);
        s.setAllowFileAccess(false); s.setAllowContentAccess(true); s.setMediaPlaybackRequiresUserGesture(true);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW); s.setSupportMultipleWindows(true); s.setJavaScriptCanOpenWindowsAutomatically(false);
        if (t.desktop) s.setUserAgentString(DESKTOP_UA);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest r) {
                return external(r.getUrl(), r.hasGesture(), r.isForMainFrame());
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view, String url) { return external(Uri.parse(url), true, true); }
            @Override public void onPageStarted(WebView view, String url, android.graphics.Bitmap icon) {
                t.url = url; t.error = ""; t.home = false; t.loading = 1;
                if (isCurrent(t)) { showTab(); updateChrome(); }
            }
            @Override public void onPageFinished(WebView view, String url) {
                t.url = url; t.loading = 100; CookieManager.getInstance().flush();
                if (t.error.isEmpty() && BrowserInput.isWebUrl(url)) remember("history", url, t.title, 200);
                if (isCurrent(t)) updateChrome();
            }
            @Override public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) { t.error = String.valueOf(error.getDescription()); t.loading = 100; if (isCurrent(t)) showTab(); }
            }
            @Override public void onReceivedSslError(WebView view, SslErrorHandler handler, SslError error) {
                handler.cancel();
                if (error.getUrl().equals(t.url)) { t.error = "网站证书验证失败，请检查网址、设备日期或网络后重试。"; t.loading = 100; if (isCurrent(t)) showTab(); }
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override public void onProgressChanged(WebView view, int value) { t.loading = value; if (isCurrent(t)) updateChrome(); }
            @Override public void onReceivedTitle(WebView view, String value) { if (value != null && !value.isEmpty()) t.title = value; if (isCurrent(t)) updateChrome(); }
            @Override public boolean onCreateWindow(WebView view, boolean dialog, boolean gesture, Message result) {
                if (!gesture || tabs.size() >= MAX_TABS) return false;
                newTab(null, true); tab().home = false; showTab();
                ((WebView.WebViewTransport) result.obj).setWebView(tab().web); result.sendToTarget(); return true;
            }
            @Override public void onCloseWindow(WebView window) { int index = tabs.indexOf(t); if (index >= 0) closeTab(index); }
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;
                Intent pick = new Intent(Intent.ACTION_OPEN_DOCUMENT); pick.addCategory(Intent.CATEGORY_OPENABLE);
                LinkedHashSet<String> types = new LinkedHashSet<>();
                for (String value : params.getAcceptTypes()) if (value != null) for (String type : value.split(",")) if (type.trim().contains("/")) types.add(type.trim());
                pick.setType(types.size() == 1 ? types.iterator().next() : "*/*");
                if (types.size() > 1) pick.putExtra(Intent.EXTRA_MIME_TYPES, types.toArray(new String[0]));
                pick.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, params.getMode() == FileChooserParams.MODE_OPEN_MULTIPLE);
                try { startActivityForResult(pick, FILE_PICKER); } catch (Exception e) { fileCallback.onReceiveValue(null); fileCallback = null; toast("未找到文件选择器"); }
                return true;
            }
            @Override public void onPermissionRequest(PermissionRequest request) { runOnUiThread(() -> askMedia(request)); }
            @Override public void onPermissionRequestCanceled(PermissionRequest request) { if (mediaRequest == request) mediaRequest = null; }
            @Override public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback callback) { askLocation(origin, callback); }
            @Override public void onGeolocationPermissionsHidePrompt() { if (geoCallback != null) { geoCallback.invoke(geoOrigin, false, false); geoCallback = null; } }
            @Override public void onShowCustomView(View view, CustomViewCallback callback) { showFullscreen(view, callback); }
            @Override public void onHideCustomView() { hideFullscreen(); }
        });
        web.setOnLongClickListener(v -> {
            WebView.HitTestResult hit = web.getHitTestResult();
            if (hit == null) return false;
            if (hit.getType() == WebView.HitTestResult.SRC_ANCHOR_TYPE) { linkMenu(hit.getExtra(), false); return true; }
            if (hit.getType() == WebView.HitTestResult.IMAGE_TYPE || hit.getType() == WebView.HitTestResult.SRC_IMAGE_ANCHOR_TYPE) { linkMenu(hit.getExtra(), true); return true; }
            return false;
        });
        web.setDownloadListener((url, agent, disposition, mime, length) -> download(url, agent, disposition, mime));
        return web;
    }

    private void showTab() {
        if (destroyed || current < 0 || current >= tabs.size()) return;
        Tab t = tab(); content.removeAllViews();
        for (Tab other : tabs) { if (other == t && !t.home) other.web.onResume(); else other.web.onPause(); }
        if (t.home) content.addView(homeView(), new FrameLayout.LayoutParams(-1, -1));
        else if (!t.error.isEmpty()) content.addView(errorView(t), new FrameLayout.LayoutParams(-1, -1));
        else { if (t.web.getParent() != null) ((ViewGroup) t.web.getParent()).removeView(t.web); content.addView(t.web, new FrameLayout.LayoutParams(-1, -1)); }
        content.requestFocus(); updateChrome();
    }

    private View homeView() {
        ScrollView scroll = new ScrollView(this); scroll.setFillViewport(true);
        LinearLayout page = new LinearLayout(this); page.setOrientation(LinearLayout.VERTICAL); page.setGravity(Gravity.CENTER); page.setPadding(dp(24), dp(32), dp(24), dp(32));
        ImageView logo = new ImageView(this); logo.setImageDrawable(getApplicationInfo().loadIcon(getPackageManager())); page.addView(logo, new LinearLayout.LayoutParams(dp(68), dp(68)));
        TextView title = text("H5 浏览器", 30, ink); title.setGravity(Gravity.CENTER); title.setPadding(0, dp(20), 0, dp(8)); page.addView(title);
        TextView subtitle = text("从一个网址，发现更多", 15, muted); subtitle.setGravity(Gravity.CENTER); page.addView(subtitle);
        TextView input = chip("搜索或输入网址  →", () -> { address.requestFocus(); ((InputMethodManager) getSystemService(INPUT_METHOD_SERVICE)).showSoftInput(address, InputMethodManager.SHOW_IMPLICIT); });
        LinearLayout.LayoutParams ip = new LinearLayout.LayoutParams(dp(280), dp(56)); ip.setMargins(0, dp(30), 0, dp(20)); page.addView(input, ip);
        LinearLayout shortcuts = new LinearLayout(this); shortcuts.setGravity(Gravity.CENTER);
        shortcuts.addView(chip("必应", () -> navigate("https://www.bing.com")));
        shortcuts.addView(chip("百度", () -> navigate("https://www.baidu.com")));
        shortcuts.addView(chip("书签", () -> showSaved("bookmarks", "书签")));
        page.addView(shortcuts);
        TextView hint = text("长按链接可在新标签页打开 · 更多功能在右上角菜单", 12, muted);
        hint.setGravity(Gravity.CENTER); hint.setPadding(0, dp(30), 0, 0); page.addView(hint);
        scroll.addView(page, new ScrollView.LayoutParams(-1, -1)); return scroll;
    }

    private TextView chip(String label, Runnable action) {
        TextView v = text(label, 15, accent); v.setGravity(Gravity.CENTER); v.setPadding(dp(18), dp(14), dp(18), dp(14));
        v.setBackground(shape(accentBg, 22)); LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-2, -2); p.setMargins(dp(4), dp(4), dp(4), dp(4)); v.setLayoutParams(p);
        v.setOnClickListener(w -> action.run()); return v;
    }
    private View errorView(Tab t) {
        LinearLayout page = new LinearLayout(this); page.setOrientation(LinearLayout.VERTICAL); page.setGravity(Gravity.CENTER); page.setPadding(dp(32), dp(24), dp(32), dp(24));
        TextView title = text("暂时无法打开网页", 24, ink); title.setGravity(Gravity.CENTER); page.addView(title);
        TextView detail = text(t.error, 15, muted); detail.setGravity(Gravity.CENTER); detail.setPadding(0, dp(16), 0, dp(24)); page.addView(detail);
        page.addView(chip("重新加载", () -> { t.error = ""; showTab(); t.web.loadUrl(t.url); })); return page;
    }

    private void updateChrome() {
        if (current < 0 || current >= tabs.size() || address == null) return;
        Tab t = tab(); if (!address.hasFocus()) address.setText(t.home ? "" : t.url);
        back.setAlpha(t.home || !t.web.canGoBack() ? .55f : 1f);
        if (forward != null) forward.setAlpha(t.web.canGoForward() ? 1f : .35f);
        boolean loading = !t.home && t.error.isEmpty() && t.loading > 0 && t.loading < 100;
        progress.setProgress(t.loading); progress.setVisibility(loading ? View.VISIBLE : View.INVISIBLE);
        reload.setImageDrawable(new Glyph(loading ? "close" : "reload", ink));
        tabCount.setText(String.valueOf(tabs.size())); setTitle(t.home ? "H5 浏览器" : t.title);
    }
    private void navigate(String input) {
        ++launchRequest;
        String url = BrowserInput.resolve(input, SEARCH[Math.max(0, Math.min(SEARCH.length - 1, prefs.getInt("engine", 0)))]);
        if (url.isEmpty()) { if (input != null && !input.trim().isEmpty()) toast("网址格式无法识别"); return; }
        ((InputMethodManager) getSystemService(INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(address.getWindowToken(), 0);
        address.clearFocus(); content.requestFocus(); load(tab(), url);
    }
    private void load(Tab t, String url) { t.home = false; t.error = ""; t.url = url; t.loading = 1; if (isCurrent(t)) showTab(); t.web.loadUrl(url); }
    private void home() { ++launchRequest; tab().home = true; address.clearFocus(); showTab(); }
    private void goBack() {
        ++launchRequest;
        if (customView != null) { hideFullscreen(); return; }
        Tab t = tab();
        if (t.home && !t.url.isEmpty()) { t.home = false; showTab(); }
        else if (!t.home && t.web.canGoBack()) { t.error = ""; t.web.goBack(); }
        else if (!t.home) home(); else super.onBackPressed();
    }
    @Override public void onBackPressed() { goBack(); }

    private void menu() {
        String[] items = {"新建标签页", "主页", "前进", "添加书签", "书签", "历史记录", "下载内容", "分享网页", "复制网址", "在网页中查找", (tab().desktop ? "✓ " : "") + "桌面版网站", "外观", "搜索引擎", "清除浏览数据", "关于"};
        new AlertDialog.Builder(this).setTitle("浏览器").setItems(items, (d, which) -> {
            switch (which) {
                case 0: newTab(null, true); break;
                case 1: home(); break;
                case 2: if (tab().web.canGoForward()) { tab().home = false; showTab(); tab().web.goForward(); } break;
                case 3: addBookmark(); break;
                case 4: showSaved("bookmarks", "书签"); break;
                case 5: showSaved("history", "历史记录"); break;
                case 6: try { startActivity(new Intent(DownloadManager.ACTION_VIEW_DOWNLOADS)); } catch (Exception e) { toast("可在系统“文件”中的 Download 文件夹查看"); } break;
                case 7: if (hasPage()) { Intent share = new Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT, tab().url); startActivity(Intent.createChooser(share, "分享网页")); } break;
                case 8: if (hasPage()) { ((ClipboardManager) getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("网址", tab().url)); toast("已复制网址"); } break;
                case 9: findInPage(); break;
                case 10: tab().desktop = !tab().desktop; prefs.edit().putBoolean("desktop", tab().desktop).apply(); tab().web.getSettings().setUserAgentString(tab().desktop ? DESKTOP_UA : WebSettings.getDefaultUserAgent(this)); if (!tab().home) tab().web.reload(); break;
                case 11: chooseTheme(); break;
                case 12: chooseEngine(); break;
                case 13: clearData(); break;
                case 14: new AlertDialog.Builder(this).setTitle("H5 浏览器").setMessage("1.0.13 · 浏览器修改版 2\n\n使用系统 Android WebView。支持独立启动、网址与搜索、多标签页、书签、历史、下载和文件上传。\n\n基于 H5应用修改；修改：xuezhangjam / Codex").setPositiveButton("知道了", null).show(); break;
            }
        }).show();
    }
    private boolean hasPage() { if (tab().home || !BrowserInput.isWebUrl(tab().url)) { toast("先打开一个网页"); return false; } return true; }

    private void showTabs() {
        LinearLayout list = new LinearLayout(this); list.setOrientation(LinearLayout.VERTICAL); list.setPadding(dp(12), dp(8), dp(12), dp(8));
        ScrollView scroll = new ScrollView(this); scroll.addView(list);
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("标签页 · " + tabs.size()).setView(scroll).setPositiveButton("新建标签页", (d, w) -> newTab(null, true)).setNegativeButton("完成", null).create();
        for (int i = 0; i < tabs.size(); i++) {
            final int index = i; Tab t = tabs.get(i); LinearLayout row = new LinearLayout(this); row.setGravity(Gravity.CENTER_VERTICAL); row.setPadding(dp(8), dp(4), dp(2), dp(4));
            row.setBackground(shape(i == current ? accentBg : Color.TRANSPARENT, 16));
            TextView title = text((i == current ? "●  " : "") + (t.home ? "新标签页" : t.title) + (t.home ? "" : "\n" + t.url), 14, ink); title.setMaxLines(2); title.setEllipsize(TextUtils.TruncateAt.END); title.setPadding(dp(8), dp(10), 0, dp(10));
            row.addView(title, new LinearLayout.LayoutParams(0, -2, 1)); title.setOnClickListener(v -> { current = index; address.clearFocus(); showTab(); dialog.dismiss(); });
            row.addView(button("close", "关闭标签页", v -> { closeTab(index); dialog.dismiss(); })); list.addView(row);
        } dialog.show();
    }
    private void closeTab(int index) {
        Tab removed = tabs.get(index); removed.web.stopLoading(); if (removed.web.getParent() != null) ((ViewGroup) removed.web.getParent()).removeView(removed.web);
        removed.web.destroy(); tabs.remove(index);
        if (tabs.isEmpty()) { current = -1; newTab(null, true); }
        else { if (current > index) current--; current = Math.min(current, tabs.size() - 1); showTab(); }
    }

    private JSONArray saved(String key) { try { return new JSONArray(prefs.getString(key, "[]")); } catch (Exception e) { return new JSONArray(); } }
    private void remember(String key, String url, String title, int limit) {
        try {
            JSONArray next = new JSONArray(); next.put(new JSONObject().put("url", url).put("title", title).put("time", System.currentTimeMillis()));
            JSONArray old = saved(key); for (int i = 0; i < old.length() && next.length() < limit; i++) if (!url.equals(old.getJSONObject(i).optString("url"))) next.put(old.getJSONObject(i));
            prefs.edit().putString(key, next.toString()).apply();
        } catch (Exception ignored) {}
    }
    private void addBookmark() {
        if (!hasPage()) return;
        EditText name = new EditText(this); name.setSingleLine(true); name.setText(tab().title); name.setSelectAllOnFocus(true);
        new AlertDialog.Builder(this).setTitle("添加书签").setView(padded(name)).setPositiveButton("保存", (d, w) -> { remember("bookmarks", tab().url, name.getText().toString(), 500); toast("已保存书签"); }).setNegativeButton("取消", null).show();
    }
    private View padded(View child) { FrameLayout box = new FrameLayout(this); box.setPadding(dp(22), dp(8), dp(22), dp(8)); box.addView(child, new FrameLayout.LayoutParams(-1, -2)); return box; }
    private void showSaved(String key, String title) {
        JSONArray data = saved(key); if (data.length() == 0) { toast("还没有" + title); return; }
        ArrayList<String> labels = new ArrayList<>(); for (int i = 0; i < data.length(); i++) { JSONObject item = data.optJSONObject(i); labels.add(item.optString("title") + "\n" + item.optString("url")); }
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle(title + " · " + data.length()).setItems(labels.toArray(new String[0]), (d, index) -> navigate(data.optJSONObject(index).optString("url"))).setNegativeButton("关闭", null).create();
        dialog.setOnShowListener(d -> dialog.getListView().setOnItemLongClickListener((parent, view, index, id) -> {
            new AlertDialog.Builder(this).setTitle("删除这一条" + title + "？").setPositiveButton("删除", (dd, w) -> { JSONArray next = new JSONArray(); for (int j = 0; j < data.length(); j++) if (j != index) next.put(data.optJSONObject(j)); prefs.edit().putString(key, next.toString()).apply(); dialog.dismiss(); if (next.length() > 0) showSaved(key, title); }).setNegativeButton("取消", null).show(); return true;
        })); dialog.show();
    }
    private void chooseEngine() { new AlertDialog.Builder(this).setTitle("搜索引擎").setSingleChoiceItems(ENGINES, prefs.getInt("engine", 0), (d, which) -> { prefs.edit().putInt("engine", which).apply(); d.dismiss(); }).setNegativeButton("取消", null).show(); }
    private void chooseTheme() { new AlertDialog.Builder(this).setTitle("外观").setSingleChoiceItems(new String[]{"跟随系统", "浅色", "深色"}, prefs.getInt("theme", 0), (d, which) -> { prefs.edit().putInt("theme", which).apply(); d.dismiss(); recreate(); }).setNegativeButton("取消", null).show(); }
    private void findInPage() {
        if (!hasPage()) return;
        EditText query = new EditText(this); query.setSingleLine(true); query.setHint("输入要查找的文字");
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("在网页中查找").setView(padded(query)).setPositiveButton("查找", null).setNeutralButton("下一个", null).setNegativeButton("完成", (d, w) -> tab().web.clearMatches()).create();
        dialog.setOnShowListener(d -> { dialog.getButton(-1).setOnClickListener(v -> tab().web.findAllAsync(query.getText().toString())); dialog.getButton(-3).setOnClickListener(v -> tab().web.findNext(true)); }); dialog.show();
    }
    private void clearData() {
        String[] names = {"历史记录", "缓存", "Cookie 与网站登录状态"}; boolean[] choices = {true, true, false};
        new AlertDialog.Builder(this).setTitle("清除浏览数据").setMultiChoiceItems(names, choices, (d, which, checked) -> choices[which] = checked).setPositiveButton("清除", (d, w) -> {
            if (choices[0]) { prefs.edit().remove("history").apply(); for (Tab t : tabs) t.web.clearHistory(); }
            if (choices[1]) for (Tab t : tabs) t.web.clearCache(true);
            if (choices[2]) { CookieManager.getInstance().removeAllCookies(null); CookieManager.getInstance().flush(); android.webkit.WebStorage.getInstance().deleteAllData(); }
            toast("已清除所选数据");
        }).setNegativeButton("取消", null).show();
    }

    private void linkMenu(String url, boolean image) {
        if (url == null || url.isEmpty()) return;
        new AlertDialog.Builder(this).setTitle(image ? "图片" : "链接").setItems(new String[]{"在新标签页打开", "复制链接", image ? "下载图片" : "下载链接文件"}, (d, which) -> {
            if (which == 0) { if (BrowserInput.isWebUrl(url)) newTab(url, true); else external(Uri.parse(url), true, true); }
            if (which == 1) { ((ClipboardManager) getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("链接", url)); toast("已复制链接"); }
            if (which == 2) download(url, tab().web.getSettings().getUserAgentString(), null, null);
        }).setNegativeButton("取消", null).show();
    }

    private boolean external(Uri uri, boolean gesture, boolean mainFrame) {
        String scheme = uri.getScheme() == null ? "" : uri.getScheme().toLowerCase(Locale.ROOT);
        if (scheme.equals("http") || scheme.equals("https") || uri.toString().equals("about:blank")) return false;
        if (scheme.equals("javascript") || scheme.equals("file") || scheme.equals("content") || scheme.equals("data") || !mainFrame || !gesture) return true;
        new AlertDialog.Builder(this).setTitle("打开外部应用？").setMessage(uri.toString()).setPositiveButton("打开", (d, w) -> {
            try {
                Intent intent = scheme.equals("intent") ? Intent.parseUri(uri.toString(), Intent.URI_INTENT_SCHEME) : new Intent(Intent.ACTION_VIEW, uri);
                String fallback = intent.getStringExtra("browser_fallback_url");
                intent.addCategory(Intent.CATEGORY_BROWSABLE); intent.setComponent(null); intent.setSelector(null); intent.removeExtra("browser_fallback_url");
                if (getPackageName().equals(intent.getPackage())) { toast("无法打开此链接"); return; }
                try { startActivity(intent); } catch (Exception e) { if (BrowserInput.isWebUrl(fallback)) navigate(fallback); else toast("未找到可打开此链接的应用"); }
            } catch (Exception e) { toast("无法打开此链接"); }
        }).setNegativeButton("取消", null).show(); return true;
    }

    private void download(String url, String agent, String disposition, String mime) {
        if (!BrowserInput.isWebUrl(url)) { toast("此链接无法交给系统下载，请使用网页的保存或导出功能"); return; }
        final String name = URLUtil.guessFileName(url, disposition, mime).replaceAll("[\\\\/:*?\"<>|]", "_");
        new AlertDialog.Builder(this).setTitle("下载文件").setMessage(name).setPositiveButton("下载", (d, w) -> {
            try {
                DownloadManager.Request request = new DownloadManager.Request(Uri.parse(url));
                String cookies = CookieManager.getInstance().getCookie(url); if (cookies != null) request.addRequestHeader("Cookie", cookies);
                if (agent != null) request.addRequestHeader("User-Agent", agent);
                if (BrowserInput.isWebUrl(tab().url)) request.addRequestHeader("Referer", tab().url);
                if (mime != null) request.setMimeType(mime);
                request.setTitle(name).setDescription("H5 浏览器").setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED).setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, name);
                ((DownloadManager) getSystemService(DOWNLOAD_SERVICE)).enqueue(request); toast("已加入下载，可在“下载内容”中查看");
            } catch (Exception e) { toast("无法开始下载：" + e.getMessage()); }
        }).setNegativeButton("取消", null).show();
    }

    private void askMedia(PermissionRequest request) {
        if (!"https".equalsIgnoreCase(request.getOrigin().getScheme())) { request.deny(); return; }
        ArrayList<String> supported = new ArrayList<>(); for (String resource : request.getResources()) if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(resource) || PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(resource)) supported.add(resource);
        if (supported.isEmpty()) { request.deny(); return; }
        new AlertDialog.Builder(this).setTitle("网站请求权限").setMessage(request.getOrigin() + "\n\n允许此网站使用它请求的摄像头或麦克风？").setPositiveButton("允许", (d, w) -> {
            if (mediaRequest != null) mediaRequest.deny(); mediaRequest = request;
            ArrayList<String> needed = new ArrayList<>();
            if (supported.contains(PermissionRequest.RESOURCE_VIDEO_CAPTURE) && checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) needed.add(Manifest.permission.CAMERA);
            if (supported.contains(PermissionRequest.RESOURCE_AUDIO_CAPTURE) && checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) needed.add(Manifest.permission.RECORD_AUDIO);
            if (needed.isEmpty()) grantMedia(); else requestPermissions(needed.toArray(new String[0]), SITE_PERMISSION);
        }).setNegativeButton("拒绝", (d, w) -> request.deny()).setOnCancelListener(d -> request.deny()).show();
    }
    private void grantMedia() {
        PermissionRequest r = mediaRequest; mediaRequest = null; if (r == null) return;
        ArrayList<String> granted = new ArrayList<>(); for (String resource : r.getResources()) {
            if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(resource) && checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) granted.add(resource);
            if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(resource) && checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) granted.add(resource);
        }
        if (granted.isEmpty()) r.deny(); else r.grant(granted.toArray(new String[0]));
    }
    private void askLocation(String origin, GeolocationPermissions.Callback callback) {
        if (!origin.startsWith("https://")) { callback.invoke(origin, false, false); return; }
        new AlertDialog.Builder(this).setTitle("网站请求位置").setMessage(origin + "\n\n允许此网站获取设备位置？").setPositiveButton("允许", (d, w) -> {
            if (geoCallback != null) geoCallback.invoke(geoOrigin, false, false); geoOrigin = origin; geoCallback = callback;
            if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED || checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED) grantLocation();
            else requestPermissions(new String[]{Manifest.permission.ACCESS_COARSE_LOCATION, Manifest.permission.ACCESS_FINE_LOCATION}, SITE_PERMISSION + 1);
        }).setNegativeButton("拒绝", (d, w) -> callback.invoke(origin, false, false)).setOnCancelListener(d -> callback.invoke(origin, false, false)).show();
    }
    private void grantLocation() { if (geoCallback != null) { boolean allowed = checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED || checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED; geoCallback.invoke(geoOrigin, allowed, false); geoCallback = null; } }
    @Override public void onRequestPermissionsResult(int code, String[] permissions, int[] results) { super.onRequestPermissionsResult(code, permissions, results); if (code == SITE_PERMISSION) grantMedia(); if (code == SITE_PERMISSION + 1) grantLocation(); }
    @Override public void onActivityResult(int code, int result, Intent data) {
        super.onActivityResult(code, result, data);
        if (code == FILE_PICKER && fileCallback != null) {
            ArrayList<Uri> uris = new ArrayList<>(); if (result == RESULT_OK && data != null) { ClipData clip = data.getClipData(); if (clip != null) for (int i = 0; i < clip.getItemCount(); i++) uris.add(clip.getItemAt(i).getUri()); else if (data.getData() != null) uris.add(data.getData()); }
            fileCallback.onReceiveValue(uris.isEmpty() ? null : uris.toArray(new Uri[0])); fileCallback = null;
        }
    }

    private void showFullscreen(View view, WebChromeClient.CustomViewCallback callback) {
        if (customView != null) { callback.onCustomViewHidden(); return; }
        customView = view; customCallback = callback; oldSystemUi = getWindow().getDecorView().getSystemUiVisibility();
        ((FrameLayout) getWindow().getDecorView()).addView(view, new FrameLayout.LayoutParams(-1, -1));
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
    }
    private void hideFullscreen() {
        if (customView == null) return; ((ViewGroup) customView.getParent()).removeView(customView); customView = null;
        getWindow().getDecorView().setSystemUiVisibility(oldSystemUi); if (customCallback != null) { customCallback.onCustomViewHidden(); customCallback = null; }
    }

    @Override public void onNewIntent(Intent intent) { super.onNewIntent(intent); setIntent(intent); handleIntent(intent); }
    private void handleIntent(Intent intent) {
        if (intent == null) return;
        String value = null;
        JSONObject payload = null;
        try {
            if (Intent.ACTION_SEND.equals(intent.getAction())) value = intent.getStringExtra(Intent.EXTRA_TEXT);
            String json = intent.getStringExtra("jsonData");
            if (json != null) { try { payload = new JSONObject(json); value = payload.optString("url", value); } catch (Exception malformed) { payload = null; } }
            if (value == null || value.isEmpty()) for (String key : new String[]{"url", "URL", "htmlUrl"}) { String extra = intent.getStringExtra(key); if (extra != null && !extra.isEmpty()) { value = extra; break; } }
            Uri data = intent.getData(); if ((value == null || value.isEmpty()) && data != null) {
                if ("hlxxb".equalsIgnoreCase(data.getScheme())) value = data.getQueryParameter("url"); else if ("http".equalsIgnoreCase(data.getScheme()) || "https".equalsIgnoreCase(data.getScheme())) value = data.toString();
            }
            if (value != null && !value.trim().isEmpty()) {
                boolean legacy = data != null && "hlxxb".equalsIgnoreCase(data.getScheme()) && "hailiang.web.com".equalsIgnoreCase(data.getHost()) && "/openUrl".equals(data.getPath());
                String component = intent.getComponent() == null ? "" : intent.getComponent().getClassName();
                legacy = legacy || component.equals("com.hailiang.webbrowser.WebViewActivity") || component.equals("com.hailiang.webbrowser.LaunchDispatcherActivity");
                if (Intent.ACTION_SEND.equals(intent.getAction()) && payload == null) navigate(value);
                else openAppLink(value, legacy, intent, payload);
            }
        } catch (Exception e) { toast("链接格式无法识别，请直接输入网址"); }
    }

    private void openAppLink(String value, boolean legacy, Intent intent, JSONObject payload) {
        final int request = ++launchRequest;
        if (legacy && BrowserInput.hasTemplate(value)) {
            new Thread(() -> {
                String filled = BrowserInput.expandTemplates(value, PortalContext.values(getApplicationContext(), intent, payload, value));
                String url = BrowserInput.directUrl(filled);
                runOnUiThread(() -> { if (!destroyed && request == launchRequest) finishAppLink(url); });
            }, "h5-launch-context").start();
        } else finishAppLink(BrowserInput.directUrl(value));
    }

    private void finishAppLink(String url) {
        if (url.isEmpty()) { toast("应用网址格式无法识别，未进行搜索"); return; }
        if (!tab().home) { if (tabs.size() >= MAX_TABS) { toast("请先关闭一个标签页"); return; } newTab(null, true); }
        ((InputMethodManager) getSystemService(INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(address.getWindowToken(), 0);
        address.clearFocus(); content.requestFocus(); load(tab(), url);
    }

    @Override public void onSaveInstanceState(Bundle state) {
        super.onSaveInstanceState(state); ArrayList<Bundle> items = new ArrayList<>();
        for (Tab t : tabs) { Bundle item = new Bundle(); item.putString("url", t.url); item.putString("title", t.title); item.putBoolean("home", t.home); item.putBoolean("desktop", t.desktop); Bundle web = new Bundle(); t.web.saveState(web); item.putBundle("web", web); items.add(item); }
        state.putParcelableArrayList("browser_tabs", items); state.putInt("browser_current", current);
    }
    private void restoreTabs(Bundle state) {
        ArrayList<Bundle> items = state.getParcelableArrayList("browser_tabs"); if (items == null) return;
        for (Bundle item : items) { if (tabs.size() == MAX_TABS) break; Tab t = new Tab(); t.url = item.getString("url", ""); t.title = item.getString("title", "新标签页"); t.home = item.getBoolean("home", true); t.desktop = item.getBoolean("desktop", false); t.web = createWebView(t); tabs.add(t); }
        current = Math.max(0, Math.min(tabs.size() - 1, state.getInt("browser_current", 0)));
        for (int i = 0; i < tabs.size(); i++) { Tab t = tabs.get(i); Bundle web = items.get(i).getBundle("web"); boolean wasHome = t.home; if (web == null || t.web.restoreState(web) == null) { if (!t.url.isEmpty() && !wasHome) t.web.loadUrl(t.url); else if (wasHome) t.url = ""; } t.home = wasHome; }
        if (!tabs.isEmpty()) showTab();
    }
    @Override public void onPause() { super.onPause(); for (Tab t : tabs) t.web.onPause(); CookieManager.getInstance().flush(); }
    @Override public void onResume() { super.onResume(); if (current >= 0) tab().web.onResume(); }
    @Override public void onDestroy() {
        destroyed = true; hideFullscreen(); if (fileCallback != null) { fileCallback.onReceiveValue(null); fileCallback = null; }
        if (mediaRequest != null) mediaRequest.deny(); if (geoCallback != null) geoCallback.invoke(geoOrigin, false, false);
        content.removeAllViews(); for (Tab t : tabs) { t.web.stopLoading(); t.web.destroy(); } tabs.clear(); super.onDestroy();
    }
    private void toast(String message) { Toast.makeText(this, message, Toast.LENGTH_SHORT).show(); }

    private static final class Glyph extends Drawable {
        private final String name; private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        Glyph(String name, int color) { this.name = name; paint.setColor(color); paint.setStyle(Paint.Style.STROKE); paint.setStrokeWidth(1.9f); paint.setStrokeCap(Paint.Cap.ROUND); paint.setStrokeJoin(Paint.Join.ROUND); }
        @Override public void draw(Canvas canvas) {
            int save = canvas.save(); canvas.translate(getBounds().left, getBounds().top); canvas.scale(getBounds().width() / 24f, getBounds().height() / 24f);
            Path p = new Path();
            if (name.equals("back") || name.equals("forward")) { if (name.equals("forward")) { canvas.translate(24, 0); canvas.scale(-1, 1); } p.moveTo(19, 12); p.lineTo(5, 12); p.moveTo(11, 5); p.lineTo(4, 12); p.lineTo(11, 19); canvas.drawPath(p, paint); }
            else if (name.equals("home")) { p.moveTo(3, 11); p.lineTo(12, 3); p.lineTo(21, 11); p.moveTo(6, 10); p.lineTo(6, 21); p.lineTo(10, 21); p.lineTo(10, 15); p.lineTo(14, 15); p.lineTo(14, 21); p.lineTo(18, 21); p.lineTo(18, 10); canvas.drawPath(p, paint); }
            else if (name.equals("reload")) { canvas.drawArc(new RectF(4, 4, 20, 20), 35, 285, false, paint); p.moveTo(19, 3); p.lineTo(19, 8); p.lineTo(14, 8); canvas.drawPath(p, paint); }
            else if (name.equals("close")) { canvas.drawLine(6, 6, 18, 18, paint); canvas.drawLine(6, 18, 18, 6, paint); }
            else if (name.equals("menu")) { paint.setStyle(Paint.Style.FILL); canvas.drawCircle(12, 5, 1.7f, paint); canvas.drawCircle(12, 12, 1.7f, paint); canvas.drawCircle(12, 19, 1.7f, paint); paint.setStyle(Paint.Style.STROKE); }
            canvas.restoreToCount(save);
        }
        @Override public void setAlpha(int alpha) { paint.setAlpha(alpha); invalidateSelf(); }
        @Override public void setColorFilter(ColorFilter filter) { paint.setColorFilter(filter); invalidateSelf(); }
        @Override public int getOpacity() { return PixelFormat.TRANSLUCENT; }
    }
}
