# 簡介
歡迎來到 EKS 最佳實踐指南。這個專案的主要目標是為 Amazon EKS 的第二天運營提供一套最佳實踐。我們選擇將這份指南發佈到 GitHub 上,以便我們能夠快速迭代、為各種問題提供及時有效的建議,並輕鬆地納入更廣泛社區的建議。

我們目前已發佈以下主題的指南:

* [安全性最佳實踐](security/docs/)
* [可靠性最佳實踐](reliability/docs/)
* 集群自動擴展最佳實踐: [karpenter](karpenter/)、[cluster-autoscaler](cluster-autoscaling/)
* [運行 Windows 容器的最佳實踐](windows/docs/ami/)
* [網絡最佳實踐](networking/index/)
* [可擴展性最佳實踐](scalability/docs/)
* [集群升級最佳實踐](upgrades/)
* [成本優化最佳實踐](cost_optimization/cfm_framework.md)

我們還開源了一個基於 Python 的命令行界面 (CLI) 工具 [hardeneks](https://github.com/aws-samples/hardeneks),用於檢查本指南中的一些建議。

未來,我們將發佈有關性能、成本優化和運營卓越的最佳實踐指南。

## 相關指南
除了 [EKS 用戶指南](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html) 之外,AWS 還發佈了其他一些指南,可能會幫助您實施 EKS。

* [EMR Containers 最佳實踐指南](https://aws.github.io/aws-emr-containers-best-practices/)
* [EKS 上的數據](https://awslabs.github.io/data-on-eks/)
* [AWS 可觀測性最佳實踐](https://aws-observability.github.io/observability-best-practices/)
* [Amazon EKS Blueprints for Terraform](https://aws-ia.github.io/terraform-aws-eks-blueprints/)
* [Amazon EKS Blueprints 快速入門](https://aws-quickstart.github.io/cdk-eks-blueprints/)

## 貢獻
我們鼓勵您為這些指南做出貢獻。如果您已實施了一種被證明有效的實踐,請通過開啟 issue 或 pull request 與我們分享。同樣,如果您發現我們已發佈的指南中存在錯誤或缺陷,請提交 PR 加以糾正。提交 PR 的指南可以在我們的 [貢獻指南](https://github.com/aws/aws-eks-best-practices/blob/master/CONTRIBUTING.md) 中找到。