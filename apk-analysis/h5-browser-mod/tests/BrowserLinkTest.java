import com.hailiang.webbrowser.browser.BrowserInput;
import java.net.URI;
import java.net.URLEncoder;
import java.util.HashMap;
import java.util.Map;

public final class BrowserLinkTest {
    private static int count;
    private static final String SEARCH = "https://www.bing.com/search?q=";
    private static void same(String actual, String expected) { count++; if (!actual.equals(expected)) throw new AssertionError(actual + " != " + expected); }
    private static void yes(boolean condition) { count++; if (!condition) throw new AssertionError("case " + count); }
    private static void direct(String in, String expected) { same(BrowserInput.directUrl(in), expected); if (!expected.isEmpty()) { yes(BrowserInput.isWebUrl(expected) || expected.equals("about:blank")); yes(!expected.startsWith(SEARCH)); } }
    public static void main(String[] args) throws Exception {
        direct("https://school.example/app?token=fixture", "https://school.example/app?token=fixture");
        direct("https://school.example/课程中心?a=hello world", "https://school.example/%E8%AF%BE%E7%A8%8B%E4%B8%AD%E5%BF%83?a=hello%20world");
        direct("https://school.example/app?options={\"mode\":\"app\"}", "https://school.example/app?options=%7B%22mode%22:%22app%22%7D");
        String redirect = "https://school.example/sso?redirect=https%3A%2F%2Ftarget.example%2Fa%3Fx%3D1%26y%3D2&sig=A+B%2FC%3D";
        direct(redirect, redirect);
        direct(URLEncoder.encode(redirect,"UTF-8"), redirect);
        direct(URLEncoder.encode(URLEncoder.encode(redirect,"UTF-8"),"UTF-8"), redirect);
        direct("https://school.example/a b?q=100%done#first#second", "https://school.example/a%20b?q=100%25done#first%23second");
        direct("\"https://school.example/app\"", "https://school.example/app");
        direct("school.example/app", "https://school.example/app");
        direct("//school.example/app", "https://school.example/app");
        direct("https://bad host/path?token=fixture", "");
        direct("https://", ""); direct("javascript:alert(1)", ""); direct("file:///private", "");
        direct("some keywords", ""); direct("https://school.example:99999/app", "");
        same(BrowserInput.resolve("https://bad host/path?token=fixture", SEARCH), "");
        same(BrowserInput.resolve("http:/school.example/app?token=fixture", SEARCH), "");
        same(BrowserInput.resolve("正常搜索", SEARCH), SEARCH+"%E6%AD%A3%E5%B8%B8%E6%90%9C%E7%B4%A2");
        same(BrowserInput.resolve("school.example/a b", SEARCH), "https://school.example/a%20b");
        String template = "https://school.example/app?token=${token}&saas=${saasToken}&uid=${userId}&classId=${classId}&staff=${staffId}&campus=${campusId}&tenant=${tenantId}&school=${schoolId}&device=${deviceId}";
        // This reproduces the old strict-URI rejection that sent a real H5
        // app template through Bing. All data below is synthetic test data.
        boolean oldRejected=false; try {new URI(template);} catch(Exception expected){oldRejected=true;} yes(oldRejected);
        Map<String,String> values=new HashMap<String,String>();
        values.put("token","fixture+A/B="); values.put("saasToken","fixture&part=2");
        values.put("userId","101"); values.put("classId","102"); values.put("staffId","103"); values.put("campusId","104"); values.put("tenantId","105"); values.put("schoolId","106"); values.put("deviceId","fixture SN+$");
        String filled="https://school.example/app?token=fixture%2BA%2FB%3D&saas=fixture%26part%3D2&uid=101&classId=102&staff=103&campus=104&tenant=105&school=106&device=fixture%20SN%2B%24";
        same(BrowserInput.expandTemplates(template,values),filled); direct(filled,filled);
        same(BrowserInput.expandTemplates(URLEncoder.encode(template,"UTF-8"),values),filled);
        yes(BrowserInput.hasTemplate(template)); yes(BrowserInput.hasTemplate(URLEncoder.encode(template,"UTF-8")));
        same(BrowserInput.expandTemplates("https://school.example/?token=${token}",new HashMap<String,String>()),"https://school.example/?token=");
        // Ordinary web links do not obtain template values automatically.
        direct("https://site.example/?token=${token}","https://site.example/?token=$%7Btoken%7D");
        direct("https://例子.测试/", "https://xn--fsqu00a.xn--0zwm56d/");
        System.out.println("PASS: "+count+" external-link/transport/template regressions; no URL-to-search fallback");
    }
}
