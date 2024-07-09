---
search:
  exclude: true
---


# 인프라(호스트) 보호

컨테이너 이미지를 보호하는 것도 중요하지만 이미지를 실행하는 인프라를 보호하는 것도 마찬가지로 중요합니다. 이 섹션에서는 호스트를 대상으로 직접 시작된 공격으로 인한 위험을 완화하는 다양한 방법을 살펴봅니다. 이 지침은 [런타임 보안](runtime.md) 섹션에 설명된 지침과 함께 사용해야 합니다.

## 권장 사항

### 컨테이너 실행에 최적화된 OS 사용

Flatcar Linux, Project Atomic, RancherOS 및 리눅스 컨테이너 실행을 위해 설계된 AWS의 컨테이너 실행 최적화 OS인 [Bottlerocket](https://github.com/bottlerocket-os/bottlerocket/)을 사용해 보세요. 이것은 공격 표면 감소, 부팅 시 검증된 디스크 이미지, SELinux를 사용한 권한 제한 등이 포함하고 있습니다.

또는 쿠버네티스 워커 노드에 [EKS 최적화 AMI][eks-ami]를 사용할 수 있습니다. EKS 최적화 AMI는 정기적으로 릴리스되며 컨테이너식 워크로드를 실행하는 데 필요한 최소한의 OS 패키지 및 바이너리 세트를 포함합니다.

[eks-ami]: https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-amis.html

### 워커 노드 OS를 최신 상태로 유지

Bottlerocket과 같은 컨테이너에 최적화된 호스트 OS를 사용하거나 EKS 최적화 AMI와 같은 Amazon 머신 이미지를 사용하고 최신 보안 패치를 사용하여 이런 호스트 OS 이미지를 최신 상태로 유지하는 것이 가장 좋습니다.

EKS 최적화 AMI의 경우 [변경 로그][eks-ami-changes] 또는 [릴리스 노트 채널][eks-ami-releases]를 정기적으로 확인하고 업데이트된 워커 노드 이미지를 클러스터로 자동 롤아웃합니다.

[eks-ami-changes]: https://github.com/awslabs/amazon-eks-ami/blob/master/CHANGELOG.md
[eks-ami-releases]: https://github.com/awslabs/amazon-eks-ami/releases

### 인프라를 변경할 수 없는 대상으로 분류하고 워커 노드 교체를 자동화하십시오

전체 업그레이드를 수행하는 대신 새 패치 또는 업데이트가 제공되면 워커 노드를 교체합니다. 몇 가지 방법으로 이 문제를 해결할 수 있습니다. 그룹의 모든 노드가 최신 AMI로 교체될 때까지 순차적으로 노드를 차단하고 드레이닝하는 최신 AMI를 사용하여 기존 자동 확장 그룹에 인스턴스를 추가할 수도 있습니다. 또는 모든 노드가 교체될 때까지 이전 노드 그룹에서 노드를 순차적으로 차단하고 제거하면서 새 노드 그룹에 인스턴스를 추가할 수도 있습니다. EKS [관리형 노드 그룹](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html)은 첫 번째 접근 방식을 사용하며 새 AMI를 사용할 수 있게 되면 콘솔에 작업자를 업그레이드하라는 메시지를 표시합니다. 또한 'eksctl'에는 최신 AMI로 노드 그룹을 생성하고 인스턴스가 종료되기 전에 노드 그룹에서 파드를 정상적으로 차단하고 드레이닝하는 메커니즘이 있습니다. 워커 노드를 교체하는 데 다른 방법을 사용하기로 결정한 경우, 새 업데이트/패치가 릴리스되고 컨트롤 플레인이 업그레이드될 때 작업자를 정기적으로 교체해야 할 수 있으므로 프로세스를 자동화하여 사람의 감독을 최소화하는 것이 좋습니다.

EKS Fargate를 사용하면 AWS는 업데이트가 제공되는 대로 기본 인프라를 자동으로 업데이트합니다.이 작업을 원활하게 수행할 수 있는 경우가 많지만 업데이트로 인해 파드 일정이 변경되는 경우가 있을 수 있습니다.따라서 애플리케이션을 Fargate 파드로 실행할 때는 여러 복제본으로 배포를 생성하는 것이 좋습니다.

### kube-bench를 주기적으로 실행하여 [쿠버네티스에 대한 CIS 벤치마크](https://www.cisecurity.org/benchmark/kubernetes/) 준수 여부를 확인합니다

kube-bench는 쿠버네티스의 CIS 벤치마크와 비교하여 클러스터를 평가하는 Aqua의 오픈 소스 프로젝트입니다. 벤치마크는 관리되지 않는 쿠버네티스 클러스터를 보호하는 모범 사례를 설명합니다. CIS 쿠버네티스 벤치마크는 컨트롤 플레인과 데이터 플레인을 포함합니다. Amazon EKS는 완전 관리형 컨트롤 플레인을 제공하므로 CIS 쿠버네티스 벤치마크의 모든 권장 사항이 적용되는 것은 아닙니다. 이 범위에 Amazon EKS 구현 방식이 반영되도록 AWS는 *CIS Amazon EKS 벤치마크*를 만들었습니다. EKS 벤치마크는 CIS 쿠버네티스 벤치마크를 계승하고 EKS 클러스터의 특정 구성 고려 사항과 함께 커뮤니티의 추가 의견을 반영합니다.

EKS 클러스터에 대해 [kube-bench](https://github.com/aquasecurity/kube-bench)를 실행할 때는 아쿠아 시큐리티의 [이 지침](https://github.com/aquasecurity/kube-bench/blob/main/docs/running.md#running-cis-benchmark-in-an-eks-cluster)을 따릅니다. 자세한 내용은 [CIS Amazon EKS 벤치마크 소개](https://aws.amazon.com/blogs/containers/introducing-cis-amazon-eks-benchmark/)를 참조합니다.

### 워커 노드에 대한 액세스 최소화

호스트에 원격으로 접속해야 할 때는 SSH 액세스를 활성화하는 대신 [SSM Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)를 사용합니다. 분실, 복사 또는 공유될 수 있는 SSH 키와 달리 세션 관리자에서는 IAM을 사용하여 EC2 인스턴스에 대한 액세스를 제어할 수 있습니다. 또한 인스턴스에서 실행된 명령에 대한 감사 추적 및 로그를 제공합니다.

2020년 8월 19일부터 관리형 노드 그룹은 사용자 지정 AMI와 EC2 시작 템플릿(Launch Template)을 지원합니다. 이를 통해 SSM 에이전트를 AMI에 내장하거나 워커 노드가 부트스트랩될 때 설치할 수 있습니다. 최적화된 AMI 또는 ASG의 시작 템플릿을 수정하지 않는 경우, 이 [예시](https://github.com/aws-samples/ssm-agent-daemonset-installer)에서처럼 데몬셋을 사용하여 SSM 에이전트를 설치할 수 있습니다.

#### SSM 기반 SSH 액세스를 위한 최소 IAM 정책

`AmazonSSMManagedInstanceCore` AWS 관리형 정책에는 SSH 액세스를 피하려는 경우 SSM Session Manager 및 SSM RunCommand에 필요하지 않은 여러 권한이 포함되어 있습니다.
특히 우려되는 것은 `SSM:GetParameter (s)`에 대한 `*` 권한입니다. 이렇게 하면 해당 역할이 파라미터 스토어의 모든 파라미터(AWS 관리형 KMS 키가 구성된 SecureString 포함)에 액세스할 수 있게 됩니다.

다음 IAM 정책에는 SSM Systems Manager를 통해 노드 액세스를 활성화하기 위한 최소 권한 세트가 포함되어 있습니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EnableAccessViaSSMSessionManager",
      "Effect": "Allow",
      "Action": [
        "ssmmessages:OpenDataChannel",
        "ssmmessages:OpenControlChannel",
        "ssmmessages:CreateDataChannel",
        "ssmmessages:CreateControlChannel",
        "ssm:UpdateInstanceInformation"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EnableSSMRunCommand",
      "Effect": "Allow",
      "Action": [
        "ssm:UpdateInstanceInformation",
        "ec2messages:SendReply",
        "ec2messages:GetMessages",
        "ec2messages:GetEndpoint",
        "ec2messages:FailMessage",
        "ec2messages:DeleteMessage",
        "ec2messages:AcknowledgeMessage"
      ],
      "Resource": "*"
    }
  ]
}
```

이 정책을 적용하고 [Session Manager 플러그인](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)을 설치하면 다음을 실행하여 노드에 접속합니다.

```bash
aws ssm start-session --target [INSTANCE_ID_OF_EKS_NODE]
```

!!! note
    [Session Manager 로깅 활성화](https://docs.aws.amazon.com/systems-manager/latest/userguide/getting-started-create-iam-instance-profile.html#create-iam-instance-profile-ssn-logging)에 권한을 추가하는 것도 고려해 볼 수 있습니다.

### 프라이빗 서브넷에 워커 노드 배포

워커 노드를 프라이빗 서브넷에 배치하면 공격이 자주 발생하는 인터넷에 대한 노출을 최소화할 수 있습니다. 2020년 4월 22일부터 관리형 노드 그룹의 노드에 대한 퍼블릭 IP 주소 할당은 해당 노드가 배포되는 서브넷에 의해 제어됩니다. 이전에는 관리형 노드 그룹의 노드에 퍼블릭 IP가 자동으로 할당되었습니다. 워커 노드를 퍼블릭 서브넷에 배포하기로 선택한 경우, 제한적인 AWS 보안 그룹 규칙을 구현하여 노출을 제한합니다.

### Amazon Inspector를 실행하여 호스트의 노출, 취약성 및 모범 사례와의 편차를 평가하십시오

[Amazon Inspector](https://docs.aws.amazon.com/inspector/latest/user/what-is-inspector.html)를 사용하여 노드에 대한 의도하지 않은 네트워크 액세스와 기본 Amazon EC2 인스턴스의 취약성을 확인할 수 있습니다.

Amazon Inspector는 Amazon EC2 Systems Manager(SSM) 에이전트가 설치되고 활성화된 경우에만 Amazon EC2 인스턴스에 대한 일반적인 취약성 및 노출 (CVE) 데이터를 제공할 수 있습니다. 이 에이전트는 [EKS 최적화 Amazon Linux AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html)를 비롯한 여러 [Amazon 머신 이미지 (AMI)](https://docs.aws.amazon.com/systems-manager/latest/userguide/ami-preinstalled-agent.html)에 사전 설치되어 있습니다. SSM 에이전트 상태에 관계없이 모든 Amazon EC2 인스턴스는 네트워크 연결 문제 여부를 검사합니다.Amazon EC2용 스캔 구성에 대한 자세한 내용은 [Amazon EC2 인스턴스 스캔](https://docs.aws.amazon.com/inspector/latest/user/enable-disable-scanning-ec2.html)을 참조합니다.

!!! attention
    Fargate 파드를 실행하는 데 사용되는 인프라에서는 Inspector를 실행할 수 없습니다.

## 대안으로 선택 가능한 옵션

### SELinux 실행

!!! info
    RHEL(Red Hat Enterprise Linux), CentOS, Bottlerocket과 Amazon Linux 2023 에서 사용 가능

SELinux는 컨테이너를 서로 격리하고 호스트로부터 격리된 상태로 유지하기 위한 추가 보안 계층을 제공합니다. SELinux를 통해 관리자는 모든 사용자, 애플리케이션, 프로세스 및 파일에 대해 필수 액세스 제어(MAC)를 적용할 수 있습니다. 레이블 집합을 기반으로 특정 리소스에 대해 수행할 수 있는 작업을 제한하는 안정장치라고 생각하면 됩니다. EKS에서는 SELinux를 사용하여 컨테이너가 서로의 리소스에 액세스하는 것을 방지할 수 있습니다.

컨테이너 SELinux 정책은 [container-selinux](https://github.com/containers/container-selinux) 패키지에 정의되어 있습니다. Docker CE에는 Docker(또는 다른 컨테이너 런타임)에서 생성한 프로세스와 파일이 제한된 시스템 액세스로 실행되도록 하려면 이 패키지 (종속 항목 포함)가 필요합니다.컨테이너는 `svirt_lxc_net_t`의 별칭인 `container_t` 레이블을 활용합니다. 이런 정책은 컨테이너가 호스트의 특정 기능에 액세스하는 것을 효과적으로 방지합니다.

Docker용 SELinux를 구성하면 Docker는 워크로드에 `container_t` 레이블링하여 타입으로 자동으로 인식하고 각 컨테이너에 고유한 MCS 레벨을 부여합니다. 이렇게 하면 컨테이너가 서로 격리됩니다. 보다 엄격한 제한이 필요한 경우 SELinux에서 파일 시스템의 특정 영역에 대한 컨테이너 권한을 부여하는 자체 프로파일을 만들 수 있습니다. 이는 컨테이너/파드마다 다른 프로파일을 생성할 수 있다는 점에서 PSP와 비슷합니다. 예를 들어, 일련의 제한적인 제어가 포함된 일반 워크로드용 프로파일과 권한 있는 액세스가 필요한 항목에 대한 프로파일을 각각 가질 수 있습니다.

컨테이너용 SELinux에는 기본 제한을 수정하도록 구성할 수 있는 옵션 세트가 있습니다. 필요에 따라 다음과 같은 SELinux Booleans를 활성화하거나 비활성화할 수 있습니다.

| Boolean | Default | Description|
|---|:--:|---|
| `container_connect_any` | `off` | 컨테이너가 호스트의 권한 있는 포트에 액세스할 수 있도록 허용합니다. 호스트의 443 또는 80에 포트를 매핑해야 하는 컨테이너가 있는 경우를 예로 들 수 있습니다. |
| `container_manage_cgroup` | `off` | 컨테이너가 cgroup 구성을 관리할 수 있도록 허용합니다. 예를 들어 systemd를 실행하는 컨테이너는 이 기능을 활성화해야 합니다. |
| `container_use_cephfs` | `off` | 컨테이너가 ceph 파일 시스템을 사용할 수 있도록 허용합니다. |

기본적으로 컨테이너는 `/usr`에서 읽고 실행할 수 있으며 `/etc`에서 대부분의 콘텐츠를 읽을 수 있습니다. `/var/lib/docker` 및 `/var/lib/containers` 아래의 파일에는 `container_var_lib_t`라는 레이블이 붙어 있습니다. 기본 레이블의 전체 목록을 보려면 [container.fc](https://github.com/containers/container-selinux/blob/master/container.fc) 파일을 참조합니다.

```bash
docker container run -it \
  -v /var/lib/docker/image/overlay2/repositories.json:/host/repositories.json \
  centos:7 cat /host/repositories.json
# cat: /host/repositories.json: Permission denied

docker container run -it \
  -v /etc/passwd:/host/etc/passwd \
  centos:7 cat /host/etc/passwd
# cat: /host/etc/passwd: Permission denied
```

`container_file_t`로 레이블이 지정된 파일은 컨테이너에서 쓸 수 있는 유일한 파일입니다. 볼륨 마운트를 쓰기 가능하게 하려면 끝에 `:z` 또는 `:Z`를 지정해야 합니다.

- `:z` 는 컨테이너가 읽고 쓸 수 있도록 파일의 레이블을 다시 지정합니다.
- `:Z` 는  컨테이너**만** 읽고 쓸 수 있도록 파일에 레이블을 다시 지정합니다.

```bash
ls -Z /var/lib/misc
# -rw-r--r--. root root system_u:object_r:var_lib_t:s0   postfix.aliasesdb-stamp

docker container run -it \
  -v /var/lib/misc:/host/var/lib/misc:z \
  centos:7 echo "Relabeled!"

ls -Z /var/lib/misc
#-rw-r--r--. root root system_u:object_r:container_file_t:s0 postfix.aliasesdb-stamp
```

```bash
docker container run -it \
  -v /var/log:/host/var/log:Z \
  fluentbit:latest
```

쿠버네티스에서는 레이블을 다시 지정하는 방식이 약간 다릅니다. Docker가 파일의 레이블을 자동으로 다시 지정하도록 하는 대신 사용자 지정 MCS 레이블을 지정하여 파드를 실행할 수 있습니다. 레이블 재지정을 지원하는 볼륨은 액세스할 수 있도록 자동으로 레이블이 다시 지정됩니다. MCS 레이블이 일치하는 파드는 해당 볼륨에 접근할 수 있다. 엄격한 격리가 필요한 경우 각 파드에 다른 MCS 레이블을 설정하세요.

```yaml
securityContext:
  seLinuxOptions:
    # Provide a unique MCS label per container
    # You can specify user, role, and type also
    # enforcement based on type and level (svert)
    level: s0:c144:c154
```

이 예제에서 `s0:c144:c154`는 컨테이너의 액세스가 허용된 파일에 할당된 MCS 레이블에 해당합니다.

EKS에서는 FluentD와 같은 권한 있는 컨테이너를 실행할 수 있는 정책을 생성하고 호스트 디렉터리에 레이블을 다시 지정할 필요 없이 호스트의 /var/log에서 읽을 수 있도록 허용하는 SELinux 정책을 생성할 수 있습니다. 레이블이 같은 파드는 동일한 호스트 볼륨에 액세스할 수 있습니다.

CentOS7 및 RHEL7에 SELinux가 구성된 [Amazon EKS 샘플 AMI](https://github.com/aws-samples/amazon-eks-custom-amis)를 구현했습니다. 이런 AMI는 STIG, CJIS, C2S와 같이 규제가 엄격한 고객의 요구 사항을 충족하는 샘플 구현을 시연하기 위해 개발되었습니다.

!!! caution
  SELinux는 타입이 제한되지 않은 컨테이너를 무시합니다.

## 도구 및 리소스

- [온프레미스 애플리케이션을 위한 SELinux, 쿠버네티스 RBAC 및 보안 정책](https://platform9.com/blog/selinux-kubernetes-rbac-and-shipping-security-policies-for-on-prem-applications/)
- [쿠버네티스의 반복적 하드닝](https://jayunit100.blogspot.com/2019/07/iterative-hardening-of-kubernetes-and.html)
- [Audit2Allow](https://linux.die.net/man/1/audit2allow)
- [SEAlert](https://linux.die.net/man/8/sealert)
- [Udica를 사용하여 컨테이너에 대한 SELinux 정책 생성](https://www.redhat.com/en/blog/generate-selinux-policies-containers-with-udica)은 Linux 기능에 대한 컨테이너 사양 파일을 확인하는 도구를 설명합니다. 포트, 마운트 지점, 컨테이너가 제대로 실행되도록 하는 일련의 SELinux 규칙을 생성합니다.
- [AMI Hardening](https://github.com/aws-samples/amazon-eks-custom-amis#hardening)은 다양한 규제 요구 사항을 충족하기 위해 OS를 강화하기 위한 플레이북입니다.
- [Keiko Upgrade Manager](https://github.com/keikoproj/upgrade-manager)는 워커 노드의 회전을 오케스트레이션하는 Intuit의 오픈 소스 프로젝트입니다.
- [Sysdig Secure](https://sysdig.com/products/kubernetes-security/)
- [eksctl](https://eksctl.io/)
