# Stage 1: Build the Kotlin Spring Boot backend
FROM gradle:8.5-jdk21 AS build
WORKDIR /app
COPY . .
# copy the whole repo (gradle wrapper, settings, backend, frontend, etc.)
WORKDIR /app/backend
RUN gradle build -x test

# Stage 2: Run the app with JDK 21
FROM openjdk:21-jdk-slim
WORKDIR /app
COPY --from=build /app/backend/build/libs/*.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
