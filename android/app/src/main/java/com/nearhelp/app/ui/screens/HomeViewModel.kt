package com.nearhelp.app.ui.screens

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.nearhelp.app.data.api.ApiService
import com.nearhelp.app.data.auth.SessionStore
import com.nearhelp.app.data.location.LatLon
import com.nearhelp.app.data.location.LocationClient
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val api: ApiService,
    private val locationClient: LocationClient,
    val sessionStore: SessionStore,
) : ViewModel() {

    data class UiState(
        val location: LatLon? = null,
        val nearbyResponders: Int? = null,
        val locationPermissionDenied: Boolean = false,
    )

    private val _state = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = _state

    var hasLocationPermission: Boolean = false

    fun refresh() {
        viewModelScope.launch {
            val location = runCatching { locationClient.current() }.getOrNull()
            _state.value = _state.value.copy(
                location = location,
                locationPermissionDenied = !hasLocationPermission,
            )
            if (location != null && hasLocationPermission) {
                // Publish our position so the network can find us too.
                runCatching {
                    api.updateLocation(
                        com.nearhelp.app.data.api.LocationUpdateRequest(location.lat, location.lon)
                    )
                }
                _state.value = _state.value.copy(
                    nearbyResponders = runCatching {
                        api.nearbyCount(location.lat, location.lon).count
                    }.getOrNull(),
                )
            }
        }
    }
}
