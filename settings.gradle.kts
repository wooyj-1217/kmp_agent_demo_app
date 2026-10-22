pluginManagement { repositories { gradlePluginPortal(); google(); mavenCentral() } }
dependencyResolutionManagement { repositories { mavenCentral(); google() } }
rootProject.name = "memo-mvp"
include(":shared", ":server", ":web")
if (providers.gradleProperty("android").isPresent) include(":androidApp")
