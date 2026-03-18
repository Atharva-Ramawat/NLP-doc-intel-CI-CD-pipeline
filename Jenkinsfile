pipeline {
    agent any
    
    // 🧹 This is the new block! It automatically deletes old builds.
    options {
        buildDiscarder(logRotator(numToKeepStr: '3'))
    }
    
    stages {
        stage('Checkout Code') {
            steps {
                // Pull the latest code from GitHub
                checkout scm
            }
        }
        
        stage('Run Unit Tests') {
            steps {
                // Spin up a temporary Python container to run tests
                sh '''
                echo "🚀 Starting Python Unit Tests..."
                docker run --rm -v $(pwd):/app -w /app python:3.10-slim /bin/bash -c "pip install --no-cache-dir -r requirements.txt && pytest test_main.py -v"
                echo "✅ Tests Passed Successfully!"
                '''
            }
        }
    }
}