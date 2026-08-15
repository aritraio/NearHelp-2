package com.nearhelp.app.ui.screens

import android.Manifest
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.PowerManager
import android.provider.Settings
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BatteryAlert
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.Place
import androidx.compose.material3.Button
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.nearhelp.app.ui.components.GlassCard
import com.nearhelp.app.ui.theme.Blue
import com.nearhelp.app.ui.theme.Green
import com.nearhelp.app.ui.theme.GreenDeep
import com.nearhelp.app.ui.theme.Text1
import com.nearhelp.app.ui.theme.Text2

/** Skill types mirrored from the backend catalog (app/core/constants.py). */
private val SkillTypes = listOf(
    "doctor", "nurse", "paramedic", "firefighter", "police", "cpr_certified",
    "first_aid_trained", "blood_donor", "electrician", "mechanic",
)

/**
 * Profile (DESIGN.md §4.6): identity + trust, skill claims with verification
 * state, the readiness indicator (improvements.md §1.4), demo settings, logout.
 */
@Composable
fun ProfileScreen(
    onLoggedOut: () -> Unit,
    viewModel: ProfileViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val demoRoute by viewModel.demoRoute.collectAsStateWithLifecycle(initialValue = false)
    val context = LocalContext.current
    var skillMenuOpen by remember { mutableStateOf(false) }

    val notificationsOk = remember {
        Build.VERSION.SDK_INT < 33 ||
            context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) ==
            android.content.pm.PackageManager.PERMISSION_GRANTED
    }
    val locationOk = remember {
        context.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) ==
            android.content.pm.PackageManager.PERMISSION_GRANTED
    }
    val batteryOk = remember {
        val pm = context.getSystemService(Context.POWER_SERVICE) as PowerManager
        pm.isIgnoringBatteryOptimizations(context.packageName)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
    ) {
        Text("Profile", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = Text1)

        state.user?.let { user ->
            GlassCard(Modifier.fillMaxWidth()) {
                Text(user.name, fontWeight = FontWeight.Bold, fontSize = 16.sp, color = Text1)
                Text(user.email, fontSize = 12.sp, color = Text2)
                Text(
                    "trust score: ${user.trust_score.toInt()} / 100",
                    fontSize = 12.sp,
                    color = GreenDeep,
                    modifier = Modifier.padding(top = 8.dp),
                )
            }
        }

        Spacer(Modifier.height(16.dp))

        // Readiness indicator: the invisible reliability problem made visible.
        GlassCard(Modifier.fillMaxWidth()) {
            Text("Responder readiness", fontWeight = FontWeight.Bold)
            readinessRow("Notifications", Icons.Filled.Notifications, notificationsOk)
            readinessRow("Location access", Icons.Filled.Place, locationOk)
            readinessRow(
                "Battery unrestricted",
                Icons.Filled.BatteryAlert,
                batteryOk,
            )
            if (!batteryOk) {
                Spacer(Modifier.height(8.dp))
                OutlinedButton(onClick = { requestBatteryExemption(context) }) {
                    Text("Remove battery restriction", color = Blue)
                }
                Text(
                    "Indian OEM battery managers kill background apps — exempting " +
                        "NearHelp keeps you reachable for nearby emergencies.",
                    fontSize = 10.sp,
                    color = Text2,
                )
            }
        }

        Spacer(Modifier.height(16.dp))

        // Skills + verification state.
        GlassCard(Modifier.fillMaxWidth()) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Skills", fontWeight = FontWeight.Bold)
                Spacer(Modifier.weight(1f))
                OutlinedButton(onClick = { skillMenuOpen = true }) {
                    Text("+ claim", color = Blue)
                }
                DropdownMenu(expanded = skillMenuOpen, onDismissRequest = { skillMenuOpen = false }) {
                    SkillTypes.forEach { skill ->
                        DropdownMenuItem(
                            text = { Text(skill.replace('_', ' ')) },
                            onClick = {
                                viewModel.claimSkill(skill)
                                skillMenuOpen = false
                            },
                        )
                    }
                }
            }
            if (state.skills.isEmpty()) {
                Text("No skill claims yet — verified skills rank you higher.", fontSize = 12.sp, color = Text2)
            }
            state.skills.forEach { claim ->
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.padding(top = 8.dp),
                ) {
                    Text(claim.skill_type.replace('_', ' '), fontSize = 13.sp, color = Text1)
                    Spacer(Modifier.weight(1f))
                    Text(
                        text = claim.status,
                        fontSize = 12.sp,
                        color = when (claim.status) {
                            "approved" -> GreenDeep
                            "rejected" -> Color(0xFFD32F2F)
                            else -> Text2
                        },
                        fontWeight = FontWeight.Bold,
                    )
                }
            }
        }

        Spacer(Modifier.height(16.dp))

        // Demo settings (improvements.md §5): fake-GPS scripted route.
        GlassCard(Modifier.fillMaxWidth()) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column {
                    Text("Demo mode", fontWeight = FontWeight.Bold)
                    Text(
                        "fake GPS: scripted approach toward Salt Lake",
                        fontSize = 10.sp,
                        color = Text2,
                    )
                }
                Spacer(Modifier.weight(1f))
                Switch(checked = demoRoute, onCheckedChange = viewModel::setDemoRoute)
            }
        }

        state.error?.let { Text(it, color = Color(0xFFD32F2F), fontSize = 12.sp) }

        Spacer(Modifier.height(24.dp))
        Button(
            onClick = { viewModel.logout(onLoggedOut) },
            colors = androidx.compose.material3.ButtonDefaults.buttonColors(
                containerColor = Color(0xFFD32F2F),
            ),
            modifier = Modifier.fillMaxWidth(),
        ) { Text("LOG OUT", fontWeight = FontWeight.Bold) }
        Spacer(Modifier.height(32.dp))
    }
}

@Composable
private fun readinessRow(label: String, icon: androidx.compose.ui.graphics.vector.ImageVector, ok: Boolean) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier.padding(top = 8.dp),
    ) {
        Icon(
            imageVector = icon,
            contentDescription = label,
            tint = if (ok) Green else Color(0xFFD32F2F),
        )
        Text(
            text = " $label",
            fontSize = 13.sp,
            color = Text1,
        )
        Spacer(Modifier.weight(1f))
        Text(
            text = if (ok) "ready" else "action needed",
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold,
            color = if (ok) GreenDeep else Color(0xFFD32F2F),
        )
    }
}

private fun requestBatteryExemption(context: Context) {
    val intent = Intent(
        Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
        Uri.parse("package:${context.packageName}"),
    )
    runCatching { context.startActivity(intent) }
}
