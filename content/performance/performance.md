# Performance Efficiency Pillar

The performance efficiency pillar focuses on the efficient use of computing resources to meet requirements and how to maintain that efficiency as demand changes and technologies evolve. This section provides in-depth, best practices guidance for architecting for performance efficiency on AWS.

## Definition

To ensure the efficient use of EKS container services, you should gather data on all aspects of the architecture, from the high-level design to the selection of EKS resource types. By reviewing your choices on a regular basis, you ensure that you are taking advantage of the continually evolving Amazon EKS and Container services. Monitoring will ensure that you are aware of any deviance from expected performance so you can take action on it.

Performance efficiency for EKS containers is composed of three areas:

- Optimize your container

- Resource Management

- Scalability Management

## Best Practices

### Optimize your container

You can run most applications in a Docker container without too much hassle. There are a number of things that you need to do to ensure it&#39;s running effectively in a production environment, including streamlining the build process. The following best practices will help you to achieve that.

#### Recommendations

- **Make your container images stateless:** A container created with a Docker image should be ephemeral and immutable. In other words, the container should be disposable and independent, i.e. a new one can be built and put in place with absolutely no configuration changes. Design your containers to be stateless. If you would like to use persistent data, use [volumes](https://docs.docker.com/engine/admin/volumes/volumes/) instead. If you would like to store secrets or sensitive application data used by services, you can use solutions like AWS [Systems Manager](https://aws.amazon.com/systems-manager/)[Parameter Store](https://aws.amazon.com/ec2/systems-manager/parameter-store/) or third-party offerings or open source solutions, such as [HashiCorp Valut](https://www.vaultproject.io/) and [Consul](https://www.consul.io/), for runtime configurations.
- [**Minimal base image**](https://docs.docker.com/develop/develop-images/baseimages/) **:** Start with a small base image. Every other instruction in the Dockerfile builds on top of this image. The smaller the base image, the smaller the resulting image is, and the more quickly it can be downloaded. For example, the [alpine:3.7](https://hub.docker.com/r/library/alpine/tags/) image is 71 MB smaller than the [centos:7](https://hub.docker.com/r/library/centos/tags/) image. You can even use the [scratch](https://hub.docker.com/r/library/scratch/) base image, which is an empty image on which you can build your own runtime environment.
- **Avoid unnecessary packages:** When building a container image, include only the dependencies what your application needs and avoid installing unnecessary packages. For example if your application does not need an SSH server, don&#39;t include one.  This will reduce complexity, dependencies, file sizes, and build times.  To exclude files not relevant to the build use a .dockerignore file.
- [**Use multi-stage build**](https://docs.docker.com/v17.09/engine/userguide/eng-image/multistage-build/#use-multi-stage-builds):Multi-stage builds allow you to build your application in a first &quot;build&quot; container and use the result in another container, while using the same Dockerfile.  To expand a bit on that, in multi-stage builds, you use multiple FROM statements in your Dockerfile. Each FROM instruction can use a different base, and each of them begins a new stage of the build. You can selectively copy artifacts from one stage to another, leaving behind everything you don&#39;t want in the final image.  This method drastically reduces the size of your final image, without struggling to reduce the number of intermediate layers and files.
- **Minimize number of layers:** Each instruction in the Dockerfile adds an extra layer to the Docker image. The number of instructions and layers should be kept to a minimum as this affects build performance and time. For example, the first  instruction below will create multiple layers, whereas the second instruction by using &amp;&amp;(chaining) we reduced the number of layers, which will help provide better performance. The is the best way to reduce the number of layers that will be created in your Dockerfile.
- 
    ```
            RUN apt-get -y update
            RUN apt-get install -y python
            RUN apt-get -y update && apt-get install -y python
    ```
            
- **Properly tag your images:** When building images, always tag them with useful and meaningful tags. This is a good way to organize and document metadata describing an image, for example, by including a unique counter like build id from a CI server (e.g. CodeBuild or Jenkins) to help with identifying the correct image. The tag latest is used by default if you do not provide one in your Docker commands.  We recommend not to use the automatically created latest tag, because by using this tag you&#39;ll automatically be running future major releases, which could include breaking changes for your application. The best practice is to avoid the latest tag and instead use the unique digest created by your CI server.
- **Use** [**Build Cache**](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/) **to improve build speed** : The cache allows you to take advantage of existing cached images, rather than building each image from scratch. For example, you should add the source code of your application as late as possible in your Dockerfile so that the base image and your application&#39;s dependencies get cached and aren&#39;t rebuilt on every build. To reuse already cached images, By default in Amazon EKS, the kubelet will try to pull each image from the specified registry. However, if the imagePullPolicy property of the container is set to IfNotPresent or Never, then a local image is used (preferentially or exclusively, respectively).
- **Image Security :** Using public images  may be  a great way to start working on containers and deploying it to Kubernetes. However, using them in production can come with a set of challenges. Especially when it comes to security. Ensure to follow the best practices for packaging and distributing the containers/applications. For example, don&#39;t build your containers with passwords baked in also you might need to control what&#39;s inside them.  Recommend to use private repository such as [Amazon ECR](https://aws.amazon.com/ecr/) and leverage the in-built [image scanning](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html) feature to identify software vulnerabilities in your container images.  

- **Right size your containers:**  As you develop and run applications in containers, there are a few key areas to consider. How you size containers and manage your application deployments can negatively impact the end-user experience of services that you provide. To help you succeed, the following best practices will help you right size your containers. After you determine the number of resources required for your application, you should set requests and limits Kubernetes to ensure that your applications are running correctly. 

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*(a) Perform testing of the application*:  to gather vital statistics and other performance &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Based upon this data you can work out the optimal configuration, in terms of memory and &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;CPU, for your container. Vital statistics such as : __*CPU, Latency, I/O, Memory usage, &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Network*__ . Determine expected, mean, and peak container memory and CPU usage by &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;doing a separate load test if necessary. Also consider all the processes that might &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;potentially run in parallel in the container. 

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;     Recommend to use  [CloudWatch Container insights](https://aws.amazon.com/blogs/mt/introducing-container-insights-for-amazon-ecs/) or partner products, which will give &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;you the right information to size containers and the Worker nodes.


&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*(b)Test services independently:*  As many applications depend on each other in a true &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;microservice architecture, you need to test them with a high degree of independence &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;meaning that the services are both able to properly function by themselves, as well as &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;function as part of a cohesive system.

### Resource Management 

One of the most common questions that asked in the adoption of Kubernetes is &quot;*What should I put in a Pod?*&quot;. For example, a three tier LAMP application container. Should we keep this application in the same pod? Well, this works effectively as a single pod but this is an example of an anti-pattern for Pod creation. There are two reasons for that 

***(a)*** If you have both the containers in the same Pod, you are forced to use the same scaling strategy which is not ideal for production environment also you can&#39;t effectively manage or constraint resources based on the usage. *E.g:* you might need to scale just the frontend not frontend and backend (MySQL) as a unit also if you would like to increase the resources dedicated just to the backend, you cant just do that.

***(b)*** If you have two separate pods, one for frontend and other for backend. Scaling would be very easy and you get a better reliability.

The above might not work in all the use-cases. In the above example frontend and backend may land in different machines and they will communicate with each other via network, So you need to ask the question &quot;***Will my application work correctly, If they are placed and run on different machines?***&quot; If the answer is a &quot;***no***&quot; may be because of the application design or for some other technical reasons, then grouping of containers in a single pod makes sense. If the answer is &quot;***Yes***&quot; then multiple Pods is the correct approach.

#### Recommendations

+ **Package a single application per container:**
A container works best when a single application runs inside it. This application should have a single parent process. For example, do not run PHP and MySQL in the same container: it&#39;s harder to debug, and you can&#39;t horizontally scale the PHP container alone. This separation allows you to better tie the lifecycle of the application to that of the container.  Your containers should be both stateless and immutable. Stateless means that any state (persistent data of any kind) is stored outside of the container, for example, you can use different kinds of external storage like Persistent disk, Amazon EBS, and Amazon EFS if needed, or managed database like Amazon RDS.  Immutable means that a container will not be modified during its life: no updates, no patches, and no configuration changes. To update the application code or apply a patch, you build a new image and deploy it.

+ **Use Labels to Kubernetes Objects:**
[Labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/#labels) allow Kubernetes objects to be queried and operated upon in bulk. They can also be used to identify and organize Kubernetes objects into groups. As such defining labels should figure right at the top of any Kubernetes best practices list.

+ **Setting resource request limits:**
Setting request limits is the mechanism used to control the amount of system resources that a container can consume such as CPU and memory. These settings are what the container is guaranteed to get when the container initially starts. If a container requests a resource, container orchestrators such as Kubernetes will only schedule it on a node that can provide that resource. Limits, on the other hand, make sure that a container never goes above a certain value. The container is only allowed to go up to the limit, and then it is restricted.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; In the below example Pod manifest, we add a limit of 1.0 CPU and 256 MB of memory

```
        apiVersion: v1
        kind: Pod
        metadata:
          name: nginx-pod-webserver
          labels:
            name: nginx-pod
        spec:
          containers:
          - name: nginx
            image: nginx:latest
            resources:
              limits:
                memory: "256Mi"
                cpu: "1000m"
              requests:
                memory: "128Mi"
                cpu: "500m"
            ports:
            - containerPort: 80

         
```


&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;It&#39;s a best practice to define these requests and limits in your pod definitions. If you don&#39;t &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;include these values, the scheduler doesn&#39;t understand what resources are needed. &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Without this information, the scheduler might schedule the pod on a node without &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;sufficient resources to provide acceptable application performance.

+ **Limit the number of concurrent disruptions:**
Use  _PodDisruptionBudget_, This settings allows you to set a policy on the minimum available and maximum unavailable pods during voluntary eviction events. An example of an eviction would be when perform maintenance on the node or draining a node.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; _Example:_ A web frontend might want to ensure that 8 Pods to be available at any &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;given time. In this scenario, an eviction can evict as many pods as it wants, as long as &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;eight are available.
```
apiVersion: policy/v1beta1
kind: PodDisruptionBudget
metadata:
  name: frontend-demo
spec:
  minAvailable: 8
  selector:
    matchLabels:
      app: frontend
```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**N.B:** You can also specify pod disruption budget as a percentage by using maxAvailable &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;or maxUnavailable parameter.

+ **Use Namespaces:**
Namespaces allows a physical cluster to be shared by multiple teams. A namespace allows to partition created resources into a logically named group. This allows you to set resource quotas per namespace, Role-Based Access Control (RBAC) per namespace, and also network policies per namespace. It gives you soft multitenancy features.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;For example, If you have three applications running on a single Amazon EKS cluster &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;accessed by three different teams which requires multiple resource constraints and &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;different levels of QoS each group  you could create a namespace per team and give each &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;team a quota on the number of resources that it can utilize, such as CPU and memory.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;You can also specify default limits in Kubernetes namespaces level by enabling &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;[LimitRange](https://kubernetes.io/docs/concepts/policy/limit-range/) admission controller. These default limits will constrain the amount of CPU &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;or memory a given Pod can use unless the defaults are explicitly overridden by the Pod&#39;s &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;configuration.

+ **Manage Resource Quota:** 
Each namespace can be assigned resource quota. Specifying quota allows to restrict how much of cluster resources can be consumed across all resources in a namespace. Resource quota can be defined by a [ResourceQuota](https://kubernetes.io/docs/concepts/policy/resource-quotas/) object. A presence of ResourceQuota object in a namespace ensures that resource quotas are enforced.

+ **Configure Health Checks for Pods:**
Health checks are a simple way to let the system know if an instance of your app is working or not. If an instance of your app is not working, then other services should not access it or send requests to it. Instead, requests should be sent to another instance of the app that is working. The system also should bring your app back to a healthy state.  By default, all the running pods have the restart policy set to always which means the kubelet running within a node will automatically restart a pod when the container encounters an error. Health checks extend this capability of kubelet through the concept of [container probes](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#container-probes).

  Kubernetes provides two types of [health checks](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/): readiness and liveness probes.  For example, consider if one of your applications, which typically runs for long periods of time, transitions to a non-running state and can only recover by being restarted. You can use liveness probes to detect and remedy such situations. Using health checks gives your applications better reliability, and higher uptime.


+ **Advanced Scheduling Techniques:**
Generally, schedulers ensure that pods are placed only on nodes that have sufficient free resources, and across nodes, they try to balance out the resource utilization across nodes, deployments, replicas, and so on. But sometimes you want to control how your pods are scheduled. For example, perhaps you want to ensure that certain pods are only scheduled on nodes with specialized hardware, such as requiring a GPU machine for an ML workload. Or you want to collocate services that communicate frequently.

  Kubernetes offers many[advanced scheduling features](https://kubernetes.io/blog/2017/03/advanced-scheduling-in-kubernetes/)and multiple filters/constraints to schedule the pods on the right node.  For example, when using Amazon EKS, you can use[taints and tolerations](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#taints-and-toleations-beta-feature)to restrict what workloads can run on specific nodes. You can also control pod scheduling using [node selectors](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#nodeselector)and[affinity and anti-affinity](https://kubernetes.io/docs/concepts/configuration/assign-pod-node/#affinity-and-anti-affinity)constructs and even have your own custom scheduler built for this purpose.

#### Scalability Management 
  Containers are stateless. They are born and when they die, they are not resurrected.  There are many techniques that you can leverage on Amazon EKS, not only to scale out your containerized applications but also the Kubernetes worker node.
  
#### Recommendations

  + On Amazon EKS, you can configure [Horizontal pod autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/),which automatically scales the number of pods in a replication controller, deployment, or replica set based on observed CPU utilization (or use[custom metrics](https://git.k8s.io/community/contributors/design-proposals/instrumentation/custom-metrics-api.md)based on application-provided metrics).

  + You can use  [Vertical Pod Autoscaler](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler) which automatically adjusts the CPU and memory reservations for your pods to help &quot;right size&quot; your applications. This adjustment can improve cluster resource utilization and free up CPU and memory for other pods.  This is useful in scenarios like your production database &quot;MongoDB&quot; does not scale the same way as a stateless application frontend, In this scenario you could use VPA to scale up the MongoDB Pod.

  + To enable VPA you need to use  Kubernetes metrics server, which is an aggregator of resource usage data in your cluster. It is not deployed by default in Amazon EKS clusters.  You need to configure it before [configure VPA](https://docs.aws.amazon.com/eks/latest/userguide/vertical-pod-autoscaler.html) alternatively you can also use Prometheus to provide metrics for the Vertical Pod Autoscaler.

  + While HPA and VPA scale the deployments and pods, [Cluster Autoscaler](https://github.com/kubernetes/autoscaler) will scale-out  and scale-in the size of the pool of worker nodes. It adjusts the size of a Kubernetes cluster based on the current utilization. Cluster Autoscaler increases the size of the cluster when there are pods that failed to schedule on any of the current nodes due to insufficient resources or when adding a new node would increase the overall availability of cluster resources. Please follow this [step by step](https://eksworkshop.com/scaling/deploy_ca/) guide to setup Cluster Autoscaler.  If you are using Amazon EKS on AWS Fargate, AWS Manages the control plane for you. 

     Please have a look at the reliability pillar for detailed information.
     
#### Monitoring 
#### Deployment Best Practices 
#### Trade-Offs

Remember that in software engineering “Everything is a trade-off" and there is no free lunch. Therefore, before making any architectural decision make sure to analyze those trade-offs. Also, you need to pay more attention to "why" you are making an architectural decision than to "how" to do it.
