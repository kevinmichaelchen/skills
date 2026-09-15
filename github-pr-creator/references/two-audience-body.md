# Canonical two-audience PR body

The example body begins below the divider.

---

## For humans

Closes #42

AI-assisted.

Moves command-line profile selection from an implicit environment default to
an explicit `--profile` option. Existing invocations continue to use the
default profile, so no migration is required.

```diff
- command -> environment default -> request
+ command --profile <name> -> resolved profile -> request
```

Validation: unit tests and the CLI smoke test passed. Packaging was not run.

<details>
<summary>For machines: exhaustive review context</summary>

## For machines

### Objective and context

Users could not select among configured profiles without changing process
environment. The change adds an explicit option while preserving the old
default when the option is absent.

### Implementation map

- The argument parser accepts `--profile <name>`.
- Configuration resolution prefers the option, then the existing environment
  value, then the default profile.
- Unit tests cover explicit, environment, and default resolution.

### Decisions and alternatives

The option overrides rather than replaces the environment variable to preserve
automation compatibility. Interactive selection remains out of scope.

### Behavioral and data impact

Existing commands are unchanged. Supplying an unknown profile now fails before
network access with the available profile names listed.

### Risk, rollout, and rollback

The main risk is precedence drift between the CLI and configuration loader.
Rollback is a code revert; no stored data or schema changes are involved.

### Validation evidence

- Unit tests: passed.
- CLI smoke test: passed for explicit and default profiles.
- Packaging: not run.

### Review guide

Review precedence in the resolver first, parser wiring second, and tests last.

### References and open questions

- Issue: #42.
- Open questions: none recorded.

</details>
