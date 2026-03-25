pipeline {
    agent any
    
   
    options {
        buildDiscarder(logRotator(numToKeepStr: '3'))
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
    }
}
