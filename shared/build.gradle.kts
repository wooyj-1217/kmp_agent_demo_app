plugins { kotlin("multiplatform"); kotlin("plugin.serialization") }
kotlin {
    jvm { compilerOptions { jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17) } }
    js(IR) { browser(); binaries.library() }
    iosArm64 { binaries.framework { baseName = "Shared"; isStatic = true } }
    iosX64 { binaries.framework { baseName = "Shared"; isStatic = true } }
    iosSimulatorArm64 { binaries.framework { baseName = "Shared"; isStatic = true } }
    sourceSets {
        commonMain.dependencies { implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.9.0") }
        commonTest.dependencies { implementation(kotlin("test")) }
        jvmTest.dependencies { implementation(kotlin("test-junit")) }
    }
}
