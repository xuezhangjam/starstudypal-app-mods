package com.hailiang.webbrowser.browser;

import java.net.URI;
import java.net.IDN;
import java.net.URLDecoder;
import java.net.URLEncoder;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** Address/search parsing. No school configuration, login or host allowlist. */
public final class BrowserInput {
    private BrowserInput() {}
    private static final Pattern TEMPLATE = Pattern.compile("\\$\\{(deviceId|token|saasToken|userId|classId|staffId|campusId|tenantId|schoolId)\\}");

    public static String resolve(String input, String searchPrefix) {
        String value = input == null ? "" : input.trim();
        if (value.isEmpty()) return "";
        if (value.equalsIgnoreCase("about:blank")) return "about:blank";
        String lower = value.toLowerCase(Locale.ROOT);
        if (lower.startsWith("https:") || lower.startsWith("http:")) {
            return directUrl(value);
        }
        if (encodedScheme(value)) return directUrl(value);
        if (value.startsWith("//")) return directUrl(value);
        if (!value.split("[/#?]", 2)[0].matches(".*\\s+.*") && looksLikeHost(value)) {
            return directUrl(value);
        }
        return search(value, searchPrefix);
    }

    /** Decode only a transport-encoded WHOLE URL. Never decode a normal URL's
     * query, redirect parameters, percent escapes or plus signs. */
    public static String transport(String input) {
        String value = input == null ? "" : input.trim();
        if (value.length() > 1 && value.startsWith("\"") && value.endsWith("\"")) value = value.substring(1, value.length() - 1).trim();
        for (int i = 0; i < 2 && encodedScheme(value); i++) {
            try { value = URLDecoder.decode(value, "UTF-8"); } catch (Exception e) { return ""; }
        }
        return value;
    }

    private static boolean encodedScheme(String value) {
        String lower = value.toLowerCase(Locale.ROOT);
        return lower.matches("^https?%3a(?:%2f|/){2}.*") || lower.startsWith("https%253a") || lower.startsWith("http%253a");
    }

    public static boolean hasTemplate(String value) { return value != null && TEMPLATE.matcher(transport(value)).find(); }

    /** Only used for the legacy H5 app launch envelope, never ordinary links
     * or searches. Missing values match the original container's empty values. */
    public static String expandTemplates(String input, Map<String, String> values) {
        Matcher m = TEMPLATE.matcher(transport(input)); StringBuffer out = new StringBuffer();
        while (m.find()) {
            String value = values.get(m.group(1));
            try { value = value == null ? "" : URLEncoder.encode(value, "UTF-8").replace("+", "%20"); }
            catch (Exception impossible) { value = ""; }
            m.appendReplacement(out, Matcher.quoteReplacement(value));
        }
        m.appendTail(out); return out.toString();
    }

    /** An external launch is a URL request, and must never become a search. */
    public static String directUrl(String input) {
        String value = transport(input);
        if (value.equalsIgnoreCase("about:blank")) return "about:blank";
        if (value.startsWith("//")) value = "https:" + value;
        String lower = value.toLowerCase(Locale.ROOT);
        if (!lower.startsWith("https://") && !lower.startsWith("http://")) {
            if (!value.split("[/#?]", 2)[0].matches(".*\\s+.*") && looksLikeHost(value)) value = "https://" + value;
            else return "";
        }
        try {
            int start = value.indexOf("://") + 3, end = value.length();
            for (char c : new char[]{'/', '?', '#'}) { int at = value.indexOf(c, start); if (at >= 0) end = Math.min(end, at); }
            String authority = value.substring(start, end);
            if (authority.isEmpty() || authority.matches(".*[\\s\\p{Cntrl}<>\"{}\\\\].*")) return "";
            int user = authority.lastIndexOf('@');
            String info = user >= 0 ? authority.substring(0, user + 1) : "";
            String host = authority.substring(user + 1), port = "";
            if (!host.startsWith("[")) {
                int colon = host.lastIndexOf(':');
                if (colon >= 0) { port = host.substring(colon); host = host.substring(0, colon); if (!port.matches(":[0-9]{1,5}") || Integer.parseInt(port.substring(1)) > 65535) return ""; }
                host = IDN.toASCII(host);
            }
            if (host.isEmpty()) return "";
            String suffix = encodeSuffix(value.substring(end));
            String result = value.substring(0, start) + info + host + port + suffix;
            return isWebUrl(result) ? result : "";
        } catch (Exception invalid) { return ""; }
    }

    private static String encodeSuffix(String value) throws Exception {
        StringBuilder out = new StringBuilder(); boolean fragment = false;
        for (int i = 0; i < value.length();) {
            int cp = value.codePointAt(i); i += Character.charCount(cp);
            if (cp == '%' && i + 1 < value.length() && Character.digit(value.charAt(i), 16) >= 0 && Character.digit(value.charAt(i + 1), 16) >= 0) { out.append('%').append(value.charAt(i++)).append(value.charAt(i++)); continue; }
            boolean allowed = cp < 128 && ((cp >= 'a' && cp <= 'z') || (cp >= 'A' && cp <= 'Z') || (cp >= '0' && cp <= '9') || "-._~:/?@!$&'()*+,;=".indexOf(cp) >= 0 || (cp == '#' && !fragment));
            if (cp == '#') fragment = true;
            if (allowed) out.append((char) cp);
            else for (byte b : new String(Character.toChars(cp)).getBytes("UTF-8")) { int v = b & 255; out.append('%').append("0123456789ABCDEF".charAt(v >> 4)).append("0123456789ABCDEF".charAt(v & 15)); }
        }
        return out.toString();
    }

    private static boolean looksLikeHost(String value) {
        String authority = value.split("[/#?]", 2)[0];
        if (authority.indexOf('@') >= 0) return false;
        String lower = authority.toLowerCase(Locale.ROOT);
        if (lower.equals("localhost") || lower.matches("localhost:[0-9]+")) return true;
        if (authority.startsWith("[") && authority.contains("]")) return true;
        return authority.indexOf('.') > 0 && !authority.endsWith(".");
    }

    public static boolean isWebUrl(String value) {
        try {
            URI uri = new URI(value);
            String scheme = uri.getScheme();
            return scheme != null && (scheme.equalsIgnoreCase("http") || scheme.equalsIgnoreCase("https"))
                && uri.getRawAuthority() != null && !uri.getRawAuthority().isEmpty()
                && !uri.getRawAuthority().matches(".*\\s+.*");
        } catch (Exception ignored) { return false; }
    }

    private static String search(String text, String prefix) {
        try { return prefix + URLEncoder.encode(text, "UTF-8"); }
        catch (Exception impossible) { throw new IllegalStateException(impossible); }
    }
}
