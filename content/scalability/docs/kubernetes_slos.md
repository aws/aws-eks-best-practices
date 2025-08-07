---
redirect: https://docs.aws.amazon.com/eks/latest/best-practices/kubernetes_upstream_slos.html
---


!!! info "We've Moved to the AWS Docs! 🚀"
    This content has been updated and relocated to improve your experience. 
    Please visit our new site for the latest version:
    [AWS EKS Best Practices Guide](https://docs.aws.amazon.com/eks/latest/best-practices/kubernetes_upstream_slos.html) on the AWS Docs

    Bookmarks and links will continue to work, but we recommend updating them for faster access in the future.

---

# Kubernetes Upstream SLOs

Amazon EKS runs the same code as the upstream Kubernetes releases and ensures that EKS clusters operate within the SLOs defined by the Kubernetes community. The Kubernetes[Scalability Special Interest Group (SIG)](https://github.com/kubernetes/community/tree/master/sig-scalability) defines the scalability goals and investigates bottlenecks in performance through SLIs and SLOs. 

SLIs are how we measure a system like metrics or measures that can be used to determine how “well” the system is running, e.g. request latency or count. SLOs define the values that are expected for when the system is running “well”, e.g. request latency remains less than 3 seconds. The Kubernetes SLOs and SLIs focus on the performance of the Kubernetes components and are completely independent from the Amazon EKS Service SLAs which focus on availability of the EKS cluster endpoint.

Kubernetes has a number of features that allow users to extend the system with custom add-ons or drivers, like CSI drivers, admission webhooks, and auto-scalers. These extensions can drastically impact the performance of a Kubernetes cluster in different ways, i.e. an admission webhook with `failurePolicy=Ignore` could add latency to K8s API requests if the webhook target is unavailable. The Kubernetes Scalability SIG defines scalability using a ["you promise, we promise" framework](https://github.com/kubernetes/community/blob/master/sig-scalability/slos/slos.md#how-we-define-scalability):


> If you promise to:  
>     - correctly configure your cluster  
>     - use extensibility features "reasonably"  
>     - keep the load in the cluster within [recommended limits](https://github.com/kubernetes/community/blob/master/sig-scalability/configs-and-limits/thresholds.md)  
> 
> then we promise that your cluster scales, i.e.:  
>     - all the SLOs are satisfied.   

## Kubernetes SLOs
The Kubernetes SLOs don't account for all of the plugins and external limitations that could impact a cluster, such as worker node scaling or admission webhooks. These SLOs focus on [Kubernetes components](https://kubernetes.io/docs/concepts/overview/components/) and ensure that Kubernetes actions and resources are operating within expectations. The SLOs help Kubernetes developers ensure that changes to Kubernetes code do not degrade performance for the entire system.

The [Kuberntes Scalability SIG defines the following official SLO/SLIs](https://github.com/kubernetes/community/blob/master/sig-scalability/slos/slos.md). The Amazon EKS team regularly runs scalability tests on EKS clusters for these SLOs/SLIs to monitor for performance degradation as changes are made and new versions are released.


|Objective	|Definition	|SLO	|
|---	|---	|---	|
|API request latency (mutating)	|Latency of processing mutating  API calls for single objects for every (resource, verb) pair, measured as 99th percentile over last 5 minutes	|In default Kubernetes installation, for every (resource, verb) pair, excluding virtual and aggregated resources and Custom Resource Definitions, 99th percentile per cluster-day <= 1s	|
|API request latency (read-only)	|Latency of processing non-streaming read-only API calls for every (resource, scope) pair, measured as 99th percentile over last 5 minutes	|In default Kubernetes installation, for every (resource, scope) pair, excluding virtual and aggregated resources and Custom Resource Definitions, 99th percentile per cluster-day: (a) <= 1s if `scope=resource` (b) <= 30s otherwise (if `scope=namespace` or `scope=cluster`)	|
|Pod startup latency	|Startup latency of schedulable stateless pods, excluding time to pull images and run init containers, measured from pod creation timestamp to when all its containers are reported as started and observed via watch, measured as 99th percentile over last 5 minutes	|In default Kubernetes installation, 99th percentile per cluster-day <= 5s	|

### API Request Latency 

The `kube-apiserver` has `--request-timeout` defined as `1m0s` by default, which means a request can run for up to one minute (60 seconds) before being timed out and cancelled. The SLOs defined for Latency are broken out by the type of request that is being made, which can be mutating or read-only:

#### Mutating

Mutating requests in Kubernetes make changes to a resource, such as creations, deletions, or updates. These requests are expensive because those changes must be written to [the etcd backend](https://kubernetes.io/docs/concepts/overview/components/#etcd) before the updated object is returned. [Etcd](https://etcd.io/) is a distributed key-value store that is used for all Kubernetes cluster data.

This latency is measured as the 99th percentile over 5min for (resource, verb) pairs of Kubernetes resources, for example this would measure the latency for Create Pod requests and Update Node requests. The request latency must be <= 1 second to satisfy the SLO.

#### Read-only

Read-only requests retrieve a single resource (such as Get Pod X) or a collection (such as “Get all Pods from Namespace X”). The `kube-apiserver` maintains a cache of objects, so the requested resources may be returned from cache or they may need to be retrieved from etcd first. 
These latencies are also measured by the 99th percentile over 5 minutes, however read-only requests can have separate scopes. The SLO defines two different objectives:

* For requests made for a *single* resource (i.e. `kubectl get pod -n mynamespace my-controller-xxx` ), the request latency should remain <= 1 second.
* For requests that are made for multiple resources in a namespace or a cluster (for example, `kubectl get pods -A`) the latency should remain <= 30 seconds

The SLO has different target values for different request scopes because requests made for a list of Kubernetes resources expect the details of all objects in the request to be returned within the SLO. On large clusters, or large collections of resources, this can result in large response sizes which can take some time to return. For example, in a cluster running tens of thousands of Pods with each Pod being roughly 1 KiB when encoded in JSON, returning all Pods in the cluster would consist of 10MB or more. Kubernetes clients can help reduce this response size [using APIListChunking to retrieve large collections of resources](https://kubernetes.io/docs/reference/using-api/api-concepts/#retrieving-large-results-sets-in-chunks). 

### Pod Startup Latency

This SLO is primarily concerned with the time it takes from Pod creation to when the containers in that Pod actually begin execution. To measure this the difference from the creation timestamp recorded on the Pod, and when [a WATCH on that Pod](https://kubernetes.io/docs/reference/using-api/api-concepts/#efficient-detection-of-changes) reports the containers have started is calculated (excluding time for container image pulls and init container execution). To satisfy the SLO the 99th percentile per cluster-day of this Pod Startup Latency must remain <=5 seconds. 

Note that this SLO assumes that the worker nodes already exist in this cluster in a ready state for the Pod to be scheduled on. This SLO does not account for image pulls or init container executions, and also limits the test to “stateless pods” which don't leverage persistent storage plugins. 

## Kubernetes SLI Metrics 

Kubernetes is also improving the Observability around the SLIs by adding [Prometheus metrics](https://prometheus.io/docs/concepts/data_model/) to Kubernetes components that track these SLIs over time. Using [Prometheus Query Language (PromQL)](https://prometheus.io/docs/prometheus/latest/querying/basics/) we can build queries that display the SLI performance over time in tools like Prometheus or Grafana dashboards, below are some examples for the SLOs above.

### API Server Request Latency

|Metric	|Definition	|
|---	|---	|
|apiserver_request_sli_duration_seconds	| Response latency distribution (not counting webhook duration and priority & fairness queue wait times) in seconds for each verb, group, version, resource, subresource, scope and component.	|
|apiserver_request_duration_seconds	| Response latency distribution in seconds for each verb, dry run value, group, version, resource, subresource, scope and component.	|  

*Note: The `apiserver_request_sli_duration_seconds` metric is available starting in Kubernetes 1.27.*

You can use these metrics to investigate the API Server response times and if there are bottlenecks in the Kubernetes components or other plugins/components. The queries below are based on [the community SLO dashboard](https://github.com/kubernetes/perf-tests/tree/master/clusterloader2/pkg/prometheus/manifests/dashboards). 

**API Request latency SLI (mutating)** - this time does *not* include webhook execution or time waiting in queue.   
`histogram_quantile(0.99, sum(rate(apiserver_request_sli_duration_seconds_bucket{verb=~"CREATE|DELETE|PATCH|POST|PUT", subresource!~"proxy|attach|log|exec|portforward"}[5m])) by (resource, subresource, verb, scope, le)) > 0`

**API Request latency Total (mutating)** - this is the total time the request took on the API server, this time may be longer than the SLI time because it includes webhook execution and API Priority and Fairness wait times.  
`histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb=~"CREATE|DELETE|PATCH|POST|PUT", subresource!~"proxy|attach|log|exec|portforward"}[5m])) by (resource, subresource, verb, scope, le)) > 0`

In these queries we are excluding the streaming API requests which do not return immediately, such as `kubectl port-forward` or `kubectl exec` requests (`subresource!~"proxy|attach|log|exec|portforward"`), and we are filtering for only the Kubernetes verbs that modify objects (`verb=~"CREATE|DELETE|PATCH|POST|PUT"`). We are then calculating the 99th percentile of that latency over the last 5 minutes.

We can use a similar query for the read only API requests, we simply modify the verbs we're filtering for to include the Read only actions `LIST` and `GET`. There are also different SLO thresholds depending on the scope of the request, i.e. getting a single resource or listing a number of resources.

**API Request latency SLI  (read-only)** - this time does *not* include webhook execution or time waiting in queue.
For a single resource (scope=resource, threshold=1s)  
`histogram_quantile(0.99, sum(rate(apiserver_request_sli_duration_seconds_bucket{verb=~"GET", scope=~"resource"}[5m])) by (resource, subresource, verb, scope, le))`

For a collection of resources in the same namespace (scope=namespace, threshold=5s)  
`histogram_quantile(0.99, sum(rate(apiserver_request_sli_duration_seconds_bucket{verb=~"LIST", scope=~"namespace"}[5m])) by (resource, subresource, verb, scope, le))`

For a collection of resources across the entire cluster (scope=cluster, threshold=30s)  
`histogram_quantile(0.99, sum(rate(apiserver_request_sli_duration_seconds_bucket{verb=~"LIST", scope=~"cluster"}[5m])) by (resource, subresource, verb, scope, le))`

**API Request latency Total (read-only)** - this is the total time the request took on the API server, this time may be longer than the SLI time because it includes webhook execution and wait times.
For a single resource (scope=resource, threshold=1s)  
`histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb=~"GET", scope=~"resource"}[5m])) by (resource, subresource, verb, scope, le))`

For a collection of resources in the same namespace (scope=namespace, threshold=5s)  
`histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb=~"LIST", scope=~"namespace"}[5m])) by (resource, subresource, verb, scope, le))`

For a collection of resources across the entire cluster (scope=cluster, threshold=30s)  
`histogram_quantile(0.99, sum(rate(apiserver_request_duration_seconds_bucket{verb=~"LIST", scope=~"cluster"}[5m])) by (resource, subresource, verb, scope, le))`

The SLI metrics provide insight into how Kubernetes components are performing by excluding the time that requests spend waiting in API Priority and Fairness queues, working through admission webhooks, or other Kubernetes extensions. The total metrics provide a more holistic view as it reflects the time your applications would be waiting for a response from the API server. Comparing these metrics can provide insight into where the delays in request processing are being introduced. 

### Pod Startup Latency

|Metric	| Definition	|
|---	|---	|
|kubelet_pod_start_sli_duration_seconds	|Duration in seconds to start a pod, excluding time to pull images and run init containers, measured from pod creation timestamp to when all its containers are reported as started and observed via watch	|
|kubelet_pod_start_duration_seconds	|Duration in seconds from kubelet seeing a pod for the first time to the pod starting to run. This does not include the time to schedule the pod or scale out worker node capacity.	|

*Note:  `kubelet_pod_start_sli_duration_seconds` is available starting in Kubernetes 1.27.*

Similar to the queries above you can use these metrics to gain insight into how long node scaling, image pulls and init containers are delaying the pod launch compared to Kubelet actions. 

**Pod startup latency SLI -** this is the time from the pod being created to when the application containers reported as running. This includes the time it takes for the worker node capacity to be available and the pod to be scheduled, but this does not include the time it takes to pull images or for the init containers to run.  
`histogram_quantile(0.99, sum(rate(kubelet_pod_start_sli_duration_seconds_bucket[5m])) by (le))`

**Pod startup latency Total -** this is the time it takes the kubelet to start the pod for the first time. This is measured from when the kubelet recieves the pod via WATCH, which does not include the time for worker node scaling or scheduling. This includes the time to pull images and init containers to run.  
`histogram_quantile(0.99, sum(rate(kubelet_pod_start_duration_seconds_bucket[5m])) by (le))`



## SLOs on Your Cluster

If you are collecting the Prometheus metrics from the Kubernetes resources in your EKS cluster you can gain deeper insights into the performance of the Kubernetes control plane components. 

The [perf-tests repo](https://github.com/kubernetes/perf-tests/) includes Grafana dashboards that display the latencies and critical performance metrics for the cluster during tests. The perf-tests configuration leverages the [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack), an open source project that comes configured to collect Kubernetes metrics, but you can also [use Amazon Managed Prometheus and Amazon Managed Grafana.](https://aws-observability.github.io/terraform-aws-observability-accelerator/eks/)

If you are using the `kube-prometheus-stack` or similar Prometheus solution you can install the same dashboard to observe the SLOs on your cluster in real time. 

1. You will first need to install the Prometheus Rules that are used in the dashboards with `kubectl apply -f prometheus-rules.yaml`. You can download a copy of the rules here: https://github.com/kubernetes/perf-tests/blob/master/clusterloader2/pkg/prometheus/manifests/prometheus-rules.yaml
    1. Be sure to check the namespace in the file matches your environment
    2. Verify that the labels match the `prometheus.prometheusSpec.ruleSelector` helm value if you are using `kube-prometheus-stack`
2. You can then install the dashboards in Grafana. The json dashboards and python scripts to generate them are available here: https://github.com/kubernetes/perf-tests/tree/master/clusterloader2/pkg/prometheus/manifests/dashboards
    1. [the `slo.json` dashboard](https://github.com/kubernetes/perf-tests/blob/master/clusterloader2/pkg/prometheus/manifests/dashboards/slo.json) displays the performance of the cluster in relation to the Kubernetes SLOs

Consider that the SLOs are focused on the performance of the Kubernetes components in your clusters, but there are additional metrics you can review which provide different perspectives or insights in to your cluster. Kubernetes community projects like [Kube-state-metrics](https://github.com/kubernetes/kube-state-metrics/tree/main) can help you quickly analyze trends in your cluster. Most common plugins and drivers from the Kubernetes community also emit Prometheus metrics, allowing you to investigate things like autoscalers or custom schedulers.  

The [Observability Best Practices Guide](https://aws-observability.github.io/observability-best-practices/guides/containers/oss/eks/best-practices-metrics-collection/#control-plane-metrics) has examples of other Kubernetes metrics you can use to gain further insight. 






