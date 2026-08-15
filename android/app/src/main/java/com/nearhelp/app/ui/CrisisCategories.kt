package com.nearhelp.app.ui

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Air
import androidx.compose.material.icons.filled.Bolt
import androidx.compose.material.icons.filled.DirectionsCar
import androidx.compose.material.icons.filled.HelpOutline
import androidx.compose.material.icons.filled.LocalHospital
import androidx.compose.material.icons.filled.LocalPolice
import androidx.compose.material.icons.filled.Thunderstorm
import androidx.compose.material.icons.filled.Water
import androidx.compose.material.icons.filled.Whatshot
import com.nearhelp.app.ui.components.CrisisCategory
import com.nearhelp.app.ui.theme.CatAccident
import com.nearhelp.app.ui.theme.CatDisaster
import com.nearhelp.app.ui.theme.CatFire
import com.nearhelp.app.ui.theme.CatGas
import com.nearhelp.app.ui.theme.CatMedical
import com.nearhelp.app.ui.theme.CatOther
import com.nearhelp.app.ui.theme.CatPolice
import com.nearhelp.app.ui.theme.CatPower

/** The 3×3 crisis grid (DESIGN.md §4.2) — one color per category everywhere. */
val CrisisCategories: List<CrisisCategory> = listOf(
    CrisisCategory("medical", "Medical", Icons.Filled.LocalHospital, CatMedical),
    CrisisCategory("fire", "Fire", Icons.Filled.Whatshot, CatFire),
    CrisisCategory("gas_leak", "Gas Leak", Icons.Filled.Air, CatGas),
    CrisisCategory("accident", "Accident", Icons.Filled.DirectionsCar, CatAccident),
    CrisisCategory("security", "Security", Icons.Filled.LocalPolice, CatPolice),
    CrisisCategory("disaster", "Disaster", Icons.Filled.Thunderstorm, CatDisaster),
    CrisisCategory("power", "Power", Icons.Filled.Bolt, CatPower),
    CrisisCategory("disaster_flood", "Flood", Icons.Filled.Water, CatDisaster),
    CrisisCategory("other", "Other", Icons.Filled.HelpOutline, CatOther),
)

fun crisisCategory(key: String?): CrisisCategory =
    CrisisCategories.firstOrNull { it.key == key } ?: CrisisCategories.last()
