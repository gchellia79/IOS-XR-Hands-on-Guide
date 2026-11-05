# 02. IOS XR processes

!!! abstract "Goal"
    Identify the job ID, process ID, and thread ID of the ISIS process, restart the process, and observe which identifiers change.

## 2.1 Job ID, process ID, and thread ID

Get the process ID of the `isis` process.

```text
RP/0/RP0/CPU0:R1#show processes isis
Thu Oct 29 00:43:33.528 UTC
                  Job Id: 1003
                     PID: 16870
            Process name: isis
```

1. Note the job ID, process ID, and thread ID.
2. Restart the ISIS process using `process restart isis`.
3. Observe the job ID, process ID, and thread ID again. The job ID will not change, but the process ID and thread ID will change.

After the restart:

```text
RP/0/RP0/CPU0:R1#show processes isis
Thu Oct 29 00:49:50.975 UTC
                  Job Id: 1003
                     PID: 17432

JID    TID  Stack  pri  state        NAME             rt_pri
1003   17432    0K  20   Sleeping     IS-IS Managemen  0
1003   17433    0K  20   Sleeping     libsani_backing  0
1003   17434    0K  20   Sleeping     lwm_service_thr  0
1003   17435    0K  20   Sleeping     qsm_service_thr  0
```

| Parameter | Value | Notes |
| --- | --- | --- |
| Process | `isis` | Process inspected in this exercise |
| Job Id (before) | `1003` | Unchanged after restart |
| PID (before) | `16870` | Changes after `process restart isis` |
| Job Id (after) | `1003` | Same as before the restart |
| PID (after) | `17432` | New process ID |

!!! warning "TODO"
    The original paste includes `<Delete>` markers around the post-restart output. The first capture does not list thread IDs; the second capture lists `JID`/`TID` rows. Confirm whether any lines were intentionally removed.

## Next step

Continue with [03. Memory leak detection](../03-memory-leak-detection/index.md).
