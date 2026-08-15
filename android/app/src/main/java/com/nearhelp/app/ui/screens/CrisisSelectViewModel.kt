package com.nearhelp.app.ui.screens

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.nearhelp.app.data.api.ApiService
import com.nearhelp.app.data.api.SosCreateRequest
import com.nearhelp.app.data.location.LatLon
import com.nearhelp.app.data.location.LocationClient
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

/**
 * Crisis selection + the 5-second cancel window (todos.md §3.2 AC):
 * arming the countdown generates ONE idempotency key for the whole operation;
 * cancelling before zero never calls the API — no responders get notified.
 */
@HiltViewModel
class CrisisSelectViewModel @Inject constructor(
    private val api: ApiService,
    private val locationClient: LocationClient,
) : ViewModel() {

    data class UiState(
        val location: LatLon? = null,
        val categoryKey: String? = null,
        val description: String = "",
        val isDrill: Boolean = false,
        val countdown: Int? = null,
        val busy: Boolean = false,
        val error: String? = null,
        val createdSosId: String? = null,
    )

    private val _state = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = _state

    private var idempotencyKey: String = ""

    init {
        viewModelScope.launch {
            _state.value = _state.value.copy(
                location = runCatching { locationClient.current() }.getOrNull()
            )
        }
    }

    fun selectCategory(key: String?) {
        _state.value = _state.value.copy(categoryKey = _state.value.categoryKey?.takeIf { it != key } ?: key)
    }

    fun setDescription(value: String) {
        _state.value = _state.value.copy(description = value)
    }

    fun setDrill(value: Boolean) {
        _state.value = _state.value.copy(isDrill = value)
    }

    /** Arms the 5-second cancel window (single idempotency key per attempt). */
    fun armCountdown() {
        idempotencyKey = UUID.randomUUID().toString().replace("-", "").substring(0, 32)
        _state.value = _state.value.copy(countdown = 5)
        viewModelScope.launch {
            while ((_state.value.countdown ?: 0) > 0) {
                delay(1_000)
                _state.value = _state.value.copy(countdown = (_state.value.countdown ?: 1) - 1)
            }
            if (_state.value.countdown == 0) commit()
        }
    }

    fun cancel() {
        _state.value = _state.value.copy(countdown = null, error = null)
    }

    private fun commit() {
        val current = _state.value
        val location = current.location ?: run {
            _state.value = current.copy(countdown = null, error = "no location — cannot send")
            return
        }
        _state.value = current.copy(busy = true)
        viewModelScope.launch {
            runCatching {
                api.createSos(
                    idempotencyKey,
                    SosCreateRequest(
                        description = current.description.ifBlank { null },
                        lat = location.lat,
                        lon = location.lon,
                        crisis_type = current.categoryKey,
                        is_drill = current.isDrill,
                    ),
                )
            }.onSuccess { event ->
                _state.value = _state.value.copy(busy = false, createdSosId = event.id)
            }.onFailure {
                _state.value = _state.value.copy(
                    busy = false,
                    countdown = null,
                    error = "could not send — check connection and retry",
                )
            }
        }
    }
}
