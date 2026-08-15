package com.nearhelp.app.ui.screens

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.nearhelp.app.data.api.ApiService
import com.nearhelp.app.data.api.LoginRequest
import com.nearhelp.app.data.api.RegisterRequest
import com.nearhelp.app.data.auth.SessionStore
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import retrofit2.HttpException
import javax.inject.Inject

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val api: ApiService,
    private val sessionStore: SessionStore,
) : ViewModel() {

    data class UiState(
        val busy: Boolean = false,
        val error: String? = null,
        val loggedIn: Boolean = false,
    )

    private val _state = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = _state

    fun login(email: String, password: String) = submit {
        val response = api.login(LoginRequest(email.trim().lowercase(), password))
        sessionStore.saveTokens(response.access_token, response.refresh_token)
    }

    fun register(email: String, password: String, name: String) = submit {
        val response = api.register(
            RegisterRequest(email.trim().lowercase(), password, name.trim())
        )
        sessionStore.saveTokens(response.access_token, response.refresh_token)
    }

    private fun submit(block: suspend () -> Unit) {
        viewModelScope.launch {
            _state.value = UiState(busy = true)
            runCatching { block() }
                .onSuccess { _state.value = UiState(loggedIn = true) }
                .onFailure { failure ->
                    _state.value = UiState(error = failure.toMessage())
                }
        }
    }

    private fun Throwable.toMessage(): String = when (this) {
        is HttpException -> when (code()) {
            401 -> "Invalid email or password"
            409 -> "An account with this email already exists"
            429 -> "Too many attempts — wait a minute"
            else -> "Server error ($code)"
        }
        else -> "Network error — is the backend reachable?"
    }
}
