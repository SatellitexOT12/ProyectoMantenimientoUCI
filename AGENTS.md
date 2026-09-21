# AGENTS.md — SGUM-UCI

## Project identity

**SGUM-UCI** — Sistema de Gestión Universitaria de Mantenimiento (Universidad de las Ciencias Informáticas, La Habana, Cuba). Django 4.2 app renderizada en servidor dentro de `web_mantenimiento_uci/`. Una sola app: `usuarios`.

## Quick facts

- **App root**: `web_mantenimiento_uci/` (this is where `manage.py` lives; **not** the repo root)
- **Run tests**: `cd web_mantenimiento_uci && python manage.py test` (needs `sgum_dev.py` env with SQLite + Django 5.2 in the run venv)
- **Run server**: `cd web_mantenimiento_uci && python manage.py runserver`
- **CI**: `.github/workflows/django.yml` — runs from `web_mantenimiento_uci/` working directory, PostgreSQL 16 service
- **Migrations**: `web_mantenimiento_uci/usuarios/migrations/` (35+ migrations, already applied)
- **Tests**: `web_mantenimiento_uci/usuarios/tests/` (12 test files, `base.py` has `SGUMTestCase` with all 4 roles pre-created)
- **Test creds**: `sugm1234` / `dev_admin`, `dev_tecnico`, `dev_almacen`, `dev_solicitante`
- **Branch**: `rediseno-plano-uci`
- **Latest commit**: `78ca78a` (pre-redesign)

## Architecture

```
web_mantenimiento_uci/          ← Django project root (manage.py here)
├── web_mantenimiento_uci/      ← Django package (settings, urls, wsgi)
│   ├── settings.py             ← Env-var driven: DJANGO_SECRET_KEY, DJANGO_DEBUG, DB_*, etc.
│   ├── urls.py                 ← All URLs via usuarios.urls
│   └── wsgi.py
├── usuarios/                   ← The ONLY app
│   ├── models.py               ← Incidencia, Material, Personal, SolicitudSoporte, Reporte, etc.
│   ├── views.py                ← All views; permissions always via usuarios.permisos
│   ├── urls.py                 ← ~30 URL patterns
│   ├── permisos.py             ← Single source of truth for roles/permissions
│   ├── servicios.py            ← Business logic (sync reporte, assign tech, stock atomic)
│   ├── context_processors.py   ← roles/puede injected into ALL templates
│   ├── validaciones.py         ← Form validation
│   ├── estadisticas.py         ← Dashboard stats
│   ├── forms.py                ← Empty module (no CustomLoginForm; login uses manual field.html)
│   ├── templates/
│   │   ├── master.html         ← Base template; paints Django messages once
│   │   ├── login.html          ← Migrated to sg-* (sg-login, sg-login__photo, sg-login__form)
│   │   ├── navbar.html, footer.html, paginacion.html, 403.html, 404.html
│   │   └── partials/           ← page_head.html, field.html, icon.html, badge_*.html,
│   │   │                       ← modal_confirm.html, messages.html, search_form.html, etc.
│   │   └── soporte/            ← solicitar_soporte, bandeja_entrada_soporte, detalle_solicitud
│   ├── static/
│   │   ├── vendor/             ← Bootstrap 5.3.3, jQuery 3.7.1, Chart.js 4.4.7
│   │   ├── sgum/               ← tokens.css, sgum.css, sgum.js, login.css, pages/*.css/js
│   │   ├── js/                 ← scripts.js, notificaciones.js, validar*.js
│   │   ├── docs/               ← PDFs (manual, guía rápida, FAQ) + documentation ZIP
│   │   ├── logoSGUM.png, portada_fidel_2.jpeg
│   │   └── img/
│   └── tests/                  ← 12 test files, base.py has SGUMTestCase
├── DESIGN.md                   ← Generated design system spec (YAML tokens + 8 sections)
├── .impeccable/                ← Impeccable skill context (design.json, config.json, agents/)
├── .opencode/                  ← OpenCode skill integration (skills/impeccable/, commands/)
├── AGENTS.md                   ← This file
├── PRODUCT.md                  ← Product truth (single source of truth)
└── requirements.txt            ← Django==4.2.19, django-bootstrap-v5, openpyxl, selenium, pillow, psycopg2-binary
```

## Key constraints

- **No internet dependency**: Bootstrap/jQuery/Chart.js served locally from `static/vendor/`. Icons are SVG sprites, no Font Awesome / Bootstrap Icons. No CDN, no Google Fonts, no emoji as icons.
- **Spanish only**: `LANGUAGE_CODE = 'es'`, `TIME_ZONE = 'America/Havana'`. All UI text in Spanish.
- **Rol naming**: Django group `cliente` → displayed as "Solicitante" everywhere.
- **Product name**: "SGUM-UCI". Never "MainPage" or "Mantenimiento UCI".
- **POST-only for mutations**: All data-changing actions use POST + redirect + `django.contrib.messages`. `GET` to a POST URL returns 405.
- **Message tags**: `MESSAGE_TAGS` maps Django's `error` → `danger`. Use `success`, `info`, `warning`, `danger`.
- **Impeccable design system**: `static/sgum/tokens.css` and `static/sgum/sgum.css` define the "Plano de la UCI" visual system. **Do not edit `static/vendor/` or `static/sgum/` from within a page task.**

## Design system (Impeccable / "Plano de la UCI")

- **Product truth**: `PRODUCT.md` (single source of truth)
- **Design spec**: `DESIGN.md` at repo root — all tokens (YAML frontmatter) + 8 canonical sections (Overview, Colors, Typography, Layout, Elevation, Shapes, Components, Do's/Don'ts). Creative North Star: "The Architect's Draft".
- **Sidecar**: `.impeccable/design.json` — tonal ramps, component snippets, motion tokens, breakpoints
- **Config**: `.impeccable/config.json` — `{"schemaVersion": 1, "buildPath": "code"}`
- **CSS classes**: `sg-*` prefix (sg-sheet, sg-btn, sg-table, sg-field, sg-badge, sg-alert, sg-toast, sg-login, sg-foot, sg-help, etc.)
- **Tokens**: `--sg-ink` (#0b4a7f), `--sg-text` (#0b2a44), `--sg-sheet` (#f3f6f9), `--sg-cyan` (#2a94d4, marks only), `--sg-grid` (#c9d3dc)
- **Partials**: All in `templates/partials/`. Use `{% include 'partials/X' with ... %}`.
- **Craft floor rules**: No kickers/eyebrows, no card structures, no gradients in text, no `border-left/right` > 1px, no decorative shadows, no hero metrics, no section numbers.

## Login page (migrated)

The login page (`login.html`) is now fully migrated to the `sg-*` system:
- Uses `sg-login` grid layout (photo left, form right on desktop; stacked on mobile)
- `sg-login__photo` for the UCI fence photo (`portada_fidel_2.jpeg`)
- `sg-login__form` contains `sg-sheet` with `page_head.html` (title "Acceso")
- `sg-field` partials for username/password
- `sg-alert sg-alert--danger` for errors
- `sg-form-actions` for the submit button
- `sg-help` and `sg-foot` for help text and footer
- `data-sg-toggle-password` for the password toggle
- `field.html` Mode B (manual) is used — NOT Django form widgets
- `forms.py` has `CustomLoginForm` removed (dead code — login uses manual fields)
- CSS: `login.css` uses `.sg-login`, `.sg-login__photo`, `.sg-login__form`, `.sg-login__form` classes

## Testing specifics

- Test user password is `Sgum-Prueba-2025!` (in `usuarios/tests/base.py`: `CLAVE`)
- `SGUMTestCase` creates admin, tecnico (with Personal), almacenero, solicitante, superusuario
- Tests use `@override_settings(MEDIA_ROOT=tempfile)` and `MD5PasswordHasher` for speed
- Image uploads in tests: `imagen_png()` helper creates 8×8 PNG via Pillow
- Browser tests (`test_login_page.py`, Selenium) are **optional**: run with `SGUM_SELENIUM=1`
- `test_login_page.py` updated to check new `sg-*` selectors: `h1.sg-page-head__title`, `button[data-sg-toggle-password]`, `.sg-field__msg`, `[role="alert"]`
- **Test environment**: Need `sgum_dev.py` with SQLite settings. The run venv is at `$RUN/venv/` (Python 3.14, Django 5.2.17). Run with `PYTHONPATH="$RUN;..." DJANGO_SETTINGS_MODULE=sgum_dev`.
- `python manage.py test` from `web_mantenimiento_uci/`

## Django quirks

- **manage.py is NOT at repo root**: it's at `web_mantenimiento_uci/manage.py`. CI and all commands run from there.
- **Settings are env-var driven**: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`. Defaults exist for local dev (PostgreSQL, password `root`).
- **`staticfiles/` is a build artifact**: run `collectstatic` for production; do not commit or edit.
- **`media/`**: served by Django only when `DEBUG=True`. In production the web server serves it.
- **Context processor `usuarios.context_processors.roles`**: injects `is_admin`, `is_tecnico`, `is_almacenero`, `is_cliente`, `rol_display`, `puede` into ALL templates. `cliente` group = "Solicitante" display.
- **Permissions**: Always use `usuarios.permisos` — never duplicate permission logic in views.

## Impeccable skill (OpenCode)

- **Skill is available**: `skill({ name: "impeccable" })` — installed at `.opencode/skills/impeccable/`
- **Command**: `.opencode/skills/impeccable/scripts/impeccable context` to load session context
- **Windows**: use `.opencode/skills/impeccable/scripts/impeccable.cmd` instead of the shell script
- **Reference files**: `.opencode/skills/impeccable/reference/` contains all playbooks (craft-floor.md, operate.md, new-work.md, etc.)
- **Commands**: `init`, `document`, `shape`, `craft`, `extract`, `critique`, `audit`, `polish`, `bolder`, `quieter`, `distill`, `harden`, `onboard`, `adapt`, `animate`, `colorize`, `typeset`, `layout`, `delight`, `overdrive`, `clarify`, `optimize`, `live`, `generate`
- **Launcher**: `.opencode/skills/impeccable/scripts/impeccable` (or `.cmd` on Windows); the binary is at `.opencode/skills/impeccable/scripts/bin/windows-x64/impeccable.exe`
- **`/impeccable` command**: available in OpenCode; uses `.opencode/commands/impeccable.md`

## Important notes

- `PRODUCT.md` is the single source of truth for product decisions. Honor it over any assumption.
- `DESIGN.md` was generated by the Impeccable skill — all design tokens, components, and rules are captured there and in `.impeccable/design.json`. The foundation spec (`.impeccable/agents/foundation-handoff.md`) and `PRODUCT.md` remain the source of truth for product decisions.
- `.impeccable/hook.cache.json` tracks which files have been edited by the design agent and any findings.
- `.claude/settings.local.json` has Claude-specific permissions; not relevant to OpenCode.
- The `.opencode/` directory was created for OpenCode skill integration; it contains the impeccable skill adapted from the Claude Code plugin.
- `quitar_tecnico` modal form uses `action=""` — `incidencias.js` sets the correct action from `data-action` on the triggering button when the modal opens (`show.bs.modal` event listener).
- `403.html` and `404.html` use the full `sg-*` system (`sg-sheet`, `sg-page-head`, `sg-empty`).
- `forms.py` is effectively empty — no `CustomLoginForm`. The login page uses `field.html` Mode B (manual fields).
- Bootstrap CSS/JS still loaded in `master.html` for modals, dropdowns, and toasts on pages not yet fully migrated.

## Common commands

```bash
# Run server (from repo root)
cd web_mantenimiento_uci && python manage.py runserver

# Run tests (from web_mantenimiento_uci dir)
python manage.py test

# Run specific test file
python manage.py test usuarios.tests.test_flujo

# Run login page tests (Selenium, optional)
SGUM_SESELIUM=1 python manage.py test usuarios.tests.test_login_page

# Check migrations
python manage.py makemigrations --check --dry-run

# Create new migration
python manage.py makemigrations usuarios

# Apply migrations
python manage.py migrate

# Check project
python manage.py check

# Collect static
python manage.py collectstatic --noinput
```

## Vercel deployment

The project is deployed on Vercel (GitHub connected). Key files:
- `vercel.json` — framework preset `"python"`, build commands for migrate + collectstatic
- `server.py` — WSGI entry point exposing `application` (at repo root)
- `requirements.txt` — includes `gunicorn`, `dj-database-url`, `psycopg2-binary`

### Environment variables required on Vercel:
- `DJANGO_SECRET_KEY` — secure random key
- `DJANGO_DEBUG=0`
- `DJANGO_ALLOWED_HOSTS` — optional; auto-configured to `*.vercel.app` when `DATABASE_URL` is set
- Vercel Postgres integration automatically provides `DATABASE_URL`

### Database:
- Vercel uses **Postgres** via the Vercel Postgres integration
- `DATABASE_URL` is injected automatically by Vercel Postgres
- `settings.py` auto-detects `DATABASE_URL` and uses `dj-database-url` to parse it
- Falls back to `DB_*` env vars for local dev

### Troubleshooting 500 errors:
1. Verify `vercel.json` and `server.py` are committed to the branch
2. Check that Vercel Postgres is connected in the Vercel dashboard
3. Ensure `DJANGO_SECRET_KEY` is set in Vercel environment variables
4. Check Vercel deployment logs (`vercel logs` or dashboard)
5. Verify `requirements.txt` includes all dependencies (especially `dj-database-url`)

## Common commands
