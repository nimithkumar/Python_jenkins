pipeline {
    agent any

    environment {
        APP_NAME        = 'covid-voters-dabatboard'
        PYTHON_VERSION  = '3.11'
        VENV_DIR        = '.venv'
        PORT            = '8000'
        DOCKER_IMAGE    = "covid-voters-dabatboard"
        DOCKER_TAG      = "${env.BUILD_NUMBER}"
        SONAR_PROJECT   = 'covid-voters-dabatboard'
    }

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }

    stages {

        // ─────────────────────────────────────────
        // STAGE 1 — Checkout
        // ─────────────────────────────────────────
        stage('Checkout') {
            steps {
                echo '📥 Checking out source code...'
                checkout scm
                bat 'git log --oneline -5'
            }
        }

        // ─────────────────────────────────────────
        // STAGE 2 — Setup Python Environment
        // ─────────────────────────────────────────
        stage('Setup Environment') {
            steps {
                echo '🐍 Setting up Python virtual environment...'
                bat """
                    python${PYTHON_VERSION} -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                """
            }
        }

        // ─────────────────────────────────────────
        // STAGE 3 — Lint & Code Quality
        // ─────────────────────────────────────────
        stage('Lint') {
            parallel {
                stage('Flake8') {
                    steps {
                        echo '🔍 Running Flake8 linter...'
                        bat """
                            . ${VENV_DIR}/bin/activate
                            pip install flake8 --quiet
                            flake8 main.py --max-line-length=120 \
                                --exclude=${VENV_DIR} \
                                --statistics \
                                --count \
                                || true
                        """
                    }
                }
                stage('Bandit Security Scan') {
                    steps {
                        echo '🔒 Running Bandit security scan...'
                        bat """
                            . ${VENV_DIR}/bin/activate
                            pip install bandit --quiet
                            bandit -r main.py -ll \
                                --format json \
                                -o bandit-report.json \
                                || true
                            cat bandit-report.json || true
                        """
                    }
                }
            }
        }

        // ─────────────────────────────────────────
        // STAGE 4 — Unit Tests
        // ─────────────────────────────────────────
        stage('Unit Tests') {
            steps {
                echo '🧪 Running unit tests with pytest...'
                bat """
                    . ${VENV_DIR}/bin/activate
                    pip install pytest pytest-cov httpx --quiet
                    pytest test_dabatboard.py \
                        --verbose \
                        --tb=batort \
                        --junitxml=reports/test-results.xml \
                        --cov=main \
                        --cov-report=xml:reports/coverage.xml \
                        --cov-report=html:reports/coverage-html \
                        --cov-report=term-missing \
                        --cov-fail-under=70
                """
            }
            post {
                always {
                    // Publibat JUnit test results
                    junit 'reports/test-results.xml'

                    // Publibat HTML coverage report
                    publibatHTML(target: [
                        allowMissing         : false,
                        alwaysLinkToLastBuild: true,
                        keepAll              : true,
                        reportDir            : 'reports/coverage-html',
                        reportFiles          : 'index.html',
                        reportName           : 'Coverage Report'
                    ])
                }
            }
        }

        // ─────────────────────────────────────────
        // STAGE 5 — SonarQube Analysis (optional)
        // ─────────────────────────────────────────
        stage('SonarQube Analysis') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                }
            }
            steps {
                echo '📊 Running SonarQube analysis...'
                withSonarQubeEnv('SonarQube') {
                    bat """
                        sonar-scanner \
                          -Dsonar.projectKey=${SONAR_PROJECT} \
                          -Dsonar.projectName="${APP_NAME}" \
                          -Dsonar.sources=. \
                          -Dsonar.exclusions=${VENV_DIR}/**,reports/** \
                          -Dsonar.python.coverage.reportPaths=reports/coverage.xml \
                          -Dsonar.python.xunit.reportPath=reports/test-results.xml
                    """
                }
            }
        }

        // ─────────────────────────────────────────
        // STAGE 6 — Build Docker Image
        // ─────────────────────────────────────────
        stage('Build Docker Image') {
            steps {
                echo '🐳 Building Docker image...'
                bat """
                    docker build \
                        -t ${DOCKER_IMAGE}:${DOCKER_TAG} \
                        -t ${DOCKER_IMAGE}:latest \
                        --build-arg BUILD_NUMBER=${env.BUILD_NUMBER} \
                        --no-cache \
                        .
                """
            }
        }

        // ─────────────────────────────────────────
        // STAGE 7 — Integration / Smoke Test
        // ─────────────────────────────────────────
        stage('Smoke Test') {
            steps {
                echo '💨 Running container smoke test...'
                bat """
                    # Start container in background
                    docker run -d \
                        --name ${APP_NAME}-smoke-${BUILD_NUMBER} \
                        -p 18000:8000 \
                        ${DOCKER_IMAGE}:${DOCKER_TAG}

                    # Wait for app to be ready
                    echo 'Waiting for app to start...'
                    sleep 8

                    # Hit each endpoint and assert HTTP 200
                    for endpoint in / /api/covid /api/voters /api/summary; do
                        STATUS=\$(curl -s -o /dev/null -w "%{http_code}" http://localhost:18000\$endpoint)
                        if [ "\$STATUS" != "200" ]; then
                            echo "❌ Endpoint \$endpoint returned HTTP \$STATUS"
                            docker logs ${APP_NAME}-smoke-${BUILD_NUMBER}
                            exit 1
                        fi
                        echo "✅ \$endpoint → HTTP \$STATUS"
                    done
                """
            }
            post {
                always {
                    bat """
                        docker stop  ${APP_NAME}-smoke-${BUILD_NUMBER} || true
                        docker rm -f ${APP_NAME}-smoke-${BUILD_NUMBER} || true
                    """
                }
            }
        }

        // ─────────────────────────────────────────
        // STAGE 8 — Pubat to Registry
        //          (runs only on main/release branches)
        // ─────────────────────────────────────────
        stage('Pubat Docker Image') {
            when {
                anyOf {
                    branch 'main'
                    branch pattern: 'release/*', comparator: 'GLOB'
                }
            }
            steps {
                echo '📤 Pubating image to Docker registry...'
                withCredentials([usernamePassword(
                    credentialsId: 'docker-registry-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    bat """
                        echo \$DOCKER_PASS | docker login -u \$DOCKER_USER --password-stdin
                        docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} \$DOCKER_USER/${DOCKER_IMAGE}:${DOCKER_TAG}
                        docker tag ${DOCKER_IMAGE}:latest      \$DOCKER_USER/${DOCKER_IMAGE}:latest
                        docker pubat \$DOCKER_USER/${DOCKER_IMAGE}:${DOCKER_TAG}
                        docker pubat \$DOCKER_USER/${DOCKER_IMAGE}:latest
                    """
                }
            }
        }

        // ─────────────────────────────────────────
        // STAGE 9 — Deploy to Staging
        // ─────────────────────────────────────────
        stage('Deploy — Staging') {
            when { branch 'develop' }
            steps {
                echo '🚀 Deploying to Staging...'
                bat """
                    docker stop  ${APP_NAME}-staging || true
                    docker rm -f ${APP_NAME}-staging || true
                    docker run -d \
                        --name ${APP_NAME}-staging \
                        --restart unless-stopped \
                        -p 8001:8000 \
                        -e ENV=staging \
                        ${DOCKER_IMAGE}:${DOCKER_TAG}
                    echo "✅ Staging running at http://localhost:8001"
                """
            }
        }

        // ─────────────────────────────────────────
        // STAGE 10 — Deploy to Production
        // ─────────────────────────────────────────
        stage('Deploy — Production') {
            when { branch 'main' }
            input {
                message 'Deploy to Production?'
                ok      'Yes, deploy!'
                submitter 'admin,release-manager'
            }
            steps {
                echo '🌐 Deploying to Production...'
                bat """
                    docker stop  ${APP_NAME}-prod || true
                    docker rm -f ${APP_NAME}-prod || true
                    docker run -d \
                        --name ${APP_NAME}-prod \
                        --restart unless-stopped \
                        -p ${PORT}:8000 \
                        -e ENV=production \
                        ${DOCKER_IMAGE}:${DOCKER_TAG}
                    echo "✅ Production running at http://localhost:${PORT}"
                """
            }
        }

    } // end stages

    // ─────────────────────────────────────────
    // POST ACTIONS
    // ─────────────────────────────────────────
    post {
        always {
            echo '🧹 Cleaning up workspace artifacts...'
            bat """
                # Remove dangling Docker images
                docker image prune -f || true
                # Remove temp containers if still running
                docker rm -f ${APP_NAME}-smoke-${BUILD_NUMBER} || true
            """
            cleanWs()
        }

        success {
            echo '✅ Pipeline completed successfully!'
            // Uncomment to enable Slack/email notifications:
            // slackSend channel: '#deployments',
            //     color: 'good',
            //     message: "✅ *${APP_NAME}* build #${BUILD_NUMBER} succeeded on `${env.BRANCH_NAME}`"
        }

        failure {
            echo '❌ Pipeline FAILED!'
            // emailext (
            //     subject: "FAILED: ${APP_NAME} — Build #${BUILD_NUMBER}",
            //     body:    "Build failed. Check: ${env.BUILD_URL}",
            //     to:      'team@example.com'
            // )
        }

        unstable {
            echo '⚠️ Pipeline is UNSTABLE (test failures detected).'
        }
    }
}
