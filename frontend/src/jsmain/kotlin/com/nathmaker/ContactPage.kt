package com.nathmaker

import androidx.compose.runtime.Composable
import org.jetbrains.compose.web.css.*
import org.jetbrains.compose.web.dom.*

@Composable
fun ContactPage(onNavigate: (Screen) -> Unit) {
    Div({
        style {
            padding(80.px, 20.px)
            maxWidth(600.px)
            property("margin", "0 auto")
            fontFamily("system-ui, -apple-system, sans-serif")
            textAlign("center")
        }
    }) {
        H1({
            style {
                fontSize(40.px)
                color(Color("#2c3e50"))
                marginBottom(20.px)
            }
        }) { Text("Get in Touch") }

        P({
            style {
                fontSize(18.px)
                color(Color("#666"))
                marginBottom(50.px)
                lineHeight("1.6")
            }
        }) { Text("Whether you're looking for a bespoke creation or have a question about our existing collections, our concierge team is here to assist you.") }

        Div({
            style {
                backgroundColor(Color("#fdfbf7"))
                padding(40.px)
                borderRadius(8.px)
                border(1.px, LineStyle.Solid, Color("#eee"))
            }
        }) {
            H3({
                style {
                    fontSize(22.px)
                    color(Color("#333"))
                    marginBottom(15.px)
                }
            }) { Text("Direct Inquiry") }

            P({
                style {
                    color(Color("#777"))
                    marginBottom(30.px)
                }
            }) { Text("The fastest way to reach us is through WhatsApp. Our representatives respond within 24 hours.") }

            val phone = "919000000000"
            val msg = js("encodeURIComponent")("Hello NathMaker, I have an inquiry.").toString()

            A(href = "https://wa.me/$phone?text=$msg", attrs = {
                attr("target", "_blank")
                style {
                    backgroundColor(Color("#25D366"))
                    color(Color("white"))
                    padding(15.px, 40.px)
                    textDecoration("none")
                    borderRadius(30.px)
                    fontSize(16.px)
                    fontWeight("bold")
                    display(DisplayStyle.InlineBlock)
                }
            }) { Text("Message us on WhatsApp") }

            Div({
                style {
                    marginTop(40.px)
                    paddingTop(30.px)
                    property("border-top", "1px solid #e0e0e0")
                    textAlign("left")
                }
            }) {
                P({ style { color(Color("#333")); fontWeight("bold"); marginBottom(10.px) } }) { Text("Store Location:") }
                P({ style { color(Color("#666")); lineHeight("1.5") } }) {
                    Text("123 Diamond Avenue, Suite 400")
                    Br()
                    Text("Jewellery District, HD 400010")
                }
            }
        }
    }
}

