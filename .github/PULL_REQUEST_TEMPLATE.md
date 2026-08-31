## Summary

<!-- Provide a clear and concise description of what this PR does and why. -->



## Type of change

<!-- Put an `x` in all boxes that apply. -->

- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that causes existing functionality to change)
- [ ] ♻️  Refactor (code change that neither fixes a bug nor adds a feature)
- [ ] 📦 Dependency update
- [ ] 🏗️  Infrastructure / DevOps change
- [ ] 📝 Documentation update
- [ ] 🔧 Configuration change

## Related issues / tickets

<!-- Link any related issues or Jira tickets.
     e.g. Closes #123, Relates to #456 -->



## Testing done

<!-- Describe the tests you ran to verify your changes. Include relevant details
     such as test configuration, commands run, and results. -->

- [ ] Unit tests pass locally (`pytest tests/ -v --tb=short`)
- [ ] Linting passes locally (`ruff check app/ tests/`)
- [ ] Manually tested the affected endpoints / behaviour
- [ ] Added new tests to cover the change (if applicable)

**Test output (paste or summarise):**

```
# paste relevant test output here
```

## Screenshots / recordings (if applicable)

<!-- Add screenshots or screen recordings for UI/API changes if helpful. -->



## Checklist

<!-- Put an `x` in all boxes that apply. Remove items that are not relevant. -->

- [ ] My code follows the project's style and conventions
- [ ] I have performed a self-review of my own code
- [ ] I have added / updated docstrings and inline comments where necessary
- [ ] I have updated the relevant documentation (README, ADRs, etc.)
- [ ] My changes do not introduce new linting or type-checking errors
- [ ] I have added tests that prove the fix / feature works
- [ ] New and existing tests pass locally with my changes
- [ ] Any dependent changes (migrations, config updates) are included in this PR
- [ ] I have checked for secrets or credentials accidentally committed
- [ ] I have updated `requirements.txt` if dependencies changed
- [ ] Kubernetes manifests are valid (kustomize build succeeds) if k8s/ was changed
- [ ] Terraform fmt and validate pass if terraform/ was changed

## Deployment notes

<!-- Anything the reviewer or on-call engineer should know before merging,
     e.g. database migrations, feature flags, environment variables needed. -->

- [ ] No special deployment steps required
- [ ] Requires the following environment variables / secrets: _(list them)_
- [ ] Requires a database migration: _(describe)_
- [ ] Requires a manual production step after merge: _(describe)_
