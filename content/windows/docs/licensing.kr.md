<!-- # Choosing a Windows Server Version and License -->
# 윈도우 서버 버전 및 라이선스 선택

<!-- There are two primary release channels available to Windows Server customers, the Long-Term Servicing Channel and the Semi-Annual Channel. -->
Windows Server 고객은 장기 서비스 채널과 반기 채널이라는 두 가지 기본 릴리스 채널을 이용할 수 있습니다.

<!-- You can keep servers on the Long-Term Servicing Channel (LTSC), move them to the Semi-Annual Channel (SAC), or have some servers on either track, depending on what works best for your needs. -->
필요에 따라 서버를 LTSC (장기 서비스 채널) 에 유지하거나, 반기 채널 (SAC) 로 이동하거나, 일부 서버를 둘 중 하나에 둘 수 있습니다.

<!-- ## Long-Term Servicing Channel (LTSC) -->
## 장기 서비스 채널 (LTSC)

<!-- Formerly called the “Long-Term Servicing Branch”, this is the release model you are already familiar with where a new major version of Windows Server is released every 2-3 years. Users are entitled to 5 years of mainstream support and 5 years of extended support. This channel is appropriate for systems that require a longer servicing option and functional stability. Deployments of Windows Server 2019 and earlier versions of Windows Server will not be affected by the new Semi-Annual Channel releases. The Long-Term Servicing Channel will continue to receive security and non-security updates, only receiving select new features and functionality. -->
이전에 “장기 서비스 분기”라고 불렸던 이 모델은 이미 잘 알고 있는 릴리스 모델로, 2-3년마다 Windows Server의 새 메이저 버전이 릴리스됩니다.사용자는 5년간의 일반 지원과 5년의 추가 지원을 받을 수 있습니다.이 채널은 더 긴 서비스 옵션과 기능적 안정성이 필요한 시스템에 적합합니다. Windows Server 2019 및 이전 버전의 Windows Server 배포는 새로운 반기 채널 릴리스의 영향을 받지 않습니다.장기 서비스 채널에는 보안 및 비보안 업데이트가 계속 제공되며 엄선된 새로운 특징과 기능만 제공됩니다.

<!-- ## Semi-Annual Channel (SAC) -->
## 반기 채널 (SAC)

<!-- Windows Server products in the Semi-Annual Channel have new releases available twice a year, in spring and fall. Each release in this channel is supported for 18 months from the initial release. -->
반기 채널의 Windows Server 제품은 봄과 가을에 일년에 두 번 새 릴리스를 제공합니다.이 채널의 각 릴리스는 최초 릴리스로부터 18개월 동안 지원됩니다.

<!-- Most of the features introduced in the Semi-Annual Channel will be rolled up into the next Long-Term Servicing Channel release of Windows Server. The editions, functionality, and supporting content might vary from release to release depending on customer feedback. In this model, Windows Server releases are identified by the year and month or half of release: for example, in 2020, the release in the 4th month (April) is identified as version 2004. This naming changed with the last SAC release which is identified as 20H2. -->
반기 채널에 도입된 대부분의 기능은 Windows Server의 다음 장기 서비스 채널 릴리스에 포함될 예정입니다.에디션, 기능 및 지원 콘텐츠는 고객 피드백에 따라 릴리스마다 다를 수 있습니다.이 모델에서 Windows Server 릴리스는 출시 연도 및 월 또는 절반으로 식별됩니다. 예를 들어 2020년에는 4개월 차 (4월) 릴리스가 버전 2004로 식별됩니다.이 이름은 20H2로 식별되는 마지막 SAC 릴리스에서 변경되었습니다.

<!-- ## Which channel should I use? -->
## 어떤 채널을 사용해야 하나요?

<!-- Microsoft is moving to the LTSC as the primary release channel. The two current SAC builds will be supported until the end of their 18-month lifecycles ending 2021-12-14 for version 2004 and 2022-05-10 for version 20H2. -->
마이크로소프트는 LTSC를 기본 릴리스 채널로 전환하고 있습니다.현재 두 개의 SAC 빌드는 버전 2004의 경우 2021-12-14년, 버전 20H2의 경우 2022-05-10에 종료되는 18개월의 수명 주기가 끝날 때까지 지원됩니다.

<!-- Important features optimized for Container workloads which originated in the SAC have been incorporated into the LTSC build: -->
SAC에서 시작된 컨테이너 워크로드에 최적화된 중요 기능이 LTSC 빌드에 통합되었습니다.

* DSR(Direct Server Return) 지원. (LTSC [August 2020 Cumulative Update](https://support.microsoft.com/en-us/topic/august-20-2020-kb4571748-os-build-17763-1432-preview-fa1db909-8923-e70f-9aef-ba09edaee6f0)에서 사용 가능합니다.)

<!-- **What is Direct Server Return?** -->
**DSR(Direct Server Return)이란 무엇입니까?**
<!-- DSR is an implementation of asymmetric network load distribution in load balanced systems, meaning that the request and response traffic use a different network path. -->
DSR은 부하 분산 시스템에서 비대칭 네트워크 부하 분산을 구현한 것으로, 요청 트래픽과 응답 트래픽이 서로 다른 네트워크 경로를 사용한다는 의미입니다.

<!-- ## Licensing -->
## 라이선싱

<!-- At Amazon Web Services (AWS), the EKS Optimized AMIs for Windows are based on the Datacenter version, which doesn't have a limitation on the numbers of containers running on a worker node. For more information: https://docs.microsoft.com/en-us/virtualization/windowscontainers/about/faq -->
Amazon Web Services (AWS) 의 Windows용 EKS 최적화 AMI는 워커 노드에서 실행되는 컨테이너 수에 제한이 없는 데이터 센터 버전을 기반으로 합니다.자세한 내용: https://docs.microsoft.com/en-us/virtualization/windowscontainers/about/faq

