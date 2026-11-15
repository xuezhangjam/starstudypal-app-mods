import com.hailiang.webbrowser.browser.BrowserInput;

public final class BrowserInputTest {
    private static int count;
    private static final String SEARCH = "https://www.bing.com/search?q=";
    private static void check(String input, String expected) {
        String actual = BrowserInput.resolve(input, SEARCH);
        if (!actual.equals(expected)) throw new AssertionError(input + " => " + actual + "; expected " + expected);
        count++;
    }
    private static void web(String input, boolean expected) {
        if (BrowserInput.isWebUrl(input) != expected) throw new AssertionError("Web URL: " + input);
        count++;
    }
    public static void main(String[] args) {
        check(null, ""); check("  ", ""); check("example.com", "https://example.com");
        check(" sub.example.org/path?q=1#result ", "https://sub.example.org/path?q=1#result");
        check("HTTP://example.com/", "HTTP://example.com/");
        check("http://192.168.1.1:8080/", "http://192.168.1.1:8080/");
        check("localhost:3000/path", "https://localhost:3000/path");
        check("[::1]:8080", "https://[::1]:8080");
        check("//example.net/a", "https://example.net/a");
        check("about:blank", "about:blank");
        check("你好 世界", SEARCH + "%E4%BD%A0%E5%A5%BD+%E4%B8%96%E7%95%8C");
        check("a + b", SEARCH + "a+%2B+b");
        check("example.com hello", SEARCH + "example.com+hello");
        check("javascript:alert(1)", SEARCH + "javascript%3Aalert%281%29");
        check("file:///sdcard/private", SEARCH + "file%3A%2F%2F%2Fsdcard%2Fprivate");
        check("https://bad host/path", "");
        check("someone@example.com", SEARCH + "someone%40example.com");
        check("https://example.org/a%20b?q=a+b", "https://example.org/a%20b?q=a+b");
        for (String domain : new String[]{"chatgpt.com", "gemini.google.com", "www.deepseek.com", "en.wikipedia.org", "github.com", "www.bilibili.com", "www.example.net", "school.example.cn"}) {
            check(domain, "https://" + domain); web("https://" + domain, true);
        }
        web(null, false); web("", false); web("file:///etc/passwd", false); web("javascript:alert(1)", false);
        web("https://", false); web("https://bad host", false); web("mailto:a@example.com", false);
        web("https://例子.测试/", true); web("https://[::1]/", true); web("http://localhost:8080", true);
        System.out.println("PASS: " + count + " address/search/URL cases; arbitrary domains accepted without a school list");
    }
}
