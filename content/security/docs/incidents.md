# Incident response and forensics
Your ability to react quickly to an incident can help minimize damage caused from a breach. Having a reliable alerting system that can warn you of suspicious behavior is the first step in a good incident response plan. When an incident does arise you have to quickly decide whether to destroy and replace the container, or isolate and inspect the container. If you choose to isolate the worker node for forensic investigation and root cause analysis, then the following set of activities should be followed:

## Sample incident response plan

### Identify the offending pod and worker node
Your first course of action should be to isolate the damage.  Start by identifying where the breach occurred and isolate that pod/node from the rest of the infratructure
### Isolate the pod by creating a network policy the denies all ingress and egress traffic to the pod
A deny all traffic rule may help stop an attack that is already underway. 
### Revoke temporary security credentials assigned to the pod or worker node if necessary
If the worker node has been assigned an IAM role that allows pods to gain access to other AWS resources, remove those roles from the instance to prevent further damage from the attack. Similarly, if the pod has been assigned an IAM role, evaluate whether you can safely remove the IAM policies from the role without impacting other workloads.
### Cordon the worker node
By cordoning the impacted worker node, you're informing the scheduler to avoid scheduling pods onto the affected node. This will allow you to remove the node for forensic study without disrupting other workloads.
### Enable termination protection on impacted worker node
An attacker may attempt to erase their misdeeds by terminating affected node.  Enabling termination protection can prvent this from happening.  It will also protect the node from a scale-in event. 
### Label offending the pod/node with a label indicating that it is part of an active investigation
This will serve as a warning to cluster administrators not to tamper with the affected pods/nodes until the investigation is complete. 
### Capture volatile artifacts on the worker node
+ **Capture the operating system memory**. This will capture the docker daemon and its subprocess per container.
+ **Perform a netstat tree dump of the processes running and the open ports**. This will capture the docker daemon and its subprocess per container. 
+ **Run docker commands before evidence is altered on the worker node**.
    + `docker container top CONTAINER` for processes running.
    + `docker container logs CONTAINER` for daemon level held logs.
    + `docker container port CONTAINER` for list of open ports.
    + `docker container diff CONTAINER` to capture changes to files and directories to container's  filesystem since its initial launch.   
+ **Pause the container for forensic capture**.
+ **Snapshot the instance's EBS volumes**.

## Recommendations
### Practice security game days
Divide your security practitioners into 2 teams: red and blue.  The red team will be focused on probing different systems for vulnerabilities while the blue team will be responsible for defending against them.  If you don't have enough security practitioners to create separate teams, consider hiring an outside entity that has knowledge of Kubernetes exploits. 

### Run penetration tests against your cluster
Periodically attacking your own cluster can help you discover vulnerabilities and misconfigurations.  Before getting started, follow the [penetration test guidelines](https://aws.amazon.com/security/penetration-testing/) before conducting a test against your cluster. 

## Tools
+ [kube-hunter](https://github.com/aquasecurity/kube-hunter)
+ [Gremlin](https://www.gremlin.com/product/#kubernetes)
+ [kube-forensics](https://github.com/keikoproj/kube-forensics)