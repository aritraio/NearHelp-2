package com.nearhelp.app.data.push

import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow

/**
 * In-process bridge from the FCM service to the UI (and to token upload).
 * The MessagingService emits here; MainActivity collects and navigates to the
 * alert screen. Keeps push handling testable and UI-free.
 */
object PushRouter {

    data class SosAlert(
        val sosId: String,
        val crisisType: String?,
        val severity: Int?,
        val isDrill: Boolean,
        val lat: Double?,
        val lon: Double?,
    )

    data class CallServicesPrompt(val sosId: String)

    /** Emitted for every sos_alert data message (foreground routing). */
    val alerts = MutableSharedFlow<SosAlert>(extra = 1)

    /** Wave-3 cue: victim should call 108/112. */
    val callPrompts = MutableSharedFlow<CallServicesPrompt>(extra = 1)

    /** FCM registration token, refreshed by the service; UI uploads it. */
    val fcmToken = MutableStateFlow<String?>(null)
}
