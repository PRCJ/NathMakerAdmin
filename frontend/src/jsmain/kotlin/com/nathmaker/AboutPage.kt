package com.nathmaker

import androidx.compose.runtime.Composable
import org.jetbrains.compose.web.css.*
import org.jetbrains.compose.web.dom.*

@Composable
fun AboutPage(onNavigate: (Screen) -> Unit) {
    Div({
        style {
            padding(80.px, 20.px)
            maxWidth(800.px)
            property("margin", "0 auto")
            fontFamily("system-ui, -apple-system, sans-serif")
            textAlign("center")
            lineHeight("1.8")
        }
    }) {
        H1({
            style {
                fontSize(40.px)
                color(Color("#2c3e50"))
                marginBottom(30.px)
            }
        }) { Text("Our Story") }

        P({
            style {
                fontSize(18.px)
                color(Color("#555"))
                marginBottom(40.px)
            }
        }) {
            Text("Founded with a passion for exquisite design and uncompromising quality, NathMaker has been shaping dreams into reality for over three decades of artisanal heritage.")
            Br()
            Br()
            Text("Every piece in our collection is a testament to the dedication of our master craftsmen, who meticulously transform ethically sourced precious metals and gemstones into timeless works of art.")
            Br()
            Br()
            Text("We believe that jewellery is more than adornment—it is a personal narrative, a symbol of love, and a legacy to be cherished for generations.")
        }

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
        }) { Text("Discover Our Legacy") }
    }
}

