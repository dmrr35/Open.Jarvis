# Pull Request

## Summary

-

## Type of Change

- [ ] Bug fix
- [ ] Feature
- [ ] Documentation
- [ ] Tests
- [ ] Refactor
- [ ] Security or safety change

## Safety Checklist

- [ ] I did not commit real `.env` values, API keys, tokens, logs, or private user data.
- [ ] Risky actions such as file writes, process execution, plugins, browser control, and desktop automation are gated or documented.
- [ ] New user-facing text is in English.
- [ ] New behavior has tests or a clear reason why tests are not practical.

## Validation

- [ ] `python -m unittest discover -s tests -p "test_*.py"`
- [ ] `python -m ruff check .`
- [ ] `python project_audit.py`
- [ ] `python kontrol.py --no-pause`

## Notes

Add screenshots, logs, or follow-up tasks when useful. Do not include secrets.
