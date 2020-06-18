# EKS Data Plane

To operate high-available and resilient applications, you need a highly-available and resilient data plane. An elastic data plane ensures that Kubernetes can scale and heal your applications automatically. A resilient data plane consists of two or more worker nodes, can grow and shrink with workload, and automatically recover from failures.

You have two choices for worker nodes with EKS: [EC2 instances](https://docs.aws.amazon.com/eks/latest/userguide/worker.html) and [Fargate](https://docs.aws.amazon.com/eks/latest/userguide/fargate.html). If you choose EC2 instances, then you can either manage the worker nodes yourself or use [EKS managed node groups](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html). You can have a cluster with a mix of managed, self-managed worker nodes, and Fargate. 

EKS on Fargate offers the easiest path to a resilient data plane. Fargate runs each Pod in an isolated compute environment. Each Pod running on Fargate gets its own worker node. Fargate automatically scales the data plane as Kubernetes scales pods. You can scale both the data plane and your workload by using the [horizontal pod autoscaler](https://docs.aws.amazon.com/eks/latest/userguide/horizontal-pod-autoscaler.html).

The preferred way to scale EC2 worker nodes is by using [Kubernetes Cluster Autoscaler](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md), [EC2 auto scaling groups](https://docs.aws.amazon.com/autoscaling/ec2/userguide/AutoScalingGroup.html) or community projects like [Atlassian’s Esclator](https://github.com/atlassian/escalator).

## Recommendations 

### Use EC2 Auto Scaling Groups to create worker nodes

It is a best practice to create worker nodes using EC2 Auto Scaling groups as opposed to creating individual EC2 instances and joining them to the cluster. Auto scaling groups will automatically replace any terminated or failed nodes ensuring that the cluster always has the capacity to run your workload. 

### Use Kubernetes Cluster Autoscaler to scale nodes

Cluster Autoscaler adjusts the size of the data plane when there are pods that cannot be run because the cluster has insufficient resources and adding another worker node would help. Although, Cluster Autoscaler is a reactive process. It waits until pods are in *Pending* state due to insufficient capacity in the cluster. When such an event occurs, it adds EC2 instances to the cluster. Whenever the cluster runs out of capacity, new replicas - or new pods - will be unavailable (*in Pending state*) until worker nodes are added. This delay may impact the reliability of your applications if the data plane cannot scale fast enough to meet the demands of the workload. If a worker node is consistently underutilized and all of its pods can be scheduled on other worker nodes, Cluster Autoscaler terminates it.

Consider inflating the `replica` count to account for delay in data plane scaling, especially when using smaller EC2 instances that take longer to join the cluster.

### Using Cluster Autoscaler with multiple Auto Scaling Groups

Run the Cluster Autoscaler with the `--node-group-auto-discovery` flag enabled. This will enable the Cluster Autoscaler to find all autoscaling groups that include a particular defined tag and prevents the need to define and maintain each and every autoscaling group in the manifest.

### Using Cluster Autoscaler with local storage

By default the Cluster Autoscaler does not scale-down nodes that have pods deployed with local storage attached. Set the `--skip-nodes-with-local-storage` flag to false to allow Cluster Autoscaler to scale-down these nodes.

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


!!! warning Do not require that pods be scheduled across distinct AZs otherwise the number of pods in a deployment will never exceed the number of AZs. 


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

If you use [Amazon EBS to provide Persistent Volumes](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html) then you need to ensure that the pods and associated EBS volume are located in the same AZ. At the time of writing, EBS volumes are only available within a single AZ. A Pod cannot access EBS-backed persistent volumes located in a different AZ. Kubernetes [scheduler knows which AZ a worker node](https://kubernetes.io/docs/reference/kubernetes-api/labels-annotations-taints/#topologykubernetesiozone) is located in. Kubernetes will always schedule a Pod that requires an EBS volume in the same AZ as the volume. However, if there are no worker nodes available in the AZ where the volume is located, then the Pod cannot be scheduled. 

Create Auto Scaling Group for each AZ with enough capacity to ensure that the cluster always has capacity to schedule pods in the same AZ as the EBS volumes they need. In addition, you should enable the `--balance-similar-node-groups` feature in Cluster Autoscaler.

If you are running an application that uses EBS volume but has no requirements to be highly available then you can restrict the deployment of the application to a single AZ. In EKS worker nodes are automatically added `failure-domain.beta.kubernetes.io/zone` label which contains the name of the AZ. You can see the labels attached to your nodes by running `kubectl get nodes --show-labels`. More information about built-in node labels is available [here](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#built-in-node-labels). You can use node selectors to schedule a pod in a particular AZ. 

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

Persistent volumes (backed by EBS) are also automatically labeled with the name of AZ, you can see which AZ your persistent volume belongs to by running `kubectl get pv -L topology.ebs.csi.aws.com/zone`. When a pod is created and it claims a volume, Kubernetes will schedule the pod on a node in the same AZ as the volume. 

Consider this scenario, you have an EKS cluster with one node group, this node group has three worker nodes spread across three AZs. You have an application that uses EBS-backed Persistent Volume. When you create this application and the corresponding volume, its Pod gets created in the first of the three AZs. Then, the worker node that runs this pod becomes unhealthy and subsequently unavailable for use. Cluster Autoscaler will replace the unhealthy node with a new worker node, however because the autoscaling group spans across three AZs, the new worker node may get launched in the second or the third AZ, but not in the first AZ as the situation demands. As the AZ-constrained EBS volume only exists in the first AZ, but there are no worker nodes available in that AZ, the pod cannot be scheduled. Therefore, you should create one node group in each AZ so there is always enough capacity available to run pods that cannot be scheduled in other AZs. 


Alternatively you can use [EFS](https://github.com/kubernetes-sigs/aws-efs-csi-driver) can simplify cluster autoscaling when running applications that need persistent storage. EFS file systems can be concurrently accessed from all the AZs in the region. Even if a Pod using EFS-backed Persistent Volume gets terminated and gets scheduled in different AZ, it will be able to mount the volume.

### Run node-problem-detector

Failures in worker nodes can impact the availability of your applications. [node-problem-detector](https://github.com/kubernetes/node-problem-detector) is a Kubernetes add-on you can install in your cluster to detect worker node issues. You can use a [npd’s remedy system](https://github.com/kubernetes/node-problem-detector#remedy-systems) to automatically drain and terminate the node.



