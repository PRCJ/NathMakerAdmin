package com.nathmaker.config

import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import org.springframework.security.config.annotation.web.builders.HttpSecurity
import org.springframework.security.web.SecurityFilterChain

@Configuration
class SecurityConfig {

    @Bean
    fun filterChain(http: HttpSecurity): SecurityFilterChain {
        http
            .csrf { it.disable() } // 👈 disable CSRF for testing POST from curl/browser
            .authorizeHttpRequests {
                it.requestMatchers("/admin/**").permitAll()
                it.requestMatchers("/products/**").permitAll()
                it.requestMatchers("/api/catalogue/**").permitAll() // 👈 allow catalogue API
                    .anyRequest().authenticated()
            }
        return http.build()
    }
}
