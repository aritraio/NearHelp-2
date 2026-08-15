package com.nearhelp.app.data.api

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.PUT
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

/** Backend REST API (Architecture.md §3.2). Base URL comes from BuildConfig. */
interface ApiService {

    // --- Auth -----------------------------------------------------------------

    @POST("api/auth/register")
    suspend fun register(@Body body: RegisterRequest): AuthResponse

    @POST("api/auth/login")
    suspend fun login(@Body body: LoginRequest): AuthResponse

    @POST("api/auth/refresh")
    suspend fun refresh(@Body body: RefreshRequest): AuthResponse

    // --- Profile ---------------------------------------------------------------

    @GET("api/users/me")
    suspend fun me(): UserOut

    @PUT("api/users/me")
    suspend fun updateMe(@Body body: Map<String, String>): UserOut

    @PUT("api/users/me/location")
    suspend fun updateLocation(@Body body: LocationUpdateRequest): retrofit2.Response<Unit>

    @POST("api/users/me/fcm-token")
    suspend fun registerFcmToken(@Body body: FcmTokenRequest): retrofit2.Response<Unit>

    @GET("api/users/me/skills")
    suspend fun mySkills(): List<SkillVerificationOut>

    @POST("api/users/me/skills")
    suspend fun claimSkill(@Query("skill_type") skillType: String): SkillVerificationOut

    // --- SOS -------------------------------------------------------------------

    @GET("api/sos/nearby-count")
    suspend fun nearbyCount(
        @Query("lat") lat: Double,
        @Query("lon") lon: Double,
        @Query("radius_m") radiusM: Int = 2000,
    ): NearbyCount

    @POST("api/sos/create")
    suspend fun createSos(
        @Header("Idempotency-Key") idempotencyKey: String,
        @Body body: SosCreateRequest,
    ): SosOut

    @GET("api/sos/active")
    suspend fun activeEvents(): List<SosOut>

    @GET("api/sos/{sos_id}")
    suspend fun sos(@Path("sos_id") sosId: String): SosOut

    @POST("api/sos/{sos_id}/respond")
    suspend fun respond(@Path("sos_id") sosId: String): RespondOut

    @POST("api/sos/{sos_id}/ack")
    suspend fun ack(@Path("sos_id") sosId: String): RespondOut

    @POST("api/sos/{sos_id}/arrive")
    suspend fun arrive(@Path("sos_id") sosId: String): RespondOut

    @GET("api/sos/{sos_id}/ws-ticket")
    suspend fun wsTicket(@Path("sos_id") sosId: String): WsTicket

    @GET("api/sos/{sos_id}/messages")
    suspend fun messages(@Path("sos_id") sosId: String): List<ChatMessageOut>

    @GET("api/sos/{sos_id}/guidance")
    suspend fun guidance(@Path("sos_id") sosId: String): GuidanceOut

    @PUT("api/sos/{sos_id}/resolve")
    suspend fun resolve(
        @Path("sos_id") sosId: String,
        @Body body: ResolveRequest = ResolveRequest(outcome = null),
    ): SosOut

    @GET("api/sos/{sos_id}/timeline")
    suspend fun timeline(@Path("sos_id") sosId: String): List<TimelineEventOut>
}
