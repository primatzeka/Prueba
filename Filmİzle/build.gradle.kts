version = 3

cloudstream {
    authors     = listOf("primatzeka")
    language    = "tr"
    description = "(Film izle ile Full HD Film Keyfini Sınırsız Yaşa. Yerli ve yabancı filmleri Türkçe dublaj veya Türkçe altyazılı seçeneğiyle reklamsız film sitesi."

    /**
     * Status int as the following:
     * 0: Down
     * 1: Ok
     * 2: Slow
     * 3: Beta only
    **/
    status  = 1 // will be 3 if unspecified
    tvTypes = listOf("Movie")
    iconUrl = "https://www.google.com/s2/favicons?domain=www.filmizle.cx&sz=%size%"
}