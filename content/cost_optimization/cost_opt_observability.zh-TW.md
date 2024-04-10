---
日期: 2023-09-29
作者:
  - Rachel Leekin
  - Nirmal Mehta
---
# 成本優化 - 可觀察性

## 簡介

可觀察性工具可幫助您有效地檢測、補救和調查您的工作負載。隨著您對 EKS 的使用增加,遙測數據的成本自然也會增加。有時,在衡量對您的業務至關重要的事項並控制可觀察性成本方面,可能會有一些挑戰。本指南著重於三大可觀察性支柱的成本優化策略:日誌、指標和追蹤。這些最佳實踐可以單獨應用,以符合您組織的優化目標。

## 日誌

日誌在監控和排除集群中應用程式的故障方面扮演著重要的角色。有幾種策略可用於優化日誌成本。下面列出的最佳實踐策略包括檢查您的日誌保留政策,以實施對保留日誌數據的時間長度的細粒度控制,根據重要性將日誌數據發送到不同的存儲選項,以及利用日誌過濾來縮小要存儲的日誌消息類型。有效管理日誌遙測可以為您的環境節省成本。

## EKS 控制平面

### 優化您的控制平面日誌

Kubernetes 控制平面是一組管理集群的 [組件](https://kubernetes.io/docs/concepts/overview/components/#control-plane-components),這些組件將不同類型的信息作為日誌流發送到 [Amazon CloudWatch](https://aws.amazon.com/cloudwatch/) 中的日誌組。雖然啟用所有控制平面日誌類型都有好處,但您應該了解每個日誌中的信息以及存儲所有日誌遙測的相關成本。您需要為從集群發送到 Amazon CloudWatch Logs 的日誌支付標準的 [CloudWatch Logs 數據攝取和存儲成本](https://aws.amazon.com/cloudwatch/pricing/)。在啟用它們之前,請評估每個日誌流是否必需。

例如,在非生產集群中,只啟用特定的日誌類型(如 api server 日誌)用於分析,並在之後將其停用。但對於生產集群,您可能無法重現事件,解決問題需要更多日誌信息,因此您可以啟用所有日誌類型。進一步的控制平面成本優化實施細節在此 [博客](https://aws.amazon.com/blogs/containers/understanding-and-cost-optimizing-amazon-eks-control-plane-logs/) 文章中。

#### 將日誌流傳輸到 S3

另一種成本優化最佳實踐是通過 CloudWatch Logs 訂閱將控制平面日誌流式傳輸到 S3。利用 CloudWatch Logs [訂閱](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions.html)允許您選擇性地將日誌轉發到 S3,S3 提供了比無限期保留日誌在 CloudWatch 中更具成本效益的長期存儲。例如,對於生產集群,您可以創建一個關鍵日誌組,並利用訂閱在 15 天後將這些日誌流式傳輸到 S3。這將確保您可以快速訪問日誌進行分析,但也可以通過將日誌移動到更具成本效益的存儲來節省成本。

!!! 注意
    截至 2023 年 9 月 5 日,EKS 日誌在 Amazon CloudWatch Logs 中被歸類為 Vended Logs。Vended Logs 是 AWS 服務代表客戶原生發布的特定 AWS 服務日誌,可享受批量折扣定價。請訪問 [Amazon CloudWatch 定價頁面](https://aws.amazon.com/cloudwatch/pricing/) 以了解有關 Vended Logs 定價的更多信息。

## EKS 數據平面

### 日誌保留

Amazon CloudWatch 的默認保留政策是無限期保留日誌,永不過期,從而產生適用於您所在 AWS 區域的存儲成本。為了減少存儲成本,您可以根據工作負載要求為每個日誌組自定義保留政策。

在開發環境中,可能不需要長期的保留期。但在生產環境中,您可以設置更長的保留政策,以滿足故障排除、合規性和容量規劃要求。例如,如果您在高峰假日期間運行電子商務應用程序,系統承受更重的負載,可能會出現一些問題,但不會立即被發現,您將希望設置更長的日誌保留期,以便進行詳細的故障排除和事後分析。

您可以在 AWS CloudWatch 控制台或 [AWS API](https://docs.aws.amazon.com/cli/latest/reference/logs/put-retention-policy.html) 中 [配置您的保留期](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html#SettingLogRetention),持續時間從 1 天到 10 年不等,取決於每個日誌組。靈活的保留期可以節省日誌存儲成本,同時也能保留關鍵日誌。

### 日誌存儲選項

存儲是可觀察性成本的主要驅動因素,因此優化您的日誌存儲策略至關重要。您的策略應與您的工作負載要求保持一致,同時保持性能和可擴展性。減少存儲日誌成本的一種策略是利用 AWS S3 bucket 及其不同的存儲層。

#### 將日誌直接轉發到 S3

考慮將不太重要的日誌(如開發環境)直接轉發到 S3 而不是 Cloudwatch。這可以立即影響日誌存儲成本。一種選擇是使用 Fluentbit 將日誌直接轉發到 S3。您可以在 `[OUTPUT]` 部分中定義這一點,該部分是 FluentBit 傳輸容器日誌以進行保留的目的地。在 [這裡](https://docs.fluentbit.io/manual/pipeline/outputs/s3#worker-support) 查看其他配置參數。

```
[OUTPUT]
        Name eks_to_s3
        Match application.* 
        bucket $S3_BUCKET name
        region us-east-2
        store_dir /var/log/fluentbit
        total_file_size 30M
        upload_timeout 3m
```

#### 僅將日誌轉發到 CloudWatch 以進行短期分析

對於更關鍵的日誌(如生產環境,您可能需要立即對數據進行分析),請考慮將日誌轉發到 CloudWatch。您可以在 `[OUTPUT]` 部分中定義這一點,該部分是 FluentBit 傳輸容器日誌以進行保留的目的地。在 [這裡](https://docs.fluentbit.io/manual/pipeline/outputs/cloudwatch) 查看其他配置參數。

```
[OUTPUT]
        Name eks_to_cloudwatch_logs
        Match application.*
        region us-east-2
        log_group_name fluent-bit-cloudwatch
        log_stream_prefix from-fluent-bit-
        auto_create_group On
```

但是,這不會立即對您的成本節省產生影響。為了進一步節省,您將不得不將這些日誌導出到 Amazon S3。

#### 從 CloudWatch 導出到 Amazon S3

為了長期存儲 Amazon CloudWatch 日誌,我們建議將您的 Amazon EKS CloudWatch 日誌導出到 Amazon Simple Storage Service (Amazon S3)。您可以通過在 [控制台](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/S3ExportTasksConsole.html) 或 API 中創建導出任務,將日誌轉發到 Amazon S3 bucket。完成後,Amazon S3 提供了許多進一步降低成本的選項。您可以定義自己的 [Amazon S3 生命週期規則](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html) 將您的日誌移動到符合您需求的存儲類別,或者利用 [Amazon S3 智能分層存儲](https://aws.amazon.com/s3/storage-classes/intelligent-tiering/) 存儲類別,讓 AWS 根據您的使用模式自動將數據移動到長期存儲。請參考此 [博客](https://aws.amazon.com/blogs/containers/understanding-and-cost-optimizing-amazon-eks-control-plane-logs/) 以獲取更多詳細信息。例如,對於您的生產環境日誌,在 CloudWatch 中保留超過 30 天,然後導出到 Amazon S3 bucket。如果您需要在以後參考日誌,可以使用 Amazon Athena 查詢 Amazon S3 bucket 中的數據。

### 減少日誌級別

對您的應用程序實踐選擇性日誌記錄。默認情況下,您的應用程序和節點都會輸出日誌。對於您的應用程序日誌,請根據工作負載和環境的重要性調整日誌級別。例如,下面的 java 應用程序正在輸出 `INFO` 日誌,這是典型的默認應用程序配置,並且根據代碼可能會產生大量日誌數據。


```java hl_lines="7"
import org.apache.log4j.*;

public class LogClass {
   private static org.apache.log4j.Logger log = Logger.getLogger(LogClass.class);
   
   public static void main(String[] args) {
      log.setLevel(Level.INFO);

      log.debug("This is a DEBUG message, check this out!");
      log.info("This is an INFO message, nothing to see here!");
      log.warn("This is a WARN message, investigate this!");
      log.error("This is an ERROR message, check this out!");
      log.fatal("This is a FATAL message, investigate this!");
   }
}
```

在開發環境中,將您的日誌級別更改為 `DEBUG`,因為這可以幫助您調試問題或在進入生產之前捕獲潛在問題。

```java
      log.setLevel(Level.DEBUG);
```

在生產環境中,請考慮將日誌級別修改為 `ERROR` 或 `FATAL`。這將僅在您的應用程序出現錯誤時輸出日誌,從而減少日誌輸出,並幫助您關注應用程序狀態的重要數據。


```java
      log.setLevel(Level.ERROR);
```

您可以微調各種 Kubernetes 組件的日誌級別。例如,如果您使用 [Bottlerocket](https://bottlerocket.dev/) 作為 EKS 節點操作系統,則有一些配置設置可讓您調整 kubelet 進程的日誌級別。下面是此配置設置的一個片段。請注意默認的 [日誌級別](https://github.com/bottlerocket-os/bottlerocket/blob/3f716bd68728f7fd825eb45621ada0972d0badbb/README.md?plain=1#L528) **2**,它調整了 `kubelet` 進程的日誌記錄詳細程度。

```toml hl_lines="2"
[settings.kubernetes]
log-level = "2"
image-gc-high-threshold-percent = "85"
image-gc-low-threshold-percent = "80"
```

對於開發環境,您可以將日誌級別設置為大於 **2** 的值,以便查看更多事件,這對於調試很有用。對於生產環境,您可以將級別設置為 **0**,以便只查看關鍵事件。

### 利用過濾器

當使用默認的 EKS Fluentbit 配置將容器日誌發送到 Cloudwatch 時,FluentBit 會捕獲並將 **所有** 應用程序容器日誌(附帶 Kubernetes 元數據)發送到 Cloudwatch,如下面的 `[INPUT]` 配置塊所示。

```
    [INPUT]
        Name                tail
        Tag                 application.*
        Exclude_Path        /var/log/containers/cloudwatch-agent*, /var/log/containers/fluent-bit*, /var/log/containers/aws-node*, /var/log/containers/kube-proxy*
        Path                /var/log/containers/*.log
        Docker_Mode         On
        Docker_Mode_Flush   5
        Docker_Mode_Parser  container_firstline
        Parser              docker
        DB                  /var/fluent-bit/state/flb_container.db
        Mem_Buf_Limit       50MB
        Skip_Long_Lines     On
        Refresh_Interval    10
        Rotate_Wait         30
        storage.type        filesystem
        Read_from_Head      ${READ_FROM_HEAD}
```

上面的 `[INPUT]` 部分正在攝取所有容器日誌。這可能會產生大量不必要的數據。過濾掉這些數據可以減少發送到 CloudWatch 的日誌數據量,從而降低成本。您可以在輸出到 CloudWatch 之前對日誌應用過濾器。Fluentbit 在 `[FILTER]` 部分中定義這一點。例如,過濾掉附加到日誌事件的 Kubernetes 元數據可以減少日誌量。

```
    [FILTER]
        Name                nest
        Match               application.*
        Operation           lift
        Nested_under        kubernetes
        Add_prefix          Kube.

    [FILTER]
        Name                modify
        Match               application.*
        Remove              Kube.<Metadata_1>
        Remove              Kube.<Metadata_2>
        Remove              Kube.<Metadata_3>
    
    [FILTER]
        Name                nest
        Match               application.*
        Operation           nest
        Wildcard            Kube.*
        Nested_under        kubernetes
        Remove_prefix       Kube.
```

## 指標

[指標](https://aws-observability.github.io/observability-best-practices/signals/metrics/) 提供了有關系統性能的寶貴信息。通過將所有系統相關或可用資源指標合併到一個集中位置,您將能夠比較和分析性能數據。這種集中方法使您能夠做出更明智的戰略決策,例如擴大或縮小資源。此外,指標在評估資源健康狀況方面也扮演著關鍵角色,使您能夠在必要時採取主動措施。通常,可觀察性成本會隨著遙測數據收集和保留而增加。以下是您可以實施的一些策略,以降低指標遙測的成本:只收集重要的指標、減少遙測數據的基數以及微調遙測數據收集的粒度。

### 監控重要內容並僅收集所需內容

降低成本的第一個策略是減少您收集的指標數量,從而降低保留成本。

1. 首先,從您和/或您的利益相關者的要求出發,確定 [最重要的指標](https://aws-observability.github.io/observability-best-practices/guides/#monitor-what-matters)。每個人的成功指標都不一樣!了解 *良好* 的樣子,並對其進行測量。
2. 考慮深入了解您正在支持的工作負載,並確定其關鍵性能指標 (KPI) 或 "黃金信號"。這些應該與業務和利益相關者的要求保持一致。使用 Amazon CloudWatch 和 Metric Math 計算 SLI、SLO 和 SLA 對於管理服務可靠性至關重要。遵循此 [指南](https://aws-observability.github.io/observability-best-practices/guides/operational/business/key-performance-indicators/#10-understanding-kpis-golden-signals) 中概述的最佳實踐,有效監控和維護您的 EKS 環境的性能。
3. 然後繼續通過不同的基礎設施層將 EKS 集群、節點和其他基礎設施指標與您的工作負載 KPI 關聯起來。將您的業務指標和操作指標存儲在一個系統中,您可以在其中關聯它們並根據觀察到的對兩者的影響得出結論。
4. EKS 公開了來自控制平面、集群 kube-state-metrics、pod 和節點的指標。所有這些指標的相關性取決於您的需求,但您可能不需要跨不同層的每個指標。您可以使用此 [EKS 基本指標](https://aws-observability.github.io/observability-best-practices/guides/containers/oss/eks/best-practices-metrics-collection/) 指南作為監控 EKS 集群和工作負載整體健康狀況的基線。

這是一個 prometheus scrape 配置的示例,我們在其中使用 `relabel_config` 僅保留 kubelet 指標,並使用 `metric_relabel_config` 刪除所有容器指標。

```yaml
  kubernetes_sd_configs:
  - role: endpoints
    namespaces:
      names:
      - kube-system
  bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
  tls_config:
    insecure_skip_verify: true
  relabel_configs:
  - source_labels: [__meta_kubernetes_service_label_k8s_app]
    regex: kubelet
    action: keep

  metric_relabel_configs:
  - source_labels: [__name__]
    regex: container_(network_tcp_usage_total|network_udp_usage_total|tasks_state|cpu_load_average_10s)
    action: drop
```

### 在適用的情況下減少基數

基數是指特定指標集合及其維度 (例如 prometheus 標籤) 組合的數據值的唯一性。高基數指標具有許多維度,每個維度指標組合的唯一性更高。更高的基數會導致更大的指標遙測數據大小和存儲需求,從而增加成本。

在下面的高基數示例中,我們看到指標 Latency 具有維度 RequestID、CustomerID 和 Service,每個維度都有許多唯一值。基數是每個維度可能值數量組合的度量。在 Prometheus 中,每組唯一的維度/標籤都被視為一個新指標,因此高基數意味著更多指標。

![高基數](../images/high-cardinality.png)

在具有許多指標和每個指標的維度/標籤 (集群、命名空間、服務、Pod、容器等) 的 EKS 環境中,基數往往會增長。為了優化成本,請仔細考慮您正在收集的指標的基數。例如,如果您在集群級別聚合特定指標以進行可視化,則可以刪除低於命名空間標籤等級的其他標籤。

要在 prometheus 中識別高基數指標,您可以運行以下 PROMQL 查詢來確定哪些 scrape 目標具有最高的指標數量 (基數):

```promql 
topk_max(5, max_over_time(scrape_samples_scraped[1h]))
```

以及以下 PROMQL 查詢可以幫助您確定哪些 scrape 目標具有最高的指標流量率 (在給定的 scrape 中創建了多少新的指標序列):

```promql
topk_max(5, max_over_time(scrape_series_added[1h]))
```

如果您使用 grafana,您可以使用 Grafana Lab 的 Mimirtool 分析您的 grafana 儀表板和 prometheus 規則,以識別未使用的高基數指標。按照 [此指南](https://grafana.com/docs/grafana-cloud/account-management/billing-and-usage/control-prometheus-metrics-usage/usage-analysis-mimirtool/?pg=blog&plcmt=body-txt#analyze-and-reduce-metrics-usage-with-grafana-mimirtool) 了解如何使用 `mimirtool analyze` 和 `mimirtool analyze prometheus` 命令來識別在您的儀表板中未引用的活動指標。


### 考慮指標粒度

以每秒而不是每分鐘的更高粒度收集指標可能會對收集和存儲的遙測量產生很大影響,從而增加成本。確定合理的 scrape 或指標收集間隔,在能夠看到瞬態問題的足夠粒度和具有成本效益之間取得平衡。對於用於容量規劃和較大時間窗口分析的指標,降低粒度。

下面是 AWS Distro for Opentelemetry (ADOT) EKS Addon Collector 的默認 [配置](https://docs.aws.amazon.com/eks/latest/userguide/deploy-deployment.html) 的一個片段。

!!! 注意
    全局 prometheus scrape 間隔設置為 15s。可以增加此 scrape 間隔,從而減少在 prometheus 中收集的指標數據量。

```yaml hl_lines="22"
apiVersion: opentelemetry.io/v1alpha1
kind: OpenTelemetryCollector
metadata:
  name: my-collector-amp

...

  config: |
    extensions:
      sigv4auth:
        region: "<YOUR_AWS_REGION>"
        service: "aps"

    receivers:
      #
      # Scrape configuration for the Prometheus Receiver
      # This is the same configuration used when Prometheus is installed using the community Helm chart
      # 
      prometheus:
        config:
          global:
  scrape_interval: 15s
            scrape_timeout: 10s
```



## 追蹤

追蹤的主要成本來自追蹤存儲生成。對於追蹤,目標是收集足夠的數據來診斷和了解性能方面。但是,由於 X-Ray 追蹤成本是基於轉發到 X-Ray 的數據,因此刪除已轉發的追蹤將不會降低您的成本。讓我們回顧一下降低追蹤成本的方法,同時保留數據以便您進行適當的分析。


### 應用採樣規則

默認情況下,X-Ray 採樣率是保守的。定義採樣規則,您可以控制收集的數據量。這將提高性能效率,同時降低成本。通過 [降低採樣率](https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html#xray-console-custom),您可以僅從您的工作負載需要的請求中收集追蹤,同時保持較低的成本結構。

例如,您有一個 java 應用程序,您希望調試所有請求的追蹤,以了解 1 個有問題的路由。

**通過 SDK 配置從 JSON 文檔加載採樣規則**

```json
{
"version": 2,
  "rules": [
    {
"description": "debug-eks",
      "host": "*",
      "http_method": "PUT",
      "url_path": "/history/*",
      "fixed_target": 0,
      "rate": 1,
      "service_type": "debug-eks"
    }
  ],
  "default": {
"fixed_target": 1,
    "rate": 0.1
  }
}
```


**通過控制台**

![控制台](../images/console.png)

### 應用 AWS Distro for OpenTelemetry (ADOT) 的尾部採樣

ADOT 尾部採樣允許您控制攝入服務的追蹤量。但是,尾部採樣允許您在請求中的所有跨度完成後,而不是在開始時定義採樣策略。這進一步限制了轉移到 CloudWatch 的原始數據量,從而降低了成本。

例如,如果您對登錄頁面的流量採樣 1%,對付款頁面的請求採樣 10%,那麼在 30 分鐘內可能會留下 300 個追蹤。使用過濾特定錯誤的 ADOT 尾部採樣規則,您可能只剩下 200 個追蹤,從而減少了存儲的追蹤數量。


```yaml hl_lines="5"
processors:
  groupbytrace:
    wait_duration: 10s
    num_traces: 300 
    tail_sampling:
    decision_wait: 1s # This value should be smaller than wait_duration
    policies:
      - ..... # Applicable policies**
  batch/tracesampling:
    timeout: 0s # No need to wait more since this will happen in previous processors
    send_batch_max_size: 8196 # This will still allow us to limit the size of the batches sent to subsequent exporters

service:
  pipelines:
    traces/tailsampling:
      receivers: [otlp]
      processors: [groupbytrace, tail_sampling, batch/tracesampling]
      exporters: [awsxray]
```

### 利用 Amazon S3 存儲選項

您應該利用 AWS S3 bucket 及其不同的存儲類別來存儲追蹤。在保留期過期之前將追蹤導出到 S3。使用 Amazon S3 生命週期規則將追蹤數據移動到符合您要求的存儲類別。

例如,如果您有 90 天前的追蹤, [Amazon S3 智能分層](https://aws.amazon.com/s3/storage-classes/intelligent-tiering/) 可以根據您的使用模式自動將數據移動到長期存儲。如果您需要參考追蹤,可以使用 [Amazon Athena](https://aws.amazon.com/athena/) 查詢 Amazon S3 中的數據。這可以進一步降低您的分佈式追蹤成本。


## 其他資源:

* [可觀察性最佳實踐指南](https://aws-observability.github.io/observability-best-practices/guides/)
* [最佳實踐指標收集](https://aws-observability.github.io/observability-best-practices/guides/containers/oss/eks/)
* [AWS re:Invent 2022 - Amazon 的可觀察性最佳實踐 (COP343)](https://www.youtube.com/watch?v=zZPzXEBW4P8)
* [AWS re:Invent 2022 - 可觀察性:現代應用程序的最佳實踐 (COP344)](https://www.youtube.com/watch?v=YiegAlC_yyc)