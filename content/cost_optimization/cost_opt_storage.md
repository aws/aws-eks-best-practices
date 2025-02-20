---
redirect: https://docs.aws.amazon.com/eks/latest/best-practices/cost-opt-storage.html
---


!!! info "We've Moved to the AWS Docs! 🚀"
    This content has been updated and relocated to improve your experience. 
    Please visit our new site for the latest version:
    [AWS EKS Best Practices Guide](https://docs.aws.amazon.com/eks/latest/best-practices/cost-opt-storage.html) on the AWS Docs

    Bookmarks and links will continue to work, but we recommend updating them for faster access in the future.

---

---
date: 2023-10-31
authors: 
  - Chance Lee
---
# Cost Optimization - Storage

## Overview

There are scenarios where you may want to run applications that need to preserve data for a short or long term basis. For such use cases, volumes can be defined and mounted by Pods so that their containers can tap into different storage mechanisms. Kubernetes supports different types of [volumes](https://kubernetes.io/docs/concepts/storage/volumes/) for ephemeral and persistent storage. The choice of storage largely depends on application requirements. For each approach, there are cost implications, and the practices detailed below which will help you accomplish cost efficiency for workloads needing some form of storage in your EKS environments. 


## Ephemeral Volumes

Ephemeral volumes are for applications that require transient local volumes but don't require data to be persisted after restarts. Examples of this include requirements for scratch space, caching, and read-only input data like configuration data and secrets. You can find more details of Kubernetes ephemeral volumes [here](https://kubernetes.io/docs/concepts/storage/ephemeral-volumes/). Most of ephemeral volumes (e.g. emptyDir, configMap, downwardAPI, secret, hostpath) are backed by locally-attached writable devices (usually the root disk) or RAM, so it's important to choose the most cost efficient and performant host volume. 


### Using EBS Volumes

*We recommend starting with [gp3](https://aws.amazon.com/ebs/general-purpose/) as the host root volume.* It is the latest general purpose SSD volume offered by Amazon EBS and also offers a lower price (up to 20%) per GB compared to gp2 volumes. 


### Using Amazon EC2 Instance Stores

[Amazon EC2 instance stores](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/InstanceStorage.html) provide temporary block-level storage for your EC2 instances. The storage provided by EC2 instance stores is accessible through disks that are physically attached to the hosts. Unlike Amazon EBS, you can only attach instance store volumes when the instance is launched, and these volumes only exist during the lifetime of the instance. They cannot be detached and re-attached to other instances. You can learn more about Amazon EC2 instance stores [here](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/InstanceStorage.html). *There are no additional fees associated with an instance store volume.* This makes them (instance store volumes) _more cost efficient_ than the general EC2 instances with large EBS volumes. 

To use local store volumes in Kubernetes, you should partition, configure, and format the disks [using the Amazon EC2 user-data](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instancedata-add-user-data.html) so that volumes can be mounted as a [HostPath](https://kubernetes.io/docs/concepts/storage/volumes/#hostpath) in the pod spec. Alternatively, you can leverage the [Local Persistent Volume Static Provisioner](https://github.com/kubernetes-sigs/sig-storage-local-static-provisioner) to simplify local storage management. The Local Persistent Volume static provisioner allows you to access local instance store volumes through the standard Kubernetes PersistentVolumeClaim (PVC) interface. Furthermore, it will provision PersistentVolumes (PVs) that contains node affinity information to schedule Pods to the correct nodes. Although it uses Kubernetes PersistentVolumes, EC2 instance store volumes are ephemeral in nature. Data written to ephemeral disks is only available during the instance’s lifetime. When the instance is terminated, so is the data. Please refer to this [blog](https://aws.amazon.com/blogs/containers/eks-persistent-volumes-for-instance-store/) for more details.

Keep in mind that when using Amazon EC2 instance store volumes, the total IOPS limit is shared with the host and it binds Pods to a specific host. You should thoroughly review your workload requirements before adopting Amazon EC2 instance store volumes.


## Persistent Volumes

Kubernetes is typically associated with running stateless applications. However, there are scenarios where you may want to run microservices that need to preserve persistent data or information from one request to the next. Databases are a common example for such use cases. However, Pods, and the containers or processes inside them, are ephemeral in nature. To persist data beyond the lifetime of a Pod, you can use PVs to define access to storage at a specific location that is independent from the Pod. *The costs associated with PVs is highly dependent on the type of storage being used and how applications are consuming it.* 

There are different types of storage options that support Kubernetes PVs on Amazon EKS listed [here](https://docs.aws.amazon.com/eks/latest/userguide/storage.html). The storage options covered below are Amazon EBS, Amazon EFS, Amazon FSx for Lustre, Amazon FSx for NetApp ONTAP.


### Amazon Elastic Block Store (EBS) Volumes

Amazon EBS volumes can be consumed as Kubernetes PVs to provide block-level storage volumes. These are well suited for databases that rely on random reads & writes and throughput-intensive applications that perform long, continuous reads and writes. [The Amazon Elastic Block Store Container Storage Interface (CSI) driver](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html) allows Amazon EKS clusters to manage the lifecycle of Amazon EBS volumes for persistent volumes. The Container Storage Interface enables and facilitates interaction between Kubernetes and a storage system. When a CSI driver is deployed to your EKS cluster, you can access it’s capabilities through the native Kubernetes storage resources such as Persistent Volumes (PVs), Persistent Volume Claims (PVCs) and Storage Classes (SCs). This [link](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/tree/master/examples/kubernetes) provides practical examples of how to interact with Amazon EBS volumes with Amazon EBS CSI driver.


#### Choosing the right volume

*We recommend using the latest generation of block storage (gp3) as it provides the right balance between price and performance*. It also allows you to scale volume IOPS and throughput independently of volume size without needing to provision additional block storage capacity. If you’re currently using gp2 volumes, we highly recommend migrating to gp3 volumes. This [blog](https://aws.amazon.com/blogs/containers/migrating-amazon-eks-clusters-from-gp2-to-gp3-ebs-volumes/) explains how to migrate from *gp2* on *gp3* on Amazon EKS clusters. 

When you have applications that require higher performance and need volumes larger than what a single [gp3 volume can support](https://aws.amazon.com/ebs/general-purpose/), you should consider using [io2 block express](https://aws.amazon.com/ebs/provisioned-iops/). This type of storage is ideal for your largest, most I/O intensive, and mission critical deployment such as SAP HANA or other large databases with low latency requirements. Keep in mind that an instance's EBS performance is bounded by the instance's performance limits, so not all the instances support io2 block express volumes. You can check the supported instance types and other considerations in this [doc](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/provisioned-iops.html). 

*A single gp3 volume can support up to up to 16,000 max IOPS, 1,000 MiB/s max throughput, max 16TiB. The latest generation of Provisioned IOPS SSD volume that provides up to 256,000 IOPS, 4,000 MiB/s, throughput, and 64TiB.*

Among these options, you should best tailor your storage performance and cost to the needs of your applications.


#### Monitor and optimize over time

It's important to understand your application's baseline performance and monitor it for selected volumes to check if it's meeting your requirements/expectations or if it's over-provisioned (e.g. a scenario where provisioned IOPS are not being fully utilized). 

Instead of allocating a large volume from the beginning, you can gradually increase the size of the volume as you accumulate data. You can dynamically re-size volumes using the [volume resizing](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/tree/master/examples/kubernetes/resizing) feature in the Amazon Elastic Block Store CSI driver (aws-ebs-csi-driver). *Keep in mind that you can only increase the EBS volume size.*

To identify and remove any dangling EBS volumes, you can use [AWS trusted advisor’s cost optimization category](https://docs.aws.amazon.com/awssupport/latest/user/cost-optimization-checks.html). This feature helps you identify unattached volumes or volumes with very low write activity for a period of time. There is a cloud-native open-source, read-only tool called [Popeye](https://github.com/derailed/popeye) that scans live Kubernetes clusters and reports potential issues with deployed resources and configurations. For example, it can scan for unused PVs and PVCs and check whether they are bound or whether there is any volume mount error.

For a deep dive on monitoring, please refer to the [EKS cost optimization observability guide](https://aws.github.io/aws-eks-best-practices/cost_optimization/cost_opt_observability/).  

One other option you can consider is the [AWS Compute Optimizer Amazon EBS volume recommendations](https://docs.aws.amazon.com/compute-optimizer/latest/ug/view-ebs-recommendations.html). This tool automatically identifies the optimal volume configuration and correct level of performance needed. For example, it can be used for optimal settings pertaining to provisioned IOPS, volume sizes, and types of EBS volumes based on the maximum utilization during the past 14 days. It also quantifies the potential monthly cost savings derived from its recommendations. You can review this [blog](https://aws.amazon.com/blogs/storage/cost-optimizing-amazon-ebs-volumes-using-aws-compute-optimizer/) for more details.


#### Backup retention policy

You can back up the data on your Amazon EBS volumes by taking point-in-time snapshots. The Amazon EBS CSI driver supports volume snapshots. You can learn how to create a snapshot and restore an EBS PV using the steps outlined [here](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/blob/master/examples/kubernetes/snapshot/README.md). 

Subsequent snapshots are incremental backups, meaning that only the blocks on the device that have changed after your most recent snapshot are saved. This minimizes the time required to create the snapshot and saves on storage costs by not duplicating data. However, growing the number of old EBS snapshots without a proper retention policy can cause unexpected costs when operating at scale. If you’re directly backing up Amazon EBS volumes through AWS API, you can leverage [Amazon Data Lifecycle Manager](https://aws.amazon.com/ebs/data-lifecycle-manager/) (DLM) that provides an automated, policy-based lifecycle management solution for Amazon Elastic Block Store (EBS) Snapshots and EBS-backed Amazon Machine Images (AMIs). The console makes it easier to automate the creation, retention, and deletion of EBS Snapshots and AMIs. 

!!! note 
    There is currently no way to make use of Amazon DLM via the Amazon EBS CSI driver.

In a Kubernetes environment, you can leverage an open-source tool called [Velero](https://velero.io/) to backup your EBS Persistent Volumes. You can set a TTL flag when scheduling the job to expire backups. Here is a [guide](https://velero.io/docs/v1.12/how-velero-works/#set-a-backup-to-expire) from Velero as an example. 


### Amazon Elastic File System (EFS)

[Amazon Elastic File System (EFS)](https://aws.amazon.com/efs/) is a serverless, fully elastic file system that lets you share file data using standard file system interface and file system semantics for a broad spectrum of workloads and applications. Examples of workloads and applications include Wordpress and Drupal, developer tools like JIRA and Git, and shared notebook system such as Jupyter as well as home directories.

One of main benefits of Amazon EFS is that it can be mounted by multiple containers spread across multiple nodes and multiple availability zones. Another benefit is that you only pay for the storage you use. EFS file systems will automatically grow and shrink as you add and remove files which eliminates the need for capacity planning. 

To use Amazon EFS in Kubernetes, you need to use the Amazon Elastic File System Container Storage Interface (CSI) Driver, [aws-efs-csi-driver](https://github.com/kubernetes-sigs/aws-efs-csi-driver). Currently, the driver can dynamically create [access points](https://docs.aws.amazon.com/efs/latest/ug/efs-access-points.html). However, the Amazon EFS file system has to be provisioned first and provided as an input to the Kubernetes storage class parameter. 


#### Choosing the right EFS storage class

Amazon EFS offers [four storage classes](https://docs.aws.amazon.com/efs/latest/ug/storage-classes.html). 

Two standard storage classes:

* Amazon EFS Standard 
* [Amazon EFS Standard-Infrequent Access](https://aws.amazon.com/blogs/aws/optimize-storage-cost-with-reduced-pricing-for-amazon-efs-infrequent-access/) (EFS Standard-IA) 


Two one-zone storage classes: 

* [Amazon EFS One Zone](https://aws.amazon.com/blogs/aws/new-lower-cost-one-zone-storage-classes-for-amazon-elastic-file-system/) 
* Amazon EFS One Zone-Infrequent Access (EFS One Zone-IA)


The Infrequent Access (IA) storage classes are cost-optimized for files that are not accessed every day. With Amazon EFS lifecycle management, you can move files that have not been accessed for the duration of the lifecycle policy (7, 14, 30, 60, or 90 days) to the IA storage classes *which can reduce the storage cost by up to 92 percent compared to EFS Standard and EFS One Zone storage classes respectively*. 

With EFS Intelligent-Tiering, lifecycle management monitors the access patterns of your file system and automatically move files to the most optimal storage class. 

!!! note 
    aws-efs-csi-driver currently doesn’t have a control on changing storage classes, lifecycle management or Intelligent-Tiering. Those should be setup manually in the AWS console or through the EFS APIs.

!!! note
    aws-efs-csi-driver isn’t compatible with Window-based container images.

!!! note
    There is a known memory issue when *vol-metrics-opt-in* (to emit volume metrics) is enabled due to the [DiskUsage](https://github.com/kubernetes/kubernetes/blob/ee265c92fec40cd69d1de010b477717e4c142492/pkg/volume/util/fs/fs.go#L66) function that consumes an amount of memory that is proportional to the size of your filesystem. *Currently, we recommend to disable the* *`--vol-metrics-opt-in` option on large filesystems to avoid consuming too much memory. Here is a github issue [link](https://github.com/kubernetes-sigs/aws-efs-csi-driver/issues/1104) for more details.*


### Amazon FSx for Lustre

Lustre is a high-performance parallel file system commonly used in workloads requiring throughput up to hundreds of GB/s and sub-millisecond per-operation latencies. It’s used for scenarios such as machine learning training, financial modeling, HPC, and video processing. [Amazon FSx for Lustre](https://aws.amazon.com/fsx/lustre/) provides a fully managed shared storage with the scalability and performance, seamlessly integrated with Amazon S3. 

You can use Kubernetes persistent storage volumes backed by FSx for Lustre using the [FSx for Lustre CSI driver](https://github.com/kubernetes-sigs/aws-fsx-csi-driver) from Amazon EKS or your self-managed Kubernetes cluster on AWS. See the [Amazon EKS documentation](https://docs.aws.amazon.com/eks/latest/userguide/fsx-csi.html) for more details and examples. 

#### Link to Amazon S3

It's recommended to link a highly durable long-term data repository residing on Amazon S3 with your FSx for Lustre file system. Once linked, large datasets are lazy-loaded as needed from Amazon S3 to FSx for Lustre file systems. You can also run your analyses and your results back to S3, and then delete your [Lustre] file system. 


#### Choosing the right deployment and storage options

FSx for Lustre provides different deployment options. The first option is called *scratch* and it doesn’t replicate data, while the second option is called *persistent* which, as the name implies, persists data. 

The first option (*scratch*) can be used *to reduce the cost of temporary shorter-term data processing.* The persistent deployment option _is designed for longer-term storage_ that automatically replicates data within an AWS Availability Zone. It also supports both SSD and HDD storage. 

You can configure the desired deployment type under parameters in the FSx for lustre filesystem’s Kubernetes StorageClass. Here is an [link](https://github.com/kubernetes-sigs/aws-fsx-csi-driver/tree/master/examples/kubernetes/dynamic_provisioning#edit-storageclass) that provides sample templates.

!!! note
    For latency-sensitive workloads or workloads requiring the highest levels of IOPS/throughput, you should choose SSD storage. For throughput-focused workloads that aren’t latency-sensitive, you should choose HDD storage.


#### Enable data compression

You can also enable data compression on your file system by specifying “LZ4” as the Data Compression Type. Once it’s enabled, all newly-written files will be automatically compressed on FSx for Lustre before they are written to disk and uncompressed when they are read. LZ4 data compression algorithm is lossless so the original data can be fully reconstructed from the compressed data. 

You can configure the data compression type as LZ4 under parameters in the FSx for lustre filesystem’s Kubernetes StorageClass. Compression is disabled when the value is set to NONE, which is default. This [link](https://github.com/kubernetes-sigs/aws-fsx-csi-driver/tree/master/examples/kubernetes/dynamic_provisioning#edit-storageclass) provides sample templates.

!!! note
    Amazon FSx for Lustre isn’t compatible with Window-based container images.


### Amazon FSx for NetApp ONTAP

[Amazon FSx for NetApp ONTAP](https://aws.amazon.com/fsx/netapp-ontap/) is a fully managed shared storage built on NetApp’s ONTAP file system. FSx for ONTAP provides feature-rich, fast, and flexible shared file storage that’s broadly accessible from Linux, Windows, and macOS compute instances running in AWS or on premises. 

Amazon FSx for NetApp ONTAP supports two tiers of storage: *1/primary tier* and *2/capacity pool tier.* 

The *primary tier* is a provisioned, high-performance SSD-based tier for active, latency-sensitive data. The fully elastic *capacity pool tier* is cost-optimized for infrequently accessed data, automatically scales as data is tiered to it, and offers virtually unlimited petabytes of capacity. You can enable data compression and deduplication on capacity pool storage and further reduce the amount of storage capacity your data consumes. NetApp’s native, policy-based FabricPool feature continually monitors data access patterns, automatically transferring data bidirectionally between storage tiers to optimize performance and cost.

NetApp's Astra Trident provides dynamic storage orchestration using a CSI driver which allows Amazon EKS clusters to manage the lifecycle of persistent volumes PVs backed by Amazon FSx for NetApp ONTAP file systems. To get started, see [Use Astra Trident with Amazon FSx for NetApp ONTAP](https://docs.netapp.com/us-en/trident/trident-use/trident-fsx.html) in the Astra Trident documentation.


## Other considerations

### Minimize the size of container image

Once containers are deployed, container images are cached on the host as multiple layers. By reducing the size of images, the amount of storage required on the host can be reduced. 

By using slimmed-down base images such as [scratch](https://hub.docker.com/_/scratch) images or [distroless](https://github.com/GoogleContainerTools/distroless) container images (that contain only your application and its runtime dependencies) from the beginning, *you can reduce storage cost in addition to other ancillary benefits such as a reducing the attack surface area and shorter image pull times.*

You should also consider using open source tools, such as [Slim.ai](https://www.slim.ai/docs/quickstart) that provides an easy, secure way to create minimal images.

Multiple layers of packages, tools, application dependencies, libraries can easily bloat the container image size. By using multi-stage builds, you can selectively copy artifacts from one stage to another, excluding everything that isn’t necessary from the final image. You can check more image-building best practices [here](https://docs.docker.com/get-started/09_image_best/). 

Another thing to consider is how long to persist cached images. You may want to clean up the stale images from the image cache when a certain amount of disk is utilized. Doing so will help make sure you have enough space for the host’s operation. By default, the [kubelet](https://kubernetes.io/docs/reference/generated/kubelet) performs garbage collection on unused images every five minutes and on unused containers every minute. 

*To configure options for unused container and image garbage collection, tune the kubelet using a [configuration file](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-config-file/) and change the parameters related to garbage collection using the [`KubeletConfiguration`](https://kubernetes.io/docs/reference/config-api/kubelet-config.v1beta1/) resource type.* 

You can learn more about it in the Kubernetes [documentation](https://kubernetes.io/docs/concepts/architecture/garbage-collection/#containers-images). 
