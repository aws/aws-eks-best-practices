# Protecting the infrastructure (hosts)

+ **Run SELinux**. SELinux provides an additional layer of security to keep containers isolated from each other and from the host. SELinux allows administrators to enforce mandatory access controls (MAC) for every user, application, process, and file.
Use a OS optimized for running containers, e.g. Flatcar Linux, Project Atomic, RancherOS, and [Bottlerocket](https://github.com/bottlerocket-os/bottlerocket/), a new OS from AWS that has a read only root file system and uses partition flips for fast and reliable system updates.  A majority of these operating systems, like Bottlerocket, have been substantially paired down and optimized to run containers. 

**Additional resources**

  + https://platform9.com/blog/selinux-kubernetes-rbac-and-shipping-security-policies-for-on-prem-applications/
  + https://jayunit100.blogspot.com/2019/07/iterative-hardening-of-kubernetes-and.html 

+ **Treat your infrastructure as immutable**.  Rather than performing in-place upgrades, replace your workers when a new patch or update becomes available. This can be approached a couple of ways. You can either add instances to an existing autoscaling group using the latest AMI as you sequentially cordon and drain nodes until all of the nodes in the group have been replaced with the latest AMI.  Alternatively, you can add instances to a new node group while you sequentally cordon and drain nodes from the old node group until all of the nodes have been replaced.  EKS [managed node groups](https://docs.aws.amazon.com/eks/latest/userguide/managed-node-groups.html) utilizes the second approach and will present an option to upgrade workers when a new AMI becomes available. `eksctl` also has a mechanism for creating node groups with the latest AMI and for gracefully cordoning and draining pods from nodes groups before the instances are terminated. If you decide to use a different method for replacing your worker nodes, it is recommended that you automate the process to minimize human oversight as you will likely need to replace workers regularly as new updates/patches are released and when the control plane is upgraded. 
With EKS Fargate, AWS will automatically update the underlying infrastructure as updates become available.  Oftentimes this can be done seamlessly, but there may be times when an update will cause your task to be rescheduled.  Hence, we recommend that you create deployments with multiple replicas when running your application as a Fargate pod. 

+ **Periodically run [kube-bench](https://github.com/aquasecurity/kube-bench) to verify compliance with [CIS benchmarks for Kubernetes](https://www.cisecurity.org/benchmark/kubernetes/)**. When running kube-bench against an EKS cluster, follow these instructions, https://github.com/aquasecurity/kube-bench#running-in-an-eks-cluster. Be aware that false positives may appear in the report because of the way the he EKS optimized AMI configures the kubelet.  See https://github.com/aquasecurity/kube-bench/issues/571 for further information. 

+ **Minimize access to worker nodes**. Instead of enabling SSH access, use [SSM Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html) when you need to remote into a host.  Unlike SSH keys which can be lost, copied, or shared, Session Manager allows you to control access to EC2 instances using IAM.  Moreover, it provides an audit trail and log of the commands that were run on the instance.  If you've lost access to the host through SSH or Session Manager, you can try running a node-shell, a privileged pod that gives you shell access on the node. An example appears below: 

```yaml
kind: Pod
apiVersion: v1
metadata:
  name: node-shell
  namespace: kube-system
  annotations:
    kubernetes.io/psp: eks.privileged
spec:
  containers:
    - name: shell
      image: 'docker.io/alpine:3.9'
      command:
        - nsenter
      args:
        - '-t'
        - '1'
        - '-m'
        - '-u'
        - '-i'
        - '-n'
        - sleep
        - '14000'
      securityContext:
        privileged: true
  restartPolicy: Never
  nodeSelector:
    kubernetes.io/hostname: ip-192-168-49-62.us-west-2.compute.internal
  nodeName: ip-192-168-49-62.us-west-2.compute.internal
  hostNetwork: true
  hostPID: true
  hostIPC: true
  enableServiceLinks: true
```

+ **Deploy workers onto private subnets**. By deploying workers onto private subnets, you minimize their exposure to the Internet where attacks often originate.  At present, worker nodes that are part of a managed node group are are automatically assigned a public IP. If you plan to use managed node groups use AWS security groups to restrict or deny inbound access from the Internet (0.0.0.0/0). Risk to workers that are deployed onto public subnets can also be mitigated by implementing restrictive security group rules. 

+ **Run [Amazon Inspector](https://docs.aws.amazon.com/inspector/latest/userguide/inspector_introduction.html) to assesses applications for exposure, vulnerabilities, and deviations from best practices**.  It requires the deployment of an agent that continually monitors activity on the instance while using set of rules to assess alignment with best practices. 
  At present, managed node groups do not allow you to supply user metadata or your own AMI.  If you want to run Inspector on managed workers, you will need to install the agent after the node has been bootstrapped.  
  Inspector cannot be run on the infrastructure used to run Fargate pods. 

**Alternatives**

+ [Sysdig Secure](https://sysdig.com/products/kubernetes-security/)

### Tools
+ [Keiko](https://github.com/keikoproj/keiko)