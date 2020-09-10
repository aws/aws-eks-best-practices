# Network security
Network security has several facets.  The first involves the application of rules which restrict the flow of network traffic between services.  The second involves the encryption of traffic while it is in transit.  The mechanisms to implement these security measures on EKS are varied but often include the following items:

#### Traffic control
+ Network Policies
+ Security Groups
#### Encryption in transit
+ Service Mesh
+ Container Network Interfaces (CNIs)
+ Nitro Instances

## Network policy
Within a Kubernetes cluster, all Pod to Pod communication is allowed by default.  While this flexibility may help promote experimentation, it is not considered secure.  Kubernetes network policies give you a mechanism to restrict network traffic between Pods (often referred to as East/West traffic) and between Pods and external services. Kubernetes network policies operate at layers 3 and 4 of the OSI model.  Network policies use pod selectors and labels to identify source and destination pods, but can also include IP addresses, port numbers, protocol number, or a combination of these. [Calico](https://docs.projectcalico.org/introduction/), is an open source policy engine from [Tigera](https://tigera.io) that works well with EKS. In addition to implementing the full set of Kubernetes network policy features, Calico supports extended network polices with a richer set of features, including support for layer 7 rules, e.g. HTTP, when integrated with Istio. Isovalent, the maintainers of [Cilium](https://cilium.readthedocs.io/en/stable/intro/), have also extended the network policies to include partial support for layer 7 rules, e.g. HTTP.  Cilium also has support for DNS hostnames which can be useful for restricting traffic between Kubernetes Services/Pods and resources that run within or outside of your VPC. By contrast, Calico Enterprise includes a feature that allows you to map a Kubernetes network policy to an AWS security group, as well as DNS hostnames. 

!!! attention
    When you first provision an EKS cluster, the Calico policy engine is not installed by default. The manifests for installing Calico can be found in the VPC CNI repository at https://github.com/aws/amazon-vpc-cni-k8s/tree/master/config.

Calico policies can be scoped to Namespaces, Pods, service accounts, or globally.  When policies are scoped to a service account, it associates a set of ingress/egress rules with that service account.  With the proper RBAC rules in place, you can prevent teams from overriding these rules, allowing IT security professionals to safely delegate administration of namespaces.

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

![](./images/default-deny.jpg)

!!! tip 
    The image above was created by the network policy viewer from [Tufin](https://orca.tufin.io/netpol/).

_Calico global network policy_
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
Once you have the default deny all rule in place, you can begin layering on additional rules, such as a global rule that allows pods to query CoreDNS for name resolution. You begin by labeling the namespace: 

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

![](./images/allow-dns-access.jpg)

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
  
The following is an example of how to associate a network policy with a service account while preventing users associated with the readonly-sa-group from editing the service account my-sa in the default namespace: 

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
# Binds the readonly-sa-role to the RBAC group called readonly-sa-group.
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
Start by allowing Pods within a Namespace to communicate with each other and then add custom rules that further restrict Pod to Pod communication within that Namespace. 

### Log network traffic metadata
[AWS VPC Flow Logs](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html) captures metadata about the traffic flowing through a VPC, such as source and destination IP address and port along with accepted/dropped packets. This information could be analyzed to look for suspicous or unusual activity between resources within the VPC, including Pods.  However, since the IP addresses of pods frequently change as they are replaced, Flow Logs may not be sufficient on its own.  Calico Enterprise extends the Flow Logs with pod labels and other metadata, making it easier to decipher the traffic flows between pods.

### Use encryption with AWS load balancers
The [AWS Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html) (ALB) and [Network Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html) (NLB) both have support for transport encryption (SSL and TLS).  The `alb.ingress.kubernetes.io/certificate-arn` annotation for the ALB lets you to specify which certificates to add to the ALB.  If you omit the annotation the controller will attempt to add certificates to listeners that require it by matching the available [AWS Certificate Manager (ACM)](https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html) certificates using the host field. Starting with EKS v1.15 you can use the service.beta.kubernetes.io/aws-load-balancer-ssl-cert annotation with the NLB as shown in the example below. 

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
+ [Kinvolk's Network Policy Advisor](https://kinvolk.io/blog/2020/03/writing-kubernetes-network-policies-with-inspektor-gadgets-network-policy-advisor/) Suggests network policies based on an analysis of network traffic

## Security groups
EKS uses [AWS VPC Security Groups](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html) (SGs) to control the traffic between the Kubernetes control plane and the cluster's worker nodes. Security groups are also used to control the traffic between worker nodes, and other VPC resources, and external IP addresses.  When you provision an EKS cluster (with Kubernetes version 1.14-eks.3 or greater), a cluster security group is automatically created for you.  This security group allows unfettered communication between the EKS control plane and the nodes from managed node groups. For simplicity, it is recommended that you add the cluster SG to all node groups, including unmanaged node groups.

Prior to Kubernetes version 1.14 and EKS version eks.3, there were separate security groups configured for the EKS control plane and node groups. The minimum and suggested rules for the control plane and node group security groups can be found at https://docs.aws.amazon.com/eks/latest/userguide/sec-group-reqs.html.  The minimum rules for the _control plane security group_ allows port 443 inbound from the worker node SG. This rule is what allows the kubelets to communicate with the Kubernetes API server.  It also also port 10250 outbound traffic to the worker node SG; 10250 is the port that the kubelets listen on. Similarly, the minimum _node group_ rules allow port 10250 inbound from the control plane SG and 443 outbound to the control plane SG.  Finally there is a rule that allows unfettered communication between nodes within a node group. 

If you need to control communication between services that run within the cluster and service the run outside the cluster such as an RDS database, consider [security groups for pods](https://docs.aws.amazon.com/eks/latest/userguide/security-groups-for-pods.html). With security groups for pods, you can assign an **existing** security group to a collection of pods. 

!!! warning
If you reference a security group that does not exist prior to the creation of the pods, the pods will not get scheduled. 

You can control which pods are assigned to a security group by creating a SecurityGroupPolicy object and specifying a PodSelector or a ServiceAccountSelector. Setting the selectors to `{}` will assign the SGs referenced in the SecurityGroupPolicy to all pods in a namespace or all Service Accounts in a namespace. Be sure you've familiarized youself with all the [considerations](https://docs.aws.amazon.com/eks/latest/userguide/security-groups-for-pods.html#security-groups-pods-considerations) before implementing security groups for pods.  

!!! important
If you use SGs for pods you **must** create a SGs that allow port 53 outbound to the to the cluster security group.  Similarly, you **must** update the cluster security group to accept port 53 inbound traffic from the pod security group.

!!! important
The [limits for security groups](https://docs.aws.amazon.com/vpc/latest/userguide/amazon-vpc-limits.html#vpc-limits-security-groups) still apply when using security groups for pods so use them judiciously. 

!!! important
You **must** create rules for inbound traffic from the cluster security group (kubelet) for all of the probes configured for pod.

While security groups for pods offers an AWS-native way to control network traffic within and outside of your cluster without the overhead of a policy daemon, other options are available. For example, the Cilium policy engine allows you to reference a DNS name in a network policy. Calico Enterprise includes an option for mapping network policies to AWS security groups. If you've implemented a service mesh like Istio, you can use an egress gateway to restrict network egress to specific, fully qualified domains or IP addresses. For further infomration about this option, read the three part series on [egress traffic control in Istio](https://istio.io/blog/2019/egress-traffic-control-in-istio-part-1/). 

## Encryption in transit
Applications that need to conform to PCI, HIPAA, or other regulations may need to encrypt data while it is in transit.  Nowadays TLS is the de facto choice for encrypting traffic on the wire.  TLS, like it's predecessor SSL, provides secure communications over a network using cryptographic protocols.  TLS uses symmetric encryption where the keys to encrypt the data are generated based on a shared secret that is negotiated at the beginning of the session. The following are a few ways that you can encrypt data in a Kubernetes environment. 

### Nitro Instances
Traffic exchanged between the following Nitro instance types C5n, G4, I3en, M5dn, M5n, P3dn, R5dn, and R5n, is automatically encrypted by default.  When there's an intermediate hop, like a transit gateway or a load balancer, the traffic is not encrypted. See [Encryption in transit](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/data-protection.html#encryption-transit) and the following [What's new](https://aws.amazon.com/about-aws/whats-new/2019/10/introducing-amazon-ec2-m5n-m5dn-r5n-and-r5dn-instances-featuring-100-gbps-of-network-bandwidth/) announcement for further details.

### Container Network Interfaces (CNIs)
[WeaveNet](https://www.weave.works/oss/net/) can be configured to automatically encrypt all traffic using NaCl encryption for sleeve traffic, and IPsec ESP for fast datapath traffic.

### Service Mesh
Encryption in transit can also be implemented with a service mesh like App Mesh, Linkerd v2, and Istio. Currently, App Mesh supports [TLS encryption](https://docs.aws.amazon.com/app-mesh/latest/userguide/virtual-node-tls.html) with a private certificate issued by [AWS Certificate Manager](https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html) (ACM) or a certificate stored on the local file system of the virtual node. Linkerd and Istio both have support for mTLS which adds another layer of security through mutual exchange and validation of certificates.
  
The [aws-app-mesh-examples](https://github.com/aws/aws-app-mesh-examples) GitHub repository provides walkthroughs for configuring TLS using certificates issued by ACM and certificates that are packaged with your Envoy container:
+ [Configuring TLS with File Provided TLS Certificates](https://github.com/aws/aws-app-mesh-examples/tree/master/walkthroughs/howto-tls-file-provided)
+ [Configuring TLS with AWS Certificate Manager](https://github.com/aws/aws-app-mesh-examples/tree/master/walkthroughs/tls-with-acm) 

### Ingress Controllers and Load Balancers
Ingress controllers are a way for you to intelligently route HTTP/S traffic that emanates from outside the cluster to services running inside the cluster. Oftentimes, these Ingresses are fronted by a layer 4 load balancer, like the Classic Load Balancer or the Network Load Balancer (NLB). Encrypted traffic can be terminated at different places within the network, e.g. at the load balancer, at the ingress resource, or the Pod. How and where you terminate your SSL connection will ultimately be dictated by your organization's network security policy. For instance, if you have a policy that requires end-to-end encryption, you will have to decrypt the traffic at the Pod. This will place additional burden on your Pod as it will have to spend cycles establishing the initial handshake. Overall SSL/TLS processing is very CPU intensive. Consequently, if you have the flexibility, try performing the SSL offload at the Ingress or the load balancer. 

An ingress controller can be configured to terminate SSL/TLS connections. An example for how to terminate SSL/TLS connections at the NLB appears [above](#Use-encryption-with-AWS-load-balancers). Additional examples for SSL/TLS termination appear below.
 
+ [Securing EKS Ingress With Contour And Let’s Encrypt The GitOps Way](https://aws.amazon.com/blogs/containers/securing-eks-ingress-contour-lets-encrypt-gitops/)
+ [How do I terminate HTTPS traffic on Amazon EKS workloads with ACM?](https://aws.amazon.com/premiumsupport/knowledge-center/terminate-https-traffic-eks-acm/)

!!! attention 
    Some Ingresses, like the ALB ingress controller, implement the SSL/TLS using Annotations instead of as part of the Ingress Spec. 

## Tooling
+ [Verifying Service Mesh TLS in Kubernetes, Using ksniff and Wireshark](https://itnext.io/verifying-service-mesh-tls-in-kubernetes-using-ksniff-and-wireshark-2e993b26bf95)
+ [ksniff](https://github.com/eldadru/ksniff)
