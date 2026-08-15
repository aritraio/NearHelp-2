package com.nearhelp.app.data.ws

import com.nearhelp.app.BuildConfig
import com.nearhelp.app.data.api.ApiService
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import javax.inject.Inject
import javax.inject.Singleton

/**
 * The SOS event channel client (Architecture.md §7):
 *  - fetches a one-time ticket over REST, then opens the WS;
 *  - auto-reconnects up to 3 times with backoff;
 *  - after the 3rd failure stops trying and flips [state] to FAILED — the
 *    IncidentViewModel keeps its REST polling as the fallback path.
 */
@Singleton
class SosSocket @Inject constructor(
    private val okHttp: OkHttpClient,
    private val api: ApiService,
    private val json: Json,
) {

    enum class State { IDLE, CONNECTING, CONNECTED, FAILED }

    private val _events = MutableSharedFlow<JsonObject>(extra = 32)
    val events: SharedFlow<JsonObject> = _events

    private val _state = MutableStateFlow(State.IDLE)
    val state: StateFlow<State> = _state

    private var scope: CoroutineScope? = null
    private var webSocket: WebSocket? = null
    private var sosId: String? = null
    private var attempts = 0

    fun connect(targetSosId: String) {
        if (_state.value == State.CONNECTED || sosId == targetSosId) return
        disconnect()
        sosId = targetSosId
        attempts = 0
        val newScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
        scope = newScope
        newScope.launch { open() }
    }

    fun disconnect() {
        webSocket?.close(1000, "bye")
        webSocket = null
        scope?.cancel()
        scope = null
        sosId = null
        _state.value = State.IDLE
    }

    fun sendLocation(lat: Double, lon: Double) {
        sendJson("""{"type":"location_update","lat":$lat,"lon":$lon}""")
    }

    fun sendMessage(text: String, language: String = "en") {
        val escaped = text.replace("\\", "\\\\").replace("\"", "\\\"")
        sendJson("""{"type":"send_message","text":"$escaped","language":"$language"}""")
    }

    private fun sendJson(payload: String) {
        webSocket?.send(payload)
    }

    private suspend fun open() {
        val target = sosId ?: return
        _state.value = State.CONNECTING
        val ticket = runCatching { api.wsTicket(target).ticket }.getOrNull() ?: run {
            retryOrGiveUp()
            return
        }
        val wsUrl = BuildConfig.BASE_URL
            .replace("http://", "ws://")
            .replace("https://", "wss://") + "api/ws/$target?ticket=$ticket"

        webSocket = okHttp.newWebSocket(
            Request.Builder().url(wsUrl).build(),
            object : WebSocketListener() {
                override fun onOpen(webSocket: WebSocket, response: Response) {
                    attempts = 0
                    _state.value = State.CONNECTED
                }

                override fun onMessage(webSocket: WebSocket, text: String) {
                    runCatching { json.parseToJsonElement(text) }
                        .getOrNull()
                        ?.let { it as? JsonObject }
                        ?.let { _events.tryEmit(it) }
                }

                override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                    scope?.launch { retryOrGiveUp() }
                }
            },
        )
    }

    private suspend fun retryOrGiveUp() {
        attempts += 1
        if (attempts > 3) {
            _state.value = State.FAILED
            return
        }
        _state.value = State.CONNECTING
        delay(attempts * 1_500L)
        if (sosId != null) open()
    }
}
