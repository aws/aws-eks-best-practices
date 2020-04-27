# Incident response and forensics
Your ability to react quickly to an incident can help minimize damage caused from a breach. Having a reliable alerting system that can warn you of suspicious behavior is the first step in a good incident response plan. When an incident does arise, you have to quickly decide whether to destroy and replace the container, or isolate and inspect the container. If you choose to isolate the container for forensic investigation and root cause analysis, then the following set of activities should be followed:

## Sample incident response plan

### Identify the offending Pod and worker node
Your first course of action should be to isolate the damage.  Start by identifying where the breach occurred and isolate that Pod and its node from the rest of the infrastructure.
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
An attacker may attempt to erase their misdeeds by terminating affected node.  Enabling [termination protection](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/terminating-instances.html#Using_ChangingDisableAPITermination) can prevent this from happening.  [Instance scale-in protection](https://docs.aws.amazon.com/autoscaling/ec2/userguide/as-instance-termination.html#instance-protection) will protect the node from a scale-in event. 
!!! warning 
    You cannot enable termination protection on a Spot instance. 
### Label offending the Pod/Node with a label indicating that it is part of an active investigation
This will serve as a warning to cluster administrators not to tamper with the affected Pods/Nodes until the investigation is complete. 
### Capture volatile artifacts on the worker node
+ **Capture the operating system memory**. This will capture the Docker daemon and its subprocess per container.  [MargaritaShotgun](https://github.com/ThreatResponse/margaritashotgun), a remote memory acquisition tool, can aid in this effort. 
+ **Perform a netstat tree dump of the processes running and the open ports**. This will capture the docker daemon and its subprocess per container. 
+ **Run docker commands before evidence is altered on the worker node**.
    + `docker container top CONTAINER` for processes running.
    + `docker container logs CONTAINER` for daemon level held logs.
    + `docker container port CONTAINER` for list of open ports.
    + `docker container diff CONTAINER` to capture changes to files and directories to container's  filesystem since its initial launch.   
+ **Pause the container for forensic capture**.
+ **Snapshot the instance's EBS volumes**.

## Recommendations

### Review the AWS Security Incident Response Whitepaper
While this section gives a brief overview along with a few  recommendations for handling suspected security breaches, the topic is exhaustively covered in the white paper, [AWS Security Incident Response](https://d1.awsstatic.com/whitepapers/aws_security_incident_response.pdf).

### Practice security game days
Divide your security practitioners into 2 teams: red and blue.  The red team will be focused on probing different systems for vulnerabilities while the blue team will be responsible for defending against them.  If you don't have enough security practitioners to create separate teams, consider hiring an outside entity that has knowledge of Kubernetes exploits. 

### Run penetration tests against your cluster
Periodically attacking your own cluster can help you discover vulnerabilities and misconfigurations.  Before getting started, follow the [penetration test guidelines](https://aws.amazon.com/security/penetration-testing/) before conducting a test against your cluster. 

## Tools
+ [kube-hunter](https://github.com/aquasecurity/kube-hunter), a penetration testing tool for Kubernetes. 
+ [Gremlin](https://www.gremlin.com/product/#kubernetes), a chaos engineering toolkit that you can use to simulate attacks against your applications and infrastructure. 
+ [kube-forensics](https://github.com/keikoproj/kube-forensics), a Kubernetes controller that triggers a job that collects the state of a running pod and dumps it in an S3 bucket. 
