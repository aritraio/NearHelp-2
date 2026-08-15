package com.nearhelp.app.ui.screens

import android.content.Context
import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.nearhelp.app.data.api.ApiService
import com.nearhelp.app.data.api.ResolveRequest
import com.nearhelp.app.data.api.SosOut
import com.nearhelp.app.data.api.TimelineEventOut
import com.nearhelp.app.data.ws.SosSocket
import com.nearhelp.app.service.ResponderLocationService
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import javax.inject.Inject

const val OFFLINE_DISCLAIMER =
    "Offline first-aid protocols for reference only — NOT medical advice. " +
        "Always call emergency services (108/112) for serious emergencies."

/**
 * Incident view, real-time edition (Phase 4): WebSocket channel with the
 * REST poll as fallback (todos.md §4). Live positions, chat, and server
 * pushes (accept/arrive/escalation/resolve) arrive over the socket; polling
 * slows to 10 s while connected and runs at 3 s otherwise.
 */
@HiltViewModel
class IncidentViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    private val api: ApiService,
    private val socket: SosSocket,
    private val json: Json,
    @ApplicationContext private val appContext: Context,
) : ViewModel() {

    private val sosId: String = checkNotNull(savedStateHandle["sosId"])

    data class LivePosition(val name: String, val lat: Double, val lon: Double)

    data class ChatEntry(
        val id: String,
        val senderId: String?,
        val senderName: String,
        val text: String,
        val mine: Boolean,
    )

    data class UiState(
        val event: SosOut? = null,
        val timeline: List<TimelineEventOut> = emptyList(),
        val myUserId: String? = null,
        val iAmResponder: Boolean = false,
        val iAmNotifiedResponder: Boolean = false,
        val iArrived: Boolean = false,
        val livePositions: Map<String, LivePosition> = emptyMap(),
        val chat: List<ChatEntry> = emptyList(),
        val guidance: com.nearhelp.app.data.api.GuidanceOut? = null,
        val guidanceFromOfflineCache: Boolean = false,
        val wsConnected: Boolean = false,
        val callPrompt: Boolean = false,
        val error: String? = null,
    )

    private val _state = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = _state

    init {
        viewModelScope.launch {
            _state.value = _state.value.copy(
                myUserId = runCatching { api.me().id }.getOrNull(),
            )
            runCatching { api.ack(sosId) }

            // Chat history first, then the live channel.
            runCatching { api.messages(sosId) }.onSuccess { history ->
                val me = _state.value.myUserId
                _state.value = _state.value.copy(
                    chat = history.map {
                        ChatEntry(
                            id = it.id,
                            senderId = it.sender_id,
                            senderName = it.sender_name,
                            text = it.text,
                            mine = it.sender_id != null && it.sender_id == me,
                        )
                    }
                )
            }

            socket.connect(sosId)
            loadGuidance() // server guidance if ready; offline cache otherwise
            launch {
                socket.state.collect { s ->
                    _state.value = _state.value.copy(wsConnected = s == SosSocket.State.CONNECTED)
                }
            }
            launch {
                socket.events.collect { handleEvent(it) }            }

            while (isActive) {
                refresh()
                delay(if (_state.value.wsConnected) 10_000 else 3_000)
            }
        }
    }

    private fun handleEvent(message: JsonObject) {
        when (message["type"]?.jsonPrimitive?.content) {
            "responder_update" -> {
                val id = message["responder_id"]?.jsonPrimitive?.content ?: return
                val lat = message["lat"]?.jsonPrimitive?.doubleOrNull ?: return
                val lon = message["lon"]?.jsonPrimitive?.doubleOrNull ?: return
                val name = message["name"]?.jsonPrimitive?.content ?: "Responder"
                _state.value = _state.value.copy(
                    livePositions = _state.value.livePositions + (id to LivePosition(name, lat, lon))
                )
            }
            "new_message" -> {
                val id = message["id"]?.jsonPrimitive?.content ?: return
                if (_state.value.chat.any { it.id == id }) return
                val entry = ChatEntry(
                    id = id,
                    senderId = message["sender_id"]?.jsonPrimitive?.content,
                    senderName = message["sender_name"]?.jsonPrimitive?.content ?: "?",
                    text = message["text"]?.jsonPrimitive?.content ?: "",
                    mine = message["sender_id"]?.jsonPrimitive?.content == _state.value.myUserId,
                )
                _state.value = _state.value.copy(chat = _state.value.chat + entry)
            }
            "call_services_prompt" -> _state.value = _state.value.copy(callPrompt = true)
            "ai_guidance" -> loadGuidance()
            "responder_accepted", "responder_arrived", "sos_resolved",
            "sos_expired", "escalation_wave" -> refresh()
        }
    }

    /** Server guidance when reachable; bundled offline protocols otherwise
     *  (improvements.md §1.2 rung 3 — guidance must survive a dead network). */
    fun loadGuidance() {
        viewModelScope.launch {
            runCatching { api.guidance(sosId) }
                .onSuccess { fetched ->
                    if (fetched.steps.isNotEmpty()) {
                        _state.value = _state.value.copy(
                            guidance = fetched, guidanceFromOfflineCache = false,
                        )
                    }
                }
                .onFailure { serveOfflineGuidance() }
            if (_state.value.guidance == null) serveOfflineGuidance()
        }
    }

    private fun serveOfflineGuidance() {
        val event = _state.value.event ?: return
        runCatching {
            val text = appContext.assets.open("offline_protocols.json")
                .bufferedReader().readText()
            val doc = json.parseToJsonElement(text).jsonObject
            val procedures = doc["procedures"]!!.jsonArray
            val crisis = event.crisis_type ?: "other"
            val steps = mutableListOf<com.nearhelp.app.data.api.GuidanceStep>()
            for (element in procedures) {
                val procedure = element.jsonObject
                val matches = procedure["crisis_type"]?.jsonPrimitive?.content == crisis ||
                    crisis == "other"
                if (!matches) continue
                val name = procedure["procedure_name"]!!.jsonPrimitive.content
                val source = procedure["source"]!!.jsonPrimitive.content
                procedure["steps"]!!.jsonArray.forEachIndexed { index, step ->
                    steps += com.nearhelp.app.data.api.GuidanceStep(
                        text = step.jsonPrimitive.content,
                        source = "$source — $name, step ${index + 1}",
                    )
                }
                if (steps.isNotEmpty()) break // first matching procedure
            }
            if (steps.isNotEmpty()) {
                _state.value = _state.value.copy(
                    guidance = com.nearhelp.app.data.api.GuidanceOut(
                        sos_id = sosId,
                        mode = "offline_cache",
                        steps = steps.take(8),
                        summary = "Bundled offline protocol — no network required.",
                        disclaimer = OFFLINE_DISCLAIMER,
                    ),
                    guidanceFromOfflineCache = true,
                )
            }
        }
    }

    private fun refresh() {
        viewModelScope.launch {
            val me = _state.value.myUserId
            runCatching { api.sos(sosId) }
                .onSuccess { event ->
                    val mine = event.responders.filter { it.responder_id == me }
                    _state.value = _state.value.copy(
                        event = event,
                        error = null,
                        iAmResponder = mine.any { it.status == "accepted" || it.status == "arrived" },
                        iAmNotifiedResponder = mine.isNotEmpty(),
                        iArrived = mine.any { it.status == "arrived" },
                    )
                }
            runCatching { api.timeline(sosId) }
                .onSuccess { _state.value = _state.value.copy(timeline = it) }
        }
    }

    fun respond(onDone: (Boolean) -> Unit = {}) {
        viewModelScope.launch {
            runCatching { api.respond(sosId) }
                .onSuccess {
                    _state.value = _state.value.copy(iAmResponder = true)
                    _state.value.event?.let { event ->
                        ResponderLocationService.start(
                            appContext, sosId, event.lat, event.lon,
                        )
                    }
                    onDone(true)
                }
                .onFailure {
                    _state.value = _state.value.copy(error = "could not respond")
                    onDone(false)
                }
        }
    }

    fun arrive() {
        viewModelScope.launch {
            runCatching { api.arrive(sosId) }
                .onSuccess {
                    _state.value = _state.value.copy(iArrived = true)
                    ResponderLocationService.stop(appContext)
                }
                .onFailure { _state.value = _state.value.copy(error = "could not check in") }
        }
    }

    fun resolve() {
        viewModelScope.launch {
            runCatching { api.resolve(sosId, ResolveRequest(outcome = null)) }
                .onSuccess {
                    ResponderLocationService.stop(appContext)
                    _state.value = _state.value.copy(event = it)
                }
                .onFailure { _state.value = _state.value.copy(error = "could not resolve") }
        }
    }

    fun sendMessage(text: String) {
        val trimmed = text.trim()
        if (trimmed.isEmpty()) return
        if (!state.value.wsConnected) {
            _state.value = _state.value.copy(error = "chat offline — reconnecting")
            return
        }
        socket.sendMessage(trimmed)
    }

    fun dismissError() {
        _state.value = _state.value.copy(error = null)
    }

    override fun onCleared() {
        socket.disconnect()
        super.onCleared()
    }
}
