# 介绍
欢迎阅读 EKS 最佳实践指南。本项目的主要目标是为 Amazon EKS 的第二天运维提供一套最佳实践。我们选择将此指南发布到 GitHub 上，以便我们能够快速迭代、及时有效地为各种问题提供建议，并轻松地纳入更广泛社区的建议。

我们目前已发布以下主题的指南：

* [安全最佳实践](security/docs/)
* [可靠性最佳实践](reliability/docs/)
* 集群自动扩缩最佳实践： [karpenter](karpenter/)、[cluster-autoscaler](cluster-autoscaling/)
* [运行 Windows 容器的最佳实践](windows/docs/ami/)
* [网络最佳实践](networking/index/)
* [可扩展性最佳实践](scalability/docs/)
* [集群升级最佳实践](upgrades/)
* [成本优化最佳实践](cost_optimization/cfm_framework.md)

我们还开源了一个名为 [hardeneks](https://github.com/aws-samples/hardeneks) 的基于 Python 的 CLI (命令行界面)，用于检查本指南中的一些建议。

未来我们将发布有关性能、成本优化和运营卓越的最佳实践指南。

## 相关指南
除了 [EKS 用户指南](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html)之外，AWS 还发布了其他一些指南，可能会帮助您实施 EKS。

* [EMR Containers 最佳实践指南](https://aws.github.io/aws-emr-containers-best-practices/)
* [EKS 上的数据](https://awslabs.github.io/data-on-eks/)
* [AWS 可观测性最佳实践](https://aws-observability.github.io/observability-best-practices/)
* [Amazon EKS Blueprints for Terraform](https://aws-ia.github.io/terraform-aws-eks-blueprints/)
* [Amazon EKS Blueprints 快速入门](https://aws-quickstart.github.io/cdk-eks-blueprints/)

## 贡献
我们鼓励您为这些指南做出贡献。如果您已实施了一种被证明有效的实践，请通过提出问题或拉取请求与我们分享。同样，如果您发现我们已发布的指南中存在错误或缺陷，请提交 PR 加以纠正。提交 PR 的指南可以在我们的[贡献指南](https://github.com/aws/aws-eks-best-practices/blob/master/CONTRIBUTING.md)中找到。