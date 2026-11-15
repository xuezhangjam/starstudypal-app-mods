@file:OptIn(androidx.compose.material3.ExperimentalMaterial3ExpressiveApi::class)
package com.hailiang.workcloud.student.md3e.v3

import android.app.DownloadManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Environment
import android.widget.Toast
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.OpenInNew
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.hailiang.workcloud.student.data.enums.TaskFileType
import com.hailiang.workcloud.student.data.model.WorkTask
import java.net.URI
import java.net.URLDecoder
import java.util.UUID

data class HomeworkDownload(val url: String, val fileName: String, val kind: String)

fun isDownloadUrl(value: String): Boolean = try {
    val uri = URI(value)
    (uri.scheme.equals("https", true) || uri.scheme.equals("http", true)) &&
        !uri.host.isNullOrBlank() && uri.rawUserInfo == null && value.none { it.isISOControl() }
} catch (_: Exception) { false }

private fun urlName(url: String): String = try {
    val raw = URI(url).rawPath.orEmpty().substringAfterLast('/')
    // '+' is a literal path character, not application/x-www-form-urlencoded space.
    URLDecoder.decode(raw.replace("+", "%2B"), "UTF-8")
} catch (_: Exception) { "" }

fun safeDownloadName(preferred: String, fallback: String, url: String, pdf: Boolean): String {
    val fromUrl = urlName(url).takeIf { it.matches(Regex(".+\\.[A-Za-z0-9]{1,10}")) }.orEmpty()
    val name = preferred.ifBlank { fromUrl.ifBlank { fallback } }
    var cleaned = name.replace(Regex("[\\p{Cntrl}/\\\\:*?\"<>|]"), "_").trim(' ', '.')
    if (cleaned.isBlank()) cleaned = "作业文件"
    val existingExtension = Regex("\\.([A-Za-z0-9]{1,10})$").find(cleaned)?.value.orEmpty()
    val urlExtension = Regex("\\.([A-Za-z0-9]{1,10})$").find(fromUrl)?.value.orEmpty()
    val extension = existingExtension.ifBlank { if (pdf) ".pdf" else urlExtension }
    var base = if (existingExtension.isNotEmpty()) cleaned.dropLast(existingExtension.length) else cleaned
    base = base.take(64).trimEnd(' ', '.')
    if (base.isNotEmpty() && Character.isHighSurrogate(base.last())) base = base.dropLast(1)
    return base.ifBlank { "作业文件" } + extension
}

/** Read only teacher-provided material URLs. Never scrape answers, invent URLs or strip signed queries. */
fun collectDownloads(task: WorkTask): List<HomeworkDownload> {
    val result = mutableListOf<HomeworkDownload>()
    var number = 0
    task.getTasks().orEmpty().forEach { sub -> sub.getMaterials().orEmpty().forEach { material ->
        number++
        val original = material.getFileUrl().orEmpty().trim()
        val label = material.getFileName().orEmpty()
        val base = task.getTitle().orEmpty().ifBlank { "作业" } + "-文件$number"
        if (isDownloadUrl(original)) {
            result += HomeworkDownload(original, safeDownloadName(label, base, original, material.getMaterialFileType() == TaskFileType.PDF), "原文件")
        } else {
            material.getImageUrls().orEmpty().forEachIndexed { page, raw ->
                val url = raw.trim()
                if (isDownloadUrl(url)) result += HomeworkDownload(url,
                    safeDownloadName("$base-第${page+1}页", "$base-第${page+1}页", url, false), "预览图片 · 第${page+1}页")
            }
        }
    } }
    return result.distinctBy { it.url }
}

/** UUID suffix prevents overwriting earlier downloads without needing storage enumeration. */
fun uniqueDownloadName(name: String, suffix: String): String {
    val extension = Regex("\\.[A-Za-z0-9]{1,10}$").find(name)?.value.orEmpty()
    return name.dropLast(extension.length) + "_" + suffix.filter { it.isLetterOrDigit() }.take(12).ifBlank { "copy" } + extension
}

fun enqueueHomeworkDownload(context: Context, file: HomeworkDownload): Long {
    require(isDownloadUrl(file.url)) { "不支持的下载地址" }
    val manager = context.getSystemService(Context.DOWNLOAD_SERVICE) as? DownloadManager
        ?: throw IllegalStateException("系统下载服务不可用")
    val name = uniqueDownloadName(file.fileName, UUID.randomUUID().toString().replace("-", ""))
    val request = DownloadManager.Request(Uri.parse(file.url))
        .setTitle(file.fileName).setDescription("精准作业 · ${file.kind}")
        .setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, "精准作业/$name")
        .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
    // Server Content-Type remains authoritative; do not turn image previews into fake PDFs.
    return manager.enqueue(request).also { check(it > 0) { "系统未接受下载任务" } }
}

private fun toast(context: Context, message: String) = Toast.makeText(context, message, Toast.LENGTH_LONG).show()
private fun openBrowser(context: Context, url: String) {
    try { context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
    catch (_: Exception) { toast(context, "没有可打开此链接的浏览器") }
}

@Composable
fun DownloadAction(tasks: List<WorkTask>, index: Int) {
    val task = tasks.getOrNull(index) ?: return
    val files = remember(task) { collectDownloads(task) }
    if (files.isEmpty()) return
    val context = LocalContext.current
    var opened by remember(task.getId()) { mutableStateOf(false) }
    IconButton(onClick = { opened = true }, modifier = Modifier.size(48.dp)) {
        Icon(Icons.Filled.Download, "下载作业文件")
    }
    if (opened) AlertDialog(onDismissRequest = { opened = false }, title = { Text("下载作业文件") },
        text = {
            Column(Modifier.heightIn(max = 420.dp).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("保存到 Download/精准作业，下载进度可在系统下载中查看。", style = MaterialTheme.typography.bodyMedium)
                files.forEach { file -> key(file.url) {
                    var queued by remember { mutableStateOf(false) }
                    Surface(shape = MaterialTheme.shapes.large, color = MaterialTheme.colorScheme.surfaceContainerLow) {
                        Column(Modifier.fillMaxWidth().padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                            Text(file.fileName, style = MaterialTheme.typography.titleSmall, maxLines = 2, overflow = TextOverflow.Ellipsis)
                            Text(if (queued) "已加入系统下载队列" else file.kind, style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End, verticalAlignment = Alignment.CenterVertically) {
                                TextButton(onClick = { openBrowser(context, file.url) }) { Icon(Icons.Filled.OpenInNew, null, Modifier.size(18.dp)); Spacer(Modifier.width(6.dp)); Text("浏览器") }
                                Button(onClick = {
                                    try { enqueueHomeworkDownload(context, file); queued = true; toast(context, "已加入系统下载队列") }
                                    catch (_: Exception) { toast(context, "无法创建下载任务，可尝试用浏览器打开") }
                                }, enabled = !queued, shapes = ButtonDefaults.shapes()) {
                                    Icon(Icons.Filled.Download, null, Modifier.size(18.dp)); Spacer(Modifier.width(6.dp)); Text(if(queued) "已排队" else "下载")
                                }
                            }
                        }
                    }
                } }
            }
        }, confirmButton = { TextButton(onClick = {
            try { context.startActivity(Intent(DownloadManager.ACTION_VIEW_DOWNLOADS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
            catch (_: Exception) { toast(context, "请在系统文件应用中查看 Download/精准作业") }
        }) { Text("系统下载") } }, dismissButton = { TextButton(onClick = { opened = false }) { Text("关闭") } })
}
