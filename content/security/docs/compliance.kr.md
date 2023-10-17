# 컴플라이언스

컴플라이언스는 AWS와 해당 서비스 소비자 간의 공동 책임입니다. 일반적으로 AWS는 “클라우드의 보안”을 책임지고, 사용자는 “클라우드에서의 보안”을 담당합니다. AWS와 해당 사용자가 책임져야 할 책임을 설명하는 선은 서비스에 따라 달라집니다. 예를 들어 Fargate를 통해 AWS는 데이터 센터, 하드웨어, 가상 인프라 (Amazon EC2) 및 컨테이너 런타임(Docker)의 물리적 보안을 관리할 책임이 있습니다. Fargate 사용자는 컨테이너 이미지와 해당 애플리케이션을 보호할 책임이 있습니다. 컴플라이언스 표준을 준수해야 하는 워크로드를 실행할 때 고려해야 할 중요한 사항은 누구의 책임자인지 파악하는 것입니다.

다음 표는 다양한 컨테이너 서비스가 준수하는 규정 준수 프로그램을 보여줍니다.

| 컴플라이언스 프로그램 | Amazon ECS 오케스트레이터 | Amazon EKS 오케스트레이터| ECS Fargete | 아마존 ECR |
| --- |:----------:|:----------:|:---- -------:|:----------:|
| PCI DSS Level 1	| 1 | 1 | 1 | 1 |
| HIPAA Eligible	| 1 | 1	| 1	| 1 |
| SOC I | 1 | 1 | 1 | 1 |
| SOC II | 1 |	1 |	1 |	1 |
| SOC III |	1 |	1 |	1 |	1 |
| ISO 27001:2013 | 1 | 1 | 1 | 1 |
| ISO 9001:2015 | 1 | 1 | 1 | 1 |
| ISO 27017:2015 |	1 |	1 |	1 |	1 |
| ISO 27018:2019 |	1 |	1 |	1 |	1 |
| IRAP | 1 | 1 | 1 | 1 |
| FedRAMP Moderate (East/West) | 1 | 1 | 0 | 1 |
| FedRAMP High (GovCloud) | 1 | 1 | 0 | 1 |
| DOD CC SRG | 1 |	DISA Review (IL5) |	0 |	1 |
| HIPAA BAA | 1 | 1 | 1 | 1 |
| MTCS | 1 | 1 | 0 | 1 |
| C5 | 1 | 1 | 0 | 1 |
| K-ISMS | 1 | 1 | 0 | 1 |
| ENS High | 1 | 1 | 0 | 1 |
| OSPAR | 1 | 1 | 0 | 1 |
| HITRUST CSF | 1 | 1 | 1 | 1 |

컴플라이언스 상태는 시간이 지남에 따라 변경됩니다. 최신 상태는 항상 [https://aws.amazon.com/compliance/services-in-scope/](https://aws.amazon.com/compliance/services-in-scope/)를 참조하십시오.

클라우드 인증 모델 및 모범 사례에 대한 자세한 내용은 AWS 백서 [안전한 클라우드 채택을 위한 인증 모델](https://d1.awsstatic.com/whitepapers/accreditation-models-for-secure-cloud-adoption.pdf)을 참조하십시오.

## Shift Left

Shift Left 개념은 소프트웨어 개발 수명 주기 초기에 정책 위반 및 오류를 포착하는 것이 포함됩니다. 보안 관점에서 이것은 매우 유익할 수 있습니다. 예를 들어 개발자는 애플리케이션을 클러스터에 배포하기 전에 구성 문제를 수정할 수 있습니다. 이와 같은 실수를 조기에 포착하면 정책을 위반하는 구성이 배포되는 것을 방지할 수 있습니다.

### 코드로서의 정책

정책은 행동, 즉 허용된 행동 또는 금지된 행동을 규제하기 위한 일련의 규칙으로 생각할 수 있습니다. 예를 들어 모든 Dockerfile에는 컨테이너를 루트 사용자가 아닌 사용자로 실행하도록 하는 USER 지시문이 포함되어야 한다는 정책이 있을 수 있습니다. 문서로서 이와 같은 정책은 발견하고 적용하기 어려울 수 있습니다. 요구 사항이 변경됨에 따라 이 정책이 시대에 뒤처질 수도 있습니다. PaC (Policy as Code) 솔루션을 사용하면 알려진 위협과 지속적인 위협을 탐지, 예방, 감소 및 대응하는 보안, 규정 준수 및 개인 정보 보호 제어를 자동화할 수 있습니다. 또한 정책을 체계화하고 다른 코드 아티팩트와 마찬가지로 관리할 수 있는 메커니즘을 제공합니다. 이 접근 방식의 이점은 DevOps 및 GitOps 전략을 재사용하여 Kubernetes 클러스터 전체에 정책을 관리하고 일관되게 적용할 수 있다는 것입니다. PAC 옵션과 PSP의 미래에 대한 자세한 내용은 [파드 보안](https://aws.github.io/aws-eks-best-practices/security/docs/pods/#pod-security) 을 참조하십시오.

## 권장 사항

### 파이프라인에서 PaC 도구를 사용하여 배포 전에 위반 감지

+ [OPA](https://www.openpolicyagent.org/)는 CNCF의 일부인 오픈 소스 정책 엔진입니다. 정책 결정을 내리는 데 사용되며 언어 라이브러리 또는 서비스 등 다양한 방식으로 실행할 수 있습니다. OPA 정책은 Rego라는 도메인 특정 언어(DSL) 로 작성됩니다. OPA는 쿠버네티스 동적 어드미션 컨트롤러의 일부로 [게이트키퍼](https://github.com/open-policy-agent/gatekeeper) 프로젝트로 실행되는 경우가 많지만, OPA는 CI/CD 파이프라인에 통합될 수도 있습니다. 이를 통해 개발자는 릴리스 주기 초기에 구성에 대한 피드백을 받을 수 있으며, 이를 통해 프로덕션에 들어가기 전에 문제를 해결하는 데 도움이 될 수 있습니다. 일반적인 OPA 정책 모음은 이 프로젝트의 GitHub [리포지토리](https://github.com/aws/aws-eks-best-practices/tree/master/policies/opa)에서 찾을 수 있습니다.
+ [Conftest](https://github.com/open-policy-agent/conftest) 는 OPA를 기반으로 구축되었으며 쿠버네티스 구성을 테스트하기 위한 개발자 중심의 경험을 제공합니다.
+ [Kyverno](https://kyverno.io/) 는 쿠버네티스용으로 설계된 정책 엔진입니다.Kyverno를 사용하면 정책이 쿠버네티스 리소스로 관리되므로 정책을 작성하는 데 새로운 언어가 필요하지 않습니다. 이를 통해 kubectl, git, kustomize와 같은 친숙한 도구를 사용하여 정책을 관리할 수 있습니다.Kyverno 정책은 Kubernetes 리소스를 검증, 변경 및 생성하고 OCI 이미지 공급망 보안을 보장할 수 있습니다. [Kyverno CLI](https://kyverno.io/docs/kyverno-cli/)는 CI/CD 파이프라인의 일부로 정책을 테스트하고 리소스를 검증하는 데 사용할 수 있습니다. 모든 Kyverno 커뮤니티 정책은 [Kyverno 웹 사이트](https://kyverno.io/policies/)에서 확인할 수 있으며, Kyverno CLI를 사용하여 파이프라인에서 테스트를 작성하는 예는 [정책 리포지토리](https://github.com/kyverno/policies)를 참조하십시오.

## 도구 및 리소스 

+ [kube-bench](https://github.com/aquasecurity/kube-bench)
+ [docker-bench-security](https://github.com/docker/docker-bench-security)
+ [AWS Inspector](https://aws.amazon.com/inspector/)
+ [Kubernetes Security Review](https://github.com/kubernetes/community/blob/master/sig-security/security-audit-2019/findings/Kubernetes%20Final%20Report.pdf) 쿠버네티스 버전 1.13.4에 대한 서드파티 보안 평가(2019)
