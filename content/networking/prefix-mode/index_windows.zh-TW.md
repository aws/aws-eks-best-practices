# Windows 的前綴模式
在 Amazon EKS 中，預設會由 [VPC 資源控制器](https://github.com/aws/amazon-vpc-resource-controller-k8s) 為每個在 Windows 主機上運行的 Pod 分配一個次要 IP 位址。這個 IP 位址是從主機的子網路中分配的 VPC 可路由位址。在 Linux 上，連接到實例的每個 ENI 都有多個可以填入次要 IP 位址或 /28 CIDR (前綴) 的插槽。然而，Windows 主機只支援單一 ENI 及其可用插槽。僅使用次要 IP 位址可能會人為地限制您在 Windows 主機上可以運行的 Pod 數量，即使有大量可分配的 IP 位址。

為了增加 Windows 主機上的 Pod 密度，尤其是在使用較小的實例類型時，您可以為 Windows 節點啟用 **前綴委派**。啟用前綴委派後，會將 /28 IPv4 前綴而非次要 IP 位址分配給 ENI 插槽。可以透過在 `amazon-vpc-cni` 設定對映中新增 `enable-windows-prefix-delegation: "true"` 條目來啟用前綴委派。這與您需要設定 `enable-windows-ipam: "true"` 條目以啟用 Windows 支援的設定對映相同。

請遵循 [EKS 使用者指南](https://docs.aws.amazon.com/eks/latest/userguide/cni-increase-ip-addresses.html) 中提到的說明，為 Windows 節點啟用前綴委派模式。

![illustration of two worker subnets, comparing ENI secondary IPvs to ENIs with delegated prefixes](./windows-1.jpg)

圖: 次要 IP 模式與前綴委派模式的比較

您可以指派給網路介面的 IP 位址數量上限取決於實例類型和大小。每個指派給網路介面的前綴都會佔用一個可用插槽。例如，`c5.large` 實例每個網路介面的限制為 `10` 個插槽。網路介面的第一個插槽始終由介面的主要 IP 位址佔用，因此您只剩下 9 個插槽可用於前綴和/或次要 IP 位址。如果這些插槽被指派前綴，節點可以支援 (9 * 16) 144 個 IP 位址，而如果被指派次要 IP 位址，則只能支援 9 個 IP 位址。請參閱 [每個實例類型的網路介面 IP 位址](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html#AvailableIpPerENI) 和 [將前綴指派給網路介面](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-prefix-eni.html) 的文件，以獲取更多資訊。

在工作節點初始化期間，VPC 資源控制器會將一個或多個前綴指派給主要 ENI，以透過維護一個暖池的 IP 位址來加快 Pod 啟動速度。可以透過在 `amazon-vpc-cni` 設定對映中設定以下設定參數來控制暖池中要保留的前綴數量。

* `warm-prefix-target`，超出目前需求而分配的前綴數量。
* `warm-ip-target`，超出目前需求而分配的 IP 位址數量。
* `minimum-ip-target`，任何時候都必須可用的最小 IP 位址數量。
* 如果設定了 `warm-ip-target` 和/或 `minimum-ip-target`，將會覆蓋 `warm-prefix-target`。

當更多 Pod 被排程到節點上時，將會為現有 ENI 要求額外的前綴。當 Pod 被排程到節點上時，VPC 資源控制器會首先嘗試從節點上現有的前綴中指派一個 IPv4 位址。如果這不可行，只要子網路有足夠的容量，就會要求新的 IPv4 前綴。

![flow chart of procedure for assigning IP to pod](./windows-2.jpg)

圖: 為 Pod 指派 IPv4 位址的工作流程

## 建議
### 何時使用前綴委派
如果您在工作節點上遇到 Pod 密度問題，請使用前綴委派。為避免發生錯誤，我們建議在遷移到前綴模式之前，檢查子網路是否有連續的 /28 前綴位址區塊。請參考 "[使用子網路保留以避免子網路碎片化 (IPv4)](https://docs.aws.amazon.com/vpc/latest/userguide/subnet-cidr-reservation.html)" 一節的子網路保留詳細資訊。

預設情況下，Windows 節點的 `max-pods` 設定為 `110`。對於絕大多數實例類型而言，這應該已經足夠。如果您想增加或減少此限制，請在使用者資料中的啟動命令中新增以下內容:
```
-KubeletExtraArgs '--max-pods=example-value'
```
有關 Windows 節點的啟動設定參數的更多詳細資訊，請造訪[這裡](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-windows-ami.html#bootstrap-script-configuration-parameters)的文件。

### 何時避免使用前綴委派
如果您的子網路非常碎片化且沒有足夠的可用 IP 位址來建立 /28 前綴，請避免使用前綴模式。如果產生前綴的子網路碎片化 (大量使用且散佈著次要 IP 位址的子網路)，則前綴附加可能會失敗。您可以透過建立新的子網路並保留前綴來避免此問題。

### 設定前綴委派的參數以節省 IPv4 位址
`warm-prefix-target`、`warm-ip-target` 和 `minimum-ip-target` 可用於微調使用前綴時的預先調整和動態調整行為。預設會使用以下值:
```
warm-ip-target: "1"
minimum-ip-target: "3"
```
透過微調這些設定參數，您可以在節省 IP 位址和確保減少 IP 位址指派延遲之間達到最佳平衡。有關這些設定參數的更多資訊，請造訪[這裡](https://github.com/aws/amazon-vpc-resource-controller-k8s/blob/master/docs/windows/prefix_delegation_config_options.md)的文件。

### 使用子網路保留以避免子網路碎片化 (IPv4)
當 EC2 將 /28 IPv4 前綴分配給 ENI 時，必須是來自您子網路的連續 IP 位址區塊。如果產生前綴的子網路碎片化 (大量使用且散佈著次要 IP 位址的子網路)，則前綴附加可能會失敗，您將看到以下節點事件:
```
InsufficientCidrBlocks: The specified subnet does not have enough free cidr blocks to satisfy the request
```
為了避免碎片化並有足夠的連續空間來建立前綴，請使用 [VPC 子網路 CIDR 保留](https://docs.aws.amazon.com/vpc/latest/userguide/subnet-cidr-reservation.html#work-with-subnet-cidr-reservations)來保留子網路內專供前綴使用的 IP 空間。建立保留後，保留區塊中的 IP 位址將不會被指派給其他資源。這樣一來，VPC 資源控制器就能在將前綴指派給節點 ENI 時獲得可用的前綴。

建議您建立新的子網路、保留前綴的空間，並為在該子網路中運行的工作節點啟用前綴指派。如果新的子網路僅專用於在您的 EKS 叢集中運行且已啟用前綴委派的 Pod，則您可以跳過前綴保留步驟。

### 在次要 IP 模式與前綴委派模式之間遷移時替換所有節點
強烈建議您建立新的節點群組來增加可用的 IP 位址數量，而不是對現有工作節點進行滾動替換。

使用自行管理的節點群組時，轉換的步驟如下:

* 增加叢集的容量，以便新節點能夠容納您的工作負載
* 啟用/停用 Windows 的前綴委派功能
* 隔離並清空所有現有節點以安全地逐出所有現有 Pod。為了防止服務中斷，我們建議在生產叢集上為關鍵工作負載實作 [Pod 中斷預算](https://kubernetes.io/docs/tasks/run-application/configure-pdb)。
* 確認 Pod 在運行後，您可以刪除舊節點和節點群組。新節點上的 Pod 將從指派給節點 ENI 的前綴獲得 IPv4 位址。

使用受管理的節點群組時，轉換的步驟如下:

* 啟用/停用 Windows 的前綴委派功能
* 使用[這裡](https://docs.aws.amazon.com/eks/latest/userguide/update-managed-node-group.html)提到的步驟更新節點群組。這會執行類似上述但由 EKS 管理的步驟。

!!! warning
    在同一模式下運行節點上的所有 Pod

對於 Windows，我們建議您避免同時在次要 IP 模式和前綴委派模式下運行 Pod。當您從次要 IP 模式遷移到前綴委派模式或反之亦然時，可能會出現這種情況，而且有運行中的 Windows 工作負載。

雖然這不會影響您正在運行的 Pod，但節點的 IP 位址容量可能會不一致。例如，考慮一個 t3.xlarge 節點，它有 14 個插槽可用於次要 IPv4 位址。如果您正在運行 10 個 Pod，則 ENI 上的 10 個插槽將被次要 IP 位址佔用。啟用前綴委派後，向 kube-api 伺服器公佈的容量將是 (14 個插槽 * 每個前綴 16 個 IP 位址) 244，但當時的實際容量將是 (剩餘 4 個插槽 * 每個前綴 16 個位址) 64。公佈的容量量與實際剩餘容量 (剩餘插槽) 之間的不一致可能會導致在沒有可用於指派的 IP 位址的情況下運行更多 Pod。

儘管如此，您可以使用上述遷移策略來安全地將您的 Pod 從次要 IP 位址轉換為從前綴獲得的位址。在切換模式時，Pod 將繼續正常運行，並且:

* 從次要 IP 模式切換到前綴委派模式時，不會釋放分配給正在運行的 Pod 的次要 IP 位址。前綴將被分配給空閒插槽。一旦 Pod 終止，它所使用的次要 IP 和插槽將被釋放。
* 從前綴委派模式切換到次要 IP 模式時，如果前綴範圍內的所有 IP 都未分配給 Pod，則該前綴將被釋放。如果前綴中的任何 IP 被分配給 Pod，則該前綴將被保留直到 Pod 終止。

### 除錯前綴委派問題
您可以使用我們的[這裡](https://github.com/aws/amazon-vpc-resource-controller-k8s/blob/master/docs/troubleshooting.md)的除錯指南深入了解您在 Windows 上使用前綴委派時遇到的問題。