package com.nearhelp.app.ui.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nearhelp.app.ui.theme.Blue
import com.nearhelp.app.ui.theme.RedDeep
import com.nearhelp.app.ui.theme.Text2
import com.nearhelp.app.ui.theme.Text3

/**
 * Guidance step card (DESIGN.md §3): numbered instruction + its source
 * citation + confidence dot. The disclaimer strip below is non-dismissible.
 */
@Composable
fun GuidanceCard(index: Int, text: String, source: String) {
    GlassCard(Modifier.fillMaxWidth()) {
        Row {
            Surface(shape = CircleShape, color = Blue.copy(alpha = 0.15f)) {
                Text(
                    text = "${index + 1}",
                    color = Blue,
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    modifier = Modifier.padding(horizontal = 9.dp, vertical = 3.dp),
                )
            }
            Spacer(Modifier.size(12.dp))
            Column(Modifier.padding(top = 2.dp)) {
                Text(text = text, fontSize = 15.sp, color = com.nearhelp.app.ui.theme.Text1)
                Text(
                    text = source,
                    fontSize = 10.sp,
                    color = Text3,
                    modifier = Modifier.padding(top = 4.dp),
                )
            }
        }
    }
}

/**
 * The persistent, non-dismissible medical disclaimer (proposal §13.4).
 * Rendered under every guidance surface — never a dismissible dialog.
 */
@Composable
fun DisclaimerStrip(text: String) {
    Surface(
        shape = MaterialTheme.shapes.small,
        color = Color(0xFFFDECEA),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text(
            text = "⚠ $text",
            fontSize = 10.sp,
            color = RedDeep,
            lineHeight = 14.sp,
            modifier = Modifier.padding(10.dp),
        )
    }
}

@Composable
fun ModePill(mode: String) {
    val label = when (mode) {
        "rag" -> "AI-generated · cited"
        "retrieval_only" -> "verified protocol · offline AI"
        "fallback" -> "call services"
        else -> mode
    }
    Surface(shape = CircleShape, color = Color(0xE6FFFFFF)) {
        Text(
            text = label,
            fontSize = 10.sp,
            fontWeight = FontWeight.Bold,
            color = Text2,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
        )
    }
}
