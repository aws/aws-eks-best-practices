# Configure gMSA for Windows Pods and containers

## What is a gMSA account

Windows-based applications such as .NET applications often use Active Directory as an identity provider, providing authorization/authentication using NTLM or Kerberos protocol. 

An application server to exchange Kerberos tickets with Active Directory requires to be domain-joined. Windows containers don’t support domain joins and would not make much sense as containers are ephemeral resources, creating a burden on the Active Directory RID pool.

However, administrators can leverage [gMSA Active Directory](https://docs.microsoft.com/en-us/windows-server/security/group-managed-service-accounts/group-managed-service-accounts-overview) accounts to negotiate a Windows authentication for resources such as Windows containers, NLB, and server farms.

## Windows container and gMSA use case

ASP.NET applications that leverage on Windows authentication, and run as Windows containers, benefit from gMSA because the Windows Node is used to exchange the Kerberos ticket on behalf of the container. However, the dockerfile used to build the Windows container image needs configure IIS and enable Windows authentication.

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
