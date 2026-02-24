package com.nathmaker

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import org.jetbrains.compose.web.renderComposable

sealed class Screen {
    object Splash : Screen()
    object Home : Screen()
    object Catalogues : Screen()
    data class Products(val catalogueId: Int? = null) : Screen()
    data class ProductDetail(val productId: Int) : Screen()
    object About : Screen()
    object Contact : Screen()
}

fun main() {
    renderComposable(rootElementId = "root") {
        var currentScreen by remember { mutableStateOf<Screen>(Screen.Splash) }

        NavBar(
            onNavigate = { screen -> currentScreen = screen }
        )

        when (val screen = currentScreen) {
            is Screen.Splash -> SplashScreen { currentScreen = Screen.Home }
            is Screen.Home -> HomePage(onNavigate = { s -> currentScreen = s })
            is Screen.Catalogues -> CataloguePage(onNavigate = { s -> currentScreen = s })
            is Screen.Products -> ProductListingPage(screen.catalogueId, onNavigate = { s -> currentScreen = s })
            is Screen.ProductDetail -> ProductDetailPage(screen.productId, onNavigate = { s -> currentScreen = s })
            is Screen.About -> AboutPage(onNavigate = { s -> currentScreen = s })
            is Screen.Contact -> ContactPage(onNavigate = { s -> currentScreen = s })
        }
    }
}

