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
