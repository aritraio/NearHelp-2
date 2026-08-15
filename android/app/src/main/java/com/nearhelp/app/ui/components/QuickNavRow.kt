package com.nearhelp.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nearhelp.app.ui.theme.SurfaceGlassHi
import com.nearhelp.app.ui.theme.Text1
import com.nearhelp.app.ui.theme.Text2

data class QuickNavItem(
    val label: String,
    val icon: ImageVector,
    val enabled: Boolean = true,
    val onClick: () -> Unit,
)

/**
 * The reference app's four circles (DESIGN.md §3): 40 dp white circles with
 * icon + caption. Contextual per screen; disabled items render dimmed.
 */
@Composable
fun QuickNavRow(items: List<QuickNavItem>, modifier: Modifier = Modifier) {
    androidx.compose.foundation.layout.Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(20.dp),
    ) {
        items.forEach { item ->
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Surface(
                    shape = CircleShape,
                    color = SurfaceGlassHi,
                    modifier = Modifier
                        .size(40.dp)
                        .then(
                            if (item.enabled) {
                                Modifier.clickable { item.onClick() }
                            } else {
                                Modifier
                            }
                        ),
                ) {
                    Icon(
                        imageVector = item.icon,
                        contentDescription = item.label,
                        tint = if (item.enabled) Text1 else Text2.copy(alpha = 0.4f),
                        modifier = Modifier.padding(8.dp),
                    )
                }
                Text(
                    text = item.label,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    color = if (item.enabled) Text2 else Text2.copy(alpha = 0.4f),
                    modifier = Modifier.padding(top = 4.dp),
                )
            }
        }
    }
}
