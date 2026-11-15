# 星学伴 3.2.1.5 Mod：系统应用图标、更新仅下载

基于用户提供的 3.2.1.5 官方 APK，迁入指定的 3.2.1.4「全部未下发应用－保留管控提醒」修改版功能。输入哈希见 `inputs.json`，成品哈希与证书见 `verification.json`。

## 使用

- 应用页和侧栏中的非 H5 条目使用 Android PackageManager 返回的已安装应用图标，包括自适应图标；不存在或无法读取的应用使用系统默认图标。H5 条目仍显示其网页图标。四个固定快捷入口在对应原生包已安装时也使用该包的系统图标。
- 更新检测保留原官方接口。收到应用列表后检查完整列表，随后再执行原列表整理；可选更新也会被检测，不依赖强制更新标记。已安装应用的新版本提示可跳过，不会阻止继续打开现有版本。
- 下载前提供 **下载 APK**、**浏览器打开下载链接**、**稍后更新**。点击下载后加入系统 DownloadManager 队列，目标为公共 **Download** 文件夹；显示系统进度及完成通知。加入队列与下载完成分别提示。
- 同一版本的同一链接若已排队或下载完成，不重复下载；失败或已移除的任务可重新下载。文件名清理路径字符并添加版本编号和时间，不覆盖之前的下载。
- 浏览器选项通过系统浏览器选择机制打开原 HTTP/HTTPS 链接，保留查询参数、转义与片段。缺少浏览器或被拒绝时保留选择窗口。没有另加账号、令牌或网址搜索包装。
- **个人中心 → 应用更新（仅下载）** 可重新查看已检测更新、刷新官方应用列表及星学伴版本、打开系统下载。自动提示仅在星学伴首页或个人中心前台展示，同一进程同一版本提示一次；稍后仍可手动查看。
- 页面退出时关闭对应更新窗口，账号变化丢弃旧更新结果，过期按钮不会发起下载或浏览器跳转。检测列表使用不可变快照。

下载的是原接口提供的 APK，不会自动改造成新的 Mod。此修改版不自动安装；安装操作由用户在系统中选择。

## 迁移范围

保留原版／MD3 主题切换、动态取色、独立首页卡片、Day 课表与通知、待提交作业待办、日历、侧栏前八项、应用排序、AI 选择及 H5 浏览器选择。本机未下发应用仍经过原管控提示及「仍然打开 → 确认仍然打开」，临时放行只对应当前选定应用，返回首页清除。

新官方课堂直接启动／任务栈／常驻策略保留。旧 Mod 中指向已删除 `ClassRoomPackageHelper` 的辅助调用已适配，不把旧官方辅助类恢复进新版。编译器重排的 AI、排序和侧栏回调按新版签名匹配。

原更新窗口改为可取消选择框，绕开自动下载／安装链；APK 更新管理器的安装方法及其工作线程回调均不触发安装。更新元数据仍保留，但本地 `forceUpdate()` 不再要求强制更新。更新获取接口、服务器返回数据及应用内部认证未替换。

原包名 `com.hljzjx.edu.student.launch`，3.2.1.5 / 32015，min/target SDK 均 29。沿用 launcher-mod 证书 `0262266e6908148d5411f0d6f190818d95cdb4f859556b6d5f53ab7109e244ca`，可覆盖用户提供的同签名 3.2.1.4 修改版。不同签名的官方安装不属于可直接覆盖的对象。

## 构建和校验

保留三份输入 APK（文件名及哈希见 `inputs.json`）。在同一工作目录准备 Python、`apk-analysis/deps` 中的 androguard／loguru／lxml，以及 `tools/apk-patch` 下的 Java 21、apktool、ECJ、D8、签名工具；Android 编译声明使用 `tools/android-sdk/android-34-ext12/android.jar`。自有辅助声明仅用于编译，不打入 APK。私钥只保留本机，不随源码归档。

```text
python -X utf8 apk-analysis/launcher-migration-3.2.1.5/prepare.py
python -X utf8 apk-analysis/launcher-migration-3.2.1.5/plan.py
python -X utf8 apk-analysis/launcher-migration-3.2.1.5/test_updates.py
python -X utf8 apk-analysis/launcher-migration-3.2.1.5/build.py
python -X utf8 apk-analysis/launcher-migration-3.2.1.5/verify.py
```

新官方 DEX3 接近方法编号上限，原样将本次官方从 DEX1 移入的 23 个 RxJava observer 类转入 DEX9，验证所有原方法保留且指令相同。DEX1/2/4 保留新官方字节，DEX6/7/8 保留指定 Mod 字节；DEX5 仅适配图标与旧课堂辅助调用，新增下载界面位于自有 DEX10。资源表及全部资源文件与指定 Mod 一致，不重编资源；清单只把该 Mod 的版本号更新到 3.2.1.5 / 32015。

校验包含最终 DEX 的管控提醒／确认／待办路径、系统图标绑定和旧版负对照，以及实际自有 Java 的下载、重复任务、失败重试、原 URL、页面生命周期、账号隔离、可取消窗口、设置入口等替身测试。`verification.json` 与 `update-tests.json` 记录实际结果。

**没有 Android／Pixel Tablet 实测、真实服务器下载、系统浏览器及实际像素验收。** 本地替身通过不能代替这些现场结果。没有连接、安装、卸载或清理用户设备，没有向学校接口发请求，也没有自动发布 GitHub。

## 参考和许可

系统 API：

- [Android PackageManager 图标接口](https://developer.android.com/reference/android/content/pm/PackageManager)
- [DownloadManager.Request 公共下载目录及通知](https://developer.android.com/reference/android/app/DownloadManager.Request)

自有补丁、辅助代码、脚本和测试采用 **GPL-3.0-only**，贡献者：**xuezhangjam、Codex**。原厂及第三方软件不因本归档改变权利或许可。源码归档不包含 APK、完整原软件源码、反编译树、工具或私钥；旧功能以用户提供的修改 APK 作为输入。
