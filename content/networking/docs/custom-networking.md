# Custom Networking

By default, the CNI assigns Pod’s IP address from the worker node's primary elastic network interface's (ENI) security groups and subnet. If you don’t have enough IP addresses in the worker node subnet or prefer that the worker nodes and Pods reside in separate subnets, you can use [CNI custom networking](https://docs.aws.amazon.com/eks/latest/userguide/cni-custom-network.html).  

Enabling a custom network removes an available elastic network interface (and all of its available IP addresses for pods) from each worker node that uses it. The worker node's primary network interface is not used for pod placement when a custom network is enabled.

If you want the CNI to assign IP addresses for Pods from a different subnet, you can set `AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG` environment variable to `true`.

```shell
kubectl set env daemonset aws-node -n kube-system AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG=true
```

EKS managed node groups currently don’t support custom networking option.

When `AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG=true`, the CNI will assign Pod IP address from a subnet defined in `ENIConfig`. The `ENIConfig` custom resource is used to define the subnet in which Pods will be scheduled. 

```yaml
apiVersion: crd.k8s.amazonaws.com/v1alpha1
kind: ENIConfig
metadata: 
  name: us-west-2a
spec: 
  securityGroups: 
    - sg-0dff111a1d11c1c11
  subnet: subnet-011b111c1f11fdf11
```

You will need to create an `ENIconfig` custom resource for each subnet you want to use for Pod networking.

- The `securityGroups` field should have the ID of the security group attached to the worker nodes.
- The `name` field should be the name of the Availability Zone in your VPC. If you name your ENIConfig custom resources after each Availability Zone in your VPC, you can enable Kubernetes to automatically apply the corresponding ENIConfig for the worker node Availability Zone with the following command.

```shell
kubectl set env daemonset aws-node \
-n kube-system ENI_CONFIG_LABEL_DEF=failure-domain.beta.kubernetes.io/zone
```

Upon creating the `ENIconfig` custom resources, you will need to create new worker nodes. The existing worker nodes and Pods will remain unaffected.

You will also need to calculate the maximum number of Pods that can be scheduled on each worker node and pass it in worker nodes’ user-data script.

To determine the number of Pods for each worker node, you will need to know [the number of network interfaces and the IPv4 addresses per network interface the worker node supports](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-eni.html#AvailableIpPerENI). The formula for calculating the maximum number of pods for an EC2 instance is:

```console
maxPods = (number of interfaces - 1) * (max IPv4 addresses per interface - 1) + 2
```

For a `c3.large` EC2 instance, the calculation will be:

```console
Maximum Pods = ((number of interfaces = 3) - 1) * ((max IPv4 addresses = 10) - 1) +2 
=> Maximum Pods = (3 - 1) * (10 - 1) + 2
=> Maximum Pods = 2 * 9 + 2 = 20
```

You can then pass the `max-pods` value in the worker nodes’ user-data script:

```console
--use-max-pods false --kubelet-extra-args '--max-pods=20'
```

Since the node’s primary ENI is no longer used to assign Pod IP addresses, there is a decline in the number of Pods you can run on a given EC2 instance type.

## Recommendations
