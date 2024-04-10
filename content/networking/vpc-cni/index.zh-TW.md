# Amazon VPC CNI

<iframe width="560" height="315" src="https://www.youtube.com/embed/RBE3yk2UlYA" title="YouTube 視頻播放器" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

Amazon EKS 透過 [Amazon VPC Container Network Interface](https://github.com/aws/amazon-vpc-cni-k8s) [(VPC CNI)](https://github.com/aws/amazon-vpc-cni-k8s) 插件實現叢集網路。CNI 插件允許 Kubernetes Pod 擁有與 VPC 網路相同的 IP 地址。更確切地說,Pod 內的所有容器共享一個網路命名空間,並且它們可以使用本地端口彼此通信。

Amazon VPC CNI 有兩個組件:

* CNI 二進制檔案,將設置 Pod 網路以啟用 Pod 間通信。CNI 二進制檔案運行在節點根檔案系統上,並由 kubelet 在新的 Pod 被添加到或現有 Pod 從節點移除時調用。
* ipamd,一個長期運行的節點本地 IP 地址管理 (IPAM) 守護程序,負責:
  * 管理節點上的 ENI,以及
  * 維護可用 IP 地址或前綴的熱池

當實例被創建時,EC2 會創建並附加與主子網關聯的主 ENI。主子網可以是公共的或私有的。在 hostNetwork 模式下運行的 Pod 使用分配給節點主 ENI 的主 IP 地址,並與主機共享相同的網路命名空間。

CNI 插件管理節點上的 [彈性網路接口 (ENI)](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html)。當節點被配置時,CNI 插件會自動從節點的子網為主 ENI 分配一個插槽池 (IP 或前綴)。這個池被稱為 *熱池*,其大小由節點的實例類型決定。根據 CNI 設置,插槽可能是 IP 地址或前綴。當 ENI 上的插槽已被分配時,CNI 可能會將額外的 ENI 附加到節點,並為其分配熱池插槽。這些額外的 ENI 被稱為 次要 ENI。每個 ENI 只能支援一定數量的插槽,這取決於實例類型。CNI 根據所需的插槽數量 (通常對應於 Pod 數量) 將更多 ENI 附加到實例。這個過程一直持續到節點無法支援額外的 ENI 為止。CNI 還會預先分配 "熱" ENI 和插槽,以加快 Pod 啟動速度。請注意,每種實例類型都有可以附加的 ENI 的最大數量。這是 Pod 密度 (每個節點的 Pod 數量) 的一個限制,除了計算資源之外。

![流程圖說明了何時需要新的 ENI 委派前綴](./image.png)

每種 EC2 實例類型支援的網路接口和插槽數量是不同的。由於每個 Pod 都會佔用一個插槽上的 IP 地址,因此您可以在特定 EC2 實例上運行的 Pod 數量取決於可以附加到它的 ENI 數量以及每個 ENI 支援的 IP 地址數量。我們建議您按照 EKS 用戶指南設置最大 Pod 數量,以避免耗盡實例的 CPU 和內存資源。使用 `hostNetwork` 的 Pod 不包括在此計算中。您可以考慮使用名為 [max-pod-calculator.sh](https://github.com/awslabs/amazon-eks-ami/blob/master/files/max-pods-calculator.sh) 的腳本來計算 EKS 為給定實例類型建議的最大 Pod 數量。

## 概述

次要 IP 模式是 VPC CNI 的默認模式。本指南提供了 VPC CNI 在啟用次要 IP 模式時的一般行為概述。ipamd (IP 地址分配) 的功能可能會因 VPC CNI 的配置設置而有所不同,例如 [前綴模式](../prefix-mode/index_linux.md)、[每 Pod 安全組](../sgpp/index.md) 和 [自定義網路](../custom-networking/index.md)。

Amazon VPC CNI 作為名為 aws-node 的 Kubernetes Daemonset 部署在工作節點上。當工作節點被配置時,它有一個默認的 ENI 附加到它,稱為主 ENI。CNI 從附加到節點主 ENI 的子網中分配一個熱池的 ENI 和次要 IP 地址。默認情況下,ipamd 會嘗試為節點分配一個額外的 ENI。當單個 Pod 被調度並從主 ENI 分配一個次要 IP 地址時,IPAMD 會分配額外的 ENI。這個 "熱" ENI 可以加快 Pod 網路的啟動速度。隨著次要 IP 地址池耗盡,CNI 會添加另一個 ENI 來分配更多地址。

ENI 和 IP 地址池的數量通過名為 [WARM_ENI_TARGET、WARM_IP_TARGET、MINIMUM_IP_TARGET](https://github.com/aws/amazon-vpc-cni-k8s/blob/master/docs/eni-and-ip-target.md) 的環境變量進行配置。`aws-node` Daemonset 將定期檢查是否附加了足夠數量的 ENI。當滿足所有 `WARM_ENI_TARGET` 或 `WARM_IP_TARGET` 和 `MINIMUM_IP_TARGET` 條件時,就表示附加了足夠數量的 ENI。如果附加的 ENI 數量不足,CNI 將向 EC2 發出 API 調用以附加更多 ENI,直到達到 `MAX_ENI` 限制為止。

* `WARM_ENI_TARGET` - 整數,值 >0 表示需求已啟用
  * 要維護的熱 ENI 數量。當 ENI 作為次要 ENI 附加到節點但未被任何 Pod 使用時,它就是 "熱" 的。更確切地說,ENI 的 IP 地址尚未與任何 Pod 關聯。
  * 示例:考慮一個實例有 2 個 ENI,每個 ENI 支援 5 個 IP 地址。WARM_ENI_TARGET 設置為 1。如果實例上正好有 5 個 IP 地址被關聯,CNI 將維護 2 個附加到實例的 ENI。第一個 ENI 正在使用中,它的所有 5 個可能的 IP 地址都被使用。第二個 ENI 是 "熱" 的,有 5 個 IP 地址在池中。如果在實例上再啟動另一個 Pod,就需要第 6 個 IP 地址。CNI 將從第二個 ENI 的 5 個 IP 地址池中為第 6 個 Pod 分配一個 IP 地址。第二個 ENI 現在正在使用中,不再處於 "熱" 狀態。CNI 將分配第 3 個 ENI 以維持至少 1 個熱 ENI。

!!! 注意
    熱 ENI 仍然會從 VPC 的 CIDR 中消耗 IP 地址。IP 地址在與工作負載 (如 Pod) 關聯之前是 "未使用" 或 "熱" 的。

* `WARM_IP_TARGET`,整數,值 >0 表示需求已啟用
  * 要維護的熱 IP 地址數量。熱 IP 是在活動附加的 ENI 上可用,但尚未分配給 Pod。換句話說,可用的熱 IP 數量就是可以分配給 Pod 而不需要額外 ENI 的 IP 數量。
  * 示例:考慮一個實例有 1 個 ENI,每個 ENI 支援 20 個 IP 地址。WARM_IP_TARGET 設置為 5。WARM_ENI_TARGET 設置為 0。只有 1 個 ENI 將被附加,直到需要第 16 個 IP 地址。然後,CNI 將附加第二個 ENI,從子網 CIDR 中消耗 20 個可能的地址。
* `MINIMUM_IP_TARGET`,整數,值 >0 表示需求已啟用
  * 任何時候都要分配的最小 IP 地址數量。這通常用於在實例啟動時預先分配多個 ENI。
  * 示例:考慮一個新啟動的實例。它有 1 個 ENI,每個 ENI 支援 10 個 IP 地址。MINIMUM_IP_TARGET 設置為 100。ENI 立即附加 9 個更多的 ENI,總共有 100 個地址。這發生在任何 WARM_IP_TARGET 或 WARM_ENI_TARGET 值之前。

本項目包括一個 [子網計算機 Excel 文檔](../subnet-calc/subnet-calc.xlsx)。該計算機文檔模擬了在不同 ENI 配置選項 (如 `WARM_IP_TARGET` 和 `WARM_ENI_TARGET`) 下指定工作負載的 IP 地址消耗情況。

![說明分配 Pod IP 地址所涉及的組件的插圖](./image-2.png)

當 Kubelet 收到添加 Pod 請求時,CNI 二進制檔案會向 ipamd 查詢可用的 IP 地址,ipamd 隨後會將其提供給 Pod。CNI 二進制檔案連接主機和 Pod 網路。

默認情況下,部署在節點上的 Pod 被分配到與主 ENI 相同的安全組。或者,Pod 也可以配置為使用不同的安全組。

![說明分配 Pod IP 地址所涉及的組件的第二個插圖](./image-3.png)

隨著 IP 地址池的耗盤,插件會自動將另一個彈性網路接口附加到實例上,並為該接口分配另一組次要 IP 地址。這個過程一直持續到節點無法再支援額外的彈性網路接口為止。

![說明分配 Pod IP 地址所涉及的組件的第三個插圖](./image-4.png)

當 Pod 被刪除時,VPC CNI 將 Pod 的 IP 地址放入 30 秒的冷卻緩存中。冷卻緩存中的 IP 不會被分配給新的 Pod。冷卻期結束後,VPC CNI 將 Pod IP 移回熱池。冷卻期可防止 Pod IP 地址過早被回收,並允許所有叢集節點上的 kube-proxy 完成更新 iptables 規則。當 IP 或 ENI 的數量超過熱池設置的數量時,ipamd 插件會將 IP 和 ENI 返回給 VPC。

如上所述,在次要 IP 模式下,每個 Pod 從附加到實例的 ENI 之一獲得一個次要私有 IP 地址。由於每個 Pod 都使用一個 IP 地址,因此您可以在特定 EC2 實例上運行的 Pod 數量取決於可以附加到它的 ENI 數量以及它支援的 IP 地址數量。VPC CNI 檢查 [限制](https://github.com/aws/amazon-vpc-resource-controller-k8s/blob/master/pkg/aws/vpc/limits.go) 檔案以找出每種實例類型允許的 ENI 和 IP 地址數量。

您可以使用以下公式來確定可以在節點上部署的最大 Pod 數量。

`(實例類型的網路接口數量 × (每個網路接口的 IP 地址數量 - 1)) + 2`

+2 表示需要主機網路的 Pod,例如 kube-proxy 和 VPC CNI。Amazon EKS 要求在每個節點上運行 kube-proxy 和 VPC CNI,並將這些要求納入 max-pods 值中。如果您想運行更多主機網路 Pod,請考慮更新 max-pods 值。

+2 表示使用主機網路的 Kubernetes Pod,例如 kube-proxy 和 VPC CNI。Amazon EKS 要求在每個節點上運行 kube-proxy 和 VPC CNI,並將它們計算在 max-pods 中。如果您計劃運行更多主機網路 Pod,請考慮更新 max-pods。您可以在啟動模板的用戶數據中指定 `--kubelet-extra-args "—max-pods=110"`。

例如,在一個有 3 個 c5.large 節點的叢集上 (每個節點 3 個 ENI,每個 ENI 最多 10 個 IP),當叢集啟動並有 2 個 CoreDNS Pod 時,CNI 將消耗 49 個 IP 地址並將它們保留在熱池中。熱池可以加快應用程序部署時的 Pod 啟動速度。

節點 1 (帶 CoreDNS Pod): 2 個 ENI,分配 20 個 IP

節點 2 (帶 CoreDNS Pod): 2 個 ENI,分配 20 個 IP

節點 3 (無 Pod): 1 個 ENI,分配 10 個 IP

請記住,通常作為守護程序集運行的基礎設施 Pod,每個都會佔用 max-pod 計數。這些可能包括:

* CoreDNS
* Amazon 彈性負載均衡器
* 用於指標服務器的操作 Pod

我們建議您通過結合這些 Pod 的容量來規劃您的基礎設施。有關每種實例類型支援的最大 Pod 數量的列表,請參閱 GitHub 上的 [eni-max-Pods.txt](https://github.com/awslabs/amazon-eks-ami/blob/master/files/eni-max-pods.txt)。

![多個 ENI 附加到節點的插圖](./image-5.png)

## 建議

### 部署 VPC CNI 托管附加組件

當您配置叢集時,Amazon EKS 會自動安裝 VPC CNI。不過,Amazon EKS 支援托管附加組件,使叢集能夠與底層 AWS 資源 (如計算、存儲和網路) 交互。我們強烈建議您部署包含 VPC CNI 在內的托管附加組件的叢集。

Amazon EKS 托管附加組件為 Amazon EKS 叢集提供 VPC CNI 安裝和管理。Amazon EKS 附加組件包括最新的安全補丁、錯誤修復,並經 AWS 驗證可與 Amazon EKS 一起使用。VPC CNI 附加組件使您能夠持續確保 Amazon EKS 叢集的安全性和穩定性,並減少安裝、配置和更新附加組件所需的工作量。此外,托管附加組件可以通過 Amazon EKS API、AWS 管理控制台、AWS CLI 和 eksctl 進行添加、更新或刪除。

您可以使用 `kubectl get` 命令的 `--show-managed-fields` 標誌找到 VPC CNI 的托管欄位。

```
kubectl get daemonset aws-node --show-managed-fields -n kube-system -o yaml
```

托管附加組件可以防止配置偏移,每 15 分鐘自動覆蓋一次配置。這意味著在附加組件創建後通過 Kubernetes API 對托管附加組件所做的任何更改都將被自動化的防止偏移過程覆蓋,並且在附加組件更新過程中也會設置為默認值。

由 EKS 管理的欄位列在 managedFields 下,manager 為 EKS。由 EKS 管理的欄位包括服務帳戶、映像、映像 URL、活性探測、就緒探測、標籤、卷和卷掛載。

!!! 信息
最常用的欄位,如 WARM_ENI_TARGET、WARM_IP_TARGET 和 MINIMUM_IP_TARGET 都不受管理,在更新附加組件時也不會被重新調節。對這些欄位的更改將在更新附加組件時得到保留。

我們建議您在生產叢集之前先在非生產叢集中測試特定配置的附加組件行為。此外,請按照 EKS 用戶指南中的步驟進行 [附加組件](https://docs.aws.amazon.com/eks/latest/userguide/eks-add-ons.html) 配置。

#### 遷移到托管附加組件

您將管理自行管理的 VPC CNI 的版本兼容性並更新安全補丁。要更新自行管理的附加組件,您必須使用 Kubernetes API 和 [EKS 用戶指南](https://docs.aws.amazon.com/eks/latest/userguide/managing-vpc-cni.html#updating-vpc-cni-add-on) 中概述的說明。我們建議為現有 EKS 叢集遷移到托管附加組件,並強烈建議在遷移之前備份您當前的 CNI 設置。要配置托管附加組件,您可以使用 Amazon EKS API、AWS 管理控制台或 AWS 命令行界面。

```
kubectl apply view-last-applied daemonset aws-node -n kube-system > aws-k8s-cni-old.yaml
```

如果某個欄位被列為托管欄位,Amazon EKS 將用默認設置替換 CNI 配置設置。我們建議不要修改托管欄位。該附加組件不會重新調節 *熱* 環境變量和 CNI 模式等配置欄位。在您遷移到托管 CNI 時,Pod 和應用程序將繼續運行。

#### 在更新前備份 CNI 設置

VPC CNI 運行在客戶數據平面 (節點) 上,因此 Amazon EKS 在發布新版本或您 [更新叢集](https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html) 到新的 Kubernetes 次要版本後不會自動更新附加組件 (托管和自行管理)。要為現有叢集更新附加組件,您必須通過 update-addon API 或在 EKS 控制台中單擊 update now 鏈接來觸發更新。如果您部署了自行管理的附加組件,請按照 [更新自行管理的 VPC CNI 附加組件](https://docs.aws.amazon.com/eks/latest/userguide/managing-vpc-cni.html#updating-vpc-cni-add-on) 中的步驟操作。

我們強烈建議您一次只更新一個次要版本。例如,如果您當前的次要版本是 `1.9`,而您想要更新到 `1.11`,您應該先更新到 `1.10` 的最新修補版本,然後再更新到 `1.11` 的最新修補版本。

在更新 Amazon VPC CNI 之前,請檢查 aws-node Daemonset。備份現有設置。如果使用托管附加組件,請確認您沒有更新任何 Amazon EKS 可能會覆蓋的設置。我們建議在自動化工作流程中添加一個後更新鉤子,或者在附加組件更新後手動應用。

```
kubectl apply view-last-applied daemonset aws-node -n kube-system > aws-k8s-cni-old.yaml
```

對於自行管理的附加組件,請將備份與 GitHub 上的 `releases` 進行比較,查看可用版本並熟悉您要更新到的版本中的更改。我們建議使用 Helm 來管理自行管理的附加組件,並利用值文件來應用設置。任何涉及 Daemonset 刪除的更新操作都會導致應用程序停機,必須避免。

### 了解安全上下文

我們強烈建議您了解為有效管理 VPC CNI 而配置的安全上下文。Amazon VPC CNI 有兩個組件:CNI 二進制檔案和 ipamd (aws-node) Daemonset。CNI 以二進制檔案的形式運行在節點上,可以訪問節點根檔案系統,並具有特權訪問權限,因為它處理節點級別的 iptables。CNI 二進制檔案由 kubelet 在 Pod 被添加或移除時調用。

aws-node Daemonset 是一個長期運行的進程,負責節點級別的 IP 地址管理。aws-node 在 `hostNetwork` 模式下運行,允許訪問環回設備和同一節點上其他 Pod 的網路活動。aws-node 初始化容器在特權模式下運行,並掛載 CRI 套接字,允許 Daemonset 監控節點上運行的 Pod 的 IP 使用情況。Amazon EKS 正在努力消除 aws-node 初始化容器的特權要求。此外,aws-node 需要更新 NAT 條目並加載 iptables 模組,因此以 NET_ADMIN 權限運行。

Amazon EKS 建議部署 aws-node 清單中定義的安全策略,用於 Pod 的 IP 管理和網路設置。請考慮更新到最新版本的 VPC CNI。此外,如果您有特定的安全要求,請考慮在 [GitHub 上開一個問題](https://github.com/aws/amazon-vpc-cni-k8s/issues)。

### 使用單獨的 IAM 角色進行 CNI

AWS VPC CNI 需要 AWS Identity and Access Management (IAM) 權限。在可以使用 IAM 角色之前,必須設置 CNI 策略。您可以使用 [`AmazonEKS_CNI_Policy`](https://console.aws.amazon.com/iam/home#/policies/arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy%24jsonEditor),這是一個適用於 IPv4 叢集的 AWS 托管策略。AmazonEKS CNI 托管策略只有 IPv4 叢集的權限。您必須為 IPv6 叢集創建一個單獨的 IAM 策略,其中包含 [這裡](https://docs.aws.amazon.com/eks/latest/userguide/cni-iam-role.html#cni-iam-role-create-ipv6-policy) 列出的權限。

默認情況下,VPC CNI 繼承 [Amazon EKS 節點 IAM 角色](https://docs.aws.amazon.com/eks/latest/userguide/create-node-role.html) (包括托管和自行管理的節點組)。

為 Amazon VPC CNI 配置單獨的 IAM 角色並附加相關策略是 **強烈** 建議的。否則,Amazon VPC CNI 的 Pod 將獲得分配給節點的實例配置文件的權限。

VPC CNI 插件創建並配置了一個名為 aws-node 的服務帳戶。默認情況下,該服務帳戶綁定到附加了 Amazon EKS CNI 策略的 Amazon EKS 節點 IAM 角色。要使用單獨的 IAM 角色,我們建議您 [創建一個新的服務帳戶](https://docs.aws.amazon.com/eks/latest/userguide/cni-iam-role.html#cni-iam-role-create-role),並附加 Amazon EKS CNI 策略。要使用新的服務帳戶,您必須 [重新部署 CNI Pod](https://docs.aws.amazon.com/eks/latest/userguide/cni-iam-role.html#cni-iam-role-redeploy-pods)。在創建新叢集時,請考慮為 VPC CNI 托管附加組件指定 `--service-account-role-arn`。請確保從 Amazon EKS 節點角色中刪除 IPv4 和 IPv6 的 Amazon EKS CNI 策略。

建議您 [阻止訪問實例元數據](https://aws.github.io/aws-eks-best-practices/security/docs/iam/#restrict-access-to-the-instance-profile-assigned-to-the-worker-node),以盡量減小安全漏洞的影響範圍。

### 處理活性/就緒探測失敗

我們建議您為 EKS 1.20 及更高版本的叢集增加活性和就緒探測超時值 (默認 `timeoutSeconds: 10`),以防止探測失敗導致您的應用程序的 Pod 陷入 containerCreating 狀態。這個問題已在數據密集型和批處理叢集中看到。高 CPU 使用率會導致 aws-node 探測健康狀況失敗,進而導致未滿足的 Pod CPU 請求。除了修改探測超時外,還要確保 aws-node 的 CPU 資源請求 (默認 `CPU: 25m`) 配置正確。我們不建議在節點沒有問題的情況下更新這些設置。

我們強烈建議您在節點上運行 `sudo bash /opt/cni/bin/aws-cni-support.sh`,同時與 Amazon EKS 支持部門聯繫。該腳本將協助評估 kubelet 日誌和節點上的內存使用情況。請考慮在 Amazon EKS 工作節點上安裝 SSM Agent 以運行該腳本。

### 在非 EKS 優化 AMI 實例上配置 IPTables 轉發策略

如果您使用自定義 AMI,請確保將 iptables 轉發策略設置為 [kubelet.service](https://github.com/awslabs/amazon-eks-ami/blob/master/files/kubelet.service#L8) 下的 ACCEPT。許多系統將 iptables 轉發策略設置為 DROP。您可以使用 [HashiCorp Packer](https://packer.io/intro/why.html) 和 [AWS GitHub 上的 Amazon EKS AMI 存儲庫](https://github.com/awslabs/amazon-eks-ami) 中的資源和配置腳本構建自定義 AMI。您可以更新 [kubelet.service](https://github.com/awslabs/amazon-eks-ami/blob/master/files/kubelet.service#L8),並按照 [這裡](https://aws.amazon.com/premiumsupport/knowledge-center/eks-custom-linux-ami/) 指定的說明創建自定義 AMI。

### 定期升級 CNI 版本

VPC CNI 向後兼容。最新版本可與所有 Amazon EKS 支持的 Kubernetes 版本一起使用。此外,VPC CNI 作為 EKS 附加組件提供 (參見上面的 "部署 VPC CNI 托管附加組件")。雖然 EKS 附加組件協調升級附加組件,但它不會自動升級像 CNI 這樣運行在數據平面上的附加組件。您有責任在托管和自行管理的工作節點升級後升級 VPC CNI 附加組件。
