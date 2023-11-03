# 윈도우 워커 노드 하드닝

윈도우 서버 하드닝에는 악용되기 전에 보안 취약성을 식별하고 해결하는 작업이 포함됩니다. 

Microsoft는 운영 체제에 적용해야 하는 [Microsoft 보안 규정 준수](https://www.microsoft.com/en-us/download/details.aspx?id=55319) 및 [보안 기준](https://docs.microsoft.com/en-us/windows/security/threat-protection/windows-security-baselines)과 같은 다양한 도구를 제공합니다.

이 가이드는 특히 Amazon Elastic Kubernetes Service(EKS)에서 실행되는 윈도우 노드에 초점을 맞춥니다.

## 윈도우 Server Core를 통한 공격 대상 감소

윈도우 Server Core는 [EKS 최적화 윈도우 AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-windows-ami.html) 의 일부로 사용할 수 있는 최소 설치 옵션입니다. 윈도우 Server Core를 배포하면 몇 가지 이점이 있습니다. 먼저, 데스크톱 환경을 지원하는 윈도우 서버에서는 10GB에 비해 Server Core에서는 6GB라는 디스크 사용량이 비교적 작습니다.둘째, 코드베이스가 작기 때문에 공격 대상 영역이 더 작습니다.

`eksctl` 또는 Cloudformation을 통해 노드를 배포할 때 윈도우용 Server Core EKS 최적화 AMI를 지정할 수 있습니다.

아래 예는 윈도우 Server Core 2004를 기반으로 하는 윈도우 노드 그룹에 대한 eksctl 매니페스트입니다.

```yaml
nodeGroups:
- name: windows-ng
  instanceType: c5.xlarge
  minSize: 1
  volumeSize: 50
  amiFamily: WindowsServer2019CoreContainer
  ssh:
    allow: false
```

AMiFamily 이름 규칙은[eksctl 공식 문서](https://eksctl.io/usage/custom-ami-support/)에서 찾을 수 있습니다.

## RDP 연결 최소화

RDP(Remote Desktop Protocol, 원격 데스크톱 프로토콜)는 사용자가 네트워크를 통해 다른 윈도우 컴퓨터에 연결할 수 있는 그래픽 인터페이스를 제공하기 위해 Microsoft에서 개발한 연결 프로토콜입니다. 

모범사례로서 윈도우 워커 노드를 변경할 수 없는 것처럼 처리하는 것이 가장 좋습니다. 즉, 관리 연결도, 업데이트도 필요 없고 문제 해결도 필요 없습니다.모든 수정 및 업데이트는 새 사용자 지정 AMI로 구현하고 Auto Scaling 그룹을 업데이트하는 것으로 대체해야 합니다.**윈도우 서버 및 컨테이너 패치 적용** 및 **Amazon EKS 최적화 윈도우 AMI 관리**를 참조하십시오.

아래 예와 같이 ssh 속성에 **false** 값을 전달하여 배포 중에 윈도우 노드에서 RDP 연결을 비활성화합니다.

```yaml 
nodeGroups:
- name: windows-ng
  instanceType: c5.xlarge
  minSize: 1
  volumeSize: 50
  amiFamily: WindowsServer2019CoreContainer
  ssh:
    allow: false
```

윈도우 노드에 대한 액세스가 필요한 경우 [AWS System Manager Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)를 사용하여 AWS 콘솔 및 SSM 에이전트를 통해 안전한 PowerShell 세션을 연결합니다. 솔루션을 구현하는 방법을 보려면 [AWS System Manager Session Manager를 사용하여 윈도우 인스턴스에 안전하게 액세스하기](https://www.youtube.com/watch?v=nt6NTWQ-h6o)를 참조하세요.

System Manager Session Manager를 사용하려면 윈도우 노드에 추가 IAM 정책을 적용해야 합니다. 아래는 `eksctl` 클러스터 매니페스트에 **AmazonSSMManagedInstanceCore**가 지정된 예입니다.

```yaml 
 nodeGroups:
- name: windows-ng
  instanceType: c5.xlarge
  minSize: 1
  volumeSize: 50
  amiFamily: WindowsServer2019CoreContainer
  ssh:
    allow: false
  iam:
    attachPolicyARNs:
      - arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy
      - arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy
      - arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess
      - arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly
      - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
```

## Amazon Inspector
> [Amazon Inspector](https://aws.amazon.com/inspector/)는 AWS에 배포된 애플리케이션의 보안 및 규정 준수를 개선하는 데 도움이 되는 자동 보안 평가 서비스입니다. Amazon Inspector는 애플리케이션의 노출, 취약성 및 모범 사례와의 편차를 자동으로 평가합니다. 평가를 수행한 후 Amazon Inspector는 심각도 수준에 따라 우선 순위가 지정된 보안 조사 결과의 세부 목록을 생성합니다. 이런 결과는 직접 검토하거나 Amazon Inspector 콘솔 또는 API를 통해 제공되는 세부 평가 보고서의 일부로 검토할 수 있습니다.

Amazon Inspector를 사용하여 윈도우 워커 노드에서 CIS 벤치마크 평가를 실행할 수 있으며, 다음 작업을 수행하여 윈도우 Server Core에 설치할 수 있습니다.

1. 다음 .exe 파일을 다운로드합니다.
https://inspector-agent.amazonaws.com/windows/installer/latest/AWSAgentInstall.exe
2. 에이전트를 윈도우 워커 노드로 전송합니다.
3. PowerShell에서 다음 명령을 실행하여 아마존 인스펙터 에이전트를 설치합니다: `.\ AWSAgentInstall.exe /install `

아래는 첫 실행 후의 출력입니다. 보시다시피 [CVE](https://cve.mitre.org/) 데이터베이스를 기반으로 검색 결과를 생성했습니다. 이를 사용하여 워커 노드를 강화하거나 강화된 구성을 기반으로 AMI를 생성할 수 있습니다.

![](./images/inspector-agent.png)

Amazon Inspector 에이전트 설치, CIS 벤치마크 평가 설정 및 보고서 생성 방법을 포함하여 Amazon Inspector에 대한 자세한 내용은 [Amazon Inspector를 통한 윈도우 워크로드의 보안 및 규정 준수 개선](https://www.youtube.com/watch?v=nIcwiJ85EKU) 비디오를 시청하십시오.

## Amazon GuardDuty
> [Amazon GuardDuty](https://aws.amazon.com/guardduty/)는 악의적인 활동 및 무단 행동을 지속적으로 모니터링하여 AWS 계정, 워크로드 및 Amazon S3에 저장된 데이터를 보호하는 위협 탐지 서비스입니다. 클라우드를 사용하면 계정 및 네트워크 활동의 수집 및 집계가 단순화되지만 보안 팀이 이벤트 로그 데이터를 지속적으로 분석하여 잠재적 위협을 찾아내려면 시간이 많이 걸릴 수 있습니다. 

Amazon GuardDuty를 사용하면 RDP 무차별 대입 공격 및 포트 프로브 공격과 같은 윈도우 워커 노드에 대한 악의적인 활동을 가시화할 수 있습니다. 

[Amazon GuardDuty를 사용한 윈도우 워크로드의 위협 탐지](https://www.youtube.com/watch?v=ozEML585apQ) 비디오를 시청하여 최적화된 EKS 윈도우 AMI에서 CIS 벤치마크를 구현하고 실행하는 방법을 알아보십시오.

## 윈도우 Amazon EC2의 보안
모든 계층에서 보안 제어를 구현하려면 [Amazon EC2 윈도우 인스턴스의 보안 모범 사례](https://docs.aws.amazon.com/AWSEC2/latest/WindowsGuide/ec2-security.html)를 읽어보십시오.
