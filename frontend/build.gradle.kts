plugins {
    kotlin("multiplatform") version "2.0.0"
    id("org.jetbrains.compose") version "1.6.10"
    id("org.jetbrains.kotlin.plugin.compose") version "2.0.0"
    kotlin("plugin.serialization") version "2.0.0"
}

kotlin {
    js(IR) {
        browser {
            binaries.executable()

            webpackTask {
                mainOutputFileName = "frontend.js"
            }

            runTask {
                outputFileName = "frontend.js"
            }

            testTask {
                useKarma {
                    useChromeHeadless()
                }
            }
        }

        // Ensure proper compilation settings
        compilations.all {
            compileKotlinTask.kotlinOptions {
                moduleKind = "umd"
                sourceMap = true
                sourceMapEmbedSources = "always"
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

                // Ensure these web-specific dependencies are included
                implementation("org.jetbrains.compose.web:web-core:1.6.10")
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core-js:1.9.0")
            }
        }

        val jsTest by getting {
            dependencies {
                implementation(kotlin("test-js"))
            }
        }
    }
}

// Critical: Configure webpack properly for production
tasks.named("jsBrowserProductionWebpack") {
    dependsOn("jsMainClasses")
}

// Ensure main function is callable
tasks.withType<org.jetbrains.kotlin.gradle.targets.js.ir.KotlinJsIrLink>().configureEach {
    kotlinOptions {
        main = "call"
        moduleKind = "umd"
    }
}

tasks.register<Copy>("prepareVercelDist") {
    dependsOn("jsBrowserProductionWebpack")

    from("$buildDir/kotlin-webpack/js/productionExecutable") {
        include("*.js")
        include("*.map")
    }
    from("$buildDir/processedResources/js/main") {
        include("index.html")
    }
    into("$buildDir/vercel-dist")
}
