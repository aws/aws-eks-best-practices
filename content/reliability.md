# Reliability Pillar

The reliability pillar encompasses the ability of a system to recover itself from infrastructure or service disruptions, dynamically acquiring computing resources to meet demand, and mitigate disruptions such as misconfigurations or transient network issues.

Containers must be measured on at least two dimensions in terms of reliability. First, can the container be made reliable and recover from a transient failure, and second, can both the container and the underlying host meet changing demand based on CPU, memory, or custom metrics.

## Design Principles

There are five design principles for reliability in the cloud:

* Automatic recovery from failure
* Horizontal scaling to increase aggregate system availability
* Automatic scaling
* Automatic changes

To achieve reliability, a system must have a well-planned foundation and monitoring in place, with mechanisms for handling changes in demand or requirements. The system should be designed to detect failure and automatically heal itself.

## Best Practices
### Reliability of EKS Clusters
Amazon EKS provides a highly-available control plane that runs across multiple availability zones in AWS Region. EKS automatically manages the availability and scalability of the Kubernetes API servers and the etcd persistence layer for each cluster. Amazon EKS runs the Kubernetes control plane across three Availability Zones in order to ensure high availability, and it automatically detects and replaces unhealthy masters. Hence, reliability of an EKS cluster is not a customer responsibility, it is already built-in.

### Understanding service limits
AWS sets service limits (an upper limit on the number of each resource your team can request) to protect you from accidentally over-provisioning resources. [Amazon EKS Service Quotas](https://docs.aws.amazon.com/eks/latest/userguide/service-quotas.html) lists the service limits. There are two types of limits, soft limits, that can be changed with proper justification via a support ticket. Hard limits cannot be changed. Because of this, you should carefully architect your applications keeping these limits in mind. Consider reviewing these service limits periodically and apply them during your application design. 

Besides the limits from orchestration engines, there are limits in other AWS services, such as Elastic Load Balancing (ELB) and Amazon VPC, that may affect your application performance.
More about EC2 limits here: [EC2 service limits](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-resource-limits.html). 

### Networking considerations
When you create an EKS cluster, you need to specify the VPC subnets for your cluster to use, EKS requires subnets in at least two Availabiilty Zones. The subnets that you pass when you create the cluster influence where Amazon EKS places elastic network interfaces that are used for the control plane to worker node communication. We recommend a network architecture that uses private subnets for your worker nodes and public subnets for Kubernetes to create internet-facing load balancers within. [EKS documentation](https://docs.aws.amazon.com/eks/latest/userguide/network_reqs.html) includes more information about VPC considerations for EKS clusters.

If your cluster has high pod churn rate, then you may also create additional subnets in each Availability Zone, in this case container autoscaling will not affect IP address allocation of other resources in your VPC. This can be specified by customizing the Amazon VPC CNI. 

### Amazon VPC CNI
With Amazon EKS, the default networking driver is [Amazon VPC CNI](https://github.com/aws/amazon-vpc-cni-k8s). The CNI plugin allocates VPC IP addresses to Kubernetes pods and it uses [Elastic Network Interface (ENI)](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html) for this purpose. Each EC2 Instance is bound by the number of elastic network interfaces that can be attached and the number of secondary IP addresses it can consume. Hence, the number of pods you can run on a particular EC2 Instance depends on how many ENIs can be attached to it.

This [file](https://github.com/awslabs/amazon-eks-ami/blob/master/files/eni-max-pods.txt) is helpful when determining how many pods an EC2 instance can run.

The CNI plugin has two componenets:

* [CNI plugin](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/network-plugins/#cni), which will wire up host’s and pod’s network stack when called.
* `L-IPAMD` (aws-node daemonSet) runs on every node is a long running node-Local IP Address Management (IPAM) daemon and is responsible for:
    * maintaining a warm-pool of available IP addresses, and
    * assigning an IP address to a Pod.

The CNI caches a certain number of IP addresses so that Kubernetes scheduler can schedule pods on these worker nodes. The IP addresses are available on the worker nodes whether you launch pods or not. If you need to constrain these IP addresses, you can customize them at the worker node level. The CNI supports customization of a number of configurations options, these options are set through environment variables. To configure these options, you can download aws-k8s-cni.yaml compatible
with your cluster and set environment variables. At the time of writing, the latest release is located here https://github.com/aws/amazon-vpc-cni-k8s/blob/master/config/v1.6/aws-k8s-cni.yaml .

If you do not have enough IP addresses available in the subnet that the CNI uses, your pods will not an IP address, and the pods will remain in pending state until an IP address is released from use.

[CNI Metrics Helper](https://docs.aws.amazon.com/eks/latest/userguide/cni-metrics-helper.html) is a tool that can help you monitor number of IP addresses that are available and in use. 

### Scaling Kubernetes applications
When it comes to scaling your applications in Kubernetes, you need to think about two components in your application architecture, first your Kubernetes Worker Nodes and the application pods themselves.

There are two common ways to scale worker nodes in EKS. 

1. [Cluster Autoscaler](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md) 
2. [EC2 Auto Scaling Groups](https://docs.aws.amazon.com/autoscaling/ec2/userguide/AutoScalingGroup.html)


### Scaling Kubernetes worker nodes
Cluster Autoscaler is the preferred way to automatically scale EC2 worker nodes in EKS even though it performs reactive scaling. Cluster Autoscaler will adjust the size of your Kubernetes cluster when there are pods that cannot be run because the cluster has insufficient resources and adding another worker node would help. On the other hand, if a worker node is consistently underutilized and all of its pods can be scheduled on other worker nodes, Cluster Autoscaler will terminate it. 

Cluster Autoscaler uses EC2 Auto Scaling groups (ASG) to adjust the size of the cluster. Typically all worker nodes are part of an auto scaling group. You may have multiple ASGs within a cluster. For example, if you co-locate two distinct workloads in your cluster you may want to use two different types of EC2 instances, each suited for its workload. In this case you would have two auto scaling groups. 

Another reason for having multiple ASGs is if you use EBS to provide persistent
volumes for your pods or using statefulsets. At the time of writing, EBS volumes are only available within a single AZ. When your pods use EBS for storage, they need to reside in the same AZ as the EBS volume. In other words, a pod running in an AZ cannot access EBS volumes in another AZ. For this reason the scheduler needs to know that if a pod that uses an EBS volume crashes or gets terminated, it needs to be scheduled on a worker node in the same AZ, or else it will not be able to access the volume. 

Using [EFS](https://github.com/kubernetes-sigs/aws-efs-csi-driver) can simplify cluster autoscaling when running applications that need persistent storage. In EFS, a file system can be concurrently accessed from all the AZs in the region, this means if you persistent storage using pod ceases to exist, and is resurrected in another AZ, it will still have access to the data stored by its predecessor.

If you are using EBS, then you should create one autoscaling group for each AZ. If you use managed nodegroups, then you should create nodegroup per AZ. In addition, you should enable the `—balance-similar-node-groups feature` in Cluster Autoscaler.

So you will need multiple autoscaling groups if you are:

1. running worker nodes using a mix of EC2 instance families or purchasing options (on demand or spot)
2. using EBS volumes.

If you are running an application that uses EBS volume but has no requirements to be highly available then you may also choose to restrict your deployment of the application to a single AZ. To do this you will need to have an autoscaling group that only includes subnet(s) in a single AZ. Then you can constraint the application’s pods to run on nodes with particular labels. In EKS worker nodes are automatically added `failure-domain.beta.kubernetes.io/zone` label which contains the name of the AZ. You can see all the labels attached to your nodes by running `kubectl describe nodes {name-of-the-node}`. More information about built-in node labels is available [here](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#built-in-node-labels). Similarly persistent volumes (backed by EBS) are also automatically labeled with AZ name, you can see which AZ your persistent volume belongs to by running `kubectl get pv -L topology.ebs.csi.aws.com/zone`. When a pod is created and it claims a volume, Kubernetes will schedule the pod on a node in the same AZ as the volume. 

Consider this scenario, you have an EKS cluster with one node group (or one autoscaling group), this node group has three worker nodes spread across three AZs. You have an application that needs to persist its data using an EBS volume. When you create this application and the corresponding volume, it gets created in the first of the three AZs. Your application running inside a Kubernetes pod is successfully able to store data on the persistent volume. Then, the worker node that runs this aforementioned pod becomes unhealthy and subsequently unavailable for use. Cluster Autoscaler will replace the unhealthy node with a new worker node, however because the autoscaling group spans across three AZs, the new worker node may get launched in the second or the third AZ, but not in the first AZ as our situation demands. Now we have a problem, the AZ-constrained volume only exists in the first AZ, but there are no worker nodes available in that AZ and hence, the pod cannot be scheduled. And due to this, you will have to create one node group in each AZ so there is always enough capacity available to run pods that cannot function in other AZs. 

### Recommendations
Running worker nodes in multiple Availability Zones protects your workloads from failures in an individual Availability Zone. Due to the challenges presented in above mentioned scenarios, you may need multiple node-groups. 
* For stateless workloads, you can create one node group that spans across multiple Availability Zones. 
* If your cluster uses different types of EC2 instances then you should create multiple node groups, one for each instance type. 
* If your application that runs replicas in multiple Availability Zondes needs EBS volumes, then you should create a node group per Availability Zone. 

*****

Here is a helpful flowchart to determine when to create node groups:


![auto-scaling group-flowchart](images/reliability-ca-asg.jpg)


*****

Note:
When autosclaing, always know the EC2 limits in your account and if the limits need to be increased request a [limit increase](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-resource-limits.html)

### Running highly-available applications 
Highly available systems are designed to mitigate any harmful impact in the environment. Most modern applications depend on a network of resources that must all work together. Highly available applications are designed so a user never experiences a failure due to a malfunctioning component in the system. In order to make a service or application highly available, we need to eliminate any single points of failure and heal components as they get unhealthy. 

Kubernetes provides us tools to easily run highly available applications and services. You can eliminate single points of failure in your applications by running multiple replicas. In Kubernetes pods are the smallest deployable units and while Kubernetes allows you to create individual pods, creating individual pods outside of testing and troubleshooting scenarios is not recommended. [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) provides abstraction layer for pods, you describe a desired state in a [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#creating-a-deployment) and the Deployment controller changes the actual state to match the desired state. You can define the number of `replicas` with the deployment.

You can scale-out your application by adjusting the number of replicas. We will take a deeper look at scaling applications in the following sections. Kubernetes can also automatically heal applications, it can check application’s health and can recreate it if application’s health check fails. 


### Scaling Kubernetes pods
Kubernetes provides two ways of scaling your applications running inside pods. First is the way of [Horizontal Pod Autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) (HPA), which would automatically create or delete pods (replicas) in a Deployment based on a scaling metric. Another way Kubernetes can scale your application is using Vertical Pod Autoscaler.

### Kubernetes Metrics Server
Before you can use the HPA to autoscale your applications, you will need [Kubernetes Metrics Server](https://github.com/kubernetes-sigs/metrics-server). Metrics Server defines itself as a *cluster-wide aggregator resource usage data* and it has been inspired by [Heapster](https://github.com/kubernetes-retired/heapster).The metrics-server is responsible for collecting resource metrics from kubelets and serving them in [Metrics API format](https://github.com/kubernetes/metrics). These metrics are consumed by monitoring systems like Prometheus and by itself the metrics server only stores metrics in memory. 

You can find the instructions to install Kubernetes Metrics Server [here](https://docs.aws.amazon.com/eks/latest/userguide/metrics-server.html).

You can see data provided by the Metrics-Server api directly using curl like this 

```
$ kubectl get —raw /apis/metrics.k8s.io/v1beta1/nodes     
{“kind”:”NodeMetricsList”,”apiVersion”:”metrics.k8s.io/v1beta1”,”metadata”:{“selfLink”:”/apis/metrics.k8s.io/v1beta1/nodes”},”items”
:[{“metadata”:{“name”:”ip-192-168-76-71.us-west-2.compute.internal”,”selfLink”:”/apis/metrics.k8s.io/v1beta1/nodes/ip-192-168-76-71.
us-west-2.compute.internal”,”creationTimestamp”:”2020-03-04T16:29:47Z”},”timestamp”:”2020-03-04T16:29:35Z”,”window”:”30s”,”usage”:{“
cpu”:”25468986n”,”memory”:”481412Ki”}},{“metadata”:{“name”:”ip-192-168-50-160.us-west-2.compute.internal”,”selfLink”:”/apis/metrics.
k8s.io/v1beta1/nodes/ip-192-168-50-160.us-west-2.compute.internal”,”creationTimestamp”:”2020-03-04T16:29:47Z”},”timestamp”:”2020-03-
04T16:29:29Z”,”window”:”30s”,”usage”:{“cpu”:”27248899n”,”memory”:”467580Ki”}}]}”
“}}]}
```

Once the metrics-server has been installed, it will start collecting metrics and provide the aggregated metrics for consumption. One of the consumers of data provided by metrics API is kubectl, you can get the same information you retrieved using curl example above using kubectl.

```
$ kubectl top nodes
NAME                                           CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%   
ip-192-168-50-160.us-west-2.compute.internal   30m          1%     456Mi           6%        
ip-192-168-76-71.us-west-2.compute.internal    25m          1%     470Mi           6%  
```
The output is has a more human friendly format. 

### Autoscaling deployments using the Horizontal Pod Autoscaler (HPA)

Now that resource metrics are available, you can configure your deployment to autoscale based on CPU utilization. The Horizontal Pod Autoscaler is implemented as a control loop in Kubernetes, it periodically queries metrics from APIs that provide resource metrics.

Including the metrics-server, the Horizontal Pod Autoscaler can retrieve metrics from the following APIs:
1. `metrics.k8s.io` also known as Resource Metrics API — Provides CPU and memory usage for pods
2. `custom.metrics.k8s.io` — Provides metrics from other metric collectors like Prometheus, these metrics are __internal__ to your Kubernetes cluster. 
3. `external.metrics.k8s.io` — Provides metrics that are __external__ to your Kubernetes cluster (E.g., SQS Queue Depth, ELB latency).

Any metric that you want to use to scale should be provided by one of these three APIs. Using the `metrics.k8s.io`, you can autoscale an application based on its CPU usage using kubectl in the following way:

```
kubectl autoscale deployment php-apache —cpu-percent=80 —min=1 —max=10
```

This will create autoscale an existing deployment (nginx in this case). You can also run `kubectl get hpa` to get more information. If you generate enough load on the *php-apache* deployment and the aggregate CPU load exceeds 80%, the HPA will create more pods until the maximum limit is reached. If load subsides, the HPA will terminate pods until there is at least one pod running. 

### Custom and external metrics for autoscaling deployments

In pod autoscaling context, custom metrics are metrics other than CPU and memory usage (these are already provided by the metrics-server) that you can use to scale your deployments. [Custom Metrics](https://github.com/kubernetes/community/blob/master/contributors/design-proposals/instrumentation/custom-metrics-api.md) API servers provide the `custom-metrics.k8s.io` API which is queried by the Horizontal Pod Autoscaler. You can use the [Prometheus Adapter for Kubernetes Metrics APIs](https://github.com/directxman12/k8s-prometheus-adapter) to collect metrics from Prometheus and use with the Horizontal Pod Autoscaler to autoscale your deployments. In this case Prometheus adapter will expose Prometheus metrics in [Metrics API format](https://github.com/kubernetes/metrics/blob/master/pkg/apis/metrics/v1alpha1/types.go). A list of all custom metrics implementation can be found in [Kubernetes Documentation](https://github.com/kubernetes/metrics/blob/master/IMPLEMENTATIONS.md#custom-metrics-api). 

Once you deploy the Prometheus Adapter, you can query custom metrics using kubectl.
`kubectl get —raw /apis/custom.metrics.k8s.io/v1beta1/`

You will need to start producing custom metrics before you start consuming them for autoscaling. 

[Kube-state-metrics](https://github.com/kubernetes/kube-state-metrics) can be used to generate metrics derived from the state of Kubernetes objects. It is not focused on the health of the individual Kubernetes components, but rather on the health of the various objects inside, such as deployments, nodes and pods. 

[External metrics](https://github.com/kubernetes/community/blob/master/contributors/design-proposals/instrumentation/external-metrics-api.md), as the name suggests provide the Horizontal Pod Autoscaler the ability to scale deployments using metrics that are external to Kubernetes cluster. For example, in batch processing workloads, it is common to scale the number of replicas based on the number of jobs in flight in an SQS queue.

—TODO—
https://github.com/zalando-incubator/kube-metrics-adapter
—TODO—

You can also scale deployments using Amazon CloudWatch, at the time of writing, to do this you have to use `k8s-cloudwatch-adapter`. There is also a feature request to [enable HPA with CloudWatch
metrics and alarms](https://github.com/aws/containers-roadmap/issues/120). 

### Vertical Pod Autoscaler (VPA)

You might have wondered why the Horizontal Pod Autoscaler is not simply called “the Autoscaler”, this is because Kubernetes can scale your applications (running in pods) in two ways. First is the way of HPA, which would automatically scale replicas in a Deployment based on scaling metric. The [Vertical Pod Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler) automatically adjusts the CPU and memory reservations for your pods to help you “right-size” your applications. Vertical Pod Autoscaler’s current implementation does not perform in-place adjustments to pods, instead it will restart the pod that needs to be scaled with increased. 

[EKS Documentation](https://docs.aws.amazon.com/eks/latest/userguide/vertical-pod-autoscaler.html) includes a walkthrough for setting up VPA. 

[Fairwinds Goldilocks](https://github.com/FairwindsOps/goldilocks/) project simplifies implementation of VPA. Goldilocks can provide VPA recommendations and it can optionally auto-scale the Pods. 

### Health checks and self-healing
It’s a truism that no software is bug-free. Kubernetes gives you the ability to minimize impact of software failures. In the past, if an application crashed, someone had to manually remediate the situation by restarting the application. Kubernetes gives you the ability to detect software failures in your application and automatically heal them. Kubernetes can monitor the health of your application and stop sending requests to the Pod if it fails health-checks.  

Kubernetes supports three types of (health-checks)[https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/]:

1. Liveness probe
2. Readiness probe
3. Startup probe (requires Kubernetes 1.16+)

[Kubelet](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/) is responsible for running all the above-mentioned checks. Kubelet can check the health of your applications in three ways, it can either run a shell command inside the container, send a HTTP GET request to the container or open a TCP socket on a specified port. 


#### Liveness Probe
You can use the Liveness probe to detect failure in a running application. For example, if you are running a web application that listens on port 80, you can configure a Liveness probe to send a HTTP GET request on Pod’s port 80. Kubelet will periodically send a GET request to the Pod and expect a response, if the Pod responds between 200-399 then Kubelet considers that Pod as healthy, otherwise the Pod will be considered unhealthy. If a running pod fails health-checks, Kubernetes will restart the pod. 

#### Readiness Probe
While Liveness probe is used to detect failure in an application that can only be remediated by restarting the Pod, Readiness Probe can be used to detect situations where the application may be _temporarily_ unavailable. Some applications have external dependencies or need to perform actions such as opening a database connection, loading a large file, etc. And, they may need to do this not just during startup. In these situations the application may become temporarily unresponsive however once this operation completes, it is expected to be healthy again. You can use the Readiness Probe to detect this behavior and stop sending requests to applications’ Pod until it becomes healthy again. Unlike Liveness Probe, where a failure would result in a recreation of Pod, a failed Readiness Probe would mean that Pod will not receive any traffic through Kubernetes Services. When the Liveness Probe succeeds, Pod will resume receiving traffic from Services.
 

#### Startup Probe
When your application needs additional time to startup, you can use the Startup Probe to delay the Liveness Probe. Once the Startup Probe succeeds, the Liveness Probe takes over. You can define maximum time Kubernetes should wait for application startup. If after the maximum configured time, the Pod still fails Startup Probes, it will be restarted. 

### Recommendations
Configure both Readiness and Liveness probe in your Pods. Use `initialDelaySeconds` to delay the first probe. For example, if in your tests, you’ve identified that your application takes on an average 60 seconds to load libraries, open database connections, etc, then configure `initialDelaySeconds` to 60 seconds + plus ~10 seconds for grace period. 


### Disruptions

A Pod will run indefinitely unless a user stops or the worker node it runs on fails. Outside of failed health-checks and autoscaling there aren’t many situations where Pods need to be restarted. Performing Kubernetes cluster upgrades is one such event. When you need to upgrade your Kubernetes cluster, after performing control plane upgrade, you will need to upgrade your worker nodes. If you are not using [EKS managed node group](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html), we recommend you create new worker nodes with updated Kubernetes components rather than performing an in-place upgrade of your worker nodes. 

Worker node upgrades are generally done by terminating old worker nodes and creating new worker nodes. Before terminating a worker nodes, you should `drain` it. When a worker node is drained, all its pods are safely evicted. Safely is a key word here, when Pods on a worker are evicted, they are not sent a KILL signal. Instead a TERM signal is sent to the main process of each container in the Pods being evicted. After the TERM signal is sent, Kubernetes will give the process some time (grace period) before a KILL signal is sent. This grace period is 30 seconds by default, you can override the default by using `grace-period` flag in kubectl. 

`kubectl delete pod <pod name> —grace-period=<seconds>`

Draining also respects `PodDisruptionBudgets`

### Pod Disruption Budget

Pod Disruption Budget (or PDB) can temporarily halt the eviction process if the number of replicas of an application fall below the declared threshold. The eviction process will continue once the number of available replicas is more than the threshold. You can use PDB to declare the `minAvailable` and `maxUnavailable` number of replicas. For example, if you want to ensure that at least three copies of your application are available, you can create a PDB for your application. 

```
apiVersion: policy/v1beta1
kind: PodDisruptionBudget
metadata:
  name: my-app-pdb
spec:
  minAvailable: 3
  selector:
    matchLabels:
      app: my-app
```

This tells Kubernetes to halt the eviction process until three or more replicas are available. 

https://kubernetes.io/docs/concepts/configuration/pod-priority-preemption/#priorityclass

### Observability 

Observability, in this context, is an umbrella term that includes monitoring, logging and tracing. Microservices based applications are distributed by nature. Unlike monolithic applications where monitoring a single system is sufficient, in microservices architecture each component needs to be monitored individually as well as cohesively, as one application. Cluster-level monitoring, logging 

Kubernetes tools for troubleshooting and monitoring are very limited. The metrics-server collects resource metrics and stores them in memory but doesn’t persist them. You can view the logs of a Pod using kubectl but these logs are not retained. And implementation of distributed tracing is done either at application code level or using services meshes. 

This is where Kubernetes extensibility shines, you can bring your own preferred centralized monitoring and logging and tracing solution and use Kubernetes to manage and run it. 

### Monitoring 

Consider using a tool like [Prometheus](https://prometheus.io) or [CloudWatch Container Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights.html) for centralized monitoring Kubernetes infrastructure and applications. 

### Logging

For centralized logging, you can use tools like [FluentD](https://www.fluentd.org) or CloudWatch Container Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights.html) 

### Tracing

Tracing can help you identify problems in your microservices. While logging can be used to troubleshoot problems, logs are often scattered and may not be implemented consistently across services. Distributed tracing can show you how requests are being handled by the microservices in your application and help you identify malfunctioning components. It can provide you insights into your application’s performance and identify sources of errors and latency.

You can enable tracing in your applications running in Kubernetes in two ways. You can either implement distributed tracing at the code level by using shared libraries or you can use a service mesh. 

Implementing tracing at the code level can be disadvantageous. In this method, you have to make changes to your code. This is further complicated if you have polyglot applications. You’re also responsible to upgrading yet another library, across your application. 

Service Meshes like [LinkerD](http://linkerd.io), [Istio](http://istio.io) , and [AWS App Mesh](https://aws.amazon.com/app-mesh/) can be used to implement distributed tracing in your application without changing a single line of code. 

Tracing tools like [AWS X-Ray](https://aws.amazon.com/xray/), [Jaeger](https://www.jaegertracing.io) support both shared library and service mesh implementations. Consider using a tracing tool that supports both implementations so you will not have to switch tools if you adopt service mesh. 

### Monitoring CoreDNS

CoreDNS fulfills name resolution and service discovery functions in Kubernetes and it is installed by default on EKS clusters. For interoperability, the Kubernetes service for CoreDNS is still named [kube-dns](https://kubernetes.io/docs/tasks/administer-cluster/dns-custom-nameservers/). CoreDNS runs as a deployment in kube-system namespaces, and by default it runs two replicas with declared requests and limits. 

CoreDNS has built in support for [Prometheus](https://github.com/coredns/coredns/tree/master/plugin/metrics). You should especially consider monitoring CoreDNS latency (`coredns_dns_request_duration_seconds_sum`), errors (`coredns_dns_response_rcode_count_total`, NXDOMAIN, SERVFAIL, FormErr) and CoreDNS Pod’s memory consumption. 

For troubleshooting purposes, you can use kubectl to view CoreDNS logs:
`for p in $(kubectl get pods —namespace=kube-system -l k8s-app=kube-dns -o name); do kubectl logs —namespace=kube-system $p; done`


### Service Meshes

Service meshes enable service-to-service communication in a secure, reliable, and greatly increase observability of your microservices network. Most service mesh products works by having a small network proxy sit alongside each microservice. This so-called “sidecar” intercepts all of the service’s traffic, and handles it more intelligently than a simple layer 3 network can. The sidecar proxy is able to intercept, inspect, and manipulate all network traffic heading through the Pod, while primary container needs no alteration or even knowledge that this is happening.

Service mesh can help you implement observability in your application with minimal code change. Proxies like [Envoy](https://www.envoyproxy.io) provide in-built support for monitoring, logging and tracing and support.

You can also use service mesh features like automatic retries and rate limiting to make your microservices more resilient.

### Pod resource management

### Chaos Engineering Practice 


