pipeline {
    agent any

    environment {
        APP_NAME     = 'covid-voters-dashboard'
        VENV_DIR     = 'venv'
        PORT         = '8000'
        DOCKER_IMAGE = 'covid-voters-dashboard'
        DOCKER_TAG   = "${env.BUILD_NUMBER}"
    }

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {

        // ─────────────────────────────
        // Checkout
        // ─────────────────────────────
        stage('Checkout') {
            steps {
                checkout scm
                bat 'git log --oneline -5'
            }
        }

        // ─────────────────────────────
        // Setup Python Environment
        // ─────────────────────────────
        stage('Setup Python') {
            steps {
                bat """
                    python -m venv %VENV_DIR%
                    %VENV_DIR%\\Scripts\\python -m pip install --upgrade pip
                    %VENV_DIR%\\Scripts\\python -m pip install -r requirements.txt
                """
            }
        }

        // ─────────────────────────────
        // Run Unit Tests
        // ─────────────────────────────
        stage('Unit Tests') {
            steps {
                bat """
                    %VENV_DIR%\\Scripts\\python -m pip install pytest pytest-cov
                    %VENV_DIR%\\Scripts\\pytest test_dashboard.py ^
                        --junitxml=reports\\test-results.xml ^
                        --cov=main ^
                        --cov-report=xml:reports\\coverage.xml ^
                        --cov-report=html:reports\\coverage-html
                """
            }
            post {
                always {
                    junit 'reports/test-results.xml'
                    publishHTML(target: [
                        reportDir: 'reports/coverage-html',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report',
                        keepAll: true,
                        alwaysLinkToLastBuild: true
                    ])
                }
            }
        }

        // ─────────────────────────────
        // Build Docker Image
        // ─────────────────────────────
        stage('Build Docker') {
            steps {
                bat """
                    docker build -t %DOCKER_IMAGE%:%DOCKER_TAG% .
                    docker tag %DOCKER_IMAGE%:%DOCKER_TAG% %DOCKER_IMAGE%:latest
                """
            }
        }

        // ─────────────────────────────
        // Smoke Test
        // ─────────────────────────────
        stage('Smoke Test') {
            steps {
                bat """
                    docker run -d --name %APP_NAME%-test -p 18000:8000 %DOCKER_IMAGE%:%DOCKER_TAG%
                    timeout /t 8
                    curl -f http://localhost:18000/ || exit 1
                """
            }
            post {
                always {
                    bat """
                        docker stop %APP_NAME%-test || exit 0
                        docker rm -f %APP_NAME%-test || exit 0
                    """
                }
            }
        }

        // ─────────────────────────────
        // Push to Docker Hub
        // ─────────────────────────────
        stage('Push Docker Image') {
            when { branch 'main' }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'docker-registry-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    bat """
                        echo %DOCKER_PASS% | docker login -u %DOCKER_USER% --password-stdin
                        docker tag %DOCKER_IMAGE%:%DOCKER_TAG% %DOCKER_USER%/%DOCKER_IMAGE%:%DOCKER_TAG%
                        docker push %DOCKER_USER%/%DOCKER_IMAGE%:%DOCKER_TAG%
                    """
                }
            }
        }

        // ─────────────────────────────
        // Deploy
        // ─────────────────────────────
        stage('Deploy') {
            when { branch 'main' }
            steps {
                bat """
                    docker stop %APP_NAME%-prod || exit 0
                    docker rm -f %APP_NAME%-prod || exit 0
                    docker run -d --name %APP_NAME%-prod -p %PORT%:8000 %DOCKER_IMAGE%:%DOCKER_TAG%
                """
            }
        }
    }

    post {
        always {
            cleanWs()
        }

        success {
            echo "Build Successful!"
        }

        failure {
            echo "Build Failed!"
        }
    }
}