# JupyterHub Docker Image Build Guide

This guide walks through the process of building a Docker image for JupyterHub using the provided configuration files (env.yaml, jupyterhub_config.py, and Dockerfile).

## Prerequisites

- Docker installed and running
- Git (optional, for versioning)
- The following files in your project directory:
  - `Dockerfile`
  - `jupyterhub_config.py`
  - `env.yaml`

## Step 1: Project Structure Setup

Ensure your project directory is structured properly:

```
jupyterhub-project/
├── Dockerfile
├── jupyterhub_config.py
├── env.yaml
```

## Step 2: Review and Modify Configuration Files

### 2.1 Review Dockerfile

Make sure your Dockerfile contains all necessary instructions to build the JupyterHub image. A typical JupyterHub Dockerfile might include:

```Dockerfile
FROM mambaorg/micromamba:bookworm-slim

# Base environment setup
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV MAMBA_ROOT_PREFIX=/opt/conda
ENV ENV_NAME=itt
ENV MAMBA_EXE=/bin/micromamba
ARG MAMBA_USER=mambauser
ARG MAMBA_USER_ID=57439
ARG MAMBA_USER_GID=57439
ENV PATH=$MAMBA_ROOT_PREFIX/envs/$ENV_NAME/bin:$PATH

# Install OS packages
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash curl git unzip vim \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
# Install git (needed for pip installs from GitHub)
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*


# Create numba cache
USER ${MAMBA_USER}
ENV NUMBA_CACHE_DIR=/home/${MAMBA_USER}/.numba_cache
RUN mkdir -p ${NUMBA_CACHE_DIR} && chown -R ${MAMBA_USER}:${MAMBA_USER} ${NUMBA_CACHE_DIR}

# Add conda environment
COPY --chown=${MAMBA_USER}:${MAMBA_USER} environment.yml /tmp/environment.yml
RUN micromamba create -y -n $ENV_NAME -f /tmp/environment.yml && micromamba clean --all --yes

# Install JupyterHub, OAuthenticator, etc.
RUN micromamba install -n $ENV_NAME -c conda-forge \
    jupyterhub \
    jupyterlab \
    oauthenticator \
    boto3 \
    dask \
    coiled \
    jupyterhub-kubespawner \
    && micromamba clean --all --yes

# Copy config
COPY --chown=${MAMBA_USER}:${MAMBA_USER} jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py

# Launch command
CMD ["micromamba", "run", "-n", "itt", "jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]

```

Adjust this example to match your specific requirements.

### 2.2 Check jupyterhub_config.py

Review your `jupyterhub_config.py` file to ensure it contains the correct configuration for your JupyterHub deployment:

- Authentication method
- User spawner configuration
- Storage settings
- Resource limits
- Network settings

```python
import os
from oauthenticator.github import GitHubOAuthenticator

c = get_config()

# GitHub OAuth
c.JupyterHub.authenticator_class = GitHubOAuthenticator
c.GitHubOAuthenticator.client_id = os.environ["GITHUB_CLIENT_ID"]
c.GitHubOAuthenticator.client_secret = os.environ["GITHUB_CLIENT_SECRET"]
c.GitHubOAuthenticator.oauth_callback_url = os.environ["OAUTH_CALLBACK_URL"]
c.Authenticator.allow_all = True

# KubeSpawner for Kubernetes deployments
from kubespawner import KubeSpawner
c.JupyterHub.spawner_class = KubeSpawner
c.Spawner.http_timeout = 60

# Set persistent volume for each user
c.KubeSpawner.storage_pvc_ensure = True
c.KubeSpawner.pvc_name_template = 'claim-{username}'
c.KubeSpawner.storage_capacity = '10Gi'
c.KubeSpawner.storage_class = 'standard'  # Use your cluster's StorageClass
c.KubeSpawner.volumes = [{
    'name': 'volume-{username}',
    'persistentVolumeClaim': {
        'claimName': 'claim-{username}'
    }
}]
c.KubeSpawner.volume_mounts = [{
    'mountPath': '/home/jovyan',
    'name': 'volume-{username}'
}]

```

### 2.3 Verify env.yaml

Make sure your `env.yaml` file specifies all the Python packages needed for your JupyterHub deployment:

```yaml
name: itt
channels:
  - conda-forge
dependencies:
  - python=3.12
  - pandas
  - numpy
  - fsspec
  - gcsfs
  - ujson
  - xarray
  - kerchunk
  - numba>=0.56
  - xclim>=0.38
  - climpred
  - dask
  - xesmf
  - regionmask
  - xhistogram
  - scikit-learn
  - xskillscore
  - cartopy
  - flask
  - cfgrib
  - requests
  - s3fs
  - boto3
  - pyarrow
  - google-cloud-storage
  - pytest
  - gunicorn
  - altair
  - matplotlib
  - pip:
      - xbootstrap
      - python-dotenv
      - vl-convert-python
      - coiled

```

## Step 3: Build the Docker Image

Navigate to your project directory in the terminal and run:

```bash
docker build -t jupyterhub_helm .
```

This command builds a Docker image with the tag `jupyterhub_helm` using the Dockerfile in the current directory.

**Example Output:**
```
Sending build context to Docker daemon  15.36MB
Step 1/9 : FROM jupyter/base-notebook:latest
latest: Pulling from jupyter/base-notebook
...
Step 9/9 : CMD ["jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
 ---> Running in a1b2c3d4e5f6
 ---> 7g8h9i0j1k2l
Successfully built 7g8h9i0j1k2l
Successfully tagged jupyterhub_helm:latest
```

## Step 4: Verify the Image Build

Verify that the image has been successfully built:

```bash
docker images | grep jupyterhub_helm
```

**Example Output:**
```
jupyterhub_helm   latest    7g8h9i0j1k2l   About a minute ago   1.25GB
```

## Step 5: Test the Docker Image (Optional)

Run the container locally to test it:

```bash
docker run -p 8000:8000 jupyterhub_helm
```

This will start JupyterHub on port 8000. Access it by navigating to `http://localhost:8000` in your web browser.

# Google Cloud JupyterHub Repository Setup Guide

This guide walks through the process of setting up a Docker repository in Google Cloud Artifact Registry for storing and managing JupyterHub container images.

## Prerequisites

- Google Cloud SDK installed
- Docker installed
- Appropriate permissions in your Google Cloud project
- A JupyterHub Docker image built locally

## Commands Overview

### 1. Check Google Cloud SDK Version

```bash
gcloud version
```

**Example Output:**
```
Google Cloud SDK 440.0.0
alpha 2023.06.12
beta 2023.06.12
bq 2.0.93
bundled-python3-unix 3.9.16
core 2023.06.12
gcloud-crc32c 1.0.0
gsutil 5.24
```

### 2. Update Google Cloud Components

Ensures you have the latest version of all Google Cloud SDK components.

```bash
gcloud components update
```

**Example Output:**
```
Your current Google Cloud CLI version is: 440.0.0
The latest available version is: 440.0.0

┌─────────────────────────────────────────────────────────────┐
│                Components to be updated                     │
├───────────────────────────────────┬────────────┬───────────┤
│               Name                │  Version   │    Size   │
├───────────────────────────────────┼────────────┼───────────┤
│ gcloud cli                        │  440.0.0   │  < 1 MiB  │
└───────────────────────────────────┴────────────┴───────────┘

Do you want to continue (Y/n)? Y

Your Google Cloud CLI installation will be upgraded to version 440.0.0.
To revert your SDK to the previously installed version, you may run:
  $ gcloud components update --version 440.0.0

All components are up to date!
```

### 3. Check Current Google Cloud Configuration

Lists your current Google Cloud configuration settings.

```bash
gcloud config list
```

**Example Output:**
```
[core]
account = john.doe@example.com
disable_usage_reporting = True
project = e4drr-crafd

Your active configuration is: [default]
```

### 4. List Existing Artifact Repositories

Lists all repositories in your Google Cloud project.

```bash
gcloud artifacts repositories list
```

**Example Output:**
```
Listing items under project e4drr-crafd.

REPOSITORY  FORMAT  MODE    DESCRIPTION                      LOCATION  LABELS  ENCRYPTION  CREATE_TIME          UPDATE_TIME
my-repo     docker  STANDARD Docker repository for project   us-west1          Google managed key  2023-04-10T15:30:45  2023-04-10T15:30:45
```

### 5. Create a New Docker Repository for JupyterHub

Creates a new Docker repository specifically for JupyterHub images.

```bash
gcloud artifacts repositories create jupyterhub --repository-format=docker --location=us-east1
```

**Example Output:**
```
Creating repository [jupyterhub]...done.
Created repository [jupyterhub].
```

### 6. Verify Repository Creation

Lists repositories again to confirm the new repository was created.

```bash
gcloud artifacts repositories list
```

**Example Output:**
```
Listing items under project e4drr-crafd.

REPOSITORY   FORMAT  MODE    DESCRIPTION                      LOCATION  LABELS  ENCRYPTION  CREATE_TIME          UPDATE_TIME
jupyterhub   docker  STANDARD Docker repository for project   us-east1          Google managed key  2023-06-15T14:20:30  2023-06-15T14:20:30
my-repo      docker  STANDARD Docker repository for project   us-west1          Google managed key  2023-04-10T15:30:45  2023-04-10T15:30:45
```

### 7. Get Repository Details

Displays detailed information about the new repository.

```bash
gcloud artifacts repositories describe jupyterhub --location=us-east1
```

**Example Output:**
```
Encryption: Google managed key
Format: DOCKER
Location: us-east1
Mode: STANDARD
Name: projects/e4drr-crafd/locations/us-east1/repositories/jupyterhub
UpdateTime: 2023-06-15T14:20:30.506329Z
CreateTime: 2023-06-15T14:20:30.506329Z
```

### 8. Configure Docker to Use Google Cloud Artifact Registry

Configures Docker to authenticate with Google Cloud Artifact Registry.

```bash
gcloud auth configure-docker us-east1-docker.pkg.dev
```

**Example Output:**
```
Adding credential for us-east1-docker.pkg.dev
Docker configuration file updated successfully at [/home/user/.docker/config.json].
```

### 9. List Local Docker Images

Lists Docker images available locally.

```bash
docker image ls
```

**Example Output:**
```
REPOSITORY     TAG       IMAGE ID       CREATED         SIZE
jupyterhub     latest    a1b2c3d4e5f6   2 hours ago     1.2GB
jupyterhub_prod latest   f6e5d4c3b2a1   1 hour ago      1.3GB
python         3.9       9876z5432y1x   3 days ago      900MB
```

### 10. Tag Docker Images for Google Cloud Artifact Registry

Tags local Docker images with the repository path.

```bash
docker tag jupyterhub_prod us-east1-docker.pkg.dev/e4drr-crafd/jupyterhub/jupyterhub:v1
```

No output is expected if the command is successful.

### 11. Push Docker Image to Google Cloud Artifact Registry

Uploads the tagged Docker image to the repository.

```bash
docker push us-east1-docker.pkg.dev/e4drr-crafd/jupyterhub/jupyterhub:v1
```

**Example Output:**
```
The push refers to repository [us-east1-docker.pkg.dev/e4drr-crafd/jupyterhub/jupyterhub]
5f70bf18a086: Pushed
e16a89738269: Pushed
9dfa40a0da3b: Pushed
a6dbdbf3e873: Pushed
a5e66470b281: Pushed
831c5620387f: Pushed
v1: digest: sha256:f1a6f3a47e937a3834a720943cea4ee12b7321880f25de04e93146c6e24888c0 size: 1582
```

### 12. Enable Artifact Registry API (if needed)

Enables the Artifact Registry API in your Google Cloud project.

```bash
gcloud services enable artifactregistry.googleapis.com
```

**Example Output:**
```
Operation "operations/acf.p2-940098918766-61e7ce96-f108-4f1f-af58-90894c5e5841" finished successfully.
```

### 13. List Docker Images in Repository

Lists Docker images stored in the repository.

```bash
gcloud artifacts docker images list us-east1-docker.pkg.dev/e4drr-crafd/jupyterhub
```

**Example Output:**
```
Listing items under project e4drr-crafd, location us-east1, repository jupyterhub.

IMAGE: us-east1-docker.pkg.dev/e4drr-crafd/jupyterhub/jupyterhub
DIGEST: sha256:f1a6f3a47e937a3834a720943cea4ee12b7321880f25de04e93146c6e24888c0
```

### 14. List Tags for a Specific Image

Lists all tags for a specific Docker image.

```bash
gcloud container images list-tags us-east1-docker.pkg.dev/e4drr-crafd/jupyterhub/jupyterhub
```

**Example Output:**
```
DIGEST: sha256:f1a6f3a47e937a3834a720943cea4ee12b7321880f25de04e93146c6e24888c0
TAGS: v1
```

## Troubleshooting

### Error: Repository not found

If you encounter an error about the repository not being found, make sure:
1. You're using the correct project
2. The repository exists in the specified location
3. The Artifact Registry API is enabled

### Authentication Issues

If you have authentication issues while pushing images:
1. Run `gcloud auth login`
2. Rerun `gcloud auth configure-docker us-east1-docker.pkg.dev`

## Next Steps

After setting up your repository and pushing the JupyterHub image:
1. Deploy JupyterHub using the image from Artifact Registry
2. Set up automated CI/CD pipelines to build and push new versions
3. Configure access control for the repository

## Resources

- [Google Cloud Artifact Registry Documentation](https://cloud.google.com/artifact-registry/docs)
- [JupyterHub Documentation](https://jupyterhub.readthedocs.io)
- [Docker Documentation](https://docs.docker.com)


## Troubleshooting

### Build fails due to dependencies

If your build fails due to dependencies:
1. Check the error message for details
2. Modify your Dockerfile or env.yaml to fix dependency issues
3. Rebuild the image

### JupyterHub fails to start

If JupyterHub doesn't start properly:
1. Run the container with more verbose output: `docker run -p 8000:8000 jupyterhub_helm jupyterhub -f /srv/jupyterhub/jupyterhub_config.py --debug`
2. Check the logs for errors
3. Adjust your configuration as needed

## Resources

- [JupyterHub Documentation](https://jupyterhub.readthedocs.io/)
- [Docker Documentation](https://docs.docker.com/)
- [Conda Environment File Documentation](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#create-env-file-manually)

# Creating an Akuity ArgoCD Organization Using the GUI

This guide walks through the process of creating an organization in the Akuity Platform, which allows you to manage multiple ArgoCD instances and provide team access to your GitOps resources.

## Prerequisites

- Access to the Akuity Platform
- Administrator privileges (to create an organization)
- A valid email address for organization management

## Step 1: Log in to the Akuity Platform

1. Navigate to the Akuity Platform login page (typically at `https://app.akuity.io`)
2. Enter your credentials and click "Sign In"


## Step 2: Access Organization Management

1. After logging in, click on your profile icon in the top right corner of the dashboard
2. Select "Organizations" from the dropdown menu

*Figure 2: Accessing organization management from the profile menu*

## Step 3: Create a New Organization

1. On the Organizations page, click the "Create Organization" button
2. A creation form will appear

![Create Organization Button](/Image/Screenshot%202025-04-27%20171846.png)
*Figure 3: Organizations page with Create button highlighted*

## Step 4: Configure Organization Settings

Fill in the required information in the organization creation form:

1. **Organization Name**: Enter a name for your organization (e.g., "MyCompany-GitOps")
2. **Description** (optional): Add a brief description about your organization's purpose
3. **Email**: Enter the organization's contact email address
4. **Organization ID**: This will auto-generate based on your organization name, but you can customize it
   - Note: The ID cannot be changed after creation

*Figure 4: Organization creation form with fields to complete*

## Step 5: Configure Billing Information

1. Add payment method details if required
2. Select your subscription plan (Basic, Professional, or Enterprise)
3. Review the subscription terms
4. Click "Next"

![Billing Configuration](/Image/Screenshot%202025-04-27%20171913.png)
*Figure 5: Billing and subscription configuration screen*

## Step 6: Invite Initial Members (Optional)

1. Enter email addresses of users you want to invite to your organization
2. Assign appropriate roles to each user
   - **Owner**: Full administrative access
   - **Admin**: Can manage instances but not billing
   - **Member**: Can access instances but cannot create or modify them
3. Click "Next"

![Member Invitation Form](/Image/Screenshot%202025-04-27%20171902.png)
*Figure 6: Member invitation screen with role selection*

## Step 7: Review and Create

1. Review all your organization settings
2. Check that billing information is correct
3. Verify initial members and their roles
4. Click "Create Organization" to finalize



## Step 8: Organization Dashboard

After creation, you'll be taken to your new organization dashboard:

1. The dashboard shows organization overview, members, and instances
2. You can manage organization settings by clicking "Settings" in the left sidebar
3. To create ArgoCD instances within this organization, click on "Instances" in the left sidebar

![Organization Dashboard](/Image/Screenshot%202025-04-27%20172021.png)
*Figure 8: New organization dashboard showing key metrics and navigation*

## Step 9: Configure Organization Settings (Post-Creation)

Additional settings you can configure for your organization:

1. **Access Control**:
   - Click "Settings" → "Access Control"
   - Configure RBAC policies for your organization
   - Set up SSO integration if needed

*Figure 9: Organization access control configuration page*

2. **API Tokens**:
   - Click "Settings" → "API Tokens"
   - Create tokens for CI/CD integration
   - Set appropriate scopes and expiration


## Step 10: Create Your First Instance

From your organization dashboard:

1. Click "Instances" in the left sidebar
2. Click "Create Instance" button
3. Follow the instance creation wizard as covered in our instance creation guide

![Instance Creation from Organization](/Image/Screenshot%202025-04-27%20172936.png)
*Figure 11: Creating a new ArgoCD instance within your organization*

## Managing Organization Members

To add or manage members after organization creation:

1. Go to "Settings" → "Members" in the left sidebar
2. Click "Invite Members" to add new users
3. Adjust roles for existing members using the role dropdown
4. Remove members by clicking the trash icon next to their name

![Instance Creation from Organization](/Image/Screenshot%202025-04-27%20172946.png)


# Connect the agent to the kubernetes cluster
first we need to create cluster in argocd cloud. From GUI we have some issue. SO we are using CLI.

## How to login to akuity using cli
Using Browser login
```
akuity login 
```
After login , we have to select the organization
```
akuity config set --organization-name etderr
```

Using API
Alternatively, you can generate an API token from the Akuity Portal UI using the API Keys tab on the organization profile page and expose the key using ENV variable

```
export AKUITY_API_KEY_ID=<API_KEY_ID>
export AKUITY_API_KEY_SECRET=<API_KEY_SECRET>
akuity argocd instance list --organization-name <organization-name>
```

![Reference Image](/Image/Screenshot%202025-04-18%20222259.png)

# Once you done creating the organization, We have to create the cluster using cli
```
akuity argocd cluster create [flags]
```
```
akuity argocd cluster create \
  --organization-name=<name> \
  --instance-name=<name> \
  <cluster-name>
```
![Instance Creation from Organization](/Image/Screenshot%202025-04-27%20173403.png)

For more information [Visit] (https://docs.akuity.io/reference/cli/akuity_argocd_cluster_create)

once you create the cluster, You will get the agent manifest file. Download it and install in your kubectl cluster.

![Instance Creation from Organization](/Image/Screenshot%202025-04-27%20173522.png)

```
Kubectl apply -f <filename.yaml>
```
![Instance Creation from Organization](/Image/Screenshot%202025-04-27%20173300.png)

Using the above image URL login to the ARGO CL/CD portal
![Instance Creation from Organization](/Image/Screenshot%202025-04-27%20173938.png)

# Connecting ArgoCD to GitHub Using SSH

This guide walks through the process of configuring ArgoCD to connect to GitHub repositories using SSH authentication.

## Prerequisites

- ArgoCD installed and accessible
- Administrative access to ArgoCD
- A GitHub account with repositories you want to connect to

## Step 1: Generate an SSH Key Pair

First, you need to generate an SSH key pair that ArgoCD will use to authenticate with GitHub:

```bash
# Generate a new SSH key (use an email associated with your GitHub account)
ssh-keygen -t ed25519 -C "argocd@example.com" -f ~/.ssh/argocd_github_key -N ""
```

This will create:
- `~/.ssh/argocd_github_key` (private key)
- `~/.ssh/argocd_github_key.pub` (public key)

## Step 2: Add the SSH Public Key to GitHub

1. Copy the contents of your public key:
   ```bash
   cat ~/.ssh/argocd_github_key.pub
   ```

2. Go to GitHub:
   - For a user repository: Go to GitHub → Settings → SSH and GPG keys → New SSH key
   - For an organization repository: Go to Organization Settings → Security → SSH keys → New SSH key

3. Add the key:
   - Title: "ArgoCD Access Key"
   - Key type: Authentication Key
   - Key: Paste the content of your public key (`argocd_github_key.pub`)
   - Click "Add SSH key"

## Step 3: Configure ArgoCD to Use the SSH Key

### Option A: Using the ArgoCD UI

1. Log in to your ArgoCD UI with admin credentials
2. Go to Settings → Repositories → Connect Repo
3. Fill in the repository details:
   - Choose "VIA SSH" as the connection method
   - Repository URL: `git@github.com:your-username/your-repo.git`
   - SSH private key: Select "argocd-github-ssh-key" from the dropdown
4. Click "Connect"

![Instance Creation from Organization](/Image/Screenshot%202025-04-27%20174923.png)

### Option B: Using the ArgoCD CLI

1. Install and authenticate with the ArgoCD CLI if you haven't already:
   ```bash
   argocd login <ARGOCD_SERVER>
   ```

2. Add the repository using the CLI:
   ```bash
   argocd repo add git@github.com:your-username/your-repo.git \
     --ssh-private-key-path ~/.ssh/argocd_github_key
   ```

## Step 4: Verify the Connection

### Using the ArgoCD UI

1. Go to Settings → Repositories
2. Check that your repository shows a "Successful" connection status
3. If not, click on the repository and then "REFRESH"

### Using the ArgoCD CLI

```bash
argocd repo list
```

Verify that your GitHub repository appears in the list with "Successful" status.

## Resources

- [Akuity Platform Documentation](https://docs.akuity.io/)
- [Akuity Pricing Plans](https://www.akuity.io/pricing)
- [Akuity Support](https://support.akuity.io/)

Once you got connection between your Github to Argocd. You can create a project

before creating the we need to give the git RNV variable to helm values.yaml and move to the github.

```yaml
# fullnameOverride and nameOverride distinguishes blank strings, null values,
# and non-blank strings. For more details, see the configuration reference.
fullnameOverride: ""
nameOverride:

# enabled is ignored by the jupyterhub chart itself, but a chart depending on
# the jupyterhub chart conditionally can make use this config option as the
# condition.
enabled:

# custom can contain anything you want to pass to the hub pod, as all passed
# Helm template values will be made available there.
custom: {}

# imagePullSecret is configuration to create a k8s Secret that Helm chart's pods
# can get credentials from to pull their images.
imagePullSecret:
  name: my-secret
  create: false
  automaticReferenceInjection: true
  registry:
  username: 
  password:
  email:
# imagePullSecrets is configuration to reference the k8s Secret resources the
# Helm chart's pods can get credentials from to pull their images.
imagePullSecrets: []

# hub relates to the hub pod, responsible for running JupyterHub, its configured
# Authenticator class KubeSpawner, and its configured Proxy class
# ConfigurableHTTPProxy. KubeSpawner creates the user pods, and
# ConfigurableHTTPProxy speaks with the actual ConfigurableHTTPProxy server in
# the proxy pod.
hub:
  revisionHistoryLimit:
  config:
    JupyterHub:
      admin_access: true
      authenticator_class: github
    GitHubOAuthenticator:
      client_id: "Ov23li0XUibPdVlUsKgI" # You can put the client ID here, or from the secret
      client_secret: "457297dc3ca004299ca723cff7e898c390741de4"
      oauth_callback_url: "https://jupyterhub.e4drr-cloud.work/hub/oauth_callback"
      allow_all: True
  service:
    type: ClusterIP
    annotations: {}
    ports:
      nodePort:
      appProtocol:
    extraPorts: []
    loadBalancerIP:
  baseUrl: /
  cookieSecret:
  initContainers: []
  nodeSelector: {}
  tolerations: []
  concurrentSpawnLimit: 64
  consecutiveFailureLimit: 5
  activeServerLimit:
  deploymentStrategy:
    ## type: Recreate
    ## - sqlite-pvc backed hubs require the Recreate deployment strategy as a
    ##   typical PVC storage can only be bound to one pod at the time.
    ## - JupyterHub isn't designed to support being run in parallell. More work
    ##   needs to be done in JupyterHub itself for a fully highly available (HA)
    ##   deployment of JupyterHub on k8s is to be possible.
    type: Recreate
  db:
    type: sqlite-pvc
    upgrade:
    pvc:
      annotations: {}
      selector: {}
      accessModes:
        - ReadWriteOnce
      storage: 1Gi
      subPath:
      storageClassName:
    url:
    password:
  labels: {}
  annotations: {}
  command: []
  args: []
  extraConfig: {}
  extraFiles: {}
  extraEnv: {}
  extraContainers: []
  extraVolumes: []
  extraVolumeMounts: []
  image:
    name: quay.io/jupyterhub/k8s-hub
    tag: "4.1.0"
    pullPolicy:
    pullSecrets: []
  resources: {}
  podSecurityContext:
    runAsNonRoot: true
    fsGroup: 1000
    seccompProfile:
      type: "RuntimeDefault"
  containerSecurityContext:
    runAsUser: 1000
    runAsGroup: 1000
    allowPrivilegeEscalation: false
    capabilities:
      drop: ["ALL"]
  lifecycle: {}
  loadRoles: {}
  services: {}
  pdb:
    enabled: false
    maxUnavailable:
    minAvailable: 1
  networkPolicy:
    enabled: true
    ingress: []
    egress: []
    egressAllowRules:
      cloudMetadataServer: true
      dnsPortsCloudMetadataServer: true
      dnsPortsKubeSystemNamespace: true
      dnsPortsPrivateIPs: true
      nonPrivateIPs: true
      privateIPs: true
    interNamespaceAccessLabels: ignore
    allowedIngressPorts: []
  allowNamedServers: false
  namedServerLimitPerUser:
  authenticatePrometheus:
  redirectToServer:
  shutdownOnLogout:
  templatePaths: []
  templateVars: {}
  livenessProbe:
    # The livenessProbe's aim to give JupyterHub sufficient time to startup but
    # be able to restart if it becomes unresponsive for ~5 min.
    enabled: true
    initialDelaySeconds: 300
    periodSeconds: 10
    failureThreshold: 30
    timeoutSeconds: 3
  readinessProbe:
    # The readinessProbe's aim is to provide a successful startup indication,
    # but following that never become unready before its livenessProbe fail and
    # restarts it if needed. To become unready following startup serves no
    # purpose as there are no other pod to fallback to in our non-HA deployment.
    enabled: true
    initialDelaySeconds: 0
    periodSeconds: 2
    failureThreshold: 1000
    timeoutSeconds: 1
  existingSecret:
  serviceAccount:
    create: true
    name:
    annotations: {}
  extraPodSpec: {}

rbac:
  create: true

# proxy relates to the proxy pod, the proxy-public service, and the autohttps
# pod and proxy-http service.
proxy:
  secretToken:
  annotations: {}
  deploymentStrategy:
    ## type: Recreate
    ## - JupyterHub's interaction with the CHP proxy becomes a lot more robust
    ##   with this configuration. To understand this, consider that JupyterHub
    ##   during startup will interact a lot with the k8s service to reach a
    ##   ready proxy pod. If the hub pod during a helm upgrade is restarting
    ##   directly while the proxy pod is making a rolling upgrade, the hub pod
    ##   could end up running a sequence of interactions with the old proxy pod
    ##   and finishing up the sequence of interactions with the new proxy pod.
    ##   As CHP proxy pods carry individual state this is very error prone. One
    ##   outcome when not using Recreate as a strategy has been that user pods
    ##   have been deleted by the hub pod because it considered them unreachable
    ##   as it only configured the old proxy pod but not the new before trying
    ##   to reach them.
    type: Recreate
    ## rollingUpdate:
    ## - WARNING:
    ##   This is required to be set explicitly blank! Without it being
    ##   explicitly blank, k8s will let eventual old values under rollingUpdate
    ##   remain and then the Deployment becomes invalid and a helm upgrade would
    ##   fail with an error like this:
    ##
    ##     UPGRADE FAILED
    ##     Error: Deployment.apps "proxy" is invalid: spec.strategy.rollingUpdate: Forbidden: may not be specified when strategy `type` is 'Recreate'
    ##     Error: UPGRADE FAILED: Deployment.apps "proxy" is invalid: spec.strategy.rollingUpdate: Forbidden: may not be specified when strategy `type` is 'Recreate'
    rollingUpdate:
  # service relates to the proxy-public service
  service:
    type: LoadBalancer
    labels: {}
    annotations: {}
    nodePorts:
      http:
      https:
    disableHttpPort: false
    extraPorts: []
    loadBalancerIP:
    loadBalancerSourceRanges: []
  # chp relates to the proxy pod, which is responsible for routing traffic based
  # on dynamic configuration sent from JupyterHub to CHP's REST API.
  chp:
    revisionHistoryLimit:
    containerSecurityContext:
      runAsNonRoot: true
      runAsUser: 65534 # nobody user
      runAsGroup: 65534 # nobody group
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
      seccompProfile:
        type: "RuntimeDefault"
    image:
      name: quay.io/jupyterhub/configurable-http-proxy
      # tag is automatically bumped to new patch versions by the
      # watch-dependencies.yaml workflow.
      #
      tag: "4.6.3" # https://github.com/jupyterhub/configurable-http-proxy/tags
      pullPolicy:
      pullSecrets: []
    extraCommandLineFlags: []
    livenessProbe:
      enabled: true
      initialDelaySeconds: 60
      periodSeconds: 10
      failureThreshold: 30
      timeoutSeconds: 3
    readinessProbe:
      enabled: true
      initialDelaySeconds: 0
      periodSeconds: 2
      failureThreshold: 1000
      timeoutSeconds: 1
    resources: {}
    defaultTarget:
    errorTarget:
    extraEnv: {}
    nodeSelector: {}
    tolerations: []
    networkPolicy:
      enabled: true
      ingress: []
      egress: []
      egressAllowRules:
        cloudMetadataServer: true
        dnsPortsCloudMetadataServer: true
        dnsPortsKubeSystemNamespace: true
        dnsPortsPrivateIPs: true
        nonPrivateIPs: true
        privateIPs: true
      interNamespaceAccessLabels: ignore
      allowedIngressPorts: [http, https]
    pdb:
      enabled: false
      maxUnavailable:
      minAvailable: 1
    extraPodSpec: {}
  # traefik relates to the autohttps pod, which is responsible for TLS
  # termination when proxy.https.type=letsencrypt.
  traefik:
    revisionHistoryLimit:
    containerSecurityContext:
      runAsNonRoot: true
      runAsUser: 65534 # nobody user
      runAsGroup: 65534 # nobody group
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
      seccompProfile:
        type: "RuntimeDefault"
    image:
      name: traefik
      # tag is automatically bumped to new patch versions by the
      # watch-dependencies.yaml workflow.
      #
      tag: "v3.3.1" # ref: https://hub.docker.com/_/traefik?tab=tags
      pullPolicy:
      pullSecrets: []
    hsts:
      includeSubdomains: false
      preload: false
      maxAge: 15724800 # About 6 months
    resources: {}
    labels: {}
    extraInitContainers: []
    extraEnv: {}
    extraVolumes: []
    extraVolumeMounts: []
    extraStaticConfig: {}
    extraDynamicConfig: {}
    nodeSelector: {}
    tolerations: []
    extraPorts: []
    networkPolicy:
      enabled: true
      ingress: []
      egress: []
      egressAllowRules:
        cloudMetadataServer: true
        dnsPortsCloudMetadataServer: true
        dnsPortsKubeSystemNamespace: true
        dnsPortsPrivateIPs: true
        nonPrivateIPs: true
        privateIPs: true
      interNamespaceAccessLabels: ignore
      allowedIngressPorts: [http, https]
    pdb:
      enabled: false
      maxUnavailable:
      minAvailable: 1
    serviceAccount:
      create: true
      name:
      annotations: {}
    extraPodSpec: {}
  secretSync:
    containerSecurityContext:
      runAsNonRoot: true
      runAsUser: 65534 # nobody user
      runAsGroup: 65534 # nobody group
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
      seccompProfile:
        type: "RuntimeDefault"
    image:
      name: quay.io/jupyterhub/k8s-secret-sync
      tag: "4.1.0"
      pullPolicy:
      pullSecrets: []
    resources: {}
  labels: {}
  https:
    enabled: false
    type: letsencrypt
    #type: letsencrypt, manual, offload, secret
    letsencrypt:
      contactEmail:
      # Specify custom server here (https://acme-staging-v02.api.letsencrypt.org/directory) to hit staging LE
      acmeServer: https://acme-v02.api.letsencrypt.org/directory
    manual:
      key:
      cert:
    secret:
      name:
      key: tls.key
      crt: tls.crt
    hosts: []

# singleuser relates to the configuration of KubeSpawner which runs in the hub
# pod, and its spawning of user pods such as jupyter-myusername.
singleuser:
  podNameTemplate:
  extraTolerations: []
  nodeSelector: {}
  extraNodeAffinity:
    required: []
    preferred: []
  extraPodAffinity:
    required: []
    preferred: []
  extraPodAntiAffinity:
    required: []
    preferred: []
  networkTools:
    image:
      name: quay.io/jupyterhub/k8s-network-tools
      tag: "4.1.0"
      pullPolicy:
      pullSecrets: []
    resources: {}
  cloudMetadata:
    # block set to true will append a privileged initContainer using the
    # iptables to block the sensitive metadata server at the provided ip.
    blockWithIptables: true
    ip: 169.254.169.254
  networkPolicy:
    enabled: true
    ingress: []
    egress: []
    egressAllowRules:
      cloudMetadataServer: false
      dnsPortsCloudMetadataServer: true
      dnsPortsKubeSystemNamespace: true
      dnsPortsPrivateIPs: true
      nonPrivateIPs: true
      privateIPs: false
    interNamespaceAccessLabels: ignore
    allowedIngressPorts: []
  events: true
  extraAnnotations: {}
  extraLabels:
    hub.jupyter.org/network-access-hub: "true"
  extraFiles: {}
  extraEnv: {}
  lifecycleHooks: {}
  initContainers: []
  extraContainers: []
  allowPrivilegeEscalation: false
  uid: 1000
  fsGid: 100
  serviceAccountName:
  storage:
    type: dynamic
    extraLabels: {}
    extraVolumes: []
    extraVolumeMounts: []
    static:
      pvcName:
      subPath: "{username}"
    capacity: 10Gi
    homeMountPath: /home/jovyan
    dynamic:
      storageClass:
      pvcNameTemplate:
      volumeNameTemplate: volume-{user_server}
      storageAccessModes: [ReadWriteOnce]
      subPath:
  image:
    name: us-east1-docker.pkg.dev/e4drr-crafd/jupyterhub/jupyterhub
    tag: "v1"
    pullPolicy:
    pullSecrets: []
  startTimeout: 300
  cpu:
    limit:
    guarantee:
  memory:
    limit:
    guarantee: 1G
  extraResource:
    limits: {}
    guarantees: {}
  cmd: jupyterhub-singleuser
  defaultUrl:
  extraPodConfig: {}
  profileList: []

# scheduling relates to the user-scheduler pods and user-placeholder pods.
scheduling:
  userScheduler:
    enabled: true
    revisionHistoryLimit:
    replicas: 2
    logLevel: 4
    # plugins are configured on the user-scheduler to make us score how we
    # schedule user pods in a way to help us schedule on the most busy node. By
    # doing this, we help scale down more effectively. It isn't obvious how to
    # enable/disable scoring plugins, and configure them, to accomplish this.
    #
    # plugins ref: https://kubernetes.io/docs/reference/scheduling/config/#scheduling-plugins-1
    # migration ref: https://kubernetes.io/docs/reference/scheduling/config/#scheduler-configuration-migrations
    #
    plugins:
      score:
        # We make use of the default scoring plugins, but we re-enable some with
        # a new priority, leave some enabled with their lower default priority,
        # and disable some.
        #
        # Below are the default scoring plugins as of 2024-09-23 according to
        # https://kubernetes.io/docs/reference/scheduling/config/#scheduling-plugins.
        #
        # Re-enabled with high priority:
        # - NodeAffinity
        # - InterPodAffinity
        # - NodeResourcesFit
        # - ImageLocality
        #
        # Remains enabled with low default priority:
        # - TaintToleration
        # - PodTopologySpread
        # - VolumeBinding
        #
        # Disabled for scoring:
        # - NodeResourcesBalancedAllocation
        #
        disabled:
          # We disable these plugins (with regards to scoring) to not interfere
          # or complicate our use of NodeResourcesFit.
          - name: NodeResourcesBalancedAllocation
          # Disable plugins to be allowed to enable them again with a different
          # weight and avoid an error.
          - name: NodeAffinity
          - name: InterPodAffinity
          - name: NodeResourcesFit
          - name: ImageLocality
        enabled:
          - name: NodeAffinity
            weight: 14631
          - name: InterPodAffinity
            weight: 1331
          - name: NodeResourcesFit
            weight: 121
          - name: ImageLocality
            weight: 11
    pluginConfig:
      # Here we declare that we should optimize pods to fit based on a
      # MostAllocated strategy instead of the default LeastAllocated.
      - name: NodeResourcesFit
        args:
          scoringStrategy:
            type: MostAllocated
            resources:
              - name: cpu
                weight: 1
              - name: memory
                weight: 1
    containerSecurityContext:
      runAsNonRoot: true
      runAsUser: 65534 # nobody user
      runAsGroup: 65534 # nobody group
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
      seccompProfile:
        type: "RuntimeDefault"
    image:
      # IMPORTANT: Bumping the minor version of this binary should go hand in
      #            hand with an inspection of the user-scheduelr's RBAC
      #            resources that we have forked in
      #            templates/scheduling/user-scheduler/rbac.yaml.
      #
      #            Debugging advice:
      #
      #            - Is configuration of kube-scheduler broken in
      #              templates/scheduling/user-scheduler/configmap.yaml?
      #
      #            - Is the kube-scheduler binary's compatibility to work
      #              against a k8s api-server that is too new or too old?
      #
      #            - You can update the GitHub workflow that runs tests to
      #              include "deploy/user-scheduler" in the k8s namespace report
      #              and reduce the user-scheduler deployments replicas to 1 in
      #              dev-config.yaml to get relevant logs from the user-scheduler
      #              pods. Inspect the "Kubernetes namespace report" action!
      #
      #            - Typical failures are that kube-scheduler fails to search for
      #              resources via its "informers", and won't start trying to
      #              schedule pods before they succeed which may require
      #              additional RBAC permissions or that the k8s api-server is
      #              aware of the resources.
      #
      #            - If "successfully acquired lease" can be seen in the logs, it
      #              is a good sign kube-scheduler is ready to schedule pods.
      #
      name: registry.k8s.io/kube-scheduler
      # tag is automatically bumped to new patch versions by the
      # watch-dependencies.yaml workflow. The minor version is pinned in the
      # workflow, and should be updated there if a minor version bump is done
      # here. We aim to stay around 1 minor version behind the latest k8s
      # version.
      #
      tag: "v1.30.8" # ref: https://github.com/kubernetes/kubernetes/tree/master/CHANGELOG
      pullPolicy:
      pullSecrets: []
    nodeSelector: {}
    tolerations: []
    labels: {}
    annotations: {}
    pdb:
      enabled: true
      maxUnavailable: 1
      minAvailable:
    resources: {}
    serviceAccount:
      create: true
      name:
      annotations: {}
    extraPodSpec: {}
  podPriority:
    enabled: false
    globalDefault: false
    defaultPriority: 0
    imagePullerPriority: -5
    userPlaceholderPriority: -10
  userPlaceholder:
    enabled: true
    image:
      name: registry.k8s.io/pause
      # tag is automatically bumped to new patch versions by the
      # watch-dependencies.yaml workflow.
      #
      # If you update this, also update prePuller.pause.image.tag
      #
      tag: "3.10"
      pullPolicy:
      pullSecrets: []
    revisionHistoryLimit:
    replicas: 0
    labels: {}
    annotations: {}
    containerSecurityContext:
      runAsNonRoot: true
      runAsUser: 65534 # nobody user
      runAsGroup: 65534 # nobody group
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
      seccompProfile:
        type: "RuntimeDefault"
    resources: {}
    extraPodSpec: {}
  corePods:
    tolerations:
      - key: hub.jupyter.org/dedicated
        operator: Equal
        value: core
        effect: NoSchedule
      - key: hub.jupyter.org_dedicated
        operator: Equal
        value: core
        effect: NoSchedule
    nodeAffinity:
      matchNodePurpose: prefer
  userPods:
    tolerations:
      - key: hub.jupyter.org/dedicated
        operator: Equal
        value: user
        effect: NoSchedule
      - key: hub.jupyter.org_dedicated
        operator: Equal
        value: user
        effect: NoSchedule
    nodeAffinity:
      matchNodePurpose: prefer

# prePuller relates to the hook|continuous-image-puller DaemonsSets
prePuller:
  revisionHistoryLimit:
  labels: {}
  annotations: {}
  resources: {}
  containerSecurityContext:
    runAsNonRoot: true
    runAsUser: 65534 # nobody user
    runAsGroup: 65534 # nobody group
    allowPrivilegeEscalation: false
    capabilities:
      drop: ["ALL"]
    seccompProfile:
      type: "RuntimeDefault"
  extraTolerations: []
  # hook relates to the hook-image-awaiter Job and hook-image-puller DaemonSet
  hook:
    enabled: true
    pullOnlyOnChanges: true
    # image and the configuration below relates to the hook-image-awaiter Job
    image:
      name: quay.io/jupyterhub/k8s-image-awaiter
      tag: "4.1.0"
      pullPolicy:
      pullSecrets: []
    containerSecurityContext:
      runAsNonRoot: true
      runAsUser: 65534 # nobody user
      runAsGroup: 65534 # nobody group
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
      seccompProfile:
        type: "RuntimeDefault"
    podSchedulingWaitDuration: 10
    nodeSelector: {}
    tolerations: []
    resources: {}
    # Service Account for the hook-image-awaiter Job
    serviceAccount:
      create: true
      name:
      annotations: {}
    # Service Account for the hook-image-puller DaemonSet
    serviceAccountImagePuller:
      create: true
      name:
      annotations: {}
  continuous:
    enabled: true
    serviceAccount:
      create: true
      name:
      annotations: {}
  pullProfileListImages: true
  extraImages: {}
  pause:
    containerSecurityContext:
      runAsNonRoot: true
      runAsUser: 65534 # nobody user
      runAsGroup: 65534 # nobody group
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
      seccompProfile:
        type: "RuntimeDefault"
    image:
      name: registry.k8s.io/pause
      # tag is automatically bumped to new patch versions by the
      # watch-dependencies.yaml workflow.
      #
      # If you update this, also update scheduling.userPlaceholder.image.tag
      #
      tag: "3.10"
      pullPolicy:
      pullSecrets: []

ingress:
  enabled: false
  annotations: {}
  ingressClassName:
  hosts: []
  pathSuffix:
  pathType: Prefix
  tls: []
  extraPaths: []

# cull relates to the jupyterhub-idle-culler service, responsible for evicting
# inactive singleuser pods.
#
# The configuration below, except for enabled, corresponds to command-line flags
# for jupyterhub-idle-culler as documented here:
# https://github.com/jupyterhub/jupyterhub-idle-culler#as-a-standalone-script
#
cull:
  enabled: true
  users: false # --cull-users
  adminUsers: true # --cull-admin-users
  removeNamedServers: false # --remove-named-servers
  timeout: 3600 # --timeout
  every: 600 # --cull-every
  concurrency: 10 # --concurrency
  maxAge: 0 # --max-age

debug:
  enabled: false

global:
  safeToShowValues: false
```

# Creating a New Project in Akuity ArgoCD for a Sample Helm Project

This guide walks through the process of creating a new project in Akuity ArgoCD Cloud specifically configured for Helm chart deployments.

## Prerequisites

- Access to an Akuity ArgoCD instance
- Administrative privileges in the Akuity platform
- A Helm chart repository (GitHub, Helm repository, or OCI registry)
- Basic familiarity with Helm concepts

## Step 1: Log in to Your Akuity ArgoCD Instance

1. Navigate to your Akuity ArgoCD instance URL
2. Authenticate using your credentials

## Step 2: Create a New Project

There are two ways to create a project in Akuity ArgoCD:

### Option A: Using the UI

1. In the left sidebar, click on "Settings"
2. Select "Projects"
3. Click the "+ New Project" button in the top right corner
4. Enter a name for your project: `helm-sample`
5. (Optional) Add a description: "Project for sample Helm chart deployments"
6. Click "Create"

![Instance Creation from Organizaion](/Image/Screenshot%202025-04-27%20175548.png)

### Option B: Using the CLI

```bash
# Login to ArgoCD CLI
argocd login <your-akuity-argocd-url>

# Create the project
argocd proj create helm-sample -d https://kubernetes.default.svc,default -s https://github.com/your-org/helm-charts.git
```

## Step 3: Configure Project Settings

After creating the project, you need to configure it for Helm chart usage:

1. From the Projects list, click on your newly created `helm-sample` project
2. Go to the "Destinations" tab and click "Edit"
3. Add your Kubernetes cluster(s) as allowed destinations:
   - Server: `https://kubernetes.default.svc` (for in-cluster) or your external cluster URL
   - Namespace: `default` (or your preferred namespace)
   - Click "Save"

4. Go to the "Sources" tab and click "Edit"
5. Add your Helm chart repository as an allowed source:
   - Repository URL: `https://github.com/your-org/helm-charts.git` (for a Git repo with Helm charts)
   - Or: `https://charts.example.com` (for a Helm repository)
   - Click "Save"

6. Go to the "Permissions" tab to manage access:
   - Click on "Add Group or User"
   - Enter the relevant user or group name
   - Select the appropriate role (e.g., `role:admin`)
   - Click "Save"

## Step 4: Register Your Helm Repository

To use Helm charts, you first need to register your Helm repository with Akuity ArgoCD:

### For a Git Repository Containing Helm Charts

1. In the left sidebar, click on "Settings"
2. Select "Repositories"
3. Click "+ Connect Repo"
4. Select "VIA HTTPS" or "VIA SSH" depending on your GitHub access method
5. Enter the repository URL: `https://github.com/your-org/helm-charts.git`
6. Provide authentication details if required (username/password or SSH key)
7. Click "Connect"

### For a Helm Repository

1. In the left sidebar, click on "Settings"
2. Select "Repositories"
3. Click "+ Connect Repo"
4. Select "Helm" as the repository type
5. Enter the repository URL: `https://charts.example.com`
6. Provide authentication details if required
7. Click "Connect"

### For an OCI Registry (Helm charts in container registry)

1. In the left sidebar, click on "Settings"
2. Select "Repositories"
3. Click "+ Connect Repo"
4. Select "Helm (OCI)" as the repository type
5. Enter the registry URL: `oci://registry.example.com/helm-charts`
6. Provide authentication details if required
7. Click "Connect"

## Step 5: Create a Helm Application

Now that your project and repository are set up, you can create a Helm application:

1. In the left sidebar, click "Applications"
2. Click the "+ New App" button

3. Fill in the application details:
   - Application Name: `sample-helm-app`
   - Project: `helm-sample` (select your newly created project)
   - Sync Policy: Select your preferred option (e.g., "Automatic")

4. Configure the source:
   - Repository URL: Select your previously connected Helm repository
   - Chart: Select your chart (e.g., `nginx`)
   - Version: Choose a version or leave blank for latest

5. For Helm-specific configuration:
   - Values Files: Specify custom values files if needed
   - Parameters: Add any Helm parameters
   - Release Name: `sample-release` (or your preferred release name)
   - Namespace: `default` (or your preferred namespace)

6. Configure the destination:
   - Cluster URL: `https://kubernetes.default.svc` (for in-cluster)
   - Namespace: `default` (or your preferred namespace)

7. Click "Create"

```yaml
project: default
source:
  repoURL: https://github.com/e4drr/jupyterhub_prod
  path: jupyterhub
  targetRevision: HEAD
  helm:
    valueFiles:
      - values.yaml
destination:
  server: http://cluster-juypterhub:8001
  namespace: demo
syncPolicy:
  syncOptions:
    - CreateNamespace=true

```

## Step 6: Manage Your Helm Application

Once your application is created, you can manage it from the Akuity ArgoCD dashboard:

1. Navigate to your application on the Applications page
2. View the deployment status, resources, and logs
3. Perform actions like sync, refresh, or delete
4. View the Helm release information by clicking on the app


Once you got the public ip add that public in cloudflare

```
Kubectl get svc -A 
```


# How to setup sub domain in cloudflare
once you got the load balancer ip for the application. Just add the "A" Records in the domain.

Goto Cloudflare --> Select the domain --> goto domain --> select the records --> Finally add the A records

![Reference Image](/Image/Screenshot%202025-04-18%20213810.png)

![Reference Image](/Image/Screenshot%202025-04-18%20214147.png)

# How to Setup OAuth Github for juypterhub
Goto Setting --> Select the Developer setting --> Select the OAuth Apps --> Create a New OAuth App --> Give application name, url -->  Finally the Register the App

![Reference Image](/Image/Screenshot%202025-04-18%20214640.png)
![Reference Image](/Image/Screenshot%202025-04-18%20214715.png)

