# Choosing a Windows Server Version and License

There are two primary release channels available to Windows Server customers, the Long-Term Servicing Channel and the Semi-Annual Channel.

You can keep servers on the Long-Term Servicing Channel (LTSC), move them to the Semi-Annual Channel (SAC), or have some servers on either track, depending on what works best for your needs.

## Long-Term Servicing Channel (LTSC)

Formerly called the “Long-Term Servicing Branch”, this is the release model you are already familiar with where a new major version of Windows Server is released every 2-3 years. Users are entitled to 5 years of mainstream support and 5 years of extended support. This channel is appropriate for systems that require a longer servicing option and functional stability. Deployments of Windows Server 2019 and earlier versions of Windows Server will not be affected by the new Semi-Annual Channel releases. The Long-Term Servicing Channel will continue to receive security and non-security updates, only receiving select new features and functionality.

## Semi-Annual Channel (SAC)

Windows Server products in the Semi-Annual Channel have new releases available twice a year, in spring and fall. Each release in this channel is supported for 18 months from the initial release.

Most of the features introduced in the Semi-Annual Channel will be rolled up into the next Long-Term Servicing Channel release of Windows Server. The editions, functionality, and supporting content might vary from release to release depending on customer feedback. In this model, Windows Server releases are identified by the year and month or half of release: for example, in 2020, the release in the 4th month (April) is identified as version 2004. This naming changed with the last SAC release which is identified as 20H2.

## Which channel should I use?

Microsoft is moving to the LTSC as the primary release channel. The two current SAC builds will be supported until the end of their 18-month lifecycles ending 2021-12-14 for version 2004 and 2022-05-10 for version 20H2.

Important features optimized for Container workloads which originated in the SAC have been incorporated into the LTSC build:

* Direct Server Return (DSR) support. (available in the LTSC August 2020 Cumulative Update)
* .NET Framework optimization.

**What is Direct Server Return?**
DSR is an implementation of asymmetric network load distribution in load balanced systems, meaning that the request and response traffic use a different network path.

**.NET Framework optimization.**
The majority of apps are ASP.NET-based web apps. In Windows Server, version 2004, the Server Core container image no longer optimizes the .NET Framework for performance, which saves a lot of space. Instead, .NET Framework optimization (aka “NGEN”) is done in the higher-level .NET Framework runtime image. 

.NET Framework NGEN optimization in containers is now more targeted to ASP.NET applications and Windows PowerShell scripts. In addition, the change to optimizing assemblies in the .NET Framework Runtime image (and not the Server Core base image) led to technical benefits that also resulted on a smaller reduce container size. 

For instance, a Windows Server core 2004 with .NET Framework has **3.98GB** on disk compared with **8.06GB** on Windows Server 2019 LTSC.

## Licensing

At Amazon Web Services (AWS), the EKS Optimized AMIs for Windows are based on the Datacenter version, which doesn't have a limitation on the numbers of containers running on a worker node. For more information: https://docs.microsoft.com/en-us/virtualization/windowscontainers/about/faq
