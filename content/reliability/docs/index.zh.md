# Amazon EKS 可靠性最佳实践指南

本节提供了有关使 EKS 上运行的工作负载具有弹性和高可用性的指导。

## 如何使用本指南

本指南面向希望在 EKS 中开发和运营高可用且容错的服务的开发人员和架构师。本指南按不同主题领域组织，以便于阅读。每个主题都以简要概述开头，然后列出了确保您的 EKS 集群可靠性的建议和最佳实践。

## 简介

EKS 的可靠性最佳实践分为以下几个主题：

* 应用程序
* 控制平面
* 数据平面

---

什么使一个系统可靠？如果一个系统在一段时间内能够持续运行并满足需求，即使环境发生变化，它也可以被称为可靠。为了实现这一点，系统必须能够检测故障、自动修复自身，并具有根据需求进行扩展的能力。

客户可以使用 Kubernetes 作为运行关键任务应用程序和服务的可靠基础。但除了采用基于容器的应用程序设计原则外，可靠地运行工作负载还需要可靠的基础设施。在 Kubernetes 中，基础设施包括控制平面和数据平面。

EKS 提供了一个经过生产级别设计的高可用且容错的 Kubernetes 控制平面。

在 EKS 中，AWS 负责 Kubernetes 控制平面的可靠性。EKS 在一个 AWS 区域的三个可用区中运行 Kubernetes 控制平面。它自动管理 Kubernetes API 服务器和 etcd 集群的可用性和可扩展性。

数据平面的可靠性责任在您(客户)和 AWS 之间共享。EKS 为 Kubernetes 数据平面提供了三种选择。Fargate 是最受管理的选项，负责数据平面的供应和扩展。第二个选项是托管节点组，负责数据平面的供应和更新。最后，自管理节点是数据平面最不受管理的选项。您使用的 AWS 管理数据平面越多，您承担的责任就越少。

[托管节点组](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html)自动执行 EC2 节点的供应和生命周期管理。您可以使用 EKS API (通过 EKS 控制台、AWS API、AWS CLI、CloudFormation、Terraform 或 `eksctl`)来创建、扩展和升级托管节点。托管节点在您的账户中运行 EKS 优化的 Amazon Linux 2 EC2 实例，您可以通过启用 SSH 访问来安装自定义软件包。当您供应托管节点时，它们将作为 EKS 管理的 Auto Scaling 组的一部分运行，该组可跨多个可用区;您可以通过创建托管节点时提供的子网来控制这一点。EKS 还会自动为托管节点添加标签，以便与集群自动扩缩器一起使用。

> Amazon EKS 遵循托管节点组的 CVE 和安全补丁的共享责任模型。由于托管节点运行 Amazon EKS 优化的 AMI，因此当有错误修复时，Amazon EKS 负责构建这些 AMI 的修补版本。但是，您负责将这些修补后的 AMI 版本部署到您的托管节点组。

EKS 还[管理节点的更新](https://docs.aws.amazon.com/eks/latest/userguide/update-managed-node-group.html),尽管您必须启动更新过程。[更新托管节点](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-update-behavior.html)的过程在 EKS 文档中有解释。

如果您运行自管理节点，您可以使用 [Amazon EKS 优化的 Linux AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html) 来创建工作节点。您负责对 AMI 和节点进行修补和升级。使用 `eksctl`、CloudFormation 或基础设施作为代码工具来供应自管理节点是最佳实践，因为这将使您更容易[升级自管理节点](https://docs.aws.amazon.com/eks/latest/userguide/update-workers.html)。在更新工作节点时，请考虑[迁移到新节点](https://docs.aws.amazon.com/eks/latest/userguide/migrate-stack.html),因为迁移过程会在新堆栈准备好接受现有 pod 工作负载后，将旧节点组标记为 `NoSchedule` 并**排空**节点。但是，您也可以对自管理节点执行[就地升级](https://docs.aws.amazon.com/eks/latest/userguide/update-stack.html)。

![共享责任模型 - Fargate](./images/SRM-Fargate.jpeg)

![共享责任模型 - MNG](./images/SRM-MNG.jpeg)

本指南包含了一系列建议，您可以使用这些建议来提高 EKS 数据平面、Kubernetes 核心组件和您的应用程序的可靠性。

## 反馈
本指南在 GitHub 上发布，旨在收集来自更广泛的 EKS/Kubernetes 社区的直接反馈和建议。如果您有任何认为我们应该在指南中包含的最佳实践，请在 GitHub 存储库中提出问题或提交 PR。我们打算在服务添加新功能或出现新的最佳实践时，定期更新本指南。