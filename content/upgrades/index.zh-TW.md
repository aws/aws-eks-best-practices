# 叢集升級的最佳實踐

本指南向叢集管理員展示如何規劃和執行其 Amazon EKS 升級策略。它還描述了如何升級自行管理的節點、受管理的節點群組、Karpenter 節點和 Fargate 節點。它不包括有關 EKS Anywhere、自行管理的 Kubernetes、AWS Outposts 或 AWS Local Zones 的指導。

## 概述

Kubernetes 版本包括控制平面和數據平面。為確保順利運行,控制平面和數據平面應運行相同的 [Kubernetes 次要版本,例如 1.24](https://kubernetes.io/releases/version-skew-policy/#supported-versions)。雖然 AWS 管理和升級控制平面,但更新數據平面中的工作節點是您的責任。

* **控制平面** — 控制平面的版本由 Kubernetes API 服務器確定。在 Amazon EKS 叢集中,AWS 負責管理此組件。可通過 AWS API 發起控制平面升級。
* **數據平面** — 數據平面版本與運行在各個節點上的 Kubelet 版本相關聯。同一個叢集中的節點可能運行不同的版本。您可以通過運行 `kubectl get nodes` 來檢查所有節點的版本。

## 升級前

如果您計劃在 Amazon EKS 中升級 Kubernetes 版本,在開始升級之前,有一些重要的政策、工具和程序您應該落實。

* **了解棄用政策** — 深入了解 [Kubernetes 棄用政策](https://kubernetes.io/docs/reference/using-api/deprecation-policy/)的工作原理。注意任何可能影響您現有應用程序的即將發生的變化。Kubernetes 的新版本通常會逐步淘汰某些 API 和功能,可能會導致正在運行的應用程序出現問題。
* **查看 Kubernetes 變更日誌** — 徹底查看 [Kubernetes 變更日誌](https://github.com/kubernetes/kubernetes/tree/master/CHANGELOG)以及 [Amazon EKS Kubernetes 版本](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html),以了解可能對您的叢集產生影響的任何內容,例如可能影響您的工作負載的重大變更。
* **評估叢集附加組件的兼容性** — 當發布新版本或在您將叢集升級到新的 Kubernetes 次要版本後,Amazon EKS 不會自動更新附加組件。查看 [更新附加組件](https://docs.aws.amazon.com/eks/latest/userguide/managing-add-ons.html#updating-an-add-on),以了解任何現有叢集附加組件與您打算升級到的叢集版本的兼容性。
* **啟用控制平面日誌記錄** — 啟用 [控制平面日誌記錄](https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html),以捕獲升級過程中可能出現的日誌、錯誤或問題。考慮查看這些日誌以檢查是否有任何異常。在非生產環境中測試叢集升級,或將自動化測試集成到您的持續集成工作流中,以評估版本與您的應用程序、控制器和自定義集成的兼容性。
* **探索 eksctl 進行叢集管理** — 考慮使用 [eksctl](https://eksctl.io/) 來管理您的 EKS 叢集。它為您提供了 [更新控制平面、管理附加組件和處理工作節點更新](https://eksctl.io/usage/cluster-upgrade/) 的功能。
* **選擇受管理的節點群組或 EKS on Fargate** — 通過使用 [EKS 受管理的節點群組](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) 或 [EKS on Fargate](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html),簡化並自動化工作節點升級。這些選項簡化了流程並減少了手動干預。
* **利用 kubectl Convert 插件** — 利用 [kubectl convert 插件](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/#install-kubectl-convert-plugin)來促進 [Kubernetes 清單文件在不同 API 版本之間的轉換](https://kubernetes.io/docs/tasks/tools/included/kubectl-convert-overview/)。這可以幫助確保您的配置與新的 Kubernetes 版本保持兼容。

## 保持您的叢集最新

保持與 Kubernetes 更新同步是維護安全高效的 EKS 環境的關鍵,這反映了 Amazon EKS 中的共同責任模型。通過將這些策略集成到您的操作工作流中,您可以確保維護最新、安全的叢集,從而充分利用最新的功能和改進。策略:

* **支持版本政策** — 與 Kubernetes 社區保持一致,Amazon EKS 通常提供三個活躍的 Kubernetes 版本,同時每年淘汰第四個版本。在版本達到其支持終止日期前至少 60 天會發出棄用通知。有關更多詳細信息,請參閱 [EKS 版本常見問題解答](https://aws.amazon.com/eks/eks-version-faq/)。
* **自動升級政策** — 我們強烈建議您在 EKS 叢集中與 Kubernetes 更新保持同步。Kubernetes 社區支持(包括錯誤修復和安全補丁)通常會在版本超過一年後終止。棄用版本也可能缺乏漏洞報告,存在潛在風險。如果未主動在版本生命週期結束前進行升級,將會觸發自動升級,這可能會中斷您的工作負載和系統。有關更多信息,請查閱 [EKS 版本支持政策](https://aws.amazon.com/eks/eks-version-support-policy/)。
* **創建升級運行手冊** — 建立管理升級的明確流程。作為主動方法的一部分,開發適合您升級流程的運行手冊和專門工具。這不僅提高了您的準備程度,而且還簡化了複雜的過渡。將至少每年升級一次叢集作為標準做法。這種做法使您與不斷推進的技術進步保持一致,從而提高了環境的效率和安全性。

## 查看 EKS 發佈日曆

[查看 EKS Kubernetes 發佈日曆](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-release-calendar),了解新版本的發佈時間以及特定版本的支持終止時間。通常,EKS 每年發佈三個 Kubernetes 次要版本,每個次要版本的支持期約為 14 個月。

此外,請查看上游 [Kubernetes 發佈信息](https://kubernetes.io/releases/)。

## 了解共同責任模型如何應用於叢集升級

您負責發起對控制平面和數據平面的升級。[了解如何發起升級。](https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html) 當您發起叢集升級時,AWS 負責升級叢集控制平面。您負責升級數據平面,包括 Fargate pod 和 [其他附加組件。](#upgrade-add-ons-and-components-using-the-kubernetes-api) 您必須驗證並規劃在您的叢集上運行的工作負載的升級,以確保在叢集升級後它們的可用性和操作不受影響

## 就地升級叢集

EKS 支持就地叢集升級策略。這樣可以保留叢集資源,並保持叢集配置一致(例如,API 端點、OIDC、ENI、負載均衡器)。這對叢集用戶的干擾較小,並且它將使用叢集中現有的工作負載和資源,無需您重新部署工作負載或遷移外部資源(例如,DNS、存儲)。

在執行就地叢集升級時,請注意一次只能執行一個次要版本升級(例如,從 1.24 到 1.25)。

這意味著如果您需要更新多個版本,則需要進行一系列連續升級。規劃連續升級更加複雜,並且存在較高的停機風險。在這種情況下,[評估藍/綠叢集升級策略作為就地叢集升級的替代方案。](#evaluate-bluegreen-clusters-as-an-alternative-to-in-place-cluster-upgrades)

## 按順序升級控制平面和數據平面

要升級叢集,您需要執行以下操作:

1. [查看 Kubernetes 和 EKS 發行說明。](#use-the-eks-documentation-to-create-an-upgrade-checklist)
2. [備份叢集。(可選)](#backup-the-cluster-before-upgrading)
3. [識別並修復工作負載中已移除的 API 使用情況。](#identify-and-remediate-removed-api-usage-before-upgrading-the-control-plane)
4. [確保使用的受管理節點群組(如果有)與控制平面運行相同的 Kubernetes 版本。](#track-the-version-skew-of-nodes-ensure-managed-node-groups-are-on-the-same-version-as-the-control-plane-before-upgrading) EKS 受管理節點群組和由 EKS Fargate 配置文件創建的節點僅支持控制平面和數據平面之間的 1 個次要版本偏差。
5. [使用 AWS 控制台或 cli 升級叢集控制平面。](https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html)
6. [查看附加組件兼容性。](#upgrade-add-ons-and-components-using-the-kubernetes-api) 根據需要升級您的 Kubernetes 附加組件和自定義控制器。
7. [更新 kubectl。](https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html)
8. [升級叢集數據平面。](https://docs.aws.amazon.com/eks/latest/userguide/update-managed-node-group.html) 將您的節點升級到與升級後的叢集相同的 Kubernetes 次要版本。

## 使用 EKS 文檔創建升級清單

EKS Kubernetes [版本文檔](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html)包括每個版本的詳細變更列表。為每次升級建立清單。

有關特定 EKS 版本升級指南,請查看文檔中有關每個版本的值得注意的變更和注意事項。

* [EKS 1.27](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-1.27)
* [EKS 1.26](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-1.26)
* [EKS 1.25](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-1.25)
* [EKS 1.24](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-1.24)
* [EKS 1.23](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-1.23)
* [EKS 1.22](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html#kubernetes-1.22)

## 使用 Kubernetes API 升級附加組件和組件

在升級叢集之前,您應該了解您正在使用哪些版本的 Kubernetes 組件。列出叢集組件,並識別直接使用 Kubernetes API 的組件。這包括關鍵叢集組件,例如監控和日誌記錄代理、叢集自動擴展器、容器存儲驅動程序(例如 [EBS CSI](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html)、[EFS CSI](https://docs.aws.amazon.com/eks/latest/userguide/efs-csi.html))、入口控制器以及任何其他依賴 Kubernetes API 的工作負載或附加組件。

!!! 提示
    關鍵叢集組件通常安裝在 `*-system` 命名空間中
    
    ```
    kubectl get ns | grep '-system'
    ```

一旦您識別出依賴 Kubernetes API 的組件,請查看其文檔以了解版本兼容性和升級要求。例如,請參閱 [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/deploy/installation/) 文檔以了解版本兼容性。在繼續進行叢集升級之前,可能需要升級或更改某些組件的配置。需要檢查的一些關鍵組件包括 [CoreDNS](https://github.com/coredns/coredns)、[kube-proxy](https://kubernetes.io/docs/concepts/overview/components/#kube-proxy)、[VPC CNI](https://github.com/aws/amazon-vpc-cni-k8s) 和存儲驅動程序。

叢集中通常包含許多使用 Kubernetes API 並且對工作負載功能至關重要的工作負載,例如入口控制器、持續交付系統和監控工具。升級 EKS 叢集時,您還必須升級您的附加組件和第三方工具,以確保它們與新版本兼容。
 
請參閱以下常見附加組件及其相關升級文檔的示例:

* **Amazon VPC CNI:** 有關每個叢集版本的建議 Amazon VPC CNI 附加組件版本,請參閱 [更新 Kubernetes 自行管理附加組件的 Amazon VPC CNI 插件](https://docs.aws.amazon.com/eks/latest/userguide/managing-vpc-cni.html)。**當作為 Amazon EKS 附加組件安裝時,它只能一次升級一個次要版本。**
* **kube-proxy:** 請參閱 [更新 Kubernetes kube-proxy 自行管理附加組件](https://docs.aws.amazon.com/eks/latest/userguide/managing-kube-proxy.html)。
* **CoreDNS:** 請參閱 [更新 CoreDNS 自行管理附加組件](https://docs.aws.amazon.com/eks/latest/userguide/managing-coredns.html)。
* **AWS Load Balancer Controller:** AWS Load Balancer Controller 需要與您部署的 EKS 版本兼容。有關更多信息,請參閱 [安裝指南](https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html)。
* **Amazon Elastic Block Store (Amazon EBS) 容器存儲接口 (CSI) 驅動程序:** 有關安裝和升級信息,請參閱 [管理作為 Amazon EKS 附加組件的 Amazon EBS CSI 驅動程序](https://docs.aws.amazon.com/eks/latest/userguide/managing-ebs-csi.html)。
* **Amazon Elastic File System (Amazon EFS) 容器存儲接口 (CSI) 驅動程序:** 有關安裝和升級信息,請參閱 [Amazon EFS CSI 驅動程序](https://docs.aws.amazon.com/eks/latest/userguide/efs-csi.html)。
* **Kubernetes Metrics Server:** 有關更多信息,請參閱 GitHub 上的 [metrics-server](https://kubernetes-sigs.github.io/metrics-server/)。
* **Kubernetes Cluster Autoscaler****:** 要升級 Kubernetes Cluster Autoscaler 的版本,請更改部署中的映像版本。Cluster Autoscaler 與 Kubernetes 調度程序緊密耦合。升級叢集時,您將始終需要升級它。查看 [GitHub 發行版](https://github.com/kubernetes/autoscaler/releases),以找到與您的 Kubernetes 次要版本對應的最新發行版地址。
* **Karpenter:** 有關安裝和升級信息,請參閱 [Karpenter 文檔。](https://karpenter.sh/docs/upgrading/)

## 在升級前驗證基本 EKS 要求

AWS 要求您的帳戶中存在某些資源,以完成升級過程。如果這些資源不存在,則無法升級叢集。控制平面升級需要以下資源:

1. 可用 IP 地址: Amazon EKS 需要您在創建叢集時指定的子網中最多有 5 個可用 IP 地址,以便更新叢集。如果沒有,請在執行版本更新之前更新您的叢集配置,以包括新的叢集子網。
2. EKS IAM 角色: 控制平面 IAM 角色仍存在於帳戶中,並具有必要的權限。
3. 如果您的叢集啟用了密鑰加密,則請確保叢集 IAM 角色具有使用 AWS Key Management Service (AWS KMS) 密鑰的權限。

### 驗證可用 IP 地址

要更新叢集,Amazon EKS 需要您在創建叢集時指定的子網中最多有 5 個可用 IP 地址。

要驗證您的子網是否有足夠的 IP 地址來升級叢集,您可以運行以下命令:

```
CLUSTER=<cluster name>
aws ec2 describe-subnets --subnet-ids \
  $(aws eks describe-cluster --name ${CLUSTER} \
  --query 'cluster.resourcesVpcConfig.subnetIds' \
  --output text) \
  --query 'Subnets[*].[SubnetId,AvailabilityZone,AvailableIpAddressCount]' \
  --output table

----------------------------------------------------
|                  DescribeSubnets                 |
+---------------------------+--------------+-------+
|  subnet-067fa8ee8476abbd6 |  us-east-1a  |  8184 |
|  subnet-0056f7403b17d2b43 |  us-east-1b  |  8153 |
|  subnet-09586f8fb3addbc8c |  us-east-1a  |  8120 |
|  subnet-047f3d276a22c6bce |  us-east-1b  |  8184 |
+---------------------------+--------------+-------+
```

[VPC CNI Metrics Helper](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/cmd/cni-metrics-helper/README.md) 可用於為 VPC 指標創建 CloudWatch 控制面板。
如果您在最初創建叢集時指定的子網中的 IP 地址用完,Amazon EKS 建議在開始 Kubernetes 版本升級之前使用 "UpdateClusterConfiguration" API 更新叢集子網。請驗證您將提供的新子網:

* 屬於在叢集創建期間選擇的相同可用區域集。
* 屬於在叢集創建期間提供的相同 VPC

如果現有 VPC CIDR 塊中的 IP 地址用完,請考慮關聯其他 CIDR 塊。AWS 允許將其他 CIDR 塊與您現有的叢集 VPC 關聯,從而有效擴展您的 IP 地址池。可以通過引入其他私有 IP 範圍 (RFC 1918) 或(如有必要)公共 IP 範圍 (非 RFC 1918) 來實現此擴展。您必須添加新的 VPC CIDR 塊並允許 VPC 刷新完成,然後 Amazon EKS 才能使用新的 CIDR。之後,您可以根據新設置的 CIDR 塊更新子網到 VPC。


### 驗證 EKS IAM 角色

要驗證 IAM 角色在您的帳戶中可用並具有正確的 assume role 策略,您可以運行以下命令:

```
CLUSTER=<cluster name>
ROLE_ARN=$(aws eks describe-cluster --name ${CLUSTER} \
  --query 'cluster.roleArn' --output text)
aws iam get-role --role-name ${ROLE_ARN##*/} \
  --query 'Role.AssumeRolePolicyDocument'
  
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "eks.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

## 遷移到 EKS 附加組件

Amazon EKS 會自動為每個叢集安裝附加組件,例如 Kubernetes 的 Amazon VPC CNI 插件、`kube-proxy` 和 CoreDNS。附加組件可以是自行管理的,也可以作為 Amazon EKS 附加組件安裝。Amazon EKS 附加組件是使用 EKS API 管理附加組件的另一種方式。

您可以使用 Amazon EKS 附加組件通過單個命令更新版本。例如:

```
aws eks update-addon —cluster-name my-cluster —addon-name vpc-cni —addon-version version-number \
--service-account-role-arn arn:aws:iam::111122223333:role/role-name —configuration-values '{}' —resolve-conflicts PRESERVE
```

使用以下命令檢查是否有任何 EKS 附加組件:

```
aws eks list-addons --cluster-name <cluster name>
```

!!! 警告
      
    在控制平面升級期間,EKS 附加組件不會自動升級。您必須發起 EKS 附加組件更新,並選擇所需的版本。

    * 您負責從所有可用版本中選擇兼容版本。[查看有關附加組件版本兼容性的指導。](#upgrade-add-ons-and-components-using-the-kubernetes-api)
    * Amazon EKS 附加組件只能一次升級一個次要版本。

[了解有關哪些組件可作為 EKS 附加組件以及如何入門的更多信息。](https://docs.aws.amazon.com/eks/latest/userguide/eks-add-ons.html)

[了解如何為 EKS 附加組件提供自定義配置。](https://aws.amazon.com/blogs/containers/amazon-eks-add-ons-advanced-configuration/)

## 在升級控制平面之前識別並修復已移除的 API 使用情況

您應該在升級 EKS 控制平面之前識別已移除 API 的使用情況。為此,我們建議使用可以檢查正在運行的叢集或靜態渲染的 Kubernetes 清單文件的工具。

對靜態清單文件進行掃描通常更加準確。如果對實時叢集進行掃描,這些工具可能會返回誤報。

Kubernetes 已棄用的 API 並不意味著該 API 已被移除。您應該查看 [Kubernetes 棄用政策](https://kubernetes.io/docs/reference/using-api/deprecation-policy/),以了解 API 移除對您的工作負載的影響。

### Cluster Insights
[Cluster Insights](https://docs.aws.amazon.com/eks/latest/userguide/cluster-insights.html) 是一項功能,可提供有關可能影響升級 EKS 叢集到更新版本的 Kubernetes 的問題的發現。這些發現由 Amazon EKS 策劃和管理,並提供了如何修復它們的建議。通過利用 Cluster Insights,您可以最小化升級到更新的 Kubernetes 版本所需的工作量。

要查看 EKS 叢集的見解,您可以運行命令:
```
aws eks list-insights --region <region-code> --cluster-name <my-cluster>

{
    "insights": [
        {
            "category": "UPGRADE_READINESS", 
            "name": "Deprecated APIs removed in Kubernetes v1.29", 
            "insightStatus": {
                "status": "PASSING", 
                "reason": "No deprecated API usage detected within the last 30 days."
            }, 
            "kubernetesVersion": "1.29", 
            "lastTransitionTime": 1698774710.0, 
            "lastRefreshTime": 1700157422.0, 
            "id": "123e4567-e89b-42d3-a456-579642341238", 
            "description": "Checks for usage of deprecated APIs that are scheduled for removal in Kubernetes v1.29. Upgrading your cluster before migrating to the updated APIs supported by v1.29 could cause application impact."
        }
    ]
}
```

要獲得有關收到的見解的更詳細輸出,您可以運行命令:
```
aws eks describe-insight --region <region-code> --id <insight-id> --cluster-name <my-cluster>
```

您也可以在 [Amazon EKS 控制台](https://console.aws.amazon.com/eks/home#/clusters)中查看見解。在從叢集列表中選擇您的叢集後,見解發現位於 ```Upgrade Insights``` 選項卡下。

如果您發現叢集見解的 `"status": ERROR`,則必須在執行叢集升級之前解決該問題。運行 `aws eks describe-insight` 命令,它將分享以下修復建議:

受影響的資源:
```
"resources": [
      {
        "insightStatus": {
          "status": "ERROR"
        },
        "kubernetesResourceUri": "/apis/policy/v1beta1/podsecuritypolicies/null"
      }
]
```

已棄用的 API:
```
"deprecationDetails": [
      {
        "usage": "/apis/flowcontrol.apiserver.k8s.io/v1beta2/flowschemas", 
        "replacedWith": "/apis/flowcontrol.apiserver.k8s.io/v1beta3/flowschemas", 
        "stopServingVersion": "1.29", 
        "clientStats": [], 
        "startServingReplacementVersion": "1.26"
      }
]
```

建議採取的行動:
```
"recommendation": "Update manifests and API clients to use newer Kubernetes APIs if applicable before upgrading to Kubernetes v1.26."
```

通過 EKS 控制台或 CLI 利用叢集見解,可加快成功升級 EKS 叢集版本的過程。了解更多資訊:
* [官方 EKS 文檔](https://docs.aws.amazon.com/eks/latest/userguide/cluster-insights.html)
* [Cluster Insights 發佈博客](https://aws.amazon.com/blogs/containers/accelerate-the-testing-and-verification-of-amazon-eks-upgrades-with-upgrade-insights/)。

### Kube-no-trouble

[Kube-no-trouble](https://github.com/doitintl/kube-no-trouble) 是一個開源命令行工具,具有 `kubent` 命令。當您在不帶任何參數的情況下運行 `kubent` 時,它將使用您當前的 KubeConfig 上下文並掃描叢集,然後打印一份報告,其中包含哪些 API 將被棄用和移除。

```
kubent

4:17PM INF >>> Kube No Trouble `kubent` <<<
4:17PM INF version 0.7.0 (git sha d1bb4e5fd6550b533b2013671aa8419d923ee042)
4:17PM INF Initializing collectors and retrieving data
4:17PM INF Target K8s version is 1.24.8-eks-ffeb93d
4:l INF Retrieved 93 resources from collector name=Cluster
4:17PM INF Retrieved 16 resources from collector name="Helm v3"
4:17PM INF Loaded ruleset name=custom.rego.tmpl
4:17PM INF Loaded ruleset name=deprecated-1-16.rego
4:17PM INF Loaded ruleset name=deprecated-1-22.rego
4:17PM INF Loaded ruleset name=deprecated-1-25.rego
4:17PM INF Loaded ruleset name=deprecated-1-26.rego
4:17PM INF Loaded ruleset name=deprecated-future.rego
__________________________________________________________________________________________
>>> Deprecated APIs removed in 1.25 <<<
------------------------------------------------------------------------------------------
KIND                NAMESPACE     NAME             API_VERSION      REPLACE_WITH (SINCE)
PodSecurityPolicy   <undefined>   eks.privileged   policy/v1beta1   <removed> (1.21.0)
```

它還可以用於掃描靜態清單文件和 helm 包。建議將 `kubent` 作為持續集成 (CI) 過程的一部分運行,以在部署清單之前識別問題。對清單進行掃描也更加準確。

Kube-no-trouble 提供了一個示例 [服務帳戶和角色](https://github.com/doitintl/kube-no-trouble/blob/master/docs/k8s-sa-and-role-example.yaml),具有掃描叢集的適當權限。

### Pluto

另一個選擇是 [pluto](https://pluto.docs.fairwinds.com/),它類似於 `kubent`,因為它支持掃描實時叢集、清單文件、helm 圖表,並且您可以在 CI 過程中包含一個 GitHub Action。

```
pluto detect-all-in-cluster

NAME             KIND                VERSION          REPLACEMENT   REMOVED   DEPRECATED   REPL AVAIL  
eks.privileged   PodSecurityPolicy   policy/v1beta1                 false     true         true
```

### 資源

要在升級控制平面之前驗證您的叢集不使用已棄用的 API,您應該監控:

* 自 Kubernetes v1.19 起的指標 `apiserver_requested_deprecated_apis`:

```
kubectl get --raw /metrics | grep apiserver_requested_deprecated_apis

apiserver_requested_deprecated_apis{group="policy",removed_release="1.25",resource="podsecuritypolicies",subresource="",version="v1beta1"} 1
```

* [審計日誌](https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html)中 `k8s.io/deprecated` 設置為 `true` 的事件:

```
CLUSTER="<cluster_name>"
QUERY_ID=$(aws logs start-query \
 --log-group-name /aws/eks/${CLUSTER}/cluster \
 --start-time $(date -u --date="-30 minutes" "+%s") # or date -v-30M "+%s" on MacOS \
 --end-time $(date "+%s") \
 --query-string 'fields @message | filter `annotations.k8s.io/deprecated`="true"' \
 --query queryId --output text)

echo "Query started (query id: $QUERY_ID), please hold ..." && sleep 5 # give it some time to query

aws logs get-query-results --query-id $QUERY_ID
```

如果使用了已棄用的 API,它將輸出行:

```
{
    "results": [
        [
            {
                "field": "@message",
                "value": "{\"kind\":\"Event\",\"apiVersion\":\"audit.k8s.io/v1\",\"level\":\"Request\",\"auditID\":\"8f7883c6-b3d5-42d7-967a-1121c6f22f01\",\"stage\":\"ResponseComplete\",\"requestURI\":\"/apis/policy/v1beta1/podsecuritypolicies?allowWatchBookmarks=true\\u0026resourceVersion=4131\\u0026timeout=9m19s\\u0026timeoutSeconds=559\\u0026watch=true\",\"verb\":\"watch\",\"user\":{\"username\":\"system:apiserver\",\"uid\":\"8aabfade-da52-47da-83b4-46b16cab30fa\",\"groups\":[\"system:masters\"]},\"sourceIPs\":[\"::1\"],\"userAgent\":\"kube-apiserver/v1.24.16 (linux/amd64) kubernetes/af930c1\",\"objectRef\":{\"resource\":\"podsecuritypolicies\",\"apiGroup\":\"policy\",\"apiVersion\":\"v1beta1\"},\"responseStatus\":{\"metadata\":{},\"code\":200},\"requestReceivedTimestamp\":\"2023-10-04T12:36:11.849075Z\",\"stageTimestamp\":\"2023-10-04T12:45:30.850483Z\",\"annotations\":{\"authorization.k8s.io/decision\":\"allow\",\"authorization.k8s.io/reason\":\"\",\"k8s.io/deprecated\":\"true\",\"k8s.io/removed-release\":\"1.25\"}}"
            },
[...]
```

## 使用 kubectl-convert 更新 Kubernetes 工作負載。更新清單

在您確定需要更新哪些工作負載和清單後,您可能需要在清單文件中更改資源類型(例如,從 PodSecurityPolicies 更改為 PodSecurityStandards)。這將需要更新資源規範並進行其他研究,具體取決於要替換的資源。

如果資源類型保持不變但需要更新 API 版本,您可以使用 `kubectl-convert` 命令自動轉換您的清單文件。例如,將較舊的 Deployment 轉換為 `apps/v1`。有關更多信息,請參閱 Kubernetes 網站上的 [安裝 kubectl convert 插件](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/#install-kubectl-convert-plugin)。

`kubectl-convert -f <file> --output-version <group>/<version>`

## 配置 PodDisruptionBudgets 和 topologySpreadConstraints 以確保在升級數據平面時工作負載的可用性

確保您的工作負載具有適當的 [PodDisruptionBudgets](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/#pod-disruption-budgets) 和 [topologySpreadConstraints](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-spread-constraints),以確保在升級數據平面時工作負載的可用性。並非每個工作負載都需要相同級別的可用性,因此您需要驗證工作負載的規模和要求。

確保工作負載分散在多個可用區域和多個主機上,並使用拓撲傳播將為工作負載自動無縫遷移到新的數據平面提供更高的信心。

以下是一個工作負載的示例,它將始終有 80% 的副本可用,並且副本分散在區域和主機之間

```
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: myapp
spec:
  minAvailable: "80%"
  selector:
    matchLabels:
      app: myapp
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 10
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - image: public.ecr.aws/eks-distro/kubernetes/pause:3.2
        name: myapp
        resources:
          requests:
            cpu: "1"
            memory: 256M
      topologySpreadConstraints:
      - labelSelector:
          matchLabels:
            app: host-zone-spread
        maxSkew: 2
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: DoNotSchedule
      - labelSelector:
          matchLabels:
            app: host-zone-spread
        maxSkew: 2
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
```

[AWS Resilience Hub](https://aws.amazon.com/resilience-hub/) 已將 Amazon Elastic Kubernetes Service (Amazon EKS) 列為支持的資源。Resilience Hub 提供了一個單一位置,用於定義、驗證和跟踪您的應用程序的彈性,以便您可以避免由於軟件、基礎設施或操作中斷而導致的不必要的停機時間。

## 使用受管理的節點群組或 Karpenter 簡化數據平面升級

受管理的節點群組和 Karpenter 都可以簡化節點升級,但它們採用了不同的方法。

受管理的節點群組自動化節點的配置和生命週期管理。這意味著您可以通過單個操作創建、自動更新或終止節點。

在默認配置中,Karpenter 使用最新的兼容 EKS 優化 AMI 自動創建新節點。當 EKS 發佈更新的 EKS 優化 AMI 或升級叢集時,Karpenter 將自動開始使用這些映像。[Karpenter 還實現了節點過期來更新節點。](#enable-node-expiry-for-karpenter-managed-nodes)

[Karpenter 可以配置為使用自定義 AMI。](https://karpenter.sh/docs/concepts/nodeclasses/) 如果您在 Karpenter 中使用自定義 AMI,則需要負責 kubelet 的版本。

## 確認現有節點與控制平面的版本兼容性

在 Amazon EKS 中繼續進行 Kubernetes 升級之前,確保您的受管理節點群組、自行管理節點與控制平面之間的兼容性至關重要。兼容性取決於您使用的 Kubernetes 版本,並且因不同情況而有所不同。策略:

* **Kubernetes v1.28+** — **** 從 Kubernetes 版本 1.28 開始,核心組件的版本策略更加寬鬆。具體而言,Kubernetes API 服務器與 kubelet 之間支持的版本偏差已從 n-2 延長到 n-3。例如,如果您的 EKS 控制平面版本是 1.28,您可以安全地使用 1.25 及更高版本的 kubelet。這種版本偏差在 [AWS Fargate](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html)、[受管理節點群組](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) 和 [自行管理節點](https://docs.aws.amazon.com/eks/latest/userguide/worker.html) 中都受支持。出於安全原因,我們強烈建議保持 [Amazon Machine Image (AMI)](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-amis.html) 版本最新。較舊的 kubelet 版本可能存在潛在的常見漏洞和風險 (CVE),這可能會超過使用較舊 kubelet 版本的好處。
* **Kubernetes < v1.28** — 如果您使用的是 v1.28 之前的版本,API 服務器與 kubelet 之間支持的版本偏差為 n-2。例如,如果您的 EKS 版本是 1.27,您可以使用的最舊 kubelet 版本是 1.25。這種版本偏差適用於 [AWS Fargate](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html)、[受管理節點群組](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) 和 [自行管理節點](https://docs.aws.amazon.com/eks/latest/userguide/worker.html)。

## 為 Karpenter 管理的節點啟用節點過期

Karpenter 實現節點升級的一種方式是使用節點過期的概念。這減少了節點升級所需的規劃。當您為 provisioner 設置 **ttlSecondsUntilExpired** 值時,這將激活節點過期。在節點達到定義的秒數年齡後,它們將被安全地耗盡並刪除。即使它們正在使用,也是如此,從而允許您使用新供應的升級實例替換節點。當節點被替換時,Karpenter 將使用最新的 EKS 優化 AMI。有關更多信息,請參閱 Karpenter 網站上的 [去供應](https://karpenter.sh/docs/concepts/deprovisioning/#methods)。

Karpenter 不會自動為此值添加抖動。為防止過多的工作負載中斷,請定義 [pod 中斷預算](https://kubernetes.io/docs/tasks/run-application/configure-pdb/),如 Kubernetes 文檔所示。

如果您在 provisioner 上配置了 **ttlSecondsUntilExpired**,則它將應用於與該 provisioner 關聯的現有節點。

## 對於 Karpenter 管理的節點使用 Drift 功能

[Karpenter 的 Drift 功能](https://karpenter.sh/docs/concepts/deprovisioning/#drift)可以自動將 Karpenter 供應的節點升級到與 EKS 控制平面保持同步。目前需要使用 [功能門](https://karpenter.sh/docs/concepts/settings/#feature-gates) 啟用 Karpenter Drift。Karpenter 的默認配置使用與 EKS 叢集控制平面相同的主要和次要版本的最新 EKS 優化 AMI。

EKS 叢集升級完成後,Karpenter 的 Drift 功能將檢測到 Karpenter 供應的節點正在使用上一個叢集版本的 EKS 優化 AMI,並自動封鎖、耗盡和替換這些節點。為支持 pod 移動到新節點,請遵循 Kubernetes 最佳實踐,設置適當的 pod [資源配額](https://kubernetes.io/docs/concepts/policy/resource-quotas/)並使用 [pod 中斷預算](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/) (PDB)。Karpenter 的去供應將基於 pod 資源請求預先啟動替換節點,並在去供應節點時將遵守 PDB。

## 使用 eksctl 自動升級自行管理的節點群組

自行管理的節點群組是在您的帳戶中部署並連接到叢集之外的 EC2 實例。這些通常由某種形式的自動化工具部署和管理。要升級自行管理的節點群組,您應參考您的工具文檔。

例如,eksctl 支持 [刪除和耗盡自行管理的節點。](https://eksctl.io/usage/managing-nodegroups/#deleting-and-draining)

一些常見工具包括:

* [eksctl](https://eksctl.io/usage/nodegroup-upgrade/)
* [kOps](https://kops.sigs.k8s.io/operations/updates_and_upgrades/)
* [EKS Blueprints](https://aws-ia.github.io/terraform-aws-eks-blueprints/node-groups/#self-managed-node-groups)

## 在升級之前備份叢集

Kubernetes 的新版本為您的 Amazon EKS 叢集引入了重大變更。升級叢集後,您無法降級。

[Velero](https://velero.io/) 是一個社區支持的開源工具,可用於備份現有叢集並將備份應用到新叢集。

請注意,您只能為 EKS 當前支持的 Kubernetes 版本創建新叢集。如果您當前運行的叢集版本仍受支持且升級失敗,您可以使用原始版本創建新叢集並恢復數據平面。請注意,Velero 備份中不包括 AWS 資源(包括 IAM)。這些資源需要重新創建。

## 在升級控制平面後重新啟動 Fargate 部署

要升級 Fargate 數據平面節點,您需要重新部署工作負載。您可以通過使用 `-o wide` 選項列出所有 pod 來識別在 fargate 節點上運行的工作負載。任何以 `fargate-` 開頭的節點名稱都需要在叢集中重新部署。


## 評估藍/綠叢集作為就地叢集升級的替代方案

某些客戶更喜歡進行藍/綠升級策略。這可能有好處,但也存在一些需要考慮的缺點。

優點包括:

* 可以一次更改多個 EKS 版本(例如,從 1.23 到 1.25)
* 能夠切換回舊叢集
* 創建新的叢集,可能會使用更新的系統進行管理(例如 terraform)
* 工作負載可以單獨遷移

一些缺點包括:

* API 端點和 OIDC 更改,需要更新消費者(例如 kubectl 和 CI/CD)
* 在遷移期間需要並行運行 2 個叢集,這可能會很昂貴並限制區域容量
* 如果工作負載相互依賴,則需要更多協調才能一起遷移
* 負載均衡器和外部 DNS 無法輕易跨多個叢集

雖然可以採用這種策略,但它比就地升級更昂貴,並且需要更多時間進行協調和工作負載遷移。在某些情況下可能需要這樣做,並且應該進行仔細規劃。

隨著自動化程度和聲明式系統(如 GitOps)的提高,這樣做可能會更容易。您需要為有狀態的工作負載採取額外的預防措施,以便將數據備份並遷移到新的叢集。

查看這些博客文章以了解更多信息:

* [Kubernetes 叢集升級:藍/綠部署策略](https://aws.amazon.com/blogs/containers/kubernetes-cluster-upgrade-the-blue-green-deployment-strategy/)
* [無狀態 ArgoCD 工作負載的藍/綠或金絲雀 Amazon EKS 叢集遷移](https://aws.amazon.com/blogs/containers/blue-green-or-canary-amazon-eks-clusters-migration-for-stateless-argocd-workloads/)

## 跟踪 Kubernetes 項目中計劃的重大變更 — 提前思考

不要只看下一個版本。在新版本的 Kubernetes 發佈時查看,並識別重大變更。例如,一些應用程序直接使用了 docker API,並且在 Kubernetes `1.24` 中移除了對 Docker 容器運行時接口 (CRI) (也稱為 Dockershim) 的支持。這種變化需要更多時間來準備。
 
查看您要升級到的版本的所有記錄的變更,並注意任何必需的升級步驟。此外,還要注意 Amazon EKS 管理的叢集的任何特定要求或程序。

* [Kubernetes 變更日誌](https://github.com/kubernetes/kubernetes/tree/master/CHANGELOG)

## 特性移除的具體指導

### 在 1.25 中移除 Dockershim - 使用 Detector for Docker Socket (DDS)

1.25 的 EKS 優化 AMI 不再包括對 Dockershim 的支持。如果您依賴 Dockershim,例如您正在掛載 Docker 套接字,則在將工作節點升級到 1.25 之前需要移除這些依賴項。

在升級到 1.25 之前,找出您對 Docker 套接字有依賴的實例。我們建議使用 [Detector for Docker Socket (DDS),一個 kubectl 插件。](https://github.com/aws-containers/kubectl-detector-for-docker-socket)

### 在 1.25 中移除 PodSecurityPolicy - 遷移到 Pod Security Standards 或策略即代碼解決方案

`PodSecurityPolicy` [在 Kubernetes 1.21 中已被棄用](https://kubernetes.io/blog/2021/04/06/podsecuritypolicy-deprecation-past-present-and-future/),並在 Kubernetes 1.25 中已被移除。如果您在叢集中使用 PodSecurityPolicy,則必須在將叢集升級到 1.25 版本之前遷移到內置的 Kubernetes Pod Security Standards (PSS) 或策略即代碼解決方案,以避免對您的工作負載造成中斷。

AWS 在 EKS 文檔中發佈了 [詳細的常見問題解答。](https://docs.aws.amazon.com/eks/latest/userguide/pod-security-policy-removal-faq.html)

查看 [Pod Security Standards (PSS) 和 Pod Security Admission (PSA)](https://aws.github.io/aws-eks-best-practices/security/docs/pods/#pod-security-standards-pss-and-pod-security-admission-psa) 最佳實踐。

查看 Kubernetes 網站上的 [PodSecurityPolicy 棄用博客文章](https://kubernetes.io/blog/2021/04/06/podsecuritypolicy-deprecation-past-present-and-future/)。

### 在 1.23 中棄用內置存儲驅動程序 - 遷移到容器存儲接口 (CSI) 驅動程序

容器存儲接口 (CSI) 旨在幫助 Kubernetes 取代其現有的內置存儲驅動程序機制。Amazon EBS 容器存儲接口 (CSI) 遷移功能在 Amazon EKS `1.23` 及更高版本的叢集中默認啟用。如果您在 `1.22` 或更早版本的叢集上運行 pod,則必須在將叢集更新到 `1.23` 版本之前安裝 [Amazon EBS CSI 驅動程序](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html),以避免服務中斷。

查看 [Amazon EBS CSI 遷移常見問題解答](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi-migration-faq.html)。

## 其他資源

### ClowdHaus EKS 升級指南

[ClowdHaus EKS 升級指南](https://clowdhaus.github.io/eksup/) 是一個 CLI,可幫助升級 Amazon EKS 叢集。它可以分析叢集是否存在任何需要在升級之前修復的潛在問題。

### GoNoGo

[GoNoGo](https://github.com/FairwindsOps/GoNoGo) 是一個處於 alpha 階段的工具,用於確定您的叢集附加組件的升級信心。

