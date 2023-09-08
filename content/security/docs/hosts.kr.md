# 인프라(호스트) 보호
컨테이너 이미지를 보호하는 것이 중요한 만큼 컨테이너 이미지를 실행하는 인프라를 보호하는 것도 똑같이 중요합니다. 이 섹션에서는 호스트에 대해 직접 시작된 공격의 위험을 완화하는 다양한 방법을 살펴봅니다. 이러한 지침은 [ 런타임 보안 ]( runtime.md ) 섹션 에 설명된 지침과 함께 사용해야 합니다 .

## 추천

### 컨테이너 실행에 최적화된 OS 사용
Flatcar Linux, Project Atomic, RancherOS 및 Linux 컨테이너를 실행하도록 설계된 AWS의 특수 목적 OS인 [ Bottlerocket ]( https://github.com/bottlerocket-os/bottlerocket/ ) 사용을 고려하십시오. 여기에는 감소된 공격 표면, 부팅 시 확인되는 디스크 이미지, SELinux를 사용하는 강제 권한 경계가 포함됩니다.

또는 Kubernetes 작업자 노드에 대해 [ EKS 최적화 AMI ][eks-ami]를 사용합니다. EKS 최적화 AMI는 정기적으로 릴리스되며 컨테이너화된 워크로드를 실행하는 데 필요한 최소한의 OS 패키지 및 바이너리 세트를 포함합니다.

[eks-ami]: https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-amis.html

### 작업자 노드 OS를 최신 상태로 유지

Bottlerocket과 같은 컨테이너 최적화 호스트 OS를 사용하든 EKS 최적화 AMI와 같은 더 크지만 여전히 미니멀한 Amazon Machine Image를 사용하든 최신 보안 패치를 사용하여 이러한 호스트 OS 이미지를 최신 상태로 유지하는 것이 가장 좋습니다.

EKS 최적화 AMI의 경우 [ CHANGELOG ][eks-ami-changes] 및/또는 [ release notes channel ][eks-ami-releases]를 정기적으로 확인하고 업데이트된 작업자 노드 이미지를 클러스터로 자동 롤아웃합니다.

[eks-ami-변경]: https://github.com/awslabs/amazon-eks-ami/blob/master/CHANGELOG.md
[eks-ami-releases]: https://github.com/awslabs/amazon-eks-ami/releases

### 인프라를 불변으로 취급하고 작업자 노드 교체를 자동화하십시오.
전체 업그레이드를 수행하는 대신 새 패치 또는 업데이트가 제공되면 작업자를 교체하십시오. 이것은 몇 가지 방법으로 접근할 수 있습니다. 그룹의 모든 노드가 최신 AMI로 교체될 때까지 순차적으로 노드를 차단하고 배출하면서 최신 AMI를 사용하여 기존 Auto Scaling 그룹에 인스턴스를 추가할 수 있습니다. 또는 모든 노드가 교체될 때까지 이전 노드 그룹에서 노드를 순차적으로 차단하고 비우는 동안 새 노드 그룹에 인스턴스를 추가할 수 있습니다. EKS [ 관리형 노드 그룹 ]( https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html )은 첫 번째 접근 방식을 사용하며 다음과 같은 경우 작업자를 업그레이드하라는 메시지를 콘솔에 표시합니다. 새 AMI를 사용할 수 있게 됩니다. 또한 `eksctl` 에는 최신 AMI로 노드 그룹을 생성하고 인스턴스가 종료되기 전에 노드 그룹에서 포드를 정상적으로 차단 및 배출 하는 메커니즘이 있습니다. 작업자 노드를 교체하기 위해 다른 방법을 사용하기로 결정한 경우 새 업데이트/패치가 릴리스되고 컨트롤 플레인이 업그레이드될 때 작업자를 정기적으로 교체해야 할 가능성이 있으므로 사람의 감독을 최소화하도록 프로세스를 자동화하는 것이 좋습니다. .

EKS Fargate를 통해 AWS는 업데이트가 제공되면 기본 인프라를 자동으로 업데이트합니다. 종종 이 작업은 원활하게 수행될 수 있지만 업데이트로 인해 Pod 일정이 다시 조정되는 경우가 있을 수 있습니다. 따라서 애플리케이션을 Fargate 포드로 실행할 때 여러 복제본으로 배포를 생성하는 것이 좋습니다.

Kubernetes용 CIS 벤치마크 ]( https://www.cisecurity.org/benchmark/kubernetes/ ) 준수 여부 확인
kube-bench는 Kubernetes의 CIS 벤치마크에 대해 클러스터를 평가하는 Aqua의 오픈 소스 프로젝트입니다. 이 벤치마크는 관리되지 않는 Kubernetes 클러스터를 보호하기 위한 모범 사례를 설명합니다. CIS Kubernetes Benchmark는 컨트롤 플레인과 데이터 플레인을 포함합니다. Amazon EKS는 완전히 관리되는 제어 플레인을 제공하므로 CIS Kubernetes Benchmark의 모든 권장 사항이 적용되는 것은 아닙니다. 이 범위가 Amazon EKS 구현 방식을 반영하도록 AWS는 *CIS Amazon EKS 벤치마크* 를 생성했습니다 . EKS 벤치마크는 EKS 클러스터에 대한 특정 구성 고려 사항과 함께 커뮤니티의 추가 입력과 함께 CIS Kubernetes Benchmark에서 상속합니다.

EKS 클러스터에 대해 [ kube-bench ]( https://github.com/aquasecurity/kube-bench )를 실행할 때 [ 이 지침 ]( https://github.com/aquasecurity/kube-bench/blob/main )을 따르십시오. /docs/running.md#running-cis-benchmark-in-an-eks-cluster ) Aqua Security에서 제공합니다. 자세한 내용은 [ CIS Amazon EKS 벤치마크 소개 ]( https://aws.amazon.com/blogs/containers/introducing-cis-amazon-eks-benchmark/ )를 참조하십시오.

### 작업자 노드에 대한 액세스 최소화
SSH 액세스를 활성화하는 대신 호스트에 원격으로 접속해야 할 때 [ SSM 세션 관리자 ]( https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html )를 사용하십시오. 분실, 복사 또는 공유될 수 있는 SSH 키와 달리 세션 관리자를 사용하면 IAM을 사용하여 EC2 인스턴스에 대한 액세스를 제어할 수 있습니다. 또한 인스턴스에서 실행된 명령의 감사 추적 및 로그를 제공합니다.

2020년 8월 19일부터 관리형 노드 그룹은 사용자 지정 AMI 및 EC2 시작 템플릿을 지원합니다. 이를 통해 SSM 에이전트를 AMI에 포함하거나 작업자 노드가 부트스트랩될 때 설치할 수 있습니다. 최적화된 AMI 또는 ASG의 시작 템플릿을 수정하지 않는 경우 https://github.com/aws-samples/ssm-agent-daemonset-installer 예제와 같이 DaemonSet와 함께 SSM 에이전트를 설치할 수 있습니다.

#### SSM 기반 SSH 액세스를 위한 최소 IAM 정책

`AmazonSSMManagedInstanceCore` AWS 관리형 정책에는 SSH 액세스를 피하려는 경우 SSM Session Manager / SSM RunCommand에 필요하지 않은 여러 권한이 포함되어 있습니다 . 특히 우려되는 것은
ssm:GetParameter(s)` 에 대한 `*` 권한으로 역할이 Parameter Store의 모든 파라미터에 액세스할 수 있습니다(AWS 관리형 KMS 키가 구성된 SecureStrings 포함).

다음 IAM 정책에는 SSM Systems Manager를 통해 노드 액세스를 활성화하기 위한 최소 권한 집합이 포함되어 있습니다.

```json
{
  "버전" : "2012-10-17" ,
  "진술서" : [
{
      "Sid" : "EnableAccessViaSSMSessionManager" ,
      "효과" : "허용" ,
      "액션" : [
        "ssmmmessages:OpenDataChannel" ,
        "ssmmmessages:OpenControlChannel" ,
        "ssmmmessages:CreateDataChannel" ,
        "ssmmmessages:CreateControlChannel" ,
        "ssm:UpdateInstanceInformation"
],
      "자원" : "*"
},
{
      "시드" : "EnableSSMRunCommand" ,
      "효과" : "허용" ,
      "액션" : [
        "ssm:UpdateInstanceInformation" ,
        "ec2messages:SendReply" ,
        "ec2messages:GetMessages" ,
        "ec2messages:GetEndpoint" ,
        "ec2messages:FailMessage" ,
        "ec2messages:DeleteMessage" ,
        "ec2messages:AcknowledgeMessage"
],
      "자원" : "*"
}
]
}
```

이 정책이 적용되고 [ Session Manager 플러그인 ]( https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html )이 설치되어 있으면 그런 다음 실행할 수 있습니다
```강타
aws ssm 시작 세션 --target [INSTANCE_ID_OF_EKS_NODE]
```
노드에 액세스합니다.

!!! 노트
Session Manager 로깅 활성화 ]( https://docs.aws.amazon.com/systems-manager/latest/userguide/getting-started-create-iam-instance-profile.html# 에 대한 권한 추가를 고려할 수도 있습니다. create-iam-instance-profile-ssn-logging ).

### 프라이빗 서브넷에 작업자 배포
개인 서브넷에 작업자를 배포하면 공격이 자주 발생하는 인터넷에 대한 노출을 최소화할 수 있습니다. 2020년 4월 22일부터 관리형 노드 그룹의 노드에 대한 공용 IP 주소 할당은 배포된 서브넷에 의해 제어됩니다. 이전에는 관리 노드 그룹의 노드에 공용 IP가 자동으로 할당되었습니다. 작업자 노드를 퍼블릭 서브넷에 배포하기로 선택한 경우 제한적인 AWS 보안 그룹 규칙을 구현하여 노출을 제한하십시오.

### Amazon Inspector를 실행하여 호스트의 노출, 취약성 및 모범 사례와의 편차를 평가합니다.
[ Amazon Inspector ]( https://docs.aws.amazon.com/inspector/latest/user/what-is-inspector.html )를 사용하여 노드에 대한 의도하지 않은 네트워크 액세스와 기본 Amazon의 취약성을 확인할 수 있습니다. EC2 인스턴스.

Amazon Inspector는 Amazon EC2 Systems Manager(SSM) 에이전트가 설치되고 활성화된 경우에만 Amazon EC2 인스턴스에 대한 공통 취약성 및 노출(CVE) 데이터를 제공할 수 있습니다. 이 에이전트는 [ EKS 최적화 Amazon Linux AMI 를 포함하여 여러 [ Amazon 머신 이미지(AMI) ]( https://docs.aws.amazon.com/systems-manager/latest/userguide/ami-preinstalled-agent.html )에 사전 설치되어 있습니다. ]( https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html ). SSM 에이전트 상태와 관계없이 모든 Amazon EC2 인스턴스에서 네트워크 연결 문제를 스캔합니다. Amazon EC2 스캔 구성에 대한 자세한 내용은 [ Amazon EC2 인스턴스 스캔 ]( https://docs.aws.amazon.com/inspector/latest/user/enable-disable-scanning-ec2.html )을 참조하십시오.

!!! 주목
Fargate 포드를 실행하는 데 사용되는 인프라에서는 Inspector를 실행할 수 없습니다.

## 대안

### SELinux 실행

!!! 정보
RHEL(Red Hat Enterprise Linux), CentOS 및 CoreOS에서 사용 가능

SELinux는 컨테이너를 서로 간에 그리고 호스트로부터 격리된 상태로 유지하기 위해 추가 보안 계층을 제공합니다. SELinux를 통해 관리자는 모든 사용자, 애플리케이션, 프로세스 및 파일에 대해 필수 액세스 제어(MAC)를 시행할 수 있습니다. 레이블 세트를 기반으로 특정 리소스에 대해 수행할 수 있는 작업을 제한 하는 백스톱으로 생각하십시오 . EKS에서 SELinux를 사용하여 컨테이너가 서로의 리소스에 액세스하지 못하도록 할 수 있습니다.

컨테이너 SELinux 정책은 [ container-selinux ]( https://github.com/containers/container-selinux ) 패키지에 정의되어 있습니다. Docker CE는 Docker(또는 다른 컨테이너 런타임)에서 생성된 프로세스 및 파일이 제한된 시스템 액세스로 실행되도록 이 패키지(종속성과 함께)가 필요합니다. 컨테이너 는 `svirt_lxc_net_t` 의 별칭인 `container_t` 레이블을 활용합니다 . 이러한 정책은 컨테이너가 호스트의 특정 기능에 액세스하는 것을 효과적으로 방지합니다.

Docker용 SELinux를 구성하면 Docker는 자동으로 워크로드 'container_t' 에 유형으로 레이블을 지정하고 각 컨테이너에 고유한 MCS 수준을 부여합니다. 이렇게 하면 컨테이너가 서로 격리됩니다. 보다 느슨한 제한이 필요한 경우 SElinux에서 파일 시스템의 특정 영역에 대한 컨테이너 권한을 부여하는 고유한 프로필을 만들 수 있습니다. 이는 다른 컨테이너/포드에 대해 다른 프로필을 생성할 수 있다는 점에서 PSP와 유사합니다. 예를 들어 제한적인 제어 집합이 있는 일반 워크로드에 대한 프로필과 액세스 권한이 필요한 항목에 대한 프로필이 있을 수 있습니다.

SELinux for Containers에는 기본 제한을 수정하도록 구성할 수 있는 옵션 세트가 있습니다. 다음 SELinux 부울은 필요에 따라 활성화하거나 비활성화할 수 있습니다.

| 부울 | 기본값 | 설명|
|---|:--:|---|
| `container_connect_any` | '꺼짐' | 컨테이너가 호스트의 권한 있는 포트에 액세스하도록 허용합니다. 예를 들어 포트를 호스트의 443 또는 80에 매핑해야 하는 컨테이너가 있는 경우입니다. |
| `container_manage_cgroup` | '꺼짐' | 컨테이너가 cgroup 구성을 관리하도록 허용합니다. 예를 들어 systemd를 실행하는 컨테이너는 이를 활성화해야 합니다. |
| `container_use_cephfs` | '꺼짐' | 컨테이너가 ceph 파일 시스템을 사용하도록 허용합니다. |

기본적으로 컨테이너는 `/usr`에서 읽기/실행이 허용되고 `/etc` 에서 대부분의 콘텐츠를 읽을 수 있습니다. `/var/lib/docker` 및 `/var/lib/containers` 아래의 파일에는 `container_var_lib_t` 레이블이 있습니다 . 기본값의 전체 목록을 보려면 [ container.fc ]( https://github.com/containers/container-selinux/blob/master/container.fc ) 파일을 참조하십시오.

```강타
도커 컨테이너 실행 -it \
-v /var/lib/docker/image/overlay2/repositories.json:/host/repositories.json \
centos:7 고양이 /host/repositories.json
# cat: /host/repositories.json: 권한이 거부되었습니다.

도커 컨테이너 실행 -it \
-v /etc/passwd:/호스트/etc/passwd \
centos:7 고양이 /호스트/etc/passwd
# cat: /host/etc/passwd: 권한이 거부되었습니다.
```

`container_file_t` 레이블이 지정된 파일은 컨테이너에서 쓸 수 있는 유일한 파일입니다. 볼륨 마운트를 쓰기 가능하게 하려면 끝에 ` :z` 또는 `:Z` 를 지정해야 합니다.

- `:z` 는 컨테이너가 읽고 쓸 수 있도록 파일의 레이블을 다시 지정합니다.
- `:Z` 는 **만** 컨테이너가 읽고 쓸 수 있도록 파일에 레이블을 다시 지정합니다.

```강타
ls -Z /var/lib/misc
# -rw-r--r--. 루트 루트 system_u:object_r:var_lib_t:s0 postfix.aliasesdb-stamp

도커 컨테이너 실행 -it \
-v /var/lib/misc:/host/var/lib/misc:z \
센토스:7 에코 "재명명!"

ls -Z /var/lib/misc
#-rw-r--r--. 루트 루트 system_u:object_r:container_file_t:s0 postfix.aliasesdb-stamp
```

```강타
도커 컨테이너 실행 -it \
-v /var/log:/host/var/log:Z \
fluentbit:최신
```

Kubernetes에서 레이블 재지정은 약간 다릅니다. Docker가 자동으로 파일의 레이블을 다시 지정하도록 하는 대신 사용자 지정 MCS 레이블을 지정하여 포드를 실행할 수 있습니다. 레이블 재지정을 지원하는 볼륨은 액세스할 수 있도록 자동으로 레이블이 재지정됩니다. 일치하는 MCS 레이블이 있는 포드는 볼륨에 액세스할 수 있습니다. 엄격한 격리가 필요한 경우 각 팟(Pod)에 대해 다른 MCS 레이블을 설정하십시오.

```yaml
보안 컨텍스트 :
  seLinux 옵션 :
    # 용기별로 고유한 MCS 라벨 제공
    # 사용자, 역할 및 유형을 지정할 수도 있습니다.
    # 유형 및 수준에 따른 시행(svert)
    레벨 : s0:c144:c154
```

이 예에서 `s0:c144:c154` 는 컨테이너가 액세스할 수 있는 파일에 할당된 MCS 레이블에 해당합니다.

하고 호스트 디렉터리의 레이블을 다시 지정할 필요 없이 호스트의 /var/log에서 읽을 수 있도록 SELinux 정책을 생성할 수 있습니다 . 레이블이 동일한 포드는 동일한 호스트 볼륨에 액세스할 수 있습니다.

[ Amazon EKS용 샘플 AMI ]( https://github.com/aws-samples/amazon-eks-custom-amis )를 구현했습니다. 이러한 AMI는 샘플 구현을 시연하기 위해 개발되었습니다. STIG, CJIS 및 C2S와 같이 규제가 엄격한 고객의 요구 사항을 충족합니다.

!!! 주의
SELinux는 유형이 제한되지 않은 컨테이너를 무시합니다.

#### 추가 리소스
+ [ 온프레미스 애플리케이션을 위한 SELinux Kubernetes RBAC 및 배송 보안 정책 ]( https://platform9.com/blog/selinux-kubernetes-rbac-and-shipping-security-policies-for-on-prem-applications/ )
+ [ 쿠버네티스의 반복 강화 ]( https://jayunit100.blogspot.com/2019/07/iterative-hardening-of-kubernetes-and.html )
+ [ Audit2Allow ]( https://linux.die.net/man/1/audit2allow )
+ [ SEAlert ]( https://linux.die.net/man/8/sealert )
+ [ Udica를 사용하여 컨테이너에 대한 SELinux 정책 생성 ]( https://www.redhat.com/en/blog/generate-selinux-policies-containers-with-udica )은 Linux 기능에 대한 컨테이너 사양 파일을 확인하는 도구를 설명합니다. 포트, 마운트 지점, 컨테이너가 제대로 실행되도록 하는 일련의 SELinux 규칙 생성
+ [ AMI Hardening ]( https://github.com/aws-samples/amazon-eks-custom-amis#hardening ) 다양한 규제 요구 사항을 충족하기 위해 OS를 강화하기 위한 플레이북

## 도구
+ [ Keiko Upgrade Manager ]( https://github.com/keikoproj/upgrade-manager ) 작업자 노드의 회전을 오케스트레이션하는 Intuit의 오픈 소스 프로젝트.
+ [ Sysdig Secure ]( https://sysdig.com/products/kubernetes-security/ )
+ [ eksctl ]( https://eksctl.io/ )


