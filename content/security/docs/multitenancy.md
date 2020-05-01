# Tenant Isolation

When we think of multi-tenancy, we often want to isolate a user or application
from other users or applications running on a shared infrastructure.

Kubernetes is a _single-tenant orchestrator_: there is an single instance of the
API server, controller manager, and scheduler for the whole cluster. However,
you can create the semblance of "tenants" by using various Kubernetes objects,
such as namespaces, RBAC and network policies, along with resource quotas or
limit ranges.

While these constructs will help to logically isolate tenants from each
other and control the amount of cluster resources each tenant can consume, the
cluster is still considered the security boundary.  For instance, if an attacker
manages to gain access to the underlying host, they could easily retrieve _all_
Secrets and ConfigMaps available as Volumes mounted on that host.  They could also
impersonate the Kubelet, which might give them the ability to move laterally
within the cluster or manipulate the attributes of the node.  The following
sections will explain how to implement tenant isolation while mitigating the
risks of using a single-tenant orchestrator like Kubernetes.

## Soft multi-tenancy

With soft multi-tenancy, you use native Kubernetes constructs --
namespaces, roles, role bindings, and network policies -- to create logical
isolation between tenants. Roles and bindings, which implement Kubernetes'
Role-Based Access Control (RBAC), help prevent tenants from accessing or
manipulate each other's resources.  Quotas and limit ranges control the amount
of cluster resources each tenant can consume while network policies can help
prevent applications deployed into different namespaces from communicating with
each other.

Consider, too, that pods from different tenants can share a node unless you take
action to prevent it.  If stronger isolation is required, you can use a node
selector, anti-affinity rules, and/or taints and tolerations to force pods from
different tenants to be scheduled onto separate nodes.  This strategy is
referred to as *sole-tenant nodes*. This could get rather complicated -- and
costly -- in an environment with many tenants.  Nor is it possible to provide
tenants with a filtered list of namespaces or create hierarchical namespaces,
because namespaces are scoped to the entire Kubernetes cluster.

[Kiosk](https://github.com/kiosk-sh/kiosk) is an open-source project that can
aid in the implementation of soft multi-tenancy.  It is implemented as a series
of CRDs and controllers that provide the following capabilities:

  + **Accounts & Account Users** to separate tenants in a shared Kubernetes
    cluster
  + **Self-Service Namespace Provisioning** for account users
  + **Account Limits** to ensure quality of service and fairness when sharing a
    cluster
  + **Namespace Templates** for secure tenant isolation and self-service
    namespace initialization

There are 3 primary use cases that can be addressed by soft multi-tenancy.

### Enterprise Setting

The first is in an enterprise setting, where the "tenants" are semi-trusted in
that they are employees, contractors, or are otherwise authorized by the
organization.  Each tenant will typically align to an administrative division
such as a department or a team.

In this scenario, a cluster administrator will usually be responsible for
creating namespaces and managing policies.  They may also implement a delegated
adminstration model where certain individuals are given partial oversight of a
namespace, allowing them to perform CRUD operations for non-policy related
objects like deployments, services, pods, jobs, etc.

The isolation provided by Docker may be acceptable within this setting, or it
may need to be augmented with additional controls such as Pod Security Policies
(PSPs). It may also be necessary to restrict communication between services in
different namespaces if stricter isolation is required.

### Kubernetes as a Service

By constrast, soft multi-tenancy can be used in settings where you want to offer
Kubernetes as a service (KaaS).  With KaaS, your application is hosted in a
shared cluster along with a collection of controllers and CRDs that provide a
set of PaaS services.  Tenants interact directly with the Kubernetes API server
and are permitted to perform CRUD operations on non-policy objects.  There is
also an element of self-service in that tenants may be allowed to create and
manage their own namespaces.  In this type of environment, tenants are assumed
to be running untrusted code.

In this scenario, you will need to implement strict network policies as well as
*pod sandboxing*.  Sandboxing is where you run the containers of a pod inside a
micro-VM like Firecracker or in a user-space kernel.  EKS offers sandboxed
pods via AWS Fargate.

### Software as a Service (SaaS)

The final use case for soft multi-tenancy is in a Software-as-a-Service (SaaS)
setting.  In this setting, each tenant is associated with a particular
_instance_ of an application.  Often, each instance has its own data and uses
seprate access controls.

Unlike the other use cases, the tenant in a SaaS setting does not directly
interface with the Kubernetes API.  Instead, users or application administrators
provision an instance of the application on the cluster.  The provisioning
application is responsible for instructing the Kubernetes API server to
provision an instance of the application. Once the application has been
provisioned, the tenant can then interact with it.

## Kubernetes Constructs

In each of these instances the following constructs are used to isolate tenants
from each other:

### Namespaces

Namespaces are fundamental to implementing multi-tenancy.  They allow you to
logically divide the cluster into logical partitions.  Quotas, network policies,
roles, role bindings, service accounts, and other objects needed to implement
multi-tenancy are scoped to a namespace.

### Network policies

By default, all pods in a Kubernetes cluster are allowed to communicate with
each other.  This can be changed using network policies.

Network policies restrict communication between pods using labels or IP address
ranges.  In a multi-tenant environment where strict network isolation between
tenants is required, we recommend starting with a default rule that denies
communication between pods, and another rule that allows all pods to query the
DNS server for name resolution.  With that in place, you can add rules that
allow all communication within a namespace.  This can be further refined as
required.

!!! attention Network policies are necessary but not sufficient. The enforcement
    of network policies requires a policy engine such as Calico or Cilium.

### Role-based access control (RBAC)

Roles and role bindings are the Kubernetes objects used to enforce role-based
access control (RBAC) in Kubernetes.  **Roles** contain lists of actions that
can be performed against objects in your cluster -- they are similar to AWS IAM
Policies.  **Role bindings** specify the individuals or groups to whom the roles
apply.  In the enterprise and KaaS use cases, RBAC can be used to permit
administration of objects by selected groups or individuals.

### Quotas

Quotas are used to define limits on workloads hosted in your cluster.  With
quotas, you can specify the maximum amount of CPU and memory that a pod can
consume, or you can limit the number of resources that can be allocated in a
cluster or namespace. **Limit ranges** allow you to declare minimum, maximum,
and default values for each limit.

Overcommitting resources in a shared cluster is often beneficial because it
allows you maximize your resources.  However, unbounded access to a cluster can
cause resource starvation, which can lead to performance degradation and loss of
application availability. If a pod's requests are set too low and the actual
resource utilization exceeds the capacity of the node, the node will begin to
experience CPU or memory pressure.  When this happens, pods may be restarted
and/or evicted from the node.

To prevent this from happening, you should plan to impose quotas on namespaces
in a multi-tenant environment to force tenants to specify requests and limits
when scheduling their pods on the cluster.  It will also mitigate a potential
denial of service by contraining the amount of resources a pod can consume.

You can also use quotas to apportion the cluster's resources to align with a
tenant's spend.  This is particularly useful in the KaaS scenario.

### Pod priority and pre-emption

Pod priority and pre-emption can be useful when you want to provide different
qualities of service (QoS) for different customers.  For example, you can
configure pods from customer A to run at a higher priority than customer B. When
there's insufficient capacity available, the Kubelet will forcibly terminate
Customer B's lower-priority pods to accommodate the higher-priority pods from
customer A.  This can be especially handy in a SaaS environment where customers
receive a higher quality of service in exchange for a premium.

## Mitigating controls

Your chief concern as an administrator of a multi-tenant environment is
preventing an attacker from gaining access to the underlying host. The following
controls should be considered to mitigate this risk:

### Pod Security Policies (PSPs)

Pod Security Policies (PSPs) should be used to curtail the actions that can be
performed by a container and to reduce a container's privileges, e.g. running as
a non-root user.

### Sandboxed execution environments for containers

If you are building your own self-managed Kubernetes cluster on AWS, you may be able to
configure alternate container runtimes such as [Kata
Containers](https://github.com/kata-containers/documentation/wiki/Initial-release-of-Kata-Containers-with-Firecracker-support).

Sandboxing is a technique by which each container is run in its own isolated
virtual machine.  Technologies that perform pod sandboxing include
[Firecracker](https://firecracker-microvm.github.io/) and Weave's
[Firekube](https://www.weave.works/blog/firekube-fast-and-secure-kubernetes-clusters-using-weave-ignite).
For additional information about the effort to make Firecracker a supported
runtime for EKS, See
https://threadreaderapp.com/thread/1238496944684597248.html.

### Open Policy Agent (OPA) and Gatekeeper

[Gatekeeper](https://github.com/open-policy-agent/gatekeeper) is a Kubernetes
admission controller that enforces policies created with [Open Policy
Agent](https://www.openpolicyagent.org/), or OPA. With OPA, you can create a
policy that specified pods from different tenants be run on separate instances
or at different priorities.

## Hard multi-tenancy

Hard multi-tenancy can be implemented by provisioning separate clusters for each
tenant.  While this provides very strong isolation between tenants, it can have
several drawbacks.

First, when you have many tenants, this approach can be costly. You will have to
pay for the control plane costs for each cluster, and you will not be able to
share compute resources between clusters.

Next, hard multi-tenancy may also lead to inefficiencies and lack of availability.
This can occur when clusters are overutilized, leading to resource contention
and performance degradation, and others are underutilized, leading to excessive
resource costs.

Managing hundreds or thousands of clusters may also pose a significant
management challenge. To cope with this challenge, you may need to build
or purchase special tooling to manage those clusters.

Finally, creating a cluster per tenant will be slow relative to a creating a
namespace.

Nevertheless, a hard-tenancy approach may be necessary in highly-regulated
industries or in SaaS environments where strong isolation is required.

## Future directions

The Kubernetes community has recognized the current shortcomings of soft
multi-tenancy and the challenges with hard multi-tenancy. The [Multi-Tenancy
Special Interest Group (SIG)](https://github.com/kubernetes-sigs/multi-tenancy)
is attempting to address these shortcomings through several incubation projects,
including Hierarchical Namespace Controller (HNC) and Virtual Cluster.

The HNC proposal (KEP) describes a way to create parent-child relationships
between namespaces with \[policy\] object inheritance along with an ability for
tenant administrators to create subnamespaces.

The Virtual Cluster proposal describes a mechanism for creating separate
instances of the control plane services, including the API server, the controller
manager, and scheduler, for each tenant within the cluster (also known as
"Kubernetes on Kubernetes").

## Multi-cluster management resources

+ [Rancher](https://rancher.com/products/rancher/)
+ [Kommander](https://d2iq.com/solutions/ksphere/kommander)
+ [Weave Flux](https://www.weave.works/oss/flux/)
+ [Banzai Cloud](https://banzaicloud.com/)
+ [Rafay](https://rafay.co/)
+ [Lens](https://github.com/lensapp/lens)
