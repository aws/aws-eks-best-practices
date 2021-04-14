# Choosing a Windows Server Version and License [@momarcio]

There are two primary release channels available to Windows Server customers, the Long-Term Servicing Channel and the Semi-Annual Channel.

You can keep servers on the Long-Term Servicing Channel (LTSC), move them to the Semi-Annual Channel, or have some servers on either track, depending on what works best for your needs.

## Long-Term Servicing Channel (LTSC)

This is the release model you're already familiar with (formerly called the “Long-Term Servicing Branch”) where a new major version of Windows Server is released every 2-3 years. Users are entitled to 5 years of mainstream support and 5 years of extended support. This channel is appropriate for systems that require a longer servicing option and functional stability. Deployments of Windows Server 2019 and earlier versions of Windows Server will not be affected by the new Semi-Annual Channel releases. The Long-Term Servicing Channel will continue to receive security and non-security updates, but it will not receive the new features and functionality.

## Semi-Annual Channel

The Semi-Annual Channel is perfect for customers who are innovating quickly to take advantage of new operating system capabilities at a faster pace, focused in on containers and microservices. Windows Server products in the Semi-Annual Channel will have new releases available twice a year, in spring and fall. Each release in this channel will be supported for 18 months from the initial release.

Most of the features introduced in the Semi-Annual Channel will be rolled up into the next Long-Term Servicing Channel release of Windows Server. The editions, functionality, and supporting content might vary from release to release depending on customer feedback. In this model, Windows Server releases are identified by the year and month of release: for example, in 2017, a release in the 9th month (September) would be identified as version 1709. Fresh releases of Windows Server in the Semi-Annual Channel will occur twice each year. The support lifecycle for each release is 18 months.

## Should you keep servers on the LTSC or move them to the Semi-Annual Channel?

Microsoft recommends the version Semi-Annual Channel (SAC) for containers workload since it release news features at a faster pace. At AWS we recommend SAC versions for production environments, specifically Windows Server 2004 SAC and later.

There are technical specifics reasons why Windows Server 2004 SAC and later should be used:

* Direct Server Return (DSR) support.
* .NET Framework optimization.

**What is Direct Server Return?**
DSR is an implementation of asymmetric network load distribution in load balanced systems, meaning that the request and response traffic use a different network path.


**.NET Framework optimization.**
The majority of apps are ASP.NET-based web apps. In Windows Server, version 2004, the Server Core container image no longer optimizes the .NET Framework for performance, which saves a lot of space. Instead, .NET Framework optimization (aka “NGEN”) is done in the higher-level .NET Framework runtime image. 

.NET Framework NGEN optimization in containers is now more targeted to ASP.NET applications and Windows PowerShell scripts. In addition, the change to optimizing assemblies in the .NET Framework Runtime image (and not the Server Core base image) led to technical benefits that also resulted on a smaller reduce container size. 

For instance, a Windows Server core 2004 with .NET Framework has **3.98GB** on disk compared with **8.06GB** on Windows Server 2019 LTSC.

## Licensing

At Amazon Web Services (AWS), the EKS Optimized AMIs for Windows are based on the Datacenter version, which doesn't have a limitation on the numbers of containers running on a worker node. For more information: https://docs.microsoft.com/en-us/virtualization/windowscontainers/about/faq