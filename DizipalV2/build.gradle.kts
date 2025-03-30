version = 5

cloudstream {
    authors     = listOf("primatzeka")
    language    = "tr"
    description = "Dizipal, yabancı dizi, yerli dizi - film ve anime izlemeniz için sizinledir."

    /**
     * Status int as the following:
     * 0: Down
     * 1: Ok
     * 2: Slow
     * 3: Beta only
    **/
    status  = 1 // will be 3 if unspecified
    tvTypes = listOf("TvSeries")
    iconUrl = "https://www.google.com/s2/favicons?domain=dizipal910&sz=%size%"
}