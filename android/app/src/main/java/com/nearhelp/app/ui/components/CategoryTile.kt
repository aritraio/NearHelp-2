package com.nearhelp.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
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
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nearhelp.app.ui.theme.SurfaceGlassHi
import com.nearhelp.app.ui.theme.Text2

data class CrisisCategory(
    val key: String,
    val label: String,
    val icon: ImageVector,
    val color: Color,
)

/**
 * One tile of the crisis grid (reference Screen 2): white tile, flat category
 * icon, caption; selected state fills with the category color (DESIGN.md §3).
 */
@Composable
fun CategoryTile(
    category: CrisisCategory,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = modifier.clickable { onClick() },
    ) {
        Surface(
            shape = RoundedCornerShape(8.dp),
            color = if (selected) category.color else SurfaceGlassHi,
            modifier = Modifier.size(64.dp),
        ) {
            Box(contentAlignment = Alignment.Center) {
                Icon(
                    imageVector = category.icon,
                    contentDescription = category.label,
                    tint = if (selected) Color.White else category.color,
                    modifier = Modifier.size(28.dp),
                )
            }
        }
        Text(
            text = category.label,
            fontSize = 12.sp,
            fontWeight = if (selected) FontWeight.Bold else FontWeight.Normal,
            color = Text2,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(top = 4.dp),
        )
    }
}

/** Pill form used on the incident screen, map legend, notifications. */
@Composable
fun CategoryChip(category: CrisisCategory, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(50),
        color = category.color.copy(alpha = 0.15f),
    ) {
        Text(
            text = category.label,
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold,
            color = category.color,
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
        )
    }
}
