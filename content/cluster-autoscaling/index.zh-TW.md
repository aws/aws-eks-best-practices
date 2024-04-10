# Kubernetes 叢集自動調節器

<iframe width="560" height="315" src="https://www.youtube.com/embed/FIBc8GkjFU0" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

## 概述

[Kubernetes 叢集自動調節器](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler)是由 [SIG Autoscaling](https://github.com/kubernetes/community/tree/master/sig-autoscaling) 維護的一種流行的叢集自動調節解決方案。它負責確保您的叢集有足夠的節點來調度您的 Pod,而不會浪費資源。它會監視無法調度的 Pod 和利用率不足的節點。然後,它會在對您的叢集進行更改之前模擬添加或刪除節點。叢集自動調節器中的 AWS 雲端提供者實現控制您的 EC2 Auto Scaling 組的 `.DesiredReplicas` 欄位。

![](./architecture.png)

本指南將為配置叢集自動調節器和選擇最佳的一組權衡提供一個思維模型,以滿足您組織的要求。雖然沒有一個最佳配置,但有一組配置選項可以讓您在性能、可擴展性、成本和可用性之間進行權衡。此外,本指南還將提供在 AWS 上優化配置的技巧和最佳實踐。

### 詞彙表

以下術語將在本文件中頻繁使用。這些術語可能有廣泛的含義,但在本文件中僅限於以下定義。

**可擴展性**是指當您的 Kubernetes 叢集的 Pod 和節點數量增加時,叢集自動調節器的性能表現如何。當達到可擴展性限制時,叢集自動調節器的性能和功能將會降低。當叢集自動調節器超出其可擴展性限制時,它可能無法在您的叢集中添加或刪除節點。

**性能**是指叢集自動調節器能夠做出和執行擴展決策的速度。完美的性能意味著在出現刺激(如 Pod 無法調度)時,叢集自動調節器會立即做出決策並觸發擴展操作。

**可用性**意味著 Pod 可以快速調度且不會中斷。這包括新創建的 Pod 需要被調度以及縮減節點終止其上任何剩餘的已調度 Pod 的情況。

**成本**由縮放出和縮放入事件背後的決策決定。如果現有節點利用率不足或添加的新節點對於即將到來的 Pod 來說太大,資源就會被浪費。根據使用案例的不同,由於縮減決策過於積極而過早終止 Pod 也可能會產生相關成本。

**節點組**是叢集自動調節器、叢集 API 和其他組件中的一個抽象 Kubernetes 概念,用於表示叢集中的一組節點。它不是真正的 Kubernetes 資源,而是作為一種抽象存在。同一節點組中的節點共享屬性,如標籤和污點,但可能包含多個可用區或實例類型。

**EC2 Auto Scaling 組**可用作 EC2 上節點組的實現。EC2 Auto Scaling 組配置為啟動自動加入其 Kubernetes 叢集並將標籤和污點應用於相應的 Kubernetes API 中的節點資源的實例。

**EC2 Managed Node Groups** 是 EC2 上另一種節點組實現。它抽象了手動配置 EC2 Auto Scaling 組的複雜性,並提供了其他管理功能,如節點版本升級和優雅節點終止。

### 操作叢集自動調節器

叢集自動調節器通常作為[部署](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler/cloudprovider/aws/examples)安裝在您的叢集中。它使用[領導者選舉](https://en.wikipedia.org/wiki/Leader_election)來確保高可用性,但工作是由單個副本一次完成的。它不是水平可擴展的。對於基本設置,使用提供的[安裝說明](https://docs.aws.amazon.com/eks/latest/userguide/cluster-autoscaler.html)應該可以直接使用,但有一些事項需要注意。

確保:

* 叢集自動調節器的版本與叢集的版本相匹配。不支持跨版本兼容性 [不經測試或支持](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/README.md#releases)。
* 啟用了 [自動發現](https://github.com/kubernetes/autoscaler/tree/master/cluster-autoscaler/cloudprovider/aws#auto-discovery-setup),除非您有特定的高級用例阻止使用此模式。

### 對 IAM 角色採用最小權限訪問

當使用 [自動發現](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md#Auto-discovery-setup) 時,我們強烈建議您通過限制 `autoscaling:SetDesiredCapacity` 和 `autoscaling:TerminateInstanceInAutoScalingGroup` 操作僅適用於當前叢集範圍內的 Auto Scaling 組來採用最小權限訪問。

這將防止在一個叢集中運行的叢集自動調節器修改另一個叢集中的節點組,即使 `--node-group-auto-discovery` 參數沒有使用標籤 (例如 `k8s.io/cluster-autoscaler/<cluster-name>`) 將其範圍縮小到叢集的節點組。

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "autoscaling:SetDesiredCapacity",
                "autoscaling:TerminateInstanceInAutoScalingGroup"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "aws:ResourceTag/k8s.io/cluster-autoscaler/enabled": "true",
                    "aws:ResourceTag/k8s.io/cluster-autoscaler/<my-cluster>": "owned"
                }
            }
        },
        {
            "Effect": "Allow",
            "Action": [
                "autoscaling:DescribeAutoScalingGroups",
                "autoscaling:DescribeAutoScalingInstances",
                "autoscaling:DescribeLaunchConfigurations",
                "autoscaling:DescribeScalingActivities",
                "autoscaling:DescribeTags",
                "ec2:DescribeImages",
                "ec2:DescribeInstanceTypes",
                "ec2:DescribeLaunchTemplateVersions",
                "ec2:GetInstanceTypesFromInstanceRequirements",
                "eks:DescribeNodegroup"
            ],
            "Resource": "*"
        }
    ]
}
```

### 配置您的節點組

有效的自動擴展從正確配置一組節點組開始。選擇正確的節點組集對於最大化可用性和降低跨工作負載的成本至關重要。AWS 使用 EC2 Auto Scaling 組實現節點組,這對於大量使用案例來說非常靈活。但是,叢集自動調節器對您的節點組做出了一些假設。保持您的 EC2 Auto Scaling 組配置與這些假設一致將最小化不希望的行為。

確保:

* 每個節點組中的每個節點都具有相同的調度屬性,例如標籤、污點和資源。
  * 對於 MixedInstancePolicies,實例類型必須具有相同的 CPU、內存和 GPU 形狀
  * 策略中指定的第一個實例類型將用於模擬調度。
  * 如果您的策略包含更多資源的其他實例類型,在縮放出後資源可能會被浪費。
  * 如果您的策略包含較少資源的其他實例類型,由於容量不足,您的 Pod 可能無法在新實例上調度。
* 節點數量多的節點組優於節點數量少的多個節點組。這將對可擴展性產生最大影響。
* 盡可能選擇 EC2 功能,當兩個系統都提供支持時 (例如區域、MixedInstancePolicy)

*注意:我們建議使用 [EKS Managed Node Groups](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html)。Managed Node Groups 帶有強大的管理功能,包括用於叢集自動調節器的功能,如自動 EC2 Auto Scaling 組發現和優雅節點終止。*

## 優化性能和可擴展性

了解自動擴展算法的運行時複雜度將幫助您調整叢集自動調節器,以便在大於 [1,000 個節點](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/proposals/scalability_tests.md) 的大型叢集中繼續順利運行。

調整叢集自動調節器可擴展性的主要旋鈕是提供給進程的資源、算法的掃描間隔和叢集中的節點組數量。還有其他因素涉及到這個算法的真實運行時複雜度,例如調度插件複雜度和 Pod 數量。這些被認為是不可配置的參數,因為它們是叢集工作負載的自然屬性,無法輕易調整。

叢集自動調節器將整個叢集的狀態加載到內存中,包括 Pod、節點和節點組。在每個掃描間隔,算法識別無法調度的 Pod 並為每個節點組模擬調度。調整這些因素會帶來不同的權衡,應該根據您的使用案例仔細考慮。

### 垂直自動擴展叢集自動調節器

擴展叢集自動調節器到更大叢集的最簡單方法是增加其部署的資源請求。對於大型叢集,內存和 CPU 都應該增加,儘管這因叢集大小而有很大差異。通常會手動增加資源。如果您發現不斷調整資源會增加運營負擔,請考慮使用 [Addon Resizer](https://github.com/kubernetes/autoscaler/tree/master/addon-resizer) 或 [Vertical Pod Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler)。

### 減少節點組數量

最小化節點組數量是確保叢集自動調節器在大型叢集上繼續良好運行的一種方式。對於一些組織來說,這可能是一個挑戰,他們將節點組按團隊或應用程序進行結構化。雖然 Kubernetes API 完全支持這一點,但這被認為是叢集自動調節器的一種反模式,會對可擴展性產生影響。有許多使用多個節點組的原因 (例如 Spot 或 GPU),但在許多情況下,有替代設計可以實現相同的效果,同時使用少量組。

確保:

* Pod 隔離使用命名空間而不是節點組。
  * 在低信任多租戶叢集中可能無法實現這一點。
  * 正確設置 Pod ResourceRequests 和 ResourceLimits 以避免資源競爭。
  * 較大的實例類型將導致更優化的 bin packing 和減少系統 Pod 開銷。
* 使用 NodeTaints 或 NodeSelectors 來調度 Pod 作為例外情況,而不是規則。
* 將區域資源定義為具有多個可用區的單個 EC2 Auto Scaling 組。

### 減少掃描間隔

較低的掃描間隔 (例如 10 秒) 將確保當 Pod 無法調度時,叢集自動調節器能夠盡快做出響應。但是,每次掃描都會導致對 Kubernetes API 和 EC2 Auto Scaling 組或 EKS Managed Node Group API 進行多次 API 調用。這些 API 調用可能會導致速率限制,甚至導致您的 Kubernetes 控制平面服務不可用。

默認掃描間隔為 10 秒,但在 AWS 上,啟動新節點需要更長的時間來啟動新實例。這意味著可以在不會顯著增加整體擴展時間的情況下增加間隔。例如,如果啟動一個節點需要 2 分鐘,將間隔更改為 1 分鐘將導致 API 調用減少 6 倍,而縮放速度僅慢 38%。

### 跨節點組分片

叢集自動調節器可以配置為僅在特定的節點組集上運行。使用此功能,您可以部署多個叢集自動調節器實例,每個實例配置為在不同的節點組集上運行。這種策略使您能夠使用任意大量的節點組,以成本換取可擴展性。我們僅建議在最後一次嘗試提高性能時使用此方法。

叢集自動調節器最初並非為此配置而設計,因此存在一些副作用。由於分片不相互通信,因此有可能多個自動調節器嘗試調度無法調度的 Pod。這可能會導致多個節點組不必要的縮放出。這些額外的節點將在 `scale-down-delay` 之後縮減回來。

```
metadata:
  name: cluster-autoscaler
  namespace: cluster-autoscaler-1

...

--nodes=1:10:k8s-worker-asg-1
--nodes=1:10:k8s-worker-asg-2

---

metadata:
  name: cluster-autoscaler
  namespace: cluster-autoscaler-2

...

--nodes=1:10:k8s-worker-asg-3
--nodes=1:10:k8s-worker-asg-4
```

確保:

* 每個分片都配置為指向一組唯一的 EC2 Auto Scaling 組
* 每個分片都部署到單獨的命名空間以避免領導者選舉衝突

## 優化成本和可用性

### Spot 實例

您可以在節點組中使用 Spot 實例,並節省高達 90% 的按需價格,但代價是 Spot 實例可能會在 EC2 需要回收容量時隨時被中斷。當您的 EC2 Auto Scaling 組由於缺乏可用容量而無法擴展時,將發生 Insufficient Capacity Errors。選擇多個實例系列可以最大限度地增加多樣性,從而提高您獲得所需規模的機會,並減少 Spot 實例中斷對您的叢集可用性的影響,同時也可以訪問多個 Spot 容量池。帶有 Spot 實例的 Mixed Instance Policies 是增加多樣性而不增加節點組數量的好方法。請記住,如果您需要保證資源,請使用 On-Demand 實例而不是 Spot 實例。

在配置 Mixed Instance Policies 時,確保所有實例類型都具有相似的資源容量至關重要。自動調節器的調度模擬器使用 MixedInstancePolicy 中的第一個 InstanceType。如果後續實例類型更大,在縮放出後資源可能會被浪費。如果更小,由於容量不足,您的 Pod 可能無法在新實例上調度。例如,M4、M5、M5a 和 M5n 實例都具有相似的 CPU 和內存量,是 MixedInstancePolicy 的絕佳候選。[EC2 Instance Selector](https://github.com/aws/amazon-ec2-instance-selector) 工具可以幫助您識別相似的實例類型。

![](./spot_mix_instance_policy.jpg)

建議將 On-Demand 和 Spot 容量隔離到單獨的 EC2 Auto Scaling 組中。這比使用 [基本容量策略](https://docs.aws.amazon.com/autoscaling/ec2/userguide/asg-purchase-options.html#asg-instances-distribution) 更可取,因為調度屬性根本不同。由於 Spot 實例可能會在任何時候被中斷 (當 EC2 需要回收容量時),用戶通常會為其可預先中斷的節點添加污點,需要明確的 Pod 容忍該中斷行為。這些污點導致了不同的調度屬性,因此它們應該被分離到多個 EC2 Auto Scaling 組中。

叢集自動調節器有一個 [Expanders](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md#what-are-expanders) 概念,它提供了不同的策略來選擇要縮放哪個節點組。策略 `--expander=least-waste` 是一個不錯的通用默認值,如果您要為 Spot 實例多樣性使用多個節點組 (如上圖所示),它可以進一步優化節點組的成本,通過縮放在縮放活動後利用率最高的組。

### 優先級節點組 / ASG

您還可以通過使用 Priority expander 配置基於優先級的自動擴展。`--expander=priority` 使您的叢集能夠優先選擇一個節點組/ASG,如果無法縮放,它將選擇優先級列表中的下一個節點組。在某些情況下,這很有用,例如,您希望使用 P3 實例類型,因為它們的 GPU 為您的工作負載提供了最佳性能,但作為第二選擇,您也可以使用 P2 實例類型。

```
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-priority-expander
  namespace: kube-system
data:
  priorities: |-
    10:
      - .*p2-node-group.*
    50:
      - .*p3-node-group.*
```

叢集自動調節器將嘗試縮放與名稱 *p3-node-group* 匹配的 EC2 Auto Scaling 組。如果在 `--max-node-provision-time` 內此操作不成功,它將嘗試縮放與名稱 *p2-node-group* 匹配的 EC2 Auto Scaling 組。
此值默認為 15 分鐘,可以縮短以獲得更響應式的節點組選擇,但如果值太低,可能會導致不必要的縮放出。

### 過度配置

叢集自動調節器通過確保僅在需要時才向叢集添加節點,並在未使用時將其刪除,從而最小化成本。這顯著影響了部署延遲,因為許多 Pod 將被迫等待節點縮放出才能被調度。節點可能需要幾分鐘才能可用,這可能會將 Pod 調度延遲增加一個數量級。

這可以通過使用 [過度配置](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md#how-can-i-configure-overprovisioning-with-cluster-autoscaler) 來緩解,它以成本換取調度延遲。過度配置是使用具有負優先級的臨時 Pod 實現的,這些 Pod 佔用叢集中的空間。當新創建的 Pod 無法調度並且具有更高優先級時,臨時 Pod 將被預先中斷以騰出空間。然後,這些臨時 Pod 變為無法調度,觸發叢集自動調節器縮放出新的過度配置節點。

過度配置還有其他不太明顯的好處。如果沒有過度配置,高度利用的叢集的一個副作用是 Pod 將根據 Pod 或節點親和性的 `preferredDuringSchedulingIgnoredDuringExecution` 規則做出不太理想的調度決策。一個常見的用例是使用反親和性將高可用性應用程序的 Pod 分離到不同的可用區。過度配置可以顯著增加正確區域節點可用的機會。

您組織的過度配置容量量是一個謹慎的業務決策。從本質上講,它是性能和成本之間的權衡。做出這個決定的一種方式是確定您的平均縮放出頻率,並將其除以縮放出新節點所需的時間。例如,如果平均每 30 秒需要一個新節點,而 EC2 需要 30 秒來配置一個新節點,則單個節點的過度配置將確保始終有一個額外的節點可用,從而將調度延遲減少 30 秒,代價是一個額外的 EC2 實例。為了改善區域調度決策,請過度配置與您的 EC2 Auto Scaling 組中可用區數量相同的節點數量,以確保調度程序可以為傳入的 Pod 選擇最佳區域。

### 防止縮減驅逐

某些工作負載驅逐成本很高。大數據分析、機器學習任務和測試運行程序最終將完成,但如果中斷則必須重新啟動。叢集自動調節器將嘗試縮減低於 scale-down-utilization-threshold 的任何節點,這將中斷該節點上的任何剩餘 Pod。這可以通過確保昂貴的驅逐 Pod 由叢集自動調節器識別的標籤保護來防止。

確保:

* 昂貴的驅逐 Pod 具有註釋 `cluster-autoscaler.kubernetes.io/safe-to-evict=false`

## 高級使用案例

### EBS 卷

持久存儲對於構建有狀態應用程序(如數據庫或分佈式緩存)至關重要。[EBS 卷](https://aws.amazon.com/premiumsupport/knowledge-center/eks-persistent-storage/)使 Kubernetes 上的這種用例成為可能,但僅限於特定區域。如果使用單獨的 EBS 卷跨多個可用區分片,這些應用程序可以實現高可用性。然後,叢集自動調節器可以平衡 EC2 Auto Scaling 組的縮放。

確保:

* 通過設置 `balance-similar-node-groups=true` 啟用節點組平衡。
* 除了不同的可用區和 EBS 卷外,節點組配置相同。

### 協同調度

機器學習分佈式訓練作業可以顯著受益於同區域節點配置帶來的最小延遲。這些工作負載將多個 Pod 部署到特定區域。這可以通過為所有協同調度的 Pod 設置 Pod 親和性或使用 `topologyKey: failure-domain.beta.kubernetes.io/zone` 的節點親和性來實現。然後,叢集自動調節器將縮放出特定區域以滿足需求。您可能希望為每個可用區分配多個 EC2 Auto Scaling 組,以實現整個協同調度工作負載的故障轉移。

確保:

* 通過設置 `balance-similar-node-groups=false` 禁用節點組平衡
* 當叢集包含區域和區域節點組時,使用 [節點親和性](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity) 和/或 [Pod 抢占](https://kubernetes.io/docs/concepts/configuration/pod-priority-preemption/)。
  * 使用 [節點親和性](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity) 強制或鼓勵區域 Pod 避開區域節點組,反之亦然。
  * 如果區域 Pod 調度到區域節點組,這將導致您的區域 Pod 的容量不平衡。
  * 如果您的區域工作負載可以容忍中斷和重新調度,請配置 [Pod 抢占](https://kubernetes.io/docs/concepts/configuration/pod-priority-preemption/) 以使區域縮放的 Pod 能夠強制抢占和重新調度到競爭較少的區域。

### 加速器

某些叢集利用了諸如 GPU 之類的專用硬件加速器。在縮放出時,加速器設備插件可能需要幾分鐘才能將資源通知給叢集。叢集自動調節器已模擬該節點將具有加速器,但直到加速器準備就緒並更新節點的可用資源,待處理的 Pod 才能在該節點上調度。這可能會導致 [重複不必要的縮放出](https://github.com/kubernetes/kubernetes/issues/54959)。

此外,即使加速器未被使用,具有加速器和高 CPU 或內存利用率的節點也不會被視為縮減對象。由於加速器的相對成本,這種行為可能會很昂貴。相反,叢集自動調節器可以應用特殊規則,如果節點上的加速器未被佔用,則將其視為縮減對象。

為確保這些情況下的正確行為,您可以配置加速器節點上的 kubelet 在加入叢集之前標記該節點。叢集自動調節器將使用此標籤選擇器觸發加速器優化行為。

確保:

* 配置 GPU 節點上的 Kubelet 具有 `--node-labels k8s.amazonaws.com/accelerator=$ACCELERATOR_TYPE`
* 具有加速器的節點遵守上述相同的調度屬性規則。

### 從 0 縮放

叢集自動調節器能夠將節點組縮放到和從零,這可以帶來顯著的成本節省。它通過檢查其 LaunchConfiguration 或 LaunchTemplate 中指定的 InstanceType 來檢測 Auto Scaling 組的 CPU、內存和 GPU 資源。某些 Pod 需要其他資源,如 `WindowsENI` 或 `PrivateIPv4Address`,或特定的 NodeSelectors 或 Taints,這些資源無法從 LaunchConfiguration 中發現。叢集自動調節器可以通過在 EC2 Auto Scaling 組上的標籤來發現這些因素。例如:

```
Key: k8s.io/cluster-autoscaler/node-template/resources/$RESOURCE_NAME
Value: 5
Key: k8s.io/cluster-autoscaler/node-template/label/$LABEL_KEY
Value: $LABEL_VALUE
Key: k8s.io/cluster-autoscaler/node-template/taint/$TAINT_KEY
Value: NoSchedule
```

*注意:請記住,當縮放到零時,您的容量將返回到 EC2,將來可能無法使用。*

## 其他參數

還有許多配置選項可用於調整叢集自動調節器的行為和性能。
完整的參數列表可在 [GitHub](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md#what-are-the-parameters-to-ca) 上找到。

|  |  |  |
|-|-|-|
| 參數 | 描述 | 默認值 |
| scan-interval | 重新評估縮放出或縮減的頻率 | 10 秒 |
| max-empty-bulk-delete | 同時可刪除的最大空節點數 | 10 |
| scale-down-delay-after-add | 縮放出後恢復縮減評估的時間 | 10 分鐘 |
| scale-down-delay-after-delete | 節點刪除後恢復縮減評估的時間,默認為 scan-interval | scan-interval |
| scale-down-delay-after-failure | 縮減失敗後恢復縮減評估的時間 | 3 分鐘 |
| scale-down-unneeded-time | 節點被視為不需要並有資格縮減之前的時間 | 10 分鐘 |
| scale-down-unready-time | 未就緒節點被視為不需要並有資格縮減之前的時間 | 20 分鐘 |
| scale-down-utilization-threshold | 節點利用率水平,定義為請求資源之和除以容量,低於該值的節點可被視為縮減對象 | 0.5 |
| scale-down-non-empty-candidates-count | 在一次迭代中作為縮減候選對象的非空節點的最大數量,並進行排空。較低的值意味著更好的 CA 響應能力,但可能會導致較慢的縮減延遲。對於大型叢集(數百個節點),較高的值可能會影響 CA 性能。設置為非正值以關閉此啟發式 - CA 將不會限制它考慮的節點數量。" | 30 |
| scale-down-candidates-pool-ratio | 當上一次迭代中的某些候選節點不再有效時,作為額外非空縮減候選對象的節點比率。較低的值意味著更好的 CA 響應能力,但可能會導致較慢的縮減延遲。對於大型叢集(數百個節點),較高的值可能會影響 CA 性能。設置為 1.0 以關閉此啟發式 - CA 將把所有節點作為額外候選對象。 | 0.1 |
| scale-down-candidates-pool-min-count | 當上一次迭代中的某些候選節點不再有效時,作為額外非空縮減候選對象的最小節點數。在計算額外候選對象的池大小時,我們取 `max(#nodes * scale-down-candidates-pool-ratio, scale-down-candidates-pool-min-count)` | 50 |

## 其他資源

本頁面包含了一系列叢集自動調節器演示文稿和演示。如果您想在此添加演示文稿或演示,請發送拉取請求。

| 演示文稿/演示 | 演講者 |
| ------------ | ------- |
| [Autoscaling and Cost Optimization on Kubernetes: From 0 to 100](https://sched.co/Zemi) | Guy Templeton, Skyscanner & Jiaxin Shan, Amazon |
| [SIG-Autoscaling Deep Dive](https://youtu.be/odxPyW_rZNQ) | Maciek Pytel & Marcin Wielgus |

## 參考資料

* [https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md)
* [https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md)
* [https://github.com/aws/amazon-ec2-instance-selector](https://github.com/aws/amazon-ec2-instance-selector)
* [https://github.com/aws/aws-node-termination-handler](https://github.com/aws/aws-node-termination-handler)
