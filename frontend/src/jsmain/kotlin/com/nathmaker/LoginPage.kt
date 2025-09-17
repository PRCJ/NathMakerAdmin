package com.nathmaker

import androidx.compose.runtime.*
import org.jetbrains.compose.web.css.*
import org.jetbrains.compose.web.dom.*
import org.jetbrains.compose.web.attributes.InputType
import org.jetbrains.compose.web.attributes.placeholder

@Composable
fun LoginPage(onLoginSuccess: (String, String) -> Unit) {
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }

    Div({
        style {
            display(DisplayStyle.Flex)
            flexDirection(FlexDirection.Column)
            justifyContent(JustifyContent.Center)
            alignItems(AlignItems.Center)
            height(100.vh)
            backgroundColor(rgb(250, 250, 250))
        }
    }) {
        H2 { Text("🔐 Login to NathMaker") }

        Input(type = InputType.Text) {
            placeholder("user")
            value(username)
            onInput { username = it.value }
        }

        Br()

        Input(type = InputType.Password) {
            placeholder("2bde89bf-311b-4f2b-983b-90b8b2ecbae3")
            value(password)
            onInput { password = it.value }
        }

        Br()

        Button(attrs = {
            onClick {
                if (username.isNotBlank() && password.isNotBlank()) {
                    onLoginSuccess(username, password)
                }
            }
        }) {
            Text("Login")
        }
    }
}
