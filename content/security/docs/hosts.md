# Protecting the infrastructure (hosts)
Inasmuch as it's important to secure your container images, it's equally important to safeguard the infrastructure that runs them. This section explores different ways to mitigate risks from attacks launched directly against the host.  These guidelines should be used in conjunction with those outlined in the [Runtime Security](runtime.md) section.

## Recommendations

### Use an OS optimized for running containers
Consider using Flatcar Linux, Project Atomic, RancherOS, and [Bottlerocket](https://github.com/bottlerocket-os/bottlerocket/) (currently in preview), a special purpose OS from AWS designed for running Linux containers.  It includes a reduced attack surface, a disk image that is verified on boot, and enforced permission boundaries using SELinux.

### Treat your infrastructure as immutable and automate the replacement of your worker nodes
Rather than performing in-place upgrades, replace your workers when a new patch or update becomes available. This can be approached a couple of ways. You can either add instances to an existing autoscaling group using the latest AMI as you sequentially cordon and drain nodes until all of the nodes in the group have been replaced with the latest AMI.  Alternatively, you can add instances to a new node group while you sequentially cordon and drain nodes from the old node group until all of the nodes have been replaced.  EKS [managed node groups](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) uses the second approach and will present an option to upgrade workers when a new AMI becomes available. `eksctl` also has a mechanism for creating node groups with the latest AMI and for gracefully cordoning and draining pods from nodes groups before the instances are terminated. If you decide to use a different method for replacing your worker nodes, it is strongly recommended that you automate the process to minimize human oversight as you will likely need to replace workers regularly as new updates/patches are released and when the control plane is upgraded.

With EKS Fargate, AWS will automatically update the underlying infrastructure as updates become available.  Oftentimes this can be done seamlessly, but there may be times when an update will cause your pod to be rescheduled.  Hence, we recommend that you create deployments with multiple replicas when running your application as a Fargate pod.

### Periodically run kube-bench to verify compliance with [CIS benchmarks for Kubernetes](https://www.cisecurity.org/benchmark/kubernetes/)
When running [kube-bench](https://github.com/aquasecurity/kube-bench) against an EKS cluster, follow these instructions from Aqua Security, https://github.com/aquasecurity/kube-bench#running-in-an-eks-cluster.

!!! caution
    False positives may appear in the report because of the way the EKS optimized AMI configures the kubelet.  The issue is currently being tracked on [GitHub](https://github.com/aquasecurity/kube-bench/issues/571).

### Minimize access to worker nodes
Instead of enabling SSH access, use [SSM Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html) when you need to remote into a host.  Unlike SSH keys which can be lost, copied, or shared, Session Manager allows you to control access to EC2 instances using IAM.  Moreover, it provides an audit trail and log of the commands that were run on the instance.

At present, you cannot use custom AMIs with Managed Node Groups or modify the EC2 launch template for managed workers.  This presents a "chicken and egg problem", i.e. how can you use the SSM agent to remotely access these instances without using SSH to install the SSM agent first? As a temporary stop-gap you can run a privileged [DaemonSet](https://github.com/jicowan/ssm-agent-daemonset) to run a shell script that installs the SSM agent.

!!! caution
    Since the DaemonSet is runs as a privileged pod, you should consider deleting it once the SSM agent is installed on your worker nodes. This workaround will no longer be necessary once Managed Node Groups adds support for custom AMIs and EC2 launch templates.

### Deploy workers onto private subnets
By deploying workers onto private subnets, you minimize their exposure to the Internet where attacks often originate.  Beginning April 22, 2020, the assignment of public IP addresses to nodes in a managed node groups will be controlled by the subnet they are deployed onto.  Prior to this, nodes in a Managed Node Group were automatically assigned a public IP. If you choose to deploy your worker nodes on to public subnets, implement restrictive AWS security group rules to limit their exposure.

### Run Amazon Inspector to assess hosts for exposure, vulnerabilities, and deviations from best practices
[Inspector](https://docs.aws.amazon.com/inspector/latest/userguide/inspector_introduction.html) requires the deployment of an agent that continually monitors activity on the instance while using a set of rules to assess alignment with best practices.

!!! tip
    At present, managed node groups do not allow you to supply user metadata or your own AMI.  If you want to run Inspector on managed workers, you will need to install the agent after the node has been bootstrapped.  The method described earlier for installing the SSM Agent onto managed nodes can be repurposed to install the Inspector agent. 

!!! attention
    Inspector cannot be run on the infrastructure used to run Fargate pods.

## Alternatives

### Run SELinux

!!! info
    Available on Red Hat Enterprise Linux (RHEL), CentOS, and CoreOS

SELinux provides an additional layer of security to keep containers isolated from each other and from the host. SELinux allows administrators to enforce mandatory access controls (MAC) for every user, application, process, and file.  Think of it as a backstop that restricts the operations that can be performed against to specific resources based on a set of labels.  On EKS, SELinux can be used to prevent containers from accessing each other's resources.

Container SELinux policies are defined in the [container-selinux](https://github.com/containers/container-selinux) package.  Docker CE requires this package (along with its dependencies) so that the processes and files created by Docker (or other container runtimes) run with limited system access. Containers leverage the `container_t` label which is an alias to `svirt_lxc_net_t`. These policies effectively prevent containers from accessing certain features of the host.

When you configure SELinux for Docker, Docker automatically labels workloads `container_t` as a type and gives each container a unique MCS level. This will isolate containers from one another. If you need looser restrictions, you can create your own profile in SElinux which grants a container permissions to specific areas of the file system.  This is similiar to PSPs in that you can create different profiles for different containers/pods.  For example, you can have a profile for general workloads with a set of restrictive controls and another for things that require privileged access.

SELinux for Containers has a set of options that can be configured to modify the default restrictions. The following SELinux Booleans can be enabled or disabled based on your needs:

| Boolean | Default | Description|
|---|:--:|---|
| `container_connect_any` | `off` | Allow containers to access privileged ports on the host. For example, if you have a container that needs to map ports to 443 or 80 on the host. |
| `container_manage_cgroup` | `off` | Allow containers to manage cgroup configuration. For example, a container running systemd will need this to be enabled. |
| `container_use_cephfs` | `off` | Allow containers to use a ceph file system. |

By default, containers are allowed to read/execute under `/usr` and read most content from `/etc`. The files under `/var/lib/docker` and `/var/lib/containers` have the label `container_var_lib_t`. To view a full list of default, labels see the [container.fc](https://github.com/containers/container-selinux/blob/master/container.fc) file.

```bash
docker container run -it \
  -v /var/lib/docker/image/overlay2/repositories.json:/host/repositories.json \
  centos:7 cat /host/repositories.json
# cat: /host/repositories.json: Permission denied

docker container run -it \
  -v /etc/passwd:/host/etc/passwd \
  centos:7 cat /host/etc/passwd
# cat: /host/etc/passwd: Permission denied
```

Files labeled with `container_file_t` are the only files that are writable by containers. If you want a volume mount to be writeable, you will needed to specify `:z` or `:Z` at the end.

- `:z` will re-label the files so that the container can read/write
- `:Z` will re-label the files so that **only** the container can read/write

```bash
ls -Z /var/lib/misc
# -rw-r--r--. root root system_u:object_r:var_lib_t:s0   postfix.aliasesdb-stamp

docker container run -it \
  -v /var/lib/misc:/host/var/lib/misc:z \
  centos:7 echo "Relabeled!"

ls -Z /var/lib/misc
#-rw-r--r--. root root system_u:object_r:container_file_t:s0 postfix.aliasesdb-stamp
```

```bash
docker container run -it \
  -v /var/log:/host/var/log:Z \
  fluentbit:latest
```

In Kubernetes, relabeling is slightly different. Rather than having Docker automatically relabel the files, you can specify a custom MCS label to run the pod. Volumes that support relabeling will automatically be relabeled so that they are accessible. Pods with a matching MCS label will be able to access the volume. If you need strict isolation, set a different MCS label for each pod.

```yaml
securityContext:
  seLinuxOptions:
    # Provide a unique MCS label per container
    # You can specify user, role, and type also
    # enforcement based on type and level (svert)
    level: s0:c144:c154
```

In this example `s0:c144:c154` corresponds to an MCS label assigned to a file that the container is allowed to access.

On EKS you could create policies that allow for privileged containers to run, like FluentD and create an SELinux policy to allow it to read from /var/log on the host without needing to relabel the host directory. Pods with the same label will be able to access the same host volumes.

We have implemented [sample AMIs for Amazon EKS](https://github.com/aws-samples/amazon-eks-custom-amis) that have SELinux configured on CentOS 7 and RHEL 7. These AMIs were developed to demonstrate sample implementations that meet requirements of highly regulated customers, such as STIG, CJIS, and C2S.

!!! caution
    SELinux will ignore containers where the type is unconfined.

#### Additional resources
+ [SELinux Kubernetes RBAC and Shipping Security Policies for On-prem Applications](https://platform9.com/blog/selinux-kubernetes-rbac-and-shipping-security-policies-for-on-prem-applications/)
+ [Iterative Hardening of Kubernetes](https://jayunit100.blogspot.com/2019/07/iterative-hardening-of-kubernetes-and.html)
+ [Audit2Allow](https://linux.die.net/man/1/audit2allow)
+ [SEAlert](https://linux.die.net/man/8/sealert)
+ [Generate SELinux policies for containers with Udica](https://www.redhat.com/en/blog/generate-selinux-policies-containers-with-udica) describes a tool that looks at container spec files for Linux capabilities, ports, and mount points, and generates a set of SELinux rules that allow the container to run properly
+ [AMI Hardening](https://github.com/aws-samples/amazon-eks-custom-amis#hardening) playbooks for hardening the OS to meet different regulatory requirements

## Tools
+ [Keiko](https://github.com/keikoproj/keiko)
+ [Sysdig Secure](https://sysdig.com/products/kubernetes-security/)
+ [eksctl](https://eksctl.io/)
