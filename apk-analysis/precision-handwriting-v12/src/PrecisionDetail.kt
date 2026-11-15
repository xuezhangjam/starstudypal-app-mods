@file:OptIn(androidx.compose.material3.ExperimentalMaterial3ExpressiveApi::class)
package com.hailiang.workcloud.student.md3e.v3

import android.graphics.Color as AndroidColor
import android.graphics.drawable.GradientDrawable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.material.icons.automirrored.filled.Undo
import androidx.compose.material.icons.automirrored.filled.Redo
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalWindowInfo
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp
import com.hailiang.workcloud.student.data.enums.CheckMark
import com.hailiang.workcloud.student.shareui.work.review.model.*
import com.hailiang.workcloud.student.shareui.work.draft.*
import com.hailiang.workcloud.student.md3e.Palette
import kotlin.math.max
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive

/** Only the native selection foreground. Question content, layout and ink stay intact. */
fun questionForeground(selected: Boolean, cornerDp: Float, density: Float): GradientDrawable? {
    if (!selected) return null
    return GradientDrawable().apply {
        cornerRadius = cornerDp * density
        setColor(AndroidColor.TRANSPARENT)
        setStroke(max(1, (1.5f * density).toInt()), Palette.argb(3))
    }
}

fun reviewStateLabel(item: ReviewSidebarItemVo): String = when {
    item.getTag() == ReviewStatusTag.DOUBT -> "存疑"
    item.getTag() == ReviewStatusTag.PENDING_CORRECTION_CHECK -> "待订正"
    item.getTag() == ReviewStatusTag.PENDING_GRADING -> "待批阅"
    item.getAiUnrecognized() -> "未识别"
    item.getAiGrading() && item.getMark() == CheckMark.PENDING -> "批阅中"
    item.getMark() == CheckMark.CORRECT -> "正确"
    item.getMark() == CheckMark.HALF_WRONG -> "部分正确"
    item.getMark() == CheckMark.WRONG -> "错误"
    else -> "待批阅"
}

@Composable
fun ReviewMark(mark: CheckMark) {
    if (mark == CheckMark.PENDING) return
    val colors = MaterialTheme.colorScheme
    Icon(when (mark) {
        CheckMark.CORRECT -> Icons.Filled.Check
        CheckMark.WRONG -> Icons.Filled.Close
        else -> ToolGlyphs.HalfCorrect
    }, if (mark == CheckMark.HALF_WRONG) "部分正确" else if (mark == CheckMark.CORRECT) "正确" else "错误",
        Modifier.size(20.dp), tint = if (mark == CheckMark.WRONG) colors.error else if (mark == CheckMark.HALF_WRONG) colors.tertiary else colors.primary)
}

@Composable
fun QuestionNumber(item: ReviewSidebarItemVo, selected: Boolean, click: () -> Unit) {
    val colors = MaterialTheme.colorScheme
    val status = reviewStateLabel(item)
    val tint = when(item.getMark()) {
        CheckMark.WRONG -> colors.error
        CheckMark.CORRECT -> if (colors.surface.luminance() < 0.5f) Color(0xff81c995) else Color(0xff16803d)
        CheckMark.HALF_WRONG -> colors.tertiary
        else -> colors.onSurfaceVariant
    }
    Surface(onClick = click, shape = MaterialTheme.shapes.large,
        color = if (selected) colors.secondaryContainer else colors.surface,
        contentColor = if (selected) colors.onSecondaryContainer else colors.onSurface,
        modifier = Modifier.width(60.dp).heightIn(min = 56.dp).semantics {
            stateDescription = "${if(selected) "已选择，" else ""}$status"
            contentDescription = "第${item.getLabel()}题"
        }) {
        Column(Modifier.padding(horizontal = 4.dp, vertical = 7.dp), horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(3.dp)) {
            Text(item.getLabel(), style = MaterialTheme.typography.titleSmall, maxLines = 1)
            when {
                status == "批阅中" -> CircularProgressIndicator(Modifier.size(14.dp), strokeWidth = 2.dp)
                item.getTag() != null || item.getAiUnrecognized() -> {
                    if (item.getMark() == CheckMark.HALF_WRONG) {
                        Icon(ToolGlyphs.HalfCorrect, "部分正确", Modifier.size(18.dp), tint = tint)
                    }
                    Text(status, style = MaterialTheme.typography.labelSmall)
                }
                else -> Icon(when(item.getMark()) {
                    CheckMark.CORRECT -> Icons.Filled.Check
                    CheckMark.WRONG -> Icons.Filled.Close
                    CheckMark.HALF_WRONG -> ToolGlyphs.HalfCorrect
                    else -> Icons.Filled.MoreHoriz
                }, status, Modifier.size(16.dp), tint = tint)
            }
        }
    }
}

/** Chooses the same native tool enum; the existing router still owns ink and popups. */
@Composable
fun headerTitleWidth(): Float = with(LocalDensity.current) {
    boundedTitleWidth(LocalWindowInfo.current.containerSize.width.toDp().value)
}

@Composable
fun DraftTools(selected: DraftTool, penColor: Long, lineColor: Long, lineType: DraftLineType,
    choose: (DraftTool) -> Unit, modifier: Modifier?, defaults: Int) {
    val colors = MaterialTheme.colorScheme
    val density = LocalDensity.current
    val windowWidth = with(density) { LocalWindowInfo.current.containerSize.width.toDp().value }
    var history by remember { mutableStateOf(HistoryStatus()) }
    LaunchedEffect(Unit) {
        while (isActive) { history = InkHistory.status(); delay(180) }
    }
    DisposableEffect(Unit) { onDispose { InkHistory.reveal() } }
    Surface(modifier = if (defaults and 32 != 0) Modifier else modifier ?: Modifier,
        color = colors.surfaceContainerLowest, shape = CircleShape, shadowElevation = 6.dp) {
        Row(Modifier.widthIn(max = toolbarWidth(windowWidth).dp).horizontalScroll(rememberScrollState())
            .padding(6.dp), horizontalArrangement = Arrangement.spacedBy(2.dp), verticalAlignment = Alignment.CenterVertically) {
            DraftTool.entries.forEach { tool ->
                Surface(onClick = { InkHistory.reveal(); choose(tool) },
                    shape = CircleShape, color = if (tool == selected) colors.primaryContainer else Color.Transparent,
                    contentColor = if (tool == selected) colors.onPrimaryContainer else colors.onSurfaceVariant,
                    modifier = Modifier.size(50.dp).semantics { this.selected = tool == selected; role = Role.Button }) {
                    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Icon(when(tool) {
                            DraftTool.PEN -> if (selected == DraftTool.PEN) ToolGlyphs.PenSelected else ToolGlyphs.Pen
                            DraftTool.LINE -> if (lineType == DraftLineType.DASHED) ToolGlyphs.DashedLine else ToolGlyphs.Line
                            DraftTool.ERASER -> ToolGlyphs.Eraser
                        }, when(tool) {
                            DraftTool.PEN -> "画笔，再次点击设置颜色"
                            DraftTool.LINE -> if(lineType == DraftLineType.DASHED) "虚线，再次点击设置" else "直线，再次点击设置"
                            DraftTool.ERASER -> "橡皮"
                        }, Modifier.size(26.dp).offset(y = if(tool == DraftTool.ERASER) 0.dp else (-3).dp))
                        if (tool != DraftTool.ERASER) Surface(color = Color((if (tool == DraftTool.PEN) penColor else lineColor).toULong()),
                            shape = CircleShape, modifier = Modifier.align(Alignment.BottomCenter).padding(bottom = 7.dp).width(23.dp).height(5.dp)) {}
                    }
                }
            }
            IconButton(onClick = { InkHistory.undo(); history = InkHistory.status() }, enabled = history.undo, modifier = Modifier.size(50.dp)) {
                Icon(ToolGlyphs.Undo, "撤销上一步笔迹", Modifier.size(26.dp), tint = if(history.undo) colors.onSurfaceVariant else colors.onSurface.copy(alpha = 0.38f))
            }
            IconButton(onClick = { InkHistory.redo(); history = InkHistory.status() }, enabled = history.redo, modifier = Modifier.size(50.dp)) {
                Icon(ToolGlyphs.Redo, "重做笔迹", Modifier.size(26.dp), tint = if(history.redo) colors.onSurfaceVariant else colors.onSurface.copy(alpha = 0.38f))
            }
            IconButton(onClick = { AnswerVisibility.toggle() }, modifier = Modifier.size(50.dp).semantics {
                stateDescription = if (AnswerVisibility.visible) "参考答案和解析已显示" else "参考答案和解析已隐藏"
            }) {
                Icon(if(AnswerVisibility.visible) ToolGlyphs.VisibilityOff else ToolGlyphs.Visibility,
                    if(AnswerVisibility.visible) "隐藏参考答案和解析" else "显示参考答案和解析", Modifier.size(26.dp), tint = colors.onSurfaceVariant)
            }
        }
    }
}

@Composable
fun DetailAction(text: String, click: () -> Unit, modifier: Modifier?, enabled: Boolean, defaults: Int) {
    OutlinedButton(onClick = click, enabled = if (defaults and 8 != 0) true else enabled,
        shapes = ButtonDefaults.shapes(), modifier = (if (defaults and 4 != 0) Modifier else modifier ?: Modifier).heightIn(min = 48.dp)) { Text(text) }
}

@Composable
fun WrongBookEntry(showAdd: Boolean, click: () -> Unit) {
    AssistChip(onClick = click, enabled = showAdd, label = { Text(if (showAdd) "加入错题本" else "已加入错题本") },
        leadingIcon = { Icon(if (showAdd) Icons.Filled.AddCircleOutline else Icons.Filled.Check, null, Modifier.size(18.dp)) },
        shape = MaterialTheme.shapes.extraLarge)
}
