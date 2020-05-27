### 1. Cost-effective resources 
**1.1 Auto Scaling - Ensure that the infrastructure used to deploy the containerized service matches the application profile and scaling needs.**

Amazon EKS with EC2 managed node groups automate the provisioning and lifecycle management of nodes (Amazon EC2 instances) for Amazon EKS Kubernetes clusters. All managed nodes are provisioned as part of an Amazon EC2 Auto Scaling group that is managed for you by Amazon EKS and all resources including Amazon EC2 instances and Auto Scaling groups run within your AWS account. Amazon EKS tags managed node group resources so that they are configured to use the Kubernetes Cluster Autoscaler. 

The documentation at https://docs.aws.amazon.com/eks/latest/userguide/cluster-autoscaler.html provides detailed guidance on setting up a Managed Node Group and then deploying Kubernetes Cluster Auto Scaler. 

***To create a Kubernetes cluster 1.16 with a single managed group that spans multiple Availability Zones and deploying Kubernetes Cluster AutoScaler on Amazon EKS:***

***Create a EKS cluster with one nodegroup containing 2 m5.large nodes***
```
$ eksctl version
0.19.0
$ eksctl create cluster --name my-cluster-testscaling --version 1.16 --managed --asg-access
```

***Deploy the Cluster Autoscaler for EC2 based Worker Nodes:***
```
$ kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

$ kubectl -n kube-system annotate deployment.apps/cluster-autoscaler cluster-autoscaler.kubernetes.io/safe-to-evict="false"

$ kubectl -n kube-system edit deployment.apps/cluster-autoscaler

$ kubectl -n kube-system set image deployment.apps/cluster-autoscaler cluster-autoscaler=us.gcr.io/k8s-artifacts-prod/autoscaling/cluster-autoscaler:v1.16.5

$ kubectl -n kube-system logs -f deployment.apps/cluster-autoscaler
```
Cluster Autoscaler logs -
![Kubernetes Cluster Auto Scaler logs](../images/cluster-auto-scaler.png)

***Deploy Horizontal Pod Autoscaling***

Setup Metrics server:
```

$ kubectl create namespace metrics
$ helm install metrics-server \
    stable/metrics-server \
    --version 2.9.0 \
    --namespace metrics

$ kubectl get --raw "/apis/metrics.k8s.io/v1beta1/nodes"
$ kubectl get apiservice v1beta1.metrics.k8s.io -o yaml
```
Now you can deploy apps which can leverage HPA. Follow https://eksworkshop.com/beginner/080_scaling/test_hpa/ to deploy a sample app, perform a simple load test to test the autoscaling of pods.
```
kubectl run php-apache --image=us.gcr.io/k8s-artifacts-prod/hpa-example --requests=cpu=200m --expose --port=80
```
HPA scales up when CPU exceeds 50% of the allocated container resource, with a minimum of one pod and a maximum of ten pods.
```
kubectl autoscale deployment php-apache --cpu-percent=50 --min=1 --max=10
kubectl get hpa
```
You can then load test the app, and simulate pod autoscaling. 

The combination of Cluster Auto Scaler for the Kubernetes worker nodes and Horizontal Pod Autoscaler for the pods, will ensure that the provisioned resources will be as close to the actual utilization as possible.

![Kubernetes Cluster AutoScaler and HPA](../images/ClusterAS-HPA.png)
***(Image source: https://aws.amazon.com/blogs/containers/cost-optimization-for-kubernetes-on-aws/)***

***Autoscaling of Pods on Amazon EKS with Fargate***

Autoscaling EKS on Fargate can be done using the following mechanisms:

1. Using the Kubernetes metrics server and configure auto-scaling based on CPU and/or memory usage.
2. Configure autoscaling based on custom metrics like HTTP traffic using Prometheus and Prometheus metrics adapter
3. Configure autoscaling based on App Mesh traffic

The above scenarios are explained in a hands-on blog on ["Autoscaling EKS on Fargate with custom metrics](https://aws.amazon.com/blogs/containers/autoscaling-eks-on-fargate-with-custom-metrics/)


**1.2 Down Scaling**

As part of controlling costs, apart from Auto-scaling of the Kubernetes cluster nodes and pods, Down-Scaling of resources when not in-use can also have an huge impact on the overall costs. There are tools like [kube-downscaler](https://github.com/hjacobs/kube-downscaler), which can be used to Scale down Kubernetes deployments after work hours or during set periods of time. 

Installation of kube-downscaler:
```
git clone https://github.com/hjacobs/kube-downscaler
cd kube-downscaler
kubectl apply -k deploy/
```

The example configuration uses the --dry-run as a safety flag to prevent downscaling --- remove it to enable the downscaler, e.g. by editing the deployment:
```
$ kubectl edit deploy kube-downscaler
```

Deploy an nginx pod and schedule it to be run in the time zone - Mon-Fri 09:00-17:00 Asia/Kolkata: 
```
$ kubectl run nginx1 --image=nginx
$ kubectl annotate deploy nginx1 'downscaler/uptime=Mon-Fri 09:00-17:00 Asia/Kolkata'
```
Note that the default grace period of 15 minutes applies to the new nginx deployment, i.e. if the current time is not within Mon-Fri 9-17 (Asia/Kolkata timezone), it will downscale not immediately, but after 15 minutes. 

![Kube-down-scaler for nginx](../images/kube-down-scaler.png)

More advanced downscaling deployment scenarios are available at the [kube-down-scaler github project](https://github.com/hjacobs/kube-downscaler).

**1.3 Policies using LimitRanges and Resource Quotas**

From the [Kubernetes documentation](https://kubernetes.io/docs/concepts/policy/limit-range/) - By default, containers run with unbounded compute resources on a Kubernetes cluster. With resource quotas, cluster administrators can restrict resource consumption and creation on a namespace basis. Within a namespace, a Pod or Container can consume as much CPU and memory as defined by the namespace’s resource quota. There is a concern that one Pod or Container could monopolize all available resources. 

Kubernetes controls the allocation of resources such as CPU, memory, PersistentVolumeClaims and others using Resource Quotas and Limit Ranges. ResourceQuota is at the Namespace level, while a LimitRange applies at an container level. 

***Limit Ranges***

A LimitRange is a policy to constrain resource allocations (to Pods or Containers) in a namespace. 

The following is an example of setting an default memory request and a default memory limit using Limit Range. 

``` yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: mem-limit-range
spec:
  limits:
  - default:
      memory: 512Mi
    defaultRequest:
      memory: 256Mi
    type: Container
```

More examples are available in the [Kubernetes documentation](https://kubernetes.io/docs/tasks/administer-cluster/manage-resources/memory-default-namespace/).

***Resource Quotas***

When several users or teams share a cluster with a fixed number of nodes, there is a concern that one team could use more than its fair share of resources. Resource quotas are a tool for administrators to address this concern.

The following is an example of how to set quotas for the total amount memory and CPU that can be used by all Containers running in a namespace, by specifying quotas in a ResourceQuota object. This specifies that a Container must have a memory request, memory limit, cpu request, and cpu limit, and should not exceed the threshold set in the ResourceQuota.

``` yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: mem-cpu-demo
spec:
  hard:
    requests.cpu: "1"
    requests.memory: 1Gi
    limits.cpu: "2"
    limits.memory: 2Gi
```

More examples are available in the [Kubernetes documentation](https://kubernetes.io/docs/tasks/administer-cluster/manage-resources/quota-memory-cpu-namespace/).

**1.4 Use pricing models for effective utilization.**

The pricing details for Amazon EKS are given in the [pricing page](https://aws.amazon.com/eks/pricing/). There is a common control plane cost for both Amazon EKS on Fargate and EC2. 

If you are using AWS Fargate, pricing is calculated based on the vCPU and memory resources used from the time you start to download your container image until the Amazon EKS pod terminates, rounded up to the nearest second. A minimum charge of 1 minute applies. See detailed pricing information on the [AWS Fargate pricing page](https://aws.amazon.com/fargate/pricing/).

***Amazon EKS on EC2:***

Amazon EC2 provides a wide selection of [instance types](https://aws.amazon.com/ec2/instance-types/) optimized to fit different use cases. Instance types comprise varying combinations of CPU, memory, storage, and networking capacity and give you the flexibility to choose the appropriate mix of resources for your applications. Each instance type includes one or more instance sizes, allowing you to scale your resources to the requirements of your target workload.

One of the key decision parameters apart from number of cpus, memory, processor family type related to the instance type is the [number of Elastic network interfaces(ENI's)](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html), which in-turn has a bearing on the maximum number of pods on that EC2 Instance. The list of [max pods per EC2 Instance type](https://github.com/awslabs/amazon-eks-ami/blob/master/files/eni-max-pods.txt) is maintained in a github.

****On-Demand EC2 Instances:****

With [On-Demand instances](https://aws.amazon.com/ec2/pricing/), you pay for compute capacity by the hour or the second depending on which instances you run. No longer-term commitments or upfront payments are needed. 

Amazon EC2 A1 instances deliver significant cost savings and are ideally suited for scale-out and Arm-based workloads that are supported by the extensive Arm ecosystem. You can now use Amazon Elastic Container Service for Kubernetes (EKS) to run containers on Amazon EC2 A1 Instances as part of a [public developer preview](https://github.com/aws/containers-roadmap/tree/master/preview-programs/eks-arm-preview). 

You can use the [AWS Simple Monthly Calculator](https://calculator.s3.amazonaws.com/index.html) or the new [pricing calculator](https://calculator.aws/) to get pricing for the On-Demand Ec2 instances for the EKS workder nodes.

****Spot EC2 Instances:****

Amazon [EC2 Spot instances](https://aws.amazon.com/ec2/pricing/) allow you to request spare Amazon EC2 computing capacity for up to 90% off the On-Demand price.

We can create multiple nodegroups with a mix of on-demand instance types and EC2 Spot instances to leverage the advantages of pricing between these two instance types.

![On-Demand and Spot Node Groups](../images/spot_diagram.png)
***(Image source: https://eksworkshop.com/spot)***


A sample yaml file for eksctl to create a nodegroup with EC2 spot instances is given below. During the creation of the Node Group, we have configured a node-label so that kubernetes knows what type of nodes we have provisioned. We set the lifecycle for the nodes as Ec2Spot. We are also tainting with PreferNoSchedule to prefer pods not be scheduled on Spot Instances. This is a “preference” or “soft” version of NoSchedule – the system will try to avoid placing a pod that does not tolerate the taint on the node, but it is not required.

``` yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: my-cluster-testscaling 
  region: us-west-2
nodeGroups:
  - name: ng-spot
    labels:
      lifecycle: Ec2Spot
    taints:
      spotInstance: true:PreferNoSchedule
    minSize: 2
    maxSize: 5
    instancesDistribution: # At least two instance types should be specified
      instanceTypes:
        - m4.large
        - c4.large
        - c5.large
      onDemandBaseCapacity: 0
      onDemandPercentageAboveBaseCapacity: 0 # all the instances will be spot instances
      spotInstancePools: 2
```
Use the node-labels to identify the lifecycle of the nodes.
```
$ kubectl get nodes --label-columns=lifecycle --selector=lifecycle=Ec2Spot
```

We should also deploy the [AWS Node Termination Handler](https://github.com/aws/aws-node-termination-handler) on each Spot Instance. This will monitor the EC2 metadata service on the instance for an interruption notice. The termination handler consists of a ServiceAccount, ClusterRole, ClusterRoleBinding, and a DaemonSet.

```
$ kubectl --namespace=kube-system get daemonsets 
NAME                           DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR       AGE
aws-node                       4         4         4       4            4           <none>              6d11h
aws-node-termination-handler   2         2         2       2            2           lifecycle=Ec2Spot   33m
kube-proxy                     4         4         4       4            4           <none>              6d11h
```

We can design our services to be deployed on Spot Instances when they are available. We can use Node Affinity in our manifest file to configure this, to prefer Spot Instances, but not require them. This will allow the pods to be scheduled on On-Demand nodes if no spot instances were available or correctly labelled.

``` yaml
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 1
            preference:
              matchExpressions:
              - key: lifecycle
                operator: In
                values:
                - Ec2Spot
      tolerations:
      - key: "spotInstance"
        operator: "Equal"
        value: "true"
        effect: "PreferNoSchedule"

```

You can do a complete hands-on workshop on EC2 spot instances at the [online AWS EKS Workshop](https://eksworkshop.com/beginner/150_spotworkers/).

****Compute Savings Plan:****

Compute Savings Plans, a new and flexible discount model that provides you with the same discounts as Reserved Instances, in exchange for a commitment to use a specific amount (measured in dollars per hour) of compute power over a one or three year period. The details are covered in the [Savings Plan launch page](https://aws.amazon.com/blogs/aws/new-savings-plans-for-aws-compute-services/).The plans automatically apply to any EC2 instance regardless of region, instance family, operating system, or tenancy, including those that are part of EKS clusters. For example, you can shift from C4 to C5 instances, move a workload from Dublin to London benefiting from Savings Plan prices along the way, without having to do anything.

The AWS Cost Explorer will help you to choose a Savings Plan, and will guide you through the purchase process.
![Compute Savings Plan](../images/Compute-savings-plan.png)

Note, that compute savings plans does not apply to EKS Fargate yet.

****Note, that the above pricing does not include the other AWS services like Data transfer charges, CloudWatch, Elastic Load Balancer and other AWS services that may be used by the Kubernetes applications.****
