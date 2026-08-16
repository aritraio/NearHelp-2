package com.nearhelp.app.ui.screens

import android.Manifest
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Map
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.QuestionAnswer
import androidx.compose.material.icons.filled.VolunteerActivism
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.nearhelp.app.ui.components.QuickNavItem
import com.nearhelp.app.ui.components.QuickNavRow
import com.nearhelp.app.ui.components.ResponderStatPill
import com.nearhelp.app.ui.components.SosHoldButton
import com.nearhelp.app.ui.theme.BgCalm
import com.nearhelp.app.ui.theme.BgCalmDeep
import com.nearhelp.app.ui.theme.GreenDeep
import com.nearhelp.app.ui.theme.Text1
import com.nearhelp.app.ui.theme.Text2
import com.nearhelp.app.ui.theme.Text3

/**
 * Calm dashboard (DESIGN.md §4.1): locality header, live responder stat,
 * hold-for-SOS, CHECK-IN expander, live GPS footer. Nothing red lives here.
 */
@Composable
fun HomeScreen(
    onSosArmed: () -> Unit,
    onProfile: () -> Unit,
    viewModel: HomeViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    var checkInExpanded by remember { mutableStateOf(false) }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { grants ->
        viewModel.hasLocationPermission = grants[Manifest.permission.ACCESS_FINE_LOCATION] == true
        viewModel.refresh()
    }

    LaunchedEffect(Unit) {
        val wants = buildList {
            add(Manifest.permission.ACCESS_FINE_LOCATION)
            add(Manifest.permission.ACCESS_COARSE_LOCATION)
            if (Build.VERSION.SDK_INT >= 33) add(Manifest.permission.POST_NOTIFICATIONS)
        }
        permissionLauncher.launch(wants.toTypedArray())
    }

    Surface(modifier = Modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(Brush.verticalGradient(listOf(BgCalmDeep, BgCalm)))
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 48.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("Salt Lake", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = Text1)
                Box(Modifier.weight(1f))
                IconButton(onClick = onProfile) {
                    Icon(
                        Icons.Filled.Person,
                        contentDescription = "Profile",
                        tint = Text1,
                    )
                }
            }
            ResponderStatPill(count = state.nearbyResponders, modifier = Modifier.padding(top = 4.dp))

            Box(Modifier.weight(1f), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    SosHoldButton(onFired = onSosArmed)
                    if (state.locationPermissionDenied) {
                        Text(
                            "location permission needed for responder matching",
                            fontSize = 12.sp,
                            color = Text2,
                            modifier = Modifier.padding(top = 16.dp),
                        )
                    }
                }
            }

            QuickNavRow(
                items = listOf(
                    QuickNavItem("Respond", Icons.Filled.VolunteerActivism, enabled = false) {},
                    QuickNavItem("Map", Icons.Filled.Map, enabled = false) {},
                    QuickNavItem("Chat", Icons.Filled.QuestionAnswer, enabled = false) {},
                    QuickNavItem("Profile", Icons.Filled.Person, enabled = true, onClick = onProfile),
                ),
                modifier = Modifier.padding(vertical = 20.dp),
            )

            // CHECK-IN expander (reference Screen 1).
            Text(
                text = if (checkInExpanded) "CHECK IN ˄" else "CHECK IN ˅",
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                color = GreenDeep,
                modifier = Modifier
                    .padding(bottom = 8.dp)
                    .clickable { checkInExpanded = !checkInExpanded },
            )
            AnimatedVisibility(visible = checkInExpanded) {
                Text(
                    text = "You have no pending check-ins. Emergency contacts arrive in Phase 4.",
                    fontSize = 12.sp,
                    color = Text2,
                    modifier = Modifier.padding(bottom = 12.dp),
                )
            }

            Text(
                text = state.location?.format() ?: "locating…",
                fontSize = 10.sp,
                color = Text3,
                modifier = Modifier.padding(bottom = 24.dp),
            )
        }
    }
}
