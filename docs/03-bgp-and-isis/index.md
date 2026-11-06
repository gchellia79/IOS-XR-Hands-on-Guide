# 03. BGP and ISIS protocols configuration and troubleshooting

!!! abstract "Goal"
    Identify the lab topology and device roles used for BGP and ISIS configuration and troubleshooting.

## 3.1 Topology

The lab topology and management addresses are as follows.

![Lab topology](images/image01.png)

| S.No | Router | Hostname | Role | Mgmt-IP |
| --- | --- | --- | --- | --- |
| 1 | `xrd-1` | `R1` | PE (Provider Edge) | `198.18.131.1` |
| 2 | `xrd-2` | `R2` | P (Provider) | `198.18.131.2` |
| 3 | `xrd-3` | `R3` | P (Provider) | `198.18.131.3` |
| 4 | `xrd-4` | `R4` | PE (Provider Edge) | `198.18.131.4` |
| 5 | `Iol-4e0` | `CE-1` | CE (Customer Edge) | `198.18.131.5` |
| 6 | `Iol-4e1` | `CE-2` | CE (Customer Edge) | `198.18.131.6` |
| 7 | `Csr-1000v` | `RR-R7` | Route Reflector | `198.18.131.7` |

!!! note
    The original draft states this section will keep being added over the weekend. Configuration and troubleshooting steps are not in Draft 0.2 yet.

!!! warning "TODO"
    Add BGP and ISIS configuration and troubleshooting exercises when they are available in the Word source.

## Next step

You have finished the hands-on chapters currently in this guide. Return to the [home page](../index.md).
