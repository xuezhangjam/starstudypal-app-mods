# H5 浏览器修改版

输入：`H5应用.apk`，官方 1.0.13（1013）。

当前成品：`H5浏览器-1.0.13-首页应用直达修复.apk`。

安装包名保持 `com.hailiang.xxb.web.app`；版本 `1.0.13-browser.2`，版本号 1015；最低 Android 10（API 29），目标 API 29。与上一份浏览器修改版同签名，可以覆盖安装。

## 首页 H5 应用直达修复

用户实机反馈：首页点击 H5 应用后，浏览器把跳转网址送到必应搜索。发现原版 `WebViewActivity.fillUrlParam` 支持 `${token}`、`${userId}` 等网址参数模板；上一版独立浏览器遗漏了模板填充，又将外部应用网址送进严格的 Java URI 校验，失败时回退到搜索。没有采集用户实际跳转 URL，但用模板网址已能复现该错误分支。

本次改动：

- 首页应用、HTTP/HTTPS VIEW 和旧组件启动走直接网址入口，没有搜索回退；无效外部网址只提示错误。
- 地址栏仍支持关键词搜索；显式 HTTP/HTTPS 网址格式错误时同样不会被送到搜索引擎。
- 识别整条 URL 的传输编码（最多两层），普通 URL 中已有的 `%xx`、嵌套 redirect 和 `+` 保留。
- 网址路径/查询中的空格、中文、JSON 字符和非法百分号按 URL 规则编码。
- 原 H5 启动协议 `hlxxb://hailiang.web.com/openUrl`、旧 WebViewActivity/LaunchDispatcherActivity 入口可填充原九类模板参数。普通浏览链接和手动搜索不会自动注入这些参数。
- 需要模板时，在后台按原 `_key=?` / `_value` 协议读取首页共享缓存中的 `token`、`sass_token`、`hl_user_info`，再回退到 Intent 字段；设备 SN 按需尝试原 RomSdk 的读取接口。没有恢复学校后台初始化器、网络白名单或 MDM 控制流程，没有打印缓存值或跳转网址。
- 模板值作为 URL 参数编码，避免值中的 `+`、`&`、`=` 破坏原查询参数。缺少值时沿用原版的空值处理，网页可能仍要求登录。
- 新链接或用户主动导航会使旧的后台参数读取结果失效，避免延迟结果覆盖后来打开的页面。

本次参数处理及直接打开逻辑已做离线验证，首页共享缓存权限、ROM 设备信息接口和具体 H5 页面的登录状态仍需用户设备确认。

## 已实现

- 桌面 MAIN/LAUNCHER 入口，名称“H5 浏览器”，沿用原版图标。
- 原生浏览器主页、网址输入与关键词搜索、前进后退、刷新/停止、主页、加载进度及错误重试。
- 多标签页（最多 12 个），新窗口链接、长按链接新标签打开、图片下载。
- 本地书签、最近 200 条历史记录；长按条目删除。
- 必应、百度、Google、DuckDuckGo 搜索引擎选择。
- 浅色、深色、跟随系统主题；系统提供动态色时使用系统强调色。
- 桌面版网站、页面查找、分享网页、复制网址、清除历史/缓存/Cookie。
- 系统下载管理器下载、系统文件选择器上传，支持多选；视频全屏。
- 网站摄像头、麦克风和位置请求先询问用户，并按需请求 Android 权限。
- HTTP/HTTPS 普通网页链接、文字分享、原组件名启动以及 `jsonData.url` / `url` / `htmlUrl` 参数进入新浏览器。

## 白名单与启动

新的浏览器入口直接使用 Android 系统 WebView，不请求学校域名白名单，不依赖学校登录，也不进行应用下架校验。HTTP/HTTPS 网页跨域导航没有学校域名限制。

应用启动改为 Android 原生 Application。原学校 SDK 的自动初始化 Provider、服务和接收器不再注册。旧活动组件名改为指向新 BrowserActivity 的活动别名，避免通过旧入口重新进入受限页面。

原五个 DEX 及资源、图标、原生库均逐字节保留。改动仅为二进制 AndroidManifest.xml 和新增 classes6.dex；旧受限实现不再作为 Android 活动注册。

浏览器保留正常的证书校验。网页加载仍受设备网络与系统 WebView 版本影响。普通 HTTP/HTTPS 文件可交给下载管理器，网页生成的 blob/data 文件目前不能直接交给系统下载。

## 安装与签名

沿用上一版浏览器的本地签名，可以直接覆盖上一份浏览器修改版；与官方签名不同，不能直接覆盖官方版。没有对任何连接设备执行安装或卸载。

签名证书 SHA-256：`c44b3c9268645f6da5e766f94b9dda5b067133631bd1b2c3a18052562296f7ea`。

后续修改版应继续使用本机 `tools/apk-patch/signing/h5-browser-mod.jks`，别名 `h5browsermod`，本地开发密码 `android`。请保留该文件；源码压缩包不包含私钥。

## 构建与验证

- Java 源码：`src/com/hailiang/webbrowser/browser/`。
- `build.py`：校验输入哈希，ECJ 编译，D8 生成独立 DEX，生成新清单，保留原 APK 内容并重新签名。
- Android 编译库来自 Google 官方平台归档，下载地址与校验记录在 `tools/android-sdk/download.json`。
- Windows 原生打包工具使用 `%LOCALAPPDATA%/CodexBuilds/h5-browser-mod` 暂存路径，避免中文路径编码问题。
- `tests/BrowserInputTest.java`：44 项网址/搜索解析案例已通过。
- `tests/BrowserLinkTest.java`：55 项外部链接、编码与模板回归已通过，包含旧模板网址被严格 URI 拒绝的复现。测试仅使用合成数据。
- `verify.py`：最终清单、桌面入口、HTTP/HTTPS/分享入口、旧组件别名、资源图标、DEX 重名和新代码成员引用检查。
- `verification.json`：原版五个 DEX、资源与图标均保留；与上一版浏览器相比，仅 AndroidManifest.xml 和 classes6.dex 变化。报告包含本次成员引用、直接打开无搜索回退、同签名以及 v2/v3 签名核对结果。ZIP 对齐检查通过。

尚未在 Android 平板或模拟器上运行验证。上传、下载、网站权限与实际网页显示需要设备环境确认。

修改：xuezhangjam / Codex。
