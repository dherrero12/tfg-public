#!/bin/bash
ibmcloud login --apikey $IAM_API_KEY -g $IAM_RESOURCE_GROUP -r $IAM_REGION
ibmcloud ce project select -n $CE_PROJECT 

build () {
	BUILD_NUMBER=$(ibmcloud cr image-list | grep $1 | awk '{print $2}' | sort -n | tail -1)
	if $(ibmcloud ce job list | grep -q $2); then
		ibmcloud ce job update --name $2 --image $CR_SERVER/$CR_NAMESPACE/$1:$BUILD_NUMBER
	else
		ibmcloud ce job create --name $2 --image $CR_SERVER/$CR_NAMESPACE/$1:$BUILD_NUMBER --registry-secret $CE_REGISTRY_SECRET --env-from-secret $CE_SECRET --env-from-configmap $CE_CONFIGMAP
	fi
}
build $CR_IMAGE_POSTGRE $CE_JOB_POSTGRE
build $CR_IMAGE_CSV $CE_JOB_CSV

if ! $(ibmcloud ce subscription cos list | grep -q $CE_SUBSCRIPTION_POSTGRE); then
	ibmcloud ce subscription cos create --name $CE_SUBSCRIPTION_POSTGRE --destination $CE_JOB_POSTGRE --bucket $COS_BUCKET --destination-type job --event-type write	
fi
if ! $(ibmcloud ce subscription cron list | grep -q $CE_SUBSCRIPTION_CSV); then
	ibmcloud ce subscription cron create --name $CE_SUBSCRIPTION_CSV --destination $CE_JOB_CSV --destination-type job --schedule '0 */12 * * *'	
fi
