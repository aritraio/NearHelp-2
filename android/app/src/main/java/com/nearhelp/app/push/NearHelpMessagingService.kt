package com.nearhelp.app.push

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.nearhelp.app.R
import com.nearhelp.app.data.api.ApiService
import com.nearhelp.app.data.api.FcmTokenRequest
import com.nearhelp.app.data.auth.SessionStore
import com.nearhelp.app.data.push.PushRouter
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import javax.inject.Inject

/**
 * SOS data-message receiver (Architecture.md §8): the app renders everything
 * itself — full-screen alert activity, DRILL banners, per-event sounds.
 * Also forwards new FCM tokens to the backend so multi-device registration
 * stays current.
 */
@AndroidEntryPoint
class NearHelpMessagingService : FirebaseMessagingService() {

    @Inject lateinit var api: ApiService

    @Inject lateinit var sessionStore: SessionStore

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onNewToken(token: String) {
        PushRouter.fcmToken.value = token
        scope.launch {
            runCatching {
                val deviceId = sessionStore.deviceId()
                api.registerFcmToken(FcmTokenRequest(device_id = deviceId, fcm_token = token))
            }
        }
    }

    override fun onMessageReceived(message: RemoteMessage) {
        val data = message.data
        when (data["type"]) {
            "sos_alert" -> {
                val alert = PushRouter.SosAlert(
                    sosId = data["sos_id"] ?: return,
                    crisisType = data["crisis_type"],
                    severity = data["severity"]?.toIntOrNull(),
                    isDrill = data["is_drill"] == "true",
                    lat = data["lat"]?.toDoubleOrNull(),
                    lon = data["lon"]?.toDoubleOrNull(),
                )
                PushRouter.alerts.tryEmit(alert)
                showSosNotification(alert)
            }
            "call_services_prompt" -> {
                val sosId = data["sos_id"] ?: return
                PushRouter.callPrompts.tryEmit(PushRouter.CallServicesPrompt(sosId))
            }
        }
    }

    private fun showSosNotification(alert: PushRouter.SosAlert) {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val channel = NotificationChannel(
            CHANNEL_SOS,
            "Emergency alerts",
            NotificationManager.IMPORTANCE_HIGH,
        ).apply { description = "Nearby SOS alerts" }
        manager.createNotificationChannel(channel)

        val drillPrefix = if (alert.isDrill) "[DRILL] " else ""
        val deepLink = Uri.parse(
            "nearhelp://alert/${alert.sosId}?crisis=${alert.crisisType ?: "other"}" +
                "&drill=${alert.isDrill}"
        )
        val intent = Intent(Intent.ACTION_VIEW, deepLink).apply {
            setPackage(packageName)
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val fullScreen = PendingIntent.getActivity(
            this, alert.sosId.hashCode(), intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )

        val notification = NotificationCompat.Builder(this, CHANNEL_SOS)
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentTitle("${drillPrefix}Emergency nearby")
            .setContentText("Someone needs help — tap to respond")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_CALL)
            .setFullScreenIntent(fullScreen, true)
            .setContentIntent(fullScreen)
            .setAutoCancel(true)
            .build()
        manager.notify(alert.sosId.hashCode(), notification)
    }

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }

    private companion object {
        const val CHANNEL_SOS = "sos_alerts"
    }
}
