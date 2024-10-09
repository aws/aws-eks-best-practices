# Amazon EKS 可靠性最佳實踐指南

本節提供有關使 EKS 上運行的工作負載具有彈性和高可用性的指導。

## 如何使用本指南

本指南適用於希望在 EKS 中開發和運行高可用和容錯服務的開發人員和架構師。本指南按不同主題區域組織，以便於閱讀。每個主題都從簡要概述開始，然後列出了確保您的 EKS 集群可靠性的建議和最佳實踐。

## 簡介

EKS 的可靠性最佳實踐已分組為以下主題：

* 應用程序
* 控制平面
* 數據平面

---

什麼使系統可靠？如果一個系統在一段時間內能夠持續運行並滿足需求，儘管環境發生了變化，那麼它就可以被稱為可靠。為了實現這一點，系統必須能夠檢測故障、自動修復自身，並具有根據需求進行擴展的能力。

客戶可以使用 Kubernetes 作為運行關鍵任務應用程序和服務的可靠基礎。但除了採用基於容器的應用程序設計原則外，可靠地運行工作負載還需要可靠的基礎設施。在 Kubernetes 中，基礎設施包括控制平面和數據平面。

EKS 提供了一個經過生產級別設計的高可用和容錯的 Kubernetes 控制平面。

在 EKS 中，AWS 負責 Kubernetes 控制平面的可靠性。EKS 在 AWS 區域中的三個可用區域中運行 Kubernetes 控制平面。它自動管理 Kubernetes API 服務器和 etcd 集群的可用性和可擴展性。

數據平面可靠性的責任在您(客戶)和 AWS 之間共享。EKS 為 Kubernetes 數據平面提供了三個選項。Fargate 是最受管理的選項,負責數據平面的配置和擴展。第二個選項是受管節點組,負責數據平面的配置和更新。最後,自我管理節點是數據平面最不受管理的選項。您使用的 AWS 管理數據平面越多,您承擔的責任就越少。

[受管節點組](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) 自動化 EC2 節點的配置和生命週期管理。您可以使用 EKS API(通過 EKS 控制台、AWS API、AWS CLI、CloudFormation、Terraform 或 `eksctl`)來創建、擴展和升級受管節點。受管節點在您的帳戶中運行 EKS 優化的 Amazon Linux 2 EC2 實例,您可以通過啟用 SSH 訪問來安裝自定義軟件包。在您配置受管節點時,它們將作為 EKS 管理的 Auto Scaling 組的一部分運行,該組可以跨多個可用區域;您可以通過在創建受管節點時提供的子網來控制這一點。EKS 還會自動為受管節點添加標籤,以便與集群自動擴展器一起使用。

> Amazon EKS 遵循共享責任模型,負責受管節點組的 CVE 和安全修補程序。由於受管節點運行 Amazon EKS 優化的 AMI,因此 Amazon EKS 負責在有錯誤修復時構建這些 AMI 的修補版本。但是,您負責將這些修補的 AMI 版本部署到您的受管節點組。

EKS 還[管理節點的更新](https://docs.aws.amazon.com/eks/latest/userguide/update-managed-node-group.html),儘管您必須啟動更新過程。[更新受管節點](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-update-behavior.html)的過程在 EKS 文檔中有解釋。

如果您運行自我管理的節點,您可以使用 [Amazon EKS 優化的 Linux AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html) 來創建工作節點。您負責修補和升級 AMI 和節點。最佳做法是使用 `eksctl`、CloudFormation 或基礎設施作為代碼工具來配置自我管理的節點,因為這將使您更容易[升級自我管理的節點](https://docs.aws.amazon.com/eks/latest/userguide/update-workers.html)。在更新工作節點時,請考慮[遷移到新節點](https://docs.aws.amazon.com/eks/latest/userguide/migrate-stack.html),因為遷移過程會在新棧準備好接受現有 pod 工作負載後,將舊節點組 **標記為** `NoSchedule` 並 **排空** 節點。但是,您也可以對自我管理的節點執行[就地升級](https://docs.aws.amazon.com/eks/latest/userguide/update-stack.html)。

![共享責任模型 - Fargate](./images/SRM-Fargate.jpeg)

![共享責任模型 - MNG](./images/SRM-MNG.jpeg)

本指南包括一組建議,您可以使用這些建議來提高 EKS 數據平面、Kubernetes 核心組件和您的應用程序的可靠性。

## 反饋
本指南在 GitHub 上發佈,旨在從更廣泛的 EKS/Kubernetes 社區收集直接反饋和建議。如果您有任何您認為我們應該在指南中包含的最佳實踐,請在 GitHub 存儲庫中提出問題或提交 PR。我們打算在服務添加新功能或出現新的最佳實踐時,定期更新本指南。