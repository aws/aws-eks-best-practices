# Configure gMSA for Windows Pods and containers

## What is a gMSA account

> *The group Managed Service Account (gMSA) provides the same functionality within the domain but also extends that functionality over multiple servers. When connecting to a service hosted on a server farm, such as Network Load Balanced solution, the authentication protocols supporting mutual authentication require that all instances of the services use the same principal. When a gMSA is used as service principal, the Windows operating system manages the password for the account instead of relying on the administrator to manage the password.*
> 
> *The Microsoft Key Distribution Service (kdssvc.dll) provides the mechanism to securely obtain the latest key or a specific key with a key identifier for an Active Directory account. The Key Distribution Service shares a secret which is used to create keys for the account. These keys are periodically changed. For a gMSA the domain controller computes the password on the key provided by the Key Distribution Services, in addition to other attributes of the gMSA. Member hosts can obtain the current and preceding password values by contacting a domain controller.*
> 
> *Reference: https://docs.microsoft.com/en-us/windows-server/security/group-managed-service-accounts/group-managed-service-accounts-overview*

## Windows container and gMSA use case

Windows-based networks commonly use Active Directory (AD) for authentication and authorization. This applies to users, computers, and other network resources. In a Enterprise setting it is common for developers often design their applications to run on domain-joined servers to take advantage of Integrated Windows Authentication. Integrating with AD makes it easy for users and other services to automatically and transparently sign in to the application with their identities.

ASP.NET applications that rely on Windows authentication, and run as Windows containers, benefit from gMSA because the Windows Node is used to exchange the Kerberos ticket on behalf of the container. However, the dockerfile used to build the Windows container image needs configure IIS and enable Windows authentication.

The following steps will set up IIS for Windows Authentication:

1. Install the Windows-Auth feature on IIS as it isn't installed by default on a Windows image
2. Setup the IIS Application pool to run under a Network Account
3. Disable `anonymousAuthentication` which is enabled by default
4. Enable Windows Authentication

```dockerfile
RUN Install-WindowsFeature -Name Web-Windows-Auth -IncludeAllSubFeature
RUN Import-Module WebAdministration; Set-ItemProperty 'IIS:\AppPools\SiteName' -name processModel.identityType -value 2
RUN Import-Module WebAdministration; Set-WebConfigurationProperty -Filter '/system.webServer/security/authentication/anonymousAuthentication' -Name Enabled -Value False -PSPath 'IIS:\' -Location 'SiteName'
RUN Import-Module WebAdministration; Set-WebConfigurationProperty -Filter '/system.webServer/security/authentication/windowsAuthentication' -Name Enabled -Value True -PSPath 'IIS:\' -Location 'SiteName'
```

## Enabling gMSA on Amazon EKS cluster

In November 2020, AWS published a step-by-step on how to set up an Amazon EKS cluster to use gMSA. This guide can be used for any scenario that requires Active Directory authentication, including the use cases mentioned above. The blog post walks-through:

1. Creating an EKS cluster with self-managed Windows worker nodes
2. Joining the Windows worker node to an Active Directory Domain
3. Creating and configure gMSA accounts on Active Directory Domain
4. Installing the gMSA CredentialSpec CRD
5. Installing the Windows gMSA Webhook Admission controller
6. Creating gMSA credential spec resources
7. Creating a Kubernetes ClusterRole to be defined for each gMSA credential spec
8. Assigning the Kubernetes ClusterRole to a service accounts to use specific gMSA credential specs
9. Configuring DNS forwarder with CoreDNS
10. Configuring the gMSA credential spec in the Windows pod spec
11. Testing the Windows Authentication from inside the Windows pod

Blog link:
https://aws.amazon.com/blogs/containers/windows-authentication-on-amazon-eks-windows-pods/
