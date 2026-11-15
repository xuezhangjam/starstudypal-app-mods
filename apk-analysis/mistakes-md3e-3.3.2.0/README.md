# 错题本学生端 3.3.2.0：原生 MD3e 与系统照片入口

输入为 `错题本学生端3.3.2.0原版.apk`，包名保持 `com.nice.errorbook`，版本名 `3.3.2.0`、版本码 `3320`、最低 Android 10 均保持。成品与校验值见 `verification.json`。

## 本轮修改

- 在既有原生 View / Compose 界面上统一 MD3e 色彩、圆角、学科标签和弹窗。浅深色跟随系统，Android 12 以上默认壁纸取色；主页底部“MD3e · 外观”可关闭壁纸取色。
- 照片入口提供“系统相机拍照”和“从相册选择”。拍照调用系统 `ACTION_IMAGE_CAPTURE`，通过既有 FileProvider 交付临时原图位置；未安装可处理的相机时显示提示。
- 相册使用系统文件/照片选择器，按原入口的照片数量上限导入，取消后可重选；不新增广泛存储权限。
- 两条来源共用后台图片解码、方向处理、完整画面导入及原 SDK 的照片预览、手动裁剪、增强、识别和上传流程。导入 JPEG 质量 95，最大边 4096、最大 800 万像素，不放大小图。
- 题目纸面、公式、笔迹、图片内容和业务网络方法保持原实现。

## 构建与核验

脚本按当前项目目录组织，放在 `apk-analysis/mistakes-md3e-3.3.2.0/`。需要项目已有 Java 21、apktool、ECJ、D8、Android 34 编译 API、签名工具，以及 `apk-analysis/deps` 中的 Androguard。构建依赖的原 APK 和工具不在源码压缩包内。

1. `python build.py`：验证原 APK SHA256，生成辅助类、修改指定界面方法、打包并签名。
2. `python test_policy.py`：执行真实配色及图片尺寸策略的 JVM 离线测试。
3. `python verify.py`：核验最终 APK 的资源、清单、DEX 方法、成员引用和签名。

原 APK 资源采用缩短路径；脚本按资源 ID 映射 `activity_main` / `item_subject_tab` / `dialog_common` 到原 ZIP 路径，保留原资源表。编译用 API 声明只用于链接，不打入辅助 DEX。

签名密钥保存在本机 `tools/apk-patch/signing/errorbook-md3e-mod.jks`，不包含在源码包中。它与官方签名不同，无法直接覆盖官方安装。请先保存需要的数据；本轮未执行卸载、清数据或设备安装。

## 验证边界

`policy-test-results.txt` 记录 1860 项断言和 256 组图片尺寸场景。`verification.json` 记录最终签名包的结构与代码检查结果。这些检查没有替代 Android 实机验证：系统相机/相册实际唤起、裁剪预览、识别和服务器上传仍需在平板上验收。

## 源码范围

本目录中的新增 Java、构建脚本及测试为本轮修改源码；不包含官方 APK 的完整源码、第三方库或签名密钥，也不将原软件及其资源宣称为本项目原创。
