package com.nathmakers.admin.backend.model

import jakarta.persistence.*

@Entity
data class Catalogue(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long = 0,

    var catalogueName: String = "",

    @OneToMany(mappedBy = "catalogue", cascade = [CascadeType.ALL], orphanRemoval = true)
    var items: MutableList<Item> = mutableListOf()
)
