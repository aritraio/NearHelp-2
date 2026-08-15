package com.nearhelp.app.ui.components

import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nearhelp.app.ui.theme.GreenDeep
import com.nearhelp.app.ui.theme.SurfaceGlassHi
import com.nearhelp.app.ui.theme.Text2

/** Small glass pill for live stats — "14 responders · ~3 min" (DESIGN.md §3). */
@Composable
fun StatPill(text: String, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(50),
        color = SurfaceGlassHi,
    ) {
        Text(
            text = text,
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold,
            color = Text2,
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
        )
    }
}

/** Emergency-count variant used on Home. */
@Composable
fun ResponderStatPill(count: Int?, modifier: Modifier = Modifier) {
    val label = if (count == null) "responder network…" else "$count responders · ~3 min"
    StatPill(text = label, modifier = modifier)
}

@Composable
fun HintPill(text: String, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(50),
        color = SurfaceGlassHi,
    ) {
        Text(
            text = text,
            fontSize = 10.sp,
            color = GreenDeep,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
        )
    }
}
