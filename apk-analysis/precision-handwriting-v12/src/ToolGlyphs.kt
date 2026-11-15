// Pen, eraser, undo, redo and eye use the retained Google Material Symbols (Apache-2.0).
// Line tools use simple solid/dashed stroke previews of their current drawing mode.
package com.hailiang.workcloud.student.md3e.v3
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.PathParser
import androidx.compose.ui.graphics.vector.group
import androidx.compose.ui.graphics.vector.path
import androidx.compose.ui.unit.dp
object ToolGlyphs {
    // Traditional partial-credit check: a checkmark crossed by a short diagonal.
    val HalfCorrect: ImageVector by lazy { ImageVector.Builder("HomeworkHalfCorrect", 24.dp, 24.dp, 24f, 24f).apply {
        path(fill = null, stroke = SolidColor(Color.Black), strokeLineWidth = 2f, strokeLineCap = StrokeCap.Round) {
            moveTo(3f, 12f); lineTo(8.5f, 18f); lineTo(20.5f, 5f)
            moveTo(10f, 8f); lineTo(17f, 15f)
        }
    }.build() }
    val Pen: ImageVector by lazy { ImageVector.Builder("Google_ink_pen", 24.dp, 24.dp, 960.0f, 960.0f, autoMirror = false).apply {
        group(translationX = -0.0f, translationY = 960.0f) {
            addPath(pathData = PathParser().parsePathString("m490-527 37 37 217-217-37-37-217 217ZM200-200h37l233-233-37-37-233 233v37Zm355-205L405-555l167-167-29-29-219 219-56-56 218-219q24-24 56.5-24t56.5 24l29 29 50-50q12-12 28.5-12t28.5 12l93 93q12 12 12 28.5T828-678L555-405ZM270-120H120v-150l285-285 150 150-285 285Z").toNodes(), fill = SolidColor(Color.Black))
        }
    }.build() }
    val PenSelected: ImageVector by lazy { ImageVector.Builder("Google_ink_pen_fill1", 24.dp, 24.dp, 960.0f, 960.0f, autoMirror = false).apply {
        group(translationX = -0.0f, translationY = 960.0f) {
            addPath(pathData = PathParser().parsePathString("M611-461 461-612l111-110-29-29-219 219-56-56 218-219q24-24 56.5-24t56.5 24l29 29 50-50q12-12 28.5-12t28.5 12l93 93q12 12 12 28.5T828-678L611-461ZM270-120H120v-150l284-285 151 150-285 285Z").toNodes(), fill = SolidColor(Color.Black))
        }
    }.build() }
    val Line: ImageVector by lazy { line(false) }
    val DashedLine: ImageVector by lazy { line(true) }
    private fun line(dashed: Boolean): ImageVector = ImageVector.Builder(
        if (dashed) "HomeworkDashedLine" else "HomeworkSolidLine", 24.dp, 24.dp, 24f, 24f
    ).apply {
        path(fill = null, stroke = SolidColor(Color.Black), strokeLineWidth = 1.8f,
            strokeLineCap = StrokeCap.Round) {
            if (dashed) {
                moveTo(4f, 20f); lineTo(7f, 17f)
                moveTo(10f, 14f); lineTo(13f, 11f)
                moveTo(16f, 8f); lineTo(20f, 4f)
            } else { moveTo(4f, 20f); lineTo(20f, 4f) }
        }
    }.build()
    val Eraser: ImageVector by lazy { ImageVector.Builder("Google_ink_eraser", 24.dp, 24.dp, 960.0f, 960.0f, autoMirror = false).apply {
        group(translationX = -0.0f, translationY = 960.0f) {
            addPath(pathData = PathParser().parsePathString("M690-240h190v80H610l80-80Zm-500 80-85-85q-23-23-23.5-57t22.5-58l440-456q23-24 56.5-24t56.5 23l199 199q23 23 23 57t-23 57L520-160H190Zm296-80 314-322-198-198-442 456 64 64h262Zm-6-240Z").toNodes(), fill = SolidColor(Color.Black))
        }
    }.build() }
    val Undo: ImageVector by lazy { ImageVector.Builder("Google_undo", 24.dp, 24.dp, 960.0f, 960.0f, autoMirror = true).apply {
        group(translationX = -0.0f, translationY = 960.0f) {
            addPath(pathData = PathParser().parsePathString("M280-200v-80h284q63 0 109.5-40T720-420q0-60-46.5-100T564-560H312l104 104-56 56-200-200 200-200 56 56-104 104h252q97 0 166.5 63T800-420q0 94-69.5 157T564-200H280Z").toNodes(), fill = SolidColor(Color.Black))
        }
    }.build() }
    val Redo: ImageVector by lazy { ImageVector.Builder("Google_redo", 24.dp, 24.dp, 960.0f, 960.0f, autoMirror = true).apply {
        group(translationX = -0.0f, translationY = 960.0f) {
            addPath(pathData = PathParser().parsePathString("M396-200q-97 0-166.5-63T160-420q0-94 69.5-157T396-640h252L544-744l56-56 200 200-200 200-56-56 104-104H396q-63 0-109.5 40T240-420q0 60 46.5 100T396-280h284v80H396Z").toNodes(), fill = SolidColor(Color.Black))
        }
    }.build() }
    val Visibility: ImageVector by lazy { ImageVector.Builder("Google_visibility", 24.dp, 24.dp, 960.0f, 960.0f, autoMirror = false).apply {
        group(translationX = -0.0f, translationY = 960.0f) {
            addPath(pathData = PathParser().parsePathString("M480-320q75 0 127.5-52.5T660-500q0-75-52.5-127.5T480-680q-75 0-127.5 52.5T300-500q0 75 52.5 127.5T480-320Zm0-72q-45 0-76.5-31.5T372-500q0-45 31.5-76.5T480-608q45 0 76.5 31.5T588-500q0 45-31.5 76.5T480-392Zm0 192q-146 0-266-81.5T40-500q54-137 174-218.5T480-800q146 0 266 81.5T920-500q-54 137-174 218.5T480-200Zm0-300Zm0 220q113 0 207.5-59.5T832-500q-50-101-144.5-160.5T480-720q-113 0-207.5 59.5T128-500q50 101 144.5 160.5T480-280Z").toNodes(), fill = SolidColor(Color.Black))
        }
    }.build() }
    val VisibilityOff: ImageVector by lazy { ImageVector.Builder("Google_visibility_off", 24.dp, 24.dp, 960.0f, 960.0f, autoMirror = false).apply {
        group(translationX = -0.0f, translationY = 960.0f) {
            addPath(pathData = PathParser().parsePathString("m644-428-58-58q9-47-27-88t-93-32l-58-58q17-8 34.5-12t37.5-4q75 0 127.5 52.5T660-500q0 20-4 37.5T644-428Zm128 126-58-56q38-29 67.5-63.5T832-500q-50-101-143.5-160.5T480-720q-29 0-57 4t-55 12l-62-62q41-17 84-25.5t90-8.5q151 0 269 83.5T920-500q-23 59-60.5 109.5T772-302Zm20 246L624-222q-35 11-70.5 16.5T480-200q-151 0-269-83.5T40-500q21-53 53-98.5t73-81.5L56-792l56-56 736 736-56 56ZM222-624q-29 26-53 57t-41 67q50 101 143.5 160.5T480-280q20 0 39-2.5t39-5.5l-36-38q-11 3-21 4.5t-21 1.5q-75 0-127.5-52.5T300-500q0-11 1.5-21t4.5-21l-84-82Zm319 93Zm-151 75Z").toNodes(), fill = SolidColor(Color.Black))
        }
    }.build() }
}
