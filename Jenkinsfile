pipeline {
    agent any
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '5'))
    }
    
    environment {
        DOCKER_IMAGE = "atharvaramawat/nlp-doc-intel:latest"
    }
    
    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }
        
        stage('Run Unit Tests') {
            steps {
                sh '''
                echo "🚀 Starting Python Unit Tests..."
                # Added quotes around "$(pwd)" to handle the spaces in the workspace path
                docker run --rm -v "$(pwd)":/app -w /app python:3.10-slim /bin/bash -c "pip install --no-cache-dir -r requirements.txt && pytest test_main.py -v"
                echo "✅ Tests Passed Successfully!"
                '''
            }
        }
        
        stage('SonarQube Analysis') {
            environment {
                SCANNER_HOME = tool 'sonar-scanner'
            }
            steps {
                // We use 'withCredentials' to be 100% sure the token is available
                withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
                    withSonarQubeEnv('sonar-server') {
                        sh '''
                        $SCANNER_HOME/bin/sonar-scanner \
                          -Dsonar.projectKey=nlp-doc-intel \
                          -Dsonar.projectName="nlp-doc-intel" \
                          -Dsonar.sources=. \
                          -Dsonar.token=$SONAR_TOKEN
                        '''
                    }
                }
            }
        }
        stage('Build Docker Image') {
            steps {
                sh '''
                echo "🐳 Building the Docker Image..."
                docker build -t $DOCKER_IMAGE .
                '''
            }
        }

        stage('Trivy Security Scan') {
            steps {
                sh '''
                echo "🛡️ Scanning image for CRITICAL and HIGH vulnerabilities..."
                trivy image --severity CRITICAL,HIGH $DOCKER_IMAGE
                '''
            }
        }

        stage('Push to Docker Hub') {
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
    }
}
