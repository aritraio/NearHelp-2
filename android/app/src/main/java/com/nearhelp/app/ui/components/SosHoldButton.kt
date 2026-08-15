package com.nearhelp.app.ui.components

import androidx.compose.animation.core.Animatable
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.waitForUpOrCancellation
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nearhelp.app.ui.theme.Red
import com.nearhelp.app.ui.theme.SurfaceGlass
import com.nearhelp.app.ui.theme.Text1
import kotlinx.coroutines.delay
import kotlin.math.roundToInt

/**
 * The core SOS control (DESIGN.md §3): hold for [holdMillis] to fire — the
 * sweep arc fills the ring, haptics tick at 50 % and at fire; releasing early
 * shakes, resets and reports (the false-alarm guard from improvements.md §2.3).
 *
 * The fill loop polls [pressing], so an early release aborts without firing;
 * the shake runs in the gesture scope after the finger lifts.
 */
@Composable
fun SosHoldButton(
    onFired: () -> Unit,
    modifier: Modifier = Modifier,
    holdMillis: Long = 3_000,
    sizeDp: Int = 160,
    label: String = "HOLD FOR SOS",
    ringColor: Color = Red,
) {
    val haptics = LocalHapticFeedback.current
    val progress = remember { Animatable(0f) }
    val shake = remember { Animatable(0f) }
    var pressing by remember { mutableStateOf(false) }
    var halfHapticDone by remember { mutableStateOf(false) }

    LaunchedEffect(pressing) {
        if (!pressing) return@LaunchedEffect
        val started = System.currentTimeMillis()
        while (pressing) {
            val elapsed = System.currentTimeMillis() - started
            val fraction = (elapsed / holdMillis.toFloat()).coerceIn(0f, 1f)
            progress.snapTo(fraction)
            if (!halfHapticDone && fraction >= 0.5f) {
                halfHapticDone = true
                haptics.performHapticFeedback(HapticFeedbackType.LongPress)
            }
            if (fraction >= 1f) {
                haptics.performHapticFeedback(HapticFeedbackType.LongPress)
                onFired()
                delay(350) // let the completed ring be seen before reset
                break
            }
            delay(16)
        }
        if (progress.value < 1f) progress.snapTo(0f)
    }

    Box(
        contentAlignment = Alignment.Center,
        modifier = modifier
            .size(sizeDp.dp)
            .offset { IntOffset(shake.value.roundToInt(), 0) }
            .pointerInput(Unit) {
                awaitEachGesture {
                    awaitFirstDown()
                    pressing = true
                    halfHapticDone = false
                    // Suspends until the pointer lifts (or leaves the bounds).
                    waitForUpOrCancellation()
                    val early = progress.value < 1f
                    pressing = false
                    if (early) {
                        for (i in 1..4) {
                            shake.snapTo(if (i % 2 == 0) 12f else -12f)
                            delay(35)
                        }
                        shake.snapTo(0f)
                    }
                }
            },
    ) {
        Surface(shape = MaterialTheme.shapes.extraLarge, color = SurfaceGlass) {
            Box(contentAlignment = Alignment.Center, modifier = Modifier.size(sizeDp.dp)) {
                val strokeWidth = 10.dp
                Canvas(Modifier.size((sizeDp - 16).dp)) {
                    val inset = strokeWidth.toPx() / 2
                    val diameter = size.width - inset * 2
                    drawArc(
                        color = ringColor,
                        startAngle = -90f,
                        sweepAngle = 360f * progress.value,
                        useCenter = false,
                        topLeft = Offset(inset, inset),
                        size = Size(diameter, diameter),
                        style = Stroke(width = strokeWidth.toPx(), cap = StrokeCap.Round),
                    )
                }
                Text(
                    text = label,
                    fontSize = if (sizeDp >= 140) 16.sp else 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = Text1,
                )
            }
        }
    }
}
