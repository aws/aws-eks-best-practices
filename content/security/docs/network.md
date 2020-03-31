# Network security
Network security has a couple of different facets.  The first involves the application of rules that restrict the flow of network traffic between services.  The second involves the encryption of traffic while it is on the wire.  The mechanisms to implement these security measures on EKS are varied but often include the following items:

+ Network Policies
+ Security Groups
+ Encryption in transit
  + Service Mesh
  + Container Network Interfaces (CNIs)
  + Nitro Instances

## Network policy
Within a Kubernetes cluster, all pod to pod communication is allowed by default.  While this may help promote experimentation, it is not considered secure.  Kubernetes network policies give you a mechanism to restrict network traffic between pods or pods and external services.  The de facto policy engine for EKS is [Calico](https://docs.projectcalico.org/introduction/), an open source project from Tigera.  Network policies operate at layers 3 and 4 of the OSI model.  Rules can comprise of a src/dst address or port/protocol or a combination of both. Isovalent, the maintainers of [Cilium](https://cilium.readthedocs.io/en/stable/intro/), have extended the network policies to include partial support for layer 7 rules, e.g. HTTP.  Cilium also has support for DNS hostnames which can be useful for restricting traffic between Kubernetes services/pods and resources that run within or outside of your VPC. By contrast, Tigera Enterprise includes a feature that allows you to map a Kubernetes network policy to an AWS security group. 

  > When you first provision an EKS cluster, the Calico policy engine is not installed by default. The manifests for installing Calico can be found at https://github.com/aws/amazon-vpc-cni-k8s/tree/master/config.

Calico policies can be scoped to namespaces, pods, service accounts, or globally.  When policies are scoped to a service account, it associates a set of ingress/egress rules with that service account.  With the proper RBAC rules in place, you can prevent teams from overriding these rules, allowing IT security professionals to safely delegate administration of namespaces.

You can find a list of common Kubernetes network policies at https://github.com/ahmetb/kubernetes-network-policy-recipes.  A similar set of rules for Calico are available at https://docs.projectcalico.org/security/calico-network-policy. 

## Recommendations
### Create a default deny policy
As with RBAC policies, network policies should adhere to the policy of least privileged access.  Start by creating a deny all policy that restricts all inbound and outbound traffic from a namespace or create a global policy using Calico.

_Kubernetes network policy_
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

_Calico network policy_
```yaml
apiVersion: crd.projectcalico.org/v1
kind: GlobalNetworkPolicy
metadata:
  name: default-deny
spec:
  selector: all()
  types:
  - Ingress
  - Egress
```

### Create a rule to allow DNS queries 
Once you have the defaul deny all rule in place, you can begin to layer on additional rules, such as a global rule that allows pods to query CoreDNS for name resolution. You begin by labeling the namespace: 

```
kubectl label namespace kube-system name=kube-system
```

Then add the network policy:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns-access
  namespace: default
spec:
  podSelector:
    matchLabels: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53
```
  
_Calico global policy equivalent_

```yaml
apiVersion: crd.projectcalico.org/v1
kind: GlobalNetworkPolicy
metadata:
  name: allow-dns-egress
spec:
  selector: all()
  types:
  - Egress
  egress:
  - action: Allow
    protocol: UDP  
    destination:
      namespaceSelector: name == "kube-system"
      ports: 
      - 53
```
  
The following is an example of how to use associate a network policy to a service account while preventing users associated with the readonly-sa-group from editing the service account my-sa in the default namespace: 

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-sa
  namespace: default
  labels: 
    name: my-sa
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: readonly-sa-role
rules:
# Allows the subject to read a service account called my-sa
- apiGroups: [""]
  resources: ["serviceaccounts"]
  resourceNames: ["my-sa"]
  verbs: ["get", "watch", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  namespace: default
  name: readonly-sa-rolebinding
# Binds the readonly-sa-role to the RBAC group called readonly-sa-group
subjects:
- kind: Group 
  name: readonly-sa-group 
  apiGroup: rbac.authorization.k8s.io 
roleRef:
  kind: Role 
  name: readonly-sa-role 
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: crd.projectcalico.org/v1
kind: NetworkPolicy
metadata:
  name: netpol-sa-demo
  namespace: default
# Allows all ingress traffic to services in the default namespace that reference
# the service account called my-sa
spec:
  ingress:
    - action: Allow
      source:
        serviceAccounts:
          selector: 'name == "my-sa"'
  selector: all()
```

### Incrementally add rules to selectively allow the flow of traffic between namespaces/pods
Start by allowing pods within a namespace to communicate with each other and then add custom rules that further restrict pod to pod communication within that namespace. 

### Log network traffic metadata
VPC Flow Logs captures metadata about the traffic flowing through a VPC, such as source and destination IP address and port along with accepted/dropped packets. This information could be analyzed to look for suspicous or unusual activity between resources within the VPC, including pods.  However, since the IP addresses of pods frequently change as they replaced, Flow Logs may not be sufficient on its own.  Calico Enterprise extends the Flow Logs with pod labels, making it easier to decipher the traffic flows between pods.  It also makes use of machine learning to identify anomalous traffic.

### Use encryption with AWS load balancers
The ALB and NLB both have support for transport encryption (SSL and TLS).  The `alb.ingress.kubernetes.io/certificate-arn` annotation for the ALB lets you to specify which certificates to add to the ALB.  If you omit the annotation the controller will attempt to add certificates to listeners that require it by matching the available ACM certiciates using the host field. Starting with EKS v1.15 you can use the service.beta.kubernetes.io/aws-load-balancer-ssl-cert annotation with the NLB as shown in the example below. 

```yaml
apiVersion: v1
kind: Service
metadata:
  name: demo-app
  namespace: default
  labels:
    app: demo-app
  annotations:
     service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
     service.beta.kubernetes.io/aws-load-balancer-ssl-cert: "<certificate ARN>"
     service.beta.kubernetes.io/aws-load-balancer-ssl-ports: "443"
     service.beta.kubernetes.io/aws-load-balancer-backend-protocol: "http"
spec:
  type: LoadBalancer
  ports:
  - port: 443
    targetPort: 80
    protocol: TCP
  selector:
    app: demo-app
---
kind: Deployment
apiVersion: apps/v1
metadata:
  name: nginx
  namespace: default
  labels:
    app: demo-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: demo-app
  template:
    metadata:
      labels:
        app: demo-app
    spec:
      containers:
        - name: nginx
          image: nginx
          ports:
            - containerPort: 443
              protocol: TCP
            - containerPort: 80
              protocol: TCP
```

### Additional Resources
+ [Kubernetes & Tigera: Network Policies, Security, and Audit](https://youtu.be/lEY2WnRHYpg) 
+ [Calico Enterprise](https://www.tigera.io/tigera-products/calico-enterprise/)
+ [Cilium](https://cilium.readthedocs.io/en/stable/intro/)

## Security groups
EKS uses security groups (SGs) to control the traffic between the EKS control plane and the cluster's worker nodes. Security groups are also used to control the traffic between worker nodes, worker nodes and other VPC resources, and external IP addresses.  When you provision a 1.14 cluster at platform version eks.3 or greater a cluster security group is automatically created for you.  The security group allows unfettered communication between the EKS control plane and the nodes from managed node groups. For simplicity, it is recommended that you add the cluster SG to all node groups, including unmanaged node groups.

Prior to 1.14 platform version eks.3 there were separate security groups configured for the EKS control plane and node groups. The minimum and suggested rules for the control plan and node group security groups can be found at https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html.  The minimum rules for the control plane security group allows port 443 inbound from the worker node SG and is there for securely communicating with the Kubernetes API server.  It also allows port 10250 outbound to the worker node SG; the port that the kubelet listens on. The minimum node group rules allow port 10250 inbound from the control plane SG and 443 outbound to the control plane SG.  Finally there is a rule that allows unfettered communication between nodes within a node group. 

If you need to control communication between services that run within the cluster and service the run outside the cluster, consider using a network policy engine like Cilium which allows you to use a DNS name.  Alternatively, use Calico Enterprise which allows you to map a network policy to an AWS security group.  If you're implemting a service mesh like Istio, you can use an egress gateway to restrict network egress to specific fully qualified domains or IP addresses. Read the 3 part series on [egress traffic control in Istio](https://istio.io/blog/2019/egress-traffic-control-in-istio-part-1/) for further information. 

> Unless you are running 1 pod per instance or dedicating a set of instances to run a particular application, security groups are considered to be too course grained to control network traffic.  Contemplate using network policies which are Kubernetes-aware instead. 

## Encryption in transit
Applications that need to conform to PCI, HIPAA, or other regulations may need to encrypt data while it is in transit.  Nowadays TLS is the de facto choice for encrypting traffic on the wire.  TLS, like it's predecessor SSL, provides secure communications over a network using cyptographic protocols.  TLS uses symmetric encryption where the keys to encrypt the data are generated based on a shared secret that is negotiated at the beginning of the sesssion. The follow are a few ways that you can encrypt data in a Kubernetes environment. 

+ **Nitro Instances**. Traffic exchanged between select Nitro instance types, e.g. M5n, M5dn, R5n, and R5dn, is automatically encrypted by default.  When there's an intermediate hop, like a trasit gateway or a load balancer, the traffic is not encrypted. 
+ **Container Network Interfaces (CNIs)**. [WeaveNet](https://www.weave.works/oss/net/) can be configured to automatically encrypt all traffic using NaCl encryption for sleeve traffic, and IPsec ESP for fast datapath traffic.
+ **Service Mesh**. Encryption in transit can also be implemented with a service mesh like App Mesh, Linkerd v2, and Istio. Currently, App Mesh supports [TLS encryption](https://docs.aws.amazon.com/app-mesh/latest/userguide/virtual-node-tls.html) with a private certificate issued by ACM or a certificate stored on the local file system of the virtual node. Linkerd and Istio both have support for mTLS which adds another layer of security through mutual exchange and validation of certificates.