# Assigning PODs to Nodes Best practices

In order to keep Linux and Windows workloads on their respective OS-specific nodes, you need to use some combination of node selectors and taints/tolerations. The main goal of scheduling workloads in a heterogeneous environment is to avoid breaking compatibility for existing Linux workloads.

## Ensuring OS-specific workloads land on the appropriate container host

Users can ensure Windows containers can be scheduled on the appropriate host using nodeSelectors. All Kubernetes nodes today have the following default labels:

    kubernetes.io/os = [windows|linux]
    kubernetes.io/arch = [amd64|arm64|...]

If a Pod specification does not include a nodeSelector like ``"kubernetes.io/os": windows``, the Pod may be scheduled on any host, Windows or Linux. This can be problematic since a Windows container can only run on Windows and a Linux container can only run on Linux. 

In Enterprise environments, it's not uncommon to have a large number of pre-existing deployments for Linux containers, as well as an ecosystem of off-the-shelf configurations, like Helm charts. In these situations, you may be hesitant to make changes to a deployment's nodeSelectors. **The alternative is to use Taints**.

For example: `--register-with-taints='os=windows:NoSchedule'`

If you are using EKS, eksctl offers ways to apply taints through clusterConfig:

```yaml
NodeGroups:
  - name: windows-ng
    amiFamily: WindowsServer2019FullContainer
    ...
    labels:
      nodeclass: windows2019
    taints:
      os: "windows:NoSchedule"
```

Adding a taint to all Windows nodes, the scheduler will not schedule pods on those nodes unless they tolerate the taint. Pod manifest example:

```yaml
nodeSelector:
    kubernetes.io/os: windows
tolerations:
    - key: "os"
      operator: "Equal"
      value: "windows"
      effect: "NoSchedule"
```

## Handling multiple Windows build in the same cluster

The Windows container base image used by each pod must match the same kernel build version as the node. If you want to use multiple Windows Server builds in the same cluster, then you should set additional node labels, nodeSelectors or leverage a label called **windows-build**.

Kubernetes 1.17 automatically adds a new label **node.kubernetes.io/windows-build** to simplify the management of multiple Windows build in the same cluster. If you're running an older version, then it's recommended to add this label manually to Windows nodes.

This label reflects the Windows major, minor, and build number that need to match for compatibility. Below are values used today for each Windows Server version.


| Product Name | Build Number(s) |
| -------- | -------- |
| Server core 2019 LTSC    | 10.0.17763    |
| Server core 1809 SAC   | 10.0.17763    |
| Server core 2004 SAC     | 10.0.19041    |
| Server core 20H2 SAC | 10.0.19042 |

It is possible to check the OS build version through the following command:

```bash    
kubectl get pods -o wide
```

The KERNEL-VERSION output matches the Windows OS build version.

```bash 
NAME                           STATUS   ROLES    AGE   VERSION              INTERNAL-IP    EXTERNAL-IP     OS-IMAGE                         KERNEL-VERSION                  CONTAINER-RUNTIME
ip-172-31-20-44.ec2.internal   Ready    <none>   42d   v1.18.9-eks-d1db3c   172.31.20.44   3.237.46.98     Windows Server 2019 Datacenter   10.0.17763.1697                 docker://19.3.13
ip-172-31-44-38.ec2.internal   Ready    <none>   42d   v1.18.9-eks-d1db3c   172.31.44.38   54.91.221.109   Amazon Linux 2                   4.14.209-160.339.amzn2.x86_64   docker://19.3.6
ip-172-31-5-245.ec2.internal   Ready    <none>   31d   v1.18.9-eks-d1db3c   172.31.5.245   3.236.151.236   Windows Server Datacenter        10.0.19041.685                  docker://19.3.14
```

The example below applies an additional nodeSelector to the pod manifest in order to match the correct Windows-build version when running different Windows node groups OS versions.

```yaml
nodeSelector:
    kubernetes.io/os: windows
    node.kubernetes.io/windows-build: '10.0.17763'
tolerations:
    - key: "os"
    operator: "Equal"
    value: "windows"
    effect: "NoSchedule"
```

## Simplifying NodeSelector and Toleration in Pod manifests using RuntimeClass

You can also make use of RuntimeClass to simplify the process of using taints and tolerations. This can be accomplished by creating a RuntimeClass object which is used to encapsulate these taints and tolerations.

Create a RuntimeClass by running the following manifest:

```yaml
apiVersion: node.k8s.io/v1beta1
kind: RuntimeClass
metadata:
  name: windows-2019
handler: 'docker'
scheduling:
  nodeSelector:
    kubernetes.io/os: 'windows'
    kubernetes.io/arch: 'amd64'
    node.kubernetes.io/windows-build: '10.0.17763'
  tolerations:
  - effect: NoSchedule
    key: os
    operator: Equal
    value: "windows"
```

Once the Runtimeclass is created, assign it using as a Spec on the Pod manifest:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iis-2019
  labels:
    app: iis-2019
spec:
  replicas: 1
  template:
    metadata:
      name: iis-2019
      labels:
        app: iis-2019
    spec:
      runtimeClassName: windows-2019
      containers:
      - name: iis
```


## Additional documentations


AWS Official Documentation:
https://docs.aws.amazon.com/eks/latest/userguide/windows-support.html

To better understand how Pod Networking (CNI) works, check the following link: https://docs.aws.amazon.com/eks/latest/userguide/pod-networking.html
