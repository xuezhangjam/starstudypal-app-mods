package com.hailiang.workcloud.student.md3e.v3

import android.view.MotionEvent
import com.hailiang.question.widget.view.QuestionHandwriteView
import java.util.WeakHashMap

object WritingTouch {
    private val gestures = WeakHashMap<QuestionHandwriteView, Gesture>()
    private const val PalmTool = 5
    private const val MaxHistoricalSamples = 12

    private class Gesture {
        var forwardedFingerDown = false
        var suppressFingers = false
        var pen: Pen? = null
    }

    private class Pen(event: MotionEvent, index: Int) {
        val properties = MotionEvent.PointerProperties().also { event.getPointerProperties(index, it) }
        val coordinates = MotionEvent.PointerCoords()
        val downTime = event.eventTime
        val propertyArray = arrayOf(properties)
        val coordinateArray = arrayOf(coordinates)

        fun forward(view: QuestionHandwriteView, event: MotionEvent, index: Int, action: Int) {
            if (index >= 0 && action == MotionEvent.ACTION_MOVE) {
                val history = event.historySize
                for (sample in (history - MaxHistoricalSamples).coerceAtLeast(0) until history) {
                    event.getHistoricalPointerCoords(index, sample, coordinates)
                    deliver(view, event, event.getHistoricalEventTime(sample), action)
                }
            }
            if (index >= 0) event.getPointerCoords(index, coordinates)
            deliver(view, event, event.eventTime, action)
        }

        private fun deliver(view: QuestionHandwriteView, event: MotionEvent, time: Long, action: Int) {
            if (properties.toolType == MotionEvent.TOOL_TYPE_STYLUS) {
                coordinates.pressure = coordinates.pressure.coerceAtLeast(0.35f)
            }
            val sample = MotionEvent.obtain(
                downTime, time, action, 1, propertyArray, coordinateArray,
                event.metaState, event.buttonState, event.xPrecision, event.yPrecision,
                event.deviceId, event.edgeFlags, event.source, event.flags,
            )
            try {
                view.modDispatchWritingEvent(sample)
            } finally {
                sample.recycle()
            }
        }
    }

    @JvmStatic
    fun isPenEvent(event: MotionEvent?): Boolean {
        if (event == null) return false
        return (0 until event.pointerCount).any { isPen(event.getToolType(it)) }
    }

    private fun isPen(tool: Int) =
        tool == MotionEvent.TOOL_TYPE_STYLUS || tool == MotionEvent.TOOL_TYPE_ERASER

    @JvmStatic
    fun forget(view: QuestionHandwriteView) {
        if (gestures.remove(view)?.suppressFingers == true) {
            view.parent?.requestDisallowInterceptTouchEvent(false)
        }
    }

    @JvmStatic
    fun dispatch(view: QuestionHandwriteView, event: MotionEvent?): Boolean {
        if (event == null) return view.modDispatchWritingEvent(null)
        val action = event.actionMasked
        if (action == MotionEvent.ACTION_DOWN) forget(view)
        val existing = gestures[view]
        if (existing == null && (!view.isEnabled || !view.getCanDraw() || view.isInGeometryEditMode())) {
            return view.modDispatchWritingEvent(event)
        }
        val endsGesture = action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL
        val gesture = existing ?: Gesture().also { gestures[view] = it }
        val pen = gesture.pen
        if (pen != null) {
            val index = event.findPointerIndex(pen.properties.id)
            val liftsPen = action == MotionEvent.ACTION_POINTER_UP && index == event.actionIndex
            when {
                action == MotionEvent.ACTION_CANCEL || index < 0 || !view.getCanDraw() -> {
                    pen.forward(view, event, index, MotionEvent.ACTION_CANCEL)
                    gesture.pen = null
                }
                action == MotionEvent.ACTION_UP || liftsPen -> {
                    pen.forward(view, event, index, MotionEvent.ACTION_UP)
                    gesture.pen = null
                }
                action == MotionEvent.ACTION_MOVE -> {
                    pen.forward(view, event, index, MotionEvent.ACTION_MOVE)
                }
            }
            if (endsGesture) forget(view)
            else view.parent?.requestDisallowInterceptTouchEvent(true)
            return true
        }

        if (action == MotionEvent.ACTION_DOWN || action == MotionEvent.ACTION_POINTER_DOWN) {
            val index = event.actionIndex
            val tool = event.getToolType(index)
            if (isPen(tool)) {
                if (gesture.forwardedFingerDown) {
                    val cancel = MotionEvent.obtainNoHistory(event)
                    try {
                        cancel.action = MotionEvent.ACTION_CANCEL
                        view.modDispatchWritingEvent(cancel)
                    } finally {
                        cancel.recycle()
                    }
                    gesture.forwardedFingerDown = false
                }
                val newPen = Pen(event, index)
                gesture.pen = newPen
                gesture.suppressFingers = true
                view.parent?.requestDisallowInterceptTouchEvent(true)
                if (tool == MotionEvent.TOOL_TYPE_STYLUS) ensureReadableWidth(view)
                newPen.forward(view, event, index, MotionEvent.ACTION_DOWN)
                return true
            }
            if (action == MotionEvent.ACTION_DOWN) {
                // Keep the native core's threshold for controllers that report palms as fingers.
                gesture.suppressFingers = tool == PalmTool ||
                    (tool == MotionEvent.TOOL_TYPE_FINGER &&
                        event.getSize(index) > 0.4f && event.getPressure(index) < 0.1f)
                if (gesture.suppressFingers) view.parent?.requestDisallowInterceptTouchEvent(true)
                else if (tool == MotionEvent.TOOL_TYPE_FINGER) ensureReadableWidth(view)
            }
        }
        if (endsGesture) forget(view)
        if (gesture.suppressFingers) return true
        val handled = view.modDispatchWritingEvent(event)
        if (action == MotionEvent.ACTION_DOWN) gesture.forwardedFingerDown = handled
        return handled
    }

    private fun ensureReadableWidth(view: QuestionHandwriteView) {
        val minimum = (1.8f * view.resources.displayMetrics.density).coerceAtLeast(3.2f)
        if (view.getStrokeWidth() < minimum) view.setStrokeWidth(minimum)
    }
}
