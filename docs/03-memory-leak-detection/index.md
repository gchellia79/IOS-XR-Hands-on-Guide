# 03. Memory leak detection

!!! abstract "Goal"
    Take two memory snapshots around a trigger and use IOS XR memory compare to see which process allocated memory between them.

## 3.1 Memory leaks and snapshots

In Cisco IOS XR, a memory leak occurs when a process allocates memory for its own use but fails to return that memory to the free pool once it is no longer needed. This results in a situation where free memory appears to be "leaking" away.

There is a built-in tool in XR which computes automatically which process has allocated some memory between two snapshots. The objective is to find out if a process is leaking memory: requesting memory but never releasing it when it does not need it anymore.

If you feel some trigger is leaking the memory, you can detect a memory leak with the following method.

### Exercise 3.1

1. Take a baseline snapshot:

    ```text
    show memory compart start
    ```

2. Execute the trigger. It can be restarting the ISIS process or relearning the BGP routes.
3. Take the second snapshot and generate the report:

    ```text
    show memory compare end
    show memory compare report
    ```

`show memory compare report` shows differences between the baseline snapshot and the second snapshot.

!!! warning "TODO"
    The original step 1 uses `show memory compart start`. Steps 3 uses `show memory compare end` and `show memory compare report`. Confirm whether step 1 should be `show memory compare start`. No sample command output is included in the original notes.

## 3.2 Other useful memory commands

```text
show memory summary
show memory summary detail location all
```

## Next step

Continue with [04. Task groups](../04-task-groups/index.md).
