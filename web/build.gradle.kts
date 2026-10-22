plugins { kotlin("multiplatform"); kotlin("plugin.serialization") }
kotlin {
    js(IR) { browser { commonWebpackConfig { outputFileName = "memo.js" } }; binaries.executable() }
    sourceSets {
        jsMain.dependencies {
            implementation(project(":shared"))
            implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.9.0")
            implementation("org.jetbrains.kotlin:kotlin-dom-api-compat:2.2.10")
        }
    }
}
tasks.register<Copy>("designCss") {
    from(rootProject.file("docs/design/prototype.css"))
    into(layout.projectDirectory.dir("src/jsMain/resources"))
}
tasks.matching { it.name == "jsProcessResources" }.configureEach { dependsOn("designCss") }
