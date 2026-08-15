package com.nearhelp.app.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

// DESIGN.md §2.2 — Inter is the target family; Roboto (Compose default) is the
// accepted fallback until Inter is bundled.
val NearHelpTypography = Typography(
    displayLarge = TextStyle(fontSize = 28.sp, fontWeight = FontWeight.Bold),
    titleLarge = TextStyle(fontSize = 24.sp, fontWeight = FontWeight.Bold),
    labelLarge = TextStyle(fontSize = 16.sp, fontWeight = FontWeight.Bold),
    bodyLarge = TextStyle(fontSize = 14.sp),
    bodySmall = TextStyle(fontSize = 12.sp),
    labelSmall = TextStyle(fontSize = 10.sp),
)
