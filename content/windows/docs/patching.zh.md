# 为 Windows 服务器和容器打补丁

为 Windows 服务器打补丁是 Windows 管理员的标准管理任务。可以使用不同的工具来完成此操作，如 Amazon System Manager - Patch Manager、WSUS、System Center Configuration Manager 等。但是，Amazon EKS 集群中的 Windows 节点不应被视为普通的 Windows 服务器。它们应被视为不可变的服务器。简而言之，避免更新现有节点，只需基于新的更新后的 AMI 启动新节点即可。

使用 [EC2 Image Builder](https://aws.amazon.com/image-builder/) 您可以通过创建配方和添加组件来自动构建 AMI。

以下示例显示了 **组件**,这些组件可以是 AWS 预先构建的 (Amazon 管理的)，也可以是您自己创建的 (我拥有的)。请特别注意名为 **update-windows** 的 Amazon 管理组件，它会在通过 EC2 Image Builder 管道生成 AMI 之前更新 Windows Server。

![](./images/associated-components.png)

EC2 Image Builder 允许您基于 Amazon 管理的公共 AMI 构建 AMI，并根据您的业务需求对其进行自定义。然后，您可以将这些 AMI 与启动模板关联，从而允许您将新的 AMI 链接到由 EKS 节点组创建的自动伸缩组。完成后，您可以开始终止现有的 Windows 节点，新节点将基于新的更新后的 AMI 启动。

## 推送和拉取 Windows 镜像
Amazon 发布了包含两个缓存的 Windows 容器镜像的 EKS 优化 AMI。

    mcr.microsoft.com/windows/servercore
    mcr.microsoft.com/windows/nanoserver

![](./images/images.png)

缓存的镜像会随着主操作系统的更新而更新。当 Microsoft 发布直接影响 Windows 容器基础镜像的新 Windows 更新时，该更新将作为普通 Windows 更新在主操作系统上启动。保持环境的最新状态可以在节点和容器级别提供更安全的环境。

Windows 容器镜像的大小会影响推送/拉取操作，从而导致容器启动时间变慢。[缓存 Windows 容器镜像](https://aws.amazon.com/blogs/containers/speeding-up-windows-container-launch-times-with-ec2-image-builder-and-image-cache-strategy/) 允许在 AMI 构建创建时而不是容器启动时进行昂贵的 I/O 操作 (文件提取)。因此，所有必需的镜像层都将在 AMI 上提取，并准备就绪以供使用，从而加快 Windows 容器启动并开始接受流量的时间。在推送操作期间，只有构成您镜像的层会被上传到存储库。

以下示例显示，在 Amazon ECR 上，**fluentd-windows-sac2004** 镜像仅有 **390.18MB**。这是在推送操作期间上传的数量。

以下示例显示将 [fluentd Windows ltsc](https://github.com/fluent/fluentd-docker-image/blob/master/v1.14/windows-ltsc2019/Dockerfile) 镜像推送到 Amazon ECR 存储库。存储在 ECR 中的层的大小为 **533.05MB**。

![](./images/ecr-image.png)

从 `docker image ls` 的输出可以看到，fluentd v1.14-windows-ltsc2019-1 在磁盘上的大小为 **6.96GB**,但这并不意味着它下载和提取了那么多数据。

实际上，在拉取操作期间，只会下载和提取 **压缩的 533.05MB**。

```bash
REPOSITORY                                                              TAG                        IMAGE ID       CREATED         SIZE
111122223333.dkr.ecr.us-east-1.amazonaws.com/fluentd-windows-coreltsc   latest                     721afca2c725   7 weeks ago     6.96GB
fluent/fluentd                                                          v1.14-windows-ltsc2019-1   721afca2c725   7 weeks ago     6.96GB
amazonaws.com/eks/pause-windows                                         latest                     6392f69ae6e7   10 months ago   255MB
```

size 列显示了镜像的总大小为 6.96GB。分解如下：

* Windows Server Core 2019 LTSC 基础镜像 = 5.74GB
* Fluentd 未压缩基础镜像 = 6.96GB
* 磁盘上的差异 = 1.2GB
* Fluentd [压缩后的最终镜像 ECR](https://docs.aws.amazon.com/AmazonECR/latest/userguide/repository-info.html) = 533.05MB

基础镜像已经存在于本地磁盘上，因此磁盘上的总量增加了 1.2GB。下次看到 size 列中的 GB 数量时，不要太担心，可能已经有 70% 以上是作为缓存的容器镜像存在于磁盘上。

## 参考
[使用 EC2 Image Builder 和镜像缓存策略加快 Windows 容器启动时间](https://aws.amazon.com/blogs/containers/speeding-up-windows-container-launch-times-with-ec2-image-builder-and-image-cache-strategy/)