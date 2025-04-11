version = 5

cloudstream {
    authors     = listOf("primatzeka")
    language    = "tr"
    description = "Dizipal, Dizipal güncel, Dizipal Twitter, yabancı dizi izle, film izle, türkçe dublaj film izle, türkçe dublaj dizi izle, dizi izle"

    /**
     * Status int as the following:
     * 0: Down
     * 1: Ok
     * 2: Slow
     * 3: Beta only
    **/
    status  = 1 // will be 3 if unspecified
    tvTypes = listOf("TvSeries", "Movie")

    // Dosya ve regex tanımlamaları
    val mainKtFile = file("src/main/kotlin/com/Prueba/DiziPalV2.kt")
    val mainUrlRegex = """mainUrl\s*=\s*"https://([^"]+)"""".toRegex()

    val domain = mainKtFile.readText().let { content ->
        mainUrlRegex.find(content)?.groupValues?.get(1) ?: "dizipal1015.com"
    }

    // Burada iconUrl'yi tanımlayın
    project.extra["iconUrl"] = "https://www.google.com/s2/favicons?domain=https://$domain&sz=%size%"
}