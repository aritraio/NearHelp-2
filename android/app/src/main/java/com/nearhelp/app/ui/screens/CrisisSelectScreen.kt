package com.nearhelp.app.ui.screens

import androidx.compose.foundation.background
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
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.nearhelp.app.ui.CrisisCategories
import com.nearhelp.app.ui.components.CountdownBar
import com.nearhelp.app.ui.components.GlassCard
import com.nearhelp.app.ui.crisisCategory
import com.nearhelp.app.ui.theme.BgIncident
import com.nearhelp.app.ui.theme.BgNeutral
import com.nearhelp.app.ui.theme.Blue
import com.nearhelp.app.ui.theme.Red
import com.nearhelp.app.ui.theme.RedDeep
import com.nearhelp.app.ui.theme.Text1
import com.nearhelp.app.ui.theme.Text2

/** Emergency panel (DESIGN.md §4.2): address card, 3×3 grid, countdown bar. */
@Composable
fun CrisisSelectScreen(
    onCommitted: (String) -> Unit,
    onDismiss: () -> Unit,
    viewModel: CrisisSelectViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    if (state.createdSosId != null) {
        LaunchedEffect(state.createdSosId) { onCommitted(state.createdSosId!!) }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(
                if (state.countdown != null) Brush.verticalGradient(listOf(BgIncident, BgIncident))
                else Brush.verticalGradient(listOf(BgNeutral, BgNeutral))
            )
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = if (state.isDrill) "DRILL — select emergency" else "What is happening?",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold,
            color = Text1,
            modifier = Modifier.padding(vertical = 20.dp),
        )

        // Address card + confirm location (reference Screen 2).
        GlassCard(Modifier.fillMaxWidth()) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = state.location?.format() ?: "locating…",
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    color = Text1,
                )
            }
            Spacer(Modifier.height(8.dp))
            Text(
                text = "Confirm this location before sending",
                fontSize = 12.sp,
                color = Text2,
            )
        }

        Spacer(Modifier.height(20.dp))

        // 3×3 category grid.
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            CrisisCategories.chunked(3).forEach { row ->
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    row.forEach { category ->
                        com.nearhelp.app.ui.components.CategoryTile(
                            category = category,
                            selected = state.categoryKey == category.key,
                            onClick = { viewModel.selectCategory(category.key) },
                            modifier = Modifier.weight(1f),
                        )
                    }
                }
            }
        }

        Spacer(Modifier.height(16.dp))
        OutlinedTextField(
            value = state.description,
            onValueChange = viewModel::setDescription,
            label = { Text("Describe briefly (optional)") },
            modifier = Modifier.fillMaxWidth(),
            minLines = 1,
            maxLines = 3,
        )

        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 8.dp),
        ) {
            Text("DRILL mode", fontSize = 12.sp, color = Text2)
            Spacer(Modifier.weight(1f))
            Switch(
                checked = state.isDrill,
                onCheckedChange = viewModel::setDrill,
                colors = SwitchDefaults.colors(checkedTrackColor = Blue),
            )
        }
        if (state.isDrill) {
            Text(
                "DRILL — NOT A REAL EMERGENCY. No call-services prompt will fire.",
                fontSize = 10.sp,
                color = Blue,
            )
        }

        state.error?.let {
            Spacer(Modifier.height(8.dp))
            Text(it, color = RedDeep, fontSize = 12.sp)
        }

        Spacer(Modifier.weight(1f))
        Spacer(Modifier.height(20.dp))

        when {
            state.busy -> Text("alerting responders…", fontWeight = FontWeight.Bold, color = Text1)
            state.countdown != null -> CountdownBar(
                count = state.countdown ?: 0,
                onCancel = viewModel::cancel,
            )
            else -> Row(
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Button(
                    onClick = onDismiss,
                    colors = ButtonDefaults.buttonColors(containerColor = com.nearhelp.app.ui.theme.Green),
                    modifier = Modifier.weight(1f),
                ) { Text("BACK", fontWeight = FontWeight.Bold) }
                Button(
                    onClick = viewModel::armCountdown,
                    colors = ButtonDefaults.buttonColors(containerColor = Red),
                    modifier = Modifier.weight(2f),
                ) { Text("SEND SOS →", fontWeight = FontWeight.Bold) }
            }
        }
        Spacer(Modifier.height(32.dp))
    }
}
