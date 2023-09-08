# 이미지 보안
공격에 대한 첫 번째 방어선으로 컨테이너 이미지를 고려해야 합니다. 안전하지 않고 잘못 구성된 이미지로 인해 공격자가 컨테이너 경계를 벗어나 호스트에 액세스할 수 있습니다. 일단 호스트에 있으면 공격자는 민감한 정보에 액세스하거나 클러스터 내에서 또는 AWS 계정을 사용하여 측면으로 이동할 수 있습니다. 다음 모범 사례는 이러한 일이 발생할 위험을 완화하는 데 도움이 됩니다.

## 추천

### 최소한의 이미지 만들기
컨테이너 이미지에서 불필요한 바이너리를 모두 제거하여 시작합니다. Dockerhub의 익숙하지 않은 이미지를 사용하는 경우 각 컨테이너 레이어의 콘텐츠를 표시할 수 있는 [ Dive ]( https://github.com/wagoodman/dive )와 같은 애플리케이션을 사용하여 이미지를 검사하세요. 권한을 에스컬레이션하는 데 사용할 수 있으므로 SETUID 및 SETGID 비트가 있는 모든 바이너리를 제거하고 사악한 목적으로 사용될 수 있는 nc 및 curl과 같은 모든 셸 및 유틸리티를 제거하는 것을 고려하십시오. 다음 명령을 사용하여 SETUID 및 SETGID 비트가 있는 파일을 찾을 수 있습니다.
```강타
찾기 / -perm /6000 -type f -exec ls -ld {} \;
```
    
이러한 파일에서 특수 권한을 제거하려면 컨테이너 이미지에 다음 지시문을 추가합니다.
```도커파일
RUN find / -xdev -perm /6000 -type f -exec chmod as {} \; || 진실
```
구어체로 이것은 이미지의 송곳니를 제거하는 것으로 알려져 있습니다.
  
### 다단계 빌드 사용
다단계 빌드를 사용하는 것은 최소한의 이미지를 만드는 방법입니다. 종종 연속 통합 주기의 일부를 자동화하기 위해 다단계 빌드가 사용됩니다. 예를 들어 다단계 빌드를 사용하여 소스 코드를 린트하거나 정적 코드 분석을 수행할 수 있습니다. 이를 통해 개발자는 파이프라인이 실행될 때까지 기다리지 않고 거의 즉각적인 피드백을 얻을 수 있습니다. 다단계 빌드는 컨테이너 레지스트리에 푸시되는 최종 이미지의 크기를 최소화할 수 있기 때문에 보안 관점에서 매력적입니다. 빌드 도구 및 기타 외부 바이너리가 없는 컨테이너 이미지는 이미지의 공격 표면을 줄여 보안 상태를 개선합니다. 다단계 빌드에 대한 추가 정보는 [ https://docs.docker.com/develop/develop-images/multistage-build/ ]( https://docs.docker.com/develop/develop-images/multistage -빌드/ ).

### 취약점이 있는지 이미지를 정기적으로 스캔
가상 머신과 마찬가지로 컨테이너 이미지는 취약성이 있는 바이너리 및 애플리케이션 라이브러리를 포함하거나 시간이 지남에 따라 취약성을 개발할 수 있습니다. 악용으로부터 보호하는 가장 좋은 방법은 이미지 스캐너로 이미지를 정기적으로 스캔하는 것입니다. Amazon ECR에 저장된 이미지는 푸시 또는 온디맨드(24시간 동안 한 번)로 스캔할 수 있습니다. ECR은 현재 오픈 소스 이미지 스캐닝 솔루션인 [ Clair ]( https://github.com/quay/clair )를 활용하고 있습니다. 이미지를 스캔한 후 결과는 EventBridge의 ECR에 대한 이벤트 스트림에 기록됩니다. ECR 콘솔 내에서 검사 결과를 볼 수도 있습니다. HIGH 또는 CRITICAL 취약성이 있는 이미지는 삭제하거나 다시 빌드해야 합니다. 배포된 이미지에 취약점이 발생하면 가능한 한 빨리 교체해야 합니다.

취약성이 있는 이미지가 배포된 위치를 아는 것은 환경을 안전하게 유지하는 데 필수적입니다. 이미지 추적 솔루션을 직접 구축할 수도 있지만 다음과 같은 기본 제공 기능과 기타 고급 기능을 제공하는 몇 가지 상용 제품이 이미 있습니다.

+ [ 앵커 ]( https://docs.anchore.com/current/ )
+ [ Palo Alto - 프리즈마 클라우드(twistcli) ]( https://docs.paloaltonetworks.com/prisma/prisma-cloud/prisma-cloud-admin-compute/tools/twistcli_scan_images )
+ [ 아쿠아 ]( https://www.aquasec.com/ )
+ [ 쿠베이 ]( https://github.com/Portshift/kubei )
+ [ 트리비 ]( https://github.com/aquasecurity/trivy )
+ [ Snyk ]( https://support.snyk.io/hc/en-us/articles/360003946917-Test-images-with-the-Snyk-Container-CLI )
    
Kubernetes 유효성 검사 웹후크를 사용하여 이미지에 심각한 취약성이 없는지 유효성을 검사할 수도 있습니다. 검증 웹후크는 Kubernetes API 이전에 호출됩니다. 일반적으로 웹후크에 정의된 유효성 검사 기준을 준수하지 않는 요청을 거부하는 데 사용됩니다. [ 이 ]( https://aws.amazon.com/blogs/containers/building-serverless-admission-webhooks-for-kubernetes-with-aws-sam/ )는 ECR describeImageScanFindings API를 호출하는 서버리스 웹후크의 예입니다. 포드가 치명적인 취약점이 있는 이미지를 가져오는지 확인합니다. 취약점이 발견되면 포드가 거부되고 CVE 목록이 포함된 메시지가 이벤트로 반환됩니다.

### ECR 리포지토리에 대한 IAM 정책 생성
오늘날 조직에서 공유 AWS 계정 내에서 독립적으로 운영되는 여러 개발 팀을 보유하는 것은 드문 일이 아닙니다. 이러한 팀이 자산을 공유할 필요가 없는 경우 각 팀이 상호 작용할 수 있는 리포지토리에 대한 액세스를 제한하는 일련의 IAM 정책을 생성할 수 있습니다. 이를 구현하는 좋은 방법은 ECR [ 네임스페이스 ]( https://docs.aws.amazon.com/AmazonECR/latest/userguide/Repositories.html#repository-concepts )를 사용하는 것입니다. 네임스페이스는 유사한 리포지토리를 함께 그룹화하는 방법입니다. 예를 들어 팀 A의 모든 레지스트리는 team-a/로 시작하고 팀 B의 레지스트리는 team-b/ 접두사를 사용할 수 있습니다. 액세스를 제한하는 정책은 다음과 같습니다.
```json
{
  "버전" : "2012-10-17" ,
  "진술서" : [
{
      "시드" : "AllowPushPull" ,
      "효과" : "허용" ,
      "액션" : [
        "ecr:GetDownloadUrlForLayer" ,
        "ecr:BatchGetImage" ,
        "ecr:BatchCheckLayerAvailability" ,
        "ecr:PutImage" ,
        "ecr:InitiateLayerUpload" ,
        "ecr:UploadLayerPart" ,
        "ecr:CompleteLayerUpload"
],
      "자원" : [
        "arn:aws:ecr:<지역>:<account_id>:repository/team-a/*"
]
}
]
}
```
### ECR 프라이빗 엔드포인트 사용 고려
ECR API에는 퍼블릭 엔드포인트가 있습니다. 결과적으로 요청이 IAM에 의해 인증되고 권한이 있는 한 인터넷에서 ECR 레지스트리에 액세스할 수 있습니다. 클러스터 VPC에 인터넷 게이트웨이(IGW)가 없는 샌드박스 환경에서 작동해야 하는 경우 ECR용 프라이빗 엔드포인트를 구성할 수 있습니다. 프라이빗 엔드포인트를 생성하면 인터넷을 통해 트래픽을 라우팅하는 대신 프라이빗 IP 주소를 통해 ECR API에 비공개로 액세스할 수 있습니다. 이 주제에 대한 추가 정보는 https://docs.aws.amazon.com/AmazonECR/latest/userguide/vpc-endpoints.html을 참조하십시오.

### ECR에 대한 엔드포인트 정책 구현
에 대한 기본 엔드포인트 정책은 리전 내의 모든 ECR 리포지토리에 대한 액세스를 허용합니다. 이로 인해 공격자/내부자가 데이터를 컨테이너 이미지로 패키징하고 다른 AWS 계정의 레지스트리로 푸시하여 데이터를 유출할 수 있습니다. 이 위험을 완화하려면 ECR 리포지토리에 대한 API 액세스를 제한하는 엔드포인트 정책을 생성해야 합니다. 예를 들어 다음 정책은 계정의 모든 AWS 원칙이 ECR 리포지토리에 대해서만 모든 작업을 수행하도록 허용합니다.
```json
{
  "진술서" : [
{
      "시드" : "LimitECRAccess" ,
      "교장" : "*" ,
      "액션" : "*" ,
      "효과" : "허용" ,
      "리소스" : "arn:aws:ecr:<지역>:<account_id>:repository/*"
}
]
}
```
AWS 조직의 일부가 아닌 IAM 원칙에 의한 이미지 푸시/풀링을 방지하는 새로운 'PrincipalOrgID' 속성을 사용하는 조건을 설정하여 이를 더욱 향상시킬 수 있습니다. 자세한 내용은 [ aws:PrincipalOrgID ]( https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-principalorgid )를 참조하십시오.

`com.amazonaws.<region>.ecr.dkr` 및 `com.amazonaws.<region>.ecr.api` 엔드포인트 모두에 동일한 정책을 적용하는 것이 좋습니다 .

EKS는 ECR에서 kube-proxy, coredns 및 aws-node에 대한 이미지를 가져오므로 레지스트리의 계정 ID(예: `602401143452.dkr.ecr.us-west-2.amazonaws.com/*` )를 추가해야 합니다. 엔드포인트 정책의 리소스 목록에 추가하거나 "*"에서 가져오기를 허용하고 계정 ID에 대한 푸시를 제한하도록 정책을 변경하십시오. 아래 표에는 EKS 이미지가 판매되는 AWS 계정과 클러스터 리전 간의 매핑이 나와 있습니다.

| 계좌 번호 | 지역 |
| -------------- | ------ |
| 602401143452 | 아래 나열된 지역을 제외한 모든 상업 지역 |
| 800184023465 | 홍콩 |
| 558608220178 | 바 |
| 918309763551 | BJS |
| 961992271922 | ZHY |

엔드포인트 정책 사용에 대한 자세한 내용은 [ VPC 엔드포인트 정책을 사용하여 Amazon ECR 액세스 제어 ]( https://aws.amazon.com/blogs/containers/using-vpc-endpoint-policies-to-control-amazon-ecr -액세스/ ).

### ECR에 대한 수명 주기 정책 구현
[ NIST 애플리케이션 컨테이너 보안 가이드 ]( https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-190.pdf )는 "레지스트리의 오래된 이미지"의 위험에 대해 경고합니다. 취약하고 오래된 소프트웨어 패키지가 포함된 이미지는 우발적인 배포 및 노출을 방지하기 위해 제거해야 합니다.

각 ECR 리포지토리에는 이미지 만료 시기에 대한 규칙을 설정하는 수명 주기 정책이 있을 수 있습니다. [ AWS 공식 문서 ]( https://docs.aws.amazon.com/AmazonECR/latest/userguide/LifecyclePolicies.html )에는 테스트 규칙을 설정하고 평가한 다음 적용하는 방법이 설명되어 있습니다. 리포지토리에서 이미지를 필터링하는 다양한 방법을 보여주는 공식 문서 에는 몇 가지 [ 수명 주기 정책 예제 ]( https://docs.aws.amazon.com/AmazonECR/latest/userguide/lifecycle_policy_examples.html )가 있습니다.

* 이미지 연령 또는 개수로 필터링
* 태그 또는 태그가 지정되지 않은 이미지로 필터링
* 여러 규칙 또는 단일 규칙에서 이미지 태그로 필터링

!!! 경고
장기 실행 애플리케이션의 이미지가 ECR에서 제거되면 애플리케이션이 재배포되거나 수평으로 확장될 때 이미지 가져오기 오류가 발생할 수 있습니다. 이미지 수명 주기 정책을 사용할 때 참조하는 배포 및 이미지를 최신 상태로 유지하고 릴리스/배포 빈도를 설명하는 [ 이미지 ] 만료 규칙을 항상 생성할 수 있는 좋은 CI/CD 사례가 있는지 확인하십시오.

### 선별된 이미지 세트 만들기
개발자가 자신의 이미지를 생성하도록 허용하는 대신 조직의 다양한 애플리케이션 스택에 대해 검증된 이미지 세트를 생성하는 것이 좋습니다. 그렇게 함으로써 개발자는 Dockerfile을 작성하는 방법을 배우지 않고 코드 작성에 집중할 수 있습니다. 변경 사항이 마스터에 병합되면 CI/CD 파이프라인은 자산을 자동으로 컴파일하고 아티팩트 리포지토리에 저장하고 아티팩트를 ECR과 같은 Docker 레지스트리로 푸시하기 전에 적절한 이미지에 복사할 수 있습니다. 최소한 개발자가 자신의 Dockerfile을 만들 수 있는 기본 이미지 집합을 만들어야 합니다. 이상적으로는 a) 이미지에 무엇이 있는지 항상 알 수 없고 b) [ a five ] ( https://www.kennasecurity.com/blog/one-fifth-of -the-most-used-docker-containers-have-at-least-one-critical-vulnerability/ ) 상위 1000개 이미지 중 취약점이 있습니다. 이러한 이미지와 취약점 목록은 https://vulnerablecontainers.org/에서 확인할 수 있습니다.

### 루트가 아닌 사용자로 실행하려면 Dockerfile에 USER 지시문을 추가하십시오.
포드 보안 섹션에서 언급했듯이 컨테이너를 루트로 실행하지 않아야 합니다. 이것을 podSpec의 일부로 구성할 수 있지만 Dockerfile에 `USER` 지시문을 사용하는 것이 좋습니다. `USER` 지시어 는 USER 지시어 뒤에 나타나는 ` RUN` , `ENTRYPOINT` 또는 `CMD` 명령을 실행할 때 사용할 UID를 설정합니다 .

### Dockerfile 린트
Linting을 사용하여 Dockerfile이 사전 정의된 지침 세트를 준수하는지 확인할 수 있습니다(예: 'USER' 지시문 포함 또는 모든 이미지에 태그가 지정되어야 하는 요구 사항). [ dockerfile_lint ]( https://github.com/projectatomic/dockerfile_lint )는 RedHat의 오픈 소스 프로젝트로 일반적인 모범 사례를 확인하고 Dockerfile 린팅을 위한 자체 규칙을 빌드하는 데 사용할 수 있는 규칙 엔진을 포함합니다. 규칙을 위반하는 Dockerfile로 빌드하면 자동으로 실패한다는 점에서 CI 파이프라인에 통합할 수 있습니다.

### 스크래치에서 이미지 빌드
이미지를 빌드할 때 컨테이너 이미지의 공격 표면을 줄이는 것이 주요 목표여야 합니다. 이를 위한 이상적인 방법은 취약점을 악용하는 데 사용할 수 있는 바이너리가 없는 최소한의 이미지를 만드는 것입니다. 다행히 Docker에는 [ `scratch` ]( https://docs.docker.com/develop/develop-images/baseimages/#create-a-simple-parent-image-using-scratch )에서 이미지를 생성하는 메커니즘이 있습니다. Go와 같은 언어를 사용하면 다음 예제와 같이 정적 링크 바이너리를 만들고 Dockerfile에서 참조할 수 있습니다.
```도커파일
############################
# STEP 1 실행 가능한 바이너리 빌드
############################
FROM golang:알파인 AS 빌더
# git을 설치합니다.
# 종속성을 가져오려면 Git이 필요합니다.
RUN apk 업데이트 && apk add --no-cache git
WORKDIR $GOPATH/src/mypackage/myapp/
사본 . .
# 종속성을 가져옵니다.
# go get을 사용합니다.
실행 -d -v를 얻으십시오.
# 바이너리를 빌드합니다.
실행 go build -o /go/bin/hello
############################
# STEP 2 작은 이미지 구축
############################
처음 부터
# 정적 실행 파일을 복사합니다.
복사 --from=빌더 /go/bin/hello /go/bin/hello
# hello 바이너리를 실행합니다.
진입점 [ "/go/bin/hello" ]
```
이렇게 하면 애플리케이션으로만 구성된 컨테이너 이미지가 생성되어 매우 안전합니다.

### ECR과 함께 불변 태그 사용
[ 불변 태그 ]( https://aws.amazon.com/about-aws/whats-new/2019/07/amazon-ecr-now-supports-immutable-image-tags/ ) 이미지 태그를 강제로 업데이트하도록 합니다. 이미지 리포지토리에 푸시할 때마다. 이렇게 하면 공격자가 이미지의 태그를 변경하지 않고 이미지를 악성 버전으로 덮어쓰는 것을 막을 수 있습니다. 또한 이미지를 쉽고 고유하게 식별할 수 있는 방법을 제공합니다.

### 이미지에 서명하세요
Docker가 처음 도입되었을 때 컨테이너 이미지를 확인하기 위한 암호화 모델이 없었습니다. v2에서 Docker는 다이제스트를 이미지 매니페스트에 추가했습니다. 이를 통해 이미지의 구성을 해시하고 해시를 사용하여 이미지의 ID를 생성할 수 있습니다. 이미지 서명이 활성화되면 \[ Docker \] 엔진이 매니페스트의 서명을 확인하여 콘텐츠가 신뢰할 수 있는 소스에서 생성되었고 변조가 발생하지 않았는지 확인합니다. 각 레이어가 다운로드된 후 엔진은 레이어의 다이제스트를 확인하여 콘텐츠가 매니페스트에 지정된 콘텐츠와 일치하는지 확인합니다. 이미지 서명을 사용하면 이미지와 관련된 디지털 서명 확인을 통해 안전한 공급망을 효과적으로 만들 수 있습니다.

Kubernetes 환경에서는 https://github.com/IBM/portieris 및 https://github.com/kelseyhightower/grafeas- 예제와 같이 동적 승인 컨트롤러를 사용하여 이미지가 서명되었는지 확인할 수 있습니다 지도 시간. 이미지에 서명 하면 게시자(소스)를 확인하여 이미지가 변조되지 않았는지 확인합니다(무결성).

!!! 노트
ECR은 향후 이미지 서명을 지원할 예정입니다. [ 문제 ]( https://github.com/aws/containers-roadmap/issues/43 )는 컨테이너 로드맵에서 추적되고 있습니다.

### 컨테이너 이미지의 패키지 업데이트
이미지의 패키지를 업그레이드하려면 Dockerfile에 RUN `apt-get update && apt-get upgrade` 를 포함해야 합니다. 업그레이드하려면 루트로 실행해야 하지만 이는 이미지 빌드 단계에서 발생합니다. 응용 프로그램은 루트로 실행할 필요가 없습니다. 업데이트를 설치한 다음 USER 지시문을 사용하여 다른 사용자로 전환할 수 있습니다. 기본 이미지가 루트가 아닌 사용자로 실행되는 경우 루트로 전환했다가 다시 돌아갑니다. 최신 보안 업데이트를 설치하기 위해 기본 이미지의 관리자에게 전적으로 의존하지 마십시오.

`apt-get clean` 을 실행 하여 `/var/cache/apt/archives/` 에서 설치 프로그램 파일을 삭제합니다 . 패키지를 설치한 후 `rm -rf /var/lib/apt/lists/*` 를 실행할 수도 있습니다 . 이렇게 하면 설치할 수 있는 색인 파일 또는 패키지 목록이 제거됩니다. 이러한 명령은 각 패키지 관리자마다 다를 수 있습니다. 예를 들어:

```도커파일
실행 apt-get 업데이트 && apt-get 설치 -y \
곱슬 곱슬하다 \
자식 \
libsqlite3-dev \
&& 청소하기 && rm -rf /var/lib/apt/lists/*
```

## 도구
+ [ Bane ]( https://github.com/genuinetools/bane ) Docker 컨테이너용 AppArmor 프로파일 생성기
+ [ docker-slim ]( https://github.com/docker-slim/docker-slim ) 안전한 최소 이미지 구축
+ [ dockle ]( https://github.com/goodwithtech/dockle ) Dockerfile이 안전한 이미지 생성을 위한 모범 사례와 일치하는지 확인합니다.
+ [ dockerfile-lint ]( https://github.com/projectatomic/dockerfile_lint ) Dockerfile용 규칙 기반 린터
+ [ hadolint ]( https://github.com/hadolint/hadolint ) 스마트 도커파일 린터
+ [ 게이트키퍼 및 OPA ]( https://github.com/open-policy-agent/gatekeeper ) 정책 기반 승인 컨트롤러
+ [ Kyverno ]( https://kyverno.io/ ) 쿠버네티스 네이티브 정책 엔진
+ [ in-toto ]( https://in-toto.io/ ) 공급망의 특정 단계가 의도적으로 수행되었는지, 해당 단계가 올바른 행위자에 의해 수행되었는지 사용자가 확인할 수 있습니다.
+ [ Notary ]( https://github.com/theupdateframework/notary ) 컨테이너 이미지 서명 프로젝트
+ [ 공증 v2 ]( https://github.com/notaryproject/nv2 )
+ [ Grafeas ]( https://grafeas.io/ ) 소프트웨어 공급망을 감사하고 관리하는 개방형 아티팩트 메타데이터 API


