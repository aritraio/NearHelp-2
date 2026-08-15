package com.nearhelp.app.ui.screens

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.nearhelp.app.ui.components.CategoryChip
import com.nearhelp.app.ui.components.GlassCard
import com.nearhelp.app.ui.crisisCategory
import com.nearhelp.app.ui.theme.BgIncident
import com.nearhelp.app.ui.theme.Blue
import com.nearhelp.app.ui.theme.Green
import com.nearhelp.app.ui.theme.Red
import com.nearhelp.app.ui.theme.RedDeep
import com.nearhelp.app.ui.theme.Text1
import com.nearhelp.app.ui.theme.Text2
import com.nearhelp.app.ui.theme.Text3

/**
 * Incident status (Phase 3 slice of DESIGN.md §4.3): state banner, responder
 * list, timeline, escalation cues, resolve, and the wave-3 call-services
 * action. Live map/chat/streaming arrive with Phase 4.
 */
@Composable
fun IncidentScreen(
    onDone: () -> Unit,
    viewModel: IncidentViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val event = state.event

    Surface(modifier = Modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(Brush.verticalGradient(BgIncident, Color(0xFFFDF7F6)))
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
        ) {
            if (event?.is_drill == true) {
                Surface(color = Blue, shape = MaterialTheme.shapes.small) {
                    Text(
                        "DRILL — NOT A REAL EMERGENCY",
                        color = Color.White,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                    )
                }
                Spacer(Modifier.height(8.dp))
            }

            event?.let { ev ->
                Text(
                    text = when (ev.status) {
                        "pending" -> "SEARCHING FOR RESPONDERS"
                        "active" -> "RESPONDER ON THE WAY"
                        "resolved" -> "RESOLVED"
                        else -> ev.status.uppercase()
                    },
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold,
                    color = if (ev.status == "resolved") Green else RedDeep,
                )
                Row(verticalAlignment = Alignment.CenterVertically) {
                    CategoryChip(crisisCategory(ev.crisis_type))
                    Spacer(Modifier.weight(1f))
                    Text(
                        text = "wave ${ev.escalation_wave}",
                        fontSize = 12.sp,
                        color = Text2,
                    )
                }
                if (ev.status == "pending" && ev.escalation_wave > 0) {
                    Text(
                        "Search expanded to ×${ev.radius_m / 1000} km radius",
                        fontSize = 12.sp,
                        color = Text2,
                    )
                }
                if (ev.status == "pending" && ev.escalation_wave >= 3 && !ev.is_drill) {
                    Spacer(Modifier.height(12.dp))
                    Button(
                        onClick = { context.startActivity(Intent(Intent.ACTION_DIAL, Uri.parse("tel:112"))) },
                        colors = ButtonDefaults.buttonColors(containerColor = Red),
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text("CALL 112 / 108 NOW", fontWeight = FontWeight.Bold)
                    }
                }

                Spacer(Modifier.height(16.dp))
                GlassCard(Modifier.fillMaxWidth()) {
                    Text("Responders (${ev.notified_count} notified)", fontWeight = FontWeight.Bold)
                    ev.responders.forEach { responder ->
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.padding(top = 8.dp),
                        ) {
                            Box(
                                modifier = Modifier
                                    .height(8.dp)
                                    .background(
                                        when (responder.status) {
                                            "accepted" -> Green
                                            "acked" -> Blue
                                            else -> Text3
                                        },
                                        MaterialTheme.shapes.extraSmall,
                                    )
                                    .fillMaxWidth(0.06f)
                            )
                            Text(
                                text = " ${responder.name} — ${responder.status}",
                                fontSize = 13.sp,
                                color = Text1,
                            )
                        }
                    }
                }

                Spacer(Modifier.height(16.dp))
                GlassCard(Modifier.fillMaxWidth()) {
                    Text("Timeline", fontWeight = FontWeight.Bold)
                    state.timeline.reversed().take(12).forEach { item ->
                        Text(
                            text = "• ${item.event_type.replace('_', ' ')}",
                            fontSize = 12.sp,
                            color = Text2,
                            modifier = Modifier.padding(top = 6.dp),
                        )
                    }
                }
            } ?: Text("loading…", color = Text2)

            state.error?.let {
                Text(it, color = RedDeep, fontSize = 12.sp, modifier = Modifier.padding(top = 8.dp))
            }

            Spacer(Modifier.weight(1f))
            Spacer(Modifier.height(20.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                OutlinedButton(onClick = onDone, modifier = Modifier.weight(1f)) {
                    Text(if (event?.status == "resolved") "DONE" else "BACK")
                }
                if (state.iAmNotifiedResponder && !state.iAmResponder && event?.status == "pending") {
                    Button(
                        onClick = { viewModel.respond() },
                        colors = ButtonDefaults.buttonColors(containerColor = Blue),
                        modifier = Modifier.weight(1f),
                    ) { Text("I'M RESPONDING", fontWeight = FontWeight.Bold) }
                } else if (event != null && event.status != "resolved") {
                    Button(
                        onClick = viewModel::resolve,
                        colors = ButtonDefaults.buttonColors(containerColor = Green),
                        modifier = Modifier.weight(1f),
                    ) { Text("RESOLVE", fontWeight = FontWeight.Bold) }
                }
            }
            Spacer(Modifier.height(32.dp))
        }
    }
}
