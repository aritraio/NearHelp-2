package com.nearhelp.app.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.IBinder
import com.nearhelp.app.data.location.LocationClient
import com.nearhelp.app.data.ws.SosSocket
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import javax.inject.Inject
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Streams the accepted responder's position over the SOS channel
 * (todos.md §4): adaptive intervals — 3 s within 500 m of the victim,
 * 12 s beyond (battery vs. smoothness, improvements.md §2.7).
 */
@AndroidEntryPoint
class ResponderLocationService : Service() {

    @Inject lateinit var locationClient: LocationClient

    @Inject lateinit var socket: SosSocket

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val sosId = intent?.getStringExtra(EXTRA_SOS_ID)
        val targetLat = intent?.getDoubleExtra(EXTRA_TARGET_LAT, Double.NaN) ?: Double.NaN
        val targetLon = intent?.getDoubleExtra(EXTRA_TARGET_LON, Double.NaN) ?: Double.NaN
        if (sosId == null || targetLat.isNaN() || targetLon.isNaN()) {
            stopSelf()
            return START_NOT_STICKY
        }

        startForeground(NOTIFICATION_ID, buildNotification())
        scope.launch {
            while (isActive) {
                val position = runCatching { locationClient.current() }.getOrNull()
                if (position != null) {
                    socket.sendLocation(position.lat, position.lon)
                    val distance = distanceMeters(
                        position.lat, position.lon, targetLat, targetLon,
                    )
                    delay(if (distance < 500) 3_000 else 12_000)
                } else {
                    delay(10_000)
                }
            }
        }
        return START_STICKY
    }

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }

    private fun buildNotification(): Notification {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.createNotificationChannel(
            NotificationChannel(
                CHANNEL_ID,
                "Responder tracking",
                NotificationManager.IMPORTANCE_LOW,
            ).apply { description = "Location sharing while responding" }
        )
        return androidx.core.app.NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .setContentTitle("NearHelp — responding")
            .setContentText("Sharing your location with the emergency channel")
            .setOngoing(true)
            .build()
    }

    companion object {
        private const val CHANNEL_ID = "responder_tracking"
        private const val NOTIFICATION_ID = 42
        private const val EXTRA_SOS_ID = "sos_id"
        private const val EXTRA_TARGET_LAT = "target_lat"
        private const val EXTRA_TARGET_LON = "target_lon"

        fun start(context: Context, sosId: String, targetLat: Double, targetLon: Double) {
            val intent = Intent(context, ResponderLocationService::class.java)
                .putExtra(EXTRA_SOS_ID, sosId)
                .putExtra(EXTRA_TARGET_LAT, targetLat)
                .putExtra(EXTRA_TARGET_LON, targetLon)
            runCatching { context.startForegroundService(intent) }
        }

        fun stop(context: Context) {
            runCatching { context.stopService(Intent(context, ResponderLocationService::class.java)) }
        }
    }
}

/** Haversine distance in meters — shared with the map's ETA math. */
fun distanceMeters(lat1: Double, lon1: Double, lat2: Double, lon2: Double): Double {
    val r = 6_371_000.0
    val dLat = Math.toRadians(lat2 - lat1)
    val dLon = Math.toRadians(lon2 - lon1)
    val a = sin(dLat / 2) * sin(dLat / 2) +
        cos(Math.toRadians(lat1)) * cos(Math.toRadians(lat2)) * sin(dLon / 2) * sin(dLon / 2)
    return r * 2 * atan2(sqrt(a), sqrt(1 - a))
}
