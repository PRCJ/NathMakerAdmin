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

private val listingScope = MainScope()

@Composable
fun ProductListingPage(catalogueId: Int? = null, onNavigate: (Screen) -> Unit) {
    var products by remember { mutableStateOf<List<Product>>(emptyList()) }
    var error by remember { mutableStateOf<String?>(null) }
    var isLoading by remember { mutableStateOf(true) }

    LaunchedEffect(catalogueId) {
        listingScope.launch {
            try {
                val url = if (catalogueId != null) "/api/products?catalogueId=$catalogueId" else "/api/products"
                val response = window.fetch(url, RequestInit(method = "GET")).await()
                if (response.ok) {
                    val text = response.text().await()
                    val json = Json { ignoreUnknownKeys = true }
                    products = json.decodeFromString(text)
                } else {
                    error = "Server error: ${response.status}"
                }
            } catch (e: Exception) {
                error = "Failed to load products: ${e.message}"
            } finally {
                isLoading = false
            }
        }
    }

    Div({
        style {
            padding(40.px, 20.px)
            maxWidth(1400.px)
            property("margin", "0 auto")
            fontFamily("system-ui, -apple-system, sans-serif")
        }
    }) {
        Div({
            style {
                display(DisplayStyle.Flex)
                justifyContent(JustifyContent.SpaceBetween)
                alignItems(AlignItems.Center)
                marginBottom(40.px)
            }
        }) {
            H1({
                style {
                    fontSize(32.px)
                    color(Color("#222"))
                }
            }) { Text(if (catalogueId != null) "Collection Products" else "All Products") }

            if (catalogueId != null) {
                Button(attrs = {
                    style {
                        padding(10.px, 20.px)
                        backgroundColor(Color("transparent"))
                        border(1.px, LineStyle.Solid, Color("#ccc"))
                        borderRadius(4.px)
                        cursor("pointer")
                        color(Color("#555"))
                    }
                    onClick { onNavigate(Screen.Catalogues) }
                }) { Text("← Back to Collections") }
            }
        }

        when {
            error != null -> P({ style { color(Color("red")); textAlign("center") } }) { Text("❌ $error") }
            isLoading -> Div({ style { textAlign("center"); padding(40.px) } }) { Text("Loading products...") }
            products.isEmpty() -> {
                Div({
                    style { textAlign("center"); padding(60.px); backgroundColor(Color("#f9f9f9")); borderRadius(8.px) }
                }) {
                    Text("No products found in this collection.")
                }
            }
            else -> {
                Div({
                    style {
                        display(DisplayStyle.Grid)
                        gridTemplateColumns("repeat(auto-fill, minmax(280px, 1fr))")
                        gap(30.px)
                    }
                }) {
                    products.forEach { product ->
                        if (product.isAvailable) {
                            Div({
                                style {
                                    cursor("pointer")
                                    display(DisplayStyle.Flex)
                                    flexDirection(FlexDirection.Column)
                                    height(100.percent)
                                    property("transition", "transform 0.2s")
                                }
                                onClick { onNavigate(Screen.ProductDetail(product.id)) }
                            }) {
                                Div({
                                    style {
                                        width(100.percent)
                                        property("aspect-ratio", "1/1")
                                        backgroundColor(Color("#f5f5f5"))
                                        position(Position.Relative)
                                        overflow("hidden")
                                        marginBottom(15.px)
                                    }
                                }) {
                                    if (product.imageUrls.isNotEmpty()) {
                                        Img(src = product.imageUrls.first(), attrs = {
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
                                                color(Color("#aaa"))
                                            }
                                        }) { Text("No Image") }
                                    }
                                }

                                Div({
                                    style {
                                        flex(1)
                                        display(DisplayStyle.Flex)
                                        flexDirection(FlexDirection.Column)
                                    }
                                }) {
                                    H3({
                                        style {
                                            fontSize(18.px)
                                            property("margin", "0 0 8px 0")
                                            color(Color("#333"))
                                            fontWeight("500")
                                        }
                                    }) { Text(product.productName) }

                                    if (!product.material.isNullOrEmpty()) {
                                        Span({
                                            style {
                                                fontSize(13.px)
                                                color(Color("#888"))
                                                marginBottom(10.px)
                                                display(DisplayStyle.Block)
                                            }
                                        }) { Text(product.material) }
                                    }

                                    Div({
                                        style {
                                            property("margin-top", "auto")
                                        }
                                    }) {
                                        Span({
                                            style {
                                                fontSize(18.px)
                                                fontWeight("bold")
                                                color(Color("#222"))
                                            }
                                        }) {
                                            val pStr = product.price.toString()
                                            val fmtPrice = if (pStr.endsWith(".0")) pStr.removeSuffix(".0") else pStr
                                            Text("₹$fmtPrice")
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

