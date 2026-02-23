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

private val detailScope = MainScope()

@Composable
fun ProductDetailPage(productId: Int, onNavigate: (Screen) -> Unit) {
    var product by remember { mutableStateOf<Product?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var isLoading by remember { mutableStateOf(true) }
    var mainImageIndex by remember { mutableStateOf(0) }

    LaunchedEffect(productId) {
        detailScope.launch {
            try {
                val response = window.fetch("/api/products/$productId", RequestInit(method = "GET")).await()
                if (response.ok) {
                    val text = response.text().await()
                    val json = Json { ignoreUnknownKeys = true }
                    product = json.decodeFromString(text)
                } else {
                    error = "Server error: ${response.status}"
                }
            } catch (e: Exception) {
                error = "Failed to load product details: ${e.message}"
            } finally {
                isLoading = false
            }
        }
    }

    Div({
        style {
            maxWidth(1200.px)
            property("margin", "0 auto")
            padding(40.px, 20.px)
            fontFamily("system-ui, -apple-system, sans-serif")
        }
    }) {
        if (isLoading) {
            Div({ style { textAlign("center"); padding(40.px) } }) { Text("Loading product details...") }
        } else if (error != null) {
            P({ style { color(Color("red")); textAlign("center") } }) { Text("❌ $error") }
        } else if (product == null) {
            P({ style { textAlign("center") } }) { Text("Product not found.") }
        } else {
            val p = product!!

            Div({
                style {
                    display(DisplayStyle.Flex)
                    gap(60.px)
                    property("flex-wrap", "wrap")
                }
            }) {
                // Left Column: Images
                Div({
                    style {
                        flex(1)
                        minWidth(300.px)
                    }
                }) {
                    // Main Image
                    Div({
                        style {
                            width(100.percent)
                            property("aspect-ratio", "1/1")
                            backgroundColor(Color("#f5f5f5"))
                            marginBottom(20.px)
                            position(Position.Relative)
                            overflow("hidden")
                        }
                    }) {
                        if (p.imageUrls.isNotEmpty() && mainImageIndex < p.imageUrls.size) {
                            Img(src = p.imageUrls[mainImageIndex], attrs = {
                                style {
                                    width(100.percent)
                                    height(100.percent)
                                    property("object-fit", "contain")
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
                            }) { Text("No Image Available") }
                        }
                    }

                    // Thumbnails
                    if (p.imageUrls.size > 1) {
                        Div({
                            style {
                                display(DisplayStyle.Flex)
                                gap(10.px)
                                overflowX("auto")
                                paddingBottom(10.px)
                            }
                        }) {
                            p.imageUrls.forEachIndexed { index, url ->
                                Div({
                                    style {
                                        width(80.px)
                                        height(80.px)
                                        flexShrink(0)
                                        cursor("pointer")
                                        border(2.px, LineStyle.Solid,
                                            if (index == mainImageIndex) Color("#333") else Color("transparent"))
                                        opacity(if (index == mainImageIndex) 1.0 else 0.6)
                                    }
                                    onClick { mainImageIndex = index }
                                }) {
                                    Img(src = url, attrs = {
                                        style {
                                            width(100.percent)
                                            height(100.percent)
                                            property("object-fit", "cover")
                                        }
                                    })
                                }
                            }
                        }
                    }
                }

                // Right Column: Details
                Div({
                    style {
                        flex(1)
                        display(DisplayStyle.Flex)
                        flexDirection(FlexDirection.Column)
                        minWidth(300.px)
                    }
                }) {
                    H1({
                        style {
                            fontSize(36.px)
                            color(Color("#222"))
                            property("margin", "0 0 10px 0")
                            fontWeight("400")
                        }
                    }) { Text(p.productName) }

                    Div({
                        style {
                            fontSize(28.px)
                            color(Color("#222"))
                            fontWeight("bold")
                            marginBottom(30.px)
                        }
                    }) {
                        val pStr = p.price.toString()
                        val fmtPrice = if (pStr.endsWith(".0")) pStr.removeSuffix(".0") else pStr
                        Text("₹$fmtPrice")
                    }

                    if (!p.description.isNullOrEmpty()) {
                        P({
                            style {
                                fontSize(16.px)
                                color(Color("#555"))
                                lineHeight("1.6")
                                marginBottom(30.px)
                            }
                        }) { Text(p.description) }
                    }

                    // Spec Grid
                    if (!p.material.isNullOrEmpty() || !p.weight.isNullOrEmpty()) {
                        Div({
                            style {
                                display(DisplayStyle.Grid)
                                gridTemplateColumns("auto 1fr")
                                property("gap", "15px 30px")
                                marginBottom(40.px)
                                padding(20.px)
                                backgroundColor(Color("#fdfbf7"))
                                property("border-top", "1px solid #eee")
                                property("border-bottom", "1px solid #eee")
                            }
                        }) {
                            if (!p.material.isNullOrEmpty()) {
                                Span({ style { fontWeight("bold"); color(Color("#666")) } }) { Text("Material:") }
                                Span({ style { color(Color("#222")) } }) { Text(p.material) }
                            }
                            if (!p.weight.isNullOrEmpty()) {
                                Span({ style { fontWeight("bold"); color(Color("#666")) } }) { Text("Weight:") }
                                Span({ style { color(Color("#222")) } }) { Text(p.weight) }
                            }
                        }
                    }

                    // WhatsApp CTA
                    val msg = js("encodeURIComponent")("Hi NathMaker, I am interested in ${p.productName} (ID: ${p.id}). Could you provide more details?").toString()
                    val phone = "919000000000"

                    A(href = "https://wa.me/$phone?text=$msg", attrs = {
                        attr("target", "_blank")
                        style {
                            backgroundColor(Color("#25D366"))
                            color(Color("white"))
                            padding(16.px, 0.px)
                            textAlign("center")
                            textDecoration("none")
                            borderRadius(4.px)
                            fontSize(16.px)
                            fontWeight("bold")
                            display(DisplayStyle.Block)
                            width(100.percent)
                            property("transition", "background-color 0.2s")
                        }
                    }) { Text("Enquire on WhatsApp") }

                    Button(attrs = {
                        style {
                            marginTop(15.px)
                            backgroundColor(Color("transparent"))
                            border(0.px, LineStyle.None, Color("transparent"))
                            color(Color("#666"))
                            cursor("pointer")
                            textDecoration("underline")
                        }
                        onClick {
                            if (p.catalogueId > 0) {
                                onNavigate(Screen.Products(p.catalogueId))
                            } else {
                                onNavigate(Screen.Catalogues)
                            }
                        }
                    }) { Text("← Back to collection") }
                }
            }
        }
    }
}

