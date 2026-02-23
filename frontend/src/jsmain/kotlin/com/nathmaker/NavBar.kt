package com.nathmaker

import androidx.compose.runtime.Composable
import org.jetbrains.compose.web.css.*
import org.jetbrains.compose.web.dom.*

@Composable
fun NavBar(onNavigate: (Screen) -> Unit) {
    Nav({
        style {
            display(DisplayStyle.Flex)
            justifyContent(JustifyContent.SpaceBetween)
            alignItems(AlignItems.Center)
            padding(20.px, 40.px)
            backgroundColor(Color("white"))
            property("box-shadow", "0 2px 10px rgba(0,0,0,0.05)")
            position(Position.Sticky)
            top(0.px)
            property("z-index", "100")
        }
    }) {
        Div({
            style {
                fontSize(24.px)
                fontWeight("bold")
                color(Color("#333"))
                cursor("pointer")
                property("letter-spacing", "-0.5px")
            }
            onClick { onNavigate(Screen.Home) }
        }) {
            Text("NATHMAKER")
        }

        Div({
            style {
                display(DisplayStyle.Flex)
                gap(30.px)
            }
        }) {
            val linkStyle: StyleScope.() -> Unit = {
                color(Color("#555"))
                textDecoration("none")
                fontSize(16.px)
                cursor("pointer")
                property("transition", "color 0.2s")
            }

            A(href = "#", attrs = {
                style(linkStyle)
                onClick {
                    it.preventDefault()
                    onNavigate(Screen.Home)
                }
            }) { Text("Home") }

            A(href = "#", attrs = {
                style(linkStyle)
                onClick {
                    it.preventDefault()
                    onNavigate(Screen.Catalogues)
                }
            }) { Text("Collections") }

            A(href = "#", attrs = {
                style(linkStyle)
                onClick {
                    it.preventDefault()
                    onNavigate(Screen.Products())
                }
            }) { Text("Products") }

            A(href = "#", attrs = {
                style(linkStyle)
                onClick {
                    it.preventDefault()
                    onNavigate(Screen.About)
                }
            }) { Text("About") }

            A(href = "#", attrs = {
                style(linkStyle)
                onClick {
                    it.preventDefault()
                    onNavigate(Screen.Contact)
                }
            }) { Text("Contact") }
        }
    }
}
