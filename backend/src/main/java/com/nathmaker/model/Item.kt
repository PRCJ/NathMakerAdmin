package com.nathmakers.admin.backend.model

import jakarta.persistence.*

@Entity
data class Item(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long = 0,

    var code: String = "",
    var price: Double = 0.0,
    var type: String = "",

    @ManyToOne
    @JoinColumn(name = "catalogue_id")
    var catalogue: Catalogue? = null
)
