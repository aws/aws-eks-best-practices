## Incident response and forensics
Your ability to react quickly to an incident can help minimize damage caused from a breach. Having a reliable alerting system that can warn you of suspicious behavior is the first step in a good incident response plan. When an incident does arise you have to quickly decide whether to destroy and replace the container, or isolate and inspect the container. There are different factors that may lead to the either decision, but if you choose to isolate the worker node for forensic investigation and root cause analysis, then the following set of activities should be followed:

+ Identify the offending pod and worker node.
+ Enable termination protection on impacted worker node.
+ Revoke temporary security credentials assigned to the pod or worker node if necessary.
+ Cordon the worker node.
+ Isolate the pod by creating a network policy the denies all ingress and egress traffic
+ Label offending the pod/node with a label indicating that it is part of an active investigation.
+ Capture volatile artifacts in runtime on the worker node.
  + Memory capture operating system memory. This will capture the docker daemon and its subprocess per  container.
  + Perform a netstat tree dump of the processes running and the open ports. This will capture the docker daemon and its subprocess per container. 
+ Run docker commands before evidence is altered on the worker node.
    + Docker container top CONTAINER for processes running.
    + Docker container logs CONTAINER for daemon level held logs.
    + Docker container port CONTAINER for list of open ports.
    + Docker container diff CONTAINER to capture changes to files and directories to container's  filesystem since its initial launch.   
+ Pause the container for forensic capture.
+ Snapshot the container instance EBS volume.
+ Isolate the worker node from the network by remove it from its node security groups.

## Recommendations
+ **Practice security game days**. Divide your security practitioners into 2 teams: red and blue.  The red team will be focused on probing different systems for vulnerabilities while the blue team will be responsible for defending against them.  If you don't have enough security practitioners to create separate teams, consider hiring an outside entity that has knowledge of Kubernetes exploits. 

+ **Run penetration tests against your cluster**. Periodically attacking your own cluster can help you discover vulnerabilities and misconfigurations.  Before getting started, follow the [penetration test guidelines](https://aws.amazon.com/security/penetration-testing/) before conducting a test against your cluster. 

## Tools
+ [kube-hunter](https://github.com/aquasecurity/kube-hunter)
+ [Gremlin](https://www.gremlin.com/product/#kubernetes)
+ https://twitter.com/IanColdwater