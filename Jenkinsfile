pipeline {
    agent any
    
    stages {
        stage('Checkout Code') {
            steps {
                // This command tells Jenkins to pull the latest code from GitHub
                checkout scm
            }
        }
        
        stage('Run Unit Tests') {
            steps {
                // We use a temporary Python container to install dependencies and run Pytest
                sh '''
                echo "🚀 Starting Python Unit Tests..."
                docker run --rm -v $(pwd):/app -w /app python:3.10-slim /bin/bash -c "pip install --no-cache-dir -r requirements.txt && pytest test_main.py -v"
                echo "✅ Tests Passed Successfully!"
                '''
            }
        }
    }
}