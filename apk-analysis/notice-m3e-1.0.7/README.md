# 班级通知 1.0.7 原生 M3e

2026-10-25：用户要求在官方 1.0.7 上修改并保留原生 MD3e。用户已明确要求原版安装包名 `com.hailiang.notice.student`，后续不得擅自添加包名后缀。Java 类路径 `com.hailiang.notice.m3e` 是实现命名空间，不是安装包名。

成品：`班级通知学生端-1.0.7-M3e原生平板版-系统消息修复.apk`。版本 `1.0.7-m3e.1`，versionCode 8；minSdk 21、targetSdk 29 均保持官方值。SHA256：`71d221f4203489c7f9566babbdd74876b849600dec846e863812c1eb4200bbf4`。

官方输入 `班级通知学生端1.0.7原版.apk`，SHA256 `e446d5ad0561f69084d9a02215e98523d0a722390a662aa5f3e41601600de0a3`。原生模块来自用户提供的 1.0.6 原版包名修复版，SHA256 `8c3bba4f6b66b22402a6bf7375e649147752297c8c369f3ec2ed458590031718`。

## 迁移与验证

以 1.0.7 官方代码和资源为基础，仅改十个 UI 接入方法并新增六个生命周期方法，保留 54,057 个既有方法。保留原生导航、单／双栏、搜索、正文、媒体／附件入口、动态强调色与深色外观，以及之前的系统消息分类切换、状态同步和回调清理修复。原生模块及列表布局与 1.0.6 修复版一致，没有换回 HTML 详情界面。

官方 DEX 1、2、4 与 assets/lib 共 28 项载荷保持字节一致。5,297 个官方资源 ID 保持原义。classes5.dex 沿用原生界面，classes6.dex 沿用上一版 classes7.dex 的分页辅助类。官方 Gson 保留在主 DEX，DEX 名称连续。1.0.7 的白名单 API、模型及 WebView 域名处理代码保留，相关 65 个方法与官方等价。

152 项 JVM 导航检查再次通过；最终签名包检查 2,469 处方法／字段引用、资源与布局、签署前后载荷及同证书 v1／v2／v3 签名和对齐。没有连接 Android 平板，实际显示、学校账号、推送、媒体与附件尚未实机复测。结果见 signed-verification.json、navigation-test-results.txt。

## 链接白名单的范围

用户询问过新增白名单代码。官方详情页按学校 ID 从 `/launch/app/v1/school_control_url/white_get_lists` 获取名单。WebViewManager 合并当前页面／正文域名与服务器名单，支持精确匹配和 `*.example.com` 子域名；壳页首次进入正文站点有一次放行，之后未匹配时阻止跳转并提示“不允许访问＋域名”。请求失败时按空列表更新，仍保留当前页面域名；最终允许域名集合为空时函数直接放行。同一模块另有 SSL 错误取消加载处理。

这是原版内置 WebView 的链接检查，不是全平板网络控制。原生阅读器仍沿用原生链接处理路径，不能把 WebView 代码保留表述为这些规则自动作用于原生阅读器打开的外部浏览器。没有请求用户账号接口读取学校的实际名单。

## 签名和恢复

沿用已获用户确认的本地密钥 `tools/apk-patch/signing/notice-m3e-mod.jks`，别名 noticem3e，本地开发密码 android。证书 SHA256 `0ce16018fbc06d86a8a4f12e21d38e5673efe4b74a55bb162a74b642383d5cd7`，可覆盖上一份同包名、同签名的 1.0.6 修复版，不能覆盖学校官方签名包。本次没有执行设备安装、卸载或清除数据。密钥必须保留，不能放入公开仓库或源码压缩包。

恢复步骤：用 apktool `d -s` 将官方输入解码到 official；把官方 classes3.dex 和 AndroidManifest.xml 放入临时 classes3-input.apk（DEX 命名 classes.dex），用 apktool `d -r` 解码到 official-code。运行 `migrate_notice_107.py` 创建独立 work、接入原生模块，再用 apktool 构建为 rebuilt.apk。运行不带参数的 `verify_notice_107.py` 生成并校验 unsigned 包；用保留密钥签署后，将签名包路径传给同一验证脚本。`test_notice_system_navigation.py` 运行原生导航回归。重建需要两个输入 APK、旧修复版恢复工程及本目录记录的既有工具链。

version-comparison.json 记录逐方法对比，migration-manifest.json 记录具体接入方法。源码压缩包不包含密钥或学校完整项目。
