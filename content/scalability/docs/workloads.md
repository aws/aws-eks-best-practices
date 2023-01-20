# Workloads

Workloads have an impact on how large your cluster can scale. Workloads that use the Kubernetes APIs heavily will limit the total amount of workloads you can have in a single cluster, but there are some defaults you can change to help reduce the load.

Workloads in a Kubernetes cluster have access to features that integrate with the Kubernetes API (e.g. Secrets and ServiceAccounts), but these features are not always required and should be disabled if they’re not being used. Limiting workload access and dependence on the Kubernetes control plane will increase the number of workloads you can run in the cluster and improve the security of your clusters by removing unnecessary access to workloads and implementing least privilege practices. Please read the [security best practices](https://aws.github.io/aws-eks-best-practices/security/docs/) for more information.

## Use IPv6 for pod networking

You cannot transition a VPC from IPv4 to IPv6 so enabling IPv6 before provisioning a cluster is important. If you enable IPv6 in a VPC it does not mean you have to use it and if your pods and services use IPv6 you can still route traffic to and from IPv4 addresses. Please see the [EKS networking best practices](https://aws.github.io/aws-eks-best-practices/networking/index/) for more information.

Using [IPv6 in your cluster](https://docs.aws.amazon.com/eks/latest/userguide/cni-ipv6.html) avoids some of the most common cluster and workload scaling limits. IPv6 avoids IP address exhaustion where pods and nodes cannot be created because no IP address is available. It also has per node performance improvements because pods receive IP addresses faster by reducing the number of ENI attachments per node. You can achieve similar node performance by using [IPv4 prefix mode in the VPC CNI](https://aws.github.io/aws-eks-best-practices/networking/prefix-mode/), but you still need to make sure you have enough IP addresses available in the VPC.

## Limit number of services per namespace

The number of IP tables rules that are created per node with kube-proxy grows with the total number of services in the cluster. Generating thousands of IP tables rules and routing packets through those rules have a performance impact on the nodes and add network latency.

Create Kubernetes namespaces that encompass a single application environment so long as the number of services per namespace is under 500. This will keep service discovery small enough to avoid service discovery limits and can also help you avoid service naming collisions. Applications environments (e.g. dev, test, prod) should use separate EKS clusters instead of namespaces.

## Understand Elastic Load Balancer Quotas

When creating your services consider what type of load balancing you will use (e.g. Network Load Balancer (NLB) or Application Load Balancer (ALB)). Each load balancer type provides different functionality and have [different quotas](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-limits.html). Some of the default quotas can be adjusted, but there are some quota maximums which cannot be changed. To view your account quotas and usage view the [Service Quotas dashboard](http://console.aws.amazon.com/servicequotas) in the AWS console.

For example, the default ALB targets is 1000. If you have a service with more than 1000 endpoints you will need to increase the quota or split the service across multiple ALBs or use Kubernetes Ingress. The default NLB targets is 3000, but is limited to 500 targets per AZ. If your cluster runs more than 500 pods for an NLB service you will need to use more AZs or request a quota increase.

Kubernetes ingress allows you to expose multiple Kubernetes services from a single load balancer by running a proxy inside your cluster. You can read more about ingress options in the [Kubernetes documentation](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/).

## Use EndpointSlices instead of Endpoints

When discovering pods that match a service label you should use [EndpointSlices](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/) instead of Endpoints. Endpoints were a simple way to expose services at small scales but large services that automatically scale or have updates causes a lot of traffic on the Kubernetes control plane. EndpointSlices have automatic grouping which enable things like topology aware hints.

Not all controllers use EndpointSlices by default. You should verify your controller settings and enable it if needed. For the [AWS Load Balancer Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.4/deploy/configurations/#controller-command-line-flags) you should enable the --enable-endpoint-slices optional flag to use EndpointSlices.

## Use immutable and external secrets if possible

The kubelet keeps a cache of the current keys and values for the Secrets that are used in volumes for pods on that node. The kubelet sets a watch on the Secrets to detect changes. As the cluster scales, the growing number of watches can negatively impact the API server performance.

There are two strategies to reduce the number of watches on Secrets:

* For applications that don’t need access to Kubernetes resources, you can disable auto-mounting service account secrets by setting automountServiceAccountToken: false
* If your application’s secrets are static and will not be modified in the future, mark the [Secret as Immutable](https://kubernetes.io/docs/concepts/configuration/secret/#secret-immutable). The kubelet does not need maintain a watch for immutable secrets.

To disable automatically mounting a service account to pods you can use the following setting in your workload. You can override these settings if specific workloads need a service account.

```
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app
automountServiceAccountToken: true
```

Monitor the number of secrets in the cluster before it exceeds the limit of 10,000. You can get a total count of secrets in a cluster with the following commend.

```
kubectl get secrets -A | wc -l
```

You should set up monitoring to alert a cluster admin before this limit is reached. Consider using external secrets management options such as [AWS Key Management Service (AWS KMS)](https://aws.amazon.com/kms/) or [Hashicorp Vault](https://www.vaultproject.io/).

## Limit Deployment history

Pods can be slow when creating, updating, or deleting because old objects are still tracked in the cluster. You can reduce `therevisionHistoryLimit` of [deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#clean-up-policy) to cleanup older ReplicaSets which will lower to total amount of objects tracked by the Kubernetes Controller Manager. The default history limit for Deployments in 10.

If your cluster creates a lot of job objects through CronJobs or other mechanisms you should use the ttlSecondsAfterFinished setting to automatically clean up old pods in the cluster.

## Disable enableServiceLinks by default

When a Pod runs on a Node, the kubelet adds a set of environment variables for each active Service. Linux processes have a maximum size for their environment which can fill up if you have too many services in your namespace. The number of services per namespace should not exceed 5,000. After this, the number of service environment variables outgrows shell limits, causing Pods to crash on startup. 

There are other reasons pods should not use service environment variables for service discovery. Environment variable name clashes, leaking service names, and total environment size are a few. You should use CoreDNS for discovering service endpoints.

## Limit dynamic admission webhooks per resource

[Dynamic Admission Webhooks](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/) include admission webhooks and mutating webhooks. They are API endpoints not part of the Kubernetes Control Plane that are called in sequence when a resource is sent to the Kubernetes API. Each webhook has a default timeout of 10 seconds and can increase the amount of time an API request takes if you have multiple webhooks or any of them timeout.

Make sure your webhooks are highly available—especially during an AZ incident—and the [failurePolicy](https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/#failure-policy) is set properly to reject the resource or ignore the failure. Do not call webhooks when not needed by allowing --dry-run kubectl commands to bypass the webhook.

```
apiVersion: admission.k8s.io/v1
kind: AdmissionReview
request:
  dryRun: False
```

Mutating webhooks can modify resources in frequent succession. If you have 5 mutating webhooks and deploy 50 resources etcd will store all versions of each resource until compaction runs—every 5 minutes—to remove old versions of modified resources. In this scenario when etcd removes superseded resources there will be 200 resource version removed from etcd and depending on the size of the resources may use considerable space on the etcd host until defragmentation runs every 15 minutes.

This defragmentation may cause pauses in etcd which could have other affects on the Kubernetes API and controllers. You should avoid frequent modification of large resources or modifying hundreds of resources in quick succession.
