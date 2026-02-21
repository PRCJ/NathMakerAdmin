package com.nathmaker

import androidx.compose.runtime.*
import kotlinx.browser.window
import kotlinx.coroutines.MainScope
import kotlinx.coroutines.await
import kotlinx.coroutines.launch
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import org.jetbrains.compose.web.css.*
import org.jetbrains.compose.web.dom.*
import org.w3c.fetch.Headers
import org.w3c.fetch.RequestInit

private val scope = MainScope()

@JsName("btoa")
external fun btoa(input: String): String
// test comment
@Composable
fun HomePage(username: String, password: String) {
    var catalogues by remember { mutableStateOf<List<Catalogue>>(emptyList()) }
    var error by remember { mutableStateOf<String?>(null) }
    var isLoading by remember { mutableStateOf(true) }

    LaunchedEffect(Unit) {
        scope.launch {
            try {
                val headers = Headers().apply {
                    append("Authorization", "Basic " + btoa("$username:$password"))
                }

                val response = window.fetch(
                    "/api/catalogue",
                    RequestInit(method = "GET", headers = headers)
                ).await()

                if (response.ok) {
                    val text = response.text().await()
                    val json = Json { ignoreUnknownKeys = true }
                    catalogues = json.decodeFromString(text)
                } else {
                    error = "Server error: ${response.status}"
                }
            } catch (e: Exception) {
                error = "Failed to load data: ${e.message}"
            } finally {
                isLoading = false
            }
        }
    }

    H1 { Text("🏬 NathMaker Catalogue") }

    when {
        error != null -> P { Text("❌ $error") }
        isLoading -> P { Text("Loading products...") }
        catalogues.isEmpty() -> P { Text("The catalogue is currently empty. Add products via the admin app!") }
        else -> {
            catalogues.forEach { catalogue ->
                H2 { Text(catalogue.catalogueName) }
                Div({
                    style {
                        display(DisplayStyle.Grid)
                        gridTemplateColumns("repeat(auto-fit, minmax(200px, 1fr))")
                        gap(16.px)
                    }
                }) {
                    catalogue.items.forEach { item ->
                        Div({
                            style {
                                border(1.px, LineStyle.Solid, rgb(220, 220, 220))
                                borderRadius(10.px)
                                padding(12.px)
                                backgroundColor(rgb(250, 250, 255))
                                textAlign("center")
                            }
                        }) {
                            P { Text(item.code) }
                            P { Text(item.type) }
                            P { Text("₹${item.price}") }
                        }
                    }
                }
            }
        }
    }
}
