version = 1

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
    iconUrl = "https://www.google.com/s2/favicons?domain=https://dizipal683.com&sz=%size%"
}
