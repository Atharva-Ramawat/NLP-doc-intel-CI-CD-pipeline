pipeline {
    agent any
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '5'))
    }
    
    environment {
        IMAGE_REPO = "atharvaramawat/nlp-doc-intel"
    }
    
    stages {
        stage('Checkout & Check Trigger') {
            steps {
                checkout scm
                script {
                    def commitMsg = sh(script: 'git log -1 --pretty=%B', returnStdout: true).trim()
                    if (commitMsg.contains('[skip ci]')) {
                        // This turns the row GREY/NEUTRAL instead of RED
                        currentBuild.result = 'ABORTED'
                        echo "🛑 Automated GitOps commit detected. Stopping gracefully."
                        return // This exits the stage without triggering a 'Failure'
                    }
                }
            }
        }

        stage('Set Version') {
            // This 'when' block ensures the rest of the stages only run if we didn't abort
            when { expression { currentBuild.result != 'ABORTED' } }
            steps {
                script {
                    env.VERSION = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.DOCKER_IMAGE = "${env.IMAGE_REPO}:${env.VERSION}"
                }
                echo "🚀 Preparing to build Version: ${env.VERSION}"
            }
        }
        
        stage('Run Unit Tests') {
            when { expression { currentBuild.result != 'ABORTED' } }
            steps {
                sh '''
                echo "🚀 Starting Python Unit Tests..."
                docker run --rm -v "$(pwd)":/app -w /app python:3.10-slim /bin/bash -c "pip install --no-cache-dir -r requirements.txt && pytest test_main.py -v"
                echo "✅ Tests Passed Successfully!"
                '''
            }
        }
        
        stage('SonarQube Analysis') {
            when { expression { currentBuild.result != 'ABORTED' } }
            environment {
                SCANNER_HOME = tool 'sonar-scanner'
            }
            steps {
                withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
                    sh '''
                    $SCANNER_HOME/bin/sonar-scanner \
                      -Dsonar.host.url=http://172.31.35.18:9000 \
                      -Dsonar.login=$SONAR_TOKEN \
                      -Dsonar.projectKey=nlp-doc-intel \
                      -Dsonar.projectName="nlp-doc-intel" \
                      -Dsonar.sources=. \
                      -Dsonar.python.version=3.10 \
                      -Dsonar.exclusions="venv/**,tests/**,**/*.txt"
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            when { expression { currentBuild.result != 'ABORTED' } }
            steps {
                sh '''
                echo "🐳 Building Docker Image: $DOCKER_IMAGE"
                docker build -t $DOCKER_IMAGE .
                '''
            }
        }

        stage('Trivy Security Scan') {
            when { expression { currentBuild.result != 'ABORTED' } }
            steps {
                sh '''
                echo "🛡️ Scanning image for CRITICAL and HIGH vulnerabilities..."
                trivy image --severity CRITICAL,HIGH $DOCKER_IMAGE
                '''
            }
        }

        stage('Push to Docker Hub') {
            when { expression { currentBuild.result != 'ABORTED' } }
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-cred', passwordVariable: 'DOCKER_PASS', usernameVariable: 'DOCKER_USER')]) {
                    sh '''
                    echo "☁️ Logging into Docker Hub and pushing image..."
                    echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                    docker push $DOCKER_IMAGE
                    docker logout
                    '''
                }
            }
        }

        stage('Update GitOps Manifests') {
            when { expression { currentBuild.result != 'ABORTED' } }
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-token-cred', passwordVariable: 'GIT_TOKEN', usernameVariable: 'GIT_USER')]) {
                    sh '''
                    echo "📝 Updating Kubernetes YAML files with new version: $VERSION"
                    
                    sed -i "s|image: atharvaramawat/nlp-doc-intel:.*|image: ${DOCKER_IMAGE}|g" k8s/fastapi-deployment.yaml
                    sed -i "s|image: atharvaramawat/nlp-doc-intel:.*|image: ${DOCKER_IMAGE}|g" k8s/nlp-worker-deployment.yaml
                    
                    echo "📦 Committing changes to GitHub..."
                    git config user.name "Jenkins CI/CD"
                    git config user.email "jenkins@automation.local"
                    
                    git add k8s/fastapi-deployment.yaml k8s/nlp-worker-deployment.yaml
                    git commit -m "ci: automated deployment update to version ${VERSION} [skip ci]"
                    
                    echo "🚀 Pushing changes to GitHub securely..."
                    git push https://${GIT_USER}:${GIT_TOKEN}@github.com/Atharva-Ramawat/NLP-doc-intel-CI-CD-pipeline.git HEAD:main
                    '''
                }
            }
        }
    }
}