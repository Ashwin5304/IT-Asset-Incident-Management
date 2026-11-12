pipeline {
    agent none

    stages {

        stage('Checkout') {
            agent any
            steps {
                checkout scm
            }
        }

        stage('Run Tests') {
            agent {
                docker {
                    image 'python:3.13-slim'
                }
            }

            steps {
                sh 'python --version'
                sh 'python -m pip install --no-cache-dir -r requirements.txt'
                sh 'python -m pytest -v'
            }
        }

        stage('Build Docker Image') {
            agent any

            steps {
                sh 'docker build -t itamis:ci .'
            }
        }
    }

    post {
        success {
            echo 'ITAMIS CI pipeline completed successfully.'
        }

        failure {
            echo 'ITAMIS CI pipeline failed.'
        }
    }
}
