# Tenant Isolation
When we think of multi-tenancy, we often want to isolate a user or application from other users or applications running on a shared infrastructure. 

Kuberntes is a _single tenant orchestrator_, i.e. a single instance of the control plane is shared among all the tenants  within a cluster. There are, however, various Kubernetes objects that you can use to create the semblance of multi-tenancy. For example, Namespaces and Role-based access controls (RBAC) can be implemented to logically isolate tenants from each other. Similarly, Quotas and Limit Ranges can be used to control the amount of cluster resources each tenant can consume. Nevertheless, the cluster is the only construct that provides a strong security boundary. This is because an attacker that manages to gain access to a host within the cluster can retrieve _all_ Secrets, ConfigMaps, and Volumes, mounted on that host. They could also impersonate the Kubelet which would allow them to manipulate the attributes of the node and/or move laterally within the cluster.

The following sections will explain how to implement tenant isolation while mitigating the risks of using a single tenant orchestrator like Kubernetes.

## Soft multi-tenancy

With soft multi-tenancy, you use native Kubernetes constructs, e.g. namespaces, roles and role bindings, and network policies, to create logical separation between tenants. RBAC, for example, can prevent tenants from accessing or manipulate each other's resources. Quotas and limit ranges control the amount of cluster resources each tenant can consume while network policies can help prevent applications deployed into different namespaces from communicating with each other.

None of these controls, however, prevent pods from different tenants from sharing a node. If stronger isolation is required, you can use a node selector, anti-affinity rules, and/or taints and tolerations to force pods from different tenants to be scheduled onto separate nodes; often referred to as _sole tenant nodes_. This could get rather complicated, and cost prohibitive, in an environment with many tenants. 

!!! attention
    Soft multi-tenancy implemented with Namespaces does not allow you to provide tenants with a filtered list of Namespaces because Namespaces are a globaly scoped Type. If a tenant has the ability to view a particular Namespace, it can view all Namespaces within the cluster. 

!!! warning
    With soft-multi-tenancy, tenants retain the ability to query CoreDNS for all services that run within the cluster by default. If you need to restrict access to records, consider using the Firewall or Policy plugins for CoreDNS. For additional information, see https://github.com/coredns/policy#kubernetes-metadata-multi-tenancy-policy. 

[Kiosk](https://github.com/kiosk-sh/kiosk) is an open source project that can aid in the implementation of soft multi-tenancy.  It is implemented as a series of CRDs and controllers that provide the following capabilities: 

  + **Accounts & Account Users** to separate tenants in a shared Kubernetes cluster
  + **Self-Service Namespace Provisioning** for account users
  + **Account Limits** to ensure quality of service and fairness when sharing a cluster
  + **Namespace Templates** for secure tenant isolation and self-service namespace initialization
  
[Loft](https://loft.sh) is a commerical offering from the maintainers of Kiosk and [DevSpace](https://github.com/devspace-cloud/devspace) that adds the following capabilities: 

  + **Mutli-cluster access** for granting access to spaces in different clusters 
  + **Sleep mode** scales down deployments in a space during periods of inactivity
  + **Single sign-on** with OIDC authentication providers like GitHub

There are three primary use cases that can be addressed by soft multi-tenancy.

### Enterprise Setting

The first is in an Enterprise setting where the "tenants" are semi-trusted in that they are employees, contractors, or are otherwise authorized by the organization. Each tenant will typically align to an administrative division such as a department or team. 

In this type of setting, a cluster administrator will usually be responsible for creating namespaces and managing policies. They may also implement a delegated adminstration model where certain individuals are given oversight of a namespace, allowing them to perform CRUD operations for non-policy related objects like deployments, services, pods, jobs, etc. 

The isolation provided by Docker may be acceptable within this setting or it may need to be augmented with additional controls such as Pod Security Policies (PSPs). It may also be necessary to restrict communication between services in different namespaces if stricter isolation is required.

### Kubernetes as a Service

By constrast, soft multi-tenancy can be used in settings where you want to offer Kubernetes as a service (KaaS). With KaaS, your application is hosted in a shared cluster along with a collection of controllers and CRDs that provide a set of PaaS services.  Tenants interact directly with the Kubernetes API server and are permitted to perform CRUD operations on non-policy objects. There is also an element of self-service in that tenants may be allowed to create and manage their own namespaces. In this type of environment, tenants are assumed to be running untrusted code.

To isolate tenants in this type of environment, you will likely need to implement strict network policies as well as _pod sandboxing_. Sandboxing is where you run the containers of a pod inside a micro VM like Firecracker or in a user-space kernel.  Today, you can create sandboxed pods with EKS Fargate.

### Software as a Service (SaaS)

The final use case for soft multi-tenancy is in a Software-as-a-Service (SaaS) setting.  In this environment, each tenant is associated with a particular _instance_ of an application that's running within the cluster.  Each instance often has its own data and uses separate access controls that are usually independent of Kubernetes RBAC.

Unlike the other use cases, the tenant in a SaaS setting does not directly interface with the Kubernetes API.  Instead, the SaaS application is responsible for interfacing with the Kubernetes API to create the necessary objects to support each tenant.

## Kubernetes Constructs

In each of these instances the following constructs are used to isolate tenants from each other: 

### Namespaces

Namespaces are fundamental to implementing soft multi-tenancy. They allow you to divide the cluster into logical partitions. Quotas, network policies, service accounts, and other objects needed to implement multi-tenancy are scoped to a namespace.

### Network policies

By default, all pods in a Kubernetes cluster are allowed to communicate with each other. This behavior can be altered using network policies.

Network policies restrict communication between pods using labels or IP address ranges. In a multi-tenant environment where strict network isolation between tenants is required, we recommend starting with a default rule that denies communication between pods, and another rule that allows all pods to query the DNS server for name resolution. With that in place, you can begin adding more permissive rules that allow for communication within a namespace. This can be further refined as required. 

!!! attention 
    Network policies are necessary but not sufficient. The enforcement of network policies requires a policy engine such as Calico or Cilium.

### Role-based access control (RBAC)

Roles and role bindings are the Kubernetes objects used to enforce role-based access control (RBAC) in Kubernetes. **Roles** contain lists of actions that can be performed against objects in your cluster. **Role bindings** specify the individuals or groups to whom the roles apply.  In the enterprise and KaaS settings, RBAC can be used to permit administration of objects by selected groups or individuals.

### Quotas

Quotas are used to define limits on workloads hosted in your cluster. With quotas, you can specify the maximum amount of CPU and memory that a pod can consume, or you can limit the number of resources that can be allocated in a cluster or namespace. **Limit ranges** allow you to declare minimum, maximum, and default values for each limit.

Overcommitting resources in a shared cluster is often beneficial because it allows you maximize your resources.  However, unbounded access to a cluster can cause resource starvation, which can lead to performance degradation and loss of application availability. If a pod's requests are set too low and the actual resource utilization exceeds the capacity of the node, the node will begin to experience CPU or memory pressure.  When this happens, pods may be restarted and/or evicted from the node.

To prevent this from happening, you should plan to impose quotas on namespaces in a multi-tenant environment to force tenants to specify requests and limits when scheduling their pods on the cluster.  It will also mitigate a potential denial of service by constraining the amount of resources a pod can consume.

You can also use quotas to apportion the cluster's resources to align with a tenant's spend.  This is particularly useful in the KaaS scenario.

### Pod priority and pre-emption

Pod priority and pre-emption can be useful when you want to provide different qualities of services (QoS) for different customers.  For example, with pod priority you can configure pods from customer A to run at a higher priority than customer B. When there's insufficient capacity available, the Kubelet will evict the lower-priority pods from customer B to accommodate the higher-priority pods from customer A.  This can be especially handy in a SaaS environment where customers willing to pay a premium receive a higher quality of service.

## Mitigating controls

Your chief concern as an administrator of a multi-tenant environment is preventing an attacker from gaining access to the underlying host. The following controls should be considered to mitigate this risk: 

### Pod Security Policies (PSPs)

PSPs should be used to curtail the actions that can be performed by a container and to reduce a container's privileges, e.g. running as a non-root user.

### Sandboxed execution environments for containers

Sandboxing is a technique by which each container is run in its own isolated virtual machine. Technologies that perform pod sandboxing include [Firecracker](https://firecracker-microvm.github.io/) and Weave's [Firekube](https://www.weave.works/blog/firekube-fast-and-secure-kubernetes-clusters-using-weave-ignite).

If you are building your own self-managed Kubernetes cluster on AWS, you may be able to configure alternate container runtimes such as [Kata Containers](https://github.com/kata-containers/documentation/wiki/Initial-release-of-Kata-Containers-with-Firecracker-support).

For additional information about the effort to make Firecracker a supported runtime for EKS, see
https://threadreaderapp.com/thread/1238496944684597248.html. 

### Open Policy Agent (OPA) & Gatekeeper

[Gatekeeper](https://github.com/open-policy-agent/gatekeeper) is a Kubernetes admission controller that enforces policies created with [OPA](https://www.openpolicyagent.org/). With OPA you can create a policy that runs pods from tenants on separate instances or at a higher priority than other tenants. 

There is also an experimental [OPA plugin for CoreDNS](https://github.com/coredns/coredns-opa) that allows you to use OPA to filter/control the records returned by CoreDNS. 

## Hard multi-tenancy
Hard multi-tenancy can be implemented by provisioning separate clusters for each tenant.  While this provides very strong isolation between tenants, it has several drawbacks.  

First, when you have many tenants, this approach can quickly become expensive. Not only will you have to pay for the control plane costs for each cluster, you will not be able to share compute resources between clusters.  This will eventually cause fragmentation where a subset of your clusters are underutilized while others are overutilized. 

Second, you will likely need to buy or build special tooling to manage all of these clusters.  In time, managing hundreds or thousands of clusters may simply become too unweildy.  

Finally, creating a cluster per tenant will be slow relative to a creating a namespace. Nevertheless, a hard-tenancy approach may be necessary in highly-regulated industries or in SaaS environments where strong isolation is required. 

## Future directions

The Kubernetes community has recognized the current shortcomings of soft multi-tenancy and the challenges with hard multi-tenancy. The [Multi-Tenancy Special Interest Group (SIG)](https://github.com/kubernetes-sigs/multi-tenancy) is attempting to address these shortcomings through several incubation projects, including Hierarchical Namespace Controller (HNC) and Virtual Cluster.

The HNC proposal (KEP) describes a way to create parent-child relationships between namespaces with \[policy\] object inheritance along with an ability for tenant administrators to create subnamespaces.

The Virtual Cluster proposal describes a mechanism for creating separate instances of the control plane services, including the API server, the controller manager, and scheduler, for each tenant within the cluster (also known as "Kubernetes on Kubernetes").

## Multi-cluster management resources
+ [Rancher](https://rancher.com/products/rancher/)
+ [Kommander](https://d2iq.com/solutions/ksphere/kommander)
+ [Weave Flux](https://www.weave.works/oss/flux/)
+ [Banzai Cloud](https://banzaicloud.com/)
+ [Rafay](https://rafay.co/)
+ [Lens](https://github.com/lensapp/lens)
