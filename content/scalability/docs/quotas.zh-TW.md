# 已知限制和服務配額
Amazon EKS 可用於各種工作負載,並可與廣泛的 AWS 服務互動,我們已看到客戶工作負載遇到類似範圍的 AWS 服務配額和其他問題,這些問題會阻礙可擴展性。

您的 AWS 帳戶有預設配額(您的團隊可以請求的每種 AWS 資源的上限)。每個 AWS 服務都定義了自己的配額,而且配額通常是特定於區域的。您可以請求增加某些配額(軟性限制),而其他配額則無法增加(硬性限制)。在設計您的應用程式時,您應該考慮這些值。定期審查這些服務限制,並在應用程式設計中納入它們。

您可以在 [AWS 服務配額主控台](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-resource-limits.html#request-increase)審查您帳戶的使用情況並開啟配額增加請求,或使用 [AWS CLI](https://repost.aws/knowledge-center/request-service-quota-increase-cli)。請參閱各 AWS 服務的 AWS 文件,以瞭解更多有關服務配額的詳細資訊,以及任何進一步的限制或增加通知。

!!! 注意
    [Amazon EKS 服務配額](https://docs.aws.amazon.com/eks/latest/userguide/service-quotas.html)列出了服務配額,並提供了可用於請求增加的連結。

## 其他 AWS 服務配額
我們已看到 EKS 客戶受到下列其他 AWS 服務的配額影響。其中一些可能僅適用於特定使用案例或配置,但是您可能會考慮您的解決方案在擴展時是否會遇到任何這些情況。配額按服務組織,每個配額都有格式為 L-XXXXXXXX 的 ID,您可以在 [AWS 服務配額主控台](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-resource-limits.html#request-increase)中查找。

| 服務           | 配額 (L-xxxxx)                                                                            | **影響**                                                                                                         | **ID (L-xxxxx)** | 預設值  |
| -------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ | ---------------- | ------- |
| IAM            | 每個帳戶的角色數                                                                          | 可限制帳戶中的叢集或 IRSA 角色數量。                                                                              | L-FE177D64       | 1,000   |
| IAM            | 每個帳戶的 OpenId Connect 提供者數                                                       | 可限制每個帳戶的叢集數量,IRSA 使用 OpenID Connect                                                                | L-858F3967       | 100     |
| IAM            | 角色信任政策長度                                                                         | 可限制 IAM 角色與 IRSA 相關聯的叢集數量                                                                          | L-C07B4B0D       | 2,048   |
| VPC            | 每個網路介面的安全群組數                                                                  | 可限制叢集網路的控制或連線能力                                                                                   | L-2AFB9258       | 5       |
| VPC            | 每個 VPC 的 IPv4 CIDR 區塊數                                                               | 可限制 EKS Worker Node 的數量                                                                                    | L-83CA0A9D       | 5       |
| VPC            | 每個路由表的路由數                                                                        | 可限制叢集網路的控制或連線能力                                                                                   | L-93826ACB       | 50      |
| VPC            | 每個 VPC 的活動 VPC 對等連線數                                                             | 可限制叢集網路的控制或連線能力                                                                                   | L-7E9ECCDB       | 50      |
| VPC            | 每個安全群組的入站或出站規則數。                                                          | 可限制叢集網路的控制或連線能力,EKS 中的某些控制器會建立新規則                                                   | L-0EA8095F       | 50      |
| VPC            | 每個區域的 VPC 數                                                                         | 可限制每個帳戶的叢集數量或叢集網路的控制或連線能力                                                               | L-F678F1CE       | 5       |
| VPC            | 每個區域的網際網路閘道數                                                                  | 可限制每個帳戶的叢集數量或叢集網路的控制或連線能力                                                               | L-A4707A72       | 5       |
| VPC            | 每個區域的網路介面數                                                                      | 可限制 EKS Worker Node 的數量,或影響 EKS 控制平面的擴展/更新活動。                                              | L-DF5E4CA3       | 5,000   |
| VPC            | 網路位址使用量                                                                            | 可限制每個帳戶的叢集數量或叢集網路的控制或連線能力                                                               | L-BB24F6E5       | 64,000  |
| VPC            | 對等網路位址使用量                                                                        | 可限制每個帳戶的叢集數量或叢集網路的控制或連線能力                                                               | L-CD17FD4B       | 128,000 |
| ELB            | 每個網路負載平衡器的監聽器數                                                              | 可限制進入叢集的流量控制。                                                                                       | L-57A373D6       | 50      |
| ELB            | 每個區域的目標群組數                                                                      | 可限制進入叢集的流量控制。                                                                                       | L-B22855CB       | 3,000   |
| ELB            | 每個應用程式負載平衡器的目標數                                                            | 可限制進入叢集的流量控制。                                                                                       | L-7E6692B2       | 1,000   |
| ELB            | 每個網路負載平衡器的目標數                                                                | 可限制進入叢集的流量控制。                                                                                       | L-EEF1AD04       | 3,000   |
| ELB            | 每個可用區域每個網路負載平衡器的目標數                                                    | 可限制進入叢集的流量控制。                                                                                       | L-B211E961       | 500     |
| ELB            | 每個區域每個目標群組的目標數                                                              | 可限制進入叢集的流量控制。                                                                                       | L-A0D0B863       | 1,000   |
| ELB            | 每個區域的應用程式負載平衡器數                                                            | 可限制進入叢集的流量控制。                                                                                       | L-53DA6B97       | 50      |
| ELB            | 每個區域的傳統負載平衡器數                                                                | 可限制進入叢集的流量控制。                                                                                       | L-E9E9831D       | 20      |
| ELB            | 每個區域的網路負載平衡器數                                                                | 可限制進入叢集的流量控制。                                                                                       | L-69A177A2       | 50      |
| EC2            | 正在執行的隨需標準 (A、C、D、H、I、M、R、T、Z) 實例 (以最大 vCPU 計數)                  | 可限制 EKS Worker Node 的數量                                                                                   | L-1216C47A       | 5       |
| EC2            | 所有標準 (A、C、D、H、I、M、R、T、Z) 現貨實例請求 (以最大 vCPU 計數)                    | 可限制 EKS Worker Node 的數量                                                                                   | L-34B43A08       | 5       |
| EC2            | EC2-VPC 彈性 IP                                                                          | 可限制 NAT 閘道 (和 VPC) 的數量,從而可能限制區域中的叢集數量                                                    | L-0263D0A3       | 5       |
| EBS            | 每個區域的快照數                                                                          | 可限制有狀態工作負載的備份策略                                                                                   | L-309BACF6       | 100,000 |
| EBS            | 通用 SSD (gp3) 磁碟區的儲存空間,以 TiB 為單位                                             | 可限制 EKS Worker Node 的數量或 PersistentVolume 儲存空間                                                       | L-7A658B76       | 50      |
| EBS            | 通用 SSD (gp2) 磁碟區的儲存空間,以 TiB 為單位                                             | 可限制 EKS Worker Node 的數量或 PersistentVolume 儲存空間                                                       | L-D18FCD1D       | 50      |
| ECR            | 已註冊的儲存庫                                                                            | 可限制叢集中的工作負載數量                                                                                       | L-CFEB8E8D       | 10,000  |
| ECR            | 每個儲存庫的映像數                                                                        | 可限制叢集中的工作負載數量                                                                                       | L-03A36CE1       | 10,000  |
| SecretsManager | 每個區域的密碼數                                                                         | 可限制叢集中的工作負載數量                                                                                       | L-2F66C23C       | 500,000 |

## AWS 請求節流
AWS 服務還實施了請求節流,以確保它們對所有客戶保持高效和可用。與服務配額類似,每個 AWS 服務都維護自己的請求節流閾值。如果您的工作負載需要快速發出大量 API 呼叫或您的應用程式出現請求節流錯誤,請考慮審查各 AWS 服務的相關文件。

在大型叢集中或叢集大幅擴展時,與佈建 EC2 網路介面或 IP 位址相關的 EC2 API 請求可能會遇到請求節流。下表顯示了我們看到客戶遇到請求節流的一些 API 操作。
您可以在 [EC2 文件中關於速率限制](https://docs.aws.amazon.com/AWSEC2/latest/APIReference/throttling.html)的部分查看 EC2 速率限制預設值和請求增加速率限制的步驟。

| 可變更操作                     | 唯讀操作                       |
| ------------------------------- | ------------------------------- |
| AssignPrivateIpAddresses        | DescribeDhcpOptions             |
| AttachNetworkInterface          | DescribeInstances               |
| CreateNetworkInterface          | DescribeNetworkInterfaces       |
| DeleteNetworkInterface          | DescribeSecurityGroups          |
| DeleteTags                      | DescribeTags                    |
| DetachNetworkInterface          | DescribeVpcs                    |
| ModifyNetworkInterfaceAttribute | DescribeVolumes                 |
| UnassignPrivateIpAddresses      |                     |

## 其他已知限制

* Route 53 DNS 解析器每秒限制為 [1024 個封包](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-dns.html#vpc-dns-limits)。當來自大型叢集的 DNS 流量通過少量的 CoreDNS Pod 副本時,可能會遇到此限制。[擴展 CoreDNS 和優化 DNS 行為](../cluster-services/#scale-coredns)可避免 DNS 查詢超時。
    * [Route 53 對 Route 53 API 的速率限制也相當低,為每秒 5 個請求](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/DNSLimitations.html#limits-api-requests)。如果您有大量域名需要使用 External DNS 等專案更新,您可能會看到速率節流和延遲更新域名。

* 某些 [Nitro 實例類型的磁碟區連接限制為 28](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/volume_limits.html#instance-type-volume-limits),這是 Amazon EBS 磁碟區、網路介面和 NVMe 實例存儲磁碟區共用的限制。如果您的工作負載掛載了大量 EBS 磁碟區,您可能會遇到無法在這些實例類型上實現高 Pod 密度的限制。

* 每個 Ec2 實例可以追蹤的連線數有上限。[如果您的工作負載處理大量連線,您可能會看到通訊失敗或錯誤,因為已達到此上限。](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-connection-tracking.html#connection-tracking-throttling)您可以使用 `conntrack_allowance_available` 和 `conntrack_allowance_exceeded` [網路效能指標來監控您的 EKS Worker Node 上追蹤的連線數](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/monitoring-network-performance-ena.html)。

* 在 EKS 環境中,etcd 儲存空間限制為 **8 GiB**,這是根據 [上游指引](https://etcd.io/docs/v3.5/dev-guide/limit/#storage-size-limit)。請監控指標 `etcd_db_total_size_in_bytes` 來追蹤 etcd 資料庫大小。您可以參考 [警報規則](https://github.com/etcd-io/etcd/blob/main/contrib/mixin/mixin.libsonnet#L213-L240) `etcdBackendQuotaLowSpace` 和 `etcdExcessiveDatabaseGrowth` 來設置此監控。