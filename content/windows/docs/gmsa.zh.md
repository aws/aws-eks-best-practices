# 为 Windows Pod 和容器配置 gMSA

## 什么是 gMSA 账户

基于 Windows 的应用程序（如 .NET 应用程序）通常使用 Active Directory 作为身份提供程序，使用 NTLM 或 Kerberos 协议提供授权/身份验证。

应用程序服务器需要与 Active Directory 交换 Kerberos 票证，因此需要加入域。Windows 容器不支持加入域，并且由于容器是临时资源，这样做也没有太大意义，会给 Active Directory RID 池带来负担。

但是，管理员可以利用 [gMSA Active Directory](https://docs.microsoft.com/en-us/windows-server/security/group-managed-service-accounts/group-managed-service-accounts-overview) 账户为资源（如 Windows 容器、NLB 和服务器群）协商 Windows 身份验证。

## Windows 容器和 gMSA 的使用场景

利用 Windows 身份验证并以 Windows 容器形式运行的应用程序可从 gMSA 获益，因为 Windows 节点将代表容器交换 Kerberos 票证。有两种选择可以设置 Windows 工作节点以支持 gMSA 集成：

#### 1 - 加入域的 Windows 工作节点
在此设置中，Windows 工作节点加入了 Active Directory 域，并且 Windows 工作节点的 AD 计算机账户用于对 Active Directory 进行身份验证并检索要与 Pod 一起使用的 gMSA 身份。

在加入域的方法中，您可以轻松地使用现有的 Active Directory GPO 来管理和加固您的 Windows 工作节点；但是，它会产生额外的操作开销，并在 Windows 工作节点加入 Kubernetes 集群时延迟，因为它需要在节点启动期间额外重启，并在 Kubernetes 集群终止节点后清理 Active Directory 垃圾。

在以下博客文章中，您将找到有关如何实现加入域的 Windows 工作节点方法的详细分步说明：

[Amazon EKS Windows Pod 上的 Windows 身份验证](https://aws.amazon.com/blogs/containers/windows-authentication-on-amazon-eks-windows-pods/)

#### 2 - 无域 Windows 工作节点
在此设置中，Windows 工作节点未加入 Active Directory 域，并且使用"可移植"身份（用户/密码）对 Active Directory 进行身份验证并检索要与 Pod 一起使用的 gMSA 身份。

![](./images/domainless_gmsa.png)

可移植身份是 Active Directory 用户；该身份（用户/密码）存储在 AWS Secrets Manager 或 AWS Systems Manager Parameter Store 中，并且 AWS 开发的插件 ccg_plugin 将用于从 AWS Secrets Manager 或 AWS Systems Manager Parameter Store 检索此身份，并将其传递给 containerd 以检索 gMSA 身份并使其可用于 Pod。

在这种无域方法中，您可以在使用 gMSA 时避免在 Windows 工作节点启动期间与 Active Directory 交互，并减少 Active Directory 管理员的操作开销。

在以下博客文章中，您将找到有关如何实现无域 Windows 工作节点方法的详细分步说明：

[Amazon EKS Windows Pod 的无域 Windows 身份验证](https://aws.amazon.com/blogs/containers/domainless-windows-authentication-for-amazon-eks-windows-pods/)

#### 重要注意事项

尽管 Pod 能够使用 gMSA 账户，但也需要相应地设置应用程序或服务以支持 Windows 身份验证，例如，为了设置 Microsoft IIS 以支持 Windows 身份验证，您应该通过 dockerfile 进行准备：

```dockerfile
RUN Install-WindowsFeature -Name Web-Windows-Auth -IncludeAllSubFeature
RUN Import-Module WebAdministration; Set-ItemProperty 'IIS:\AppPools\SiteName' -name processModel.identityType -value 2
RUN Import-Module WebAdministration; Set-WebConfigurationProperty -Filter '/system.webServer/security/authentication/anonymousAuthentication' -Name Enabled -Value False -PSPath 'IIS:\' -Location 'SiteName'
RUN Import-Module WebAdministration; Set-WebConfigurationProperty -Filter '/system.webServer/security/authentication/windowsAuthentication' -Name Enabled -Value True -PSPath 'IIS:\' -Location 'SiteName'
```