package com.nearhelp.app.data.auth

import com.nearhelp.app.data.api.ApiService
import com.nearhelp.app.data.api.RefreshRequest
import kotlinx.coroutines.runBlocking
import okhttp3.Authenticator
import okhttp3.Request
import okhttp3.Response
import okhttp3.Route
import javax.inject.Inject
import javax.inject.Named
import javax.inject.Singleton

/**
 * Auto-refresh: on a 401 for a request WE authenticated, rotate the refresh
 * token once and retry. Single-flight via @Synchronized so a burst of expiring
 * requests shares one refresh call (Architecture.md §3.2).
 */
@Singleton
class TokenAuthenticator @Inject constructor(
    private val sessionStore: SessionStore,
    @Named("bare") private val bareApi: ApiService,
) : Authenticator {

    @Synchronized
    override fun authenticate(route: Route?, response: Response): Request? {
        // Only retry requests we sent a token on (never login/register).
        if (response.request.header("Authorization") == null) return null
        // One retry max — a second 401 means the new token is bad too.
        if (responseCount(response) >= 2) return null

        val tokens = sessionStore.currentTokensBlocking() ?: return null
        val newAccess = runCatching {
            runBlocking {
                val fresh = bareApi.refresh(RefreshRequest(tokens.refresh))
                sessionStore.saveTokens(fresh.access_token, fresh.refresh_token)
                fresh.access_token
            }
        }.getOrNull() ?: run {
            runBlocking { sessionStore.clear() }
            return null
        }

        return response.request.newBuilder()
            .header("Authorization", "Bearer $newAccess")
            .build()
    }

    private fun responseCount(response: Response): Int {
        var count = 1
        var prior = response.priorResponse
        while (prior != null) {
            count++
            prior = prior.priorResponse
        }
        return count
    }
}
