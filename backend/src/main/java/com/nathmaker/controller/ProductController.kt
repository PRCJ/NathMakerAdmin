package com.nathmakers.admin.backend.controller

import com.nathmakers.admin.backend.model.Product
import com.nathmakers.admin.backend.repository.ProductRepository
import org.springframework.web.bind.annotation.*

@RestController
@RequestMapping("/products")   // 👈 Root path
class ProductController(
    private val productRepository: ProductRepository
) {

    // GET /products
    @GetMapping
    fun getAllProducts(): List<Product> {
        return productRepository.findAll()
    }

    // GET /products/{id}
    @GetMapping("/{id}")
    fun getProductById(@PathVariable id: Long): Product? {
        return productRepository.findById(id).orElse(null)
    }

    // POST /products
    @PostMapping
    fun addProduct(@RequestBody product: Product): Product {
        return productRepository.save(product)
    }

    // PUT /products/{id}
    @PutMapping("/{id}")
    fun updateProduct(@PathVariable id: Long, @RequestBody updated: Product): Product? {
        return productRepository.findById(id).map { existing ->
            val newProduct = existing.copy(
                name = updated.name,
                price = updated.price
            )
            productRepository.save(newProduct)
        }.orElse(null)
    }

    // DELETE /products/{id}
    @DeleteMapping("/{id}")
    fun deleteProduct(@PathVariable id: Long): String {
        return if (productRepository.existsById(id)) {
            productRepository.deleteById(id)
            "Product deleted successfully"
        } else {
            "Product not found"
        }
    }
}
