package com.nearhelp.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

// Calm (mint) scheme per DESIGN.md — the incident/respond tinted backgrounds
// arrive with the state-driven scaffold in Phase 3; dark theme in Phase 4.
private val CalmColors = lightColorScheme(
    primary = Green,
    onPrimary = Text1,
    secondary = GreenDeep,
    onSecondary = SurfaceGlassHi,
    background = BgCalm,
    onBackground = Text1,
    surface = SurfaceGlassHi,
    onSurface = Text1,
    error = Red,
    onError = SurfaceGlassHi,
)

@Composable
fun NearHelpTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = CalmColors,
        typography = NearHelpTypography,
        shapes = NearHelpShapes,
        content = content,
    )
}
