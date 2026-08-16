package com.nearhelp.app.data.api

import com.nearhelp.app.data.auth.SessionStore
import okhttp3.Interceptor
import okhttp3.Response
import java.util.UUID

/**
 * Request hygiene (Architecture.md §10):
 *  - attaches the Bearer token when we have one (never on /api/auth/ paths);
 *  - ensures every mutating request carries an Idempotency-Key — generated
 *    here ONLY when absent, so the SOS flow can hold one key across retries.
 */
class AuthInterceptor(private val sessionStore: SessionStore) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        val builder = request.newBuilder()

        val isAuthPath = request.url.encodedPath.startsWith("/api/auth/")
        if (!isAuthPath) {
            sessionStore.currentTokensBlocking()?.let {
                builder.header("Authorization", "Bearer ${it.access}")
            }
        }
        if (request.method == "POST" || request.method == "PUT") {
            if (request.header("Idempotency-Key") == null) {
                builder.header("Idempotency-Key", UUID.randomUUID().toString().substring(0, 32))
            }
        }
        return chain.proceed(builder.build())
    }
}
