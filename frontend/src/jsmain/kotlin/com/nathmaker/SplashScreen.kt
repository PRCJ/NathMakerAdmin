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
            0%, 100% { 
                filter: drop-shadow(0 0 20px rgba(102, 126, 234, 0.6));
            }
            50% { 
                filter: drop-shadow(0 0 30px rgba(102, 126, 234, 0.9));
            }
        }
        
        @keyframes logoFloat {
            0%, 100% { 
                transform: translateY(0px) scale(1);
            }
            50% { 
                transform: translateY(-5px) scale(1.02);
            }
        }
        
        @keyframes pulse {
            0%, 100% { 
                opacity: 0.6;
                transform: scale(1);
            }
            50% { 
                opacity: 1;
                transform: scale(1.1);
            }
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
        
        @keyframes aurora {
            0%, 100% { 
                background-position: 0% 50%;
                filter: hue-rotate(0deg);
            }
            50% { 
                background-position: 100% 50%;
                filter: hue-rotate(45deg);
            }
        }
        
        .brand-glow {
            animation: glow 2s ease-in-out infinite;
        }
        
        .logo-float {
            animation: logoFloat 3s ease-in-out infinite;
        }
        
        .pulse-dot {
            animation: pulse 1.4s ease-in-out infinite;
        }
        
        .sparkle-rotate {
            animation: sparkleRotate 3s ease-in-out infinite;
        }
        
        .aurora-bg {
            background: linear-gradient(135deg, #667eea, #764ba2, #f093fb, #f5576c, #4facfe, #00f2fe);
            background-size: 400% 400%;
            animation: aurora 8s ease infinite;
        }
        
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
        classes("aurora-bg")
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
        }
    }) {

        // Decorative elements with modern colors
        if (isVisible) {
            // Dreamy sparkles
            Div({
                classes("sparkle-rotate")
                style {
                    position(Position.Absolute)
                    top(15.percent)
                    left(20.percent)
                    fontSize(1.8.em)
                    color(rgba(255, 255, 255, 0.9))
                    property("animation-delay", "0s")
                }
            }) {
                Text("✦")
            }

            Div({
                classes("sparkle-rotate")
                style {
                    position(Position.Absolute)
                    top(25.percent)
                    right(25.percent)
                    fontSize(1.5.em)
                    color(rgba(240, 147, 251, 0.8))
                    property("animation-delay", "0.8s")
                }
            }) {
                Text("✧")
            }

            Div({
                classes("sparkle-rotate")
                style {
                    position(Position.Absolute)
                    bottom(30.percent)
                    left(15.percent)
                    fontSize(1.6.em)
                    color(rgba(79, 172, 254, 0.8))
                    property("animation-delay", "1.2s")
                }
            }) {
                Text("✨")
            }

            // Modern geometric elements
            Div({
                style {
                    position(Position.Absolute)
                    top(35.percent)
                    right(15.percent)
                    fontSize(1.3.em)
                    color(rgba(245, 87, 108, 0.7))
                    property("animation", "pulse 2.5s ease-in-out infinite")
                    property("animation-delay", "1.8s")
                }
            }) {
                Text("◆")
            }
        }

        // Main content container
        Div({
            classes("logo-float")
            style {
                textAlign("center")
                color(Color.white)
                backgroundColor(rgba(255, 255, 255, 0.15))
                borderRadius(24.px)
                padding(48.px)
                border(1.px, LineStyle.Solid, rgba(255, 255, 255, 0.25))
                property("backdrop-filter", "blur(25px)")
                property("box-shadow", "0 25px 60px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.2)")
                maxWidth(420.px)
            }
        }) {

            // Logo - Beautiful jewelry placeholder
            if (isVisible) {
                Div({
                    classes("fade-in-1", "logo-float")
                    style {
                        marginBottom(24.px)
                        display(DisplayStyle.Flex)
                        alignItems(AlignItems.Center)
                        justifyContent(JustifyContent.Center)
                    }
                }) {

                    // Elegant jewelry-themed logo placeholder
                    Div({
                        style {
                            width(120.px)
                            height(120.px)
                            borderRadius(50.percent)
                            border(2.px, LineStyle.Solid, rgba(255, 255, 255, 0.6))
                            property("box-shadow", "0 15px 35px rgba(0, 0, 0, 0.2)")
                            property("filter", "drop-shadow(0 0 20px rgba(255, 255, 255, 0.3))")
                            background("linear-gradient(135deg, #FFD700 0%, #FFA500 25%, #FF6347 50%, #DC143C 75%, #8B0000 100%)")
                            display(DisplayStyle.Flex)
                            alignItems(AlignItems.Center)
                            justifyContent(JustifyContent.Center)
                            flexDirection(FlexDirection.Column)
                            position(Position.Relative)
                            property("backdrop-filter", "blur(10px)")
                        }
                    }) {
                        // Main jewelry symbol - diamond/gem
                        Div({
                            style {
                                fontSize(3.2.em)
                                color(rgba(255, 255, 255, 0.95))
                                marginBottom((-8).px)
                                property("text-shadow", "0 2px 8px rgba(0, 0, 0, 0.3)")
                                property("filter", "drop-shadow(0 0 10px rgba(255, 255, 255, 0.5))")
                            }
                        }) {
                            Text("💎")
                        }

                        // Decorative jewelry elements around the main gem
                        Div({
                            style {
                                fontSize(1.1.em)
                                color(rgba(255, 215, 0, 0.9))
                                position(Position.Absolute)
                                top(15.px)
                                right(20.px)
                                property("animation", "sparkleRotate 2s ease-in-out infinite")
                                property("animation-delay", "0.3s")
                            }
                        }) {
                            Text("✦")
                        }

                        Div({
                            style {
                                fontSize(0.9.em)
                                color(rgba(255, 255, 255, 0.8))
                                position(Position.Absolute)
                                top(22.px)
                                left(18.px)
                                property("animation", "sparkleRotate 2.5s ease-in-out infinite")
                                property("animation-delay", "0.8s")
                            }
                        }) {
                            Text("✧")
                        }

                        Div({
                            style {
                                fontSize(1.3.em)
                                color(rgba(255, 105, 180, 0.8))
                                position(Position.Absolute)
                                bottom(18.px)
                                right(28.px)
                                property("animation", "pulse 2s ease-in-out infinite")
                                property("animation-delay", "1.2s")
                            }
                        }) {
                            Text("♦")
                        }

                        Div({
                            style {
                                fontSize(1.0.em)
                                color(rgba(255, 255, 255, 0.7))
                                position(Position.Absolute)
                                bottom(20.px)
                                left(25.px)
                                property("animation", "sparkleRotate 1.8s ease-in-out infinite")
                                property("animation-delay", "0.5s")
                            }
                        }) {
                            Text("✨")
                        }
                    }
                }
            }

            // Brand name
            if (isVisible) {
                H1({
                    classes("brand-glow", "fade-in-1")
                    style {
                        fontSize(2.8.em)
                        fontWeight("700")
                        margin(0.px)
                        marginBottom(16.px)
                        background("linear-gradient(135deg, #ffffff 0%, #f0f8ff 50%, #e6e6fa 100%)")
                        property("-webkit-background-clip", "text")
                        property("-webkit-text-fill-color", "transparent")
                        property("background-clip", "text")
                        letterSpacing(1.px)
                        lineHeight("1.1")
                    }
                }) {
                    Text("NathMakers")
                }
            }

            // Tagline
            if (showTagline) {
                P({
                    classes("fade-in-2")
                    style {
                        fontSize(1.3.em)
                        fontWeight("300")
                        margin(0.px)
                        marginBottom(32.px)
                        color(rgba(255, 255, 255, 0.95))
                        letterSpacing(0.5.px)
                        lineHeight("1.4")
                    }
                }) {
                    Text("Najuk - just like you")
                }
            }

            // Loading indicator
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
                    // Loading dots
                    Div({
                        classes("pulse-dot")
                        style {
                            width(10.px)
                            height(10.px)
                            borderRadius(50.percent)
                            backgroundColor(rgba(255, 255, 255, 0.9))
                            property("animation-delay", "0s")
                        }
                    })

                    Div({
                        classes("pulse-dot")
                        style {
                            width(10.px)
                            height(10.px)
                            borderRadius(50.percent)
                            backgroundColor(rgba(255, 255, 255, 0.9))
                            property("animation-delay", "0.3s")
                        }
                    })

                    Div({
                        classes("pulse-dot")
                        style {
                            width(10.px)
                            height(10.px)
                            borderRadius(50.percent)
                            backgroundColor(rgba(255, 255, 255, 0.9))
                            property("animation-delay", "0.6s")
                        }
                    })
                }

                // Loading text
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