package com.nearhelp.app.ui.screens

import android.content.Intent
import android.content.pm.PackageManager
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
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
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
import com.google.android.gms.maps.model.CameraPosition
import com.google.android.gms.maps.model.LatLng
import com.google.maps.android.compose.GoogleMap
import com.google.maps.android.compose.MapUiSettings
import com.google.maps.android.compose.Marker
import com.google.maps.android.compose.rememberCameraPositionState
import com.google.maps.android.compose.rememberMarkerState
import com.nearhelp.app.service.distanceMeters
import com.nearhelp.app.ui.components.CategoryChip
import com.nearhelp.app.ui.components.GlassCard
import com.nearhelp.app.ui.components.HintPill
import com.nearhelp.app.ui.crisisCategory
import com.nearhelp.app.ui.theme.BgIncident
import com.nearhelp.app.ui.theme.Blue
import com.nearhelp.app.ui.theme.Green
import com.nearhelp.app.ui.theme.GreenDeep
import com.nearhelp.app.ui.theme.Red
import com.nearhelp.app.ui.theme.RedDeep
import com.nearhelp.app.ui.theme.Text1
import com.nearhelp.app.ui.theme.Text2
import com.nearhelp.app.ui.theme.Text3

/**
 * Incident Active (DESIGN.md §4.3): status header + escalation cues on top of
 * the Guidance | Map | Chat | Timeline tabs (Guidance fills in Phase 5). The
 * map degrades to a distance/ETA panel when no Maps key is configured.
 */
@Composable
fun IncidentScreen(
    onDone: () -> Unit,
    viewModel: IncidentViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val event = state.event
    var tab by remember { mutableIntStateOf(1) } // start on the map

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Brush.verticalGradient(listOf(BgIncident, Color(0xFFFDF7F6)))),
    ) {
        Column(Modifier.padding(horizontal = 20.dp)) {
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
                Spacer(Modifier.height(6.dp))
            }
            event?.let { ev ->
                Text(
                    text = when (ev.status) {
                        "pending" -> "SEARCHING FOR RESPONDERS"
                        "active" -> "RESPONDER ON THE WAY"
                        "resolved" -> "RESOLVED"
                        else -> ev.status.uppercase()
                    },
                    fontSize = 22.sp,
                    fontWeight = FontWeight.Bold,
                    color = if (ev.status == "resolved") Green else RedDeep,
                )
                Row(verticalAlignment = Alignment.CenterVertically) {
                    CategoryChip(crisisCategory(ev.crisis_type))
                    Spacer(Modifier.width(8.dp))
                    HintPill(if (state.wsConnected) "live" else "reconnecting…")
                    Spacer(Modifier.weight(1f))
                    Text("wave ${ev.escalation_wave}", fontSize = 12.sp, color = Text2)
                }
                if (ev.status == "pending" && ev.escalation_wave > 0) {
                    Text(
                        "Search expanded to ×${ev.radius_m / 1000} km radius",
                        fontSize = 12.sp,
                        color = Text2,
                    )
                }
                if ((state.callPrompt || ev.escalation_wave >= 3) && !ev.is_drill && ev.status != "resolved") {
                    Spacer(Modifier.height(8.dp))
                    Button(
                        onClick = {
                            context.startActivity(
                                Intent(Intent.ACTION_DIAL, Uri.parse("tel:112"))
                            )
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = Red),
                        modifier = Modifier.fillMaxWidth(),
                    ) { Text("CALL 112 / 108 NOW", fontWeight = FontWeight.Bold) }
                }
            } ?: Text("loading…", color = Text2)
            state.error?.let {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(it, color = RedDeep, fontSize = 12.sp, modifier = Modifier.weight(1f))
                    OutlinedButton(onClick = viewModel::dismissError) { Text("ok") }
                }
            }
            Spacer(Modifier.height(10.dp))
        }

        TabRow(selectedTabIndex = tab) {
            listOf("Guidance", "Map", "Chat", "Timeline").forEachIndexed { index, label ->
                Tab(
                    selected = tab == index,
                    onClick = { tab = index },
                    text = { Text(label, fontSize = 12.sp, fontWeight = FontWeight.Bold) },
                )
            }
        }

        Box(Modifier.weight(1f)) {
            when (tab) {
                0 -> GuidancePlaceholder(state)
                1 -> MapTab(state)
                2 -> ChatTab(state, viewModel::sendMessage)
                else -> TimelineTab(state)
            }
        }

        Row(
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
        ) {
            OutlinedButton(onClick = onDone, modifier = Modifier.weight(1f)) {
                Text(if (event?.status == "resolved") "DONE" else "BACK")
            }
            if (event != null && event.status != "resolved") {
                when {
                    state.iAmResponder && !state.iArrived -> Button(
                        onClick = viewModel::arrive,
                        colors = ButtonDefaults.buttonColors(containerColor = Blue),
                        modifier = Modifier.weight(1.4f),
                    ) { Text("I'VE ARRIVED", fontWeight = FontWeight.Bold) }

                    state.iAmNotifiedResponder && !state.iAmResponder -> Button(
                        onClick = { viewModel.respond() },
                        colors = ButtonDefaults.buttonColors(containerColor = Blue),
                        modifier = Modifier.weight(1.4f),
                    ) { Text("I'M RESPONDING", fontWeight = FontWeight.Bold) }

                    else -> Button(
                        onClick = viewModel::resolve,
                        colors = ButtonDefaults.buttonColors(containerColor = Green),
                        modifier = Modifier.weight(1.4f),
                    ) { Text("RESOLVE", fontWeight = FontWeight.Bold) }
                }
            }
        }
    }
}

@Composable
private fun GuidancePlaceholder(state: IncidentViewModel.UiState) {
    val guidance = state.guidance
    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Guidance", fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
            com.nearhelp.app.ui.components.ModePill(mode = guidance?.mode ?: "loading")
        }
        guidance?.summary?.takeIf { it.isNotBlank() }?.let {
            Text(it, fontSize = 12.sp, color = Text2)
        }
        if (guidance == null) {
            Text("preparing guidance…", fontSize = 13.sp, color = Text2)
        } else if (guidance.steps.isEmpty()) {
            com.nearhelp.app.ui.components.GlassCard(Modifier.fillMaxWidth()) {
                Text(
                    "Please wait for professional medical help. Call 108 or 112 now.",
                    fontSize = 15.sp,
                    color = Text1,
                )
            }
        } else {
            guidance.steps.forEachIndexed { index, step ->
                com.nearhelp.app.ui.components.GuidanceCard(
                    index = index,
                    text = step.text,
                    source = step.source,
                )
            }
        }
        // Non-dismissible disclaimer on every guidance surface (proposal §13.4).
        com.nearhelp.app.ui.components.DisclaimerStrip(
            text = guidance?.disclaimer?.takeIf { it.isNotBlank() } ?: OFFLINE_DISCLAIMER,
        )
    }
}

@Composable
private fun MapTab(state: IncidentViewModel.UiState) {
    val event = state.event ?: return
    val victim = LatLng(event.lat, event.lon)
    val context = LocalContext.current
    val mapsKeyPresent = remember {
        runCatching {
            val info = context.packageManager.getApplicationInfo(
                context.packageName, PackageManager.GET_META_DATA,
            )
            val key = info.metaData?.getString("com.google.android.geo.API_KEY")
            !key.isNullOrBlank() && key != "MISSING_MAPS_KEY"
        }.getOrDefault(false)
    }

    // Nearest live responder → straight-line distance + walking ETA
    // (improvements.md §2.5 — no Directions API on the critical path).
    val nearest = state.livePositions.values.minOfOrNull {
        distanceMeters(it.lat, it.lon, event.lat, event.lon)
    }
    val etaMinutes = nearest?.let { ((it / 1.4) / 60).toInt().coerceAtLeast(1) }

    if (mapsKeyPresent) {
        val camera = rememberCameraPositionState {
            position = CameraPosition.fromLatLngZoom(victim, 15f)
        }
        GoogleMap(
            modifier = Modifier.fillMaxSize(),
            cameraPositionState = camera,
            uiSettings = MapUiSettings(zoomControlsEnabled = true),
        ) {
            Marker(
                state = rememberMarkerState(position = victim),
                title = "Emergency",
            )
            state.livePositions.forEach { (id, position) ->
                androidx.compose.runtime.key(id) {
                    val latLng = LatLng(position.lat, position.lon)
                    val markerState = rememberMarkerState(position = latLng)
                    // rememberMarkerState pins the initial position — live
                    // updates must be applied explicitly.
                    LaunchedEffect(latLng) { markerState.position = latLng }
                    Marker(
                        state = markerState,
                        title = position.name,
                        snippet = "responding",
                    )
                }
            }
        }
        LiveEtaCard(nearest, etaMinutes)
    } else {
        Column(
            Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(20.dp)
        ) {
            GlassCard(Modifier.fillMaxWidth()) {
                Text("Live tracking", fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(8.dp))
                if (nearest != null) {
                    Text(
                        "nearest responder: ${"%.0f".format(nearest)} m away " +
                            "(~$etaMinutes min on foot)",
                        fontSize = 14.sp,
                        color = Text1,
                    )
                } else {
                    Text("waiting for responder locations…", fontSize = 14.sp, color = Text2)
                }
                state.livePositions.forEach { (_, p) ->
                    val d = distanceMeters(p.lat, p.lon, event.lat, event.lon)
                    Text(
                        "• ${p.name} — ${"%.0f".format(d)} m",
                        fontSize = 12.sp,
                        color = Text2,
                        modifier = Modifier.padding(top = 6.dp),
                    )
                }
                Text(
                    "add a Maps API key for the full map (README)",
                    fontSize = 10.sp,
                    color = Text3,
                    modifier = Modifier.padding(top = 8.dp),
                )
            }
        }
    }
}

@Composable
private fun LiveEtaCard(nearest: Double?, etaMinutes: Int?) {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.BottomCenter) {
        Surface(
            shape = MaterialTheme.shapes.large,
            color = Color(0xE6FFFFFF),
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
        ) {
            Text(
                text = if (nearest != null) {
                    "nearest responder ${"%.0f".format(nearest)} m · ~$etaMinutes min"
                } else {
                    "waiting for responder locations…"
                },
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
                color = Text1,
                modifier = Modifier.padding(14.dp),
            )
        }
    }
}

@Composable
private fun ChatTab(state: IncidentViewModel.UiState, onSend: (String) -> Unit) {
    var input by remember { mutableStateOf("") }
    val listState = rememberLazyListState()

    LaunchedEffect(state.chat.size) {
        if (state.chat.isNotEmpty()) listState.animateScrollToItem(state.chat.size - 1)
    }

    Column(Modifier.fillMaxSize()) {
        LazyColumn(
            state = listState,
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            items(state.chat, key = { it.id }) { message ->
                ChatBubble(message)
            }
        }
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp)
                .imePadding(),
        ) {
            OutlinedTextField(
                value = input,
                onValueChange = { input = it },
                placeholder = { Text("message…", fontSize = 13.sp) },
                modifier = Modifier.weight(1f),
                maxLines = 3,
            )
            Spacer(Modifier.width(8.dp))
            Button(
                onClick = {
                    onSend(input)
                    input = ""
                },
                enabled = input.isNotBlank() && state.wsConnected,
            ) { Text("SEND") }
        }
    }
}

@Composable
private fun ChatBubble(message: IncidentViewModel.ChatEntry) {
    Box(
        Modifier.fillMaxWidth(),
        contentAlignment = if (message.mine) Alignment.CenterEnd else Alignment.CenterStart,
    ) {
        Surface(
            shape = MaterialTheme.shapes.medium,
            color = if (message.mine) Blue.copy(alpha = 0.18f) else Color(0xCCFFFFFF),
            modifier = Modifier.width(260.dp),
        ) {
            Column(Modifier.padding(10.dp)) {
                Text(
                    text = if (message.mine) "you" else message.senderName,
                    fontSize = 10.sp,
                    color = Text3,
                )
                Text(text = message.text, fontSize = 14.sp, color = Text1)
            }
        }
    }
}

@Composable
private fun TimelineTab(state: IncidentViewModel.UiState) {
    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(20.dp)
    ) {
        Text("Timeline", fontWeight = FontWeight.Bold, color = Text1)
        state.timeline.reversed().forEach { item ->
            val cue = when (item.event_type) {
                "escalation_wave" -> " — search radius expanded"
                "call_services_prompted" -> " — call 108/112 prompted"
                "response_accepted" -> " — responder committed"
                else -> ""
            }
            Row(Modifier.padding(top = 10.dp)) {
                Box(
                    Modifier
                        .size(8.dp)
                        .background(
                            when (item.event_type) {
                                "sos_resolved" -> Green
                                "call_services_prompted" -> Red
                                "escalation_wave" -> Blue
                                else -> Text3
                            },
                            MaterialTheme.shapes.extraSmall,
                        )
                )
                Text(
                    text = "  ${item.event_type.replace('_', ' ')}$cue",
                    fontSize = 13.sp,
                    color = Text2,
                )
            }
        }
    }
}
