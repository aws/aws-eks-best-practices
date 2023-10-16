<!-- # Monitoring -->
# 모니터링

<!-- Prometheus, a [graduated CNCF project](https://www.cncf.io/projects/) is by far the most popular monitoring system with native integration into Kubernetes. Prometheus collects metrics around containers, pods, nodes, and clusters. Additionally, Prometheus leverages AlertsManager which lets you program alerts to warn you if something in your cluster is going wrong. Prometheus stores the metric data as a time series data identified by metric name and key/value pairs. Prometheus includes away to query using a language called PromQL, which is short for Prometheus Query Language.  -->
Prometheus, [CNCF 졸업 프로젝트](https://www.cncf.io/projects/)는 쿠버네티스에 기본적으로 통합되는 가장 인기 있는 모니터링 시스템입니다. Prometheus는 컨테이너, 포드, 노드 및 클러스터와 관련된 메트릭을 수집합니다. 또한 Prometheus는 AlertsManager를 활용합니다. AlertsManager를 사용하면 클러스터에서 문제가 발생할 경우 경고를 프로그래밍하여 경고할 수 있습니다. Prometheus는 지표 데이터를 지표 이름 및 키/값 쌍으로 식별되는 시계열 데이터로 저장합니다. Prometheus에는 Prometheus 쿼리 언어의 줄임말인 PromQL이라는 언어를 사용하여 쿼리하는 방법이 포함되어 있습니다. 

<!-- The high level architecture of Prometheus metrics collection is shown below: -->
Prometheus 메트릭 수집의 상위 수준 아키텍처는 다음과 같습니다.


![Prometheus Metrics collection](./images/prom.png)


<!-- Prometheus uses a pull mechanism and scrapes metrics from targets using exporters and from the Kubernetes API using the [kube state metrics](https://github.com/kubernetes/kube-state-metrics). This means applications and services must expose a HTTP(S) endpoint containing Prometheus formatted metrics. Prometheus will then, as per its configuration, periodically pull metrics from these HTTP(S) endpoints. -->
프로메테우스는 풀 메커니즘을 사용하고 Exporter를 사용하여 타겟에서 메트릭을 스크랩하고 [kube state metrics](https://github.com/kubernetes/kube-state-metrics)를 사용하여 쿠버네티스 API에서 메트릭을 스크랩합니다.즉, 애플리케이션과 서비스는 프로메테우스 형식의 메트릭이 포함된 HTTP(S) 엔드포인트를 노출해야 합니다. 그러면 프로메테우스는 구성에 따라 주기적으로 이러한 HTTP(S) 엔드포인트에서 메트릭을 가져옵니다.

<!-- An exporter lets you consume third party metrics as Prometheus formatted metrics. A Prometheus exporter is typically deployed on each node. For a complete list of exporters please refer to the Prometheus [exporters](https://prometheus.io/docs/instrumenting/exporters/). While [node exporter](https://github.com/prometheus/node_exporter) is suited for exporting host hardware and OS metrics for linux nodes, it wont work for Windows nodes.  -->
Exporter를 사용하면 타사 지표를 Prometheus 형식의 지표로 사용할 수 있습니다.Prometheus 익스포터는 일반적으로 각 노드에 배포됩니다.익스포터 전체 목록은 프로메테우스 [Exporter](https://prometheus.io/docs/instrumenting/exporters/)를 참조하십시오.[node exporter](https://github.com/prometheus/node_exporter)는 Linux 노드용 호스트 하드웨어 및 OS 메트릭을 내보내는 데 적합하지만 Windows 노드에서는 작동하지 않습니다.

<!-- In a **mixed node EKS cluster with Windows nodes** when you use the stable [Prometheus helm chart](https://github.com/prometheus-community/helm-charts), you will see failed pods on the Windows nodes, as this exporter is not intended for Windows. You will need to treat the Windows worker pool separate and instead install the [Windows exporter](https://github.com/prometheus-community/windows_exporter) on the Windows worker node group.  -->
**Windows 노드가 있는 혼합 노드 EKS 클러스터**에서 안정적인 [프로메테우스 헬름 차트](https://github.com/prometheus-community/helm-charts) 을 사용하면 Windows 노드에 장애가 발생한 포드가 표시됩니다. 이 익스포터는 Windows용이 아니기 때문입니다.Windows 작업자 풀을 별도로 처리하고 대신 Windows 작업자 노드 그룹에 [Windows 익스포터] (https://github.com/prometheus-community/windows_exporter) 를 설치해야 합니다.

In order to setup Prometheus monitoring for Windows nodes, you need to download and install the WMI exporter on the Windows server itself and then setup the targets inside the scrape configuration of the Prometheus configuration file.
The [releases page](https://github.com/prometheus-community/windows_exporter/releases) provides all available .msi installers, with respective feature sets and bug fixes. The installer will setup the windows_exporter as a Windows service, as well as create an exception in the Windows firewall. If the installer is run without any parameters, the exporter will run with default settings for enabled collectors, ports, etc.

You can check out the **scheduling best practices** section of this guide which suggests the use of taints/tolerations or RuntimeClass to selectively deploy node exporter only to linux nodes, while the Windows exporter is installed on Windows nodes as you bootstrap the node or using a configuration management tool of your choice (example chef, Ansible, SSM etc).

Note that, unlike the linux nodes where the node exporter is installed as a daemonset , on Windows nodes the WMI exporter is installed on the host itself. The exporter will export metrics such as the CPU usage, the memory and the disk I/O usage and can also be used to monitor IIS sites and applications, the network interfaces and services. 

The windows_exporter will expose all metrics from enabled collectors by default. This is the recommended way to collect metrics to avoid errors. However, for advanced use the windows_exporter can be passed an optional list of collectors to filter metrics. The collect[] parameter, in the Prometheus configuration lets you do that.

The default install steps for Windows include downloading and starting the exporter as a service during the bootstrapping process with arguments, such as the collectors you want to filter.

```powershell 
> Powershell Invoke-WebRequest https://github.com/prometheus-community/windows_exporter/releases/download/v0.13.0/windows_exporter-0.13.0-amd64.msi -OutFile <DOWNLOADPATH> 

> msiexec /i <DOWNLOADPATH> ENABLED_COLLECTORS="cpu,cs,logical_disk,net,os,system,container,memory"
```


By default, the metrics can be scraped at the /metrics endpoint on port 9182.
At this point, Prometheus can consume the metrics by adding the following scrape_config to the Prometheus configuration 

```yaml 
scrape_configs:
    - job_name: "prometheus"
      static_configs: 
        - targets: ['localhost:9090']
    ...
    - job_name: "wmi_exporter"
      scrape_interval: 10s
      static_configs: 
        - targets: ['<windows-node1-ip>:9182', '<windows-node2-ip>:9182', ...]
```

Prometheus configuration is reloaded using 

```bash 

> ps aux | grep prometheus
> kill HUP <PID> 

```

A better and recommended way to add targets is to use a  Custom Resource Definition called ServiceMonitor, which comes as part of the [Prometheus operator](https://github.com/prometheus-operator/kube-prometheus/releases)] that provides the definition for a ServiceMonitor Object and a controller that will activate the ServiceMonitors we define and automatically build the required Prometheus configuration. 

The ServiceMonitor, which declaratively specifies how groups of Kubernetes services should be monitored, is used to define an application you wish to scrape metrics from within Kubernetes. Within the ServiceMonitor we specify the Kubernetes labels that the operator can use to identify the Kubernetes Service which in turn identifies the Pods, that we wish to monitor. 

In order to leverage the ServiceMonitor, create an Endpoint object pointing to specific Windows targets, a headless service and a ServiceMontor for the Windows nodes.

```yaml
apiVersion: v1
kind: Endpoints
metadata:
  labels:
    k8s-app: wmiexporter
  name: wmiexporter
  namespace: kube-system
subsets:
- addresses:
  - ip: NODE-ONE-IP
    targetRef:
      kind: Node
      name: NODE-ONE-NAME
  - ip: NODE-TWO-IP
    targetRef:
      kind: Node
      name: NODE-TWO-NAME
  - ip: NODE-THREE-IP
    targetRef:
      kind: Node
      name: NODE-THREE-NAME
  ports:
  - name: http-metrics
    port: 9182
    protocol: TCP

---
apiVersion: v1
kind: Service ##Headless Service
metadata:
  labels:
    k8s-app: wmiexporter
  name: wmiexporter
  namespace: kube-system
spec:
  clusterIP: None
  ports:
  - name: http-metrics
    port: 9182
    protocol: TCP
    targetPort: 9182
  sessionAffinity: None
  type: ClusterIP
  
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor ##Custom ServiceMonitor Object
metadata:
  labels:
    k8s-app: wmiexporter
  name: wmiexporter
  namespace: monitoring
spec:
  endpoints:
  - interval: 30s
    port: http-metrics
  jobLabel: k8s-app
  namespaceSelector:
    matchNames:
    - kube-system
  selector:
    matchLabels:
      k8s-app: wmiexporter
```

For more details on the operator and the usage of ServiceMonitor, checkout the official [operator](https://github.com/prometheus-operator/kube-prometheus) documentation. Note that Prometheus does support dynamic target discovery using many [service discovery](https://prometheus.io/blog/2015/06/01/advanced-service-discovery/) options.

