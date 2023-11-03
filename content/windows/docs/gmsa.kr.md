# 윈도우 파드와 컨테이너를 위한 gMSA 설정

## gMSA 계정이란 무엇입니까?

.NET 응용 프로그램과 같은 윈도우 기반 응용 프로그램은 대개 Active Directory를 ID 공급자로 사용하여 NTLM 또는 Kerberos 프로토콜을 사용하여 권한 부여/인증을 제공합니다. 

Kerberos 티켓을 Active Directory와 교환하려면 애플리케이션 서버가 도메인에 가입되어 있어야 합니다. 윈도우 컨테이너는 도메인 조인을 지원하지 않으며 컨테이너는 임시 리소스이므로 의미가 없어 Active Directory RID 풀에 부담이 됩니다.

하지만 관리자는 [gMSA Active Directory](https://docs.microsoft.com/en-us/windows-server/security/group-managed-service-accounts/group-managed-service-accounts-overview) 계정을 활용하여 윈도우 컨테이너, NLB 및 서버 팜과 같은 리소스에 대한 윈도우 인증을 협상할 수 있습니다.

## 윈도우 컨테이너 및 gMSA 사용 사례

윈도우 인증을 활용하고 윈도우 컨테이너로 실행되는 ASP.NET 응용 프로그램은 윈도우 노드를 사용하여 컨테이너를 대신하여 Kerberos 티켓을 교환하기 때문에 gMSA의 이점을 누릴 수 있습니다. 하지만 윈도우 컨테이너 이미지를 빌드하는 데 사용되는 dockerfile을 사용하려면 IIS를 구성하고 윈도우 인증을 활성화해야 합니다.

다음 단계는 윈도우용 IIS를 설정하는 단계입니다.

1.Windows-Auth 기능은 윈도우 이미지에 기본적으로 설치되지 않으므로 IIS에 설치하십시오.
2.네트워크 계정으로 실행되도록 IIS 응용 프로그램 풀 설정
3.기본적으로 활성화되어 있는 `anonymousAuthentication` 을 비활성화합니다.
4.윈도우 인증 활성화

```dockerfile
RUN Install-WindowsFeature -Name Web-Windows-Auth -IncludeAllSubFeature
RUN Import-Module WebAdministration; Set-ItemProperty 'IIS:\AppPools\SiteName' -name processModel.identityType -value 2
RUN Import-Module WebAdministration; Set-WebConfigurationProperty -Filter '/system.webServer/security/authentication/anonymousAuthentication' -Name Enabled -Value False -PSPath 'IIS:\' -Location 'SiteName'
RUN Import-Module WebAdministration; Set-WebConfigurationProperty -Filter '/system.webServer/security/authentication/windowsAuthentication' -Name Enabled -Value True -PSPath 'IIS:\' -Location 'SiteName'
```

## 아마존 EKS 클러스터에서 gMSA 활성화

2020년 11월, AWS는 gMSA를 사용하도록 Amazon EKS 클러스터를 설정하는 방법을 단계별로 발표했습니다. 이 가이드는 위에서 언급한 사용 사례를 포함하여 Active Directory 인증이 필요한 모든 시나리오에 사용할 수 있습니다. 블로그 게시물에서는 다음과 같은 내용을 안내합니다.

1. 자체 관리형 Windows 워커 노드가 포함된 EKS 클러스터 생성
2. Windows 워커 노드를 액티브 디렉터리 도메인에 가입시키기
3. 액티브 디렉터리 도메인에서 gMSA 계정 생성 및 구성
4. gMSA 자격 증명 스펙 CRD 설치
5. 윈도우 gMSA 웹훅 어드미션 컨트롤러 설치
6. gMSA 자격 증명 사양 리소스 생성
7. 각 gMSA 자격 증명 사양에 대해 정의할 쿠버네티스 클러스터롤 생성
8. 특정 gMSA 자격 증명 사양을 사용하기 위해 서비스 어카운트에 쿠버네티스 클러스터 역할 할당
9. 코어 DNS를 사용하여 DNS 전달자 구성
10. 윈도우 파드 사양에서 gMSA 자격 증명 사양 구성하기
11. 윈도우 파드 내에서 윈도우 인증 테스트하기

블로그 링크:
[https://aws.amazon.com/blogs/containers/windows-authentication-on-amazon-eks-windows-pods/](https://aws.amazon.com/blogs/containers/windows-authentication-on-amazon-eks-windows-pods/)
