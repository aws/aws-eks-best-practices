# 인증 및 접근 관리
[AWS IAM(Identity and Access Management)](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html)은 인증 및 권한 부여라는 두 가지 필수 기능을 수행하는 AWS 서비스입니다. 인증에는 자격 증명 확인이 포함되는 반면 권한 부여는 AWS 리소스에서 수행할 수 있는 작업을 관리합니다. AWS 내에서 리소스는 다른 AWS 서비스(예: EC2) 또는 [IAM 사용자](https://docs.aws.amazon.com/IAM/latest/UserGuide/id.html#id_iam-users) 또는 [IAM 역할](https://docs.aws.amazon.com/IAM/latest/UserGuide/id.html#id_iam-roles)과 같은 AWS [보안 주체](https://docs.aws.amazon.com/IAM/latest/UserGuide/intro-structure.html#intro-structure-principal)일 수 있습니다. 리소스가 수행할 수 있는 작업을 관리하는 규칙은 [IAM 정책]( https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html)으로 표현됩니다.

## EKS 클러스터에 대한 접근 제어
쿠버네티스 프로젝트는 Bearer 토큰, X.509 인증서, OIDC 등 kube-apiserver 서비스에 대한 요청을 인증하기 위한 다양한 방식을 지원합니다. EKS는 현재 [웹훅(Webhook) 토큰 인증](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#webhook-token-authentication), [서비스 어카운트 토큰]( https://kubernetes.io/docs/reference/access-authn-authz/authentication/#service-account-tokens) 및 2021년 2월 21일부터 OIDC 인증을 기본적으로 지원합니다.  

웹훅 인증 방식은 베어러 토큰을 확인하는 웹훅을 호출합니다. EKS에서 이런 베어러 토큰은 `kubectl` 명령 실행 시 AWS CLI 또는 [aws-iam-authenticator](https://github.com/kubernetes-sigs/aws-iam-authenticator) 클라이언트에 의해 생성됩니다. 명령을 실행하면 토큰은 kube-apiserver로 전달되고 다시 웹훅으로 포워딩됩니다. 요청이 올바른 형식이면 웹훅은 토큰 본문에 포함된 미리 서명된 URL을 호출합니다. 이 URL은 요청 서명의 유효성을 검사하고 사용자 정보(사용자 어카운트, ARN 및 사용자 ID 등)를 kube-apiserver에 반환합니다.

인증 토큰을 수동으로 생성하려면 터미널 창에 다음 명령을 입력합니다.

```bash
aws eks get-token --cluster-name <클러스터_이름>
```

프로그래밍 방식으로 토큰을 얻을 수도 있습니다. 다음은 Go 언어로 작성된 예입니다.

```golang
package main

import (
	"fmt"
	"log"
	"sigs.k8s.io/aws-iam-authenticator/pkg/token"
)

func main()  {
	g, _ := token.NewGenerator(false, false)
	tk, err := g.Get("<cluster_name>")
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println(tk)
}
```

출력 응답은 다음과 형태를 가집니다.
```json
{
  "kind": "ExecCredential", 
  "apiVersion": "client.authentication.k8s.io/v1alpha1", 
  "spec": {}, 
  "status": {
    "expirationTimestamp": "2020-02-19T16:08:27Z", 
    "token": "k8s-aws-v1.aHR0cHM6Ly9zdHMuYW1hem9uYXdzLmNvbS8_QWN0aW9uPUdldENhbGxlcklkZW50aXR5JlZlcnNpb249MjAxMS0wNi0xNSZYLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFKTkdSSUxLTlNSQzJXNVFBJTJGMjAyMDAyMTklMkZ1cy1lYXN0LTElMkZzdHMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDIwMDIxOVQxNTU0MjdaJlgtQW16LUV4cGlyZXM9NjAmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0JTNCeC1rOHMtYXdzLWlkJlgtQW16LVNpZ25hdHVyZT0yMjBmOGYzNTg1ZTMyMGRkYjVlNjgzYTVjOWE0MDUzMDFhZDc2NTQ2ZjI0ZjI4MTExZmRhZDA5Y2Y2NDhhMzkz"
  }
}
```
각 토큰은 `k8s-aws-v1.`으로 시작하고 base64로 인코딩된 문자열이 뒤따릅니다. 문자열은 디코딩하면 다음과 같은 형태를 가집니다.
```bash
https://sts.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAJPFRILKNSRC2W5QA%2F20200219%2Fus-east-1%2Fsts%2Faws4_request&X-Amz-Date=20200219T155427Z&X-Amz-Expires=60&X-Amz-SignedHeaders=host%3Bx-k8s-aws-id&X-Amz-Signature=220f8f3285e320ddb5e683a5c9a405301ad76546f24f28111fdad09cf648a393
```
토큰은 Amazon 자격 증명 크리덴셜 및 서명이 포함된 미리 서명된 URL로 구성됩니다. 자세한 내용은 [GetCallerIdentity API 문서](https://docs.aws.amazon.com/STS/latest/APIReference/API_GetCallerIdentity.html)를 참조합니다.

토큰은 15분의 TTL 수명이 있고, 수명 종류 후에는 새 토큰을 생성해야 합니다. 이는 `kubectl`과 같은 클라이언트를 사용할 때 자동으로 처리 되지만 쿠버네티스 대시보드를 사용하는 경우 토큰이 만료될 때마다 새 토큰을 생성하고 다시 인증해야 합니다.

사용자 ID가 AWS IAM 서비스에 의해 인증되면 kube-apiserver 는 'kube-system' 네임스페이스에서 'aws-auth' ConfigMap을 읽어 사용자와 연결할 RBAC 그룹을 결정합니다. `aws-auth` 컨피그맵 은 IAM 보안 주체(예: IAM 사용자 및 역할)와 쿠버네티스 RBAC 그룹 간의 정적 매핑을 생성하는 데 사용됩니다. RBAC 그룹은 쿠버네티스 롤바인딩 또는 클러스터롤바인딩에서 참조할 수 있습니다. 쿠버네티스 리소스(객체) 모음에 대해 수행할 수 있는 일련의 작업(동사)을 정의한다는 점에서 IAM 역할과 유사합니다.

## 권장 사항

### 인증에 서비스 어카운트 토큰을 사용하지 마세요.
서비스 어카운트 토큰은 수명이 긴 정적 사용자 인증 정보입니다. 손상, 분실 또는 도난된 경우 공격자는 서비스 어카운트이 삭제될 때까지 해당 토큰과 관련된 모든 작업을 수행할 수 있습니다. 경우에 따라 클러스터 외부에서 쿠버네티스 API를 사용해야 하는 애플리케이션(예: CI/CD 파이프라인 애플리케이션)에 대한 예외를 부여해야 할 수 있습니다. 이런 애플리케이션이 EC2 인스턴스와 같은 AWS 인프라에서 실행되는 경우 대신 인스턴스 프로파일을 사용하고 이를 'aws-auth' 컨피그맵의 쿠버네티스 RBAC 역할에 매핑하는 것이 좋습니다.

### AWS 리소스에 대한 최소 권한 액세스 사용
쿠버네티스 API에 액세스하기 위해 IAM 사용자에게 AWS 리소스에 대한 권한을 할당할 필요가 없습니다. IAM 사용자에게 EKS 클러스터에 대한 액세스 권한을 부여해야 하는 경우 특정 쿠버네티스 RBAC 그룹에 매핑되는 해당 사용자 의 'aws-auth' 컨피그맵에 항목을 생성합니다.

### 여러 사용자가 클러스터에 대해 동일한 액세스 권한이 필요한 경우 IAM 역할 사용
'aws-auth' 컨피그맵 에서 각 개별 IAM 사용자에 대한 항목을 생성하는 대신 해당 사용자가 IAM 역할을 수임하고 해당 역할을 쿠버네티스 RBAC 그룹에 매핑하도록 허용합니다. 특히 액세스가 필요한 사용자 수가 증가함에 따라 유지 관리가 더 쉬워집니다.

!!! attention
    aws-auth 컨피그맵에 의해 매핑된 IAM 보안 주체로 EKS 클러스터에 액세스할 때 aws-auth 컨피그맵에 설명된 사용자 이름이 쿠버네티스 감사 로그의 사용자 필드에 기록됩니다. IAM 역할을 사용하는 경우 해당 역할을 맡는 실제 사용자는 기록되지 않으며 감사할 수 없습니다.

aws-auth 컨피그맵에서 mapRoles를 사용하여 K8s RBAC 권한을 IAM 역할에 할당할 때 사용자 이름에 {{SessionName}}을 포함해야 합니다. 이렇게 하면 감사 로그에 세션 이름이 기록되므로 CloudTrail 로그와 함께 이 역할을 맡은 실제 사용자를 추적할 수 있습니다.

```yaml
- rolearn: arn:aws:iam::XXXXXXXXXXXX:role/testRole
  username: testRole:{{SessionName}}
  groups:
    - system:masters
```

쿠버네티스 1.20 또는 이후 버전에서는 ```User.Extra.sessionName.0```이 쿠버네티스 감사 로그에 추가되었으므로 이런 변경이 더 이상 필요하지 않습니다.

### RoleBinding 및 ClusterRoleBinding 생성 시 최소 권한 접근 허용
AWS 리소스에 대한 액세스 권한 부여에 대한 이전 항목과 마찬가지로 롤바인딩 및 클러스터롤바인딩에는 특정 기능을 수행하는 데 필요한 권한 집합만 포함되어야 합니다. 절대적으로 필요한 경우가 아니면 Role 및 ClusterRole에서 `["*"]` 를 사용하지 마십시오. 할당할 권한이 확실하지 않은 경우 [audit2rbac](https://github.com/liggitt/audit2rbac)과 같은 도구를 사용하여 쿠버네티스 감사 로그에서 관찰된 API 호출을 기반으로 역할 및 바인딩을 자동으로 생성하는 것이 좋습니다.

### EKS 클러스터 엔드포인트를 비공개로 설정
기본적으로 EKS 클러스터를 프로비저닝할 때 API 클러스터 엔드포인트는 퍼블릭으로 설정됩니다. 즉, 인터넷에서 액세스할 수 있습니다. 인터넷에서 액세스할 수 있음에도 불구하고 모든 API 요청이 IAM에 의해 인증되고 쿠버네티스 RBAC에 의해 승인되어야 하기 때문에 엔드포인트는 여전히 안전한 것으로 간주됩니다. 즉, 회사 보안 정책에 따라 인터넷에서 API에 대한 액세스를 제한하거나 클러스터 VPC 외부로 트래픽을 라우팅하지 못하도록 하는 경우 다음을 수행할 수 있습니다.

+ EKS 클러스터 엔드포인트를 프라이빗으로 구성합니다. 이 주제에 대한 자세한 내용은 [클러스터 엔드포인트 액세스 수정](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html)을 참조하십시오.
+ 클러스터 엔드포인트를 퍼블릭으로 두고 클러스터 엔드포인트와 통신할 수 있는 CIDR 블록을 지정합니다. 해당 블록은 클러스터 엔드포인트에 액세스할 수 있도록 허용된 퍼블릭 IP 주소 집합입니다.
+ 퍼블릭 엔드포인트는 접근이 허용된 화이트리스트 기반의 일부 CIDR 블록에만 허용하고 프라이빗 엔드포인트를 활성화합니다. 이렇게 하면 컨트롤 플레인이 프로비저닝될 때 클러스터 VPC에 프로비저닝되는 크로스 어카운트 ENI를 통해 kubelet과 쿠버네티스 API 사이의 모든 네트워크 트래픽을 강제하는 동시에 특정 퍼블릭 IP 범위의 퍼블릭 액세스가 허용됩니다.

### 전용 IAM 역할로 클러스터 생성
Amazon EKS 클러스터를 생성하면 클러스터를 생성하는 연동 사용자와 같은 IAM 엔터티 사용자 또는 역할에 클러스터의 RBAC 구성에서 'system:masters' 권한이 자동으로 부여됩니다. 이 액세스는 제거할 수 없으며 `aws-auth` 컨피그맵을 통해 관리되지 않습니다. 따라서 전용 IAM 역할로 클러스터를 생성하고 이 역할을 맡을 수 있는 사람을 정기적으로 감사하는 것이 좋습니다. 이 역할은 클러스터에서 일상적인 작업을 수행하는 데 사용되어서는 안 되며, 대신 이런 목적을 위해 'aws-auth' 컨피그맵을 통해 추가 사용자에게 클러스터에 대한 액세스 권한을 부여해야 합니다. 'aws-auth' 컨피그맵이 구성된 이후에는 역할을 삭제할 수 있으며 'aws-auth' 컨피그맵이 손상되고 그렇지 않으면 클러스터에 액세스할 수 없는 긴급/유리 파손 시나리오에서만 다시 생성 할 수 있습니다. 이는 일반적으로 직접 사용자 액세스가 구성되지 않은 운영 클러스터에서 특히 유용할 수 있습니다.

### 도구를 사용하여 aws-auth 컨피그맵 변경
잘못된 형식의 aws-auth 컨피그맵으로 인해 클러스터에 대한 접근 권한을 잃을 수 있습니다. 컨피그맵을 변경해야 하는 경우 도구를 사용하십시오.

**eksctl**

`eksctl` CLI에는 aws-auth 컨피그맵에 ID 매핑을 추가하기 위한 명령이 포함되어 있습니다.


CLI 도움말 보기:

```bash
eksctl create iamidentitymapping --help
```

IAM 역할을 클러스터 관리자로 지정:
```bash
 eksctl create iamidentitymapping --cluster  <clusterName> --region=<region> --arn arn:aws:iam::123456:role/testing --group system:masters --username admin
```

자세한 내용은 [`eksctl` 문서]( https://eksctl.io/usage/iam-identity-mappings/)를 참조하십시오.

**keikoproj의 [aws-auth](https://github.com/keikoproj/aws-auth)**

keikoproj의 'aws-auth' 에는 cli 및 go 라이브러리가 모두 포함되어 있습니다.

CLI 도움말 다운로드 및 보기:
```
go get github.com/keikoproj/aws-auth
aws-auth help
```

또는 kubectl용 [krew 플러그인 관리자]( https://krew.sigs.k8s.io )로 `aws-auth` 를 설치 합니다.

```
kubectl krew install aws-auth
kubectl aws-auth
```

go 라이브러리를 비롯한 자세한 내용은 [GitHub 내 aws-auth 문서를 확인](https://github.com/keikoproj/aws-auth/blob/master/README.md)하십시오.

**[AWS IAM Authenticator CLI](https://github.com/kubernetes-sigs/aws-iam-authenticator/tree/master/cmd/aws-iam-authenticator)**

`aws-iam-authenticator` 프로젝트에는 컨피그맵을 업데이트하기 위한 CLI가 포함되어 있습니다.

GitHub에서 [릴리스 다운로드]( https://github.com/kubernetes-sigs/aws-iam-authenticator/releases).

IAM 역할에 클러스터 권한을 추가합니다.

```
./aws-iam-authenticator add role --rolearn arn:aws:iam::185309785115:role/lil-dev-role-cluster --username lil-dev-user --groups system:masters --kubeconfig ~/.kube/config
```

### 클러스터에 대한 접근을 정기적으로 감사합니다.
클러스터에 접근이 필요한 사람은 시간이 지남에 따라 변경될 수 있습니다. 주기적으로 `aws-auth` 컨피그맵을 감사하여 접근 권한이 부여된 사람과 할당된 권한을 확인하십시오. 특정 서비스 어카운트, 사용자 또는 그룹에 바인딩된 역할을 검사하기 위해 [kubectl-who-can](https://github.com/aquasecurity/kubectl-who-can) 또는 [rbac-lookup](https://github.com/FairwindsOps/)과 같은 오픈 소스 도구를 사용할 수도 있습니다. 해당 주제에 대해서는 [감사](detective.md)섹션에서 더 자세히 살펴 보겠습니다. 추가 아이디어는 NCC Group의 이 [기사](https://www.nccgroup.trust/us/about-us/newsroom-and-events/blog/2019/august/tools-and-methods-for-auditing-kubernetes-rbac-policies/?mkt_tok=eyJpIjoiWWpGa056SXlNV1E0WWpRNSIsInQiOiJBT1hyUTRHYkg1TGxBV0hTZnRibDAyRUZ0VzBxbndnRzNGbTAxZzI0WmFHckJJbWlKdE5WWDdUQlBrYVZpMnNuTFJ1R3hacVYrRCsxYWQ2RTRcL2pMN1BtRVA1ZFZcL0NtaEtIUDdZV3pENzNLcE1zWGVwUndEXC9Pb2tmSERcL1pUaGUifQ%3D%3D)에서 찾을 수 있습니다. 

### 인증 및 액세스 관리에 대한 대체 접근 방식
IAM은 EKS 클러스터에 액세스해야 하는 사용자를 인증하는 데 선호되는 방법이지만, 인증 프록시 또는 쿠버네티스 [impersonation](https://kubernetes.io/docs/reference/access-authn-authz/authentication/#user-impersonation)등을 사용하는 GitHub와 같은 OIDC ID 공급자를 사용할 수 있습니다. 이런 두 가지 솔루션에 대한 게시물이 AWS 오픈 소스 블로그에 게시되었습니다.

+ [Teleport와 함께 GitHub 자격 증명을 사용하여 EKS에 인증](https://aws.amazon.com/blogs/opensource/authenticating-eks-github-credentials-teleport/)
+ [kube-oidc-proxy를 사용하여 여러 EKS 클러스터에서 일관된 OIDC 인증](https://aws.amazon.com/blogs/opensource/consistent-oidc-authentication-across-multiple-eks-clusters-using-kube-oidc-proxy/)

!!! attention
    EKS는 기본적으로 프록시를 사용하지 않고 OIDC 인증을 지원합니다. 자세한 내용은 [Amazon EKS에 대한 OIDC 자격 증명 공급자 인증 소개](https://aws.amazon.com/blogs/containers/introducing-oidc-identity-provider-authentication-amazon-eks/)블로그를 참조하십시오. 다양한 인증 방법에 대한 커넥터를 제공하는 인기 있는 오픈 소스 OIDC 공급자인 Dex로 EKS를 구성하는 방법을 보여주는 예는 [Dex 및 dex-k8s-authenticator를 사용하여 Amazon EKS 인증](https://aws. amazon.com/blogs/containers/using-dex-dex-k8s-authenticator-to-authenticate-to-amazon-eks/ ) 블로그를 참조하세요. 블로그에 설명된 대로 OIDC 공급자가 인증한 사용자 이름/사용자 그룹은 쿠버네티스 감사 로그에 나타납니다.

또한 [AWS SSO](https://docs.aws.amazon.com/singlesignon/latest/userguide/what-is.html)를 사용하여 Azure AD와 같은 외부 자격 증명 공급자와 AWS를 페더레이션할 수 있습니다. 이를 사용하기로 결정한 경우 AWS CLI v2.0에는 SSO 세션을 현재 CLI 세션과 쉽게 연결하고 IAM 역할을 수임할 수 있는 명명된 프로파일을 생성하는 옵션이 포함되어 있습니다. 사용자의 쿠버네티스 RBAC 그룹을 결정하는 데 IAM 역할이 사용되므로 `kubectl` 을 실행하기 "전" 역할을 수임(Assume)하여야 합니다.

### 추가 리소스
[rbac.dev](https://github.com/mhausenblas/rbac.dev) 쿠버네티스 RBAC에 대한 블로그 및 도구를 포함한 추가 리소스 목록

## 파드 아이덴티티
쿠버네티스 클러스터 내에서 실행되는 특정 애플리케이션은 제대로 작동하기 위해 쿠버네티스 API를 호출할 수 있는 권한이 필요합니다. 예를 들어 [AWS 로드밸런서 컨트롤러](https://github.com/kubernetes-sigs/aws-load-balancer-controller)는 서비스의 엔드포인트를 나열할 수 있어야 합니다. 또한 컨트롤러는 ALB를 프로비저닝하고 구성하기 위해 AWS API를 호출할 수 있어야 합니다. 이 섹션에서는 파드에 권한을 할당하는 모범 사례를 살펴봅니다.

### 쿠버네티스 서비스 어카운트
서비스 어카운트는 파드에 쿠버네티스 RBAC 역할을 할당할 수 있는 특수한 유형의 개체입니다. 클러스터 내의 각 네임스페이스에 대해 기본 서비스 어카운트이 자동으로 생성됩니다. 특정 서비스 어카운트을 참조하지 않고 네임스페이스에 파드를 배포하면, 해당 네임스페이스의 기본 서비스 어카운트이 자동으로 파드에 할당되고 시크릿, 즉 해당 서비스 아카운트의 서비스 어카운트 (JWT) 토큰은 `/var/run/secrets/kubernetes.io/serviceaccount`에서 볼륨으로 파드에 마운트됩니다. 해당 디렉터리의 서비스 어카운트 토큰을 디코딩하면 다음과 같은 메타데이터가 나타납니다. 
```json
{
  "iss": "kubernetes/serviceaccount",
  "kubernetes.io/serviceaccount/namespace": "default",
  "kubernetes.io/serviceaccount/secret.name": "default-token-5pv4z",
  "kubernetes.io/serviceaccount/service-account.name": "default",
  "kubernetes.io/serviceaccount/service-account.uid": "3b36ddb5-438c-11ea-9438-063a49b60fba",
  "sub": "system:serviceaccount:default:default"
}
``` 

기본 서비스 어카운트에는 쿠버네티스 API에 대한 다음 권한이 있습니다.
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  annotations:
    rbac.authorization.kubernetes.io/autoupdate: "true"
  creationTimestamp: "2020-01-30T18:13:25Z"
  labels:
    kubernetes.io/bootstrapping: rbac-defaults
  name: system:discovery
  resourceVersion: "43"
  selfLink: /apis/rbac.authorization.k8s.io/v1/clusterroles/system%3Adiscovery
  uid: 350d2ab8-438c-11ea-9438-063a49b60fba
rules:
- nonResourceURLs:
  - /api
  - /api/*
  - /apis
  - /apis/*
  - /healthz
  - /openapi
  - /openapi/*
  - /version
  - /version/
  verbs:
  - get
```
이 역할은 인증되지 않은 사용자와 인증된 사용자가 API 정보를 읽을 수 있는 권한을 부여하며 공개적으로 액세스해도 안전한 것으로 간주됩니다.

파드 내에서 실행 중인 애플리케이션이 쿠버네티스 API를 호출할 때 해당 API를 호출할 수 있는 권한을 명시적으로 부여하는 서비스 어카운트를 파드에 할당해야 합니다. 사용자 접근에 대한 지침과 유사하게 서비스 어카운트에 바인딩된 Role 또는 ClusterRole은 애플리케이션이 작동하는 데 필요한 API 리소스 및 메서드로 제한되어야 합니다. 기본이 아닌 서비스 어카운트를 사용하려면 파드의 `spec.serviceAccountName` 필드를 사용하려는 서비스 어카운트의 이름으로 설정하기만 하면 됩니다. 서비스 어카운트 생성에 대한 추가 정보는 [해당 문서](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#service-account-permissions)를 참조하십시오.

!!! note
    쿠버네티스 1.24 이전에는 쿠버네티스가 각 서비스 어카운트에 대한 암호를 자동으로 생성했습니다. 이 시크릿은 파드 내 /var/run/secrets/kubernetes.io/serviceaccount 경로로 마운트되었으며 파드에서 쿠버네티스 API 서버를 인증하는 데 사용됩니다. 쿠버네티스 1.24에서는 파드가 실행될 때 서비스 어카운트 토큰이 동적으로 생성되며 기본적으로 1시간 동안만 유효합니다. 서비스 어카운트의 시크릿은 생성되지 않습니다. Jenkins와 같이 쿠버네티스 API에 인증해야 하는 클러스터 외부에서 실행되는 애플리케이션이 있는 경우, `metadata.annotations.kubernetes.io/service-account.name: <SERVICE_ACCOUNT_NAME>`와 같은 서비스 어카운트를 참조하는 어노테이션과 함께 `kubernetes.io/service-account-token` 유형의 시크릿을 생성해야 한다. 이 방법으로 생성된 시크릿은 만료되지 않습니다.

### 서비스 어카운트용 IAM 역할(IRSA)
IRSA는 쿠버네티스 서비스 어카운트에 IAM 역할을 할당할 수 있는 기능입니다. [Service Account Token Volume Projection](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/#service-account-token-volume-projection)이라는  쿠버네티스 기능을 활용하여 작동합니다. 파드가 IAM 역할을 참조하는 서비스 어카운트으로 구성된 경우 쿠버네티스 API 서버는 시작 시 클러스터에 대한 공개 OIDC 검색 엔드포인트를 호출합니다. 엔드포인트는 Kubernetes에서 발행한 OIDC 토큰에 암호로 서명하고, 생성된 토큰은 볼륨으로 마운트됩니다. 이 서명된 토큰을 통해 파드는 IAM 역할과 연결된 AWS API를 호출할 수 있습니다. AWS API가 호출되면 AWS SDK는 `sts:AssumeRoleWithWebIdentity`를 호출합니다. 토큰의 서명을 확인한 후 IAM은 쿠버네티스에서 발행한 토큰을 임시 AWS 역할 자격 증명으로 교환합니다.

IRSA에 대한 (JWT)토큰을 디코딩하면 아래에 표시된 예와 유사한 출력이 생성됩니다.
```json
{
  "aud": [
    "sts.amazonaws.com"
  ],
  "exp": 1582306514,
  "iat": 1582220114,
  "iss": "https://oidc.eks.us-west-2.amazonaws.com/id/D43CF17C27A865933144EA99A26FB128",
  "kubernetes.io": {
    "namespace": "default",
    "pod": {
      "name": "alpine-57b5664646-rf966",
      "uid": "5a20f883-5407-11ea-a85c-0e62b7a4a436"
    },
    "serviceaccount": {
      "name": "s3-read-only",
      "uid": "a720ba5c-5406-11ea-9438-063a49b60fba"
    }
  },
  "nbf": 1582220114,
  "sub": "system:serviceaccount:default:s3-read-only"
}
```
이 특정 토큰은 파드에 S3 보기 전용 권한을 부여합니다. 애플리케이션이 S3에서 읽기를 시도하면 토큰이 다음과 유사한 임시 IAM 자격 증명 세트로 교환됩니다.
```json
{
    "AssumedRoleUser": {
        "AssumedRoleId": "AROA36C6WWEJULFUYMPB6:abc", 
        "Arn": "arn:aws:sts::123456789012:assumed-role/eksctl-winterfell-addon-iamserviceaccount-de-Role1-1D61LT75JH3MB/abc"
    }, 
    "Audience": "sts.amazonaws.com", 
    "Provider": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-west-2.amazonaws.com/id/D43CF17C27A865933144EA99A26FB128", 
    "SubjectFromWebIdentityToken": "system:serviceaccount:default:s3-read-only", 
    "Credentials": {
        "SecretAccessKey": "ORJ+8Adk+wW+nU8FETq7+mOqeA8Z6jlPihnV8hX1", 
        "SessionToken": "FwoGZXIvYXdzEGMaDMLxAZkuLpmSwYXShiL9A1S0X87VBC1mHCrRe/pB2oes+l1eXxUYnPJyC9ayOoXMvqXQsomq0xs6OqZ3vaa5Iw1HIyA4Cv1suLaOCoU3hNvOIJ6C94H1vU0siQYk7DIq9Av5RZe+uE2FnOctNBvYLd3i0IZo1ajjc00yRK3v24VRq9nQpoPLuqyH2jzlhCEjXuPScPbi5KEVs9fNcOTtgzbVf7IG2gNiwNs5aCpN4Bv/Zv2A6zp5xGz9cWj2f0aD9v66vX4bexOs5t/YYhwuwAvkkJPSIGvxja0xRThnceHyFHKtj0H+bi/PWAtlI8YJcDX69cM30JAHDdQH+ltm/4scFptW1hlvMaP+WReCAaCrsHrAT+yka7ttw5YlUyvZ8EPog+j6fwHlxmrXM9h1BqdikomyJU00gm1++FJelfP+1zAwcyrxCnbRl3ARFrAt8hIlrT6Vyu8WvWtLxcI8KcLcJQb/LgkW+sCTGlYcY8z3zkigJMbYn07ewTL5Ss7LazTJJa758I7PZan/v3xQHd5DEc5WBneiV3iOznDFgup0VAMkIviVjVCkszaPSVEdK2NU7jtrh6Jfm7bU/3P6ZG+CkyDLIa8MBn9KPXeJd/y+jTk5Ii+fIwO/+mDpGNUribg6TPxhzZ8b/XdZO1kS1gVgqjXyVC+M+BRBh6C4H21w/eMzjCtDIpoxt5rGKL6Nu/IFMipoC4fgx6LIIHwtGYMG7SWQi7OsMAkiwZRg0n68/RqWgLzBt/4pfjSRYuk=", 
        "Expiration": "2020-02-20T18:49:50Z", 
        "AccessKeyId": "ASIA36C6WWEJUMHA3L7Z"
    }
}
```  

EKS 컨트롤 플레인의 일부로 실행되는 Mutating 웹훅은 AWS 역할 ARN과 웹 자격 증명 토큰 파일의 경로를 환경 변수로 파드에 주입합니다. 이런 값은 수동으로 제공할 수도 있습니다.
```
AWS_ROLE_ARN=arn:aws:iam::AWS_ACCOUNT_ID:role/IAM_ROLE_NAME
AWS_WEB_IDENTITY_TOKEN_FILE=/var/run/secrets/eks.amazonaws.com/serviceaccount/token
```

kubelet은 총 TTL의 80%보다 오래되거나 24시간이 지나면 프로젝션된 토큰을 자동으로 교체합니다. AWS SDK는 토큰이 회전할 때 토큰을 다시 로드하는 역할을 합니다. IRSA에 대한 자세한 내용은 [AWS 문서](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts-technical-overview.html)를 참조합니다.

## 권장 사항

### IRSA를 사용하도록 aws-node 데몬셋 업데이트
현재 aws-node 데몬셋은 EC2 인스턴스에 할당된 역할을 사용하여 파드에 IP를 할당하도록 구성되어 있습니다. 이 역할에는 AmazonEKS_CNI_Policy 및 EC2ContainerRegistryReadOnly와 같이 노드에서 실행 중인 **모든** 파드가 ENI를 연결/분리하거나, IP 주소를 할당/할당 해제하거나, ECR에서 이미지를 가져오도록 효과적으로 허용하는 몇 가지 AWS 관리형 정책이 포함됩니다. 이는 클러스터에 위험을 초래하므로 IRSA를 사용하도록 aws-node 데몬셋을 업데이트하는 것이 좋습니다. 이 작업을 수행하기 위한 스크립트는 이 가이드의 [리파지토리](https://github.com/aws/aws-eks-best-practices/tree/master/projects/enable-irsa/src)에서 찾을 수 있습니다.

### 워커 노드에 할당된 인스턴스 프로파일에 대한 접근 제한
IRSA를 사용하면 IRSA 토큰을 사용하도록 파드의 자격 증명 체인을 업데이트하지만 파드는 _워커 노드에 할당된 인스턴스 프로파일의 권한을 계속 상속할 수 있습니다_. IRSA 사용 시 허용되지 않은 권한의 범위를 최소화하기 위해 [인스턴스 메타데이터](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html) 액세스를 차단하는 것이 **강력하게** 권장됩니다. 

!!! caution
    인스턴스 메타데이터에 대한 액세스를 차단하면 IRSA를 사용하지 않는 파드가 워커 노드에 할당된 역할을 상속받지 못합니다.

아래 예와 같이 인스턴스가 IMDSv2만 사용하도록 하고 홉 제한을 1로 업데이트하여 인스턴스 메타데이터에 대한 액세스를 차단할 수 있습니다. 노드 그룹의 시작 템플릿에 이런 설정을 포함할 수도 있습니다. 인스턴스 메타데이터를 **비활성화 하지마세요**. 이렇게 하면 노드 종료 핸들러와 같은 구성 요소와 인스턴스 메타데이터에 의존하는 기타 요소가 제대로 작동하지 않습니다.

```
aws ec2 modify-instance-metadata-options --instance-id <value> --http-tokens required --http-put-response-hop-limit 1
```

Terraform을 사용하여 관리형 노드 그룹과 함께 사용할 시작 템플릿을 만드는 경우 메타데이터 블록을 추가하여 다음 코드 스니펫에 표시된 대로 홉 수를 구성하십시오. 

``` tf hl_lines="7"
resource "aws_launch_template" "foo" {
  name = "foo"
  ...
    metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "enabled"
  }
  ...
```

노드에서 iptables를 조작하여 EC2 메타데이터에 대한 파드의 액세스를 차단할 수도 있습니다. 이 방법에 대한 자세한 내용은 [인스턴스 메타데이터 서비스에 대한 액세스 제한](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-data-retrieval.html#instance-metadata-limiting-access) 문서를 참조하세요.

IRSA를 지원하지 않는 이전 버전의 AWS SDK를 사용하는 애플리케이션이 있는 경우 SDK 버전을 업데이트해야 합니다.

### IRSA에 대한 IAM 역할 신뢰 정책의 범위를 서비스 어카운트 이름으로 지정합니다.
신뢰 정책은 네임스페이스 또는 네임스페이스 내의 특정 서비스 어카운트로 범위를 지정할 수 있습니다. IRSA를 사용하는 경우 서비스 어카운트 이름을 포함하여 역할 신뢰 정책을 가능한 한 명시적으로 만드는 것이 가장 좋습니다. 이렇게 하면 동일한 네임스페이스 내의 다른 파드가 역할을 맡는 것을 효과적으로 방지할 수 있습니다. CLI `eksctl` 은 서비스 어카운트/IAM 역할을 생성하는 데 사용할 때 이 작업을 자동으로 수행합니다. 자세한 내용은 [eksctl 문서](https://eksctl.io/usage/iamserviceaccounts/)를 참조하세요.

### 애플리케이션이 IMDS에 액세스해야 하는 경우 IMDSv2를 사용하고 EC2 인스턴스의 홉 제한을 2로 늘리세요.
[IMDSv2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html)에서는 PUT 요청을 사용하여 세션 토큰을 가져와야 합니다. 초기 PUT 요청에는 세션 토큰에 대한 TTL이 포함되어야 합니다. 최신 버전의 AWS SDK는 이를 처리하고 해당 토큰의 갱신을 자동으로 처리합니다. 또한 IP 전달을 방지하기 위해 EC2 인스턴스의 기본 홉 제한이 의도적으로 1로 설정되어 있다는 점에 유의해야 합니다. 결과적으로 EC2 인스턴스에서 실행되는 세션 토큰을 요청하는 파드는 결국 시간 초과되어 IMDSv1 데이터 흐름을 사용하도록 대체될 수 있습니다. EKS는 v1과 v2를 모두 _활성화_하고 eksctl 또는 공식 CloudFormation 템플릿으로 프로비저닝된 노드에서 홉 제한을 2로 변경하여 지원 IMDSv2를 추가합니다.

### 서비스 어카운트 토큰 자동 마운트 비활성화
애플리케이션이 Kubernetes API를 호출할 필요가 없는 경우 애플리케이션 의 PodSpec에서 `automountServiceAccountToken` 속성을 ` false`로 설정하거나 각 네임스페이스의 기본 서비스 어카운트을 패치하여 더 이상 파드에 자동으로 마운트되지 않도록 합니다. 예:
```bash 
kubectl patch serviceaccount default -p $'automountServiceAccountToken: false'
```

### 각 애플리케이션에 전용 서비스 어카운트 사용
각 애플리케이션에는 고유한 전용 서비스 어카운트이 있어야 합니다. 이는 쿠버네티스 API 및 IRSA의 서비스 어카운트에 적용됩니다.

!!! attention
    전체 클러스터 업그레이드를 수행하는 대신 클러스터 업그레이드에 블루/그린 접근 방식을 사용하는 경우 각 IRSA IAM 역할의 신뢰 정책을 새 클러스터의 OIDC 엔드포인트로 업데이트해야 합니다. 블루/그린 클러스터 업그레이드는 이전 클러스터와 함께 최신 버전의 쿠버네티스를 실행하는 클러스터를 생성하고 로드밸런서 또는 서비스 메시를 사용하여 이전 클러스터에서 실행되는 서비스에서 새 클러스터로 트래픽을 원활하게 이동하는 것입니다.

### 루트가 아닌 사용자로 애플리케이션 실행
컨테이너는 기본적으로 루트로 실행됩니다. 이렇게 하면 웹 자격 증명 토큰 파일을 읽을 수 있지만 컨테이너를 루트로 실행하는 것은 모범 사례로 간주되지 않습니다. 또는 PodSpec에 `spec.securityContext.runAsUser` 속성을 추가하는 것이 좋습니다. `runAsUser` 의 값 은 임의의 값입니다.

다음 예제에서 파드 내의 모든 프로세스는 `RunAsUser` 필드에 지정된 사용자 ID로 실행됩니다. 

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: security-context-demo
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
  containers:
  - name: sec-ctx-demo
    image: busybox
    command: [ "sh", "-c", "sleep 1h" ]
```

루트가 아닌 사용자로 컨테이너를 실행하면 기본적으로 토큰에 0600 [Root] 권한이 할당되기 때문에 컨테이너가 IRSA 서비스 어카운트 토큰을 읽을 수 없습니다. fsgroup=65534 [Nobody]를 포함하도록 컨테이너의 securityContext를 업데이트하면 컨테이너가 토큰을 읽을 수 있습니다.

```yaml
spec:
  securityContext:
    fsGroup: 65534
```

Kubernetes 1.19 및 이후 버전에서는 이 변경이 더 이상 필요하지 않습니다.

### 애플리케이션에 대한 최소 접근 권한 부여
[Action Hero](https://github.com/princespaghetti/actionhero)는 애플리케이션이 제대로 작동하는 데 필요한 AWS API 호출 및 해당 IAM 권한을 식별하기 위해 애플리케이션과 함께 실행할 수 있는 유틸리티입니다. 애플리케이션에 할당된 IAM 역할의 범위를 점진적으로 제한하는 데 도움이 된다는 점에서 [IAM Access Advisor](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_access-advisor.html)와 유사합니다. 자세한 내용은 AWS 리소스에 [최소 접근 권한](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html#grant-least-privilege) 부여에 대한 설명서를 참조하십시오.

### 불필요한 익명 접근 검토 및 철회

이상적으로는 모든 API 작업에 대해 익명의 접근을 비활성화하여야 합니다. 쿠버네티스 기본 제공 사용자 system:anonymous에 대한 RoleBinding 또는 ClusterRoleBinding을 생성하여 익명 액세스 권한을 부여합니다. [rbac-lookup](https://github.com/FairwindsOps/rbac-lookup) 도구를 사용하여 system:anonymous 사용자가 클러스터에 대해 갖는 권한을 식별할 수 있습니다.
```
./rbac-lookup | grep -P 'system:(anonymous)|(unauthenticated)'
system:anonymous               cluster-wide        ClusterRole/system:discovery
system:unauthenticated         cluster-wide        ClusterRole/system:discovery
system:unauthenticated         cluster-wide        ClusterRole/system:public-info-viewer
```

system:public-info-viewer외의 ClusterRole 또는 모든 역할은 system:anonymous 사용자 또는 system:unauthenticated 그룹에 바인딩되지 않아야 합니다.

특정 API에서 익명 액세스를 활성화해야 하는 정당한 이유가 있을 수 있습니다. 클러스터의 경우 익명 사용자가 특정 API만 액세스할 수 있도록 하고 인증 없이 해당 API를 노출해도 클러스터가 취약해지지 않도록 해야 합니다. 

Kubernetes/EKS 버전 1.14 이전에는 system:unauthenticated 그룹이 기본적으로 system:discovery 및 system:basic-user 클러스터 역할에 연결되었습니다. 클러스터를 버전 1.14 이상으로 업데이트했더라도 클러스터를 업데이트해도 이런 권한이 취소되지 않으므로 클러스터에서 이런 권한이 계속 활성화될 수 있습니다.
system:public-info-viewer를 제외하고 어떤 ClusterRole에 "system:unauthenticated"가 있는지 확인하려면 다음 명령을 실행할 수 있습니다(jq 유틸리티가 필요합니다):

```
kubectl get ClusterRoleBinding -o json | jq -r '.items[] | select(.subjects[]?.name =="system:unauthenticated") | select(.metadata.name != "system:public-info-viewer") | .metadata.name'
```

그리고 "system:unauthenticated"는 아래 명령을 사용하여 "system:public-info-viewer"를 제외한 모든 역할에서 제거할 수 있습니다.
```
kubectl get ClusterRoleBinding -o json | jq -r '.items[] | select(.subjects[]?.name =="system:unauthenticated") | select(.metadata.name != "system:public-info-viewer") | del(.subjects[] | select(.name =="system:unauthenticated"))' | kubectl apply -f -
```

또는 kubectl describe 및 kubectl edit을 사용하여 수동으로 확인하고 제거할 수 있다. system:unauthenticated 그룹에 클러스터에 대한 system:discovery 권한이 있는지 확인하려면 다음 명령을 실행하십시오. 
```
kubectl describe clusterrolebindings system:discovery

Name:         system:discovery
Labels:       kubernetes.io/bootstrapping=rbac-defaults
Annotations:  rbac.authorization.kubernetes.io/autoupdate: true
Role:
  Kind:  ClusterRole
  Name:  system:discovery
Subjects:
  Kind   Name                    Namespace
  ----   ----                    ---------
  Group  system:authenticated
  Group  system:unauthenticated
```

system:unauthenticated 그룹에 클러스터에 대한 system:basic-user 권한이 있는지 확인하려면 다음 명령을 실행합니다.
```
kubectl describe clusterrolebindings system:basic-user

Name:         system:basic-user
Labels:       kubernetes.io/bootstrapping=rbac-defaults
Annotations:  rbac.authorization.kubernetes.io/autoupdate: true
Role:
  Kind:  ClusterRole
  Name:  system:basic-user
Subjects:
  Kind   Name                    Namespace
  ----   ----                    ---------
  Group  system:authenticated
  Group  system:unauthenticated
```

system:unauthenticated 그룹이 클러스터의 system:discovery 및/또는 system:basic-user ClusterRoles에 바인딩된 경우 이런 역할을 system:unauthenticated 그룹에서 분리해야 합니다. 다음 명령을 사용하여 system:discovery ClusterRoleBinding을 편집합니다:
```
kubectl edit clusterrolebindings system:discovery
```
위 명령은 아래와 같이 편집기에서 system:discovery ClusterRoleBinding의 현재 정의를 엽니다:
```yaml
# Please edit the object below. Lines beginning with a '#' will be ignored,
# and an empty file will abort the edit. If an error occurs while saving this file will be
# reopened with the relevant failures.
#
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  annotations:
    rbac.authorization.kubernetes.io/autoupdate: "true"
  creationTimestamp: "2021-06-17T20:50:49Z"
  labels:
    kubernetes.io/bootstrapping: rbac-defaults
  name: system:discovery
  resourceVersion: "24502985"
  selfLink: /apis/rbac.authorization.k8s.io/v1/clusterrolebindings/system%3Adiscovery
  uid: b7936268-5043-431a-a0e1-171a423abeb6
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:discovery
subjects:
- apiGroup: rbac.authorization.k8s.io
  kind: Group
  name: system:authenticated
- apiGroup: rbac.authorization.k8s.io
  kind: Group
  name: system:unauthenticated
```
위 편집기 화면의 "Subjects" 섹션에서 system:unauthenticated 그룹 항목을 삭제합니다.

system:basic-user ClusterRoleBinding에 대해 동일한 단계를 반복합니다.

### 대체 접근 방식
IRSA는 파드에 AWS "ID"를 할당하는 _선호 되는 방법_이지만 애플리케이션에 최신 버전의 AWS SDK를 포함해야 합니다. 현재 IRSA를 지원하는 SDK의 전체 목록은 [AWS 문서](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts-minimum-sdk.html)를 참조합니다. IRSA 호환 SDK로 즉시 업데이트할 수 없는 애플리케이션이 있는 경우, [kube2iam](https://github.com/jtblin/kube2iam) 및 [kiam](https://github.com/uswitch/kiam) 을 포함하여 쿠버네티스 파드에 IAM 역할을 할당하는 데 사용할 수 있는 몇 가지 커뮤니티 구축 솔루션이 있습니다. AWS는 이런 솔루션의 사용을 보증하거나 용인하지 않지만 IRSA와 유사한 결과를 얻기 위해 커뮤니티에서 자주 사용합니다.
