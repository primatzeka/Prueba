package com.primatzeka

import com.lagradost.cloudstream3.plugins.CloudstreamPlugin
import com.lagradost.cloudstream3.plugins.Plugin
import android.content.Context

@CloudstreamPlugin
class SinefilPlugin: Plugin() {
    override fun load(context: Context) {
        registerMainAPI(Sinefil())
        registerExtractorAPI(ContentX())
        registerExtractorAPI(Hotlinger())
        registerExtractorAPI(FourCX())
        registerExtractorAPI(PlayRu())
        registerExtractorAPI(FourPlayRu())
        registerExtractorAPI(FourPichive())
        registerExtractorAPI(Pichive())
    }
}