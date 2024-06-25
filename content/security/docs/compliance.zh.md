# 合规性

合规性是AWS与其服务消费者之间的共同责任。一般而言，AWS负责"云的安全性",而其用户则负责"云中的安全性"。AWS和其用户负责的范围将因服务而异。例如，对于Fargate，AWS负责管理其数据中心的物理安全性、硬件、虚拟基础设施(Amazon EC2)和容器运行时(Docker)。Fargate的用户则负责确保容器镜像和应用程序的安全性。了解谁负责什么是运行必须遵守合规标准的工作负载时的一个重要考虑因素。

下表显示了不同容器服务符合的合规性程序。

| 合规性程序 | Amazon ECS 编排器 | Amazon EKS 编排器| ECS Fargate | Amazon ECR |
| ------------------ |:----------:|:----------:|:-----------:|:----------:|
| PCI DSS 1级 | 1 | 1 | 1 | 1 |
| HIPAA 合格 | 1 | 1 | 1 | 1 |
| SOC I | 1 | 1 | 1 | 1 |
| SOC II | 1 | 1 | 1 | 1 |
| SOC III | 1 | 1 | 1 | 1 |
| ISO 27001:2013 | 1 | 1 | 1 | 1 |
| ISO 9001:2015 | 1 | 1 | 1 | 1 |
| ISO 27017:2015 | 1 | 1 | 1 | 1 |
| ISO 27018:2019 | 1 | 1 | 1 | 1 |
| IRAP | 1 | 1 | 1 | 1 |
| FedRAMP 中等级(东部/西部) | 1 | 1 | 0 | 1 |
| FedRAMP 高级(GovCloud) | 1 | 1 | 0 | 1 |
| DOD CC SRG | 1 | DISA 审查(IL5) | 0 | 1 |
| HIPAA BAA | 1 | 1 | 1 | 1 |
| MTCS | 1 | 1 | 0 | 1 |
| C5 | 1 | 1 | 0 | 1 |
| K-ISMS | 1 | 1 | 0 | 1 |
| ENS 高级 | 1 | 1 | 0 | 1 |
| OSPAR | 1 | 1 | 0 | 1 |
| HITRUST CSF | 1 | 1 | 1 | 1 |

合规性状态会随时间而变化。有关最新状态，请始终参考 [https://aws.amazon.com/compliance/services-in-scope/](https://aws.amazon.com/compliance/services-in-scope/)。

有关云认证模型和最佳实践的更多信息，请参阅 AWS 白皮书 [Accreditation Models for Secure Cloud Adoption](https://d1.awsstatic.com/whitepapers/accreditation-models-for-secure-cloud-adoption.pdf)

## 左移

左移的概念涉及在软件开发生命周期的早期捕获政策违规和错误。从安全角度来看，这可能会带来很大好处。例如，开发人员可以在将应用程序部署到集群之前修复其配置中的问题。提早发现并修复这类错误将有助于防止违反政策的配置被部署。

### 作为代码的政策

政策可以被视为管理行为的一组规则，即允许或禁止的行为。例如，您可能有一项政策规定所有 Dockerfile 都应包含一个 USER 指令，使容器以非 root 用户身份运行。作为文档，这样的政策可能难以发现和执行。随着您的要求发生变化，它也可能会过时。使用作为代码的政策(PaC)解决方案，您可以自动化安全性、合规性和隐私控制，以检测、预防、减少和应对已知和持续的威胁。此外，它们为您提供了一种机制，可以将您的政策编码并像管理其他代码工件一样管理它们。这种方法的好处是，您可以重用 DevOps 和 GitOps 策略来管理和一致地应用于整个 Kubernetes 集群。有关 PaC 选项和 PSP 的未来的信息，请参阅 [Pod 安全性](https://aws.github.io/aws-eks-best-practices/security/docs/pods/#pod-security)。

### 在管道中使用作为代码的政策工具来检测部署前的违规行为

- [OPA](https://www.openpolicyagent.org/) 是 CNCF 的一个开源政策引擎。它用于做出政策决策，可以以多种不同方式运行，例如作为语言库或服务。OPA 策略是用一种名为 Rego 的领域特定语言(DSL)编写的。虽然它通常作为 [Gatekeeper](https://github.com/open-policy-agent/gatekeeper) 项目的 Kubernetes 动态准入控制器的一部分运行，但 OPA 也可以被纳入您的 CI/CD 管道。这允许开发人员在发布周期的早期获得有关其配置的反馈，从而可以在进入生产环境之前解决问题。一组常见的 OPA 策略可以在本项目的 GitHub [存储库](https://github.com/aws/aws-eks-best-practices/tree/master/policies/opa)中找到。
- [Conftest](https://github.com/open-policy-agent/conftest) 建立在 OPA 之上，它为测试 Kubernetes 配置提供了一个面向开发人员的体验。
- [Kyverno](https://kyverno.io/) 是一个为 Kubernetes 设计的策略引擎。使用 Kyverno，策略被管理为 Kubernetes 资源，无需学习新的语言即可编写策略。这允许使用熟悉的工具(如 kubectl、git 和 kustomize)来管理策略。Kyverno 策略可以验证、变更和生成 Kubernetes 资源，并确保 OCI 镜像供应链安全。[Kyverno CLI](https://kyverno.io/docs/kyverno-cli/) 可用于在 CI/CD 管道中测试策略和验证资源。所有 Kyverno 社区策略都可以在 [Kyverno 网站](https://kyverno.io/policies/)上找到，有关在管道中使用 Kyverno CLI 编写测试的示例，请参阅 [policies 存储库](https://github.com/kyverno/policies)。

## 工具和资源

- [Amazon EKS 安全沉浸式研讨会 - 监管合规性](https://catalog.workshops.aws/eks-security-immersionday/en-US/10-regulatory-compliance)
- [kube-bench](https://github.com/aquasecurity/kube-bench)
- [docker-bench-security](https://github.com/docker/docker-bench-security)
- [AWS Inspector](https://aws.amazon.com/inspector/)
- [Kubernetes 安全审查](https://github.com/kubernetes/community/blob/master/sig-security/security-audit-2019/findings/Kubernetes%20Final%20Report.pdf) Kubernetes 1.13.4 (2019) 的第三方安全评估
- [NeuVector by SUSE](https://www.suse.com/neuvector/) 开源、零信任容器安全平台，提供合规性报告和自定义合规性检查