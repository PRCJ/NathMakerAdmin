package com.nathmaker

import androidx.compose.runtime.*
import org.jetbrains.compose.web.css.*
import org.jetbrains.compose.web.dom.*

@Composable
fun HomePage(onNavigate: (Screen) -> Unit) {
    Div({ style { fontFamily("system-ui, -apple-system, sans-serif") } }) {

        // Hero Section
        Div({
            style {
                position(Position.Relative)
                height(80.vh)
                backgroundColor(Color("#fdfbf7"))
                display(DisplayStyle.Flex)
                alignItems(AlignItems.Center)
                justifyContent(JustifyContent.Center)
                textAlign("center")
            }
        }) {
            Div({
                style {
                    maxWidth(600.px)
                    padding(40.px)
                }
            }) {
                H1({
                    style {
                        fontSize(56.px)
                        color(Color("#2c3e50"))
                        marginBottom(20.px)
                        property("letter-spacing", "-1px")
                        lineHeight("1.1")
                    }
                }) { Text("Elegance in Every Detail") }

                P({
                    style {
                        fontSize(20.px)
                        color(Color("#666"))
                        marginBottom(40.px)
                        lineHeight("1.6")
                    }
                }) { Text("Discover our exclusive collection of handcrafted jewellery, designed to celebrate your unique moments.") }

                Button(attrs = {
                    style {
                        backgroundColor(Color("#d4af37"))
                        color(Color("white"))
                        padding(15.px, 40.px)
                        border(0.px, LineStyle.None, Color("transparent"))
                        borderRadius(4.px)
                        fontSize(16.px)
                        fontWeight("bold")
                        cursor("pointer")
                        property("text-transform", "uppercase")
                        property("letter-spacing", "${1}px")
                    }
                    onClick { onNavigate(Screen.Catalogues) }
                }) {
                    Text("Explore Collections")
                }
            }
        }

        // Tagline Section
        Div({
            style {
                padding(80.px, 20.px)
                backgroundColor(Color("white"))
                textAlign("center")
            }
        }) {
            H2({
                style {
                    fontSize(32.px)
                    color(Color("#333"))
                    maxWidth(800.px)
                    property("margin", "0 auto")
                    fontWeight("300")
                    lineHeight("1.5")
                }
            }) { Text("\"True beauty is not about being noticed, it's about being remembered.\"") }
            P({
                style {
                    marginTop(20.px)
                    color(Color("#999"))
                    property("text-transform", "uppercase")
                    property("letter-spacing", "${2}px")
                    fontSize(14.px)
                }
            }) { Text("— The NathMaker Promise") }
        }
    }
}

