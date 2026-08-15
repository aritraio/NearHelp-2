package com.nearhelp.app.ui.screens

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.nearhelp.app.data.api.ApiService
import com.nearhelp.app.data.api.ResolveRequest
import com.nearhelp.app.data.api.SosOut
import com.nearhelp.app.data.api.TimelineEventOut
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * Victim/responder incident view: polls the event every 3 s (REST fallback
 * until the Phase 4 WebSocket lands), acknowledges push delivery, accepts or
 * resolves. Live map + chat arrive in Phase 4 (todos.md §4).
 */
@HiltViewModel
class IncidentViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    private val api: ApiService,
) : ViewModel() {

    private val sosId: String = checkNotNull(savedStateHandle["sosId"])

    data class UiState(
        val event: SosOut? = null,
        val timeline: List<TimelineEventOut> = emptyList(),
        val myUserId: String? = null,
        val iAmResponder: Boolean = false,
        val iAmNotifiedResponder: Boolean = false,
        val error: String? = null,
    )

    private val _state = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = _state

    init {
        viewModelScope.launch {
            _state.value = _state.value.copy(
                myUserId = runCatching { api.me().id }.getOrNull(),
            )
            // Acknowledge push delivery immediately (honest metrics, §8).
            runCatching { api.ack(sosId) }
            while (isActive) {
                refresh()
                delay(3_000)
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
                        iAmResponder = mine.any { it.status == "accepted" },
                        iAmNotifiedResponder = mine.isNotEmpty(),
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
                    onDone(true)
                }
                .onFailure {
                    _state.value = _state.value.copy(error = "could not respond")
                    onDone(false)
                }
        }
    }

    fun resolve() {
        viewModelScope.launch {
            runCatching { api.resolve(sosId, ResolveRequest(outcome = null)) }
                .onSuccess { _state.value = _state.value.copy(event = it) }
                .onFailure { _state.value = _state.value.copy(error = "could not resolve") }
        }
    }
}
