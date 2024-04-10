# 為 Windows Pod 和容器設定 gMSA

## 什麼是 gMSA 帳戶

基於 Windows 的應用程式（如 .NET 應用程式）通常使用 Active Directory 作為身份提供者，透過 NTLM 或 Kerberos 協定提供授權/驗證。

應用程式伺服器需要與 Active Directory 交換 Kerberos 票證，因此需要加入網域。Windows 容器不支援加入網域，而且對於短暫的容器資源來說也沒有太大意義，會對 Active Directory RID 池造成負擔。

不過，管理員可以利用 [gMSA Active Directory](https://docs.microsoft.com/en-us/windows-server/security/group-managed-service-accounts/group-managed-service-accounts-overview) 帳戶，為資源（如 Windows 容器、NLB 和伺服器陣列）協商 Windows 驗證。

## Windows 容器和 gMSA 使用案例

利用 Windows 驗證的應用程式，如果以 Windows 容器執行，可從 gMSA 獲益，因為 Windows 節點會代表容器與 Active Directory 交換 Kerberos 票證。有兩種選項可設定 Windows 工作節點以支援 gMSA 整合：

#### 1 - 加入網域的 Windows 工作節點
在此設定中，Windows 工作節點會加入 Active Directory 網域，並使用 Windows 工作節點的 AD 電腦帳戶對 Active Directory 進行驗證，並取得要與 Pod 一起使用的 gMSA 身份。

在加入網域的方法中，您可以輕鬆使用現有的 Active Directory GPO 來管理和強化 Windows 工作節點；不過，這會產生額外的作業負擔，並在 Windows 工作節點加入 Kubernetes 叢集時造成延遲，因為需要在節點啟動期間重新啟動，以及在 Kubernetes 叢集終止節點後進行 Active Directory 清理。

在以下部落格文章中，您可以找到實作加入網域 Windows 工作節點方法的詳細步驟：

[Windows Authentication on Amazon EKS Windows pods](https://aws.amazon.com/blogs/containers/windows-authentication-on-amazon-eks-windows-pods/)


#### 2 - 無網域的 Windows 工作節點
在此設定中，Windows 工作節點不會加入 Active Directory 網域，而是使用「可攜式」身份 (使用者/密碼) 對 Active Directory 進行驗證，並取得要與 Pod 一起使用的 gMSA 身份。

![](./images/domainless_gmsa.png)

可攜式身份是 Active Directory 使用者；該身份 (使用者/密碼) 會儲存在 AWS Secrets Manager 或 AWS System Manager Parameter Store 中，並使用 AWS 開發的外掛程式 ccg_plugin 從 AWS Secrets Manager 或 AWS System Manager Parameter Store 取得此身份，並將其傳遞給 containerd 以取得 gMSA 身份並提供給 Pod 使用。

在此無網域方法中，您可以在使用 gMSA 時免去 Windows 工作節點啟動時與 Active Directory 互動的需求，並減少 Active Directory 管理員的作業負擔。

在以下部落格文章中，您可以找到實作無網域 Windows 工作節點方法的詳細步驟：

[Domainless Windows Authentication for Amazon EKS Windows pods](https://aws.amazon.com/blogs/containers/domainless-windows-authentication-for-amazon-eks-windows-pods/)

#### 重要注意事項

雖然 Pod 能夠使用 gMSA 帳戶，但仍需要相應地設定應用程式或服務以支援 Windows 驗證，例如，為了設定 Microsoft IIS 支援 Windows 驗證，您應該透過 Dockerfile 進行準備：


```dockerfile
RUN Install-WindowsFeature -Name Web-Windows-Auth -IncludeAllSubFeature
RUN Import-Module WebAdministration; Set-ItemProperty 'IIS:\AppPools\SiteName' -name processModel.identityType -value 2
RUN Import-Module WebAdministration; Set-WebConfigurationProperty -Filter '/system.webServer/security/authentication/anonymousAuthentication' -Name Enabled -Value False -PSPath 'IIS:\' -Location 'SiteName'
RUN Import-Module WebAdministration; Set-WebConfigurationProperty -Filter '/system.webServer/security/authentication/windowsAuthentication' -Name Enabled -Value True -PSPath 'IIS:\' -Location 'SiteName'
```