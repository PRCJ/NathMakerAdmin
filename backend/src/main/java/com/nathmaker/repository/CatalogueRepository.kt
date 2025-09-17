package com.nathmakers.admin.backend.repository

import com.nathmakers.admin.backend.model.Catalogue
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.stereotype.Repository

@Repository
interface CatalogueRepository : JpaRepository<Catalogue, Long>
