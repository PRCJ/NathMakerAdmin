import org.jetbrains.kotlin.gradle.targets.js.webpack.KotlinWebpackConfig

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

            commonWebpackConfig {
                cssSupport {
                    enabled.set(true)
                }
                devServer = (devServer ?: KotlinWebpackConfig.DevServer()).apply {
                    port = 8081
                    open = true
                }
            }

            // Configure distribution directory
            distribution {
                directory = File("$buildDir/distributions")
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

// Configure webpack tasks
tasks.named("jsBrowserProductionWebpack") {
    doLast {
        // Create index.html for production build
        val distributionsDir = File("$buildDir/distributions")
        distributionsDir.mkdirs()

        val indexHtml = File(distributionsDir, "index.html")
        indexHtml.writeText("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NathMaker Admin</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        }
        #loading {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            font-size: 18px;
            color: #666;
        }
    </style>
</head>
<body>
    <div id="root">
        <div id="loading">Loading NathMaker Admin...</div>
    </div>
    <script src="frontend.js"></script>
</body>
</html>
        """.trimIndent())

        println("✅ Created index.html in distributions directory")
    }
}

tasks.named("jsBrowserDevelopmentWebpack") {
    doLast {
        // Create index.html for development build
        val distributionsDir = File("$buildDir/distributions")
        distributionsDir.mkdirs()

        val indexHtml = File(distributionsDir, "index.html")
        if (!indexHtml.exists()) {
            indexHtml.writeText("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NathMaker Admin - Development</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        }
    </style>
</head>
<body>
    <div id="root"></div>
    <script src="frontend.js"></script>
</body>
</html>
            """.trimIndent())
        }
    }
}

// Ensure distributions directory is created
tasks.named("build") {
    doLast {
        val distributionsDir = File("$buildDir/distributions")
        if (!distributionsDir.exists()) {
            distributionsDir.mkdirs()
            println("Created distributions directory")
        }
    }
}