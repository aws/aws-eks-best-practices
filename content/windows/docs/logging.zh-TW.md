# 記錄

容器化應用程式通常會將應用程式日誌導向到 STDOUT。容器運行時會捕獲這些日誌並對它們進行某些操作 - 通常是寫入到文件中。這些文件存儲在哪裡取決於容器運行時和配置。

Windows pods 的一個根本區別是它們不會生成 STDOUT。您可以運行 [LogMonitor](https://github.com/microsoft/windows-container-tools/tree/master/LogMonitor) 來從運行中的 Windows 容器檢索 ETW (Windows 事件追蹤)、Windows 事件日誌和其他應用程式特定日誌,並將格式化的日誌輸出管道傳輸到 STDOUT。然後這些日誌可以使用 fluent-bit 或 fluentd 流式傳輸到您所需的目的地,如 Amazon CloudWatch。

日誌收集機制從 Kubernetes pods 檢索 STDOUT/STDERR 日誌。[DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) 是收集容器日誌的常見方式。它使您能夠獨立於應用程式管理日誌路由/過濾/enrichment。可以使用 fluentd DaemonSet 將這些日誌和任何其他應用程式生成的日誌流式傳輸到所需的日誌聚合器。

有關從 Windows 工作負載流式傳輸日誌到 CloudWatch 的更詳細信息,請參閱[這裡](https://aws.amazon.com/blogs/containers/streaming-logs-from-amazon-eks-windows-pods-to-amazon-cloudwatch-logs-using-fluentd/)

## 記錄建議

在 Kubernetes 中操作 Windows 工作負載時,一般的記錄最佳實踐並無不同。

* 始終記錄 **結構化日誌條目** (JSON/SYSLOG),這樣可以更輕鬆地處理日誌條目,因為有許多針對此類結構化格式的預寫解析器。
* **集中** 日誌 - 專用的日誌容器可以專門用於從所有容器收集和轉發日誌消息到目的地
* 除了調試時,保持 **日誌詳細程度** 較低。詳細程度會給日誌基礎設施帶來很大壓力,重要事件可能會被噪音淹沒。
* 始終記錄 **應用程式信息** 以及 **交易/請求 id** 以便追蹤。Kubernetes 對象不會攜帶應用程式名稱,例如 pod 名稱 `windows-twryrqyw` 在調試日誌時可能沒有任何意義。這有助於在您的聚合日誌中追蹤和故障排除應用程式。

    您如何生成這些交易/關聯 id 取決於編程構造。但一個非常常見的模式是使用日誌 Aspect/Interceptor,它可以使用 [MDC](https://logging.apache.org/log4j/1.2/apidocs/org/apache/log4j/MDC.html) (映射診斷上下文)為每個傳入請求注入唯一的交易/關聯 id,如下所示:

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
