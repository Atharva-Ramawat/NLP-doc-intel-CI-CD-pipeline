pipeline {
    agent any
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '4'))
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
                docker run --rm -v $(pwd):/app -w /app python:3.10-slim /bin/bash -c "pip install --no-cache-dir -r requirements.txt && pytest test_main.py -v"
                echo "✅ Tests Passed Successfully!"
                '''
            }
        }
        
        stage('SonarQube Analysis') {
            environment {
                // Grabs the scanner we just installed in Jenkins Tools
                SCANNER_HOME = tool 'sonar-scanner'
            }
            steps {
                // Connects using the Server configuration and Secret Token we added
                withSonarQubeEnv('sonar-server') {
                    sh '''
                    echo "🔍 Starting Static Code Analysis..."
                    $SCANNER_HOME/bin/sonar-scanner \
                      -Dsonar.projectKey=nlp-doc-intel \
                      -Dsonar.projectName="nlp-doc-intel" \
                      -Dsonar.sources=. \
                      -Dsonar.python.version=3.10 \
                      -Dsonar.exclusions=venv/**,tests/**,**/*.txt
                    '''
                }
            }
        }
    }
}