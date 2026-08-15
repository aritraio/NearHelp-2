package com.nearhelp.app.ui.theme

import androidx.compose.ui.graphics.Color

// Design tokens from DESIGN.md §2.1 — the ONLY place raw colors may live.
// NOTE: DESIGN.md names the glass surfaces "Surface"/"SurfaceHi"; here they are
// SurfaceGlass/SurfaceGlassHi to avoid clashing with the Material3 Surface composable.

// Backgrounds
val BgCalm = Color(0xFFE6F7EF) // mint — normal state
val BgCalmDeep = Color(0xFFCDEFDD) // gradient top
val BgNeutral = Color(0xFFF0F0F0) // panels/forms
val BgIncident = Color(0xFFFDECEA) // red-tinted — active SOS (victim)
val BgRespond = Color(0xFFE8F0FE) // blue-tinted — responder active

// Brand / semantic (fills & icons only; text uses the -Deep variants for WCAG AA)
val Green = Color(0xFF4CAF50)
val GreenDeep = Color(0xFF2E7D32)
val Red = Color(0xFFF44336)
val RedDeep = Color(0xFFD32F2F)
val Blue = Color(0xFF2196F3)

// Category hues (grid tile, chip, marker, notification — consistent everywhere)
val CatMedical = Blue
val CatFire = Color(0xFFFF9800)
val CatGas = Color(0xFFFF9800)
val CatAccident = Blue
val CatPolice = Color(0xFF3F51B5)
val CatDisaster = Color(0xFF795548)
val CatPower = Color(0xFFFFC107)
val CatOther = Color(0xFF9E9E9E)

// Surfaces & text
val SurfaceGlass = Color(0xCCFFFFFF) // white @ 80% — glass cards
val SurfaceGlassHi = Color(0xE6FFFFFF) // white @ 90% — inputs, address card
val Text1 = Color(0xFF111111)
val Text2 = Color(0xFF6B6B6B)
val Text3 = Color(0xFF9A9A9A)
