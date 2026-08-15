package com.nearhelp.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nearhelp.app.ui.theme.BgCalm
import com.nearhelp.app.ui.theme.BgCalmDeep
import com.nearhelp.app.ui.theme.NearHelpTheme
import com.nearhelp.app.ui.theme.SurfaceGlass
import com.nearhelp.app.ui.theme.Text1
import com.nearhelp.app.ui.theme.Text2

/**
 * Phase 0 placeholder home screen — proves Compose, Hilt, and the design
 * tokens render. The real hold-for-SOS interaction lands in Phase 3
 * (todos.md §3.2); the responder stat comes online with the SOS engine.
 */
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            NearHelpTheme {
                HomeSkeleton()
            }
        }
    }
}

@Composable
fun HomeSkeleton() {
    Surface(modifier = Modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(Brush.verticalGradient(BgCalmDeep, BgCalm)),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
        ) {
            Text(
                text = "Salt Lake",
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold,
                color = Text1,
            )
            Text(
                text = "responder network booting…",
                fontSize = 12.sp,
                color = Text2,
                modifier = Modifier.padding(bottom = 48.dp),
            )
            Surface(
                shape = CircleShape,
                color = SurfaceGlass,
                modifier = Modifier.size(160.dp),
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center,
                ) {
                    Text(
                        text = "HOLD FOR SOS",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        color = Text1,
                    )
                }
            }
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun HomeSkeletonPreview() {
    NearHelpTheme {
        HomeSkeleton()
    }
}
