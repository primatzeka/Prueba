package com.primatzeka

import android.util.Log
import org.jsoup.nodes.Element
import com.lagradost.cloudstream3.*
import com.lagradost.cloudstream3.utils.*
import com.lagradost.cloudstream3.LoadResponse.Companion.addActors
import com.lagradost.cloudstream3.LoadResponse.Companion.addTrailer

class HDFilmCehennemi : MainAPI() {
    override var mainUrl              = "https://hdfilmcehennemi13.org"
    override var name                 = "NewNameValue"
    override val hasMainPage          = true
    override var lang                 = "tr"
    override val hasQuickSearch       = false
    override val supportedTypes       = setOf(TvType.TvSeries)

    override val mainPage = mainPageOf(
        "${mainUrl}/dizi-arsivi/page/SAYFA/?tur=Aile"                 to "Aile",
        "${mainUrl}/dizi-arsivi/page/SAYFA/?tur=Aksiyon"              to "Aksiyon",
        "${mainUrl}/dizi-arsivi/page/SAYFA/?tur=Animasyon"            to "Animasyon",
        "${mainUrl}/dizi-arsivi/page/SAYFA/?tur=Belgesel"             to "Belgesel",
        "${mainUrl}/dizi-arsivi/page/SAYFA/?tur=Bilim+Kurgu"          to "Bilim Kurgu",
        "${mainUrl}/dizi-arsivi/page/SAYFA/?tur=Dram"                 to "Dram",
        "${mainUrl}/dizi-arsivi/page/SAYFA/?tur=Fantazi"              to "Fantazi",
        "${mainUrl}/dizi-arsivi/page/SAYFA/?tur=Gizem"                to "Gizem",
        "${mainUrl}/dizi-arsivi/page/SAYFA/?tur=Komedi"               to "Komedi",
        "${mainUrl}/dizi-arsivi/page/SAYFA/?tur=Macera"               to "Macera",
        "${mainUrl}/dizi-arsivi/page/SAYFA/?tur=Sava%C5%9F"           to "Savaş",
        "${mainUrl}/dizi-arsivi/page/SAYFA/?tur=Su%C3%A7"             to "Suç",
        "${mainUrl}/dizi-arsivi/page/SAYFA/?tur=Vah%C5%9Fi+Bat%C4%B1" to "Vahşi Batı"
    )

    override suspend fun getMainPage(page: Int, request: MainPageRequest): HomePageResponse {
        val url      = request.data.replace("SAYFA", "$page")
        val document = app.get(url).document
        val home     = document.select("div.single-item").mapNotNull { it.toMainPageResult() }

        return newHomePageResponse(request.name, home)
    }

    private fun Element.toMainPageResult(): SearchResponse? {
        val title     = this.selectFirst("div.categorytitle a")?.text() ?: return null
        val href      = fixUrlNull(this.selectFirst("div.categorytitle a")?.attr("href")) ?: return null
        val posterUrl = fixUrlNull(this.selectFirst("img")?.attr("src"))

        return newTvSeriesSearchResponse(title, href, TvType.TvSeries) { this.posterUrl = posterUrl }
    }

    override suspend fun search(query: String): List<SearchResponse> {
        val document = app.get("${mainUrl}/?s=${query}").document

        return document.select("div.incontent div#list-series").mapNotNull { it.toMainPageResult() }
    }

    override suspend fun quickSearch(query: String): List<SearchResponse> = search(query)

    override suspend fun load(url: String): LoadResponse? {
        val document = app.get(url).document

        val title = document.selectFirst("h1")?.text()?.trim()
            ?.replace("İzle - Hdfilmcehennemi", "", ignoreCase = true)
            ?.trim() ?: return null
        val poster          = fixUrlNull(document.selectFirst("div.category_image img")?.attr("src"))
        val description     = document.selectFirst("div.category_desc")?.ownText()?.trim()
        val year            = document.selectFirst("span.dizimeta:contains(Yapım Yılı)")?.nextSibling()?.toString()?.trim()?.toIntOrNull()
        val tags            = document.select("div.genres a").map { it.text() }
        val rating          = document.selectFirst("span.dizimeta:contains(IMDB)")?.nextSibling()?.toString()?.trim()?.toRatingInt()
        val actors          = document.selectFirst("span.dizimeta:contains(Oyuncular)")?.nextSibling()?.toString()?.trim()?.split(", ")?.map { Actor(it) }
        val trailer         = document.selectFirst("iframe.trailer-video")?.attr("src")

        val episodes = document.select("div.container div.bolumust").mapNotNull {
            val epName = it.selectFirst("div.baslik")?.text()?.trim() ?: return@mapNotNull null
            val epHref = it.selectFirst("a")?.attr("href")?.let { href -> fixUrlNull(href) } ?: return@mapNotNull null
            val epEpisode = Regex("""(\d+)\. Bölüm""").find(epName)?.groupValues?.get(1)?.toIntOrNull()
            val epSeason = Regex("""(\d+)\. Sezon""").find(epName)?.groupValues?.get(1)?.toIntOrNull() ?: 1
        
            newEpisode(epHref) {
                this.name = it.selectFirst("div.bolum-ismi.bolumismi")?.text()?.trim()?.replace(Regex("""[()]"""), "")?.trim() ?: epName
                this.season = epSeason
                this.episode = epEpisode
            }
        }

        return newTvSeriesLoadResponse(title, url, TvType.TvSeries, episodes) {
            this.posterUrl = poster
            this.plot      = description
            this.year      = year
            this.tags      = tags
            this.rating    = rating
            addActors(actors)
            addTrailer(trailer)
        }
    }

    override suspend fun loadLinks(data: String, isCasting: Boolean, subtitleCallback: (SubtitleFile) -> Unit, callback: (ExtractorLink) -> Unit): Boolean {
        Log.d("DZY", "data » $data")
        val document = app.get(data).document

        val itemId     = document.selectFirst("div.video div.video-container p iframe")?.attr("src")?.split("/")?.lastOrNull()?: return false
        Log.d("DZY", "itemId » $itemId")

        val subTitles  = mutableListOf<HDFilmCehennemiSubtitle>()
        val streamUrls = mutableListOf<HDFilmCehennemiStream>()
        val storage    = mainUrl.replace("www", "storage")

        document.select("span.dil.current_dil").forEach {
            val optId   = it.attr("id")

            if (optId == "turkceAltyazili") {
                subTitles.add(HDFilmCehennemiSubtitle("Turkish", "${storage}/subtitles/${itemId}/tr.vtt"))
                streamUrls.add(HDFilmCehennemiStream("Orjinal Dil", "${storage}/episodes/${itemId}/play.m3u8"))
            }

            if (optId == "ingilizceAltyazili") {
                subTitles.add(HDFilmCehennemiSubtitle("English", "${storage}/subtitles/${itemId}/en.vtt"))
                streamUrls.add(HDFilmCehennemiStream("Orjinal Dil", "${storage}/episodes/${itemId}/play.m3u8"))
            }

            if (optId == "turkceDublaj") {
                streamUrls.add(HDFilmCehennemiStream("Türkçe Dublaj", "${storage}/episodes/${itemId}_tr/play.m3u8"))
            }
        }

        for (sub in subTitles) {
            subtitleCallback.invoke(
                SubtitleFile(
                    lang = sub.name,
                    url  = fixUrl(sub.url)
                )
            )
        }

        for (stream in streamUrls) {
            callback.invoke(
                ExtractorLink(
                    source  = stream.name,
                    name    = stream.name,
                    url     = stream.url,
                    referer = "${mainUrl}/",
                    quality = Qualities.Unknown.value,
                    isM3u8  = true
                )
            )
        }

        return true
    }

    data class HDFilmCehennemiSubtitle(val name: String, val url: String)
    data class HDFilmCehennemiStream(val name: String, val url: String)
}
