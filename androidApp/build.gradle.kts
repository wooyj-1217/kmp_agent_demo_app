plugins {
    id("com.android.application") version "8.10.0"
    kotlin("android") version "2.2.10"
    kotlin("plugin.serialization") version "2.2.10"
}
android {
    namespace = "memo.android"
    compileSdk = 35
    defaultConfig { applicationId = "dev.memo.mvp"; minSdk = 26; targetSdk = 35; versionCode = 1; versionName = "1.0"; testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner" }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
}
kotlin { compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) } }
dependencies {
    implementation(files("../shared/build/libs/shared-jvm.jar"))
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.9.0")
    androidTestImplementation("androidx.test:runner:1.6.2")
    androidTestImplementation("androidx.test:core:1.6.1")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
}
