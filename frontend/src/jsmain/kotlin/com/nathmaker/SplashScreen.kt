package com.nathmaker

import androidx.compose.runtime.*
import kotlinx.coroutines.MainScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import org.jetbrains.compose.web.css.*
import org.jetbrains.compose.web.dom.*

private val scope = MainScope()

@Composable
fun SplashScreen(onFinish: () -> Unit) {
    var isVisible by remember { mutableStateOf(false) }
    var showTagline by remember { mutableStateOf(false) }
    var showLoader by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        delay(100)
        isVisible = true
        delay(800)
        showTagline = true
        delay(600)
        showLoader = true
        delay(1000)
        onFinish()
    }

    Style {
        """
        @keyframes glow {
            0%, 100% { filter: drop-shadow(0 0 15px rgba(212, 175, 55, 0.5)); }
            50% { filter: drop-shadow(0 0 30px rgba(212, 175, 55, 0.8)); }
        }

        @keyframes logoFloat {
            0%, 100% { transform: translateY(0px) scale(1); }
            50% { transform: translateY(-5px) scale(1.02); }
        }

        @keyframes pulse {
            0%, 100% { opacity: 0.6; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.1); }
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes sparkleRotate {
            0% { transform: rotate(0deg) scale(1); opacity: 0.7; }
            50% { transform: rotate(180deg) scale(1.2); opacity: 1; }
            100% { transform: rotate(360deg) scale(1); opacity: 0.7; }
        }

        .brand-glow { animation: glow 2s ease-in-out infinite; }
        .logo-float { animation: logoFloat 3s ease-in-out infinite; }
        .pulse-dot { animation: pulse 1.4s ease-in-out infinite; }
        .sparkle-rotate { animation: sparkleRotate 3s ease-in-out infinite; }

        .fade-in-1 {
            animation: fadeIn 0.8s ease-out forwards;
            animation-delay: 0.2s;
            opacity: 0;
        }
        .fade-in-2 {
            animation: fadeIn 0.8s ease-out forwards;
            animation-delay: 0.5s;
            opacity: 0;
        }
        .fade-in-3 {
            animation: fadeIn 0.8s ease-out forwards;
            opacity: 0;
        }
        """
    }

    Div({
        style {
            display(DisplayStyle.Flex)
            flexDirection(FlexDirection.Column)
            justifyContent(JustifyContent.Center)
            alignItems(AlignItems.Center)
            height(100.vh)
            width(100.vw)
            fontFamily("'Inter', 'Segoe UI', system-ui, sans-serif")
            margin(0.px)
            padding(0.px)
            position(Position.Relative)
            overflow("hidden")
            backgroundColor(Color("#c07840"))
        }
    }) {

        if (isVisible) {
            Div({
                classes("sparkle-rotate")
                style {
                    position(Position.Absolute)
                    top(15.percent)
                    left(20.percent)
                    fontSize(1.8.em)
                    color(rgba(212, 175, 55, 0.7))
                    property("animation-delay", "0s")
                }
            }) { Text("✦") }

            Div({
                classes("sparkle-rotate")
                style {
                    position(Position.Absolute)
                    top(25.percent)
                    right(25.percent)
                    fontSize(1.5.em)
                    color(rgba(255, 215, 0, 0.6))
                    property("animation-delay", "0.8s")
                }
            }) { Text("✧") }

            Div({
                classes("sparkle-rotate")
                style {
                    position(Position.Absolute)
                    bottom(30.percent)
                    left(15.percent)
                    fontSize(1.6.em)
                    color(rgba(212, 175, 55, 0.6))
                    property("animation-delay", "1.2s")
                }
            }) { Text("✨") }
        }

        Div({
            classes("logo-float")
            style {
                textAlign("center")
                color(Color.white)
                backgroundColor(rgba(255, 255, 255, 0.1))
                borderRadius(24.px)
                padding(48.px)
                border(1.px, LineStyle.Solid, rgba(255, 255, 255, 0.15))
                property("backdrop-filter", "blur(20px)")
                property("box-shadow", "0 25px 60px rgba(0, 0, 0, 0.2)")
                maxWidth(420.px)
            }
        }) {

            if (isVisible) {
                Div({
                    classes("fade-in-1", "brand-glow")
                    style {
                        marginBottom(24.px)
                        display(DisplayStyle.Flex)
                        alignItems(AlignItems.Center)
                        justifyContent(JustifyContent.Center)
                    }
                }) {
                    Img(src = "/logo.png", alt = "NathMakers Logo", attrs = {
                        style {
                            width(180.px)
                            height(180.px)
                            property("object-fit", "contain")
                            borderRadius(16.px)
                            property("filter", "drop-shadow(0 10px 30px rgba(0, 0, 0, 0.3))")
                        }
                    })
                }
            }

            if (isVisible) {
                H1({
                    classes("fade-in-1")
                    style {
                        fontSize(2.8.em)
                        fontWeight("700")
                        margin(0.px)
                        marginBottom(16.px)
                        color(Color.white)
                        property("letter-spacing", "1px")
                        lineHeight("1.1")
                        property("text-shadow", "0 2px 10px rgba(0, 0, 0, 0.3)")
                    }
                }) {
                    Text("NathMakers")
                }
            }

            if (showTagline) {
                P({
                    classes("fade-in-2")
                    style {
                        fontSize(1.3.em)
                        fontWeight("300")
                        margin(0.px)
                        marginBottom(32.px)
                        color(rgba(255, 255, 255, 0.95))
                        property("letter-spacing", "0.5px")
                        lineHeight("1.4")
                    }
                }) {
                    Text("Najuk - just like you")
                }
            }

            if (showLoader) {
                Div({
                    classes("fade-in-3")
                    style {
                        display(DisplayStyle.Flex)
                        alignItems(AlignItems.Center)
                        justifyContent(JustifyContent.Center)
                        gap(12.px)
                        marginTop(16.px)
                    }
                }) {
                    repeat(3) { i ->
                        Div({
                            classes("pulse-dot")
                            style {
                                width(10.px)
                                height(10.px)
                                borderRadius(50.percent)
                                backgroundColor(rgba(212, 175, 55, 0.9))
                                property("animation-delay", "${i * 0.3}s")
                            }
                        })
                    }
                }

                P({
                    style {
                        fontSize(0.95.em)
                        color(rgba(255, 255, 255, 0.9))
                        marginTop(24.px)
                        marginBottom(0.px)
                        fontWeight("300")
                    }
                }) {
                    Text("Preparing your experience...")
                }
            }
        }
    }
}
