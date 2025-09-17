# Stage 1: Build the Kotlin Spring Boot app with Gradle
FROM gradle:8.5-jdk21 AS build
WORKDIR /app
COPY backend .
RUN gradle build -x test

# Stage 2: Run the app with JDK 21
FROM openjdk:21-jdk-slim
WORKDIR /app
COPY --from=build /app/build/libs/*.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
