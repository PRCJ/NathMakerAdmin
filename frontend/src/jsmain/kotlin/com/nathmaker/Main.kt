package com.nathmaker

import androidx.compose.runtime.*
import org.jetbrains.compose.web.dom.*
import org.jetbrains.compose.web.renderComposable

enum class Screen { Splash, Login, Home }
// test
fun main() {
    renderComposable(rootElementId = "root") {
        var currentScreen by remember { mutableStateOf(Screen.Splash) }
        var username by remember { mutableStateOf("") }
        var password by remember { mutableStateOf("") }

        when (currentScreen) {
            Screen.Splash -> SplashScreen { currentScreen = Screen.Login }

            Screen.Login -> LoginPage { user, pass ->
                username = user
                password = pass
                currentScreen = Screen.Home
            }

            Screen.Home -> HomePage(username, password)
        }
    }
}
