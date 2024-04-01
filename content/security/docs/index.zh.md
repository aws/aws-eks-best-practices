# Amazon EKS 安全最佳实践指南

本指南提供了有关在交付业务价值的同时保护依赖于 EKS 的信息、系统和资产的建议，包括风险评估和缓解策略。本指南中的指导是 AWS 发布的一系列最佳实践指南的一部分，旨在帮助客户按照最佳实践实施 EKS。关于性能、运营卓越、成本优化和可靠性的指南将在未来几个月内推出。

## 如何使用本指南

本指南面向负责实施和监控 EKS 集群及其支持的工作负载的安全控制有效性的安全从业人员。本指南按主题区域组织，以便于阅读。每个主题都以简要概述开始，然后列出了确保 EKS 集群安全的建议和最佳实践。主题不需按特定顺序阅读。

## 了解共享责任模型

在使用 EKS 等托管服务时，安全性和合规性被视为共享责任。一般而言，AWS 负责"云"的安全，而您作为客户则负责"云中"的安全。对于 EKS，AWS 负责管理 EKS 托管的 Kubernetes 控制平面。这包括 Kubernetes 控制平面节点、ETCD 数据库以及 AWS 交付安全可靠服务所需的其他基础设施。作为 EKS 的消费者，您主要负责本指南中的主题，例如 IAM、Pod 安全性、运行时安全性、网络安全性等。

在基础设施安全方面，随着从自管理工作节点到托管节点组再到 Fargate，AWS 将承担更多责任。例如，对于 Fargate，AWS 将负责确保运行您的 Pod 的底层实例/运行时的安全。

![共享责任模型 - Fargate](images/SRM-EKS.jpg)

AWS 还将负责使 EKS 优化的 AMI 保持最新的 Kubernetes 补丁版本和安全补丁。使用托管节点组 (MNG) 的客户负责通过 EKS API、CLI、Cloudformation 或 AWS 控制台将其节点组升级到最新的 AMI。另外，与 Fargate 不同，MNG 不会自动扩展您的基础设施/集群。这可以由 [cluster-autoscaler](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md) 或其他技术(如 [Karpenter](https://karpenter.sh/)、AWS 本地自动缩放、SpotInst 的 [Ocean](https://spot.io/solutions/kubernetes-2/) 或 Atlassian 的 [Escalator](https://github.com/atlassian/escalator)) 来处理。

![共享责任模型 - MNG](./images/SRM-MNG.jpg)

在设计系统之前，了解您的责任与服务提供商 (AWS) 的责任之间的分界线非常重要。

有关共享责任模型的更多信息，请参阅 [https://aws.amazon.com/compliance/shared-responsibility-model/](https://aws.amazon.com/compliance/shared-responsibility-model/)

## 简介

在使用 EKS 等托管 Kubernetes 服务时，有几个安全最佳实践领域很重要：

- 身份和访问管理
- Pod 安全性
- 运行时安全性
- 网络安全性
- 多租户
- 多账户用于多租户
- 检测控制
- 基础设施安全性
- 数据加密和密钥管理
- 法规遵从性
- 事件响应和取证
- 镜像安全性

在设计任何系统时，您都需要考虑其安全影响以及可能影响安全态势的实践。例如，您需要控制谁可以对一组资源执行操作。您还需要能够快速识别安全事件，保护系统和服务免受未经授权的访问，并通过数据保护来维护数据的机密性和完整性。拥有一套明确定义和经过演练的响应安全事件的流程也将提高您的安全态势。这些工具和技术很重要，因为它们支持诸如防止财务损失或遵守监管义务等目标。

AWS 通过提供一套丰富的安全服务来帮助组织实现其安全和合规目标，这些服务是根据广泛的安全意识客户的反馈而不断发展的。通过提供高度安全的基础，客户可以减少"非差异化的繁重工作",而将更多时间用于实现业务目标。

## 反馈

本指南在 GitHub 上发布，以便从更广泛的 EKS/Kubernetes 社区收集直接反馈和建议。如果您有任何认为我们应该在指南中包含的最佳实践，请在 GitHub 存储库中提出问题或提交 PR。我们的目的是在服务添加新功能或出现新的最佳实践时，定期更新本指南。

## 进一步阅读

[Kubernetes 安全白皮书](https://github.com/kubernetes/sig-security/blob/main/sig-security-external-audit/security-audit-2019/findings/Kubernetes%20White%20Paper.pdf),由安全审计工作组赞助，本白皮书描述了 Kubernetes 攻击面和安全架构的关键方面，旨在帮助安全从业人员做出明智的设计和实施决策。

CNCF 还发布了一份[白皮书](https://github.com/cncf/tag-security/blob/efb183dc4f19a1bf82f967586c9dfcb556d87534/security-whitepaper/v2/CNCF_cloud-native-security-whitepaper-May2022-v2.pdf)关于云原生安全。该白皮书检查了技术环境如何发展，并倡导采用与 DevOps 流程和敏捷方法相一致的安全实践。

## 工具和资源

[Amazon EKS 安全沉浸式研讨会](https://catalog.workshops.aws/eks-security-immersionday/en-US)