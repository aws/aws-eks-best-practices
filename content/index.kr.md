# 소개
EKS 모범 사례 가이드에 오신 것을 환영합니다. 이 프로젝트의 주요 목표는 Amazon EKS의 Day 2 작업에 대한 일련의 모범 사례를 제공하는 것입니다. 우리는 이 지침을 GitHub에 게시하기로 결정하여 신속하게 반복하고, 다양한 문제에 대해 시기 적절하고 효과적인 권장 사항을 제공하고, 더 광범위한 커뮤니티의 제안을 쉽게 통합할 수 있습니다.

현재 다음 주제에 대한 가이드를 게시했습니다.

* [보안 모범 사례](security/docs/)
* [신뢰성 모범 사례](reliability/docs/)
* 클러스터 오토스케일링 모범 사례: [karpenter](karpenter/), [cluster-autoscaler](cluster-autoscaling/)
* [Windows 컨테이너 실행 모범 사례](windows/docs/ami/)
* [네트워킹 모범 사례](networking/index/)
* [확장성 모범 사례](scalability/docs/)
* [클러스터 업그레이드 모범 사례](upgrades/)
* [비용 최적화 모범 사례](cost_optimization/cfm_framework.md)

또한 이 가이드의 권장 사항 중 일부를 확인하기 위해 [hardeneks](https://github.com/aws-samples/hardeneks)라는 Python 기반 CLI(Command Line Interface)를 오픈 소스로 제공했습니다.

향후 성능, 비용 최적화 및 운영 우수성에 대한 모범 사례 지침을 게시할 예정입니다.

## 관련 가이드
AWS는 [EKS 사용자 가이드](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html)외에도 EKS 구성에 도움이 될 수 있는 몇 가지 다른 가이드를 게시했습니다.

* [EMR 컨테이너 모범 사례 가이드](https://aws.github.io/aws-emr-containers-best-practices/)
* [Data on EKS](https://awslabs.github.io/data-on-eks/)
* [AWS 옵저버빌리티 모범 사례](https://aws-observability.github.io/observability-best-practices/)
* [Amazon EKS Blueprints for Terraform](https://aws-ia.github.io/terraform-aws-eks-blueprints/)
* [Amazon EKS Blueprints Quick Start](https://aws-quickstart.github.io/cdk-eks-blueprints/)

## 기여
이 가이드에 기여해 주시기 바랍니다. 효과가 입증된 방법을 구현했다면 이슈나 풀 리퀘스트(PR)를 열어 공유해 주세요.마찬가지로, 이미 게시한 지침에서 오류나 결함을 발견한 경우 PR을 제출하여 수정하시기 바랍니다. PR 제출 지침은 [기여 가이드라인](https://github.com/aws/aws-eks-best-practices/blob/master/CONTRIBUTING.md)에서 확인할 수 있습니다.
