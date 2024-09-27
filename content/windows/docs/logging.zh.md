# 日志记录

容器化应用程序通常将应用程序日志直接输出到STDOUT。容器运行时捕获这些日志并对其执行某些操作 - 通常是写入文件。这些文件存储在何处取决于容器运行时和配置。

Windows pod的一个根本区别是它们不会生成STDOUT。您可以运行 [LogMonitor](https://github.com/microsoft/windows-container-tools/tree/master/LogMonitor) 来从运行中的Windows容器检索ETW (Windows事件跟踪)、Windows事件日志和其他应用程序特定日志，并将格式化的日志输出管道输出到STDOUT。然后可以使用fluent-bit或fluentd将这些日志流式传输到您期望的目的地，如Amazon CloudWatch。

日志收集机制从Kubernetes pod中检索STDOUT/STDERR日志。[DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) 是收集容器日志的常用方式。它使您能够独立于应用程序管理日志路由/过滤/丰富。可以使用fluentd DaemonSet将这些日志和任何其他应用程序生成的日志流式传输到所需的日志聚合器。

有关从Windows工作负载流式传输日志到CloudWatch的更多详细信息，请参阅[此处](https://aws.amazon.com/blogs/containers/streaming-logs-from-amazon-eks-windows-pods-to-amazon-cloudwatch-logs-using-fluentd/)

## 日志记录建议

在Kubernetes中运行Windows工作负载时，一般的日志记录最佳实践并无不同。

* 始终记录**结构化日志条目**(JSON/SYSLOG),这使处理日志条目更加容易，因为有许多针对此类结构化格式的预编写解析器。
* **集中**日志 - 可以使用专用的日志容器专门收集和转发所有容器的日志消息到目的地
* 除非在调试时，否则保持**日志详细程度**较低。详细程度会给日志基础设施带来很大压力，重要事件可能会被噪音淹没。
* 始终记录**应用程序信息**以及**事务/请求ID**以便追溯。Kubernetes对象不携带应用程序名称，例如pod名称`windows-twryrqyw`在调试日志时可能没有任何意义。这有助于在聚合日志中追溯和排查应用程序问题。

    生成这些事务/关联ID的方式取决于编程构造。但一种非常常见的模式是使用日志Aspect/Interceptor,它可以使用[MDC](https://logging.apache.org/log4j/1.2/apidocs/org/apache/log4j/MDC.html)(映射诊断上下文)为每个传入请求注入唯一的事务/关联ID，如下所示：

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