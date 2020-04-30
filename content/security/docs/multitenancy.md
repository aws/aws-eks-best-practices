# Tenant Isolation

When we think of multi-tenancy, we often want to isolate a user or application
from other users or applications running on a shared infrastructure. Kuberntes
is a single tenant orchestrator in that there is an single instance of the API
server, controller manager, and scheduler for the whole cluster. You can create
the semblance of "tenants" by using various Kubernetes objects, such as
namespaces, RBAC and network policies, along with resource quotas or limit
ranges.  While these constructs will help to logically isolate tenants from each
other and control the amount of cluster resources each tenant can consume, the
cluster is still consider the security boundary.  For instance, if an attacker
manages to gain access to the underlying host, they could easily retrieve _all_
Secrets, ConfigMaps, and Volumes, mounted on that host.  They could also
impersonate the Kubelet which might give them the ability to move laterally
within the cluster or manipulate the attributes of the node.  The following
sections will explain how to implement tenant isolation while mitigating the
risks of using a single tenant orchestrator like Kubernetes.

## Soft multi-tenancy

With soft multi-tenancy, you use native Kubernetes constructs like namespaces,
RBAC, and network policies to create logical isolation between tenants.  RBAC
roles and bindings help prevent tenants from accessing or manipulate each
other's resources.  Quotas and limit ranges control the amount of cluster
resources each tenant can consume while network policies can help prevent
applications deployed into different namespaces from communicating with each
other.  None of this, however, prevents pods from different tenants from sharing
a node.  If stronger isolation is required, you can use a node selector,
anti-affinity rules, and/or taints and tolerations to force pods from different
tenants to be scheduled onto separate nodes, often referred to as sole tenant
nodes. This could get rather complicated, and costly, in an environment with
lots of tenants.  Additionally, soft multi-tenancy implemented solely with
native Kubernetes objects doesn't give you the flexibility to provide tenants
with a filtered list of namespaces or create hierarchical namespaces because
namespaces are a globaly scoped Type.

[Kiosk](https://github.com/kiosk-sh/kiosk) is an open source project that can
aid in the implementation of soft multi-tenancy.  It is implemented as a series
of CRDs and controllers that provide the following capabilities:

  + **Accounts & Account Users** to separate tenants in a shared Kubernetes
    cluster
  + **Self-Service Namespace Provisioning** for account users
  + **Account Limits** to ensure quality of service and fairness when sharing a
    cluster
  + **Namespace Templates** for secure tenant isolation and self-service
    namespace initialization

The Kubernetes community has recognized the current shortcomings of soft
multi-tenancy and the challenges with hard multi-tenancy.
[SIG-Multitenancy](https://github.com/kubernetes-sigs/multi-tenancy) is
attempting to address them with several incubation projects, including:
hierarchical namespace controller (HNC) and virtual cluster. The HNC proposal
(KEP) describes a way to create parent-child relationships between namespaces
with \[policy\] object inheritance along with an ability for tenant
administrators to create subnamespaces. Virtual Cluster proposal describes a
mechanism for creating separate instances of the control plane services, e.g.
the api server, the controller manager, and scheduler, for each tenant within
the cluster (kubernetes on kubernetes).

There are 3 primary use cases that can be addressed by soft multi-tenancy.  The
first is in an Enterprise setting where the "tenants" are semi-trusted in that
they are employees of the organization.  Each tenant will typically align to a
department or team. A cluster administrator will usually be responsible for
creating namespaces, managing policies like quotas, and/or implementing a
delegated adminstration model where certain individuals are given partial
oversight of a namespace, i.e. CRUD operations for non-policy related objects
like pods, jobs, etc. The isolation provided by Docker may be acceptable within
this setting or it may need to be augmented with additional controls such as Pod
Security Policies (PSPs). It may also be necessary to restrict communication
between services in different namespaces if stricter isolation is required.

By constrast, soft multi-tenancy can be used in settings where you want to offer
Kubernetes as a service (KaaS).  With KaaS, your application is hosted in a
shared cluster along with a collection of controllers and CRDs that provide a
set of PaaS services.  Tenants interact directly with the Kubernetes API server
and are permitted to perform CRUD operations on non policy objects.  There is
also an element of self-service in that tenants may be allowed to create and
manage their own namespaces.  In this type of environment, tenants are assumed
to be running untrusted code.  As such, you'll need to implement strict network
policies as well as pod sandboxing.  Sandboxing is where you run the containers
of a pod inside a micro VM like Firecracker or in a user-space kernel.  Outside
of Fargate, EKS doesn't support this type of configuration.

The final use case for soft multi-tenancy is in a SaaS setting where you're
deploying an instance of an application into a namespace for each tenant.
Unlike the other use cases, the tenant does not directly interface with the
Kubernetes API.  Instead, users go through a proxy to get provision an instance
of the application on the cluster.  The proxy is responsible for sending the
necessary commands to the  Kubernetes API server to create a new namespace and
provision a instance of the application in that namespace.  Once the application
has been provision, the tenant interacts with directly with the application.

In each of these instances the following constructs are used to isolate tenants
from each other:

### Namespaces

Namespaces are fundamental to implementing multi-tenancy.  They allow you to
logical divide the cluster into logical partitions.  Moreover, quotas, network
policies, service accounts, and other objects needed to implement multi-tenancy
are scoped to a namespace.

### Network policies

Network policies restrict communication between pods using labels or ip address
ranges.  In a multi-tenant environment where strict network isolation between
tenants is required, we recommend starting with a deny rule that prevents
applications between pods, another rule that allows all pods to query CoreDNS
for name resolution.  With that in place, you can begin layering additional
rules that allows all communication within a namespace.  This can be further
refined as required.  By default, all pods in all namespaces are allowed to
communicate with each other.

!!! attention Network policies are necessary but not sufficient. The enforcement
    of network policies requires a policy engine like Calico or Cilium.

### RBAC

RBAC roles and bindings are the mechanism used to restrict the actions that can
be performed againsts objects in different namespaces.  In the enterprise and
KaaS use cases, RBAC can be used to delegate administration of namespaced
objects to select groups of individuals.

### Quotas

Quotas specify the maximum amount of CPU and memory and/or number of resoures,
e.g. pods, for a namespace whereas **limit ranges** allow you to set default
along with min/max for requets and limits.  The scheduler uses the aggregate
requests for all the containers in a pod to determine which nodes it can
schedule the pod onto.  Limits specify the maximum amount of CPU or memory that
a container can consume from the node.  If the requests are set too low and the
actual resource utilization exceeds the capacity of the node, the node will
begin to experience CPU or memory pressure.  When this happens pods may be
restarted and/or evicted from the node.  Overcommitting resources in a shared
cluster is usually beneficial because it allows you maximize your resources.
Nevertheless, you should plan to impose quotas on namespaces in a multi-tenant
environment as this will force tenants to specify requests and limits when
scheduling their pods on the cluster.  It will also mitigate occurrances DoS by
contraining the amount of resources a pod can consume.  Lastly, you can use
quotas to apportion the cluster's resources to align with a tenant's spend.

### Pod priority and pre-emption

Pod priority and pre-emption can be useful when you want to provide different
qualties of services for different customers.  For example, with pod priority
you can configure pods from customer A to run at a higher priority than customer
B. When there's insufficient capacity available, the Kubelet will kill the low
priority pods from customer B to accommodate the high priority pods from
customer A.  This can be especially handy in a SaaS environment where customers
willing to pay a premium receive a higher quality of service.

## Mitigating controls

Your chief concern as an administrator of a multi-tenant environment is
preventing an attacker from gaining access to the underlying host. The following
controls should be considered to mitigate the risk of this happening:

### Pod Security Policies (PSPs)

PSPs should be used to curtail the actions that can be performed by a container
and to reduce a container's privileges, e.g. running as a non-root user.

### Sandboxed execution environments for containers

Not applicable to EKS, but useful in self-managed environments where you can
configure alterate runtimes, e.g. [Kata
Containers](https://github.com/kata-containers/documentation/wiki/Initial-release-of-Kata-Containers-with-Firecracker-support).
Sandboxing is where you run a pod's containers within a micro VM like
[Firecracker](https://firecracker-microvm.github.io/) as in Weave's
[Firekube](https://www.weave.works/blog/firekube-fast-and-secure-kubernetes-clusters-using-weave-ignite).
For additional information about the effort to make Firecracker a supported
runtime for EKS, See
https://threadreaderapp.com/thread/1238496944684597248.html.

### Open Policy Agent (OPA) & Gatekeeper

[Gatekeeper](https://github.com/open-policy-agent/gatekeeper) is a Kubernetes
admission controller that enforces policies created with
[OPA](https://www.openpolicyagent.org/). With OPA you can create a policy that
runs pods from tenants on separate instances or at a higher priority than other
tenants.

## Hard multi-tenancy

Hard multi-tenancy can be implemented by provisioning separate clusters for each
tenant.  While this provides very strong isolation between tenants, it has
several drawbacks.  First, when you have lots of tenants, this approach can
quickly become prohibitively expensive. Not only will you have to pay for the
control plane costs for each cluster, you will not be able to share compute
resources between clusters.  This will eventually cause fragmentation where
subset of clusters are underutilized while others may be overutilized. Second,
you will likely need to buy or build special tooling to manage all of these
clusters.  In time, managing hundreds or thousands of clusters may simply become
too unweildy.  Finally, creating a cluster per tenant will be slow relative to a
creating a namespace. For a majority of cluster, the cluster per tenant model is
not really practical or cost effective, yet it may be necessary in highly
regulated industries or in SaaS environments where strong isolation is required.


## Multi-cluster management resources

+ [Rancher](https://rancher.com/products/rancher/)
+ [Kommander](https://d2iq.com/solutions/ksphere/kommander)
+ [Weave Flux](https://www.weave.works/oss/flux/)
+ [Banzai Cloud](https://banzaicloud.com/)
+ [Rafay](https://rafay.co/)
+ [Lens](https://github.com/lensapp/lens)
