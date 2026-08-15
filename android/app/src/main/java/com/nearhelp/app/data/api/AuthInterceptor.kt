package com.nearhelp.app.data.api

import okhttp3.Interceptor
import okhttp3.Response
import java.util.UUID

/**
 * Request hygiene per Architecture.md §10: every mutating request carries an
 * Idempotency-Key so retries on flaky mobile networks can never duplicate an
 * SOS. Bearer-token attach lands in Phase 1 together with DataStore sessions.
 */
class AuthInterceptor : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        val builder = request.newBuilder()
        if (request.method == "POST" || request.method == "PUT") {
            builder.header("Idempotency-Key", UUID.randomUUID().toString())
        }
        return chain.proceed(builder.build())
    }
}
