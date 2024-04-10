# 每個 Pod 的安全群組

AWS 安全群組就像是 EC2 執行個體的虛擬防火牆,用來控制進出流量。預設情況下,Amazon VPC CNI 會使用與節點上主要 ENI 相關聯的安全群組。更具體地說,與執行個體相關聯的每個 ENI 都會有相同的 EC2 安全群組。因此,在節點上運行的每個 Pod 都共用與該節點相同的安全群組。

如下圖所示,運行在工作節點上的所有應用程式 Pod 都可以訪問 RDS 資料庫服務(假設 RDS 入站允許節點安全群組)。安全群組太過粗糙,因為它們適用於在節點上運行的所有 Pod。Pod 的安全群組為工作負載提供了網路隔離,這是良好深度防禦策略的重要組成部分。

![節點與安全群組連接到 RDS 的插圖](./image.png)

使用 Pod 的安全群組,您可以通過在共享計算資源上運行具有不同網路安全要求的應用程式來提高計算效率。可以在一個地方使用 EC2 安全群組定義多種安全規則,例如 Pod 到 Pod 和 Pod 到外部 AWS 服務,並使用 Kubernetes 原生 API 將其應用於工作負載。下圖顯示了在 Pod 級別應用的安全群組,以及它們如何簡化您的應用程式部署和節點架構。Pod 現在可以訪問 Amazon RDS 資料庫。

![Pod 和節點與不同安全群組連接到 RDS 的插圖](./image-2.png)

您可以通過將 `ENABLE_POD_ENI=true` 設置為 VPC CNI 來啟用 Pod 的安全群組。啟用後,由 EKS 管理的控制平面上運行的 "[VPC 資源控制器](https://github.com/aws/amazon-vpc-resource-controller-k8s)"會創建並將一個稱為"aws-k8s-trunk-eni"的幹線介面附加到節點。幹線介面充當附加到實例的標準網路介面。要管理幹線介面,您必須將 `AmazonEKSVPCResourceController` 受管政策添加到與您的 Amazon EKS 集群相關聯的集群角色。

控制器還會創建名為"aws-k8s-branch-eni"的分支介面,並將它們與幹線介面相關聯。Pod 使用 [SecurityGroupPolicy](https://github.com/aws/amazon-vpc-resource-controller-k8s/blob/master/config/crd/bases/vpcresources.k8s.aws_securitygrouppolicies.yaml) 自定義資源分配安全群組,並與分支介面相關聯。由於安全群組是與網路介面指定的,因此我們現在能夠在這些額外的網路介面上調度需要特定安全群組的 Pod。請查看 [EKS 用戶指南中關於 Pod 的安全群組部分](https://docs.aws.amazon.com/eks/latest/userguide/security-groups-for-pods.html),包括部署先決條件。

![工作子網與關聯 ENI 的安全群組的插圖](./image-3.png)

分支介面容量是 *附加* 到現有實例類型的次要 IP 地址限制。使用安全群組的 Pod 不計入 max-pods 公式中,當您為 Pod 使用安全群組時,您需要考慮提高 max-pods 值或滿足於運行比節點實際支持的更少 Pod。

m5.large 最多可以有 9 個分支網路介面,並且最多可以為其標準網路介面分配 27 個次要 IP 地址。如下例所示,m5.large 的預設 max-pods 為 29,EKS 將使用安全群組的 Pod 計入最大 Pod 數。請參閱 [EKS 用戶指南](https://docs.aws.amazon.com/eks/latest/userguide/cni-increase-ip-addresses.html) 瞭解如何更改節點的 max-pods 的說明。

當 Pod 的安全群組與 [自定義網路](https://docs.aws.amazon.com/eks/latest/userguide/cni-custom-network.html) 結合使用時,將使用 Pod 的安全群組中定義的安全群組,而不是在 ENIConfig 中指定的安全群組。因此,啟用自定義網路時,在使用每個 Pod 的安全群組時,請仔細評估安全群組排序。

## 建議

### 為活性探測禁用 TCP 早期解除

如果您使用活性或就緒探測,您還需要禁用 TCP 早期解除,以便 kubelet 可以通過 TCP 連接到分支網路介面上的 Pod。這僅在嚴格模式下需要。要執行此操作,請運行以下命令:

```
kubectl edit daemonset aws-node -n kube-system
```

在 `initContainer` 部分,將 `DISABLE_TCP_EARLY_DEMUX` 的值更改為 `true`。

### 使用 Pod 的安全群組來利用現有的 AWS 配置投資

安全群組可以更容易地限制對 VPC 資源(如 RDS 資料庫或 EC2 實例)的網路訪問。Pod 的安全群組的一個明顯優勢是可以重用現有的 AWS 安全群組資源。
如果您使用安全群組作為網路防火牆來限制對您的 AWS 服務的訪問,我們建議使用分支 ENI 將安全群組應用於 Pod。如果您正在將應用程式從 EC2 實例轉移到 EKS,並使用安全群組限制對其他 AWS 服務的訪問,請考慮使用 Pod 的安全群組。

### 配置 Pod 安全群組強制模式

Amazon VPC CNI 插件版本 1.11 增加了一個名為 `POD_SECURITY_GROUP_ENFORCING_MODE`("強制模式")的新設置。強制模式控制應用於 Pod 的安全群組,以及是否啟用源 NAT。您可以將強制模式指定為嚴格或標準。嚴格是預設值,反映了之前將 `ENABLE_POD_ENI` 設置為 `true` 時 VPC CNI 的行為。

在嚴格模式下,僅強制執行分支 ENI 安全群組。源 NAT 也被禁用。

在標準模式下,與主 ENI 和與 Pod 關聯的分支 ENI 相關聯的安全群組都會被應用。網路流量必須符合這兩個安全群組。

!!! 警告
    任何模式更改只會影響新啟動的 Pod。現有 Pod 將使用創建 Pod 時配置的模式。如果客戶想要更改流量行為,他們需要重新啟動具有安全群組的現有 Pod。

### 強制模式:使用嚴格模式隔離 Pod 和節點流量:

預設情況下,Pod 的安全群組設置為"嚴格模式"。如果您必須完全分離 Pod 流量和節點的其餘流量,請使用此設置。在嚴格模式下,源 NAT 被關閉,因此可以使用分支 ENI 出站安全群組。

!!! 警告
    啟用嚴格模式時,Pod 的所有出站流量都將離開節點並進入 VPC 網路。同一節點上的 Pod 之間的流量將通過 VPC。這增加了 VPC 流量,並限制了基於節點的功能。NodeLocal DNSCache 不支持嚴格模式。

### 強制模式:在以下情況下使用標準模式

**客戶端源 IP 對 Pod 中的容器可見**

如果您需要讓客戶端源 IP 對 Pod 中的容器可見,請考慮將 `POD_SECURITY_GROUP_ENFORCING_MODE` 設置為 `standard`。Kubernetes 服務支持 externalTrafficPolicy=local 以保留客戶端源 IP(預設類型集群)。您現在可以在標準模式下運行 externalTrafficPolicy 設置為 Local 的 NodePort 和 LoadBalancer 類型的 Kubernetes 服務。`Local` 保留客戶端源 IP,並避免了 LoadBalancer 和 NodePort 類型服務的第二跳。

**部署 NodeLocal DNSCache**

使用 Pod 的安全群組時,請配置標準模式以支持使用 [NodeLocal DNSCache](https://kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/) 的 Pod。NodeLocal DNSCache 通過在集群節點上作為 DaemonSet 運行 DNS 緩存代理,提高了集群 DNS 性能。這將有助於具有最高 DNS QPS 需求的 Pod 查詢本地 kube-dns/CoreDNS,擁有本地緩存,從而改善延遲。

NodeLocal DNSCache 不支持嚴格模式,因為所有網路流量(即使是到節點的流量)都進入 VPC。

**支持 Kubernetes 網路策略**

使用與 Pod 關聯的安全群組時,我們建議使用標準強制模式。

我們強烈建議利用 Pod 的安全群組來限制對不屬於集群的 AWS 服務的網路級訪問。考慮使用網路策略來限制集群內部的 Pod 之間的網路流量,通常稱為東西向流量。

### 識別與 Pod 的安全群組不兼容的情況

基於 Windows 和非 nitro 實例不支持 Pod 的安全群組。要使用 Pod 的安全群組,實例必須標記為 isTrunkingEnabled。如果您的 Pod 不依賴 VPC 內或外部的任何 AWS 服務,請使用網路策略而不是安全群組來管理 Pod 之間的訪問。

### 使用 Pod 的安全群組有效控制對 AWS 服務的流量

如果在 EKS 集群內運行的應用程式需要與 VPC 內的另一個資源(例如 RDS 資料庫)通信,則請考慮使用 Pod 的安全群組。雖然有一些策略引擎允許您指定 CIDR 或 DNS 名稱,但當與具有位於 VPC 內的端點的 AWS 服務通信時,它們不是最佳選擇。

相反,Kubernetes [網路策略](https://kubernetes.io/docs/concepts/services-networking/network-policies/)提供了一種控制集群內外進出流量的機制。如果您的應用程式對其他 AWS 服務的依賴有限,應該考慮 Kubernetes 網路策略。您可以配置基於 CIDR 範圍的網路策略來限制對 AWS 服務的訪問,而不是使用 AWS 本機語義(如安全群組)。您可以使用 Kubernetes 網路策略來控制 Pod 之間(通常稱為東西向流量)以及 Pod 和外部服務之間的網路流量。Kubernetes 網路策略在 OSI 第 3 和第 4 層實現。

Amazon EKS 允許您使用網路策略引擎,如 [Calico](https://projectcalico.docs.tigera.io/getting-started/kubernetes/managed-public-cloud/eks) 和 [Cilium](https://docs.cilium.io/en/stable/intro/)。預設情況下,網路策略引擎未安裝。請查看各自的安裝指南,瞭解設置說明。有關如何使用網路策略的更多信息,請參閱 [EKS 安全最佳實踐](https://aws.github.io/aws-eks-best-practices/security/docs/network/#network-policy)。DNS 主機名功能可在網路策略引擎的企業版中使用,對於控制 Kubernetes 服務/Pod 與 AWS 之外運行的資源之間的流量可能很有用。此外,對於預設不支持安全群組的 AWS 服務,您也可以考慮 DNS 主機名支持。

### 為使用 AWS Loadbalancer 控制器標記單個安全群組

當許多安全群組分配給一個 Pod 時,Amazon EKS 建議使用 [`kubernetes.io/cluster/$name`](http://kubernetes.io/cluster/$name) 標記單個共享或擁有的安全群組。該標記允許 AWS Loadbalancer 控制器更新安全群組的規則,以路由流量到 Pod。如果只給 Pod 分配了一個安全群組,則標記是可選的。安全群組中設置的權限是累加的,因此標記單個安全群組就足以讓負載均衡器控制器定位和協調規則。它還有助於遵守安全組定義的 [預設配額](https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html#vpc-limits-security-groups)。

### 為出站流量配置 NAT

從分配了安全群組的 Pod 的出站流量被禁用源 NAT。對於需要訪問互聯網的使用安全群組的 Pod,請在配置了 NAT 網關或實例的私有子網上啟動工作節點,並在 CNI 中啟用 [外部 SNAT](https://docs.aws.amazon.com/eks/latest/userguide/external-snat.html)。

```
kubectl set env daemonset -n kube-system aws-node AWS_VPC_K8S_CNI_EXTERNALSNAT=true
```

### 將具有安全群組的 Pod 部署到私有子網

分配了安全群組的 Pod 必須在部署到私有子網的節點上運行。請注意,部署到公共子網的分配了安全群組的 Pod 將無法訪問互聯網。

### 驗證 Pod 規範文件中的 *terminationGracePeriodSeconds*

確保在您的 Pod 規範文件中 `terminationGracePeriodSeconds` 為非零(預設為 30 秒)。這對於 Amazon VPC CNI 從工作節點刪除 Pod 網路來說是必需的。當設置為零時,CNI 插件不會從主機移除 Pod 網路,分支 ENI 也不會有效清除。

### 將 Pod 的安全群組與 Fargate 一起使用

在 Fargate 上運行的 Pod 的安全群組的工作方式與在 EC2 工作節點上運行的 Pod 非常相似。例如,您必須在將其引用到與您的 Fargate Pod 關聯的 SecurityGroupPolicy 之前創建安全群組。預設情況下,當您沒有明確為 Fargate Pod 分配 SecurityGroupPolicy 時,[集群安全群組](https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html) 將分配給所有 Fargate Pod。為了簡單起見,您可能希望將集群安全群組添加到 Fagate Pod 的 SecurityGroupPolicy 中,否則您將不得不將最小安全群組規則添加到您的安全群組中。您可以使用 describe-cluster API 找到集群安全群組。

```bash
 aws eks describe-cluster --name CLUSTER_NAME --query 'cluster.resourcesVpcConfig.clusterSecurityGroupId'
```

```bash
cat >my-fargate-sg-policy.yaml <<EOF
apiVersion: vpcresources.k8s.aws/v1beta1
kind: SecurityGroupPolicy
metadata:
  name: my-fargate-sg-policy
  namespace: my-fargate-namespace
spec:
  podSelector: 
    matchLabels:
      role: my-fargate-role
  securityGroups:
    groupIds:
      - cluster_security_group_id
      - my_fargate_pod_security_group_id
EOF
```

最小安全群組規則在[這裡](https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html)列出。這些規則允許 Fargate Pod 與集群內服務(如 kube-apiserver、kubelet 和 CoreDNS)通信。您還需要添加規則以允許與您的 Fargate Pod 的入站和出站連接。這將允許您的 Pod 與您的 VPC 中的其他 Pod 或資源通信。此外,您還需要包括規則,以便 Fargate 可以從 Amazon ECR 或其他容器註冊表(如 DockerHub)拉取容器映像。有關更多信息,請參閱 [AWS 通用參考](https://docs.aws.amazon.com/general/latest/gr/aws-ip-ranges.html)中的 AWS IP 地址範圍。

您可以使用以下命令找到應用於 Fargate Pod 的安全群組。

```bash
kubectl get pod FARGATE_POD -o jsonpath='{.metadata.annotations.vpc\.amazonaws\.com/pod-eni}{"\n"}'
```

請記下上面命令中的 eniId。

```bash
aws ec2 describe-network-interfaces --network-interface-ids ENI_ID --query 'NetworkInterfaces[*].Groups[*]'
```

必須刪除並重新創建現有的 Fargate Pod,新的安全群組才能應用。例如,以下命令將啟動 example-app 的部署。要更新特定 Pod,您可以在下面的命令中更改命名空間和部署名稱。

```bash
kubectl rollout restart -n example-ns deployment example-pod
```