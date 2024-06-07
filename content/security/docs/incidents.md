# Incident response and forensics

Your ability to react quickly to an incident can help minimize damage caused from a breach. Having a reliable alerting system that can warn you of suspicious behavior is the first step in a good incident response plan. When an incident does arise, you have to quickly decide whether to destroy and replace the effected container, or isolate and inspect the container. If you choose to isolate the container as part of a forensic investigation and root cause analysis, then the following set of activities should be followed:

## Sample incident response plan

### Identify the offending Pod and worker node

Your first course of action should be to isolate the damage.  Start by identifying where the breach occurred and isolate that Pod and its node from the rest of the infrastructure.

### Identify the offending Pods and worker nodes using workload name

If you know the name and namespace of the offending pod, you can identify the worker node running the pod as follows:

```bash
kubectl get pods <name> --namespace <namespace> -o=jsonpath='{.spec.nodeName}{"\n"}'   
```

If a [Workload Resource](https://kubernetes.io/docs/concepts/workloads/controllers/) such as a Deployment has been compromised, it is likely that all the pods that are part of the workload resource are compromised. Use the following command to list all the pods of the Workload Resource and the nodes they are running on:

```bash
selector=$(kubectl get deployments <name> \
 --namespace <namespace> -o json | jq -j \
'.spec.selector.matchLabels | to_entries | .[] | "\(.key)=\(.value)"')

kubectl get pods --namespace <namespace> --selector=$selector \
-o json | jq -r '.items[] | "\(.metadata.name) \(.spec.nodeName)"'
```

The above command is for deployments. You can run the same command for other workload resources such as replicasets,, statefulsets, etc.

### Identify the offending Pods and worker nodes using service account name

In some cases, you may identify that a service account is compromised.  It is likely that pods using the identified service account are compromised. You can identify all the pods using the service account and nodes they are running on with the following command:

```bash
kubectl get pods -o json --namespace <namespace> | \
    jq -r '.items[] |
    select(.spec.serviceAccount == "<service account name>") |
    "\(.metadata.name) \(.spec.nodeName)"'
```

### Identify Pods with vulnerable or compromised images and worker nodes

In some cases, you may discover that a container image being used in pods on your cluster is malicious or compromised. A container image is malicious or compromised, if it was found to contain malware, is a known bad image or has a CVE that has been exploited. You should consider all the pods using the container image compromised. You can identify the pods using the image and nodes they are running on with the following command:

```bash
IMAGE=<Name of the malicious/compromised image>

kubectl get pods -o json --all-namespaces | \
    jq -r --arg image "$IMAGE" '.items[] | 
    select(.spec.containers[] | .image == $image) | 
    "\(.metadata.name) \(.metadata.namespace) \(.spec.nodeName)"'
```

### Isolate the Pod by creating a Network Policy that denies all ingress and egress traffic to the pod

A deny all traffic rule may help stop an attack that is already underway by severing all connections to the pod. The following Network Policy will apply to a pod with the label `app=web`.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
spec:
  podSelector:
    matchLabels: 
      app: web
  policyTypes:
  - Ingress
  - Egress
```

!!! attention
    A Network Policy may prove ineffective if an attacker has gained access to underlying host. If you suspect that has happened, you can use [AWS Security Groups](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html) to isolate a compromised host from other hosts. When changing a host's security group, be aware that it will impact all containers running on that host.  

### Revoke temporary security credentials assigned to the pod or worker node if necessary

If the worker node has been assigned an IAM role that allows Pods to gain access to other AWS resources, remove those roles from the instance to prevent further damage from the attack. Similarly, if the Pod has been assigned an IAM role, evaluate whether you can safely remove the IAM policies from the role without impacting other workloads.

### Cordon the worker node

By cordoning the impacted worker node, you're informing the scheduler to avoid scheduling pods onto the affected node. This will allow you to remove the node for forensic study without disrupting other workloads.

!!! info
    This guidance is not applicable to Fargate where each Fargate pod run in its own sandboxed environment.  Instead of cordoning, sequester the affected Fargate pods by applying a network policy that denies all ingress and egress traffic.

### Enable termination protection on impacted worker node

An attacker may attempt to erase their misdeeds by terminating an affected node.  Enabling [termination protection](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/terminating-instances.html#Using_ChangingDisableAPITermination) can prevent this from happening.  [Instance scale-in protection](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-instance-termination.html#instance-protection) will protect the node from a scale-in event.

!!! warning
    You cannot enable termination protection on a Spot instance.

### Label the offending Pod/Node with a label indicating that it is part of an active investigation

This will serve as a warning to cluster administrators not to tamper with the affected Pods/Nodes until the investigation is complete.

### Capture volatile artifacts on the worker node

- **Capture the operating system memory**. This will capture the Docker daemon (or other container runtime) and its subprocesses per container. This can be accomplished using tools like [LiME](https://github.com/504ensicsLabs/LiME) and [Volatility](https://www.volatilityfoundation.org/), or through higher-level tools such as [Automated Forensics Orchestrator for Amazon EC2](https://aws.amazon.com/solutions/implementations/automated-forensics-orchestrator-for-amazon-ec2/) that build on top of them.
- **Perform a netstat tree dump of the processes running and the open ports**. This will capture the docker daemon and its subprocess per container.
- **Run commands to save container-level state before evidence is altered**. You can use capabilities of the container runtime to capture information about currently running containers. For example, with Docker, you could do the following:
  - `docker top CONTAINER` for processes running.
  - `docker logs CONTAINER` for daemon level held logs.
  - `docker inspect CONTAINER` for various information about the container.

    The same could be achieved with containerd using the [nerdctl](https://github.com/containerd/nerdctl) CLI, in place of `docker` (e.g. `nerdctl inspect`). Some additional commands are available depending on the container runtime. For example, Docker has `docker diff` to see changes to the container filesystem or `docker checkpoint` to save all container state including volatile memory (RAM). See [this Kubernetes blog post](https://kubernetes.io/blog/2022/12/05/forensic-container-checkpointing-alpha/) for discussion of similar capabilities with containerd or CRI-O runtimes.

- **Pause the container for forensic capture**.
- **Snapshot the instance's EBS volumes**.

### Redeploy compromised Pod or Workload Resource

Once you have gathered data for forensic analysis, you can redeploy the compromised pod or workload resource.

First roll out the fix for the vulnerability that was compromised and start new replacement pods. Then delete the vulnerable pods.

If the vulnerable pods are managed by a higher-level Kubernetes workload resource (for example, a Deployment or DaemonSet), deleting them will schedule new ones. So vulnerable pods will be launched again. In that case you should deploy a new replacement workload resource after fixing the vulnerability. Then you should delete the vulnerable workload.

## Recommendations

### Review the AWS Security Incident Response Whitepaper

While this section gives a brief overview along with a few  recommendations for handling suspected security breaches, the topic is exhaustively covered in the white paper, [AWS Security Incident Response](https://docs.aws.amazon.com/whitepapers/latest/aws-security-incident-response-guide/welcome.html).

### Practice security game days

Divide your security practitioners into 2 teams: red and blue.  The red team will be focused on probing different systems for vulnerabilities while the blue team will be responsible for defending against them.  If you don't have enough security practitioners to create separate teams, consider hiring an outside entity that has knowledge of Kubernetes exploits.

[Kubesploit](https://github.com/cyberark/kubesploit) is a penetration testing framework from CyberArk that you can use to conduct game days. Unlike other tools which scan your cluster for vulnerabilities, kubesploit simulates a real-world attack. This gives your blue team an opportunity to practice its response to an attack and gauge its effectiveness.

### Run penetration tests against your cluster

Periodically attacking your own cluster can help you discover vulnerabilities and misconfigurations.  Before getting started, follow the [penetration test guidelines](https://aws.amazon.com/security/penetration-testing/) before conducting a test against your cluster.

## Tools and resources

- [kube-hunter](https://github.com/aquasecurity/kube-hunter), a penetration testing tool for Kubernetes.
- [Gremlin](https://www.gremlin.com/product/#kubernetes), a chaos engineering toolkit that you can use to simulate attacks against your applications and infrastructure.
- [Attacking and Defending Kubernetes Installations](https://github.com/kubernetes/sig-security/blob/main/sig-security-external-audit/security-audit-2019/findings/AtredisPartners_Attacking_Kubernetes-v1.0.pdf)
- [kubesploit](https://www.cyberark.com/resources/threat-research-blog/kubesploit-a-new-offensive-tool-for-testing-containerized-environments)
- [NeuVector by SUSE](https://www.suse.com/neuvector/) open source, zero-trust container security platform, provides vulnerability- and risk reporting as well as security event notification
- [Advanced Persistent Threats](https://www.youtube.com/watch?v=CH7S5rE3j8w)
- [Kubernetes Practical Attack and Defense](https://www.youtube.com/watch?v=LtCx3zZpOfs)
- [Compromising Kubernetes Cluster by Exploiting RBAC Permissions](https://www.youtube.com/watch?v=1LMo0CftVC4)
