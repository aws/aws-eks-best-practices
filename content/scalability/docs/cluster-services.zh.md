# 集群服务

集群服务运行在 EKS 集群内部，但它们不是用户工作负载。如果你有一台 Linux 服务器，你通常需要运行诸如 NTP、syslog 和容器运行时等服务来支持你的工作负载。集群服务类似，支持帮助你自动化和操作集群的服务。在 Kubernetes 中，这些通常运行在 kube-system 命名空间中，有些作为 [DaemonSets](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) 运行。

集群服务应该有很高的正常运行时间，在发生故障和故障排查时通常至关重要。如果一个核心集群服务不可用，你可能会失去访问可以帮助恢复或预防故障的数据(例如高磁盘利用率)。它们应该运行在专用计算实例上，例如单独的节点组或 AWS Fargate。这将确保集群服务不会受到共享实例上可能扩展或使用更多资源的工作负载的影响。

## 扩展 CoreDNS

扩展 CoreDNS 有两个主要机制。减少对 CoreDNS 服务的调用次数和增加副本数量。

### 通过降低 ndots 减少外部查询

ndots 设置指定在域名中被认为足以避免查询 DNS 的点数。如果你的应用程序的 ndots 设置为 5(默认值)，并且你从外部域(如 api.example.com,2 个点)请求资源，那么 CoreDNS 将为 /etc/resolv.conf 中定义的每个搜索域查询一个更具体的域。默认情况下，将搜索以下域，然后再进行外部请求。

```
api.example.<namespace>.svc.cluster.local
api.example.svc.cluster.local
api.example.cluster.local
api.example.<region>.compute.internal
```

`namespace` 和 `region` 值将被替换为你的工作负载命名空间和计算区域。根据你的集群设置，你可能还有其他搜索域。

你可以通过[降低工作负载的 ndots 选项](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/#pod-dns-config)或在域请求中包含尾随 . 来完全限定域(例如 `api.example.com.`)来减少对 CoreDNS 的请求次数。如果你的工作负载通过 DNS 连接到外部服务，我们建议将 ndots 设置为 2，以便工作负载不会在集群内部进行不必要的集群 DNS 查询。如果工作负载不需要访问集群内部的服务，你可以设置不同的 DNS 服务器和搜索域。

```
spec:
  dnsPolicy: "None"
  dnsConfig:
    options:
      - name: ndots
        value: "2"
      - name: edns0
```

如果你将 ndots 降低到一个太低的值，或者你正在连接的域没有包含足够的特异性(包括尾随 .),那么 DNS 查找可能会失败。请确保测试此设置将如何影响你的工作负载。

### 水平扩展 CoreDNS

CoreDNS 实例可以通过向部署添加更多副本来扩展。建议你使用 [NodeLocal DNS](https://kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/) 或 [cluster proportional autoscaler](https://github.com/kubernetes-sigs/cluster-proportional-autoscaler) 来扩展 CoreDNS。

NodeLocal DNS 需要在每个节点上运行一个实例 - 作为 DaemonSet - 这需要集群中更多的计算资源，但它将避免 DNS 请求失败并减少集群内 DNS 查询的响应时间。cluster proportional autoscaler 将根据集群中的节点数或核心数来扩展 CoreDNS。这与请求查询没有直接关系，但根据你的工作负载和集群大小可能会有用。默认的比例扩展是每 256 个核心或 16 个节点(以先发生的为准)添加一个副本。

## 垂直扩展 Kubernetes Metrics Server

Kubernetes Metrics Server 支持水平和垂直扩展。通过水平扩展 Metrics Server，它将是高可用的，但不会水平扩展来处理更多的集群指标。随着节点和收集的指标被添加到集群中，你将需要根据[他们的建议](https://kubernetes-sigs.github.io/metrics-server/#scaling)来垂直扩展 Metrics Server。

Metrics Server 将它收集、聚合和服务的数据保存在内存中。随着集群的增长，Metrics Server 存储的数据量也会增加。在大型集群中，Metrics Server 将需要比默认安装中指定的内存和 CPU 预留更多的计算资源。你可以使用 [Vertical Pod Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler) (VPA) 或 [Addon Resizer](https://github.com/kubernetes/autoscaler/tree/master/addon-resizer) 来扩展 Metrics Server。Addon Resizer 根据工作节点的数量按比例垂直扩展，而 VPA 根据 CPU 和内存使用情况进行扩展。

## CoreDNS lameduck 持续时间

Pod 使用 `kube-dns` 服务进行名称解析。Kubernetes 使用目标 NAT (DNAT) 将 `kube-dns` 流量从节点重定向到 CoreDNS 后端 Pod。当你扩展 CoreDNS 部署时，`kube-proxy` 会更新节点上的 iptables 规则和链，以将 DNS 流量重定向到 CoreDNS Pod。根据集群的大小，传播新的端点(扩展时)和删除规则(缩减 CoreDNS 时)可能需要 1 到 10 秒。

这种传播延迟可能会导致 DNS 查找失败，因为 CoreDNS Pod 被终止，但节点的 iptables 规则尚未更新。在这种情况下，节点可能会继续向已终止的 CoreDNS Pod 发送 DNS 查询。

你可以通过在 CoreDNS Pod 中设置 [lameduck](https://coredns.io/plugins/health/) 持续时间来减少 DNS 查找失败。在 lameduck 模式下，CoreDNS 将继续响应正在进行的请求。设置 lameduck 持续时间将延迟 CoreDNS 关闭过程，让节点有时间更新其 iptables 规则和链。

我们建议将 CoreDNS lameduck 持续时间设置为 30 秒。

## CoreDNS 就绪探针

我们建议使用 `/ready` 而不是 `/health` 作为 CoreDNS 的就绪探针。

与之前建议将 lameduck 持续时间设置为 30 秒相一致，在 Pod 终止之前提供足够的时间让节点的 iptables 规则得到更新，使用 `/ready` 而不是 `/health` 作为 CoreDNS 就绪探针可确保 CoreDNS Pod 在启动时就完全准备好及时响应 DNS 请求。

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8181
    scheme: HTTP
```

有关 CoreDNS Ready 插件的更多信息，请参阅 [https://coredns.io/plugins/ready/](https://coredns.io/plugins/ready/)

## 日志和监控代理

日志和监控代理可能会给你的集群控制平面带来大量负载，因为代理会查询 API 服务器以丰富日志和指标的工作负载元数据。节点上的代理只能访问本地节点资源，看到诸如容器和进程名称之类的内容。查询 API 服务器可以添加更多详细信息，如 Kubernetes 部署名称和标签。这对于故障排查非常有帮助，但对于扩展来说是有害的。

由于日志和监控的选项有很多种，我们无法为每个提供商展示示例。对于 [fluentbit](https://docs.fluentbit.io/manual/pipeline/filters/kubernetes),我们建议启用 Use_Kubelet 从本地 kubelet 而不是 Kubernetes API 服务器获取元数据，并将 `Kube_Meta_Cache_TTL` 设置为一个数字，以减少重复调用时可以缓存数据(例如 60)。

扩展监控和日志有两个通用选项：

* 禁用集成
* 采样和过滤

禁用集成通常是不可能的，因为你会丢失日志元数据。这将消除 API 扩展问题，但会引入其他问题，因为在需要时没有所需的元数据。

采样和过滤可以减少收集的指标和日志的数量。这将降低对 Kubernetes API 的请求数量，并减少存储收集的指标和日志所需的空间。减少存储成本将降低整个系统的成本。

配置采样的能力取决于代理软件，可以在引入的不同点实现。尽可能靠近代理添加采样很重要，因为 API 服务器调用可能发生在那里。请联系你的提供商以了解有关采样支持的更多信息。

如果你正在使用 CloudWatch 和 CloudWatch Logs，你可以使用[文档中描述的模式](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html)添加代理过滤。

为了避免丢失日志和指标，你应该将数据发送到一个可以在接收端发生故障时缓冲数据的系统。使用 fluentbit，你可以使用 [Amazon Kinesis Data Firehose](https://docs.fluentbit.io/manual/pipeline/outputs/firehose) 暂时保留数据，这可以减少过载最终数据存储位置的机会。