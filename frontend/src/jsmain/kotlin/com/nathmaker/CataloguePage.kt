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
import org.w3c.fetch.RequestInit

private val catalogueScope = MainScope()

@Composable
fun CataloguePage(onNavigate: (Screen) -> Unit) {
    var catalogues by remember { mutableStateOf<List<Catalogue>>(emptyList()) }
    var error by remember { mutableStateOf<String?>(null) }
    var isLoading by remember { mutableStateOf(true) }

    LaunchedEffect(Unit) {
        catalogueScope.launch {
            try {
                val response = window.fetch("/api/catalogues", RequestInit(method = "GET")).await()
                if (response.ok) {
                    val text = response.text().await()
                    val json = Json { ignoreUnknownKeys = true }
                    catalogues = json.decodeFromString(text)
                } else {
                    error = "Server error: ${response.status}"
                }
            } catch (e: Exception) {
                error = "Failed to load catalogues: ${e.message}"
            } finally {
                isLoading = false
            }
        }
    }

    Div({
        style {
            padding(60.px, 20.px)
            maxWidth(1200.px)
            property("margin", "0 auto")
            fontFamily("system-ui, -apple-system, sans-serif")
        }
    }) {
        H1({
            style {
                textAlign("center")
                fontSize(40.px)
                color(Color("#333"))
                marginBottom(10.px)
            }
        }) { Text("Our Collections") }

        P({
            style {
                textAlign("center")
                color(Color("#666"))
                marginBottom(50.px)
            }
        }) { Text("Curated selections for every occasion") }

        when {
            error != null -> P({ style { color(Color("red")); textAlign("center") } }) { Text("❌ $error") }
            isLoading -> Div({ style { textAlign("center"); padding(40.px) } }) { Text("Loading collections...") }
            catalogues.isEmpty() -> P({ style { textAlign("center"); color(Color("#888")) } }) { Text("No collections currently available.") }
            else -> {
                Div({
                    style {
                        display(DisplayStyle.Grid)
                        gridTemplateColumns("repeat(auto-fill, minmax(300px, 1fr))")
                        gap(40.px)
                    }
                }) {
                    catalogues.forEach { cat ->
                        Div({
                            style {
                                cursor("pointer")
                                property("transition", "transform 0.3s ease")
                            }
                            onClick { onNavigate(Screen.Products(cat.id)) }
                        }) {
                            Div({
                                style {
                                    height(350.px)
                                    backgroundColor(Color("#eee"))
                                    borderRadius(8.px)
                                    overflow("hidden")
                                    marginBottom(15.px)
                                }
                            }) {
                                if (!cat.coverImageUrl.isNullOrEmpty()) {
                                    Img(src = cat.coverImageUrl, attrs = {
                                        style {
                                            width(100.percent)
                                            height(100.percent)
                                            property("object-fit", "cover")
                                        }
                                    })
                                } else {
                                    Div({
                                        style {
                                            width(100.percent)
                                            height(100.percent)
                                            display(DisplayStyle.Flex)
                                            alignItems(AlignItems.Center)
                                            justifyContent(JustifyContent.Center)
                                            color(Color("#999"))
                                        }
                                    }) { Text("No Image") }
                                }
                            }
                            H3({
                                style {
                                    fontSize(20.px)
                                    property("margin", "0 0 5px 0")
                                    color(Color("#333"))
                                }
                            }) { Text(cat.name) }
                            if (!cat.description.isNullOrEmpty()) {
                                P({
                                    style {
                                        color(Color("#777"))
                                        fontSize(14.px)
                                        property("margin", "0")
                                        lineHeight("1.4")
                                    }
                                }) { Text(cat.description) }
                            }
                        }
                    }
                }
            }
        }
    }
}

