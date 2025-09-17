package com.nathmakers.admin.backend.repository

import com.nathmakers.admin.backend.model.Admin
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.stereotype.Repository

@Repository
interface AdminRepository : JpaRepository<Admin, Long>
