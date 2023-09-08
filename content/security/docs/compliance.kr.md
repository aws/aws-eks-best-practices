# 규정 준수

규정 준수는 AWS와 해당 서비스 소비자 간의 공동 책임입니다. 일반적으로 AWS는 "클라우드 보안"을 담당하고 사용자는 "클라우드 보안"을 담당합니다. AWS와 해당 사용자가 책임지는 항목을 설명하는 선은 서비스에 따라 다릅니다. 예를 들어 Fargate에서 AWS는 데이터 센터, 하드웨어, 가상 인프라(Amazon EC2) 및 컨테이너 런타임(Docker)의 물리적 보안 관리를 담당합니다. Fargate 사용자는 컨테이너 이미지와 해당 애플리케이션을 보호할 책임이 있습니다. 규정 준수 표준을 준수해야 하는 워크로드를 실행할 때 중요한 고려 사항에 대한 책임자를 파악합니다.

다음 표는 다양한 컨테이너 서비스가 준수하는 규정 준수 프로그램을 보여줍니다.

| 컴플라이언스 프로그램 | Amazon ECS 오케스트레이터 | Amazon EKS 오케스트레이터| ECS 파게이트 | 아마존 ECR |
| --- |:----------:|:----------:|:---- -------:|:----------:|
| PCI DSS 레벨 1 | 1 | 1 | 1 | 1 |
| HIPAA 적격 | 1 | 1 | 1 | 1 |
| SOC I | 1 | 1 | 1 | 1 |
| SOC II | 1 | 1 | 1 | 1 |
| SOC III | 1 | 1 | 1 | 1 |
| ISO 27001:2013 | 1 | 1 | 1 | 1 |
| ISO 9001:2015 | 1 | 1 | 1 | 1 |
| ISO 27017:2015 | 1 | 1 | 1 | 1 |
| ISO 27018:2019 | 1 | 1 | 1 | 1 |
| IRAP | 1 | 1 | 1 | 1 |
| FedRAMP 중간(동/서) | 1 | 1 | 0 | 1 |
| FedRAMP 높음(GovCloud) | 1 | 1 | 0 | 1 |
| 국방부 CC SRG | 1 | DISA 검토(IL5) | 0 | 1 |
| 히파아 바아 | 1 | 1 | 1 | 1 |
| MTCS | 1 | 1 | 0 | 1 |
| C5 | 1 | 1 | 0 | 1 |
| K-ISMS | 1 | 1 | 0 | 1 |
| ENS 높음 | 1 | 1 | 0 | 1 |
| 오스파 | 1 | 1 | 0 | 1 |
| 히트러스트 CSF | 1 | 1 | 1 | 1 |

규정 준수 상태는 시간이 지남에 따라 변경됩니다. 최신 상태는 항상 [https://aws.amazon.com/compliance/services-in-scope/](https://aws.amazon.com/compliance/services-in-scope/)를 참조하십시오.

클라우드 인증 모델 및 모범 사례에 대한 자세한 내용은 AWS 백서 [안전한 클라우드 채택을 위한 인증 모델](https://d1.awsstatic.com/whitepapers/accreditation-models-for-secure-cloud-adoption.pdf)을 참조하십시오. )

## 왼쪽으로 이동

왼쪽으로 이동한다는 개념에는 소프트웨어 개발 수명 주기 초기에 정책 위반 및 오류를 포착하는 것이 포함됩니다. 보안 관점에서 이것은 매우 유익할 수 있습니다. 예를 들어 개발자는 애플리케이션을 클러스터에 배포하기 전에 구성 문제를 수정할 수 있습니다. 이와 같은 실수를 조기에 포착하면 정책을 위반하는 구성이 배포되는 것을 방지할 수 있습니다.

### 코드로서의 정책

정책은 행동(즉, 허용되는 행동 또는 금지되는 행동)을 관리하기 위한 일련의 규칙으로 생각할 수 있습니다. 예를 들어 컨테이너가 루트가 아닌 사용자로 실행되도록 하는 USER 지시문을 모든 Dockerfile에 포함해야 한다는 정책이 있을 수 있습니다. 문서로서 이와 같은 정책은 발견하고 시행하기 어려울 수 있습니다. 요구 사항이 변경됨에 따라 구식이 될 수도 있습니다. PaC(Policy as Code) 솔루션을 사용하면 알려진 지속적인 위협을 탐지, 예방, 감소 및 대응하는 보안, 규정 준수 및 개인 정보 제어를 자동화할 수 있습니다. 또한 정책을 코드화하고 다른 코드 아티팩트처럼 정책을 관리할 수 있는 메커니즘을 제공합니다. 이 접근 방식의 이점은 DevOps 및 GitOps 전략을 재사용하여 Kubernetes 클러스터 전체에서 정책을 관리하고 일관되게 적용할 수 있다는 것입니다. PaC 옵션 및 PSP의 미래에 대한 정보는 [Pod Security](https://aws.github.io/aws-eks-best-practices/security/docs/pods/#pod-security)를 참조하십시오.

## 추천

### 파이프라인에서 정책 코드 도구를 사용하여 배포 전에 위반 감지

[OPA](https://www.openpolicyagent.org/)는 CNCF의 일부인 오픈 소스 정책 엔진입니다. 정책 결정을 내리는 데 사용되며 다양한 방식으로 실행할 수 있습니다. 언어 라이브러리 또는 서비스로. OPA 정책은 Rego라는 도메인 특정 언어(DSL)로 작성됩니다. [Gatekeeper](https://github.com/open-policy-agent/gatekeeper) 프로젝트로 Kubernetes 동적 승인 컨트롤러의 일부로 실행되는 경우가 많지만 OPA는 CI/CD 파이프라인에 통합될 수도 있습니다. 이를 통해 개발자는 릴리스 주기 초기에 구성에 대한 피드백을 얻을 수 있으므로 프로덕션에 들어가기 전에 문제를 해결하는 데 도움이 될 수 있습니다. 이 프로젝트에 대한 일반적인 OPA 정책 모음은 GitHub [저장소](https://github.com/aws/aws-eks-best-practices/tree/master/policies/opa)에서 찾을 수 있습니다.

+ [Conftest](https://github.com/open-policy-agent/conftest)는 OPA를 기반으로 구축되었으며 Kubernetes 구성 테스트를 위한 개발자 중심 환경을 제공합니다.
+ [sKan](https://github.com/alcideio/skan)은 OPA로 구동되며 Kubernetes 구성 파일이 보안 및 운영 모범 사례를 준수하는지 여부를 확인하기 위해 "맞춤형"입니다.

[Kyverno](https://kyverno.io/)는 Kubernetes용으로 설계된 정책 엔진입니다. Kyverno를 사용하면 정책이 관리됩니다.