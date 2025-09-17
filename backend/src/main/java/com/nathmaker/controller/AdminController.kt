package com.nathmakers.admin.backend.controller

import com.nathmakers.admin.backend.model.Admin
import com.nathmakers.admin.backend.repository.AdminRepository
import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/admin")
class AdminController(private val adminRepository: AdminRepository) {

    @GetMapping("/hello")
    fun hello(): String = "Hello from AdminController!"

    @GetMapping("/")
    fun getAllAdmins(): List<Admin> = adminRepository.findAll()

    @PostMapping("/")
    fun createAdmin(@RequestBody admin: Admin): Admin = adminRepository.save(admin)
}
