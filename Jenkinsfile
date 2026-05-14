pipeline {
    agent any
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '5'))
    }
    
    environment {
        IMAGE_REPO = "atharvaramawat/nlp-doc-intel"
    }
    
    stage('Checkout Code') {
            steps {
                checkout scm
                script {
                    // Check if the very last commit message contains [skip ci]
                    def lastCommitMsg = sh(script: 'git log -1 --pretty=%B', returnStdout: true).trim()
                    
                    if (lastCommitMsg.contains('[skip ci]')) {
                        echo "🛑 [skip ci] detected in Git history. Aborting this build to stop the loop."
                        // We mark it as ABORTED so it doesn't count as a failure
                        currentBuild.result = 'ABORTED'
                        error("Stopping build: Automated commit detected.")
                    }
                }
            }
        }
        stage('Set Version') {
            steps {
                script {
                    // Random Number (Git Hash) Versioning
                    env.VERSION = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.DOCKER_IMAGE = "${env.IMAGE_REPO}:${env.VERSION}"
                }
            }
        }
        
        stage('Run Unit Tests') {
            steps {
                sh '''
                echo "🚀 Starting Python Unit Tests..."
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
            steps {
                sh "docker build -t $DOCKER_IMAGE ."
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-cred', passwordVariable: 'DOCKER_PASS', usernameVariable: 'DOCKER_USER')]) {
                    sh '''
                    echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
                    docker push $DOCKER_IMAGE
                    docker logout
                    '''
                }
            }
        }

        stage('Update GitOps Manifests') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'github-token-cred', passwordVariable: 'GIT_TOKEN', usernameVariable: 'GIT_USER')]) {
                    sh '''
                    echo "📝 Updating Kubernetes YAML files with new version: $VERSION"
                    
                    sed -i "s|image: atharvaramawat/nlp-doc-intel:.*|image: ${DOCKER_IMAGE}|g" k8s/fastapi-deployment.yaml
                    sed -i "s|image: atharvaramawat/nlp-doc-intel:.*|image: ${DOCKER_IMAGE}|g" k8s/nlp-worker-deployment.yaml
                    
                    git config user.name "Jenkins CI/CD"
                    git config user.email "jenkins@automation.local"
                    
                    git add k8s/fastapi-deployment.yaml k8s/nlp-worker-deployment.yaml
                    git commit -m "ci: automated deployment update to version ${VERSION} [skip ci]"
                    
                    git push https://${GIT_USER}:${GIT_TOKEN}@github.com/Atharva-Ramawat/NLP-doc-intel-CI-CD-pipeline.git HEAD:main
                    '''
                }
            }
        }
    }
}