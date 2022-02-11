# Tenant Isolation
When we think of multi-tenancy, we often want to isolate a user or application from other users or applications running on a shared infrastructure. 

Kubernetes is a _single tenant orchestrator_, i.e. a single instance of the control plane is shared among all the tenants  within a cluster. There are, however, various Kubernetes objects that you can use to create the semblance of multi-tenancy. For example, Namespaces and Role-based access controls (RBAC) can be implemented to logically isolate tenants from each other. Similarly, Quotas and Limit Ranges can be used to control the amount of cluster resources each tenant can consume. Nevertheless, the cluster is the only construct that provides a strong security boundary. This is because an attacker that manages to gain access to a host within the cluster can retrieve _all_ Secrets, ConfigMaps, and Volumes, mounted on that host. They could also impersonate the Kubelet which would allow them to manipulate the attributes of the node and/or move laterally within the cluster.

The following sections will explain how to implement tenant isolation while mitigating the risks of using a single tenant orchestrator like Kubernetes.

## Soft multi-tenancy

With soft multi-tenancy, you use native Kubernetes constructs, e.g. namespaces, roles and role bindings, and network policies, to create logical separation between tenants. RBAC, for example, can prevent tenants from accessing or manipulate each other's resources. Quotas and limit ranges control the amount of cluster resources each tenant can consume while network policies can help prevent applications deployed into different namespaces from communicating with each other.

None of these controls, however, prevent pods from different tenants from sharing a node. If stronger isolation is required, you can use a node selector, anti-affinity rules, and/or taints and tolerations to force pods from different tenants to be scheduled onto separate nodes; often referred to as _sole tenant nodes_. This could get rather complicated, and cost prohibitive, in an environment with many tenants. 

!!! attention
    Soft multi-tenancy implemented with Namespaces does not allow you to provide tenants with a filtered list of Namespaces because Namespaces are a globally scoped Type. If a tenant has the ability to view a particular Namespace, it can view all Namespaces within the cluster. 

!!! warning
    With soft-multi-tenancy, tenants retain the ability to query CoreDNS for all services that run within the cluster by default. An attacker could exploit this by running dig SRV *.*.svc.cluster.local from any pod in the cluster.  If you need to restrict access to DNS records of services that run within your clusters, consider using the Firewall or Policy plugins for CoreDNS. For additional information, see [https://github.com/coredns/policy#kubernetes-metadata-multi-tenancy-policy](https://github.com/coredns/policy#kubernetes-metadata-multi-tenancy-policy). 

[Kiosk](https://github.com/kiosk-sh/kiosk) is an open source project that can aid in the implementation of soft multi-tenancy.  It is implemented as a series of CRDs and controllers that provide the following capabilities: 

  + **Accounts & Account Users** to separate tenants in a shared Kubernetes cluster
  + **Self-Service Namespace Provisioning** for account users
  + **Account Limits** to ensure quality of service and fairness when sharing a cluster
  + **Namespace Templates** for secure tenant isolation and self-service namespace initialization
  
[Loft](https://loft.sh) is a commercial offering from the maintainers of Kiosk and [DevSpace](https://github.com/devspace-cloud/devspace) that adds the following capabilities:

  + **Mutli-cluster access** for granting access to spaces in different clusters 
  + **Sleep mode** scales down deployments in a space during periods of inactivity
  + **Single sign-on** with OIDC authentication providers like GitHub

There are three primary use cases that can be addressed by soft multi-tenancy.

### Enterprise Setting

The first is in an Enterprise setting where the "tenants" are semi-trusted in that they are employees, contractors, or are otherwise authorized by the organization. Each tenant will typically align to an administrative division such as a department or team. 

In this type of setting, a cluster administrator will usually be responsible for creating namespaces and managing policies. They may also implement a delegated administration model where certain individuals are given oversight of a namespace, allowing them to perform CRUD operations for non-policy related objects like deployments, services, pods, jobs, etc.

The isolation provided by a container runtime may be acceptable within this setting or it may need to be augmented with additional controls for pod security. It may also be necessary to restrict communication between services in different namespaces if stricter isolation is required.

### Kubernetes as a Service

By contrast, soft multi-tenancy can be used in settings where you want to offer Kubernetes as a service (KaaS). With KaaS, your application is hosted in a shared cluster along with a collection of controllers and CRDs that provide a set of PaaS services.  Tenants interact directly with the Kubernetes API server and are permitted to perform CRUD operations on non-policy objects. There is also an element of self-service in that tenants may be allowed to create and manage their own namespaces. In this type of environment, tenants are assumed to be running untrusted code.

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

### Sandboxed execution environments for containers

Sandboxing is a technique by which each container is run in its own isolated virtual machine. Technologies that perform pod sandboxing include [Firecracker](https://firecracker-microvm.github.io/) and Weave's [Firekube](https://www.weave.works/blog/firekube-fast-and-secure-kubernetes-clusters-using-weave-ignite).

If you are building your own self-managed Kubernetes cluster on AWS, you may be able to configure alternate container runtimes such as [Kata Containers](https://github.com/kata-containers/documentation/wiki/Initial-release-of-Kata-Containers-with-Firecracker-support).

For additional information about the effort to make Firecracker a supported runtime for EKS, see
[https://threadreaderapp.com/thread/1238496944684597248.html](https://threadreaderapp.com/thread/1238496944684597248.html). 

### Open Policy Agent (OPA) & Gatekeeper

[Gatekeeper](https://github.com/open-policy-agent/gatekeeper) is a Kubernetes admission controller that enforces policies created with [OPA](https://www.openpolicyagent.org/). With OPA you can create a policy that runs pods from tenants on separate instances or at a higher priority than other tenants. A collection of common OPA policies can be found in the GitHub [repository](https://github.com/aws/aws-eks-best-practices/tree/master/policies/opa) for this project. 

There is also an experimental [OPA plugin for CoreDNS](https://github.com/coredns/coredns-opa) that allows you to use OPA to filter/control the records returned by CoreDNS. 

### Kyverno

[Kyverno](https://kyverno.io) is a Kubernetes native policy engine that can validate, mutate, and generate configurations with policies as Kubernetes resources. Kyverno uses Kustomize-style overlays for validation, supports JSON Patch and strategic merge patch for mutation, and can clone resources across namespaces based on flexible triggers.

You can use Kyverno to isolate namespaces, enforce pod security and other best practices, and generate default configurations such as network policies.  Several examples are included in the GitHub [respository](https://github.com/aws/aws-eks-best-practices/tree/master/policies/kyverno) for this project.  

### Isolating tenant workloads to specific nodes

Restricting tenant workloads to run on specific nodes can be used to increase isolation in the soft multi-tenancy model. With this approach, tenant-specific workloads are only run on nodes provisioned for the respective tenants. To achieve this isolation, native Kubernetes properties (node affinity, and taints and tolerations) are used to target specific nodes for pod scheduling, and prevent pods, from other tenants, from being scheduled on the tenant-specific nodes.

#### Part 1 - Node affinity

Kubernetes [node affinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity) is used to target nodes for scheduling, based on node [labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/). With node affinity rules, the pods are attracted to specific nodes that match the selector terms. In the below pod specification, the `requiredDuringSchedulingIgnoredDuringExecution` node affinity is applied to the respective pod. The result is that the pod will target nodes that are labeled with the following key/value: `tenant: tenants-x`. 

``` yaml
...
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: tenant
            operator: In
            values:
            - tenants-x
...
```

With this node affinity, the label is required during scheduling, but not during execution; if the underlying nodes' labels change, the pods will not be evicted due solely to that label change. However, future scheduling could be impacted.

!!! Info
    Instead of node affinity, we could have used the [node selector](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#nodeselector). However, node affinity is more expressive and allows for more conditions to be considered during pod scheduling. For additional information about the differences and more advanced scheduling choices, please see this CNCF blog post on [Advanced Kubernetes pod to node scheduling](https://www.cncf.io/blog/2021/07/27/advanced-kubernetes-pod-to-node-scheduling/).

#### Part 2 - Taints and tolerations

Attracting pods to nodes is just the first part of this three-part approach. For this approach to work, we must repel pods from scheduling onto nodes for which the pods are not authorized. To repel unwanted or unauthorized pods, Kubernetes uses node [taints](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/). Taints are used to place conditions on nodes, to prevent pods from being scheduled. The below taint uses a key-value pair of `tenant: tenants-x`.

``` yaml
...
    taints:
      - key: tenant
        value: tenants-x
        effect: NoSchedule
...
```

Given the above node `taint`, only pods that _tolerate_ the taint will be allowed to be scheduled on the node. To allow authorized pods to be scheduled onto the node, the respective pod specifications must include a `toleration` to the taint, as seen below.

``` yaml
...
  tolerations:
  - effect: NoSchedule
    key: tenant
    operator: Equal
    value: tenants-x
...
```

Pods with the above `toleration` will not be stopped from scheduling on the node, at least not because of that specific taint. Taints are also used by Kubernetes to temporarily stop pod scheduling during certain conditions, like node resource pressure. With node affinity, and taints and tolerations, we can effectively attract the desired pods to specific nodes and repel unwanted pods.

!!! attention
    Certain Kubernetes pods are required to run on all nodes. Examples of these pods are those started by the [Container Network Interface (CNI)](https://github.com/containernetworking/cni) and [kube-proxy](https://kubernetes.io/docs/reference/command-line-tools-reference/kube-proxy/) [daemonsets](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/). To that end, the specifications for these pods contain very permissive tolerations, to tolerate different taints. Care should be taken to not change these tolerations. Changing these tolerations could result in incorrect cluster operation. Additionally, policy-management tools, such as [OPA/Gatekeeper](https://github.com/open-policy-agent/gatekeeper) and [Kyverno](https://kyverno.io/) can be used to write validating policies that prevent unauthorized pods from using these permissive tolerations.

#### Part 3 - Policy-based management for node selection

There are several tools that can be used to help manage the node affinity and tolerations of pod specifications, including enforcement of rules in CICD pipelines. However, enforcement of isolation should also be done at the Kubernetes cluster level. For this purpose, policy-management tools can be used to _mutate_ inbound Kubernetes API server requests, based on request payloads, to apply the respective node affinity rules and tolerations mentioned above.

For example, pods destined for the _tenants-x_ namespace can be _stamped_ with the correct node affinity and toleration to permit scheduling on the _tenants-x_ nodes. Utilizing policy-management tools configured using the Kubernetes [Mutating Admission Webhook](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#mutatingadmissionwebhook), policies can be used to mutate the inbound pod specifications. The mutations add the needed elements to allow desired scheduling. An example OPA/Gatekeeper policy that adds a node affinity is seen below.

``` yaml
apiVersion: mutations.gatekeeper.sh/v1alpha1
kind: Assign
metadata:
  name: mutator-add-nodeaffinity-pod
  annotations:
    aws-eks-best-practices/description: >-
      Adds Node affinity - https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#node-affinity
spec:
  applyTo:
  - groups: [""]
    kinds: ["Pod"]
    versions: ["v1"]
  match:
    namespaces: ["tenants-x"]
  location: "spec.affinity.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution.nodeSelectorTerms"
  parameters:
    assign:
      value: 
        - matchExpressions:
          - key: "tenant"
            operator: In
            values:
            - "tenants-x"
```

The above policy is applied to a Kubernetes API server request to be apply a pod to the _tenants-x_ namespace. This adds the `requiredDuringSchedulingIgnoredDuringExecution` node affinity rule, so that pods are attracted to nodes with the `tenant: tenants-x` label.

A second policy, seen below, adds the toleration to the same pod specification.

``` yaml
apiVersion: mutations.gatekeeper.sh/v1alpha1
kind: Assign
metadata:
  name: mutator-add-toleration-pod
  annotations:
    aws-eks-best-practices/description: >-
      Adds toleration - https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/
spec:
  applyTo:
  - groups: [""]
    kinds: ["Pod"]
    versions: ["v1"]
  match:
    namespaces: ["tenants-x"]
  location: "spec.tolerations"
  parameters:
    assign:
      value: 
      - key: "tenant"
        operator: "Equal"
        value: "tenants-x"
        effect: "NoSchedule"
```

The above policies are specific to pods; this is due to the paths to the mutated elements in the policies' _locations_ elements. Additional policies could be written to handle resources that create pods, like Deployment and Job resources. The listed policies and other examples can been seen in the companion [GitHub project](https://github.com/aws/aws-eks-best-practices/tree/master/policies/opa/gatekeeper/mutate/node-selection) for this guide.

The result of these two mutations is that pods are attracted to the desired node, while at the same time, not repelled by the specific node taint. To verify this, we can see the snippets of output from two `kubectl` calls to get the nodes labeled with `tenant=tenants-x`, and get the pods in the `tenants-x` namespace.

``` bash
kubectl get nodes -l tenant=tenants-x
NAME                                        
ip-10-0-11-255...
ip-10-0-28-81...
ip-10-0-43-107...

kubectl -n tenants-x get pods -owide
NAME                                  READY   STATUS    RESTARTS   AGE   IP            NODE
tenant-test-deploy-58b895ff87-2q7xw   1/1     Running   0          13s   10.0.42.143   ip-10-0-43-107...
tenant-test-deploy-58b895ff87-9b6hg   1/1     Running   0          13s   10.0.18.145   ip-10-0-28-81...
tenant-test-deploy-58b895ff87-nxvw5   1/1     Running   0          13s   10.0.30.117   ip-10-0-28-81...
tenant-test-deploy-58b895ff87-vw796   1/1     Running   0          13s   10.0.3.113    ip-10-0-11-255...
tenant-test-pod                       1/1     Running   0          13s   10.0.35.83    ip-10-0-43-107...
```

As we can see from the above outputs, all the pods are scheduled on the nodes labeled with `tenant=tenants-x`. Simply put, the pods will only run on the desired nodes, and the other pods (without the requisite affinity and tolerations) will not. The tenant workloads are effectively isolated.

An example mutated pod specification is seen below.

``` yaml
apiVersion: v1
kind: Pod
metadata:
  name: tenant-test-pod
  namespace: tenants-x
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: tenant
            operator: In
            values:
            - tenants-x
...
  tolerations:
  - effect: NoSchedule
    key: tenant
    operator: Equal
    value: tenants-x
...
```

!!! attention
    Policy-management tools that are integrated to the Kubernetes API server request flow, using mutating and validating admission webhooks, are designed to respond to the API server's request within a specified timeframe. This is usually 3 seconds or less. If the webhook call fails to return a response within the configured time, the mutation and/or validation of the inbound API sever request may or may not occur. This behavior is based on whether the admission webhook configurations are set to [Fail Open or Fail Close](https://open-policy-agent.github.io/gatekeeper/website/docs/#admission-webhook-fail-open-by-default).

In the above examples, we used policies written for OPA/Gatekeeper. However, there are other policy management tools that handle our node-selection use case as well. For example, this [Kyverno policy](https://kyverno.io/policies/other/add_node_affinity/add_node_affinity/) could be used to handle the node affinity mutation.

!!! tip
    If operating correctly, mutating policies will effect the desired changes to inbound API server request payloads. However, validating policies should be also included to verify that the desired changes occur, before changes are allowed to persist. This is especially important when using these policies for tenant-to-node isolation. It is also a good idea to include _Audit_ policies to routinely check your cluster for unwanted configurations.

### References

+ [k-rail](https://github.com/cruise-automation/k-rail) Designed to help you secure a multi-tenant environment through the enforcement of certain policies. 

+ [Security Practices for MultiTenant SaaS Applications using Amazon EKS](https://d1.awsstatic.com/whitepapers/security-practices-for-multi-tenant-saas-apps-using-eks.pdf)

## Hard multi-tenancy
Hard multi-tenancy can be implemented by provisioning separate clusters for each tenant.  While this provides very strong isolation between tenants, it has several drawbacks.

First, when you have many tenants, this approach can quickly become expensive. Not only will you have to pay for the control plane costs for each cluster, you will not be able to share compute resources between clusters.  This will eventually cause fragmentation where a subset of your clusters are underutilized while others are overutilized. 

Second, you will likely need to buy or build special tooling to manage all of these clusters.  In time, managing hundreds or thousands of clusters may simply become too unwieldy.

Finally, creating a cluster per tenant will be slow relative to a creating a namespace. Nevertheless, a hard-tenancy approach may be necessary in highly-regulated industries or in SaaS environments where strong isolation is required. 

## Future directions

The Kubernetes community has recognized the current shortcomings of soft multi-tenancy and the challenges with hard multi-tenancy. The [Multi-Tenancy Special Interest Group (SIG)](https://github.com/kubernetes-sigs/multi-tenancy) is attempting to address these shortcomings through several incubation projects, including Hierarchical Namespace Controller (HNC) and Virtual Cluster.

The HNC proposal (KEP) describes a way to create parent-child relationships between namespaces with \[policy\] object inheritance along with an ability for tenant administrators to create subnamespaces.

The Virtual Cluster proposal describes a mechanism for creating separate instances of the control plane services, including the API server, the controller manager, and scheduler, for each tenant within the cluster (also known as "Kubernetes on Kubernetes").

The [Multi-Tenancy Benchmarks](https://github.com/kubernetes-sigs/multi-tenancy/blob/master/benchmarks/README.md) proposal provides guidelines for sharing clusters using namespaces for isolation and segmentation, and a command line tool [kubectl-mtb](https://github.com/kubernetes-sigs/multi-tenancy/blob/master/benchmarks/kubectl-mtb/README.md) to validate conformance to the guidelines.

## Multi-cluster management resources

+ [Banzai Cloud](https://banzaicloud.com/)
+ [Kommander](https://d2iq.com/solutions/ksphere/kommander)
+ [Lens](https://github.com/lensapp/lens)
+ [Nirmata](https://nirmata.com)
+ [Rafay](https://rafay.co/)
+ [Rancher](https://rancher.com/products/rancher/)
+ [Weave Flux](https://www.weave.works/oss/flux/)
