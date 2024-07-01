# 支出意識

支出意識是了解誰、在哪裡以及是什麼原因導致您的 EKS 叢集中產生支出。獲得這些數據的準確圖像將有助於提高您對支出的意識,並突出需要補救的領域。

## 建議
### 使用 Cost Explorer

[AWS Cost Explorer](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/) 提供了一個簡單易用的介面,讓您隨時可視化、了解和管理您的 AWS 成本和使用情況。您可以使用 Cost Explorer 中可用的篩選器,在各個層級分析成本和使用情況數據。

#### EKS 控制平面和 EKS Fargate 成本

使用篩選器,我們可以查詢如下圖所示的 EKS 控制平面和 Fargate Pod 產生的成本:

![Cost Explorer - EKS Control Plane](../images/eks-controlplane-costexplorer.png)

使用篩選器,我們可以查詢 EKS 中跨區域 Fargate Pod 產生的總成本,其中包括每 CPU 的 vCPU 小時和 GB 小時,如下圖所示:

![Cost Explorer - EKS Fargate](../images/eks-fargate-costexplorer.png)

#### 資源標記

Amazon EKS 支持為您的 Amazon EKS 叢集[添加 AWS 標記](https://docs.aws.amazon.com/eks/latest/userguide/eks-using-tags.html)。這樣可以輕鬆控制對 EKS API 的訪問,以管理您的叢集。添加到 EKS 叢集的標記僅特定於 AWS EKS 叢集資源,它們不會傳播到叢集使用的其他 AWS 資源,如 EC2 實例或負載平衡器。目前,通過 AWS API、控制台和 SDK 支持為所有新的和現有的 EKS 叢集添加叢集標記。

AWS Fargate 是一項技術,為容器提供按需、合適大小的計算容量。在您可以在叢集中調度 Fargate 上的 Pod 之前,您必須定義至少一個 Fargate 配置文件,指定在啟動時應該使用 Fargate 的 Pod。

向 EKS 叢集添加和列出標記:
```
$ aws eks tag-resource --resource-arn arn:aws:eks:us-west-2:xxx:cluster/ekscluster1 --tags team=devops,env=staging,bu=cio,costcenter=1234
$ aws eks list-tags-for-resource --resource-arn arn:aws:eks:us-west-2:xxx:cluster/ekscluster1
{
    "tags": {
        "bu": "cio",
        "env": "staging",
        "costcenter": "1234",
        "team": "devops"
    }
}
```
在您啟用 [AWS Cost Explorer](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html) 中的成本分配標記後,AWS 將使用成本分配標記來組織您的資源成本,以便您更容易分類和跟踪您的 AWS 成本。

標記對 Amazon EKS 沒有任何語義含義,並且嚴格解釋為一串字符。例如,您可以為您的 Amazon EKS 叢集定義一組標記,以幫助您跟踪每個叢集的所有者和堆棧級別。

### 使用 AWS Trusted Advisor

AWS Trusted Advisor 提供了一套豐富的最佳實踐檢查和建議,涵蓋五個類別:成本優化;安全性;容錯能力;性能;和服務限制。

對於成本優化,Trusted Advisor 有助於消除未使用和閒置的資源,並建議對保留容量進行承諾。對於 Amazon EKS 將有助於的關鍵操作項是低使用率的 EC2 實例、未關聯的彈性 IP 地址、閒置的負載平衡器、低使用率的 EBS 卷等。完整的檢查列表可在 https://aws.amazon.com/premiumsupport/technology/trusted-advisor/best-practice-checklist/ 上找到。

Trusted Advisor 還提供了 EC2 實例和 Fargate 的 Savings Plans 和保留實例建議,允許您承諾一致的使用量以換取折扣價格。

!!! 注意
    Trusted Advisor 的建議是通用建議,而不是針對 EKS 的特定建議。

### 使用 Kubernetes 儀表板

***Kubernetes 儀表板***

Kubernetes 儀表板是一個通用的基於 Web 的 UI,用於 Kubernetes 叢集,它提供了有關 Kubernetes 叢集的信息,包括叢集、節點和 Pod 級別的資源使用情況。在 Amazon EKS 叢集上部署 Kubernetes 儀表板的過程在 [Amazon EKS 文檔](https://docs.aws.amazon.com/eks/latest/userguide/dashboard-tutorial.html)中有描述。

儀表板提供了每個節點和 Pod 的資源使用情況細分,以及有關 Pod、服務、Deployment 和其他 Kubernetes 對象的詳細元數據。這些綜合信息為您的 Kubernetes 環境提供了可見性。

![Kubernetes Dashboard](../images/kubernetes-dashboard.png)

***kubectl top 和 describe 命令***

使用 kubectl top 和 kubectl describe 命令查看資源使用情況指標。kubectl top 將顯示您的叢集中的 Pod 或節點的當前 CPU 和內存使用情況,或特定 Pod 或節點的使用情況。kubectl describe 命令將提供有關特定節點或 Pod 的更多詳細信息。
```
$ kubectl top pods
$ kubectl top nodes
$ kubectl top pod pod-name --namespace mynamespace --containers
```

使用 top 命令,輸出將顯示節點正在使用的總 CPU (以核心為單位)和內存 (以 MiB 為單位)量,以及這些數字佔節點可分配容量的百分比。然後,您可以通過添加 *--containers* 標誌,深入到 Pod 內的容器級別。


```
$ kubectl describe node <node>
$ kubectl describe pod <pod>
```

*kubectl describe* 返回每個資源請求或限制所佔總可用容量的百分比。

kubectl top 和 describe 可跟踪 Kubernetes Pod、節點和容器中關鍵資源(如 CPU、內存和存儲)的使用情況和可用性。這種意識將有助於了解資源使用情況,並有助於控制成本。

### 使用 CloudWatch Container Insights

使用 [CloudWatch Container Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/deploy-container-insights-EKS.html) 收集、匯總和總結您的容器化應用程序和微服務的指標和日誌。Container Insights 適用於 Amazon Elastic Kubernetes Service on EC2 和 Amazon EC2 上的 Kubernetes 平台。這些指標包括 CPU、內存、磁盤和網絡等資源的使用情況。

安裝說明在 [文檔](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/deploy-container-insights-EKS.html) 中有介紹。

CloudWatch 在叢集、節點、Pod、任務和服務級別創建匯總指標作為 CloudWatch 指標。

**以下查詢顯示了按平均節點 CPU 使用率排序的節點列表**
```
STATS avg(node_cpu_utilization) as avg_node_cpu_utilization by NodeName
| SORT avg_node_cpu_utilization DESC 
```

**按容器名稱劃分的 CPU 使用情況**
```
stats pct(container_cpu_usage_total, 50) as CPUPercMedian by kubernetes.container_name 
| filter Type="Container"
```
**按容器名稱劃分的磁盤使用情況**
```
stats floor(avg(container_filesystem_usage/1024)) as container_filesystem_usage_avg_kb by InstanceId, kubernetes.container_name, device 
| filter Type="ContainerFS" 
| sort container_filesystem_usage_avg_kb desc
```

更多示例查詢可在 [Container Insights 文檔](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Container-Insights-view-metrics.html)中找到。

這種意識將有助於了解資源使用情況,並有助於控制成本。

### 使用 KubeCost 實現支出意識和指導

像 [kubecost](https://kubecost.com/) 這樣的第三方工具也可以部署在 Amazon EKS 上,以獲得運行 Kubernetes 叢集的成本可見性。請參閱此 [AWS 博客](https://aws.amazon.com/blogs/containers/how-to-track-costs-in-multi-tenant-amazon-eks-clusters-using-kubecost/)以了解使用 Kubecost 跟踪成本的相關信息。

使用 Helm 3 部署 kubecost:
```
$ curl -sSL https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash
$ helm version --short
v3.2.1+gfe51cd1
$ helm repo add stable https://kubernetes-charts.storage.googleapis.com/
$ helm repo add stable https://kubernetes-charts.storage.googleapis.com/c^C
$ kubectl create namespace kubecost 
namespace/kubecost created
$ helm repo add kubecost https://kubecost.github.io/cost-analyzer/ 
"kubecost" has been added to your repositories

$ helm install kubecost kubecost/cost-analyzer --namespace kubecost --set kubecostToken="aGRoZEBqc2pzLmNvbQ==xm343yadf98"
NAME: kubecost
LAST DEPLOYED: Mon May 18 08:49:05 2020
NAMESPACE: kubecost
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
--------------------------------------------------Kubecost has been successfully installed. When pods are Ready, you can enable port-forwarding with the following command:
    
    kubectl port-forward --namespace kubecost deployment/kubecost-cost-analyzer 9090
    
Next, navigate to http://localhost:9090 in a web browser.
$ kubectl port-forward --namespace kubecost deployment/kubecost-cost-analyzer 9090

Note: If you are using Cloud 9 or have a need to forward it to a different port like 8080, issue the following command
$ kubectl port-forward --namespace kubecost deployment/kubecost-cost-analyzer 8080:9090

```
Kube Cost 儀表板 -
![Kubernetes Cluster Auto Scaler logs](../images/kube-cost.png)

### 使用 Kubernetes 成本分配和容量規劃分析工具

[Kubernetes Opex Analytics](https://github.com/rchakode/kube-opex-analytics) 是一種工具,可幫助組織跟踪其 Kubernetes 叢集正在消耗的資源,以防止支付過多費用。為此,它生成短期 (7 天)、中期 (14 天) 和長期 (12 個月) 使用報告,顯示每個項目隨時間消耗的相關資源量。

![Kubernetes Opex Analytics](../images/kube-opex-analytics.png)

### Magalix Kubeadvisor

[KubeAdvisor](https://www.magalix.com/kubeadvisor) 持續掃描您的 Kubernetes 叢集,並報告如何修復問題、應用最佳實踐以及優化您的叢集 (包括有關成本效率的 CPU/內存資源建議)。

### Spot.io,以前稱為 Spotinst

Spotinst Ocean 是一個應用程序擴展服務。與 Amazon Elastic Compute Cloud (Amazon EC2) Auto Scaling 組類似,Spotinst Ocean 旨在通過利用 Spot 實例結合按需和保留實例來優化性能和成本。使用自動 Spot 實例管理和各種實例大小的組合,Ocean 叢集自動擴展器根據 Pod 資源需求進行擴展。Spotinst Ocean 還包括一種預測算法,可以提前 15 分鐘預測 Spot 實例中斷,並在不同的 Spot 容量池中啟動一個新節點。

這可作為 [AWS Quickstart](https://aws.amazon.com/quickstart/architecture/spotinst-ocean-eks/) 提供,由 Spotinst, Inc. 與 AWS 合作開發。

EKS 研討會還有一個模塊 [Optimized Worker Node on Amazon EKS Management](https://eksworkshop.com/beginner/190_ocean/) 與 Spot.io 的 Ocean,其中包括成本分配、正確調整大小和擴展策略等部分。

### Yotascale

Yotascale 有助於準確分配 Kubernetes 成本。Yotascale Kubernetes 成本分配功能利用實際成本數據(包括保留實例折扣和現貨實例定價),而不是通用市場價格估算,來通知總 Kubernetes 成本支出。

更多詳細信息可在 [他們的網站](https://www.yotascale.com/) 上找到。

### Alcide Advisor

Alcide 是 AWS 合作夥伴網絡 (APN) 高級技術合作夥伴。Alcide Advisor 有助於確保您的 Amazon EKS 叢集、節點和 Pod 配置根據安全最佳實踐和內部指南進行調整。Alcide Advisor 是一種無代理的 Kubernetes 審計和合規性服務,旨在通過在轉移到生產環境之前加固開發階段,確保無摩擦和安全的 DevSecOps 流程。

更多詳細信息可在此 [博客文章](https://aws.amazon.com/blogs/apn/driving-continuous-security-and-configuration-checks-for-amazon-eks-with-alcide-advisor/) 中找到。

## 其他工具

### Kubernetes 垃圾收集

[Kubernetes 垃圾收集器](https://kubernetes.io/docs/concepts/workloads/controllers/garbage-collection/)的作用是刪除某些曾經有所有者但現在沒有所有者的對象。

### Fargate count

[Fargatecount](https://github.com/mreferre/fargatecount) 是一個有用的工具,它允許 AWS 客戶使用自定義 CloudWatch 指標跟踪在特定區域的特定帳戶中部署在 Fargate 上的 EKS Pod 總數。這有助於跟踪跨 EKS 叢集運行的所有 Fargate Pod。

### Kubernetes Ops View

[Kube Ops View](https://github.com/hjacobs/kube-ops-view) 是一個有用的工具,它為多個 Kubernetes 叢集提供了一個通用的操作圖像。

```
git clone https://github.com/hjacobs/kube-ops-view
cd kube-ops-view
kubectl apply -k deploy/
```

![Home Page](../images/kube-ops-report.png)

### Popeye - 一個 Kubernetes 叢集清理工具

[Popeye - A Kubernetes Cluster Sanitizer](https://github.com/derailed/popeye) 是一個實用程序,它掃描實時 Kubernetes 叢集並報告已部署資源和配置中的潛在問題。它根據部署的內容而不是磁盤上的內容來清理您的叢集。通過掃描您的叢集,它可以檢測到錯誤配置,並幫助您確保最佳實踐得到實施。

### 資源
請參閱以下資源,了解有關成本優化的最佳實踐。

文檔和博客
+	[Amazon EKS supports tagging](https://docs.aws.amazon.com/eks/latest/userguide/eks-using-tags.html)

工具
+	[什麼是 AWS Billing and Cost Management?](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/cost-alloc-tags.html)
+	[Amazon CloudWatch Container Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights.html)
+   [How to track costs in multi-tenant Amazon EKS clusters using Kubecost](https://aws.amazon.com/blogs/containers/how-to-track-costs-in-multi-tenant-amazon-eks-clusters-using-kubecost/) 
+   [Kube Cost](https://kubecost.com/)
+   [Kube Opsview](https://github.com/hjacobs/kube-ops-view)
+  [Kube Janitor](https://github.com/hjacobs/kube-janitor)
+  [Kubernetes Opex Analytics](https://github.com/rchakode/kube-opex-analytics)