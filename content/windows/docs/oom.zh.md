# 避免OOM错误

Windows没有像Linux那样的内存不足进程终止机制。Windows总是将所有用户模式内存分配视为虚拟的，并且页面文件是强制性的。其净效果是，Windows不会像Linux那样达到内存不足条件。进程将换页到磁盘而不是被终止内存不足(OOM)。如果内存过度供应并且所有物理内存都已耗尽，那么换页可能会降低性能。

## 为系统和kubelet保留内存
与Linux不同，在Linux中`--kubelet-reserve`**捕获**kubernetes系统守护进程(如kubelet、容器运行时等)的资源预留，而`--system-reserve`**捕获**操作系统系统守护进程(如sshd、udev等)的资源预留。在**Windows**上，这些标志不会**捕获**和**设置**对**kubelet**或节点上运行的**进程**的内存限制。

但是，您可以结合使用这些标志来管理**NodeAllocatable**,以减少节点上的容量，并使用Pod清单**内存资源限制**来控制每个Pod的内存分配。使用这种策略，您可以更好地控制内存分配，并且有一种最小化Windows节点内存不足(OOM)的机制。

在Windows节点上，最佳实践是至少为操作系统和进程保留2GB内存。使用`--kubelet-reserve`和/或`--system-reserve`来减少NodeAllocatable。

根据[Amazon EKS自管理Windows节点](https://docs.aws.amazon.com/eks/latest/userguide/launch-windows-workers.html)文档，使用CloudFormation模板启动一个新的Windows节点组，并对kubelet配置进行自定义。CloudFormation有一个名为`BootstrapArguments`的元素，它与`KubeletExtraArgs`相同。使用以下标志和值：

```bash
--kube-reserved memory=0.5Gi,ephemeral-storage=1Gi --system-reserved memory=1.5Gi,ephemeral-storage=1Gi --eviction-hard memory.available<200Mi,nodefs.available<10%"
```

如果使用eksctl进行部署，请查看以下文档以自定义kubelet配置https://eksctl.io/usage/customizing-the-kubelet/

## Windows容器内存需求
根据[Microsoft文档](https://docs.microsoft.com/en-us/virtualization/windowscontainers/deploy-containers/system-requirements),NANO版本的Windows Server基础镜像至少需要30MB，而Server Core需要45MB。随着添加Windows组件(如.NET Framework、Web服务IIS和应用程序)，这些数字会增加。

了解您的Windows容器镜像所需的最小内存量(即基础镜像加上其应用程序层)非常重要，并将其设置为Pod规范中容器的资源/请求。您还应该设置一个限制，以防止Pod在应用程序问题的情况下消耗所有可用的节点内存。

在下面的示例中，当Kubernetes调度程序尝试将Pod放置在节点上时，Pod的请求用于确定哪个节点有足够的可用资源进行调度。

```yaml
 spec:
  - name: iis
    image: mcr.microsoft.com/windows/servercore/iis:windowsservercore-ltsc2019
    resources:
      limits:
        cpu: 1
        memory: 800Mi
      requests:
        cpu: .1
        memory: 128Mi
```
## 结论

使用这种方法可以最小化内存耗尽的风险，但不能完全防止内存耗尽。使用Amazon CloudWatch Metrics，您可以设置警报和补救措施，以防发生内存耗尽。