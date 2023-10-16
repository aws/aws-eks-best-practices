<!-- # Logging -->
# 로깅

<!-- Containerized applications typically direct application logs to STDOUT. The container runtime traps these logs and does something with them - typically writes to a file. Where these files are stored depends on the container runtime and configuration.  -->
컨테이너화된 애플리케이션은 일반적으로 애플리케이션 로그를 STDOUT으로 전달합니다. 컨테이너 런타임은 이러한 로그를 트랩하여 특정 작업(일반적으로 파일에 쓰기)을 수행합니다. 이러한 파일이 저장되는 위치는 컨테이너 런타임 및 구성에 따라 다릅니다. 

<!-- One fundamental difference with Windows pods is they do not generate STDOUT. You can run [LogMonitor](https://github.com/microsoft/windows-container-tools/tree/master/LogMonitor) to retrieve the ETW (Event Tracing for Windows), Windows Event Logs and other application specific logs from running Windows containers and pipes formatted log output to STDOUT. These logs can then be streamed using fluent-bit or fluentd to your desired destination such as Amazon CloudWatch. -->
윈도우 파드와의 근본적인 차이점 중 하나는 STDOUT을 생성하지 않는다는 것입니다.[LogMonitor](https://github.com/microsoft/windows-container-tools/tree/master/LogMonitor)를 실행하여 실행 중인 Windows 컨테이너에서 ETW (Windows용 이벤트 추적), Windows 이벤트 로그 및 기타 애플리케이션별 로그를 검색하고 형식이 지정된 로그 출력을 STDOUT으로 전송할 수 있습니다. 그런 다음 플루언트비트 또는 fluentd를 사용하여 Amazon CloudWatch와 같은 원하는 목적지로 이러한 로그를 스트리밍할 수 있습니다.

<!-- The Log collection mechanism retrieves STDOUT/STDERR logs from Kubernetes pods. A [DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) is a common way to collect logs from containers. It gives you the ability to manage log routing/filtering/enrichment independently of the application. A fluentd DaemonSet can be used to stream these logs and any other application generated logs to a desired log aggregator. -->
로그 수집 메커니즘은 쿠버네티스 파드에서 STDOUT/STDERR 로그를 검색한다.[데몬셋](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)은 컨테이너에서 로그를 수집하는 일반적인 방법입니다.애플리케이션과 독립적으로 로그 라우팅/필터링/강화를 관리할 수 있습니다. fluentd DaemonSet을 사용하여 이러한 로그와 기타 애플리케이션 생성 로그를 원하는 로그 수집기로 스트리밍할 수 있습니다.

<!-- More detailed information about log streaming from Windows workloads to CloudWatch is explained [here](https://aws.amazon.com/blogs/containers/streaming-logs-from-amazon-eks-windows-pods-to-amazon-cloudwatch-logs-using-fluentd/)  -->
Windows 워크로드에서 CloudWatch로의 로그 스트리밍에 대한 자세한 내용은 [AWS 블로그](https://aws.amazon.com/blogs/containers/streaming-logs-from-amazon-eks-windows-pods-to-amazon-cloudwatch-logs-using-fluentd/)를 참조하세요. 

<!-- ## Logging Recomendations -->
## 로깅 권장 사항

<!-- The general logging best practices are no different when operating Windows workloads in Kubernetes.  -->
쿠버네티스에서 Windows 워크로드를 운영할 때 일반적인 로깅 모범 사례는 크게 다르지 않습니다. 

<!-- * Always log **structured log entries** (JSON/SYSLOG) which makes handling log entries easier as there are many pre-written parsers for such structured formats. -->
<!-- * **Centralize** logs - dedicated logging containers can be used specifically to gather and forward log messages from all containers to a destination -->
<!-- * Keep **log verbosity** down except when debugging. Verbosity places a lot of stress on the logging infrastructure and significant events can be lost in the noise. -->
<!-- * Always log the **application information** along with **transaction/request id** for traceability. Kubernetes objects do-not carry the application name, so for example a pod name `windows-twryrqyw` may not carry any meaning when debugging logs. This helps with traceability and troubleshooting applications with your aggregated logs. -->
* 항상 **구조화된 로그 항목** (JSON/SYSLOG) 을 기록하면 이러한 구조화된 형식에 대해 미리 작성된 파서가 많기 때문에 로그 항목을 더 쉽게 처리할 수 있습니다.
* **중앙 집중화** 로그 - 전용 로깅 컨테이너를 사용하여 모든 컨테이너에서 로그 메시지를 수집하고 목적지로 전달할 수 있습니다.
* 디버깅할 때를 제외하고는 **로그 상세 정보**를 줄이십시오.상세 정보는 로깅 인프라에 많은 부담을 주고 노이즈로 인해 중요한 이벤트가 손실될 수 있습니다.
* 추적을 위해 항상**애플리케이션 정보**를 **거래/요청 ID**와 함께 기록하십시오.쿠버네티스 오브젝트에는 애플리케이션 이름이 포함되지 않으므로, 예를 들어 로그를 디버깅할 때 포드 이름 `windows-twryrqyw`는 아무런 의미가 없을 수 있습니다.이렇게 하면 추적성이 향상되고 집계된 로그로 애플리케이션 문제를 해결하는 데 도움이 됩니다.

    <!-- How you generate these transaction/correlation id's depends on the programming construct. But a very common pattern is to use a logging Aspect/Interceptor, which can use [MDC](https://logging.apache.org/log4j/1.2/apidocs/org/apache/log4j/MDC.html) (Mapped diagnostic context) to inject a unique transaction/correlation id to every incoming request, like so:  -->
    이러한 트랜잭션/상관 관계 ID를 생성하는 방법은 프로그래밍 구조에 따라 다릅니다. 하지만 매우 일반적인 패턴은 다음과 같이 [MDC](https://logging.apache.org/log4j/1.2/apidocs/org/apache/log4j/MDC.html)(매핑된 진단 컨텍스트)를 사용하여 들어오는 모든 요청에 고유한 트랜잭션/상관 관계 ID를 삽입할 수 있는 로깅 Aspect/Interceptor를 사용하는 것입니다.

```java   
import org.slf4j.MDC;
import java.util.UUID;
Class LoggingAspect { //interceptor

    @Before(value = "execution(* *.*(..))")
    func before(...) {
        transactionId = generateTransactionId();
        MDC.put(CORRELATION_ID, transactionId);
    }

    func generateTransactionId() {
        return UUID.randomUUID().toString();
    }
}
```
