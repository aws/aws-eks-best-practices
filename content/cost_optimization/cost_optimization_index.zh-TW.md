# Amazon EKS 成本優化最佳實踐指南

成本優化是以最低的價格點實現您的業務目標。通過遵循本指南中的文檔,您將優化您的 Amazon EKS 工作負載。

# 一般準則

在雲端中,有一些一般準則可以幫助您實現微服務的成本優化:
+ 確保在 Amazon EKS 上運行的工作負載與運行容器的特定基礎架構類型無關,這將為在最便宜的基礎架構類型上運行它們提供更大的靈活性。雖然使用 Amazon EKS 與 EC2 時,當我們有需要特定 EC2 實例類型的工作負載時,可能會有例外,例如 [需要 GPU](https://docs.aws.amazon.com/eks/latest/userguide/gpu-ami.html) 或其他實例類型,這是由於工作負載的性質所致。
+ 選擇最佳配置的容器實例 — 使用 [Amazon CloudWatch Container Insights for Amazon EKS](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/deploy-container-insights-EKS.html) 或 Kubernetes 生態系統中可用的第三方工具,檢視生產或預生產環境並監控關鍵指標,如 CPU 和內存。這將確保我們可以分配正確的資源量,避免資源浪費。
+ 利用 AWS 中可用於在 EC2 上運行 EKS 的不同採購選項,例如 On-Demand、Spot 和 Savings Plan。

# EKS 成本優化最佳實踐

雲端中成本優化的三個一般最佳實踐領域為:

+ 高效資源 (自動擴展、縮減、政策和採購選項)
+ 支出意識 (使用 AWS 和第三方工具)
+ 持續優化 (正確調整大小)

與任何指引一樣,都存在權衡取捨。請與您的組織合作,了解此工作負載的優先事項,以及哪些最佳實踐最為重要。

## 如何使用本指南

本指南旨在供負責實施和管理 EKS 集群及其支持的工作負載的 devops 團隊使用。本指南按不同的最佳實踐領域組織,以便於消化。每個主題都列出了建議、工具和優化 EKS 集群成本的最佳實踐。主題不需按特定順序閱讀。

### 關鍵 AWS 服務和 Kubernetes 功能
成本優化由以下 AWS 服務和功能支持:
+ 具有不同價格的 EC2 實例類型、Savings Plan (和 Reserved Instances) 和 Spot Instances。
+ 自動擴展以及 Kubernetes 原生自動擴展政策。對於可預測的工作負載,請考慮 Savings Plan (以前的 Reserved Instances)。使用托管數據存儲,如 EBS 和 EFS,以實現應用程序數據的彈性和持久性。
+ Billing and Cost Management 控制台儀表板以及 AWS Cost Explorer 提供了您的 AWS 使用情況概覽。使用 AWS Organizations 獲取詳細的計費詳情。還分享了多個第三方工具的詳細信息。
+ Amazon CloudWatch Container Metrics 提供了有關 EKS 集群資源使用情況的指標。除了 Kubernetes 儀表板外,Kubernetes 生態系統中還有多個可用於減少浪費的工具。

本指南包括一組建議,您可以使用這些建議來改善您的 Amazon EKS 集群的成本優化。

## 反饋
本指南在 GitHub 上發佈,以便從更廣泛的 EKS/Kubernetes 社區收集直接反饋和建議。如果您有任何認為應該包含在本指南中的最佳實踐,請在 GitHub 存儲庫中提出問題或提交 PR。我們的目的是在服務添加新功能或出現新的最佳實踐時,定期更新本指南。