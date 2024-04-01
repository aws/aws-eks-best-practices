# Kubernetes上游SLO

Amazon EKS运行与上游Kubernetes版本相同的代码，并确保EKS集群在Kubernetes社区定义的SLO范围内运行。Kubernetes[可扩展性特别兴趣小组(SIG)](https://github.com/kubernetes/community/tree/master/sig-scalability)定义了可扩展性目标，并通过SLI和SLO调查性能瓶颈。

SLI是我们衡量系统的方式，如指标或可用于确定系统运行"良好"程度的度量，例如请求延迟或计数。SLO定义了系统运行"良好"时的预期值，例如请求延迟保持在3秒以下。Kubernetes SLO和SLI专注于Kubernetes组件的性能，与关注EKS集群端点可用性的Amazon EKS服务SLA完全无关。

Kubernetes有许多功能允许用户使用自定义插件或驱动程序扩展系统，如CSI驱动程序、准入Webhook和自动扩缩器。这些扩展可能会以不同的方式极大影响Kubernetes集群的性能，即如果Webhook目标不可用，具有`failurePolicy=Ignore`的准入Webhook可能会增加K8s API请求的延迟。Kubernetes可扩展性SIG使用["你承诺，我们承诺"框架](https://github.com/kubernetes/community/blob/master/sig-scalability/slos/slos.md#how-we-define-scalability)定义可扩展性：

> 如果你承诺：
>     - 正确配置集群
>     - 合理使用可扩展性功能
>     - 将集群负载保持在[推荐限制](https://github.com/kubernetes/community/blob/master/sig-scalability/configs-and-limits/thresholds.md)内
>
> 那么我们承诺集群可扩展，即：
>     - 满足所有SLO

## Kubernetes SLO
Kubernetes SLO不考虑可能影响集群的所有插件和外部限制，如工作节点扩缩或准入Webhook。这些SLO专注于[Kubernetes组件](https://kubernetes.io/docs/concepts/overview/components/),并确保Kubernetes操作和资源在预期范围内运行。SLO帮助Kubernetes开发人员确保对Kubernetes代码的更改不会降低整个系统的性能。

[Kuberntes可扩展性SIG定义了以下官方SLO/SLI](https://github.com/kubernetes/community/blob/master/sig-scalability/slos/slos.md)。Amazon EKS团队定期在EKS集群上运行这些SLO/SLI的可扩展性测试，以监控随着更改和新版本发布而可能出现的性能下降。

|目标	|定义	|SLO	|
|---	|---	|---	|
|API请求延迟(变更)	|对每个(资源、动词)对的单个对象进行变更API调用的处理延迟，以过去5分钟的99百分位数衡量	|在默认Kubernetes安装中，对于每个(资源、动词)对，不包括虚拟和聚合资源以及自定义资源定义，每集群日99百分位数<=1秒	|
|API请求延迟(只读)	|对每个(资源、范围)对进行非流式只读API调用的处理延迟，以过去5分钟的99百分位数衡量	|在默认Kubernetes安装中，对于每个(资源、范围)对，不包括虚拟和聚合资源以及自定义资源定义，每集群日99百分位数：(a)如果`scope=resource`则<=1秒(b)否则(如果`scope=namespace`或`scope=cluster`)<=30秒	|
|Pod启动延迟	|可调度无状态Pod的启动延迟，不包括拉取镜像和运行初始化容器的时间，从Pod创建时间戳到通过监视观察到所有容器报告已启动为止，以过去5分钟的99百分位数衡量	|在默认Kubernetes安装中，每集群日99百分位数<=5秒	|

### API请求延迟

`kube-apiserver`默认将`--request-timeout`定义为`1m0s`,这意味着请求在被超时和取消之前最多可以运行一分钟(60秒)。延迟的定义SLO根据请求的类型(变更或只读)进行了细分：

#### 变更

Kubernetes中的变更请求会对资源进行更改，如创建、删除或更新。这些请求代价很高，因为在返回更新后的对象之前，这些更改必须写入[etcd后端](https://kubernetes.io/docs/concepts/overview/components/#etcd)。[Etcd](https://etcd.io/)是用于所有Kubernetes集群数据的分布式键值存储。

该延迟以Kubernetes资源(资源、动词)对的过去5分钟的99百分位数衡量，例如，它将测量创建Pod请求和更新节点请求的延迟。为满足SLO，请求延迟必须<=1秒。

#### 只读

只读请求检索单个资源(如获取Pod X)或集合(如"从命名空间X获取所有Pod")。`kube-apiserver`维护对象的缓存，因此请求的资源可能来自缓存，也可能需要先从etcd检索。
这些延迟也是以5分钟的99百分位数衡量，但只读请求可能有不同的范围。SLO定义了两个不同的目标：

* 对于针对*单个*资源的请求(即`kubectl get pod -n mynamespace my-controller-xxx`)的请求延迟应保持在<=1秒。
* 对于针对同一命名空间或整个集群中多个资源的请求(例如`kubectl get pods -A`),延迟应保持在<=30秒

SLO对不同请求范围有不同的目标值，因为对Kubernetes资源集合的请求期望在SLO内返回请求中所有对象的详细信息。在大型集群或大型资源集合中，这可能会导致较大的响应大小，从而需要一些时间才能返回。例如，在运行数万个Pod的集群中，每个Pod在编码为JSON时大约为1KiB，返回集群中所有Pod将包含10MB或更多数据。Kubernetes客户端可以[使用APIListChunking以块的形式检索大型资源集合](https://kubernetes.io/docs/reference/using-api/api-concepts/#retrieving-large-results-sets-in-chunks),从而减小响应大小。

### Pod启动延迟

此SLO主要关注从Pod创建到该Pod中的容器实际开始执行所需的时间。为了测量这一点，计算从记录在Pod上的创建时间戳到[对该Pod进行WATCH](https://kubernetes.io/docs/reference/using-api/api-concepts/#efficient-detection-of-changes)报告容器已启动时的时间差(不包括拉取容器镜像和运行初始化容器的时间)。为满足SLO，每集群日Pod启动延迟的99百分位数必须保持在<=5秒。

请注意，此SLO假设工作节点已在该集群中存在并处于就绪状态，以便调度Pod。此SLO不考虑镜像拉取或初始化容器执行，并且还将测试限制为不使用持久存储插件的"无状态Pod"。

## Kubernetes SLI指标

Kubernetes还通过向Kubernetes组件添加[Prometheus指标](https://prometheus.io/docs/concepts/data_model/)来跟踪这些SLI随时间的变化，从而改善了对SLI的可观察性。使用[Prometheus查询语言(PromQL)](https://prometheus.io/docs/prometheus/latest/querying/basics/),我们可以构建查询，在Prometheus或Grafana仪表板等工具中显示SLI性能随时间的变化，下面是上述SLO的一些示例。

### API服务器请求延迟

|指标	|定义	|
|---	|---	|
|apiserver_request_sli_duration_seconds	|针对每个动词、组、版本、资源、子资源、范围和组件的响应延迟分布(不包括Webhook持续时间和优先级及公平队列等待时间)，单位为秒	|
|apiserver_request_duration_seconds	|针对每个动词、dry run值、组、版本、资源、子资源、范围和组件的响应延迟分布，单位为秒	|

*注意：从Kubernetes 1.27开始提供`apiserver_request_sli_duration_seconds`指标。*

您可以使用这些指标来调查API服务器响应时间，以及Kubernetes组件或其他插件/组件中是否存在瓶颈。下面的查询基于[社区SLO仪表板](https://github.com/kubernetes/perf-tests/tree/master/clusterloader2/pkg/prometheus/manifests/dashboards)。

**API请求延迟SLI(变更)** - 此时间*不包括*Webhook执行或队列等待时间。
`histogram_quantile(0.99, sum(rate(apiserver_request_sli_duration_seconds_bucket{verb=~"CREATE|DELETE|PATCH|POST|PUT", subresource!~"proxy|attach|log|exec|portforward"}[5m])) by (resource, subresource, verb, scope, le)) > 0`

**API请求延迟总时间(变更)** - 这是请求在API服务器上花费的总时间，此时间可能比SLI时间长，因为它包括Webhook执行和API优先级和公平等待时间。
`histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb=~"CREATE|DELETE|PATCH|POST|PUT", subresource!~"proxy|attach|log|exec|portforward"}[5m])) by (resource, subresource, verb, scope, le)) > 0`

在这些查询中，我们排除了不立即返回的流式API请求，如`kubectl port-forward`或`kubectl exec`请求(`subresource!~"proxy|attach|log|exec|portforward"`),并且我们只过滤修改对象的Kubernetes动词(`verb=~"CREATE|DELETE|PATCH|POST|PUT"`),然后计算过去5分钟的99百分位延迟。

我们可以使用类似的查询来查看只读API请求，只需修改我们过滤的动词以包含只读操作`LIST`和`GET`即可。根据请求的范围(即获取单个资源或列出多个资源)，SLO阈值也有所不同。

**API请求延迟SLI(只读)** - 此时间*不包括*Webhook执行或队列等待时间。
对于单个资源(scope=resource,阈值=1秒)
`histogram_quantile(0.99, sum(rate(apiserver_request_sli_duration_seconds_bucket{verb=~"GET", scope=~"resource"}[5m])) by (resource, subresource, verb, scope, le))`

对于同一命名空间中的资源集合(scope=namespace,阈值=5秒)
`histogram_quantile(0.99, sum(rate(apiserver_request_sli_duration_seconds_bucket{verb=~"LIST", scope=~"namespace"}[5m])) by (resource, subresource, verb, scope, le))`

对于整个集群中的资源集合(scope=cluster,阈值=30秒)
`histogram_quantile(0.99, sum(rate(apiserver_request_sli_duration_seconds_bucket{verb=~"LIST", scope=~"cluster"}[5m])) by (resource, subresource, verb, scope, le))`

**API请求延迟总时间(只读)** - 这是请求在API服务器上花费的总时间，此时间可能比SLI时间长，因为它包括Webhook执行和等待时间。
对于单个资源(scope=resource,阈值=1秒)
`histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb=~"GET", scope=~"resource"}[5m])) by (resource, subresource, verb, scope, le))`

对于同一命名空间中的资源集合(scope=namespace,阈值=5秒)
`histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb=~"LIST", scope=~"namespace"}[5m])) by (resource, subresource, verb, scope, le))`

对于整个集群中的资源集合(scope=cluster,阈值=30秒)
`histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb=~"LIST", scope=~"cluster"}[5m])) by (resource, subresource, verb, scope, le))`

SLI指标提供了对Kubernetes组件性能的洞见，因为它们排除了请求在API优先级和公平队列、通过准入Webhook或其他Kubernetes扩展时花费的时间。总体指标提供了更全面的视角，因为它反映了应用程序等待API服务器响应的时间。比较这些指标可以提供请求处理延迟引入的见解。

### Pod启动延迟

|指标	|定义	|
|---	|---	|
|kubelet_pod_start_sli_duration_seconds	|启动Pod所需的时间(秒)，不包括拉取镜像和运行初始化容器的时间，从Pod创建时间戳到通过监视观察到所有容器已启动为止	|
|kubelet_pod_start_duration_seconds	|从kubelet第一次看到Pod到Pod开始运行所需的时间(秒)。这不包括调度Pod或扩展工作节点容量所需的时间。	|

*注意：`kubelet_pod_start_sli_duration_seconds`从Kubernetes 1.27开始提供。*

与上面的查询类似，您可以使用这些指标来了解节点扩缩、镜像拉取和初始化容器执行延迟Pod启动的程度，与Kubelet操作相比。

**Pod启动延迟SLI -** 这是从Pod创建到应用程序容器报告为运行所需的时间。这包括工作节点容量可用和Pod被调度所需的时间，但不包括拉取镜像或初始化容器运行所需的时间。
`histogram_quantile(0.99, sum(rate(kubelet_pod_start_sli_duration_seconds_bucket[5m])) by (le))`

**Pod启动延迟总时间 -** 这是kubelet启动Pod所需的时间。这是从kubelet通过WATCH接收Pod开始测量的，不包括节点扩缩或调度所需的时间。这包括拉取镜像和初始化容器运行所需的时间。
`histogram_quantile(0.99, sum(rate(kubelet_pod_start_duration_seconds_bucket[5m])) by (le))`

## 集群上的SLO

如果您正在从EKS集群中的Kubernetes资源收集Prometheus指标，您可以更深入地了解Kubernetes控制平面组件的性能。

[perf-tests仓库](https://github.com/kubernetes/perf-tests/)包括Grafana仪表板，用于显示测试期间集群的延迟和关键性能指标。perf-tests配置利用了[kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack),这是一个开源项目，预配置为收集Kubernetes指标，但您也可以[使用Amazon Managed Prometheus和Amazon Managed Grafana。](https://aws-observability.github.io/terraform-aws-observability-accelerator/eks/)

如果您使用的是`kube-prometheus-stack`或类似的Prometheus解决方案，您可以安装相同的仪表板来实时观察集群上的SLO。

1. 您首先需要使用`kubectl apply -f prometheus-rules.yaml`安装仪表板中使用的Prometheus规则。您可以从这里下载规则副本：https://github.com/kubernetes/perf-tests/blob/master/clusterloader2/pkg/prometheus/manifests/prometheus-rules.yaml
    1. 确保文件中的命名空间与您的环境匹配
    2. 如果您使用`kube-prometheus-stack`,请验证标签是否与`prometheus.prometheusSpec.ruleSelector`helm值匹配
2. 然后，您可以在Grafana中安装仪表板。json仪表板和生成它们的python脚本可在此处获得：https://github.com/kubernetes/perf-tests/tree/master/clusterloader2/pkg/prometheus/manifests/dashboards
    1. [`slo.json`仪表板](https://github.com/kubernetes/perf-tests/blob/master/clusterloader2/pkg/prometheus/manifests/dashboards/slo.json)显示了集群相对于Kubernetes SLO的性能

请考虑SLO专注于集群中Kubernetes组件的性能，但您还可以查看其他指标，这些指标可以提供不同的视角或对集群的见解。像[Kube-state-metrics](https://github.com/kubernetes/kube-state-metrics/tree/main)这样的Kubernetes社区项目可以帮助您快速分析集群中的趋势。来自Kubernetes社区的大多数常见插件和驱动程序也会发出Prometheus指标，允许您调查自动扩缩器或自定义调度程序等内容。

[可观察性最佳实践指南](https://aws-observability.github.io/observability-best-practices/guides/containers/oss/eks/best-practices-metrics-collection/#control-plane-metrics)提供了您可以使用的其他Kubernetes指标示例，以获得更深入的见解。