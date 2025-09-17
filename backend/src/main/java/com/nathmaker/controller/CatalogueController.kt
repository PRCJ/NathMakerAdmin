package com.nathmakers.admin.backend.controller

import com.nathmakers.admin.backend.model.Catalogue
import com.nathmakers.admin.backend.repository.CatalogueRepository
import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/api/catalogue")
class CatalogueController(
    private val catalogueRepository: CatalogueRepository
) {

    // POST /api/catalogue
    @PostMapping
    fun createCatalogue(@RequestBody catalogue: Catalogue): Catalogue {
        // Link each item to the catalogue before saving
        catalogue.items.forEach { it.catalogue = catalogue }
        return catalogueRepository.save(catalogue)
    }

    // GET /api/catalogue
    @GetMapping
    fun getAllCatalogues(): List<Catalogue> {
        return catalogueRepository.findAll()
    }
}
