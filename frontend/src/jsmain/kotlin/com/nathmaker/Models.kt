package com.nathmaker

import kotlinx.serialization.Serializable

@Serializable
data class Product(
    val id: Int,
    val catalogueId: Int,
    val productName: String,
    val description: String? = null,
    val price: Double,
    val material: String? = null,
    val weight: String? = null,
    val imageUrls: List<String> = emptyList(),
    val isAvailable: Boolean = true,
    val createdAt: String? = null
)

@Serializable
data class Catalogue(
    val id: Int,
    val name: String,
    val description: String? = null,
    val coverImageUrl: String? = null,
    val createdAt: String? = null
)

