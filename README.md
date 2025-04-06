# Install JupyterHub with HTTPS & OAuth (Github) in GKE Cluster


## Prerequisites 
    - Download and Install Gcloud CLI
    - Create Service account in GCP
    - Create GKE Cluster using cli
    - Install JupyterHub with helm on GKE 
    - Cloudflare account(For SSL)
    - OAuthenticator (Github account)
---
 # Download and install Gcloud cli in windows

 Download using the link
```
 https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe
```
or

Use **powershell** to download 
```
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")

& $env:Temp\GoogleCloudSDKInstaller.exe
    
```
---
 # Create Service account and give required roles to create GKE cluster
 
Use GCP Console to create Service account

or

Use gcloud cli

## To create Service account in cli
1. Enable the IAM API
2. User have the below two roles

    1. roles/iam.serviceAccountCreator
    2. roles/resourcemanager.projectIamAdmin


3. Create a SA 
```
gcloud iam service-accounts create SERVICE_ACCOUNT_NAME \
  --description="DESCRIPTION" \
  --display-name="DISPLAY_NAME"
```

4. To give the permission to the created user. We should bind the roles
```
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT_NAME@PROJECT_ID.iam.gserviceaccount.com" \
  --role="ROLE_NAME"
```

For more information [Visit] (https://cloud.google.com/iam/docs/service-accounts-create)

5. To create SA key, we need following roles permission
   1. roles/orgpolicy.policyAdmin
   2. roles/resourcemanager.organizationViewer
   3. roles/resourcemanager.tagAdmin 

```
gcloud iam service-accounts keys create KEY_FILE \
    --iam-account=SA_NAME@PROJECT_ID.iam.gserviceaccount.com
```
The service account key file is now downloaded to your machine

4. To create cluster, we need to give following roles to the SA
    1. roles/resourcemanager.projectIamAdmin
    2. roles/resourcemanager.projects.getIamPolicy
    3. roles/resourcemanager.projects.setIamPolicy

For more information [Visit] (https://cloud.google.com/iam/docs/keys-create-delete)

---
# Create GKE Cluster using cli

Before creating cluster - We need to authorize access to Google Cloud with a service account

```
gcloud auth activate-service-account SERVICE_ACCOUNT@DOMAIN.COM --key-file=/path/key.json --project=PROJECT_ID
```
To list all credentialed accounts and identify the current active account
```
gcloud auth list
```
Create a cluster 
```
gcloud container clusters create <Cluster Name> --zone us-central1-a --num-nodes=1 --machine-type=e2-medium
```

For more information [Visit] (https://cloud.google.com/sdk/gcloud/reference/container/clusters/create)
To resize the cluster 
```
gcloud container clusters resize sample-cluster --num-nodes=2 --zone us-central1-a
```
For more information [Visit] (https://cloud.google.com/sdk/gcloud/reference/container/clusters/resize)

To use kubectl 
```
gke-gcloud-auth-plugin 
```
To view the cluster config
```
kubectl config view
```
---
# Install JupyterHub with helm

## Install helm on the master nodes
Take ssh to the machine and add key, repo and install helm
```
curl https://baltocdn.com/helm/signing.asc | gpg --dearmor | sudo tee /usr/share/keyrings/helm.gpg > /dev/null
sudo apt-get install apt-transport-https --yes
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/helm.gpg] https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt-get update
sudo apt-get install helm
```

## Install Juypterhub
Add the helm repo 
```
helm repo add jupyterhub https://hub.jupyter.org/helm-chart/
helm repo update
```
Create a New Namespaces for better visibity
````
Kubectl create ns <name>
``````

Use helm search to get juypterhub details
```
helm search repo jupyterhub
```
See the helm values
```
helm show values jupyterhub/jupyterhub > hub.txt
```
Create the custom config file and install 
```
helm install jupyterhub jupyterhub/jupyterhub --namespace demo  --values .\hub.yaml
``` 
After installed Juypterhub. access url using public ip. Once you checked, configure SSL and github Oauth

# Configure OAuth github.
Goto your organization --> Developer setting --> OAuth Apps --> Create new app 

Give Application Name --> Homepage url --> Authorization callback URL

Eg- Your homepage url - demo.com 

Your Authorization callback URL should be - **https://demo.com/hub/oauth_callback**

You will get Client id and Client secret

**Note: URL should be in HTTPS**

Once you done Github side. Goto helm config file add the client id and client secret 

```
  config:
    JupyterHub:
      admin_access: true
      authenticator_class: github
    GitHubOAuthenticator:
      client_id: "xxxxxxxxxxxxxxxxxxxxxxxxxx" # You can put the client ID here, or from the secret
      client_secret: "xxxxxxxxxxxxxxxxxxxxxxxxxx"
      oauth_callback_url: "https://demo.demo.com/hub/oauth_callback"
      allow_all: True
```

Update the helm 
```
helm upgrade jupyterhub jupyterhub/jupyterhub -f .\hub.yaml
```

# SSL Configure 
We use automatic, to get certificate from Letsencrypt
Just add the email and domain url in the host
```
 https:
    enabled: false
    type: letsencrypt
    #type: letsencrypt, manual, offload, secret
    letsencrypt:
      contactEmail: [xxx@xx.com]
      # Specify custom server here (https://acme-staging-v02.api.letsencrypt.org/directory) to hit staging LE
      acmeServer: https://acme-v02.api.letsencrypt.org/directory
    manual:
      key:
      cert:
    secret:
      name:
      key: tls.key
      crt: tls.crt
    hosts: [demo.com]

```