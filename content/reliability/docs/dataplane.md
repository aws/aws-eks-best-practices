# EKS Data Plane

To operate high-available and resilient applications, you need a highly-available and resilient data plane. An elastic data plane ensures that Kubernetes can scale and heal your applications automatically. A resilient data plane consists of two or more worker nodes, can grow and shrink with the workload, and automatically recover from failures.

You have two choices for worker nodes with EKS: [EC2 instances](https://docs.aws.amazon.com/eks/latest/userguide/worker.html) and [Fargate](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html). If you choose EC2 instances, you can manage the worker nodes yourself or use [EKS managed node groups](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html). You can have a cluster with a mix of managed, self-managed worker nodes, and Fargate. 

EKS on Fargate offers the easiest path to a resilient data plane. Fargate runs each Pod in an isolated compute environment. Each Pod running on Fargate gets its own worker node. Fargate automatically scales the data plane as Kubernetes scales pods. You can scale both the data plane and your workload by using the [horizontal pod autoscaler](https://docs.aws.amazon.com/eks/latest/userguide/horizontal-pod-autoscaler.html).

The preferred way to scale EC2 worker nodes is by using [Kubernetes Cluster Autoscaler](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md), [EC2 Auto Scaling groups](https://docs.aws.amazon.com/autoscaling/ec2/userguide/AutoScalingGroup.html) or community projects like [Atlassian’s Esclator](https://github.com/atlassian/escalator).

## Recommendations 

### Use EC2 Auto Scaling Groups to create worker nodes

It is a best practice to create worker nodes using EC2 Auto Scaling groups instead of creating individual EC2 instances and joining them to the cluster. Auto Scaling Groups will automatically replace any terminated or failed nodes ensuring that the cluster always has the capacity to run your workload. 

### Use Kubernetes Cluster Autoscaler to scale nodes

Cluster Autoscaler adjusts the size of the data plane when there are pods that cannot be run because the cluster has insufficient resources, and adding another worker node would help. Although Cluster Autoscaler is a reactive process, it waits until pods are in *Pending* state due to insufficient capacity in the cluster. When such an event occurs, it adds EC2 instances to the cluster. Whenever the cluster runs out of capacity, new replicas - or new pods - will be unavailable (*in Pending state*) until worker nodes are added. This delay may impact your applications' reliability if the data plane cannot scale fast enough to meet the demands of the workload. If a worker node is consistently underutilized and all of its pods can be scheduled on other worker nodes, Cluster Autoscaler terminates it.

### Configure over-provisioning with Cluster Autoscaler

Cluster Autoscaler triggers a scale-up of the data-plane when Pods in the cluster are already *Pending*. Hence, there may be a delay between the time your application needs more replicas, and when it, in fact, gets more replicas. An option to account for this possible delay is through adding more than required replicas, inflating the number of replicas for the application. 

Another pattern that Cluster Autoscaler recommends uses [*pause* Pods and the Priority Preemption feature](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md#how-can-i-configure-overprovisioning-with-cluster-autoscaler). The *pause Pod* runs a [pause container](https://github.com/kubernetes/kubernetes/tree/master/build/pause), which as the name suggests, does nothing but acts as a placeholder for compute capacity that can be used by other Pods in your cluster. Because it runs with a *very low assigned priority*, the pause Pod gets evicted from the node when another Pod needs to be created, and the cluster doesn’t have available capacity. The Kubernetes Scheduler notices the eviction of the pause Pod and tries to reschedule it. But since the cluster is running at capacity, the pause Pod remains *Pending*, to which the Cluster Autoscaler reacts by adding nodes. 

A Helm chart is available to install [cluster overprovisioner](https://github.com/helm/charts/tree/master/stable/cluster-overprovisioner).

### Using Cluster Autoscaler with multiple Auto Scaling Groups

Run the Cluster Autoscaler with the `--node-group-auto-discovery` flag enabled. Doing so will allow the Cluster Autoscaler to find all autoscaling groups that include a particular defined tag and prevents the need to define and maintain each autoscaling group in the manifest.

### Using Cluster Autoscaler with local storage

By default, the Cluster Autoscaler does not scale-down nodes that have pods deployed with local storage attached. Set the `--skip-nodes-with-local-storage` flag to false to allow Cluster Autoscaler to scale-down these nodes.

### Spread worker nodes and workload across multiple AZs

You can protect your workloads from failures in an individual AZ by running worker nodes and pods in multiple AZs. You can control the AZ the worker nodes are created in using the subnets you create the nodes in.

You can set pod anti-affinity rules to schedule pods across multiple AZs. The manifest below informs Kubernetes scheduler to *prefer* scheduling pods in distinct AZs. 

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-server
  labels:
    app: web-server
spec:
  replicas: 4
  selector:
    matchLabels:
      app: web-server
  template:
    metadata:
      labels:
        app: web-server
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - web-server
              topologyKey: failure-domain.beta.kubernetes.io/zone
            weight: 100
      containers:
      - name: web-app
        image: nginx
```


!!! warning Do not require that pods be scheduled across distinct AZs otherwise, the number of pods in a deployment will never exceed the number of AZs. 


With Kubernetes 1.18+, you can use [Spread Constraints for Pods](https://kubernetes.io/docs/concepts/workloads/pods/pod-topology-spread-constraints/#spread-constraints-for-pods) to schedule pods across multiple AZs.

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-server
  labels:
    app: web-server
spec:
  replicas: 3
  template:
    metadata:
      labels:
        app: web-server
    spec:
      topologySpreadConstraints:
        - maxSkew: 1
          whenUnsatisfiable: DoNotSchedule
          topologyKey: failure-domain.beta.kubernetes.io/zone
          labelSelector:
            matchLabels:
              app: web-server
      containers:
      - name: web-app
        image: nginx
```

### Ensure capacity in each AZ when using EBS volumes

If you use [Amazon EBS to provide Persistent Volumes](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html), then you need to ensure that the pods and associated EBS volume are located in the same AZ. At the time of writing, EBS volumes are only available within a single AZ. A Pod cannot access EBS-backed persistent volumes located in a different AZ. Kubernetes [scheduler knows which AZ a worker node](https://kubernetes.io/docs/reference/kubernetes-api/labels-annotations-taints/#topologykubernetesiozone) is located in. Kubernetes will always schedule a Pod that requires an EBS volume in the same AZ as the volume. However, if there are no worker nodes available in the AZ where the volume is located, then the Pod cannot be scheduled. 

Create Auto Scaling Group for each AZ with enough capacity to ensure that the cluster always has capacity to schedule pods in the same AZ as the EBS volumes they need. In addition, you should enable the `--balance-similar-node-groups` feature in Cluster Autoscaler.

If you are running an application that uses EBS volume but has no requirements to be highly available, then you can restrict the deployment of the application to a single AZ. In EKS, worker nodes are automatically added `failure-domain.beta.kubernetes.io/zone` label, which contains the name of the AZ. You can see the labels attached to your nodes by running `kubectl get nodes --show-labels`. More information about built-in node labels is available [here](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#built-in-node-labels). You can use node selectors to schedule a pod in a particular AZ. 

In the example below, the pod will only be scheduled in `us-west-2c` AZ:

```
apiVersion: v1
kind: Pod
metadata:
  name: single-az-pod
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: failure-domain.beta.kubernetes.io/zone
            operator: In
            values:
            - us-west-2c
  containers:
  - name: single-az-container
    image: kubernetes/pause
```

Persistent volumes (backed by EBS) are also automatically labeled with the name of AZ; you can see which AZ your persistent volume belongs to by running `kubectl get pv -L topology.ebs.csi.aws.com/zone`. When a pod is created and claims a volume, Kubernetes will schedule the Pod on a node in the same AZ as the volume. 

Consider this scenario; you have an EKS cluster with one node group. This node group has three worker nodes spread across three AZs. You have an application that uses an EBS-backed Persistent Volume. When you create this application and the corresponding volume, its Pod gets created in the first of the three AZs. Then, the worker node that runs this Pod becomes unhealthy and subsequently unavailable for use. Cluster Autoscaler will replace the unhealthy node with a new worker node; however, because the autoscaling group spans across three AZs, the new worker node may get launched in the second or the third AZ, but not in the first AZ as the situation demands. As the AZ-constrained EBS volume only exists in the first AZ, but there are no worker nodes available in that AZ, the Pod cannot be scheduled. Therefore, you should create one node group in each AZ, so there is always enough capacity available to run pods that cannot be scheduled in other AZs. 


Alternatively, you can use [EFS](https://github.com/kubernetes-sigs/aws-efs-csi-driver) can simplify cluster autoscaling when running applications that need persistent storage. Clients can access EFS file systems concurrently from all the AZs in the region. Even if a Pod using EFS-backed Persistent Volume gets terminated and gets scheduled in different AZ, it will be able to mount the volume.

### Run node-problem-detector

Failures in worker nodes can impact the availability of your applications. [node-problem-detector](https://github.com/kubernetes/node-problem-detector) is a Kubernetes add-on that you can install in your cluster to detect worker node issues. You can use a [npd’s remedy system](https://github.com/kubernetes/node-problem-detector#remedy-systems) to drain and terminate the node automatically.

### Reserving resources for system and Kubernetes daemons

You can improve worker nodes' stability by [reserving compute capacity for the operating system and Kubernetes daemons](https://kubernetes.io/docs/tasks/administer-cluster/reserve-compute-resources/). Pods  - especially ones without `limits` declared - can saturate system resources putting nodes in a situation where operating system processes and Kubernetes daemons (`kubelet`, container runtime, etc.) compete with pods for system resources. You can use `kubelet` flags `--system-reserved` and `--kube-reserved` to reserve resources for system process (`udev`, `sshd`, etc.) and Kubernetes daemons respectively. 

If you use the [EKS-optimized Linux AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html), the CPU, memory, and storage are reserved for the system and Kubernetes daemons by default. When worker nodes based on this AMI launch, EC2 user-data is configured to trigger the [`bootstrap.sh` script](https://github.com/awslabs/amazon-eks-ami/blob/master/files/bootstrap.sh). This script calculates CPU and memory reservations based on the number of CPU cores and total memory available on the EC2 instance. The calculated values are written to the `KubeletConfiguration` file located at `/etc/kubernetes/kubelet/kubelet-config.json`. 

You may need to increase the system resource reservation if you run custom daemons on the node and the amount of CPU and memory reserved by default is insufficient. 

`eksctl` offers the easiest way to customize [resource reservation for system and Kubernetes daemons](https://eksctl.io/usage/customizing-the-kubelet/). 

## Implement QoS

For critical applications, consider defining `requests`=`limits` for the container in the Pod. This will ensure that the container will not be killed if another Pod requests resources.

It is a best practice to implement CPU and memory limits for all containers as it prevents a container inadvertently consuming system resources impacting the availability of other co-located processes.

### Configure resource quotas for namespaces

Namespaces are intended for use in environments with many users spread across multiple teams, or projects. They provide a scope for names and are a way to divide cluster resources between multiple teams, projects, workloads. You can limit the aggregate resource consumption in a namespace. The [`ResourceQuota`](https://kubernetes.io/docs/concepts/policy/resource-quotas/) object can limit the quantity of objects that can be created in a namespace by type, as well as the total amount of compute resources that may be consumed by resources in that project. You can limit the total sum of storage and/or compute (CPU and memory) resources that can be requested in a given namespace.

> If resource quota is enabled for a namespace for compute resources like CPU and memory, users must specify requests or limits for each container in that namespace.

Consider configuring quotas for each namespace. Consider using `LimitRanges` to automatically apply preconfigured limits to containers within a namespaces. 

### Limit container resource usage within a namespace

Resource Quotas help limit the amount of resources a namespace can use. The [`LimitRange` object](https://kubernetes.io/docs/concepts/policy/limit-range/) can help you implement minimum and maximum resources a container can request. Using `LimitRange` you can set a default request and limits for containers, which is helpful if setting compute resource limits is not a standard practice in your organization. As the name suggests, `LimitRange` can enforce minimum and maximum compute resources usage per Pod or Container in a namespace. As well as, enforce minimum and maximum storage request per PersistentVolumeClaim in a namespace.

Consider using `LimitRange` in conjunction with `ResourceQuota` to enforce limits at a container as well as namespace level. Setting these limits will ensure that a container or a namespace does not impinge on resources used by other tenants in the cluster. 
