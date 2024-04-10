# 監控 EKS 工作負載的網路效能問題

## 監控 CoreDNS 流量以檢測 DNS 節流問題

運行 DNS 密集型工作負載有時會因 DNS 節流而導致間歇性的 CoreDNS 故障,這可能會影響應用程式,您可能會遇到偶爾的 UnknownHostException 錯誤。

CoreDNS 的 Deployment 具有反親和性策略,指示 Kubernetes 調度程序在集群中的不同工作節點上運行 CoreDNS 實例,即它應該避免在同一工作節點上共置副本。這有效地減少了每個網路介面的 DNS 查詢數量,因為來自每個副本的流量都通過不同的 ENI 路由。如果您注意到 DNS 查詢因每秒 1024 個數據包的限制而被節流,您可以 1) 嘗試增加 CoreDNS 副本的數量或 2) 實現 [NodeLocal DNSCache](https://kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/)。有關更多資訊,請參閱 [監控 CoreDNS 指標](https://aws.github.io/aws-eks-best-practices/reliability/docs/dataplane/#monitor-coredns-metrics)。

### 挑戰
* 數據包丟棄發生在幾秒鐘內,對我們來說很難適當監控這些模式以確定是否實際發生了 DNS 節流。
* DNS 查詢在彈性網路介面層面上被節流。因此,被節流的查詢不會出現在查詢日誌中。
* 流量日誌不會捕獲所有 IP 流量。例如,當實例與 Amazon DNS 服務器聯繫時產生的流量。如果您使用自己的 DNS 服務器,則會記錄所有到該 DNS 服務器的流量。

### 解決方案
識別工作節點中 DNS 節流問題的一種簡單方法是捕獲 `linklocal_allowance_exceeded` 指標。[linklocal_allowance_exceeded](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/metrics-collected-by-CloudWatch-agent.html#linux-metrics-enabled-by-CloudWatch-agent) 是因為到本地代理服務的流量的 PPS 超過網路介面的最大值而丟棄的數據包數量。這會影響到 DNS 服務、實例元數據服務和 Amazon Time Sync 服務的流量。與其實時跟踪此事件,我們還可以將此指標流式傳輸到 [Amazon Managed Service for Prometheus](https://aws.amazon.com/prometheus/) 並在 [Amazon Managed Grafana](https://aws.amazon.com/grafana/) 中將其可視化。

## 使用 Conntrack 指標監控 DNS 查詢延遲

另一個可以幫助監控 CoreDNS 節流/查詢延遲的指標是 `conntrack_allowance_available` 和 `conntrack_allowance_exceeded`。
由於超過連接跟踪允許值而導致的連接失敗可能會產生比超過其他允許值更大的影響。當依賴 TCP 來傳輸數據時,由於 TCP 的擁塞控制能力,由於超過 EC2 實例網路允許值(如帶寬、PPS 等)而導致的排隊或丟棄的數據包通常會被優雅地處理。受影響的流量將被減慢,並且丟失的數據包將被重新傳輸。但是,當實例超過其連接跟踪允許值時,在關閉一些現有連接以為新連接騰出空間之前,無法建立新連接。

`conntrack_allowance_available` 和 `conntrack_allowance_exceeded` 可以幫助客戶監控每個實例的連接跟踪允許值。這些網路效能指標讓客戶可以了解實例的網路帶寬、每秒數據包數 (PPS)、連接跟踪和鏈路本地服務訪問 (Amazon DNS、實例元數據服務、Amazon Time Sync) 等允許值超過時排隊或丟棄的數據包數量。

`conntrack_allowance_available` 是實例在達到該實例類型的連接跟踪允許值之前可以建立的跟踪連接數 (僅支持基於 nitro 的實例)。
`conntrack_allowance_exceeded` 是因為連接跟踪超過實例的最大值而無法建立新連接而丟棄的數據包數量。

## 其他重要的網路效能指標

其他重要的網路效能指標包括:

`bw_in_allowance_exceeded` (該指標的理想值應為零) 是因入站總帶寬超過實例的最大值而排隊和/或丟棄的數據包數量。

`bw_out_allowance_exceeded` (該指標的理想值應為零) 是因出站總帶寬超過實例的最大值而排隊和/或丟棄的數據包數量。

`pps_allowance_exceeded` (該指標的理想值應為零) 是因雙向 PPS 超過實例的最大值而排隊和/或丟棄的數據包數量。

## 捕獲指標以監控工作負載的網路效能問題

彈性網路適配器 (ENA) 驅動程序會從啟用它們的實例發布上述網路效能指標。所有網路效能指標都可以使用 CloudWatch 代理程序發布到 CloudWatch。請參閱 [博客](https://aws.amazon.com/blogs/networking-and-content-delivery/amazon-ec2-instance-level-network-performance-metrics-uncover-new-insights/) 以獲取更多資訊。

現在讓我們捕獲上面討論的指標,將它們存儲在 Amazon Managed Service for Prometheus 中,並使用 Amazon Managed Grafana 進行可視化。

### 先決條件
* ethtool - 確保工作節點已安裝 ethtool
* 在您的 AWS 帳戶中配置了 AMP 工作區。有關說明,請參閱 AMP 用戶指南中的 [建立工作區](https://docs.aws.amazon.com/prometheus/latest/userguide/AMP-onboard-create-workspace.html)。
* Amazon Managed Grafana 工作區

### 部署 Prometheus ethtool 導出器
該部署包含一個 python 腳本,從 ethtool 中提取資訊並以 prometheus 格式發布。

```
kubectl apply -f https://raw.githubusercontent.com/Showmax/prometheus-ethtool-exporter/master/deploy/k8s-daemonset.yaml
```

### 部署 ADOT 收集器以抓取 ethtool 指標並將其存儲在 Amazon Managed Service for Prometheus 工作區中
在每個安裝了 AWS Distro for OpenTelemetry (ADOT) 的集群中,您都必須具有此角色,以授予您的 AWS 服務帳戶將指標存儲到 Amazon Managed Service for Prometheus 的權限。按照以下步驟使用 IRSA 為您的 Amazon EKS 服務帳戶創建和關聯 IAM 角色:

```
eksctl create iamserviceaccount --name adot-collector --namespace default --cluster <CLUSTER_NAME> --attach-policy-arn arn:aws:iam::aws:policy/AmazonPrometheusRemoteWriteAccess --attach-policy-arn arn:aws:iam::aws:policy/AWSXrayWriteOnlyAccess --attach-policy-arn arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy --region <REGION> --approve  --override-existing-serviceaccounts
```

讓我們部署 ADOT 收集器以從 prometheus ethtool 導出器抓取指標並將其存儲在 Amazon Managed Service for Prometheus 中。

以下過程使用了一個示例 YAML 文件,其中 mode 值為 deployment。這是默認模式,並將 ADOT 收集器類似於獨立應用程序的方式部署。此配置從示例應用程序接收 OTLP 指標,並從集群上的 pod 抓取 Amazon Managed Service for Prometheus 指標。

```
curl -o collector-config-amp.yaml https://raw.githubusercontent.com/aws-observability/aws-otel-community/master/sample-configs/operator/collector-config-amp.yaml
```

在 collector-config-amp.yaml 中,用您自己的值替換以下內容:
* mode: deployment
* serviceAccount: adot-collector
* endpoint: "<YOUR_REMOTE_WRITE_ENDPOINT>"
* region: "<YOUR_AWS_REGION>"
* name: adot-collector

```
kubectl apply -f collector-config-amp.yaml 
```

一旦部署了 adot 收集器,指標就會成功存儲在 Amazon Prometheus 中。

### 在 Amazon Managed Service for Prometheus 中配置警報管理器以發送通知
讓我們配置錄製規則和警報規則來檢查到目前為止討論的指標。

我們將使用 [ACK Controller for Amazon Managed Service for Prometheus](https://github.com/aws-controllers-k8s/prometheusservice-controller) 來設置警報和錄製規則。

讓我們部署 Amazon Managed Service for Prometheus 服務的 ACL 控制器:

```
export SERVICE=prometheusservice
export RELEASE_VERSION=`curl -sL https://api.github.com/repos/aws-controllers-k8s/$SERVICE-controller/releases/latest | grep '"tag_name":' | cut -d'"' -f4`
export ACK_SYSTEM_NAMESPACE=ack-system
export AWS_REGION=us-east-1
aws ecr-public get-login-password --region us-east-1 | helm registry login --username AWS --password-stdin public.ecr.aws
helm install --create-namespace -n $ACK_SYSTEM_NAMESPACE ack-$SERVICE-controller \
oci://public.ecr.aws/aws-controllers-k8s/$SERVICE-chart --version=$RELEASE_VERSION --set=aws.region=$AWS_REGION
```

運行該命令,片刻之後您應該會看到以下消息:

```
You are now able to create Amazon Managed Service for Prometheus (AMP) resources!

The controller is running in "cluster" mode.

The controller is configured to manage AWS resources in region: "us-east-1"

The ACK controller has been successfully installed and ACK can now be used to provision an Amazon Managed Service for Prometheus workspace.
```

現在讓我們為設置警報管理器定義和規則組創建一個 yaml 文件。
將下面的內容保存為 `rulegroup.yaml`

```
apiVersion: prometheusservice.services.k8s.aws/v1alpha1
kind: RuleGroupsNamespace
metadata:
   name: default-rule
spec:
   workspaceID: <Your WORKSPACE-ID>
   name: default-rule
   configuration: |
     groups:
     - name: ppsallowance
       rules:
       - record: metric:pps_allowance_exceeded
         expr: rate(node_net_ethtool{device="eth0",type="pps_allowance_exceeded"}[30s])
       - alert: PPSAllowanceExceeded
         expr: rate(node_net_ethtool{device="eth0",type="pps_allowance_exceeded"} [30s]) > 0
         labels:
           severity: critical
           
         annotations:
           summary: Connections dropped due to total allowance exceeding for the  (instance {{ $labels.instance }})
           description: "PPSAllowanceExceeded is greater than 0"
     - name: bw_in
       rules:
       - record: metric:bw_in_allowance_exceeded
         expr: rate(node_net_ethtool{device="eth0",type="bw_in_allowance_exceeded"}[30s])
       - alert: BWINAllowanceExceeded
         expr: rate(node_net_ethtool{device="eth0",type="bw_in_allowance_exceeded"} [30s]) > 0
         labels:
           severity: critical
           
         annotations:
           summary: Connections dropped due to total allowance exceeding for the  (instance {{ $labels.instance }})
           description: "BWInAllowanceExceeded is greater than 0"
     - name: bw_out
       rules:
       - record: metric:bw_out_allowance_exceeded
         expr: rate(node_net_ethtool{device="eth0",type="bw_out_allowance_exceeded"}[30s])
       - alert: BWOutAllowanceExceeded
         expr: rate(node_net_ethtool{device="eth0",type="bw_out_allowance_exceeded"} [30s]) > 0
         labels:
           severity: critical
           
         annotations:
           summary: Connections dropped due to total allowance exceeding for the  (instance {{ $labels.instance }})
           description: "BWoutAllowanceExceeded is greater than 0"            
     - name: conntrack
       rules:
       - record: metric:conntrack_allowance_exceeded
         expr: rate(node_net_ethtool{device="eth0",type="conntrack_allowance_exceeded"}[30s])
       - alert: ConntrackAllowanceExceeded
         expr: rate(node_net_ethtool{device="eth0",type="conntrack_allowance_exceeded"} [30s]) > 0
         labels:
           severity: critical
           
         annotations:
           summary: Connections dropped due to total allowance exceeding for the  (instance {{ $labels.instance }})
           description: "ConnTrackAllowanceExceeded is greater than 0"
     - name: linklocal
       rules:
       - record: metric:linklocal_allowance_exceeded
         expr: rate(node_net_ethtool{device="eth0",type="linklocal_allowance_exceeded"}[30s])
       - alert: LinkLocalAllowanceExceeded
         expr: rate(node_net_ethtool{device="eth0",type="linklocal_allowance_exceeded"} [30s]) > 0
         labels:
           severity: critical
           
         annotations:
           summary: Packets dropped due to PPS rate allowance exceeded for local services  (instance {{ $labels.instance }})
           description: "LinkLocalAllowanceExceeded is greater than 0"
```

將 Your WORKSPACE-ID 替換為您正在使用的工作區的工作區 ID。

現在讓我們配置警報管理器定義。將下面的文件保存為 `alertmanager.yaml`

```
apiVersion: prometheusservice.services.k8s.aws/v1alpha1  
kind: AlertManagerDefinition
metadata:
  name: alert-manager
spec:
  workspaceID: <Your WORKSPACE-ID >
  configuration: |
    alertmanager_config: |
      route:
         receiver: default_receiver
       receivers:
       - name: default_receiver
          sns_configs:
          - topic_arn: TOPIC-ARN
            sigv4:
              region: REGION
            message: |
              alert_type: {{ .CommonLabels.alertname }}
              event_type: {{ .CommonLabels.event_type }}     
```

將 You WORKSPACE-ID 替換為新工作區的工作區 ID,將 TOPIC-ARN 替換為您希望發送警報的 [Amazon Simple Notification Service](https://aws.amazon.com/sns/) 主題的 ARN,並將 REGION 替換為當前工作負載的區域。請確保您的工作區有權限向 Amazon SNS 發送消息。

### 在 Amazon Managed Grafana 中可視化 ethtool 指標
讓我們在 Amazon Managed Grafana 中可視化指標並構建一個儀表板。根據說明在 Amazon Managed Grafana 控制台中將 Amazon Managed Service for Prometheus 配置為數據源,請參閱 [添加 Amazon Prometheus 作為數據源](https://docs.aws.amazon.com/grafana/latest/userguide/AMP-adding-AWS-config.html)。

現在讓我們在 Amazon Managed Grafana 中探索指標:
單擊探索按鈕,並搜索 ethtool:

![Node_ethtool metrics](./explore_metrics.png)

讓我們使用查詢 `rate(node_net_ethtool{device="eth0",type="linklocal_allowance_exceeded"}[30s])` 為 linklocal_allowance_exceeded 指標構建一個儀表板。它將產生以下儀表板。

![linklocal_allowance_exceeded dashboard](./linklocal.png)

我們可以清楚地看到沒有數據包被丟棄,因為值為零。

讓我們使用查詢 `rate(node_net_ethtool{device="eth0",type="conntrack_allowance_exceeded"}[30s])` 為 conntrack_allowance_exceeded 指標構建一個儀表板。它將產生以下儀表板。

![conntrack_allowance_exceeded dashboard](./conntrack.png)

如果您按照 [這裡](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Agent-network-performance.html) 所述運行 cloudwatch 代理程序,則可以在 CloudWatch 中可視化 `conntrack_allowance_exceeded` 指標。在 CloudWatch 中的結果儀表板將如下所示:

![CW_NW_Performance](./cw_metrics.png)

我們可以清楚地看到沒有數據包被丟棄,因為值為零。如果您使用基於 Nitro 的實例,您可以為 `conntrack_allowance_available` 創建類似的儀表板,並主動監控您的 EC2 實例中的連接。您可以進一步擴展這一點,在 Amazon Managed Grafana 中配置警報以將通知發送到 Slack、SNS、Pagerduty 等。