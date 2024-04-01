---
date: 2023-09-29
authors: 
  - Rachel Leekin
  - Nirmal Mehta
---
# 成本优化 - 可观测性

## 简介

可观测性工具可帮助您高效地检测、修复和调查工作负载。随着您对 EKS 的使用增加，遥测数据的成本自然也会增加。有时，在满足运营需求、衡量对业务重要的指标并控制可观测性成本之间，可能会有一些挑战。本指南重点介绍了可观测性三大支柱：日志、指标和跟踪的成本优化策略。这些最佳实践中的每一个都可以独立应用，以适应您组织的优化目标。

## 日志记录

日志在监控和排查集群中应用程序的问题时起着至关重要的作用。有几种策略可以用来优化日志成本。下面列出的最佳实践策略包括检查您的日志保留策略，以实现对日志数据保留时间的精细控制;根据重要性将日志数据发送到不同的存储选项;以及利用日志过滤来缩小存储的日志消息类型。高效管理日志遥测可以为您的环境节省成本。

## EKS 控制平面

### 优化您的控制平面日志

Kubernetes 控制平面是一组[组件](https://kubernetes.io/docs/concepts/overview/components/#control-plane-components),用于管理集群，这些组件会将不同类型的信息作为日志流发送到 [Amazon CloudWatch](https://aws.amazon.com/cloudwatch/) 中的一个日志组。虽然启用所有控制平面日志类型都有好处，但您应该了解每种日志中的信息以及存储所有日志遥测数据的相关成本。您需要为从集群发送到 Amazon CloudWatch Logs 的日志支付标准的 [CloudWatch Logs 数据引入和存储成本](https://aws.amazon.com/cloudwatch/pricing/)。在启用它们之前，请评估每个日志流是否必需。

例如，在非生产集群中，只有在分析时才选择性启用特定日志类型，如 API 服务器日志，之后再将其停用。但对于生产集群，您可能无法重现事件，解决问题需要更多日志信息，因此您可以启用所有日志类型。进一步的控制平面成本优化实施细节在这篇[博客](https://aws.amazon.com/blogs/containers/understanding-and-cost-optimizing-amazon-eks-control-plane-logs/)文章中。

#### 将日志流式传输到 S3

另一种成本优化最佳实践是通过 CloudWatch Logs 订阅将控制平面日志流式传输到 S3。利用 CloudWatch Logs [订阅](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions.html)允许您选择性地将日志转发到 S3，与无限期保留日志在 CloudWatch 中相比，这提供了更加经济高效的长期存储。例如，对于生产集群，您可以创建一个关键日志组，并利用订阅在 15 天后将这些日志流式传输到 S3。这将确保您可以快速访问日志进行分析，同时通过将日志移动到更加经济高效的存储来节省成本。

!!! attention
    截至 2023 年 9 月 5 日，EKS 日志在 Amazon CloudWatch Logs 中被归类为 Vended Logs。Vended Logs 是 AWS 服务代表客户本地发布的特定 AWS 服务日志，可享受批量折扣定价。请访问 [Amazon CloudWatch 定价页面](https://aws.amazon.com/cloudwatch/pricing/)了解有关 Vended Logs 定价的更多信息。

## EKS 数据平面

### 日志保留

Amazon CloudWatch 的默认保留策略是永不过期，永久保留日志，并根据您的 AWS 区域收取相应的存储成本。为了减少存储成本，您可以根据工作负载要求为每个日志组自定义保留策略。

在开发环境中，可能不需要长期保留。但在生产环境中，您可以设置更长的保留策略，以满足故障排查、合规性和容量规划要求。例如，如果您在节日高峰季运行电子商务应用程序，系统承受更重的负载，可能会出现一些问题并不是立即可见的，您将需要设置更长的日志保留期，以便进行详细的故障排查和事后分析。

您可以在 AWS CloudWatch 控制台或 [AWS API](https://docs.aws.amazon.com/cli/latest/reference/logs/put-retention-policy.html) 中[配置保留期](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html#SettingLogRetention),持续时间从 1 天到 10 年不等，具体取决于每个日志组。拥有灵活的保留期可以节省日志存储成本，同时保留关键日志。

### 日志存储选项

存储是可观测性成本的主要驱动因素，因此优化日志存储策略至关重要。您的策略应与工作负载要求保持一致，同时保持性能和可扩展性。减少存储日志成本的一种策略是利用 AWS S3 存储桶及其不同的存储层。

#### 直接将日志转发到 S3

考虑将不太重要的日志(如开发环境日志)直接转发到 S3，而不是 Cloudwatch。这可以立即影响日志存储成本。一种选择是使用 Fluentbit 直接将日志转发到 S3。您可以在 `[OUTPUT]` 部分中定义这一点，该部分是 FluentBit 传输容器日志以进行保留的目标位置。请在[此处](https://docs.fluentbit.io/manual/pipeline/outputs/s3#worker-support)查看其他配置参数。

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

#### 仅将日志转发到 CloudWatch 以进行短期分析

对于更关键的日志，如生产环境日志(您可能需要立即对数据进行分析)，请考虑将日志转发到 CloudWatch。您可以在 `[OUTPUT]` 部分中定义这一点，该部分是 FluentBit 传输容器日志以进行保留的目标位置。请在[此处](https://docs.fluentbit.io/manual/pipeline/outputs/cloudwatch)查看其他配置参数。

```
[OUTPUT]
        Name eks_to_cloudwatch_logs
        Match application.*
        region us-east-2
        log_group_name fluent-bit-cloudwatch
        log_stream_prefix from-fluent-bit-
        auto_create_group On
```

但是，这不会立即产生成本节省效果。为了进一步节省，您必须将这些日志导出到 Amazon S3。

#### 从 CloudWatch 导出到 Amazon S3

为了长期存储 Amazon CloudWatch 日志，我们建议将您的 Amazon EKS CloudWatch 日志导出到 Amazon Simple Storage Service (Amazon S3)。您可以通过在[控制台](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/S3ExportTasksConsole.html)或 API 中创建导出任务，将日志转发到 Amazon S3 存储桶。完成后，Amazon S3 提供了许多进一步降低成本的选项。您可以定义自己的 [Amazon S3 生命周期规则](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html),将日志移动到符合您需求的存储类，或者利用 [Amazon S3 智能分层存储](https://aws.amazon.com/s3/storage-classes/intelligent-tiering/)存储类，让 AWS 根据您的使用模式自动将数据移动到长期存储。请参阅此[博客](https://aws.amazon.com/blogs/containers/understanding-and-cost-optimizing-amazon-eks-control-plane-logs/)了解更多详情。例如，对于您的生产环境日志，如果在 CloudWatch 中保留超过 30 天，则导出到 Amazon S3 存储桶。如果您需要在以后参考日志，可以使用 Amazon Athena 查询 Amazon S3 存储桶中的数据。

### 减少日志级别

对您的应用程序实践选择性日志记录。默认情况下，您的应用程序和节点都会输出日志。对于应用程序日志，请根据工作负载和环境的重要性调整日志级别。例如，下面的 java 应用程序正在输出 `INFO` 级别的日志，这是典型的默认应用程序配置，根据代码的不同，可能会产生大量日志数据。


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

在开发环境中，将您的日志级别更改为 `DEBUG`,这可以帮助您调试问题或在问题进入生产环境之前捕获潜在问题。

```java
      log.setLevel(Level.DEBUG);
```

在生产环境中，请考虑将日志级别修改为 `ERROR` 或 `FATAL`。这将仅在应用程序出现错误时输出日志，从而减少日志输出，并帮助您关注应用程序状态的重要数据。


```java
      log.setLevel(Level.ERROR);
```

您可以微调各种 Kubernetes 组件的日志级别。例如，如果您使用 [Bottlerocket](https://bottlerocket.dev/) 作为 EKS 节点操作系统，有一些配置设置可以让您调整 kubelet 进程的日志级别。下面是此配置设置的一个片段。注意默认的[日志级别](https://github.com/bottlerocket-os/bottlerocket/blob/3f716bd68728f7fd825eb45621ada0972d0badbb/README.md?plain=1#L528)为 **2**,它调整了 `kubelet` 进程的日志记录详细程度。

```toml hl_lines="2"
[settings.kubernetes]
log-level = "2"
image-gc-high-threshold-percent = "85"
image-gc-low-threshold-percent = "80"
```

对于开发环境，您可以将日志级别设置为大于 **2** 的值，以查看更多事件，这有助于调试。对于生产环境，您可以将级别设置为 **0**,以仅查看关键事件。

### 利用过滤器

当使用默认的 EKS Fluentbit 配置将容器日志发送到 Cloudwatch 时，FluentBit 会捕获并将 **所有** 应用程序容器日志(附加了 Kubernetes 元数据)发送到 Cloudwatch，如下面的 `[INPUT]` 配置块所示。

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

上面的 `[INPUT]` 部分正在引入所有容器日志。这可能会产生大量不必要的数据。过滤掉这些数据可以减少发送到 CloudWatch 的日志数据量，从而降低成本。您可以在输出到 CloudWatch 之前对日志应用过滤器。Fluentbit 在 `[FILTER]` 部分中定义这一点。例如，过滤掉附加到日志事件的 Kubernetes 元数据可以减少日志量。

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

## 指标

[指标](https://aws-observability.github.io/observability-best-practices/signals/metrics/)提供了有关系统性能的宝贵信息。通过将所有与系统相关或可用资源指标合并到一个中心位置，您就可以比较和分析性能数据。这种集中式方法使您能够做出更明智的战略决策，例如扩大或缩小资源。此外，指标在评估资源健康状况方面也起着至关重要的作用，让您可以在必要时采取主动措施。通常，可观测性成本会随着遥测数据收集和保留而增加。以下是您可以实施的一些策略，以降低指标遥测的成本：仅收集重要的指标、减少遥测数据的基数(cardinality)以及微调遥测数据收集的粒度。

### 监控重点并仅收集所需内容

降低成本的第一个策略是减少您收集的指标数量，从而降低保留成本。

1. 首先从您和/或您的利益相关者的要求出发，确定[最重要的指标](https://aws-observability.github.io/observability-best-practices/guides/#monitor-what-matters)。每个人的成功指标都不一样!了解什么是"良好"状态，并对其进行衡量。
2. 考虑深入研究您正在支持的工作负载，并确定其关键性能指标 (KPI)，也称为"黄金信号"。这些应该与业务和利益相关者的要求保持一致。使用 Amazon CloudWatch 和 Metric Math 计算 SLI、SLO 和 SLA 对于管理服务可靠性至关重要。请遵循本[指南](https://aws-observability.github.io/observability-best-practices/guides/operational/business/key-performance-indicators/#10-understanding-kpis-golden-signals)中概述的最佳实践，有效监控和维护您的 EKS 环境的性能。
3. 然后继续深入不同的基础设施层，将 EKS 集群、节点和其他基础设施指标与您的工作负载 KPI 相关联。将您的业务指标和运营指标存储在一个系统中，您可以在其中将它们相互关联并根据观察到的影响得出结论。
4. EKS 公开了来自控制平面、集群 kube-state-metrics、Pod 和节点的指标。所有这些指标的相关性取决于您的需求，但您可能不需要跨不同层的每个指标。您可以使用这个 [EKS 基本指标](https://aws-observability.github.io/observability-best-practices/guides/containers/oss/eks/best-practices-metrics-collection/)指南作为监控 EKS 集群和工作负载整体健康状况的基线。

下面是一个 prometheus 抓取配置示例，我们使用 `relabel_config` 只保留 kubelet 指标，并使用 `metric_relabel_config` 删除所有容器指标。

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

### 在适用的情况下减少基数

基数是指特定指标集中数据值及其维度 (例如 prometheus 标签) 的唯一性。高基数指标具有许多维度，每个维度指标组合的唯一性也更高。更高的基数会导致更大的指标遥测数据大小和存储需求，从而增加成本。

在下面的高基数示例中，我们看到指标 Latency 具有维度 RequestID、CustomerID 和 Service，每个维度都有许多唯一值。基数是每个维度可能值数量的组合度量。在 Prometheus 中，每组唯一的维度/标签都被视为一个新的指标，因此高基数意味着更多的指标。

![高基数](../images/high-cardinality.png)

在具有许多指标和每个指标的维度/标签 (集群、命名空间、服务、Pod、容器等) 的 EKS 环境中，基数往往会增长。为了优化成本，请仔细考虑您正在收集的指标的基数。例如，如果您正在聚合特定指标以进行集群级别的可视化，那么您可以删除低于命名空间级别的其他标签。

要在 prometheus 中识别高基数指标，您可以运行以下 PROMQL 查询来确定哪些抓取目标具有最高的指标数量 (基数)：

```promql 
topk_max(5, max_over_time(scrape_samples_scraped[1h]))
```

以下 PROMQL 查询可帮助您确定哪些抓取目标具有最高的指标变化率 (在给定的抓取中创建了多少新的指标序列)：

```promql
topk_max(5, max_over_time(scrape_series_added[1h]))
```

如果您使用 grafana，您可以使用 Grafana Lab 的 Mimirtool 分析您的 grafana 仪表板和 prometheus 规则，以识别未使用的高基数指标。请按照[此指南](https://grafana.com/docs/grafana-cloud/account-management/billing-and-usage/control-prometheus-metrics-usage/usage-analysis-mimirtool/?pg=blog&plcmt=body-txt#analyze-and-reduce-metrics-usage-with-grafana-mimirtool)了解如何使用 `mimirtool analyze` 和 `mimirtool analyze prometheus` 命令来识别未在您的仪表板中引用的活动指标。


### 考虑指标粒度

每秒而不是每分钟收集指标可能会对收集和存储的遥测数据量产生很大影响，从而增加成本。确定合理的抓取或指标收集间隔，在能够看到瞬时问题的足够粒度和成本效益之间取得平衡。对于用于容量规划和较大时间窗口分析的指标，请降低其粒度。

下面是 AWS Distro for Opentelemetry (ADOT) EKS 插件 Collector 的默认[配置](https://docs.aws.amazon.com/eks/latest/userguide/deploy-deployment.html)的一个片段。

!!! attention
    全局 prometheus 抓取间隔设置为 15 秒。可以增加此抓取间隔，从而减少在 prometheus 中收集的指标数据量。

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



## 跟踪

跟踪的主要成本来自跟踪存储生成。对于跟踪，目标是收集足够的数据来诊断和了解性能方面。但是，由于 X-Ray 跟踪成本是基于转发到 X-Ray 的数据，因此删除已转发的跟踪不会降低您的成本。让我们回顾一下降低跟踪成本的方法，同时保留数据以便您进行适当的分析。


### 应用采样规则

X-Ray 采样率默认情况下是保守的。定义采样规则，您可以控制收集的数据量。这将提高性能效率，同时降低成本。通过[降低采样率](https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html#xray-console-custom),您可以仅从您的工作负载所需的请求中收集跟踪，同时保持较低的成本结构。

例如，您有一个 java 应用程序，您想调试所有请求的跟踪，针对 1 个有问题的路由。

**通过 SDK 配置从 JSON 文档加载采样规则**

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


**通过控制台**

![控制台](../images/console.png)

### 应用 AWS Distro for OpenTelemetry (ADOT) 的尾部采样

ADOT 尾部采样允许您控制引入服务的跟踪量。但是，尾部采样允许您在请求中的所有跨度完成后，而不是在开始时定义采样策略。这进一步限制了转移到 CloudWatch 的原始数据量，从而降低了成本。

例如，如果您对着陆页面的 1% 流量进行采样，对付款页面的 10% 请求进行采样，在 30 分钟内，您可能会得到 300 个跟踪。使用过滤特定错误的 ADOT 尾部采样规则，您可能只剩下 200 个跟踪，从而减少了存储的跟踪数量。


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

### 利用 Amazon S3 存储选项

您应该利用 AWS S3 存储桶及其不同的存储类来存储跟踪。在保留期到期之前将跟踪导出到 S3。使用 Amazon S3 生命周期规则将跟踪数据移动到满足您要求的存储类。

例如，如果您有 90 天的旧跟踪，[Amazon S3 智能分层存储](https://aws.amazon.com/s3/storage-classes/intelligent-tiering/)可以根据您的使用模式自动将数据移动到长期存储。如果您需要参考跟踪，可以使用 [Amazon Athena](https://aws.amazon.com/athena/) 查询 Amazon S3 中的数据。这可以进一步降低您的分布式跟踪成本。


## 其他资源：

* [可观测性最佳实践指南](https://aws-observability.github.io/observability-best-practices/guides/)
* [最佳实践指标收集](https://aws-observability.github.io/observability-best-practices/guides/containers/oss/eks/)
* [AWS re:Invent 2022 - 亚马逊的可观测性最佳实践 (COP343)](https://www.youtube.com/watch?v=zZPzXEBW4P8)
* [AWS re:Invent 2022 - 可观测性：现代应用程序的最佳实践 (COP344)](https://www.youtube.com/watch?v=YiegAlC_yyc)