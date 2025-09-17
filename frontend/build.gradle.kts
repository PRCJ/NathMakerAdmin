import org.jetbrains.kotlin.gradle.targets.js.webpack.KotlinWebpackConfig
import org.jetbrains.kotlin.gradle.targets.js.webpack.KotlinWebpack

plugins {
    kotlin("multiplatform") version "2.0.0"
    id("org.jetbrains.compose") version "1.6.10"
    id("org.jetbrains.kotlin.plugin.compose") version "2.0.0"
    id("org.jetbrains.kotlin.js") apply false
    kotlin("plugin.serialization") version "2.0.0"
}

kotlin {
    js(IR) {
        browser {
            binaries.executable()

            commonWebpackConfig {
                cssSupport {
                    enabled.set(true)
                }
                devServer = (devServer ?: KotlinWebpackConfig.DevServer()).apply {
                    port = 8081
                    open = true
//                    proxy = mutableMapOf(
//                        "/api" to mapOf(
//                            "target" to "http://localhost:8080",
//                            "changeOrigin" to true
//                    ))
                }
            }

            webpackTask {
                output.libraryTarget = "umd"
                mainOutputFileName = "app.js"
                // 👇 after webpack finishes, copy index.html into distributions
                doLast {
                    copy {
                        from("$projectDir/src/jsMain/resources")
                        include("index.html")
                        into("$buildDir/distributions")
                    }
                }
            }
        }
    }

    sourceSets {
        val jsMain by getting {
            dependencies {
                implementation(compose.html.core)
                implementation(compose.runtime)
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.9.0")
                implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.2")

            }
        }
    }
}


tasks.named<Copy>("jsProcessResources") {
    from("src/jsMain/resources") {
        include("index.html")
        // 👇 OR include all static files
        // include("**/*")
    }
    into("$buildDir/distributions")
}
tasks.withType<Copy>().configureEach {
    duplicatesStrategy = DuplicatesStrategy.EXCLUDE
}


tasks.named<KotlinWebpack>("jsBrowserProductionWebpack") {
    outputFileName = "app.js"

    doLast {
        copy {
            from(destinationDirectory)   // ✅ no .get(), it's already a File
            include("app.js", "app.js.map")
            into("$buildDir/distributions")
        }
    }
}

tasks.named<KotlinWebpack>("jsBrowserDevelopmentWebpack") {
    outputFileName = "app.js"
}
tasks.named<KotlinWebpack>("jsBrowserProductionWebpack") {
    outputFileName = "app.js"
}

tasks.named<KotlinWebpack>("jsBrowserDevelopmentWebpack") {
    outputFileName = "app.js"
}