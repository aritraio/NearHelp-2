package com.nearhelp.app.data.api

import kotlinx.serialization.Serializable
import retrofit2.http.GET

@Serializable
data class HealthResponse(
    val status: String,
    val db: String? = null,
    val env: String? = null,
)

/** Backend REST API (Architecture.md §3.2). Base URL comes from BuildConfig. */
interface ApiService {

    @GET("api/health")
    suspend fun health(): HealthResponse
}
