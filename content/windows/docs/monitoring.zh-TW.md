# 監控

Prometheus 是 [CNCF 畢業項目](https://www.cncf.io/projects/)，無疑是與 Kubernetes 原生整合最受歡迎的監控系統。Prometheus 收集有關容器、Pod、節點和集群的指標。此外，Prometheus 利用 AlertsManager，允許您編程警報以在集群出現問題時警告您。Prometheus 將指標數據存儲為由指標名稱和鍵/值對識別的時間序列數據。Prometheus 包括一種名為 PromQL 的查詢語言，即 Prometheus 查詢語言。

下圖顯示了 Prometheus 指標收集的高級架構：

![Prometheus 指標收集](./images/prom.png)

Prometheus 使用拉取機制，並使用 exporters 從目標抓取指標，使用 [kube state metrics](https://github.com/kubernetes/kube-state-metrics) 從 Kubernetes API 抓取指標。這意味著應用程序和服務必須公開包含 Prometheus 格式指標的 HTTP(S) 端點。然後，Prometheus 將根據其配置定期從這些 HTTP(S) 端點拉取指標。

exporter 允許您將第三方指標作為 Prometheus 格式指標使用。Prometheus exporter 通常部署在每個節點上。有關 exporter 的完整列表，請參閱 Prometheus [exporters](https://prometheus.io/docs/instrumenting/exporters/)。雖然 [node exporter](https://github.com/prometheus/node_exporter) 適用於導出 linux 節點的主機硬件和操作系統指標，但它不適用於 Windows 節點。

在具有 Windows 節點的 **混合節點 EKS 集群**中，當您使用穩定的 [Prometheus helm chart](https://github.com/prometheus-community/helm-charts) 時，您將在 Windows 節點上看到失敗的 Pod，因為此 exporter 不適用於 Windows。您需要單獨處理 Windows 工作節點池，而是在 Windows 工作節點組上安裝 [Windows exporter](https://github.com/prometheus-community/windows_exporter)。

為了為 Windows 節點設置 Prometheus 監控，您需要下載並在 Windows 服務器本身上安裝 WMI exporter，然後在 Prometheus 配置文件的抓取配置中設置目標。
[releases page](https://github.com/prometheus-community/windows_exporter/releases) 提供了所有可用的 .msi 安裝程序，包括各自的功能集和錯誤修復。安裝程序將設置 windows_exporter 作為 Windows 服務，並在 Windows 防火牆中創建一個例外。如果在不帶任何參數的情況下運行安裝程序，exporter 將使用啟用的收集器、端口等的默認設置運行。

您可以查看本指南的 **調度最佳實踐**部分，該部分建議使用 taints/tolerations 或 RuntimeClass 僅選擇性地將 node exporter 部署到 linux 節點，而 Windows exporter 則在引導節點或使用您選擇的配置管理工具(例如 chef、Ansible、SSM 等)時安裝在 Windows 節點上。

請注意，與在 linux 節點上將 node exporter 安裝為 daemonset 不同，在 Windows 節點上 WMI exporter 安裝在主機本身上。exporter 將導出 CPU 使用率、內存和磁盤 I/O 使用率等指標，還可用於監控 IIS 站點和應用程序、網絡接口和服務。

windows_exporter 將默認公開啟用收集器的所有指標。這是收集指標以避免錯誤的推薦方式。但是，對於高級使用，windows_exporter 可以傳遞一個可選的收集器列表來過濾指標。Prometheus 配置中的 collect[] 參數允許您這樣做。

Windows 的默認安裝步驟包括在引導過程中下載並以參數(如您要過濾的收集器)啟動 exporter 作為服務。

```powershell
> Powershell Invoke-WebRequest https://github.com/prometheus-community/windows_exporter/releases/download/v0.13.0/windows_exporter-0.13.0-amd64.msi -OutFile <DOWNLOADPATH>

> msiexec /i <DOWNLOADPATH> ENABLED_COLLECTORS="cpu,cs,logical_disk,net,os,system,container,memory"
```

默認情況下，可以在端口 9182 上的 /metrics 端點抓取指標。
此時，Prometheus 可以通過將以下 scrape_config 添加到 Prometheus 配置來使用指標

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

使用以下命令重新加載 Prometheus 配置

```bash
> ps aux | grep prometheus
> kill HUP <PID>
```

一種更好、更推薦的添加目標方式是使用名為 ServiceMonitor 的自定義資源定義，它是 [Prometheus operator](https://github.com/prometheus-operator/kube-prometheus/releases) 的一部分，提供了 ServiceMonitor 對象的定義和一個控制器，該控制器將激活我們定義的 ServiceMonitor 並自動構建所需的 Prometheus 配置。

ServiceMonitor 聲明性地指定應如何監控 Kubernetes 服務組，用於定義您希望在 Kubernetes 中從中抓取指標的應用程序。在 ServiceMonitor 中，我們指定 Kubernetes 標籤，操作員可以使用這些標籤來識別 Kubernetes 服務，從而識別我們希望監控的 Pod。

為了利用 ServiceMonitor，請為指向特定 Windows 目標的 Endpoint 對象、無頭服務和 Windows 節點的 ServiceMontor 創建。

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

有關操作員和 ServiceMonitor 的使用的更多詳細信息，請查看官方 [operator](https://github.com/prometheus-operator/kube-prometheus) 文檔。請注意，Prometheus 支持使用許多 [service discovery](https://prometheus.io/blog/2015/06/01/advanced-service-discovery/) 選項進行動態目標發現。