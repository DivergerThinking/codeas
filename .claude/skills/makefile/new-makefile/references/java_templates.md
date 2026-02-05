# Java Makefile Templates

This file contains professional Makefile templates for Java projects.

## Basic Java Project Template

```makefile
# Project configuration
PROJECT_NAME := MyJavaProject
MAIN_CLASS := com.example.Main
SRC_DIR := src
BUILD_DIR := build
CLASSES_DIR := $(BUILD_DIR)/classes
JAR_DIR := $(BUILD_DIR)/jar
LIB_DIR := lib

# Java configuration
JAVAC := javac
JAVA := java
JAR := jar
JAVAC_FLAGS := -d $(CLASSES_DIR) -sourcepath $(SRC_DIR) -cp $(CLASSPATH)
JAVA_FLAGS := -cp $(CLASSES_DIR):$(CLASSPATH)

# Classpath (include all JARs in lib directory)
CLASSPATH := $(LIB_DIR)/*

# Find all Java source files
SOURCES := $(shell find $(SRC_DIR) -name "*.java")
CLASSES := $(SOURCES:$(SRC_DIR)/%.java=$(CLASSES_DIR)/%.class)

.PHONY: all clean compile run jar help

all: compile

help:
	@echo "Available targets:"
	@echo "  make compile   - Compile Java sources"
	@echo "  make run       - Run main class"
	@echo "  make jar       - Create JAR file"
	@echo "  make clean     - Remove compiled files"
	@echo "  make rebuild   - Clean and compile"

# Create directories
$(CLASSES_DIR):
	mkdir -p $(CLASSES_DIR)

$(JAR_DIR):
	mkdir -p $(JAR_DIR)

# Compile Java sources
compile: $(CLASSES_DIR) $(CLASSES)

$(CLASSES_DIR)/%.class: $(SRC_DIR)/%.java
	$(JAVAC) $(JAVAC_FLAGS) $<

# Run the application
run: compile
	$(JAVA) $(JAVA_FLAGS) $(MAIN_CLASS)

# Create JAR file
jar: compile $(JAR_DIR)
	$(JAR) cfm $(JAR_DIR)/$(PROJECT_NAME).jar manifest.txt -C $(CLASSES_DIR) .

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR)

rebuild: clean all
```

## Maven-style Java Project Template

```makefile
# Project configuration
PROJECT_NAME := my-java-app
VERSION := 1.0.0
MAIN_CLASS := com.example.App

# Directory structure (Maven-style)
SRC_DIR := src/main/java
TEST_DIR := src/test/java
RESOURCES_DIR := src/main/resources
TEST_RESOURCES_DIR := src/test/resources
TARGET_DIR := target
CLASSES_DIR := $(TARGET_DIR)/classes
TEST_CLASSES_DIR := $(TARGET_DIR)/test-classes
JAR_FILE := $(TARGET_DIR)/$(PROJECT_NAME)-$(VERSION).jar

# Java configuration
JAVAC := javac
JAVA := java
JAR := jar
JAVAC_FLAGS := -encoding UTF-8 -source 11 -target 11
JAVA_FLAGS := -Xmx512m

# Dependencies
LIB_DIR := lib
TEST_LIB_DIR := lib/test
CLASSPATH := $(CLASSES_DIR):$(LIB_DIR)/*
TEST_CLASSPATH := $(TEST_CLASSES_DIR):$(CLASSES_DIR):$(LIB_DIR)/*:$(TEST_LIB_DIR)/*

# Find source files
SOURCES := $(shell find $(SRC_DIR) -name "*.java" 2>/dev/null)
TEST_SOURCES := $(shell find $(TEST_DIR) -name "*.java" 2>/dev/null)

.PHONY: all clean compile test package run install help

all: package

help:
	@echo "Maven-style Java project targets:"
	@echo "  make compile    - Compile main sources"
	@echo "  make test       - Run tests"
	@echo "  make package    - Create JAR package"
	@echo "  make run        - Run application"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make install    - Install to local repository"

# Create directories
$(CLASSES_DIR) $(TEST_CLASSES_DIR) $(TARGET_DIR):
	mkdir -p $@

# Compile main sources
compile: $(CLASSES_DIR)
	@echo "Compiling main sources..."
	@if [ -n "$(SOURCES)" ]; then \
		$(JAVAC) $(JAVAC_FLAGS) -d $(CLASSES_DIR) -cp $(CLASSPATH) $(SOURCES); \
	fi
	@if [ -d "$(RESOURCES_DIR)" ]; then \
		cp -r $(RESOURCES_DIR)/* $(CLASSES_DIR)/; \
	fi
	@echo "✓ Compilation complete"

# Compile test sources
compile-tests: compile $(TEST_CLASSES_DIR)
	@echo "Compiling test sources..."
	@if [ -n "$(TEST_SOURCES)" ]; then \
		$(JAVAC) $(JAVAC_FLAGS) -d $(TEST_CLASSES_DIR) -cp $(TEST_CLASSPATH) $(TEST_SOURCES); \
	fi
	@if [ -d "$(TEST_RESOURCES_DIR)" ]; then \
		cp -r $(TEST_RESOURCES_DIR)/* $(TEST_CLASSES_DIR)/; \
	fi

# Run tests (using JUnit)
test: compile-tests
	@echo "Running tests..."
	$(JAVA) -cp $(TEST_CLASSPATH) org.junit.runner.JUnitCore $$(find $(TEST_CLASSES_DIR) -name "*Test.class" | sed 's|$(TEST_CLASSES_DIR)/||g' | sed 's|\.class$$||g' | sed 's|/|.|g')

# Create JAR package
package: compile $(TARGET_DIR)
	@echo "Creating JAR package..."
	$(JAR) cfe $(JAR_FILE) $(MAIN_CLASS) -C $(CLASSES_DIR) .
	@if [ -d "$(LIB_DIR)" ]; then \
		mkdir -p $(TARGET_DIR)/lib; \
		cp $(LIB_DIR)/*.jar $(TARGET_DIR)/lib/; \
	fi
	@echo "✓ Package created: $(JAR_FILE)"

# Run application
run: package
	$(JAVA) $(JAVA_FLAGS) -jar $(JAR_FILE)

# Install to local repository (simplified)
install: package
	@echo "Installing to local repository..."
	mkdir -p ~/.m2/repository/com/example/$(PROJECT_NAME)/$(VERSION)
	cp $(JAR_FILE) ~/.m2/repository/com/example/$(PROJECT_NAME)/$(VERSION)/

# Clean build artifacts
clean:
	rm -rf $(TARGET_DIR)

.PHONY: verify
verify: test
	@echo "✓ Verification complete"
```

## Spring Boot Application Template

```makefile
# Spring Boot project configuration
PROJECT_NAME := spring-boot-app
VERSION := 1.0.0
MAIN_CLASS := com.example.Application
JAVA_VERSION := 17

# Directories
SRC_DIR := src/main/java
RESOURCES_DIR := src/main/resources
TEST_DIR := src/test/java
TARGET_DIR := target
CLASSES_DIR := $(TARGET_DIR)/classes
JAR_FILE := $(TARGET_DIR)/$(PROJECT_NAME)-$(VERSION).jar

# Java tools
JAVAC := javac
JAVA := java
MVN := mvn

# Application settings
SPRING_PROFILE := dev
SERVER_PORT := 8080

.PHONY: all build run test clean package deploy help

all: build

help:
	@echo "Spring Boot application targets:"
	@echo "  make build      - Build the application"
	@echo "  make run        - Run the application"
	@echo "  make dev        - Run in development mode"
	@echo "  make test       - Run tests"
	@echo "  make package    - Create executable JAR"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make docker     - Build Docker image"

# Build with Maven/Gradle wrapper
build:
	@if [ -f "mvnw" ]; then \
		./mvnw clean compile; \
	elif [ -f "gradlew" ]; then \
		./gradlew build; \
	else \
		echo "No build tool wrapper found"; \
		exit 1; \
	fi

# Run application
run: build
	@if [ -f "mvnw" ]; then \
		./mvnw spring-boot:run; \
	elif [ -f "gradlew" ]; then \
		./gradlew bootRun; \
	else \
		$(JAVA) -jar $(JAR_FILE); \
	fi

# Run in development mode
dev:
	@if [ -f "mvnw" ]; then \
		./mvnw spring-boot:run -Dspring-boot.run.profiles=$(SPRING_PROFILE); \
	else \
		./gradlew bootRun --args='--spring.profiles.active=$(SPRING_PROFILE)'; \
	fi

# Run tests
test:
	@if [ -f "mvnw" ]; then \
		./mvnw test; \
	else \
		./gradlew test; \
	fi

# Create executable JAR
package:
	@if [ -f "mvnw" ]; then \
		./mvnw clean package -DskipTests; \
	else \
		./gradlew bootJar; \
	fi

# Clean
clean:
	@if [ -f "mvnw" ]; then \
		./mvnw clean; \
	else \
		./gradlew clean; \
	fi
	rm -rf $(TARGET_DIR)

# Docker build
docker: package
	docker build -t $(PROJECT_NAME):$(VERSION) .

# Database migrations (Flyway/Liquibase)
db-migrate:
	@if [ -f "mvnw" ]; then \
		./mvnw flyway:migrate; \
	fi

db-clean:
	@if [ -f "mvnw" ]; then \
		./mvnw flyway:clean; \
	fi
```

## Multi-module Java Project Template

```makefile
# Multi-module project configuration
PROJECT_NAME := multi-module-app
VERSION := 1.0.0

# Modules
MODULES := common service-a service-b web

# Build tool
MVN := mvn
GRADLE := gradle

.PHONY: all build test clean install deploy help $(MODULES)

all: build

help:
	@echo "Multi-module project targets:"
	@echo "  make build          - Build all modules"
	@echo "  make test           - Test all modules"
	@echo "  make clean          - Clean all modules"
	@echo "  make install        - Install all modules"
	@echo "  make [module-name]  - Build specific module"
	@echo ""
	@echo "Available modules: $(MODULES)"

# Build all modules
build:
	@echo "Building all modules..."
	@for module in $(MODULES); do \
		echo "Building $$module..."; \
		$(MAKE) -C $$module build; \
	done
	@echo "✓ All modules built"

# Test all modules
test:
	@echo "Testing all modules..."
	@for module in $(MODULES); do \
		echo "Testing $$module..."; \
		$(MAKE) -C $$module test; \
	done
	@echo "✓ All tests passed"

# Clean all modules
clean:
	@echo "Cleaning all modules..."
	@for module in $(MODULES); do \
		$(MAKE) -C $$module clean; \
	done
	rm -rf target

# Install all modules
install:
	@echo "Installing all modules..."
	@for module in $(MODULES); do \
		$(MAKE) -C $$module install; \
	done

# Build specific module
$(MODULES):
	@echo "Building module: $@"
	$(MAKE) -C $@ build

# Dependency graph
deps:
	@echo "Module dependencies:"
	@echo "  common (base)"
	@echo "  service-a -> common"
	@echo "  service-b -> common"
	@echo "  web -> service-a, service-b"
```

## Gradle-based Project Template

```makefile
# Gradle project configuration
PROJECT_NAME := gradle-app
GRADLE := ./gradlew

.PHONY: all build run test clean assemble help

all: build

help:
	@echo "Gradle project targets:"
	@echo "  make build      - Build project"
	@echo "  make run        - Run application"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Clean build"
	@echo "  make assemble   - Assemble artifacts"
	@echo "  make check      - Run checks"

build:
	$(GRADLE) build

run:
	$(GRADLE) run

test:
	$(GRADLE) test --info

clean:
	$(GRADLE) clean

assemble:
	$(GRADLE) assemble

check:
	$(GRADLE) check

bootRun:
	$(GRADLE) bootRun

tasks:
	$(GRADLE) tasks
```
