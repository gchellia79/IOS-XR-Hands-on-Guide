# 01. Commit configuration

!!! abstract "Goal"
    Stage changes in IOS XR target configuration, commit them with labels, and practise best-effort commit, confirmed commit, exclusive configuration sessions, and rollback.

## 1.1 Target configuration

In Cisco IOS XR, **target configuration** is the set of configuration changes you enter in configuration mode before applying them to the router's active (running) configuration.

### Exercise 1.1

Configure a loopback interface and verify the target configuration.

1. Enter configuration mode and configure a loopback interface.
2. Use `show` to view the target configuration.
3. When you are happy with the config, use `commit` to move it to running configuration.
4. Verify the running configuration.

```text
RP/0/RP0/CPU0:R1(config)#int lo11
RP/0/RP0/CPU0:R1(config-if)#ip address 11.11.11.11/32
RP/0/RP0/CPU0:R1(config)#commit label ?
  WORD  Label for this commit (must begin with an alphabet)
RP/0/RP0/CPU0:R1(config)#commit label ADDEDLOOPBACK0
Wed Oct 28 05:55:31.421 UTC
RP/0/RP0/CPU0:R1(config)#end
```

```text
RP/0/RP0/CPU0:R1(config)#show
Wed Oct 28 05:53:23.345 UTC
!! Building configuration...
!! IOS XR Configuration 26.1.1
interface Loopback11
 ipv4 address 11.11.11.11 255.255.255.255
!
end
RP/0/RP0/CPU0:R1(config)#
```

Verify the running configuration:

```text
RP/0/RP0/CPU0:R1#sh running-config interface lo11
Wed Oct 28 05:57:47.885 UTC
interface Loopback11
 ipv4 address 11.11.11.11 255.255.255.255
!
RP/0/RP0/CPU0:R1#
```

## 1.2 Commit best-effort

The `commit best-effort` operation merges the target configuration with the running configuration and commits only the valid changes.

Unlike an atomic commit, where the entire configuration is rolled back if any error occurs, a best-effort commit allows valid configuration items to be applied even if some items fail due to semantic errors.

### Exercise 1.2

Enter the following class maps and policy map, then commit.

```text
class-map DATA_1
 match dscp AF11
 exit

 class-map DATA_2
  match dscp AF21
  exit

policy-map CBWFQ
 class DATA_1
  bandwidth percent 10

 class DATA_3
  bandwidth percent 20
commit
```

1. Observe that the commit does not succeed, and note the error.
2. Use `show` to view the target config.
3. Use `show configuration failed` to understand why the commit did not succeed.
4. Use `commit best-effort` to commit only the valid configs.
5. Use `show run policy-map CBWFQ` to check the valid configs pushed to the device.

!!! warning "TODO"
  The source does not include the failed commit output.

## 1.3 Commit confirmed

In Cisco IOS XR, the `commit confirmed` command applies target configuration changes to the running configuration on a temporary basis, automatically rolling them back if they are not confirmed within a specified timeframe. This mechanism acts as a critical safety net against accidental lockouts, particularly when altering remote management or AAA configurations.

The default timer to roll back to the previous config is **10 minutes**. You can also give an explicit timer; if a second `commit` is not issued, the configuration rolls back.

### Exercise 1.3

Configure a loopback interface and use `commit confirmed` to commit the configs.

```text
int lo10
ip address 10.10.10.10/32

commit confirmed 60
```

| Parameter | Value | Notes |
| --- | --- | --- |
| Interface | `lo10` | Loopback used in this exercise |
| Address | `10.10.10.10/32` | Configured on the loopback |
| Confirmed timer | `60` | Seconds before automatic rollback if a second `commit` is not issued |

If `commit` is not issued, the configuration will roll back after 60 seconds.

Issue the second commit to push the configs to active/running configs:

```text
commit
```

## 1.4 Configure exclusive

In Cisco IOS XR, an exclusive configuration session allows a user to lock out all other users from committing configuration changes until the session is ended. While other users can still create or modify their own target configurations, they cannot commit those changes to the running configuration while an exclusive session is active.

### Exercise 1.4

1. Log in with username `cisco` and password `<password>`.
2. Establish an exclusive configuration session with `configure exclusive`.
3. Log in as `admin` with password `<password>`, try to configure something, commit, and observe the behaviour.

```text
RP/0/RP0/CPU0:R1#show users
Thu Oct 29 07:42:07.128 UTC
   Line            User                 Service  Conns   Idle        Location
*  vty0            cisco                ssh          0  00:00:03     198.18.134.23  Logged with cisco as username
   vty1            admin                ssh          0  00:01:07     198.18.134.23
RP/0/RP0/CPU0:R1#configure exclusive
Thu Oct 29 07:42:22.182 UTC
RP/0/RP0/CPU0:R1(config)#
```

From the second session:

```text
cisco@ubuntu:~$ ssh admin@198.18.131.1
RP/0/RP0/CPU0:R1#conf t
Thu Oct 29 07:42:31.268 UTC
Current Configuration Session  Line       User     Date                     Lock
00000000-00003057-00000000     vty0       cisco    Thu Oct 29 07:42:22 2026 *
RP/0/RP0/CPU0:R1(config)#
RP/0/RP0/CPU0:R1(config)#router bgp ?
  <1-65535>           2-byte AS number
  <1-65535>.          4-byte AS number in asdot (X.Y) format - first half (X)
  <65536-4294967295>  4-byte AS number in asplain format
RP/0/RP0/CPU0:R1(config)#router bgp 100
RP/0/RP0/CPU0:R1(config-bgp)#commit
Thu Oct 29 07:42:46.008 UTC

% Failed to commit .. Another configuration session
had a lock on the running configuration.
If you still want to commit your changes,
you may try the 'commit' command again.
RP/0/RP0/CPU0:R1(config-bgp)#
```

## 1.5 Rollback

In Cisco IOS XR, configuration rollback allows you to revert the router's running configuration to a previously committed configuration without manually restoring each command.

IOS XR maintains a history of committed configurations, which you can use to roll back changes. You can roll back using the label or up to a certain commit.

### Exercise 1.5

1. Use `rollback configuration last 1` to roll back to the previous commit.

Other useful CLIs for day-to-day operations:

- `show configuration commit changes last <Number of commits>` — view the configurations committed since the last number of commits.
- `show configuration commit list` — see all the previous committed config.
- `show cli history detail` — view all the CLI executed.
- `show context` and `show exceptions` — view crash information.

!!! warning "TODO"
  The source does not include sample output for rollback or these operational show commands.

## Next step

Continue with [02. IOS XR operations and monitoring tools](../02-operations-and-monitoring/index.md).
