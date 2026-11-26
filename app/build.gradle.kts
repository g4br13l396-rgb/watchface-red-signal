plugins { id("com.android.application") }

android {
    namespace = "com.personal.redsignalwatchface"
    compileSdk = 34
    defaultConfig {
        applicationId = "com.personal.redsignalwatchface"
        minSdk = 33
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }
    // Chiave di firma fissa nel repository: gli aggiornamenti si installano senza disinstallare
    signingConfigs {
        getByName("debug") {
            storeFile = file("debug.keystore")
            storePassword = "android"
            keyAlias = "androiddebugkey"
            keyPassword = "android"
        }
    }
    buildTypes { release { isMinifyEnabled = false } }
}
