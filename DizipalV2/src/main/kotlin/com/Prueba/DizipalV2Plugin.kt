package com.primatzeka

import com.lagradost.cloudstream3.plugins.CloudstreamPlugin
import com.lagradost.cloudstream3.plugins.Plugin
import android.content.Context

@CloudstreamPlugin
class DiziPalV2Plugin: Plugin() {
    override fun load(context: Context) {
        registerMainAPI(DiziPalV2())
        registerExtractorAPI(ContentX())
        registerExtractorAPI(Dplayer82())
        registerExtractorAPI(FourCX())
        registerExtractorAPI(PlayRu())
        registerExtractorAPI(FourPlayRu())
        registerExtractorAPI(FourPichive())
        registerExtractorAPI(Pichive())
    }
}