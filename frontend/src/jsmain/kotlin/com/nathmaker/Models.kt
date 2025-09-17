package com.nathmaker

import kotlinx.serialization.Serializable

@Serializable
data class Item(
    val id: Int,
    val code: String,
    val price: Double,
    val type: String
)

@Serializable
data class Catalogue(
    val id: Int,
    val catalogueName: String,
    val items: List<Item>
)
