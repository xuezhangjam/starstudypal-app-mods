@file:OptIn(androidx.compose.material3.ExperimentalMaterial3ExpressiveApi::class)
package com.hailiang.workcloud.student.md3e.v3

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Description
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp

/** Shared native controls, with original text, enablement and callback identity. */
@Composable
fun DraftSurface(click: (() -> Unit)?, defaults: Int) {
    TextButton(onClick = if (defaults and 1 != 0) ({}) else (click ?: {}),
        shapes = ButtonDefaults.shapes(), modifier = Modifier.heightIn(min = 48.dp)) {
        Icon(Icons.Filled.Description, null, Modifier.size(18.dp)); Spacer(Modifier.width(8.dp)); Text("草稿")
    }
}

fun taskActionLabel(taskNumber: Int, totalCount: Int, submitted: Boolean): String = when {
    submitted -> "任务 $taskNumber 已提交"
    totalCount > 1 -> "提交任务 $taskNumber"
    else -> "提交作业"
}

// Same guard as the original SubmitTaskButton clickable: enabled && !loading && !submitted.
fun taskActionEnabled(submitted: Boolean, enabled: Boolean, loading: Boolean): Boolean =
    enabled && !loading && !submitted

@Composable
fun SubmitSurface(taskNumber: Int, totalCount: Int, submitted: Boolean, enabled: Boolean,
    loading: Boolean, click: () -> Unit, modifier: Modifier?, defaults: Int) {
    Button(onClick = click, enabled = taskActionEnabled(submitted, enabled, loading), shapes = ButtonDefaults.shapes(),
        modifier = (if (defaults and 64 != 0) Modifier else modifier ?: Modifier).heightIn(min = 48.dp)) {
        if (loading) { CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp); Spacer(Modifier.width(8.dp)) }
        Text(taskActionLabel(taskNumber, totalCount, submitted))
    }
}

@Composable
fun CorrectionSurface(text: String, enabled: Boolean, click: () -> Unit, modifier: Modifier?, defaults: Int) {
    Button(onClick = click, enabled = enabled, shapes = ButtonDefaults.shapes(),
        modifier = (if (defaults and 8 != 0) Modifier else modifier ?: Modifier).heightIn(min = 48.dp)) { Text(text) }
}

@Composable
fun ReviewChoiceSurface(text: String, selected: Boolean, click: () -> Unit, modifier: Modifier?, defaults: Int) {
    FilterChip(selected = selected, onClick = click, label = { Text(text) },
        modifier = (if (defaults and 8 != 0) Modifier else modifier ?: Modifier).heightIn(min = 48.dp))
}

@Composable
fun InfoSurface(message: String, button: String, dismiss: () -> Unit, title: String?, defaults: Int) {
    val heading = if (defaults and 8 != 0) null else title
    AlertDialog(onDismissRequest = dismiss,
        title = heading?.let { { Text(it) } },
        text = { Text(message, Modifier.heightIn(max = 440.dp).verticalScroll(rememberScrollState())) },
        confirmButton = { TextButton(onClick = dismiss, shapes = ButtonDefaults.shapes()) { Text(button) } })
}

@Composable
fun ActionSurface(title: String, cancel: String?, confirm: String?, onCancel: () -> Unit,
    onConfirm: () -> Unit, content: @Composable () -> Unit, defaults: Int) {
    val cancelLabel = if (defaults and 2 != 0) "取消" else cancel.orEmpty()
    val confirmLabel = if (defaults and 4 != 0) "确定" else confirm.orEmpty()
    AlertDialog(onDismissRequest = onCancel, title = { Text(title) },
        text = { Column(Modifier.heightIn(max = 480.dp).verticalScroll(rememberScrollState())) { content() } },
        dismissButton = { TextButton(onClick = onCancel, shapes = ButtonDefaults.shapes()) { Text(cancelLabel) } },
        confirmButton = { TextButton(onClick = onConfirm, shapes = ButtonDefaults.shapes()) { Text(confirmLabel) } })
}

fun resolvedAlignment(value: Int, defaults: Int): TextAlign = if (defaults and 128 != 0) TextAlign.Center else when(value) {
    1 -> TextAlign.Left
    2 -> TextAlign.Right
    3 -> TextAlign.Center
    4 -> TextAlign.Justify
    6 -> TextAlign.End
    else -> TextAlign.Start
}

@Composable
fun ConfirmationSurface(title: String, message: String, cancel: String?, confirm: String?,
    onCancel: () -> Unit, onConfirm: () -> Unit, onDismiss: (() -> Unit)?, alignment: Int,
    reverse: Boolean, defaults: Int) {
    val cancelLabel = if (defaults and 4 != 0) "取消" else cancel.orEmpty()
    val confirmLabel = if (defaults and 8 != 0) "确定" else confirm.orEmpty()
    val dismiss = if (defaults and 64 != 0) onCancel else onDismiss ?: onCancel
    val reversed = defaults and 256 == 0 && reverse
    AlertDialog(onDismissRequest = dismiss, title = { Text(title) },
        text = { Text(message, Modifier.fillMaxWidth().heightIn(max = 440.dp).verticalScroll(rememberScrollState()),
            textAlign = resolvedAlignment(alignment, defaults)) },
        dismissButton = { TextButton(onClick = if (reversed) onConfirm else onCancel, shapes = ButtonDefaults.shapes()) {
            Text(if (reversed) confirmLabel else cancelLabel)
        } },
        confirmButton = { TextButton(onClick = if (reversed) onCancel else onConfirm, shapes = ButtonDefaults.shapes()) {
            Text(if (reversed) cancelLabel else confirmLabel)
        } })
}
