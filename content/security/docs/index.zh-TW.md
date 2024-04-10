# Amazon EKS 安全最佳實踐指南

本指南提供了有關保護依賴於 EKS 的資訊、系統和資產的建議,同時透過風險評估和緩解策略提供商業價值。本指南中的指導是 AWS 發布的一系列最佳實踐指南的一部分,旨在幫助客戶按照最佳實踐實施 EKS。未來幾個月內,將提供有關性能、運營卓越、成本優化和可靠性的指南。

## 如何使用本指南

本指南適用於負責實施和監控 EKS 集群及其支持的工作負載的安全控制有效性的安全從業人員。本指南按主題區域組織,以便於閱讀。每個主題都從簡短的概述開始,然後列出了保護 EKS 集群的建議和最佳實踐。主題不需按特定順序閱讀。

## 了解共同責任模型

在使用 EKS 等受管理服務時,安全和合規被視為共同責任。一般而言,AWS 負責雲端的安全,而您作為客戶則負責雲端內部的安全。對於 EKS,AWS 負責管理 EKS 受管理的 Kubernetes 控制平面。這包括 Kubernetes 控制平面節點、ETCD 數據庫以及 AWS 提供安全可靠服務所需的其他基礎設施。作為 EKS 的消費者,您主要負責本指南中的主題,例如 IAM、Pod 安全性、運行時安全性、網絡安全性等。

在基礎設施安全方面,隨著您從自行管理的工作節點過渡到受管理的節點組,再到 Fargate,AWS 將承擔更多責任。例如,對於 Fargate,AWS 將負責保護用於運行您的 Pod 的基礎實例/運行時的安全。

![共同責任模型 - Fargate](images/SRM-EKS.jpg)

AWS 還將負責使用 Kubernetes 補丁版本和安全補丁來保持 EKS 優化的 AMI 保持最新狀態。使用受管理節點組 (MNG) 的客戶負責通過 EKS API、CLI、Cloudformation 或 AWS 控制台將其節點組升級到最新的 AMI。此外,與 Fargate 不同,MNG 不會自動擴展您的基礎設施/集群。這可以通過 [cluster-autoscaler](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md) 或其他技術(如 [Karpenter](https://karpenter.sh/)、原生 AWS 自動擴展、SpotInst 的 [Ocean](https://spot.io/solutions/kubernetes-2/) 或 Atlassian 的 [Escalator](https://github.com/atlassian/escalator)) 來處理。

![共同責任模型 - MNG](./images/SRM-MNG.jpg)

在設計系統之前,了解您的責任與服務提供商 (AWS) 的責任之間的分界線很重要。

有關共同責任模型的更多資訊,請參閱 [https://aws.amazon.com/compliance/shared-responsibility-model/](https://aws.amazon.com/compliance/shared-responsibility-model/)

## 簡介

在使用 EKS 等受管理的 Kubernetes 服務時,有幾個安全最佳實踐領域很重要:

- 身份和訪問管理
- Pod 安全性
- 運行時安全性
- 網絡安全性
- 多租戶
- 多賬戶用於多租戶
- 偵測控制
- 基礎設施安全性
- 數據加密和密鑰管理
- 法規遵從性
- 事件響應和取證
- 映像安全性

在設計任何系統時,您需要考慮其安全影響以及可能影響安全狀況的實踐。例如,您需要控制誰可以對一組資源執行操作。您還需要能夠快速識別安全事件,保護系統和服務免受未經授權的訪問,並通過數據保護來維護數據的機密性和完整性。擁有一套明確定義和經過演練的安全事件響應流程將提高您的安全狀況。這些工具和技術很重要,因為它們支持防止財務損失或遵守監管義務等目標。

AWS 通過提供一套豐富的安全服務來幫助組織實現其安全和合規目標,這些服務是根據來自廣泛安全意識客戶的反饋而不斷發展的。通過提供高度安全的基礎,客戶可以花費更少時間在"無差異化的重體力勞動"上,而將更多時間用於實現其業務目標。

## 反饋

本指南在 GitHub 上發布,目的是收集來自更廣泛的 EKS/Kubernetes 社區的直接反饋和建議。如果您有任何您認為我們應該在指南中包含的最佳實踐,請在 GitHub 存儲庫中提出問題或提交 PR。我們的目的是在服務添加新功能或出現新的最佳實踐時,定期更新指南。

## 進一步閱讀

[Kubernetes 安全白皮書](https://github.com/kubernetes/sig-security/blob/main/sig-security-external-audit/security-audit-2019/findings/Kubernetes%20White%20Paper.pdf)由安全審計工作組贊助,本白皮書描述了 Kubernetes 攻擊面和安全架構的關鍵方面,旨在幫助安全從業人員做出明智的設計和實施決策。

CNCF 還發布了一份 [白皮書](https://github.com/cncf/tag-security/blob/efb183dc4f19a1bf82f967586c9dfcb556d87534/security-whitepaper/v2/CNCF_cloud-native-security-whitepaper-May2022-v2.pdf) 關於雲原生安全。該白皮書檢查了技術環境如何演變,並倡導採用與 DevOps 流程和敏捷方法相一致的安全實踐。

## 工具和資源

[Amazon EKS 安全沉浸式工作坊](https://catalog.workshops.aws/eks-security-immersionday/en-US)
