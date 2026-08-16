package com.nearhelp.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.nearhelp.app.ui.components.GlassCard
import com.nearhelp.app.ui.theme.BgNeutral
import com.nearhelp.app.ui.theme.GreenDeep
import com.nearhelp.app.ui.theme.Red
import com.nearhelp.app.ui.theme.RedDeep
import com.nearhelp.app.ui.theme.Text1
import com.nearhelp.app.ui.theme.Text2

/** Login/register — one glass card, speed to Home (DESIGN.md §4.5). */
@Composable
fun AuthScreen(
    onAuthenticated: () -> Unit,
    viewModel: AuthViewModel = hiltViewModel(),
) {
    android.util.Log.d("NearHelp", "AuthScreen composing")
    val state by viewModel.state.collectAsStateWithLifecycle()
    var registerMode by remember { mutableStateOf(false) }
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var name by remember { mutableStateOf("") }

    if (state.loggedIn) {
        onAuthenticated()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(BgNeutral)
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Text(
            text = "NearHelp",
            fontSize = 28.sp,
            fontWeight = FontWeight.Bold,
            color = Text1,
        )
        Text(
            text = if (registerMode) "Create your responder profile" else "Welcome back",
            fontSize = 12.sp,
            color = Text2,
            modifier = Modifier.padding(bottom = 24.dp),
        )

        GlassCard(Modifier.fillMaxWidth()) {
            if (registerMode) {
                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("Full name") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                Spacer(Modifier.height(12.dp))
            }
            OutlinedTextField(
                value = email,
                onValueChange = { email = it },
                label = { Text("Email") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            Spacer(Modifier.height(12.dp))
            OutlinedTextField(
                value = password,
                onValueChange = { password = it },
                label = { Text("Password") },
                visualTransformation = PasswordVisualTransformation(),
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )

            state.error?.let { message ->
                Spacer(Modifier.height(12.dp))
                Text(text = message, color = RedDeep, fontSize = 12.sp)
            }

            Spacer(Modifier.height(20.dp))
            Button(
                onClick = {
                    if (registerMode) viewModel.register(email, password, name)
                    else viewModel.login(email, password)
                },
                enabled = !state.busy && email.isNotBlank() && password.length >= 8 &&
                    (!registerMode || name.isNotBlank()),
                colors = ButtonDefaults.buttonColors(containerColor = Red),
                modifier = Modifier.fillMaxWidth(),
            ) {
                if (state.busy) {
                    CircularProgressIndicator(
                        modifier = Modifier.height(20.dp),
                        color = Color.White,
                        strokeWidth = 2.dp,
                    )
                } else {
                    Text(
                        text = if (registerMode) "CREATE ACCOUNT" else "LOG IN",
                        fontWeight = FontWeight.Bold,
                    )
                }
            }
            Spacer(Modifier.height(8.dp))
            OutlinedButton(
                onClick = { registerMode = !registerMode },
                enabled = !state.busy,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(
                    text = if (registerMode) "I already have an account" else "Create an account",
                    color = GreenDeep,
                )
            }
        }
    }
}
