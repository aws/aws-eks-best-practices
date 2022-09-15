# Example Gatekeeper policies and constraints

This is an example set of Gatekeeper Policies that draws from the official [Gatekeeper Library](https://github.com/open-policy-agent/gatekeeper-library) as well as the fields which Kubernetes saw fit to include in its original [Pod Security Policies](https://kubernetes.io/docs/concepts/policy/pod-security-policy/).

## How to deploy?
This can be deployed to a machine that already has Gatekeeper installed via a `kubectl apply -k policies/constraint-templates/ && kubectl apply -k policies/constraints/` or via GitOps tools, such as Flux or ArgoCD, configured to deploy all the YAML manifests in that folder.

There are the required manifests in this repository (`gatekeeper-sync.yaml` and `policies-sync.yaml`) to deploy this with Flux v2.

### (Optional) Deploy Open Policy Agent (OPA) Gatekeeper and the policies via Flux v2

In order to deploy Gatekeeper and the example policies:
1. Ensure you are on a system where `kubectl` is installed and working against the cluster
1. [Install the Flux v2 CLI](https://fluxcd.io/docs/installation/#install-the-flux-cli)
1. Run `flux install` to install Flux onto the cluster
1. Change directory into the root of quickstart-eks-cdk-python
1. Run `kubectl apply -f gatekeeper-sync.yaml` to install the Gatekeeper Helm Chart w/Flux (as well as enable future GitOps if the main branch of the repo is updated)
1. Run `flux get all` to see the progress of getting and installing the Gatekeeper Helm Chart
1. Run `flux create source git gatekeeper --url=https://github.com/aws/aws-eks-best-practices --branch=main` to add this repo to Flux as a source
    1. Alternatively, and perhaps advisably, specify the URL of your git repo you've forked/cloned the project to instead - as it will trigger GitOps actions going forward when this changes!
1. Run `kubectl apply -f policies/policies-sync.yaml` to install the policies with Flux (as well as enable future GitOps if the main branch of the repo is updated)
1. Run `flux get all` to see all of the Flux items and their reconciliation statuses

If you want to change any of the Gatekeeper Constraints or ConstraintTemplates you just change the YAML and then push/merge it to the repo and branch you indicated above and Flux will them deploy those changes to your cluster via GitOps.

If you are going to do this with GitOps it is suggested that you fork these templates and constraints and do it from your own git repo(s).

## How to test it works?
There is an example that will be blocked by each policy in the `tests` folder. These policies are derived from the `allowed.yaml` template, which passes all of the policies, changed to violate *just* the policy in question.

## What policies are we enforcing by default in our Quickstart?

We started by recreating the example [Restricted legacy PSP template](https://kubernetes.io/docs/concepts/security/pod-security-standards/#restricted) but via Gatekeeper as our default - and then added a few more important things that were not possible with PSPs but are with Gatekeeper.

**NOTE:** We excluded the `kube-system` namespace in all of the constraints as many infrastructure add-ons have legitimate need for, and thus require exceptions these limitations of, elevated privileges. If you deploy those things to the kube-system namespace they will not be blocked by these example policies. This is also an example of how it is possible with Gatekeeper constraints to exclude additional namespaces, or other Kubernetes labels, as appropriate.

### Policies derived from PSPs

| Description | Legacy PSP Field | Constraint and Constraint Template Files |
| --- | --- | --- |
| Block running privileged containers | `privileged` | psp_privileged.yaml |
| Block  the ability for Pods to escalate privileges via `setuid` or `setgid` binaries etc. | `allowPrivilegeEscalation` | psp_privilege_escalation.yaml |
| Block the ability for the Pods to request any Linux capabilities (e.g. NET_ADMIN | `defaultAddCapabilities`, `requiredDropCapabilities`, `allowedCapabilities` | psp_capabilities.yaml |
| Block the ability for Pods to run as the root user | `runAsUser`, `runAsGroup`, `supplementalGroups`, `fsgroup` | psp_users.yaml |
| Block the ability for Pods to use the host's namespace(s) | `hostPID`, `hostIPC` | psp_host_namespaces.yaml |
| Block the ability to use the host's network | `hostNetwork`,`hostPort` | psp_host_network.yaml |
| Block the ability for a Pod to mount certain types of volumes (e.g. host volumes) | `volumes` | psp_volumes.yaml |
||||

### Block running privileged containers

Privileged mode comes from Docker where it "enables access to all devices on the host as well as set some configuration in AppArmor or SELinux to allow the container nearly all the same access to the host as processes running outside containers on the host." (https://docs.docker.com/engine/reference/run/#runtime-privilege-and-linux-capabilities).

One of the main reasons why people generally want privileged mode is that it allows things running within a container on the host to call the local container runtime/socket and launch more containers. This is an anti-pattern with Kubernetes - which should be launching all the Pods/containers on all of its hosts. This means that if you need one Pod to launch other containers/Pods it should do so via the Kubernetes API.

There is a more granular way to allow access to specific privileges/capabilities using the capabilities policy. We block both privileged mode as well as all the capabilities by default in that separate policy as well.

### Block privilege escalation

Linux has a feature allowing particular executables to run as a different user and/or group than the one running it - setuid/setgid. This is primarily used to escalate the privileges of the current user.

This requires the PodSpec to explicitly disable that feature.

### Block the ability for the Pods to request any Linux capabilities

In addition to privileged mode which exposes a number of capabilities at once there is also a way to granularly controlled which capabilities.

You can get a list of those capabilities [here](https://docs.docker.com/engine/reference/run/#runtime-privilege-and-linux-capabilities).

We are requiring a PodSpec to explicitly drop all capabilities in this policy.

### Block the ability for Pods to run as the root user

By default, if the creator of the image doesn't specify a USER in the Dockerfile and/or you don't specify one at runtime then the container will run as `root` (https://docs.docker.com/engine/reference/run/#user).  It does this within its own namespace and the constraints of the container environment and the Gatekeeper policies - but it is still a bad idea for it to run as root unnecessarily. Running it as a non-root user makes it just all that much harder for somebody to escalate to root on the host should there be a bug or vulnerability in the system.

We do not allow the user ID (UID) or group ID (GID) of 0 - which are the root UID and GID in Linux.

**NOTE:** In order for this policy to work your container image will usually need to create a user and group in the Dockerfile - and the application will need to be able to run in a non-root context. A good example of this is [nginx-unprivileged](https://hub.docker.com/r/nginxinc/nginx-unprivileged) which, unlike the standard [nginx](https://hub.docker.com/_/nginx), runs on port 8080 rather than 80 and so does not require root access. Also note how nginx-unprivileged's Dockerfile has a useradd and groupadd. In order to pass this policy you'll have to include *that* UID and GID in the PodSpec.

### Block the ability for Pods to use the host's namespace(s)

One of the key security features of Kubernetes is that it puts each Pod into its own separate linux [namespace](https://en.wikipedia.org/wiki/Linux_namespaces). This means that it can't see the processes, volume mounts or network interfaces etc. of either the other Pods or the host.

Is is possible, though, to ask in the PodSpec to be put into the host's namespace and therefore to see everything.

This blocks the ability to do that.

### Block the ability to use the host's network

By default, EKS via the AWS CNI gives Pod gets its own VPC IP - and that is how it communicates with the network.

It is possible, though, to ask in the PodSpec to be exposed through the host's network interface instead or as well.

We are blocking the ability to do that.

### Block the ability for a Pod to mount certain types of volumes (e.g. host volumes)

A Pod can request to mount **any** path on the host/Node/Instance that it is running on (e.g. /etc, /proc, etc.).

We're blocking the ability to do that.

### Beyond Pod Security Policies

| Description | PodSpec Equivalent Field | Constraint and Constraint Template Files |
| --- | --- | --- |
| Require any Pods to declare CPU & memory limits | `resources.limits`, `resources.requests` | container_resource_ratios.yaml |
| Require any Pods to declare readiness and liveness probes/healthchecks | `readinessProbe`,`livenessProbe` | probes.yaml |
| Blocking the use of the `latest` image tag | `image` | disallowed_tags.yaml |

#### Require any Pods to declare CPU & memory limits

Kubernetes has the concepts of `requests` and `limits` when it comes to CPU & Memory. With requests it is telling Kubernetes how much CPU and Memory a Pod is *guaranteed* to get - its minimum. It can use more than that though. While limits, on the other hand, see Kubernetes enforce at that threshold and, in the case of memory, will terminate the container(s) if they exceed the limit.

By default, we're ensuring that we run running a tight ship by not only requiring that each of the containers in our Pods have **BOTH** a CPU & Memory request & limit - and that they are the same thing.

This is the ideal configuration if you are running a multi-tenant cluster to ensure that there are not any 'noisy neighbor' issues where people who don't specify limits burst into over provisioning on the Node where it was scheduled. This forces each service to think about how much CPU and Memory they actually need and declare it in their Spec templates when they deploy to the cluster - and be held to that.

#### Require any Pods to declare readiness and liveness probes/healthchecks

Kubernetes also has the concept of probes which are often also referred to as health checks.

The readiness probe controls whether the service should be sent traffic

The liveness probe controls whether the pod should be healed through replacement

We're requiring that you specify both probes in your PodSpec.

#### Blocking the use of the `latest` tag

Almost by definition the `latest` tag will change as new versions are released - often before you've tested and deployed the new version explicitly to your cluster. This can lead to things like a Pod is healed or scaled and that leads to the new Pods running the new version alongside the old version without you knowing or intending to have released the new version.

It is best practice to always specify a specific version/tag when deploying to your clusters so any upgrades/changes are declared and intentional. A good candidate for this is the git commit ID.

## What is an example PodSpec that passes with all the default policies?

There is an example in `tests/allowed.yaml` as follows. If you find that something isn't working add the relevant section from this example.

**NOTE:** The user and group need to be created within the container and the app needs relevant permissions in order to run as that user and group you specify. In the case of our nginx example they created a 2nd image and [Dockerfile](https://github.com/nginxinc/docker-nginx-unprivileged/blob/main/Dockerfile-debian.template) to do this and had to give up some things like being able to do HTTP on port 80 with the container running as a non-root user. The 101 we are specifying for the UID and GID we got from the Dockerfile and it will vary from container to container - we just need it to not be root's UID/GID of 0.

```
apiVersion: v1
kind: Pod
metadata:
  name: nginx-allowed
  labels:
    app: nginx-allowed
spec:
  securityContext:
    supplementalGroups:
      - 101
    fsGroup: 101
  containers:
    - name: nginx
      image: nginxinc/nginx-unprivileged:1.19
      resources:
        limits:
          cpu: 1
          memory: 1Gi
        requests:
          cpu: 1
          memory: 1Gi
      ports:
      - containerPort: 8080
        protocol: TCP
      securityContext:
        runAsUser: 101
        runAsGroup: 101
        capabilities:
          drop:
            - ALL
      readinessProbe:
          httpGet:
            scheme: HTTP
            path: /index.html
            port: 8080
      livenessProbe:
          httpGet:
            scheme: HTTP
            path: /index.html
            port: 8080
```

## What are some other policies you might want to consider?

### Limiting what repositories containers can be pulled from

You might want to limit which repositories containers can be pulled from to, for example, your private AWS Elastic Container Registries. If you also have a process there to vet them then this can enforce that policy is followed.

There is an example of how to do this at https://github.com/open-policy-agent/gatekeeper-library/tree/master/library/general/allowedrepos 

Since you'll need to know what repositories are relevant for your organisation, and perhaps clone some add-ons from public repos to those, this is a policy and constraint you'll need to add to Gatekeeper yourself.

### Requiring certain labels (e.g. to help determine who 'owns' an app on the cluster and/or who to call when it breaks)

Often having the information right in the cluster and on the objects as to who owns them and who to call when it breaks can be useful to minimise the duration of an outage. It might also prove helpful in cost attribution and other Enterprise concerns.

There is an example of how to do this at https://github.com/open-policy-agent/gatekeeper-library/tree/master/library/general/requiredlabels

Since you'll know the kinds of labels you'll need for your organisation this is a policy and constraint you'll need to add to Gatekeeper yourself.
