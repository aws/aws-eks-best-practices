# Running Heterogeneous workloads

Kubernetes has support for heterogeneous clusters where you a have mixture of Linux and Windows nodes in the same cluster. Within that cluster, you can have mixture of Pods that run on Linux and Pods that run on Windows. You can even run multiple versions of Windows in the same cluster. However, there are several factors that will need to be accounted for when making this decision.

This guide specifically covers running Windows workloads on EKS but can be applied generally.

## Placement

It’s a good practice to keep the Windows workloads in a separate nodegroup  within the EKS cluster. If you are running multiple versions of Windows, deploy each version into a separate nodegroup.

If your operations model involves running multiple clusters, creating a separate cluster for running Windows workloads is not a bad idea. While the multi-cluster model comes with some advantages, there a lot of other factors, such as inter-cluster communication, single pane observability, a unified trust domain and the like, that should be considered beforehand.


## Scheduling 
There is a bit of a burden when it comes to scheduling workloads on Windows nodes. It is no different than scheduling workloads to run on specific instances in homogeneous (Linux only) clusters. You need to use taints and node selectors - in combination with tolerations - in order to keep Linux and Windows workloads on their respective OS-specific nodes. 

You can add node groups using different Windows Server image types (LTSC or SAC) to your cluster. In a cluster with mixed Windows Server types, you need to ensure that your Windows Server containers are not scheduled onto an incompatible version of Windows Server. This is achieved using node labels.

You can run windows Server node groups with multiple different LTSC or SAC versions as well. Windows Server containers have important version compatibility requirements:

* Windows Server containers built for LTSC do not run on SAC nodes, and vice-versa.
* Windows Server containers built for a specific LTSC or SAC version do not run on other LTSC or SAC versions without being rebuilt to target the other version.

Building your Windows Server container images as multi-arch images that can target multiple Windows Server versions can help you manage this versioning (https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-windows-ami.html) complexity.

If you are using EKS, eksctl offers ways to apply taints through clusterConfig

```yaml
nodeGroups:
  - name: windows-ng
    amiFamily: WindowsServer2019FullContainer
    ...
    labels:
      nodeclass: windows2019
    taints:
      os: "windows:NoSchedule"
```

And then use the following in your deployment manifest, to target the Windows specific deployments to specific Windows nodes. 

```yaml
nodeSelector:
    kubernetes.io/os: windows
    nodeclass: windows2019
  tolerations:
    - key: "os"
      operator: "Equal"
      value: "windows"
      effect: "NoSchedule"
```

The best practice is to use RuntimeClasses instead. You can create a Runtime class per nodegroup 

```yaml 
apiVersion: node.k8s.io/v1
kind: RuntimeClass
....
scheduling:
  nodeSelector:
    kubernetes.io/os: 'windows'
    nodeclass: windows2019
  tolerations:
  - effect: NoSchedule
    key: os
    operator: Equal
    value: "windows" 
```

And leverage them in the deployment Spec, like so, using runtimeClassName

```yaml    
apiVersion: apps/v1
kind: Deployment
...
spec:
  replicas: 1
  template:
    ...
    spec:
      runtimeClassName: windows2019
```

Handling multiple Windows versions in the same cluster is no different. Kubenetes versions 1.17+ the node controller applies some default labels based on Windows OS, architecture, and version. These labels can be used for scheduling workloads onto specific instances. 

## Network considerations 

Windows doesn't support hostNetwork. Consequently, at least one  Linux node (2 for production grade cluster) in the cluster is required to run the VPC resource controller and CoreDNS. When working with mixed clusters you need to understand that Windows hosts have only one ENI and that having 1 ENI can impact your pod density. Take this into consideration:

```
IP's available  =  (# of IP’s on the interface -1). 
``` 
