---
search:
  exclude: true
---


# 윈도우 파드와 컨테이너를 위한 gMSA 설정

## gMSA 계정이란 무엇입니까?

.NET 응용 프로그램과 같은 윈도우 기반 응용 프로그램은 대개 Active Directory를 ID 공급자로 사용하여 NTLM 또는 Kerberos 프로토콜을 사용하여 권한 부여/인증을 제공합니다. 

Kerberos 티켓을 Active Directory와 교환하려면 애플리케이션 서버가 도메인에 가입되어 있어야 합니다. 윈도우 컨테이너는 도메인 조인을 지원하지 않으며 컨테이너는 임시 리소스이므로 의미가 없어 Active Directory RID 풀에 부담이 됩니다.

하지만 관리자는 [gMSA Active Directory](https://docs.microsoft.com/en-us/windows-server/security/group-managed-service-accounts/group-managed-service-accounts-overview) 계정을 활용하여 윈도우 컨테이너, NLB 및 서버팜과 같은 리소스에 대한 윈도우 인증을 협상할 수 있습니다.

## 윈도우 컨테이너 및 gMSA 사용 사례

윈도우 인증을 활용하고 윈도우 컨테이너로 실행되는 애플리케이션은 윈도우 노드가 컨테이너 대신 Kerberos 티켓을 교환하는 데 사용되기 때문에 gMSA 이점을 활용할 수 있습니다. gMSA 통합을 지원하도록 윈도우 워커 노드를 설정하는 데 사용할 수 있는 두 가지 옵션이 있습니다.

#### 1 - 도메인에 가입된 윈도우 워커 노드
이 설정에서는 윈도우 워커 노드가 Active Directory 도메인에 가입되고 윈도우 워커 노드의 AD 컴퓨터 계정을 사용하여 Active Directory에 대해 인증하고 파드에 사용할 gMSA ID를 검색합니다. 

도메인 조인 접근 방식에서는 기존 Active Directory GPO를 사용하여 Windows 워커 노드를 쉽게 관리하고 강화할 수 있습니다. 하지만 이 경우 노드 시작 시 추가 재부팅이 필요하고 쿠버네티스 클러스터가 노드를 종료한 후 Active Directory Garage Cleaning이 필요하기 때문에 쿠버네티스 클러스터에서 윈도우 워커 노드를 조인하는 동안 추가적인 운영 오버헤드와 지연이 발생합니다.

다음 블로그 게시물에서는 도메인에 가입된 윈도우 워커 노드 접근 방식을 구현하는 방법을 단계별로 자세히 설명합니다.

[아마존 EKS 윈도우 파드에서의 윈도우 인증](https://aws.amazon.com/blogs/containers/windows-authentication-on-amazon-eks-windows-pods/)


#### 2 - 도메인이 없는 윈도우 워커 노드
이 설정에서는 윈도우 워커 노드가 Active Directory 도메인에 연결되지 않으며 "휴대용" ID (사용자/암호) 를 사용하여 Active Directory에 대해 인증하고 파드와 함께 사용할 gMSA ID를 검색합니다.

![](./images/domainless_gmsa.png)

이동식 자격 증명은 Active Directory 사용자입니다; 자격 증명 (사용자/암호)은 AWS Secrets Manager 또는 AWS System Manager Parameter Store에 저장되며, ccg_plugin라는 AWS에서 개발한 플러그인을 사용하여 AWS Secrets Manager 또는 AWS System Manager Parameter Store에서 이 자격 증명을 검색하고 이를 컨테이너에 전달하여 gMSA ID를 검색하고 파드에서 사용할 수 있도록 합니다.

도메인이 없는 이 접근 방식을 사용하면 gMSA를 사용할 때 윈도우 워커 노드를 시작할 때 Active Directory 상호 작용이 전혀 발생하지 않고 Active Directory 관리자의 운영 오버헤드가 줄어드는 이점을 얻을 수 있습니다.

다음 블로그 게시물에서는 도메인이 없는 윈도우 워커 노드 접근 방식을 구현하는 방법을 단계별로 자세히 설명합니다.

[아마존 EKS 윈도우 파드를 위한 도메인리스 윈도우 인증](https://aws.amazon.com/blogs/containers/domainless-windows-authentication-for-amazon-eks-windows-pods/)

#### 중요 참고 사항

파드가 gMSA 계정을 사용할 수 있음에도 불구하고 Windows 인증을 지원하도록 애플리케이션 또는 서비스도 적절히 설정해야 합니다. 예를 들어 Windows 인증을 지원하도록 Microsoft IIS를 설정하려면 dockerfile을 통해 준비해야 합니다.


```dockerfile
RUN Install-WindowsFeature -Name Web-Windows-Auth -IncludeAllSubFeature
RUN Import-Module WebAdministration; Set-ItemProperty 'IIS:\AppPools\SiteName' -name processModel.identityType -value 2
RUN Import-Module WebAdministration; Set-WebConfigurationProperty -Filter '/system.webServer/security/authentication/anonymousAuthentication' -Name Enabled -Value False -PSPath 'IIS:\' -Location 'SiteName'
RUN Import-Module WebAdministration; Set-WebConfigurationProperty -Filter '/system.webServer/security/authentication/windowsAuthentication' -Name Enabled -Value True -PSPath 'IIS:\' -Location 'SiteName'
```