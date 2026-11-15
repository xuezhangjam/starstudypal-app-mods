# 老师网页链接打开方式选择 v8

在已发布v7基础上，给老师通过课堂外部链接入口下发的HTTP/HTTPS网页增加两种打开方式。原包名和版本为com.hljzjx.edu.student.classroom、3.2.1.0/321000，使用与v7相同的课堂mod签名。

## 使用方式

收到网页后，先显示深色圆角“网页打开方式”选择框：

- **默认浏览器打开**：把原网址交给系统默认浏览器，不在课堂内先加载一遍。已设置且可解析时优先使用默认浏览器；未设置默认、返回系统选择器或查询受限时，使用系统浏览器选择。不会固定到Chrome或把网址变成搜索词。
- **课堂内打开**：继续调用原来的白名单查询和HLWebViewFragment流程，保留原网页标题、图标、白名单、最小化/恢复与课堂生命周期处理。
- 取消后可通过原生底栏中的老师应用入口重新选择。浏览器无法启动时保留选择框，可改选课堂内打开。

网址的查询参数、转义内容和锚点原样传递。不复制课堂登录头、Cookie、笔迹或作答数据到外部浏览器；网页若依赖课堂内登录状态，浏览器可能需要按网站要求重新登录。网页本身的URL由老师原数据提供，不附加新的身份参数。

选择框沿用课堂mod既有AI选择框的深色圆角配色。宽度跟随当前窗口，内容置于ScrollView。新链接替换、结束网页活动、下课或Activity销毁时关闭旧框；账号、课堂、链接对象或窗口变化后，不执行旧选择。异步白名单回调只接受当前一次课堂内打开请求，避免旧链接后到覆盖新页面。

现有AI问问的海亮/ChatGPT选择不进入此入口；原生应用启动路径继续使用原方法。已经最小化的课堂内网页仍按原入口直接恢复，不另建第二个网页。

## 实现与验证

新增自有TeacherWebLinks辅助类，放在DEX12；DEX4只调整ThirdAppInteraction的openApp、白名单完成回调、end和下课分支，另加三个窄桥接方法及一个临时重入标记。课堂内桥接仅在本次调用期间跳过选择框，正常及异常分支都会复位；原openApp和原回调的其余指令完整保留。

所有其他载荷应与v7逐字节一致，包括PPT、分屏底栏、续答结果、相册、AI、画中画、资源和Manifest。具体SHA256、成员引用、签名及指令差异见verification.json。

136个实际辅助Java/可观察Android与原生API替身断言通过：两种路由、完整URL、默认浏览器解析与系统选择后备、查询受限、浏览器缺失/拒绝、取消与重复点击、底栏入口、替换链接、延迟白名单、账号/课堂/活动销毁边界、窄窗口和监听释放。原生方法的真实DEX指令、桥接与成员引用另作校验。

**这些是本地模型与静态检查，尚无Pixel Tablet、真实浏览器分发或老师下发网页的联调结果。** 本轮没有安装/卸载/清数据、访问学校服务或发出真实课堂HTTP/MQTT，也未自动发布新Release。

Android路由参考：[Intent.setSelector](https://developer.android.com/reference/android/content/Intent#setSelector(android.content.Intent))、[CATEGORY_APP_BROWSER](https://developer.android.com/reference/android/content/Intent#CATEGORY_APP_BROWSER)。

## 构建

输入为[已发布v7 APK](https://github.com/xuezhangjam/starstudypal-app-mods/releases/tag/classroom-3.2.1.0-v7)。准备Java/Android SDK/ECJ/D8/apktool/签名工具、Python分析依赖及自己的签名密钥，在工作区根执行：

```text
python -X utf8 apk-analysis/classroom-teacher-web-choice-v8/test_web_links.py
python -X utf8 apk-analysis/classroom-teacher-web-choice-v8/build.py
python -X utf8 apk-analysis/classroom-teacher-web-choice-v8/verify.py
python -X utf8 apk-analysis/classroom-teacher-web-choice-v8/package_source.py
```

归档只包含本次自有辅助源码、窄补丁、编译声明、测试替身和构建/验证报告，不含完整原软件反编译树、APK、第三方工具或签名密钥。原创贡献沿用GPL-3.0-only，原软件和第三方权利保持。贡献者：xuezhangjam、Codex。
