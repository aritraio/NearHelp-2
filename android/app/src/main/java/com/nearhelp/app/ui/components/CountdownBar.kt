package com.nearhelp.app.ui.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nearhelp.app.ui.theme.Green
import com.nearhelp.app.ui.theme.Red
import com.nearhelp.app.ui.theme.Text1

/**
 * The 5-second cancel window (reference Screen 2 bottom bar / DESIGN.md §3):
 * green ✕ cancels, the red circle counts down, commit fires at zero. Pressing
 * cancel BEFORE zero means no API call was ever made — no responders notified.
 */
@Composable
fun CountdownBar(
    count: Int,
    onCancel: () -> Unit,
    modifier: Modifier = Modifier,
    message: String = "SENDING SOS…",
) {
    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(20.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Surface(shape = CircleShape, color = Green, modifier = Modifier.size(52.dp)) {
            IconButton(onClick = onCancel) {
                Icon(
                    imageVector = Icons.Filled.Close,
                    contentDescription = "Cancel",
                    tint = Color.White,
                )
            }
        }
        Text(
            text = message,
            fontWeight = FontWeight.Bold,
            fontSize = 16.sp,
            color = Text1,
        )
        Surface(shape = CircleShape, color = Red, modifier = Modifier.size(52.dp)) {
            Box(contentAlignment = Alignment.Center) {
                Text(
                    text = "$count",
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                    fontSize = 20.sp,
                )
            }
        }
    }
}

