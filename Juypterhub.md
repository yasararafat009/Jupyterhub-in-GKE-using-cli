# How to setup sub domain in cloudflare
once you got the load balancer ip for the application. Just add the "A" Records in the domain.

Goto Cloudflare --> Select the domain --> goto domain --> select the records --> Finally add the A records

![Reference Image](/Image/Screenshot%202025-04-18%20213810.png)

![Reference Image](/Image/Screenshot%202025-04-18%20214147.png)

# How to Setup OAuth Github for juypterhub
Goto Setting --> Select the Developer setting --> Select the OAuth Apps --> Create a New OAuth App --> Give application name, url -->  Finally the Register the App

![Reference Image](/Image/Screenshot%202025-04-18%20214640.png)
![Reference Image](/Image/Screenshot%202025-04-18%20214715.png)

# How to use Akuity argocd using CLI

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

For more information [Visit] (https://docs.akuity.io/reference/cli/akuity_argocd_cluster_create)

once you create the cluster, You will get the agent manifest file. Download it and install in your kubectl cluster.