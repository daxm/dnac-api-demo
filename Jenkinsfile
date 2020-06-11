#!/usr/bin/env groovy

// library mantaining groovy files which are adding functionality
@Library('AutomateEverything@1.1')
import com.cisco.jenkins.*
import com.cisco.docker.*

// Groovey funcs
def dock  = new Docker(this)
def utils = new Utils(this)

// Build
def credentials_id    = "345c79bc-9def-4981-94b5-d8190fdd2304"
def build = utils.getBuildId() // Unique buildId based upon the Jenkins Job & Build Number
def release_version   = "${env.BUILD_NUMBER}"
def release_name      = "dnawf_dnac_module_pack"

// Artifactory
def artifactory_url   = "http://engci-maven-master.cisco.com/artifactory"
def artifactory_browse_url = "https://engci-maven-master.cisco.com/artifactory/webapp/#/artifacts/browse/simple/General"
def artifactory_repo  = "AS-release/Community/dnawf_dnac_module_pack"

// Docker
def dockerhub         = "dockerhub.cisco.com/as-release-docker"
def docker_repo       = "dnawf_dnac_module_pack"
def docker_tag        = "${dockerhub}/${docker_repo}"

// Jenkins
properties([
  buildDiscarder(logRotator(artifactDaysToKeepStr: '7',
                            artifactNumToKeepStr: '30',
                            daysToKeepStr: '7',
                            numToKeepStr: '30')),
  parameters([
    booleanParam(name: 'destroyPreviousDockerEnvironment', defaultValue: true),
    booleanParam(name: 'stopContainerOnExit'             , defaultValue: false),
    string(name: 'jenkinsNode', defaultValue: 'emear-sio-slv03')
  ])
])

node(params.jenkinsNode) {

    try {

        stage ('Clean') {

            // Ensure old files are cleaned up
            sh "rm -rf ${env.WORKSPACE}/* || true"
            sh 'printenv'

        }

        stage('Git Checkout') {

            // See https://github.com/jenkinsci/pipeline-examples/blob/master/docs/BEST_PRACTICES.md
            def commitHash = checkout(scm).GIT_COMMIT
            echo "commitHash: ${commitHash}"
            echo "workspace: ${env.NODE_NAME}"
            echo "workspace: ${env.WORKSPACE}"
            echo "gitBranch: ${env.BRANCH_NAME}"
            echo "BuildId: ${env.BUILD_ID}"

        }

        stage('Container Creation ') {
            python_image = docker.image('python:3.8.3-slim-buster')
            python_container = python_image.run("-d --name dnawf_dnac_module_pack_${build} -v ${env.workspace}:/mnt python:3.8.3-slim-buster tail -f /dev/null")


            echo "Python Container ID = ${python_container.id}"

            dock.exec(
                containerId: "${python_container.id}",
                commands: ["pip3 install dna_workflows"]
            )
        }

    } catch(error) {

        echo "Exception: " + error

        // overwrite the build result!
        currentBuild.result = 'FAILURE'
    }

// --------CLEAN UP---------------

    finally {

        stage('Clean up'){


            if (params.stopContainerOnExit == true) {

                sh "cd ${configDir}; docker-compose -p ${project_prefix} down -v || true"

            } else {
                echo "Not stopping the containers!"
            }

            echo "RESULT: ${currentBuild.result}"
        }
    }

// --------END---------------

}


