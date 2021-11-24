# Logging

Containerized applications typically direct application logs to STDOUT. The container runtime traps these logs and does something with them - typically writes to a file. Where these files are stored depends on the container runtime and configuration. 

One fundamental difference with Windows pods is they do not generate STDOUT. You can run [LogMonitor](https://github.com/microsoft/windows-container-tools/tree/master/LogMonitor) to retrieve the ETW (Event Tracing for Windows), Windows Event Logs and other application specific logs from running Windows containers and pipes formatted log output to STDOUT. These logs can then be streamed using fluent-bit or fluentd to your desired destination such as Amazon CloudWatch.

The Log collection mechanism retrieves STDOUT/STDERR logs from Kubernetes pods. A [DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) is a common way to collect logs from containers. It gives you the ability to manage log routing/filtering/enrichment independently of the application. A fluentd DaemonSet can be used to stream these logs and any other application generated logs to a desired log aggregator.

More detailed information about log streaming from Windows workloads to CloudWatch is explained [here](https://aws.amazon.com/blogs/containers/streaming-logs-from-amazon-eks-windows-pods-to-amazon-cloudwatch-logs-using-fluentd/) 

## Logging Recomendations

The general logging best practices are no different when operating Windows workloads in Kubernetes. 

* Always log **structured log entries** (JSON/SYSLOG) which makes handling log entries easier as there are many pre-written parsers for such structured formats.
* **Centralize** logs - dedicated logging containers can be used specifically to gather and forward log messages from all containers to a destination
* Keep **log verbosity** down except when debugging. Verbosity places a lot of stress on the logging infrastructure and significant events can be lost in the noise.
* Always log the **application information** along with **transaction/request id** for traceability. Kubernetes objects do-not carry the application name, so for example a pod name `windows-twryrqyw` may not carry any meaning when debugging logs. This helps with traceability and troubleshooting applications with your aggregated logs.

    How you generate these transaction/correlation id's depends on the programming construct. But a very common pattern is to use a logging Aspect/Interceptor, which can use [MDC](https://logging.apache.org/log4j/1.2/apidocs/org/apache/log4j/MDC.html) (Mapped diagnostic context) to inject a unique transaction/correlation id to every incoming request, like so: 


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
