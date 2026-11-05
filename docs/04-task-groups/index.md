# 04. Task groups

!!! abstract "Goal"
    Create users and task groups in IOS XR, bind them to user groups, and check which privileges a user has.

## 4.1 User authentication and authorization

IOS XR has a strong embedded mechanism for user authentication and authorization. XR does not have the concept of privilege levels as IOS had. Embedded user task group management allows creation of different task groups. You can use a system-defined group, or you can define your own task group and assign granular privileges.

### Exercise 4.1

1. Create a user called `lab` and bind the usergroup `level_1`.
2. Log in as `lab` and check what privileges the user has.

Configs from the original notes:

```text
username test
 group operator
 secret <password>
```

| Parameter | Value | Notes |
| --- | --- | --- |
| Username in the steps | `lab` | Bound to usergroup `level_1` in the exercise text |
| Username in the config sample | `test` | Bound to group `operator` |
| Secret | `<password>` | Do not store a real secret in this guide |

!!! warning "TODO"
    Exercise 4.1 asks for user `lab` and usergroup `level_1`, but the config sample under this exercise is `username test` / `group operator`. Confirm which example to use. The original notes do not include login or privilege-check output.

## 4.2 Custom task group and user group

### Exercise 4.2

1. Define a taskgroup called `ISISREAD` and give only read permission for ISIS.
2. Define a usergroup called `LEVEL_1` and bind the taskgroup `ISISREAD`.
3. Create a user called `lab` and bind the usergroup `level_1`.
4. Log in as `lab` and check what privileges the user has.

```text
taskgroup ISISREAD
 task read isis

usergroup LEVEL_1
 taskgroup ISISREAD

username lab
 group LEVEL_1
 secret <password>
```

| Parameter | Value | Notes |
| --- | --- | --- |
| Task group | `ISISREAD` | `task read isis` only |
| User group | `LEVEL_1` | Bound to `ISISREAD` |
| Username | `lab` | Bound to `LEVEL_1` |
| Secret | `<password>` | Placeholder |

Use these commands to inspect authentication and group privileges:

```text
show user authentication method
show aaa usergroup operator
show aaa usergroup level_1
```

- `show user authentication method` — see by which method you are authenticated.
- `show aaa usergroup operator` — check what privileges the system-defined usergroup has.
- `show aaa usergroup level_1` — check what privileges the custom-defined usergroup has.

!!! note
    `cisco-support` has the highest privilege.

!!! warning "TODO"
    The original notes do not include output for the `show user` / `show aaa usergroup` commands.

## Next step

Continue with [05. Useful debugging commands](../05-useful-debugging-commands/index.md).
