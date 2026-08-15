package com.nearhelp.app.ui.screens

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.nearhelp.app.data.api.ApiService
import com.nearhelp.app.data.api.SkillVerificationOut
import com.nearhelp.app.data.api.UserOut
import com.nearhelp.app.data.auth.SessionStore
import com.nearhelp.app.data.location.LocationClient
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ProfileViewModel @Inject constructor(
    private val api: ApiService,
    val sessionStore: SessionStore,
    val locationClient: LocationClient,
) : ViewModel() {

    data class UiState(
        val user: UserOut? = null,
        val skills: List<SkillVerificationOut> = emptyList(),
        val error: String? = null,
    )

    private val _state = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = _state

    val demoRoute = sessionStore.demoRouteEnabled

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            runCatching { api.me() }.onSuccess { _state.value = _state.value.copy(user = it) }
            runCatching { api.mySkills() }
                .onSuccess { _state.value = _state.value.copy(skills = it) }
        }
    }

    fun claimSkill(skillType: String) {
        viewModelScope.launch {
            runCatching { api.claimSkill(skillType) }
                .onSuccess { refresh() }
                .onFailure { _state.value = _state.value.copy(error = "could not claim skill") }
        }
    }

    fun setDemoRoute(enabled: Boolean) {
        viewModelScope.launch { sessionStore.setDemoRoute(enabled) }
    }

    fun logout(onLoggedOut: () -> Unit) {
        viewModelScope.launch {
            sessionStore.clear()
            onLoggedOut()
        }
    }
}
