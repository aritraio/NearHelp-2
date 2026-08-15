package com.nearhelp.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Icon
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nearhelp.app.ui.components.SosHoldButton
import com.nearhelp.app.ui.crisisCategory
import com.nearhelp.app.ui.theme.BgRespond
import com.nearhelp.app.ui.theme.Blue
import com.nearhelp.app.ui.theme.Text1
import com.nearhelp.app.ui.theme.Text2
import kotlinx.coroutines.delay

/**
 * Responder alert (DESIGN.md §5): full-bleed blue, category + severity,
 * hold-to-confirm respond (1.5 s), 20 s auto-dismiss so stale alerts don't
 * haunt the tray. Reached via FCM deep link or foreground push routing.
 */
@Composable
fun AlertScreen(
    sosId: String,
    crisisType: String?,
    isDrill: Boolean,
    onResponded: (String) -> Unit,
    onDismiss: () -> Unit,
    viewModel: IncidentViewModel = androidx.hilt.navigation.compose.hiltViewModel(),
) {
    val category = crisisCategory(crisisType)
    var remaining by remember { mutableIntStateOf(20) }
    val state by viewModel.state.collectAsStateWithLifecycle()

    LaunchedEffect(sosId) {
        while (remaining > 0) {
            delay(1_000)
            remaining -= 1
        }
        if (!state.iAmResponder) onDismiss()
    }

    if (state.iAmResponder) {
        LaunchedEffect(state.iAmResponder) { onResponded(sosId) }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Brush.verticalGradient(BgRespond, Color(0xFFF4F8FE)))
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Spacer(Modifier.height(48.dp))
        if (isDrill) {
            Surface(color = Blue, shape = androidx.compose.material3.MaterialTheme.shapes.small) {
                Text(
                    "DRILL — NOT A REAL EMERGENCY",
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp,
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                )
            }
            Spacer(Modifier.height(16.dp))
        }
        Surface(
            shape = androidx.compose.material3.MaterialTheme.shapes.extraLarge,
            color = Color.White,
            modifier = Modifier.size(96.dp),
        ) {
            Box(contentAlignment = Alignment.Center) {
                Icon(
                    imageVector = category.icon,
                    contentDescription = null,
                    tint = category.color,
                    modifier = Modifier.size(48.dp),
                )
            }
        }
        Spacer(Modifier.height(16.dp))
        Text(
            text = "${category.label} emergency nearby",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold,
            color = Text1,
            textAlign = TextAlign.Center,
        )
        Text(
            text = "someone within walking distance needs help now",
            fontSize = 14.sp,
            color = Text2,
            textAlign = TextAlign.Center,
        )

        Spacer(Modifier.weight(1f))
        SosHoldButton(
            onFired = { viewModel.respond() },
            holdMillis = 1_500,
            sizeDp = 140,
            label = "HOLD TO RESPOND",
            ringColor = Blue,
        )
        state.error?.let {
            Text(it, color = androidx.compose.ui.graphics.Color(0xFFD32F2F), fontSize = 12.sp)
        }
        Spacer(Modifier.height(24.dp))
        Text(
            text = "dismiss in ${remaining}s",
            fontSize = 12.sp,
            color = Text2,
            modifier = Modifier
                .padding(bottom = 24.dp)
                .clickable { onDismiss() },
        )
    }
}
