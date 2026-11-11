import org.jetbrains.kotlin.gradle.ExperimentalWasmDsl
import org.jetbrains.kotlin.gradle.targets.js.webpack.KotlinWebpackConfig
import java.security.MessageDigest

plugins {
    kotlin("multiplatform")
    kotlin("plugin.compose")
    id("org.jetbrains.compose")
    id("com.android.application")
}
kotlin {
    androidTarget { compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) } }
    listOf(iosArm64(), iosSimulatorArm64(), iosX64()).forEach { target ->
        target.binaries.framework { baseName = "MoaKit"; isStatic = true }
    }
    @OptIn(ExperimentalWasmDsl::class)
    wasmJs {
        outputModuleName.set("yeoback")
        browser {
            commonWebpackConfig {
                outputFileName = "yeoback.js"
                devServer = (devServer ?: KotlinWebpackConfig.DevServer()).apply { port = 8080 }
            }
        }
        binaries.executable()
    }
    sourceSets {
        commonMain.dependencies {
            implementation(project(":shared"))
            implementation(compose.runtime)
            implementation(compose.foundation)
            implementation(compose.material3)
            implementation(compose.ui)
            implementation(compose.components.resources)
        }
        androidMain.dependencies { implementation("androidx.activity:activity-compose:1.10.1") }
        androidInstrumentedTest.dependencies {
            implementation("androidx.compose.ui:ui-test-junit4:1.9.0")
            implementation("androidx.test:runner:1.6.2")
            implementation("androidx.test.ext:junit:1.2.1")
        }
    }
}
compose.resources { packageOfResClass = "dev.yeoback.resources" }
android {
    namespace = "dev.yeoback.app"
    compileSdk = 35
    defaultConfig { applicationId = providers.gradleProperty("memoAcceptanceAppId").getOrElse("dev.yeoback.app"); minSdk = 24; targetSdk = 35; versionCode = 1; versionName = "1.0"; testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner" }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
}
dependencies { debugImplementation("androidx.compose.ui:ui-test-manifest:1.9.0") }

tasks.register("packageOfflineWeb") {
    dependsOn("wasmJsBrowserDistribution")
    doLast {
        val directory = layout.buildDirectory.dir("dist/wasmJs/productionExecutable").get().asFile
        val assets = directory.walkTopDown().filter { it.isFile && it.name != "sw.js" && it.extension != "map" }.sortedBy { it.relativeTo(directory).path }.toList()
        val digest = MessageDigest.getInstance("SHA-256")
        assets.forEach { digest.update(it.relativeTo(directory).path.toByteArray()); digest.update(it.readBytes()) }
        val version = digest.digest().take(12).joinToString("") { "%02x".format(it) }
        val paths = (listOf("./") + assets.map { "./" + it.relativeTo(directory).invariantSeparatorsPath }).joinToString(",", "[", "]") { "\"$it\"" }
        directory.resolve("sw.js").writeText("""
            const CACHE = 'yeoback-$version';
            const ASSETS = $paths;
            self.addEventListener('install', event => {
              event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting()));
            });
            self.addEventListener('activate', event => {
              event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith('yeoback-') && key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()));
            });
            self.addEventListener('fetch', event => {
              if (event.request.method !== 'GET' || new URL(event.request.url).origin !== self.location.origin) return;
              event.respondWith(caches.open(CACHE).then(cache => cache.match(event.request, {ignoreSearch:true}).then(cached => cached || fetch(event.request))));
            });
        """.trimIndent())
        println("Offline web bundle: ${assets.size} assets, cache $version")
    }
}
