package com.nearhelp.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import androidx.navigation.navDeepLink
import com.nearhelp.app.data.auth.SessionStore
import com.nearhelp.app.data.push.PushRouter
import com.nearhelp.app.ui.screens.AlertScreen
import com.nearhelp.app.ui.screens.AuthScreen
import com.nearhelp.app.ui.screens.CrisisSelectScreen
import com.nearhelp.app.ui.screens.HomeScreen
import com.nearhelp.app.ui.screens.IncidentScreen
import com.nearhelp.app.ui.screens.ProfileScreen
import com.nearhelp.app.ui.theme.BgCalm
import com.nearhelp.app.ui.theme.NearHelpTheme
import dagger.hilt.android.AndroidEntryPoint
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            NearHelpTheme {
                NearHelpApp()
            }
        }
    }
}

@HiltViewModel
class MainViewModel @Inject constructor(sessionStore: SessionStore) : ViewModel() {
    /** null = still reading DataStore; true/false = session present/absent. */
    val loggedIn: StateFlow<Boolean?> = sessionStore.isLoggedIn
        .map { it as Boolean? }
        .stateIn(viewModelScope, SharingStarted.Eagerly, null)
}

@Composable
fun NearHelpApp(viewModel: MainViewModel = hiltViewModel()) {
    val loggedIn by viewModel.loggedIn.collectAsStateWithLifecycle()
    val navController = rememberNavController()

    // Foreground push routing: SOS alerts hop straight to the alert screen.
    LaunchedEffect(Unit) {
        PushRouter.alerts.collect { alert ->
            navController.navigate(
                "alert/${alert.sosId}?crisis=${alert.crisisType ?: "other"}&drill=${alert.isDrill}"
            ) {
                launchSingleTop = true
            }
        }
    }

    Surface(modifier = Modifier.fillMaxSize()) {
        when (loggedIn) {
            null -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
            else -> AppNavHost(navController, startLoggedOut = loggedIn == false)
        }
    }
}

@Composable
private fun AppNavHost(navController: NavHostController, startLoggedOut: Boolean) {
    NavHost(
        navController = navController,
        startDestination = if (startLoggedOut) "auth" else "home",
    ) {
        composable("auth") {
            AuthScreen(
                onAuthenticated = {
                    navController.navigate("home") {
                        popUpTo("auth") { inclusive = true }
                    }
                },
            )
        }

        composable("home") {
            HomeScreen(
                onSosArmed = { navController.navigate("crisis") },
                onProfile = { navController.navigate("profile") },
            )
        }

        composable("crisis") {
            CrisisSelectScreen(
                onCommitted = { sosId ->
                    navController.navigate("incident/$sosId") {
                        popUpTo("home")
                    }
                },
                onDismiss = { navController.popBackStack() },
            )
        }

        composable("profile") {
            ProfileScreen(
                onLoggedOut = {
                    navController.navigate("auth") {
                        popUpTo(0) { inclusive = true }
                    }
                },
            )
        }

        composable("incident/{sosId}") {
            IncidentScreen(onDone = { navController.popBackStack() })
        }

        // Responder alert — deep-linked from FCM notifications
        // (nearhelp://alert/{sosId}?crisis=…&drill=…) and foreground pushes.
        composable(
            route = "alert/{sosId}?crisis={crisis}&drill={drill}",
            arguments = listOf(
                navArgument("sosId") { },
                navArgument("crisis") {
                    defaultValue = "other"
                    type = androidx.navigation.NavType.StringType
                },
                navArgument("drill") {
                    defaultValue = false
                    type = androidx.navigation.NavType.BoolType
                },
            ),
            deepLinks = listOf(navDeepLink { uriPattern = "nearhelp://alert/{sosId}" }),
        ) { entry ->
            val sosId = entry.arguments?.getString("sosId").orEmpty()
            val crisis = entry.arguments?.getString("crisis")
            val drill = entry.arguments?.getBoolean("drill") ?: false
            AlertScreen(
                sosId = sosId,
                crisisType = crisis,
                isDrill = drill,
                onResponded = { id ->
                    navController.navigate("incident/$id") {
                        popUpTo("home")
                    }
                },
                onDismiss = { navController.popBackStack() },
            )
        }
    }
}
