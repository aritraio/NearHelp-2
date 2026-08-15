package com.nearhelp.app.data.api

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// Backend field names are snake_case (BLUEPRINT.md §4); @SerialName keeps the
// DTOs explicit instead of relying on a naming strategy.

@Serializable
data class RegisterRequest(
    val email: String,
    val password: String,
    val name: String,
    val phone: String? = null,
)

@Serializable
data class LoginRequest(val email: String, val password: String)

@Serializable
data class RefreshRequest(val refresh_token: String)

@Serializable
data class UserOut(
    val id: String,
    val email: String,
    val name: String,
    val phone: String? = null,
    val languages: List<String> = emptyList(),
    val skills: List<SkillEntry> = emptyList(),
    val trust_score: Double = 50.0,
)

@Serializable
data class SkillEntry(
    val skill_type: String,
    val verified: Boolean = false,
)

@Serializable
data class AuthResponse(
    val token_type: String,
    val access_token: String,
    val expires_in: Int,
    val refresh_token: String,
    val user: UserOut,
)

@Serializable
data class LocationUpdateRequest(val lat: Double, val lon: Double)

@Serializable
data class FcmTokenRequest(val device_id: String, val fcm_token: String)

@Serializable
data class SkillVerificationOut(
    val id: String,
    val skill_type: String,
    val status: String,
    val submitted_at: String,
    val has_certificate: Boolean = false,
)

@Serializable
data class SosCreateRequest(
    val description: String? = null,
    val lat: Double,
    val lon: Double,
    val crisis_type: String? = null,
    val is_drill: Boolean = false,
)

@Serializable
data class ResponderOut(
    val responder_id: String,
    val name: String,
    val status: String,
    val eta_seconds: Int? = null,
)

@Serializable
data class SosOut(
    val id: String,
    val status: String,
    val crisis_type: String? = null,
    val severity_score: Int? = null,
    val description: String? = null,
    val lat: Double,
    val lon: Double,
    val radius_m: Int,
    val escalation_wave: Int = 0,
    val is_drill: Boolean = false,
    val created_at: String,
    val resolved_at: String? = null,
    val notified_count: Int = 0,
    val responders: List<ResponderOut> = emptyList(),
)

@Serializable
data class RespondOut(val response_id: String, val status: String)

@Serializable
data class ResolveRequest(val outcome: String? = null)

@Serializable
data class TimelineEventOut(
    val event_type: String,
    val actor_id: String? = null,
    val details: Map<String, String> = emptyMap(),
    val created_at: String,
)

@Serializable
data class NearbyCount(val count: Int)

/** Human-readable error body from FastAPI: {"detail": "..."}. */
@Serializable
data class ApiError(val detail: String? = null)
