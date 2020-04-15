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
Before you can use the HPA to autoscale your applications, you will need [Kubernetes Metrics Server](https://github.com/kubernetes-sigs/metrics-server). Metrics Server defines itself as a *cluster-wide aggregator resource usage data* and it has been inspired by [Heapster](https://github.com/kubernetes-retired/heapster).The metrics-server is responsible for collecting resource metrics from kubelets and serving them in [Metrics API format](https://github.com/kubernetes/metrics). These metrics are consumed by monitoring systems like Prometheus and by itself the metrics-server only stores metrics in memory. 

You can find the instructions to install Kubernetes Metrics Server [here](https://docs.aws.amazon.com/eks/latest/userguide/metrics-server.html).

You can see data provided by the Metrics-Server api directly using curl like this 

```
$ kubectl get —raw “/apis/metrics.k8s.io/v1beta1/nodes”       
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

### Health checks
It’s a truism that no software is bug-free. Kubernetes gives you the ability to minimize impact of software crashes. In the past, if an application crashed, someone had to manually remediate the situation by restarting the application. Kubernetes gives you the ability to detect software failures in your application and restart it. Kubernetes can monitor the health of your application and restart it’s Pod in case of health-check failure.  

Kubernetes supports three types of (health-checks)[https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/]:
1. Readiness probe
2. Liveness probe
3. Startup probe (requires Kubernetes 1.16+)

[Kubelet](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/) is responsible for running all the above-mentioned checks. Kubelet can check the health of your applications in three ways, it can either run a shell command inside the container, send a HTTP GET request to the container or try connecting to open a TCP socket on a specified port. 


#### Readiness Probe
When you deploy a pod, your application may take some time before it is ready to accept requests. Readiness probes should be used to determine when a Pod is ready to its work. If your application depends on external services, for example a database, you can run a shell script to verify that your database connection is successful before accepting traffic. 
 
#### Liveness Probe
You can use the Liveness probe to detect failure in a running application. For example, if you are running a web application that listens on port 80, you can configure a Liveness probe to send a HTTP GET request on Pod’s port 80. Kubelet will periodically send a GET request to the Pod and expect a response, if the Pod responds between 200-399 then Kubelet considers that Pod as healthy, otherwise the Pod will be considered unhealthy. 

#### Startup Probe

—-TODO—-
How is this different from readiness probe. 
—-TODO—- 

### Recommendations
At minimum, configure Readiness and Liveness probe in your Pod spec. Use `initialDelaySeconds` to delay the first probe. For example, if in your tests, you’ve identified that your application takes on an average 60 seconds to load libraries, open database connections, etc, then configure `initialDelaySeconds` to 60 seconds. 


### Disruptions

Kubernetes makes it easy to run highly-available applications by providing the ability to run multiple replicas. Running multiple replicas and using Kubernetes health checks you can mitigate disruptions. If aggregate load in a Deployment exceeds the threshold, HPA can add replicas. If a Pod fails health checks 



A Pod in a cluster will run indefinitely unless a user (human or system) terminates it or the host running the pod malfunctions, e.g., a kernel panic on the worker node running the pod. 



—-PDB here—

https://kubernetes.io/docs/concepts/configuration/pod-priority-preemption/#priorityclass

### Observability 

### Monitoring CoreDNS

### Service Meshes

### CI/CD

### Simulating failure
