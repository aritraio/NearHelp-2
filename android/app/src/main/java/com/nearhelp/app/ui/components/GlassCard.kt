package com.nearhelp.app.ui.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.nearhelp.app.ui.theme.SurfaceGlass

/**
 * The universal container (DESIGN.md §3): translucent white surface, 12 dp
 * radius, soft shadow. No hard borders anywhere in the app.
 */
@Composable
fun GlassCard(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    Surface(
        modifier = modifier,
        shape = MaterialTheme.shapes.medium,
        color = SurfaceGlass,
        shadowElevation = 2.dp,
    ) {
        Column(Modifier.padding(16.dp)) { content() }
    }
}
