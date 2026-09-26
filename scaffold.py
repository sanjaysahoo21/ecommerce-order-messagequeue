import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip())

# COMMON DOCKERFILE
dockerfile_template = """
FROM eclipse-temurin:21-jdk-alpine AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
# Using maven wrapper from parent if possible, or just maven
# Assuming we can just install maven
RUN apk add --no-cache maven
RUN mvn clean package -DskipTests

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
ENTRYPOINT ["java", "-jar", "app.jar"]
"""

services = [
    ('order-service', 'orderservice', 'web,data-jpa,amqp,postgresql'),
    ('payment-service', 'paymentservice', 'data-jpa,amqp,postgresql'),
    ('inventory-service', 'inventoryservice', 'data-jpa,amqp,postgresql'),
    ('shipping-service', 'shippingservice', 'data-jpa,amqp,postgresql'),
    ('notification-service', 'notificationservice', 'amqp')
]

for svc, pkg, deps in services:
    # Dockerfile
    write_file(f"{svc}/Dockerfile", dockerfile_template)
    
    # POM
    deps_xml = ""
    for dep in deps.split(','):
        if dep == 'web':
            deps_xml += "<dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-web</artifactId></dependency>\n"
        elif dep == 'data-jpa':
            deps_xml += "<dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-data-jpa</artifactId></dependency>\n"
        elif dep == 'amqp':
            deps_xml += "<dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-amqp</artifactId></dependency>\n"
        elif dep == 'postgresql':
            deps_xml += "<dependency><groupId>org.postgresql</groupId><artifactId>postgresql</artifactId><scope>runtime</scope></dependency>\n"
            
    pom_content = f"""
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
	<modelVersion>4.0.0</modelVersion>
	<parent>
		<groupId>com.sanju</groupId>
		<artifactId>ecommerceOrderFullfillment</artifactId>
		<version>0.0.1-SNAPSHOT</version>
	</parent>
	<artifactId>{svc}</artifactId>
	<name>{svc}</name>
	<dependencies>
		{deps_xml}
	</dependencies>
	<build>
		<plugins>
			<plugin>
				<groupId>org.springframework.boot</groupId>
				<artifactId>spring-boot-maven-plugin</artifactId>
			</plugin>
		</plugins>
	</build>
</project>
"""
    write_file(f"{svc}/pom.xml", pom_content)
    
    # Application Properties
    props = f"""
spring.application.name={svc}
"""
    if 'postgresql' in deps:
        props += f"""
spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=true
"""
    write_file(f"{svc}/src/main/resources/application.properties", props)

    # Main Application
    class_name = svc.replace('-', ' ').title().replace(' ', '') + "Application"
    main_content = f"""
package com.example.{pkg};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class {class_name} {{
    public static void main(String[] args) {{
        SpringApplication.run({class_name}.class, args);
    }}
}}
"""
    write_file(f"{svc}/src/main/java/com/example/{pkg}/{class_name}.java", main_content)

print("Scaffolding complete.")
