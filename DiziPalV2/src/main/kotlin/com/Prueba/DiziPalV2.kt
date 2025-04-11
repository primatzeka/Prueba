package com.primatzeka

import android.util.Log
import org.jsoup.nodes.Element
import com.lagradost.cloudstream3.*
import com.lagradost.cloudstream3.utils.*
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import com.lagradost.cloudstream3.network.CloudflareKiller
import okhttp3.Interceptor
import okhttp3.Response
import org.jsoup.Jsoup

class DiziPalV2 : MainAPI() {
    override var mainUrl = "https://dizipal1015.com"
    override var name = "DiziPalV2"
    override val hasMainPage = true
    override var lang = "tr"
    override val hasQuickSearch = true
    override val hasChromecastSupport = true
    override val hasDownloadSupport = true
    override val supportedTypes = setOf(TvType.TvSeries, TvType.Movie)

    override var sequentialMainPage = true
    // URL'leri düzeltmek için yardımcı fonksiyon ekleyelim
    private fun fixUrl(url: String): String {
        return url.replace(Regex("/+$"), "")  // Sondaki tüm / işaretlerini kaldır
    }
    private val cloudflareKiller by lazy { CloudflareKiller() }
    private val interceptor by lazy { CloudflareInterceptor(cloudflareKiller) }

    class CloudflareInterceptor(private val cloudflareKiller: CloudflareKiller) : Interceptor {
        override fun intercept(chain: Interceptor.Chain): Response {
            val request = chain.request()
            val response = chain.proceed(request)
            val doc = Jsoup.parse(response.peekBody(1024 * 1024).string())

            if (doc.select("title").text() == "Just a moment..." || doc.select("title").text() == "Bir dakika lütfen...") {
                return cloudflareKiller.intercept(chain)
            }

            return response
        }
    }

    override val mainPage = mainPageOf(
        "${mainUrl}/bolumler" to "Son Bölümler",
        "${mainUrl}/dizi" to "Yeni Diziler",
        "${mainUrl}/film" to "Yeni Filmler",
        "${mainUrl}/koleksiyon/netflix" to "Netflix",
        "${mainUrl}/koleksiyon/exxen" to "Exxen",
        "${mainUrl}/koleksiyon/blutv" to "BluTV",
        "${mainUrl}/koleksiyon/disney" to "Disney+",
        "${mainUrl}/koleksiyon/amazon-prime" to "Amazon Prime",
        "${mainUrl}/koleksiyon/tod-bein" to "TOD (beIN)",
        "${mainUrl}/koleksiyon/gain" to "Gain",
        "${mainUrl}/tur/mubi" to "Mubi",
        "${mainUrl}/diziler?kelime=&durum=&tur=26&type=&siralama=" to "Anime",
        "${mainUrl}/diziler?kelime=&durum=&tur=5&type=&siralama=" to "Bilimkurgu Dizileri",
        "${mainUrl}/tur/bilimkurgu" to "Bilimkurgu Filmleri",
        "${mainUrl}/diziler?kelime=&durum=&tur=11&type=&siralama=" to "Komedi Dizileri",
        "${mainUrl}/tur/komedi" to "Komedi Filmleri",
        "${mainUrl}/diziler?kelime=&durum=&tur=4&type=&siralama=" to "Belgesel Dizileri",
        "${mainUrl}/tur/belgesel" to "Belgesel Filmleri",
    )

    override suspend fun getMainPage(page: Int, request: MainPageRequest): HomePageResponse {
        val document = app.get(request.data).document
        val home = if (request.data.contains("/bolumler")) {
            document.select("article.post.dfx.fcl").mapNotNull { it.sonBolumler() }
        } else {
            document.select("article.post.dfx.fcl.movies").mapNotNull { it.diziler() }
        }

        return newHomePageResponse(request.name, home, hasNext = false)
    }

    private suspend fun Element.sonBolumler(): SearchResponse? {
        val name = this.selectFirst("header.entry-header h2.entry-title")?.text() ?: return null
        val episode = this.selectFirst("header.entry-header h2.num-epi")?.text()?.trim()?.replace(". Sezon ", "x")?.replace(". Bölüm", "") ?: return null
        val title = "$name $episode"

        val href = fixUrl(fixUrlNull(this.selectFirst("a")?.attr("href")) ?: return null)
        val posterUrl = fixUrlNull(this.selectFirst("div.post-thumbnail img")?.attr("src"))

        return newTvSeriesSearchResponse(title, href.substringBefore("/sezon"), TvType.TvSeries) {
            this.posterUrl = posterUrl
        }
    }

    private fun Element.diziler(): SearchResponse? {
        val title = this.selectFirst("header.entry-header h2.entry-title")?.text() ?: return null
        val href = fixUrl(fixUrlNull(this.selectFirst("a")?.attr("href")) ?: return null)
        val posterUrl = fixUrlNull(this.selectFirst("div.post-thumbnail.or-1 img")?.attr("src"))

        return newTvSeriesSearchResponse(title, href, TvType.TvSeries) { this.posterUrl = posterUrl }
    }

    private fun SearchItem.toPostSearchResult(): SearchResponse {
        val title = this.title
        val href = fixUrl("${mainUrl}${this.url}")
        val posterUrl = this.poster

        return if (this.type == "series") {
            newTvSeriesSearchResponse(title, href, TvType.TvSeries) { this.posterUrl = posterUrl }
        } else {
            newMovieSearchResponse(title, href, TvType.Movie) { this.posterUrl = posterUrl }
        }
    }

    override suspend fun search(query: String): List<SearchResponse> {
        val responseRaw = app.post(
            "${mainUrl}/api/search-autocomplete",
            headers = mapOf(
                "Accept" to "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With" to "XMLHttpRequest"
            ),
            referer = "${mainUrl}/",
            data = mapOf("query" to query)
        )

        val searchItemsMap = jacksonObjectMapper().readValue<Map<String, SearchItem>>(responseRaw.text)
        return searchItemsMap.values.map { it.toPostSearchResult() }
    }

    override suspend fun quickSearch(query: String): List<SearchResponse> = search(query)

    override suspend fun load(url: String): LoadResponse? {
        val cleanUrl = fixUrl(url)
        val document = app.get(cleanUrl).document
    
        val poster = fixUrlNull(document.selectFirst("[property='og:image']")?.attr("content"))
        val year = document.selectXpath("//div[text()='Yapım Yılı']//following-sibling::div").text().trim().toIntOrNull()
        val description = document.selectFirst("div.summary p")?.text()?.trim()
        val tags = document.selectXpath("//div[text()='Türler']//following-sibling::div").text().trim().split(" ").mapNotNull { it.trim() }
        val rating = document.selectXpath("//div[text()='IMDB Puanı']//following-sibling::div").text().trim().toRatingInt()
        val duration = Regex("(\\d+)").find(document.selectXpath("//div[text()='Ortalama Süre']//following-sibling::div").text() ?: "")?.value?.toIntOrNull()
    
        return if (cleanUrl.contains("/dizi/")) {
            val title = document.selectFirst("div.cover h5")?.text() ?: return null
    
            val episodes = document.select("div.episode-item").mapNotNull {
                val epName = it.selectFirst("div.name")?.text()?.trim() ?: return@mapNotNull null
                val epHref = fixUrl(fixUrlNull(it.selectFirst("a")?.attr("href")) ?: return@mapNotNull null)
                val epEpisode = it.selectFirst("div.episode")?.text()?.trim()?.split(" ")?.get(2)?.replace(".", "")?.toIntOrNull()
                val epSeason = it.selectFirst("div.episode")?.text()?.trim()?.split(" ")?.get(0)?.replace(".", "")?.toIntOrNull()
    
                Episode(
                    data = epHref,
                    name = epName,
                    season = epSeason,
                    episode = epEpisode
                )
            }
    
            newTvSeriesLoadResponse(title, cleanUrl, TvType.TvSeries, episodes) {
                this.posterUrl = poster
                this.year = year
                this.plot = description
                this.tags = tags
                this.rating = rating
                this.duration = duration
            }
        } else {
            val title = document.selectXpath("//div[@class='g-title'][2]/div").text().trim()
    
            newMovieLoadResponse(title, cleanUrl, TvType.Movie, cleanUrl) {
                this.posterUrl = poster
                this.year = year
                this.plot = description
                this.tags = tags
                this.rating = rating
                this.duration = duration
            }
        }
    }

    override suspend fun loadLinks(
      data: String,
      isCasting: Boolean,
      subtitleCallback: (SubtitleFile) -> Unit,
      callback: (ExtractorLink) -> Unit
  ): Boolean {
      Log.d("DZP", "Loading URL: $data")
    try {
        // URL'yi temizle ve düzelt
        val cleanUrl = url.trim().removeSuffix("/")
        Log.d("DZP", "Loading URL: $cleanUrl")

        // Sayfayı çek
        val document = app.get(
            cleanUrl,
            headers = mapOf(
                "User-Agent" to USER_AGENT,
                "Accept" to "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language" to "tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3",
                "Connection" to "keep-alive",
                "Upgrade-Insecure-Requests" to "1"
            ),
            timeout = 25 // Timeout süresini artır
        ).document

        val title = if (cleanUrl.contains("/dizi/")) {
            document.selectFirst("div.cover h5")?.text()
        } else {
            document.selectXpath("//div[@class='g-title'][2]/div")?.text()?.trim()
        } ?: throw Exception("Title not found")

        val poster = fixUrlNull(document.selectFirst("[property='og:image']")?.attr("content"))
        val year = document.selectXpath("//div[text()='Yapım Yılı']//following-sibling::div")?.text()?.trim()?.toIntOrNull()
        val description = document.selectFirst("div.summary p")?.text()?.trim()
        val tags = document.selectXpath("//div[text()='Türler']//following-sibling::div")?.text()?.trim()?.split(" ")?.mapNotNull { it.trim() }
        val rating = document.selectXpath("//div[text()='IMDB Puanı']//following-sibling::div")?.text()?.trim()?.toRatingInt()
        val duration = Regex("(\\d+)").find(document.selectXpath("//div[text()='Ortalama Süre']//following-sibling::div")?.text() ?: "")?.value?.toIntOrNull()

        return if (cleanUrl.contains("/dizi/")) {
            val episodes = document.select("div.episode-item").mapNotNull {
                val epName = it.selectFirst("div.name")?.text()?.trim() ?: return@mapNotNull null
                val epHref = fixUrlNull(it.selectFirst("a")?.attr("href"))?.removeSuffix("/") ?: return@mapNotNull null
                val epText = it.selectFirst("div.episode")?.text()?.trim() ?: return@mapNotNull null
                
                val seasonMatch = Regex("(\\d+)\\. Sezon").find(epText)
                val episodeMatch = Regex("(\\d+)\\. Bölüm").find(epText)
                
                val epSeason = seasonMatch?.groupValues?.get(1)?.toIntOrNull()
                val epNumber = episodeMatch?.groupValues?.get(1)?.toIntOrNull()

                Episode(
                    data = epHref,
                    name = epName,
                    season = epSeason,
                    episode = epNumber
                )
            }

            newTvSeriesLoadResponse(title, cleanUrl, TvType.TvSeries, episodes) {
                this.posterUrl = poster
                this.year = year
                this.plot = description
                this.tags = tags
                this.rating = rating
                this.duration = duration
            }
        } else {
            newMovieLoadResponse(title, cleanUrl, TvType.Movie, cleanUrl) {
                this.posterUrl = poster
                this.year = year
                this.plot = description
                this.tags = tags
                this.rating = rating
                this.duration = duration
            }
        }
    } catch (e: Exception) {
        Log.e("DZP", "Error during load: ${e.message}", e)
        return null
    }
}
}