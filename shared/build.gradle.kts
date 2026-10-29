plugins { kotlin("multiplatform"); id("com.android.library") }
kotlin {
    androidTarget { compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) } }
    jvm()
    iosArm64(); iosSimulatorArm64(); iosX64()
    @OptIn(org.jetbrains.kotlin.gradle.ExperimentalWasmDsl::class)
    wasmJs { browser() }
    sourceSets { commonTest.dependencies { implementation(kotlin("test")) } }
}
android {
    namespace = "dev.yeoback.shared"
    compileSdk = 35
    defaultConfig { minSdk = 24 }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
}
