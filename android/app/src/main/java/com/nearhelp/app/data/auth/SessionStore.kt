package com.nearhelp.app.data.auth

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.runBlocking
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

private val Context.dataStore by preferencesDataStore("nearhelp_session")

data class SessionTokens(val access: String, val refresh: String)

/**
 * Device-local session state: JWT pair, a stable per-install device id (the
 * multi-device FCM key), and the fake-GPS demo toggle (improvements.md §5).
 */
@Singleton
class SessionStore @Inject constructor(@ApplicationContext private val context: Context) {

    private object Keys {
        val ACCESS = stringPreferencesKey("access_token")
        val REFRESH = stringPreferencesKey("refresh_token")
        val DEVICE = stringPreferencesKey("device_id")
        val DEMO_ROUTE = booleanPreferencesKey("demo_route_enabled")
    }

    val tokens: Flow<SessionTokens?> = context.dataStore.data.map { prefs ->
        val access = prefs[Keys.ACCESS] ?: return@map null
        val refresh = prefs[Keys.REFRESH] ?: return@map null
        SessionTokens(access, refresh)
    }

    val isLoggedIn: Flow<Boolean> = tokens.map { it != null }

    val demoRouteEnabled: Flow<Boolean> = context.dataStore.data.map { it[Keys.DEMO_ROUTE] ?: false }

    suspend fun saveTokens(access: String, refresh: String) {
        context.dataStore.edit {
            it[Keys.ACCESS] = access
            it[Keys.REFRESH] = refresh
        }
    }

    suspend fun clear() {
        context.dataStore.edit {
            it.remove(Keys.ACCESS)
            it.remove(Keys.REFRESH)
        }
    }

    /** Stable per-install id; generated on first use. Runs on OkHttp threads. */
    fun deviceIdBlocking(): String = runBlocking {
        val existing = context.dataStore.data.first()[Keys.DEVICE]
        if (existing != null) return@runBlocking existing
        val id = "device-" + UUID.randomUUID().toString().substring(0, 18)
        context.dataStore.edit { it[Keys.DEVICE] = id }
        id
    }

    suspend fun deviceId(): String = deviceIdBlocking()

    suspend fun setDemoRoute(enabled: Boolean) {
        context.dataStore.edit { it[Keys.DEMO_ROUTE] = enabled }
    }

    /** Interceptor-path accessor (OkHttp threads; blocking is fine there). */
    fun currentTokensBlocking(): SessionTokens? = runBlocking { tokens.first() }
}
