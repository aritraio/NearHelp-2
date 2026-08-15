package com.nearhelp.app.data.location

import android.annotation.SuppressLint
import android.content.Context
import android.location.LocationManager
import android.os.Looper
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.nearhelp.app.data.auth.SessionStore
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import java.util.concurrent.atomic.AtomicInteger
import javax.inject.Inject
import javax.inject.Singleton

data class LatLon(val lat: Double, val lon: Double) {
    fun format(): String =
        "${"%.4f".format(Math.abs(lat))}° ${if (lat >= 0) "N" else "S"}  " +
            "${"%.4f".format(Math.abs(lon))}° ${if (lon >= 0) "E" else "W"}"
}

/**
 * Location access with the fake-GPS demo route bolted on (improvements.md §5):
 * when demo mode is enabled the client ignores the real GPS and walks a
 * scripted approach toward the Salt Lake reference point — moving responder
 * pins without anyone jogging down a corridor.
 */
@Singleton
class LocationClient @Inject constructor(
    @ApplicationContext private val context: Context,
    private val sessionStore: SessionStore,
) {

    /** Demo target: Salt Lake Sector V (matches the backend test fixture). */
    val demoTarget = LatLon(22.5726, 88.3639)

    private val demoTick = AtomicInteger((System.currentTimeMillis() / 5_000L).toInt())

    suspend fun current(): LatLon {
        if (sessionStore.demoRouteEnabled.first()) return demoPosition()
        return realPosition() ?: demoTarget
    }

    fun updates(intervalMs: Long = 5_000): Flow<LatLon> = callbackFlow {
        if (sessionStore.demoRouteEnabled.first()) {
            val job = launch {
                while (true) {
                    trySend(demoPosition())
                    delay(intervalMs)
                }
            }
            awaitClose { job.cancel() }
        } else {
            val provider = LocationServices.getFusedLocationProviderClient(context)
            val request = LocationRequest.Builder(
                Priority.PRIORITY_BALANCED_POWER_ACCURACY,
                intervalMs,
            ).build()
            val callback = object : LocationCallback() {
                override fun onLocationResult(result: LocationResult) {
                    result.lastLocation?.let {
                        trySend(LatLon(it.latitude, it.longitude))
                    }
                }
            }
            provider.requestLocationUpdates(request, callback, Looper.getMainLooper())
            awaitClose { provider.removeLocationUpdates(callback) }
        }
    }

    @SuppressLint("MissingPermission")
    private suspend fun realPosition(): LatLon? =
        suspendCancellableCoroutine { cont ->
            val provider = LocationServices.getFusedLocationProviderClient(context)
            provider.getCurrentLocation(Priority.PRIORITY_BALANCED_POWER_ACCURACY, null)
                .addOnSuccessListener { location ->
                    if (cont.isActive) {
                        cont.resumeWith(
                            Result.success(location?.let { LatLon(it.latitude, it.longitude) })
                        )
                    }
                }
                .addOnFailureListener {
                    if (cont.isActive) cont.resumeWith(Result.success(null))
                }
        }

    /**
     * Scripted approach: starts ~800 m north of the target and closes ~15 m
     * per call, looping forever. Deterministic enough to demo live tracking.
     */
    private fun demoPosition(): LatLon {
        val calls = demoTick.incrementAndGet()
        val remaining = 800 - ((calls * 15) % 800)
        return LatLon(demoTarget.lat + remaining / 111_000.0, demoTarget.lon)
    }

    /** Coarse "GPS on?" check used by the readiness indicator. */
    fun isLocationEnabled(): Boolean {
        val lm = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
        return lm.isProviderEnabled(LocationManager.GPS_PROVIDER) ||
            lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER)
    }
}
