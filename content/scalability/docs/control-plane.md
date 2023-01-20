# Kubernetes Control Plane

The Kubernetes control plane is the Kubernetes components such as the API Server, kubelet, and Kubernetes Controller Manager. Scalability limits of these components are different depending on what you’re running in the cluster, but the areas with the biggest impact to scale include the Kubernetes version, utilization, and individual Node scaling.

## Use EKS 1.24 or above

EKS 1.24 introduced a number of changes and switches the default container runtime to [containerd](https://containerd.io/) instead of docker. Containerd helps clusters scale by increasing individual node performance by limiting container runtime features to closely align with Kubernetes’ needs. Containerd is available in every supported version of EKS and if you would like to switch to containerd in versions prior to 1.24 please read the documentation about [Dockershim deprecation](https://docs.aws.amazon.com/eks/latest/userguide/dockershim-deprecation.html).

## Automate Amazon Machine Image (AMI) updates

It is recommended that you use the latest [Amazon EKS optimized Amazon Linux 2](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html) or [Amazon EKS optimized Bottlerocket AMI](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami-bottlerocket.html) for your node image. Karpenter will automatically use the [latest available AMI](https://karpenter.sh/v0.19.0/aws/provisioning/#amazon-machine-image-ami-family) to provision new nodes in the cluster. Managed node groups will update the AMI during a [node group update](https://docs.aws.amazon.com/eks/latest/userguide/update-managed-node-group.html) but will not update the AMI ID at node provisioning time.

For Managed Node Groups you need to update the Auto Scaling Group (ASG) launch template with new AMI IDs when they are available for patch releases. AMI minor versions (e.g. 1.23.5 to 1.24.3) will be available in the EKS console and API as [upgrades for the node group](https://docs.aws.amazon.com/eks/latest/userguide/update-managed-node-group.html). Patch release versions (e.g. 1.23.5 to 1.23.6) will not be presented as upgrades for the node groups. If you want to keep your node group up to date with AMI patch releases you need to create new launch template version and let the node group replace instances with the new AMI release.

You can find the latest available AMI from [this page](https://docs.aws.amazon.com/eks/latest/userguide/eks-optimized-ami.html) or use the AWS CLI.

```
aws ssm get-parameter \
  --name /aws/service/eks/optimized-ami/1.24/amazon-linux-2/recommended/image_id \
  --query "Parameter.Value" \
  --output text
```

## Limit workload and node bursting

The EKS control plane will automatically scale as your cluster grows, but there are limits on how fast it will scale. When you first create an EKS cluster the Control Plane will not immediately be able to scale to hundreds of nodes or thousands of pods. To avoid reaching API limits on the control plane you should limit scaling spikes that increase cluster size by double digit percentages at a time (e.g. 1000 nodes to 1100 nodes or 4000 to 4500 pods at once).

Scaling large applications requires infrastructure to adapt to become fully ready (e.g. warming load balancers). To control the speed of scaling make sure you are scaling based on the right metrics for your application. CPU and memory scaling may not accurately predict your application constraints and using custom metrics (e.g. requests per second) in Kubernetes Horizontal Pod Autoscaler](hPA) may be a more accurate scaling option.

To use a custom metric see the examples in the [Kubernetes documentation](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/#autoscaling-on-multiple-metrics-and-custom-metrics).

## Scale nodes and pods down safely using Pod Disruption Budgets or Karpenter TTL Settings

Use Karpenter’s [time to live (TTL)](https://aws.github.io/aws-eks-best-practices/karpenter/#use-timers-ttl-to-automatically-delete-nodes-from-the-cluster) settings to replace instances after they’ve been running for a specified amount of time. Self managed node groups can use the `max-instance-lifetime` setting to cycle nodes automatically. Managed node groups do not currently have this feature but you can track the request [here on GitHub](https://github.com/aws/containers-roadmap/issues/1190).

Remove nodes when they have no running workloads using scale down settings in the Kubernetes Cluster Autoscaler and Karpenter. Set Pod Disruption budgets (PDB) on your workloads to avoid application outages when nodes are removed. Consider enabling [consolidation](https://aws.github.io/aws-eks-best-practices/karpenter/#configure-requestslimits-for-all-non-cpu-resources-when-using-consolidation) in your Karpenter provisioner to replace nodes that are not fully utilized.

You can set the node scale down threshold in the Kubernetes Cluster Autoscaler with the [`--scale-down-utilization-threshold`](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/FAQ.md#how-does-scale-down-work) or in Karpenter you can use the ttlSecondsAfterEmpty provisioner setting.

## Use Client-Side Cache when running Kubectl

Using the kubectl command, you can add additional load to the Kubernetes control plane. You should avoid running scripts or automation that uses kubectl repeatedly (e.g. in a for loop) because each command makes dozens or hundreds of calls to the API server.

This can be especially impactful if you run kubectl from a container without a client-side cache. The client-side cache is a local file that caches information from the cluster about APIs available and Custom Resources (CR). Refreshing the cache happens by default every 10 minutes when kubectl is run and will make hundreds of API calls. You’re likely to run into API throttling issues if you run kubectl commands frequently without a local cache.

## Disable kubectl Compression

Disabling kubectl compression in your kubeconfig file can reduce API and client CPU usage. By default the server will compress data sent to the client to optimize network bandwidth. This adds CPU load on the client and server for every request and disabling compression can reduce the overhead and latency if you have adequate bandwidth. To disable compression you can use the --disable-compression flag or set DisableCompression: false in your kubeconfig file.

## Shard Cluster Autoscaler

The [Kubernetes Cluster Autoscaler has been tested](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/proposals/scalability_tests.md) to scale up to 1000 nodes. On a large cluster with more than 1000 nodes, it is recommended to run multiple instances of the Cluster Autoscaler in shard mode. Each Cluster Autoscaler instance is configured to scale a set of node groups. The following example shows 2 cluster autoscaling configurations that are configured to each scale 4 node groups.

ClusterAutoscaler-1

```
autoscalingGroups:
- name: eks-core-node-grp-20220823190924690000000011-80c1660e-030d-476d-cb0d-d04d585a8fcb
  maxSize: 50
  minSize: 2
- name: eks-data_m1-20220824130553925600000011-5ec167fa-ca93-8ca4-53a5-003e1ed8d306
  maxSize: 450
  minSize: 2
- name: eks-data_m2-20220824130733258600000015-aac167fb-8bf7-429d-d032-e195af4e25f5
  maxSize: 450
  minSize: 2
- name: eks-data_m3-20220824130553914900000003-18c167fa-ca7f-23c9-0fea-f9edefbda002
  maxSize: 450
  minSize: 2
```

ClusterAutoscaler-2

```
autoscalingGroups:
- name: eks-data_m4-2022082413055392550000000f-5ec167fa-ca86-6b83-ae9d-1e07ade3e7c4
  maxSize: 450
  minSize: 2
- name: eks-data_m5-20220824130744542100000017-02c167fb-a1f7-3d9e-a583-43b4975c050c
  maxSize: 450
  minSize: 2
- name: eks-data_m6-2022082413055392430000000d-9cc167fa-ca94-132a-04ad-e43166cef41f
  maxSize: 450
  minSize: 2
- name: eks-data_m7-20220824130553921000000009-96c167fa-ca91-d767-0427-91c879ddf5af
  maxSize: 450
  minSize: 2
```

## Use multiple EBS volumes for containers

EBS volumes have input/output (I/O) quota based on the type of volume (e.g. gp3) and the size of the disk. If your applications share a single EBS root volume with the host this can exhaust the disk quota for the entire host and cause other applications to wait for available capacity. Applications write to disk if they write files to their overlay partition, mount a local volume from the host, and also when they log to standard out (STDOUT) depending on the logging agent used.

To avoid disk I/O exhaustion you should mount a second volume to the container state folder (e.g. /run/containerd), use separate EBS volumes for workload storage, and disable unnecessary local logging.

To mount a second volume to your EC2 instances using [eksctl](https://eksctl.io/) you can use a node group with this configuration:

```
managedNodeGroups:
  - name: al2-workers
    amiFamily: AmazonLinux2
    desiredCapacity: 2
    volumeSize: 80
    additionalVolumes:
      - volumeName: '/dev/sdz'
        volumeSize: 100
    preBootstrapCommands:
      - "systemctl stop containerd"
      - "mkfs -t ext4 /dev/nvme1n1"
      - "rm -rf /var/lib/containerd/*"
      - "mount /dev/nvme1n1 /var/lib/containerd/"
      - "systemctl start containerd"
```

If you are using terraform to provision your node groups please see examples in [EKS Blueprints for terraform](https://github.com/aws-ia/terraform-aws-eks-blueprints/blob/main/examples/node-groups/managed-node-groups/main.tf). If you are using Karpenter to provision nodes you can use [`blockDeviceMappings`](https://karpenter.sh/v0.20.0/concepts/node-templates/#block-device-mappings) with node user-data to add additional volumes.

To mount an EBS volume directly to your pod you should use the [AWS EBS CSI driver](https://github.com/kubernetes-sigs/aws-ebs-csi-driver) and consume a volume with a storage class.

```
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-sc
provisioner: ebs.csi.aws.com
volumeBindingMode: WaitForFirstConsumer
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ebs-claim
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ebs-sc
  resources:
    requests:
      storage: 4Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: public.ecr.aws/docker/library/nginx
    volumeMounts:
    - name: persistent-storage
      mountPath: /data
  volumes:
  - name: persistent-storage
    persistentVolumeClaim:
      claimName: ebs-claim
```

## Disable unnecessary logging to disk

Avoid unnecessary local logging by not running your applications with debug logging in production and disabling logging that reads and writes to disk frequently. Journald is the local logging service that keeps a log buffer in memory and flushes to disk periodically. Journald is preferred over syslog which logs every line immediately to disk. Disabling syslog also lowers the total amount of storage you need and avoids needing complicated log rotation rules. To disable syslog you can add the following snippet to your cloud-init configuration:

```
runcmd:
  - [ systemctl, disable, --now, syslog.service ]
```
