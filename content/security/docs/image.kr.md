# 이미지 보안
컨테이너 이미지는 공격에 대한 첫 번째 방어선으로 고려됩니다. 안전하지 않고 잘못 구성된 이미지는 공격자는 컨테이너의 경계를 벗어나 호스트에 액세스할 수 있도록 합니다. 호스트에 들어가면 공격자는 민감한 정보에 액세스하거나 클러스터 내 또는 AWS 계정 내에 접근할 수 있습니다. 다음 모범 사례는 이러한 상황이 발생할 위험을 완화하는 데 도움이 됩니다.

## 권장 사항
### 최소 이미지 생성
먼저 컨테이너 이미지에서 관련 없는 바이너리를 모두 제거합니다. Dockerhub의 익숙하지 않은 이미지를 사용하는 경우 각 컨테이너 레이어의 내용을 보여줄 수 있는 [Dive](https://github.com/wagoodman/dive)와 같은 애플리케이션을 사용하여 이미지를 검사합니다. 권한을 승격하는 데 사용할 수 있는 SETUID 및 SETGID 비트가 있는 모든 바이너리를 제거하고 nc나 curl과 같이 악의적인 용도로 사용될 수 있는 셸과 유틸리티를 모두 제거하는 것을 고려합니다. 다음 명령을 사용하여 SETUID 및 SETGID 비트가 있는 파일을 찾을 수 있습니다.

```
find / -perm /6000 -type f -exec ls -ld {} \;
```
    
이러한 파일에서 특수 권한을 제거하려면 컨테이너 이미지에 다음 지시문을 추가합니다.

```docker
RUN find / -xdev -perm /6000 -type f -exec chmod a-s {} \; || true
```

  

### 멀티 스테이지 빌드 사용
멀티 스테이지 빌드를 사용하면 최소한의 이미지를 만들 수 있습니다. 지속적 통합 주기의 일부를 자동화하는 데 멀티 스테이지 빌드를 사용하는 경우가 많습니다. 예를 들어 멀티 스테이지 빌드를 사용하여 소스 코드를 린트하거나 정적 코드 분석을 수행할 수 있습니다. 이를 통해 개발자는 파이프라인 실행을 기다릴 필요 없이 거의 즉각적인 피드백을 받을 수 있습니다. 멀티 스테이지 빌드는 컨테이너 레지스트리로 푸시되는 최종 이미지의 크기를 최소화할 수 있기 때문에 보안 관점에서 매력적입니다. 빌드 도구 및 기타 관련 없는 바이너리가 없는 컨테이너 이미지는 이미지의 공격 표면을 줄여 보안 상태를 개선합니다. 멀티 스테이지 빌드에 대한 추가 정보는 [본 문서](https://docs.docker.com/develop/develop-images/multistage-build/)를 참조합니다.

### 컨테이너 이미지를 위한 소프트웨어 재료 명세서 (sBOM) 생성
“소프트웨어 재료 명세서" (SBOM) 는 컨테이너 이미지를 구성하는 소프트웨어 아티팩트의 중첩된 인벤토리입니다.
SBOM은 소프트웨어 보안 및 소프트웨어 공급망 위험 관리의 핵심 구성 요소입니다.[SBOM을 생성하여 중앙 리포지토리에 저장하고 sBOM의 취약성 검사](https://anchore.com/sbom/)는 다음과 같은 문제를 해결하는 데 도움이 됩니다.

* **가시성**: 컨테이너 이미지를 구성하는 구성 요소를 이해합니다. 중앙 리포지토리에 저장하면 배포 이후에도 언제든지 sBOM을 감사 및 스캔하여 제로 데이 취약성과 같은 새로운 취약성을 탐지하고 이에 대응할 수 있습니다.
* **출처 검증**: 아티팩트의 출처 및 출처에 대한 기존 가정이 사실이고 빌드 또는 제공 프로세스 중에 아티팩트 또는 관련 메타데이터가 변조되지 않았음을 보증합니다.
* **신뢰성**: 특정 유물과 그 내용물이 의도한 작업, 즉 목적에 적합하다는 것을 신뢰할 수 있다는 보장. 여기에는 코드를 실행하기에 안전한지 판단하고 코드 실행과 관련된 위험에 대해 정보에 입각한 결정을 내리는 것이 포함됩니다. 인증된 SBOM 및 인증된 CVE 스캔 보고서와 함께 검증된 파이프라인 실행 보고서를 작성하여 이미지 소비자에게 이 이미지가 실제로 보안 구성 요소를 갖춘 안전한 수단 (파이프라인) 을 통해 생성되었음을 확인하면 신뢰성이 보장됩니다.
* **종속성 신뢰 확인**: 아티팩트의 종속성 트리가 사용하는 아티팩트의 신뢰성과 출처를 반복적으로 검사합니다. sBOM의 드리프트는 신뢰할 수 없는 무단 종속성, 침입 시도 등 악의적인 활동을 탐지하는 데 도움이 될 수 있습니다.

다음 도구를 사용하여 SBOM을 생성할 수 있습니다:

* [Amazon Inspector](https://docs.aws.amazon.com/inspector)를 사용하여 [sBOM 생성 및 내보내기](https://docs.aws.amazon.com/inspector/latest/user/sbom-export.html)를 수행할 수 있습니다.
* [Syft from Anchore](https://github.com/anchore/syft) 는 SBOM 생성에도 사용할 수 있습니다. 취약성 스캔을 더 빠르게 하기 위해 컨테이너 이미지에 대해 생성된 SBOM을 스캔을 위한 입력으로 사용할 수 있습니다. 그런 다음 검토 및 감사 목적으로 이미지를 Amazon ECR과 같은 중앙 OCI 리포지토리로 푸시하기 전에 SBOM 및 스캔 보고서를 이미지에 [증명 및 첨부](https://github.com/sigstore/cosign/blob/main/doc/cosign_attach_attestation.md)합니다.

[CNCF 소프트웨어 공급망 모범 사례 가이드](https://project.linuxfoundation.org/hubfs/CNCF_SSCP_v1.pdf)를 검토하고 소프트웨어 공급망 보안에 대해 자세히 알아보세요.

### 취약점이 있는지 이미지를 정기적으로 스캔
가상 머신과 마찬가지로 컨테이너 이미지에는 취약성이 있는 바이너리와 애플리케이션 라이브러리가 포함되거나 시간이 지남에 따라 취약성이 발생할 수 있습니다. 악용으로부터 보호하는 가장 좋은 방법은 이미지 스캐너로 이미지를 정기적으로 스캔하는 것입니다. Amazon ECR에 저장된 이미지는 푸시 또는 온디맨드로 스캔할 수 있습니다. (24시간 동안 한 번) ECR은 현재 [두 가지 유형의 스캔 - 기본 및 고급](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html)을 지원합니다. 기본 스캔은 [Clair](https://github.com/quay/clair)의 오픈 소스 이미지 스캔 솔루션을 무료로 활용합니다. [고급 스캔](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning-enhanced.html)은 [추가 비용](https://aws.amazon.com/inspector/pricing/)이 과금되며 Amazon Inspector를 사용하여 자동 연속 스캔을 제공합니다. 이미지를 스캔한 후 결과는 EventBridge의 ECR용 이벤트 스트림에 기록됩니다. ECR 콘솔 내에서 스캔 결과를 볼 수도 있습니다. 심각하거나 심각한 취약성이 있는 이미지는 삭제하거나 다시 빌드해야 합니다. 배포된 이미지에서 취약점이 발견되면 가능한 한 빨리 교체해야 합니다.

취약성이 있는 이미지가 배포된 위치를 아는 것은 환경을 안전하게 유지하는 데 필수적입니다. 이미지 추적 솔루션을 직접 구축할 수도 있지만, 다음과 같이 이 기능을 비롯한 기타 고급 기능을 즉시 사용할 수 있는 상용 제품이 이미 여러 개 있습니다.

* [Grype](https://github.com/anchore/grype)
* [Palo Alto - Prisma Cloud (twistcli)](https://docs.paloaltonetworks.com/prisma/prisma-cloud/prisma-cloud-admin-compute/tools/twistcli_scan_images)
* [Aqua](https://www.aquasec.com/)
* [Kubei](https://github.com/Portshift/kubei)
* [Trivy](https://github.com/aquasecurity/trivy)
* [Snyk](https://support.snyk.io/hc/en-us/articles/360003946917-Test-images-with-the-Snyk-Container-CLI)
    
Kubernetes 검증 웹훅을 사용하여 이미지에 심각한 취약점이 없는지 검증할 수도 있습니다.검증 웹훅은 쿠버네티스 API보다 먼저 호출됩니다. 일반적으로 웹훅에 정의된 검증 기준을 준수하지 않는 요청을 거부하는 데 사용됩니다.[이 블로그](https://aws.amazon.com/blogs/containers/building-serverless-admission-webhooks-for-kubernetes-with-aws-sam/)는 ECR DescribeImagesCanVinds API를 호출하여 파드가 심각한 취약성이 있는 이미지를 가져오는지 여부를 확인하는 서버리스 웹훅을 소개합니다. 취약성이 발견되면 파드가 거부되고 CVE 목록이 포함된 메시지가 이벤트로 반환됩니다.

### 증명을 사용하여 아티팩트 무결성 검증
증명이란 특정 사물 (예: 파이프라인 실행, SBOM) 또는 취약성 스캔 보고서와 같은 다른 사물에 대한 “전제 조건” 또는 “주제”, 즉 컨테이너 이미지를 주장하는 암호화 방식으로 서명된 “진술”입니다.

증명을 통해 사용자는 아티팩트가 소프트웨어 공급망의 신뢰할 수 있는 출처에서 나온 것인지 검증할 수 있습니다.예를 들어 이미지에 포함된 모든 소프트웨어 구성 요소나 종속성을 알지 못한 상태에서 컨테이너 이미지를 사용할 수 있습니다.하지만 컨테이너 이미지 제작자가 어떤 소프트웨어가 존재하는지에 대해 말하는 내용을 신뢰할 수 있다면 제작자의 증명을 이용해 해당 아티팩트를 신뢰할 수 있습니다.즉, 직접 분석을 수행하는 대신 워크플로우에서 아티팩트를 안전하게 사용할 수 있습니다.

* 증명은 [AWS 서명자](https://docs.aws.amazon.com/signer/latest/developerguide/Welcome.html) 또는 [Sigstore cosign](https://github.com/sigstore/cosign/blob/main/doc/cosign_attest.md)을 사용하여 생성할 수 있습니다.
* [Kyverno](https://kyverno.io/)와 같은 쿠버네티스 어드미션 컨트롤러를 사용하여 [증명 확인](https://kyverno.io/docs/writing-policies/verify-images/sigstore/)을 할 수 있습니다.
* 컨테이너 이미지에 증명 생성 및 첨부를 포함한 주제와 함께 오픈 소스 도구를 사용하는 AWS의 소프트웨어 공급망 관리 모범 사례에 대해 자세히 알아보려면 이 [워크샵]을(https://catalog.us-east-1.prod.workshops.aws/workshops/49343bb7-2cc5-4001-9d3b-f6a33b3c4442/en-US/0-introduction)을 참조합니다.

### ECR 리포지토리에 대한 IAM 정책 생성
조직에서 공유 AWS 계정 내에서 독립적으로 운영되는 여러 개발 팀이 있는 경우가 드물지 않습니다.이러한 팀이 자산을 공유할 필요가 없는 경우 각 팀이 상호 작용할 수 있는 리포지토리에 대한 액세스를 제한하는 IAM 정책 세트를 만드는 것이 좋습니다.이를 구현하는 좋은 방법은 ECR [네임스페이스](https://docs.aws.amazon.com/AmazonECR/latest/userguide/Repositories.html#repository-concepts)를 사용하는 것입니다. 네임스페이스는 유사한 리포지토리를 그룹화하는 방법입니다. 예를 들어 팀 A의 모든 레지스트리 앞에 team-a/를 붙이고 팀 B의 레지스트리 앞에는 team-b/ 접두사를 사용할 수 있습니다. 액세스를 제한하는 정책은 다음과 같을 수 있습니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowPushPull",
      "Effect": "Allow",
      "Action": [
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": [
        "arn:aws:ecr:<region>:<account_id>:repository/team-a/*"
      ]
    }
  ]
}
```

### ECR 프라이빗 엔드포인트 사용 고려하세요
ECR API에는 퍼블릭 엔드포인트가 있습니다. 따라서 IAM에서 요청을 인증하고 승인하기만 하면 인터넷에서 ECR 레지스트리에 액세스할 수 있습니다. 클러스터 VPC에 IGW (인터넷 게이트웨이)가 없는 샌드박스 환경에서 운영해야 하는 경우 ECR용 프라이빗 엔드포인트를 구성할 수 있습니다. 프라이빗 엔드포인트를 생성하면 인터넷을 통해 트래픽을 라우팅하는 대신 프라이빗 IP 주소를 통해 ECR API에 비공개로 액세스할 수 있습니다. 이 주제에 대한 추가 정보는 [Amazon ECR 인터페이스 VPC 엔드포인트](https://docs.aws.amazon.com/AmazonECR/latest/userguide/vpc-endpoints.html)를 참조합니다.

### ECR 엔드포인트 정책 구현
기본 엔드포인트 정책은 리전 내의 모든 ECR 리포지토리에 대한 액세스를 허용합니다. 이로 인해 공격자/내부자가 데이터를 컨테이너 이미지로 패키징하고 다른 AWS 계정의 레지스트리로 푸시하여 데이터를 유출할 수 있습니다. 이 위험을 완화하려면 ECR 리포지토리에 대한 API 액세스를 제한하는 엔드포인트 정책을 생성해야 합니다. 예를 들어 다음 정책은 계정의 모든 AWS 원칙이 ECR 리포지토리에 대해서만 모든 작업을 수행하도록 허용합니다.

```json
{
  "Statement": [
    {
      "Sid": "LimitECRAccess",
      "Principal": "*",
      "Action": "*",
      "Effect": "Allow",
      "Resource": "arn:aws:ecr:<region>:<account_id>:repository/*"
    }
  ]
}
```

AWS 조직에 속하지 않은 IAM 원칙에 의한 이미지 푸시/풀링을 방지하는 새로운 `PrincipalOrGid` 속성을 사용하는 조건을 설정하여 이를 더욱 개선할 수 있습니다.자세한 내용은 [AWS:PrincipalorgID] (https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-principalorgid) 를 참조하십시오.
`com.amazonaws.<region>.ecr.dkr` 및 `com.amazonaws.<region>.ecr.api` 엔드포인트 모두에 동일한 정책을 적용하는 것을 권장합니다.
EKS는 ECR에서 kube-proxy, coredns 및 aws-node용 이미지를 가져오므로, 레지스트리의 계정 ID (예: `602401143452.dkr. ecr.us-west-2.amazonaws.com /*`) 를 엔드포인트 정책의 리소스 목록에 추가하거나 “*”에서 가져오기를 허용하고 계정 ID에 대한 푸시를 제한하도록 정책을 변경해야 합니다. 아래 표는 EKS 이미지를 제공하는 AWS 계정과 클러스터 지역 간의 매핑을 보여줍니다.

|Account Number	|Region	|
| -------------- | ------ |
|602401143452	|All commercial regions except for those listed below	|
|---	|---	|
|800184023465	|ap-east-1 - Asia Pacific (Hong Kong)	|
|558608220178	|me-south-1 - Middle East (Bahrain)	|
|918309763551	|cn-north-1 - China (Beijing)	|
|961992271922	|cn-northwest-1 - China (Ningxia)	|

엔드포인트 정책 사용에 대한 자세한 내용은 [VPC 엔드포인트 정책을 사용하여 Amazon ECR 액세스 제어](https://aws.amazon.com/blogs/containers/using-vpc-endpoint-policies-to-control-amazon-ecr-access/)를 참조합니다.

### ECR에 대한 수명 주기 정책 구현
[NIST 애플리케이션 컨테이너 보안 가이드](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-190.pdf) 는 “레지스트리의 오래된 이미지”의 위험에 대해 경고하며, 시간이 지나면 취약하고 오래된 소프트웨어 패키지가 포함된 오래된 이미지를 제거하여 우발적인 배포 및 노출을 방지해야 한다고 지적합니다.
각 ECR 저장소에는 이미지 만료 시기에 대한 규칙을 설정하는 수명 주기 정책이 있을 수 있습니다. [AWS 공식 문서](https://docs.aws.amazon.com/AmazonECR/latest/userguide/LifecyclePolicies.html)에는 테스트 규칙을 설정하고 평가한 다음 적용하는 방법이 설명되어 있습니다. 공식 문서에는 리포지토리의 이미지를 필터링하는 다양한 방법을 보여주는 여러 [수명 주기 정책 예제](https://docs.aws.amazon.com/AmazonECR/latest/userguide/lifecycle_policy_examples.html)가 있습니다.

* 이미지  또는 개수로 필터링
* 태그 또는 태그가 지정되지 않은 이미지로 필터링
* 여러 규칙 또는 단일 규칙에서 이미지 태그로 필터링

!!! 경고
    장기 실행 애플리케이션용 이미지를 ECR에서 제거하면 애플리케이션을 재배포하거나 수평으로 확장할 때 이미지 가져오기 오류가 발생할 수 있습니다.이미지 수명 주기 정책을 사용할 때는 배포와 해당 배포에서 참조하는 이미지를 최신 상태로 유지하고 릴리스/배포의 빈도를 설명하는 [이미지] 만료 규칙을 항상 만들 수 있도록 CI/CD 모범 사례를 마련해야 합니다.

### 선별된 이미지 세트 만들기
개발자가 직접 이미지를 만들도록 허용하는 대신 조직의 다양한 애플리케이션 스택에 대해 검증된 이미지 세트를 만드는 것을 고려해 보세요. 이렇게 하면 개발자는 Dockerfile 작성 방법을 배우지 않고 코드 작성에 집중할 수 있습니다. 변경 사항이 Master에 병합되면 CI/CD 파이프라인은 자동으로 에셋을 컴파일하고, 아티팩트 리포지토리에 저장하고, 아티팩트를 적절한 이미지에 복사한 다음 ECR과 같은 Docker 레지스트리로 푸시할 수 있습니다. 최소한 개발자가 자체 Dockerfile을 만들 수 있는 기본 이미지 세트를 만들어야 합니다. 이상적으로는 Dockerhub에서 이미지를 가져오지 않는 것이 좋습니다. a) 이미지에 무엇이 들어 있는지 항상 알 수는 없고 b) 상위 1000개 이미지 중 약 [1/5](https://www.kennasecurity.com/blog/one-fifth-of-the-most-used-docker-containers-have-at-least-one-critical-vulnerability/)에는 취약점이 있기 때문입니다. 이러한 이미지 및 취약성 목록은 https://vulnerablecontainers.org/ 에서 확인할 수 있습니다.

### 루트가 아닌 사용자로 실행하려면 Dockerfile에 USER 지시문을 추가하십시오.
포드 보안 섹션에서 언급했듯이 컨테이너를 루트로 실행하는 것은 피해야 합니다. 이를 PodSpec의 일부로 구성할 수 있지만 Dockerfile에는 `USER` 디렉티브를 사용하는 것이 좋습니다. `USER` 지시어는 USER 지시문 뒤에 나타나는 `RUN`, `ENTRYPOINT` 또는 `CMD` 명령을 실행할 때 사용할 UID를 설정합니다.

### Dockerfile 린트
Linting을 사용하여 Dockerfile이 사전 정의된 지침(예: 'USER' 지침 포함 또는 모든 이미지에 태그를 지정해야 함) 을 준수하는지 확인할 수 있습니다. [dockerfile_lint](https://github.com/projectatomic/dockerfile_lint)는 일반적인 모범 사례를 검증하고 도커파일 린트를 위한 자체 규칙을 구축하는 데 사용할 수 있는 규칙 엔진을 포함하는 RedHat의 오픈소스 프로젝트입니다.규칙을 위반하는 Dockerfile이 포함된 빌드는 자동으로 실패한다는 점에서 CI 파이프라인에 통합할 수 있습니다.

### 스크래치에서 이미지 빌드
이미지를 구축할 때 컨테이너 이미지의 공격 표면을 줄이는 것이 주요 목표가 되어야 합니다. 이를 위한 이상적인 방법은 취약성을 악용하는 데 사용할 수 있는 바이너리가 없는 최소한의 이미지를 만드는 것입니다. 다행히 도커에는 [`scratch`](https://docs.docker.com/develop/develop-images/baseimages/#create-a-simple-parent-image-using-scratch)에서 이미지를 생성하는 메커니즘이 있습니다. Go와 같은 언어를 사용하면 다음 예제와 같이 정적 연결 바이너리를 만들어 Dockerfile에서 참조할 수 있습니다.

```docker
############################
# STEP 1 build executable binary
############################
FROM golang:alpine AS builder# Install git.
# Git is required for fetching the dependencies.
RUN apk update && apk add --no-cache gitWORKDIR $GOPATH/src/mypackage/myapp/COPY . . # Fetch dependencies.
# Using go get.
RUN go get -d -v# Build the binary.
RUN go build -o /go/bin/hello

############################
# STEP 2 build a small image
############################
FROM scratch# Copy our static executable.
COPY --from=builder /go/bin/hello /go/bin/hello# Run the hello binary.
ENTRYPOINT ["/go/bin/hello"]
```

이렇게 하면 애플리케이션으로만 구성된 컨테이너 이미지가 생성되어 매우 안전합니다.

### ECR과 함께 불변 태그 사용
[변경 불가능한 태그](https://aws.amazon.com/about-aws/whats-new/2019/07/amazon-ecr-now-supports-immutable-image-tags/)를 사용하면 이미지 저장소로 푸시할 때마다 이미지 태그를 업데이트해야 합니다. 이렇게 하면 공격자가 이미지의 태그를 변경하지 않고도 악성 버전으로 이미지를 덮어쓰는 것을 막을 수 있습니다. 또한 이미지를 쉽고 고유하게 식별할 수 있는 방법을 제공합니다.

### 이미지, sBOM, 파이프라인 실행 및 취약성 보고서에 서명
도커가 처음 도입되었을 때는 컨테이너 이미지를 검증하기 위한 암호화 모델이 없었습니다. v2에서 도커는 이미지 매니페스트에 다이제스트를 추가했습니다. 이를 통해 이미지 구성을 해시하고 해시를 사용하여 이미지의 ID를 생성할 수 있었습니다. 이미지 서명이 활성화되면 도커 엔진은 매니페스트의 서명을 확인하여 콘텐츠가 신뢰할 수 있는 출처에서 생성되었으며 변조가 발생하지 않았는지 확인합니다. 각 계층이 다운로드된 후 엔진은 계층의 다이제스트를 확인하여 콘텐츠가 매니페스트에 지정된 콘텐츠와 일치하는지 확인합니다. 이미지 서명을 사용하면 이미지와 관련된 디지털 서명을 검증하여 안전한 공급망을 효과적으로 구축할 수 있습니다.

[AWS Signer](https://docs.aws.amazon.com/signer/latest/developerguide/Welcome.html) 또는 [Sigstore Cosign](https://github.com/sigstore/cosign)을 사용하여 컨테이너 이미지에 서명하고, sBOM에 대한 증명, 취약성 스캔 보고서 및 파이프라인 실행 보고서를 생성할 수 있습니다. 이러한 증명은 이미지의 신뢰성과 무결성을 보장하고, 이미지가 실제로 어떠한 간섭이나 변조 없이 신뢰할 수 있는 파이프라인에 의해 생성되었으며, 이미지 게시자가 검증하고 신뢰하는 SBOM에 문서화된 소프트웨어 구성 요소만 포함한다는 것을 보증합니다. 이러한 증명을 컨테이너 이미지에 첨부하여 리포지토리로 푸시할 수 있습니다.

다음 섹션에서는 감사 및 어드미션 컨트롤러 검증을 위해 입증된 아티팩트를 사용하는 방법을 살펴보겠습니다.

### 쿠버네티스 어드미션 컨트롤러를 사용한 이미지 무결성 검증
[동적 어드미션 컨트롤러](https://kubernetes.io/blog/2019/03/21/a-guide-to-kubernetes-admission-controllers/)를 사용하여 대상 쿠버네티스 클러스터에 이미지를 배포하기 전에 자동화된 방식으로 이미지 서명과 입증된 아티팩트를 확인하고 아티팩트의 보안 메타데이터가 어드미션 컨트롤러 정책을 준수하는 경우에만 배포를 승인할 수 있습니다.

예를 들어 이미지의 서명을 암호로 확인하는 정책, 입증된 SBOM, 입증된 파이프라인 실행 보고서 또는 입증된 CVE 스캔 보고서를 작성할 수 있습니다.보고서에 데이터를 확인하기 위한 조건을 정책에 작성할 수 있습니다. 예를 들어, CVE 스캔에는 중요한 CVE가 없어야 합니다. 이러한 조건을 충족하는 이미지에만 배포가 허용되며 다른 모든 배포는 어드미션 컨트롤러에 의해 거부됩니다.

어드미션 컨트롤러의 예는 다음과 같습니다:

* [Kyverno](https://kyverno.io/)
* [OPA Gatekeeper](https://github.com/open-policy-agent/gatekeeper)
* [Portieris](https://github.com/IBM/portieris)
* [Ratify](https://github.com/deislabs/ratify)
* [Kritis](https://github.com/grafeas/kritis)
* [Grafeas tutorial](https://github.com/kelseyhightower/grafeas-tutorial)
* [Voucher](https://github.com/Shopify/voucher)

### 컨테이너 이미지의 패키지 업데이트
이미지의 패키지를 업그레이드하려면 도커파일에 'apt-get update && apt-get upgrade' 실행을 포함해야 합니다. 업그레이드하려면 루트로 실행해야 하지만 이는 이미지 빌드 단계에서 발생합니다. 애플리케이션을 루트로 실행할 필요는 없습니다. 업데이트를 설치한 다음 USER 지시문을 사용하여 다른 사용자로 전환할 수 있습니다. 기본 이미지를 루트 사용자가 아닌 사용자로 실행하는 경우 루트 사용자로 전환했다가 다시 실행하세요.  기본 이미지 관리자에게만 의존하여 최신 보안 업데이트를 설치하지 마십시오.

`apt-get clean`을 실행하여 `/var/cache/apt/archives/`에서 설치 프로그램 파일을 삭제합니다. 패키지를 설치한 후 `rm -rf /var/lib/apt/lists/ *`를 실행할 수도 있습니다. 이렇게 하면 설치할 수 있는 인덱스 파일이나 패키지 목록이 제거됩니다. 이러한 명령은 각 패키지 관리자마다 다를 수 있다는 점에 유의하십시오. 예를 들면 다음과 같습니다.

```docker
RUN apt-get update && apt-get install -y \
    curl \
    git \
    libsqlite3-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
```

## 도구
* [docker-slim](https://github.com/docker-slim/docker-slim)는 안전한 최소 이미지를 구축합니다.
* [dockle](https://github.com/goodwithtech/dockle)는 Dockerfile이 보안 이미지 생성 모범 사례와 일치하는지 확인합니다.
* [dockerfile-lint](https://github.com/projectatomic/dockerfile_lint) Rule based linter for Dockerfiles
* [hadolint](https://github.com/hadolint/hadolint)는 도커파일용 규칙 기반 린터입니다.
* [Gatekeeper and OPA](https://github.com/open-policy-agent/gatekeeper)는 정책 기반 어드미션 컨트롤러입니다.
* [Kyverno](https://kyverno.io/)는 쿠버네티스 네이티브 정책 엔진입니다.
* [in-toto](https://in-toto.io/)를 통해 공급망의 특정 단계가 수행될 예정이었는지, 해당 단계가 올바른 행위자에 의해 수행되었는지 사용자가 확인할 수 있습니다.
* [Notary](https://github.com/theupdateframework/notary)는 컨테이너 이미지 서명 프로젝트입니다.
* [Notary v2](https://github.com/notaryproject/nv2)
* [Grafeas](https://grafeas.io/)는 소프트웨어 공급망을 감사 및 관리하기 위한 개방형 아티팩트 메타데이터 API입니다. 
