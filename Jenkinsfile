pipeline {
    agent any
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '4'))
    }
    
    environment {
        // Define both repositories
        BACKEND_REPO = "atharvaramawat/nlp-doc-intel"
        FRONTEND_REPO = "atharvaramawat/nlp-frontend"
    }
    
    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Set Version') {
            steps {
                script {
                    // Random Number (Git Hash) Versioning
                    env.VERSION = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    
                    // Assign tags for both images
                    env.BACKEND_IMAGE = "${env.BACKEND_REPO}:${env.VERSION}"
                    env.FRONTEND_IMAGE = "${env.FRONTEND_REPO}:${env.VERSION}"
                }
                echo "🚀 Building Version: ${env.VERSION}"
            }
        }
        
        stage('Run Unit Tests') {
            steps {
                // Fixed: Mounts specifically to the /backend workspace where requirements and tests live
                sh 'docker run --rm -v "${WORKSPACE}/backend:/app" -w /app python:3.10-slim /bin/bash -c "pip install --no-cache-dir -r requirements.txt && pytest test_main.py -v"'
            }
        }
        
        stage('SonarQube Analysis') {
            environment { SCANNER_HOME = tool 'sonar-scanner' }
            steps {
                withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
                    // Fixed exclusions to safely ignore all virtual envs across both directories
                    sh "$SCANNER_HOME/bin/sonar-scanner -Dsonar.host.url=http://172.31.35.18:9000 -Dsonar.login=$SONAR_TOKEN -Dsonar.projectKey=nlp-doc-intel -Dsonar.projectName=nlp-doc-intel -Dsonar.sources=. -Dsonar.python.version=3.10 -Dsonar.exclusions='**/venv/**,**/tests/**,**/*.txt'"
                }
            }
        }

        stage('Build Docker Images') {
            steps { 
                // Build Backend pointing to the backend folder
                sh "docker build -t $BACKEND_IMAGE ./backend" 
                
                // Build Frontend pointing to the frontend folder
                sh "docker build -t $FRONTEND_IMAGE ./frontend" 
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-cred', passwordVariable: 'DOCKER_PASS', usernameVariable: 'DOCKER_USER')]) {
                    sh '''
                    echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                    
                    docker push $BACKEND_IMAGE
                    docker push $FRONTEND_IMAGE
                    
                    docker logout
                    '''
                }
            }
        }

        stage('Update GitOps Manifests') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-token-cred', passwordVariable: 'GIT_TOKEN', usernameVariable: 'GIT_USER')]) {
                    sh '''
                    # 1. Update Backend & Worker Tags
                    sed -i "s|image: atharvaramawat/nlp-doc-intel:.*|image: ${BACKEND_IMAGE}|g" k8s/fastapi-deployment.yaml
                    sed -i "s|image: atharvaramawat/nlp-doc-intel:.*|image: ${BACKEND_IMAGE}|g" k8s/nlp-worker-deployment.yaml
                    
                    # 2. Update Frontend Tag
                    sed -i "s|image: atharvaramawat/nlp-frontend:.*|image: ${FRONTEND_IMAGE}|g" k8s/nlp-frontend-deployment.yaml
                    
                    git config user.name "Jenkins CI/CD"
                    git config user.email "jenkins@automation.local"
                    
                    git add k8s/fastapi-deployment.yaml k8s/nlp-worker-deployment.yaml k8s/nlp-frontend-deployment.yaml
                    git commit -m "ci: automated multi-service deployment update to version ${VERSION} [skip ci]"
                    
                    git push https://${GIT_USER}:${GIT_TOKEN}@github.com/Atharva-Ramawat/NLP-doc-intel-CI-CD-pipeline.git HEAD:main
                    '''
                }
            }
        }
    }
}
