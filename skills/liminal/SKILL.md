---
name: liminal
description: Operate the Liminal ORM CLI to manage Benchling schemas as code. Covers every `liminal` CLI command, two-step Benchling migrations (generate a revision file, get human verification, then upgrade), downgrades, generating schema files from a tenant, and propagating entity schema / dropdown changes safely across a codebase. Use when the user mentions Liminal, liminal-orm, Benchling schemas, Benchling migrations, revision files, dropdowns, entity schemas, results schemas, or runs any `liminal` command.
---

# Liminal ORM CLI

Liminal defines Benchling dropdowns, entity schemas, and results schemas as Python classes and migrates Benchling tenants to match them. Migrations follow an Alembic-style linear revision history stored in `liminal/versions/`. Full docs: https://dynotx.github.io/liminal-orm/

## Non-negotiable rules

1. **Every write to Benchling requires explicit human approval first.** Follow the [Benchling write approval gate](#benchling-write-approval-gate) before each one. No exceptions, including test and dev tenants.
2. **Migrations are always two steps with a human gate in between.** Run `liminal revision ...`, show the user the generated revision file, and **stop**. Only run `liminal upgrade ...` after the user explicitly approves that specific revision file. Never chain `revision` and `upgrade` in one command, script, or turn, even if the user asked to "just migrate".
3. **Never answer interactive prompts on the user's behalf** (e.g. piping `yes` into `liminal head --reset`). Ask the user and let them confirm.
4. **Never re-run a failed `upgrade` unchanged.** See [If an upgrade fails](#if-an-upgrade-fails).
5. **Never write secrets into `liminal/env.py`.** Read credentials from environment variables or a secrets manager.
6. **Run every command from the Liminal root**, the directory that contains `liminal/env.py`. The CLI resolves `liminal/` relative to the current working directory.

## Benchling write approval gate

### What counts as a Benchling write

- `liminal upgrade` and `liminal downgrade`
- `liminal revision` when the timeline contains only the initial revision (`liminal/versions/` has a single file). That run writes the initial revision_id to the tenant's `liminal_remote` schema. Later `revision` runs are read-only against Benchling.
- `liminal live-test ... -e/--execute`
- Any Python that changes Benchling: calling `.execute()` on a Liminal operation, `execute_operations(...)`, `upsert_remote_revision_id(...)`, or Benchling SDK create/update/archive/delete calls through `BenchlingService`. Don't use these to get around the CLI gate. Prefer the CLI for all schema changes.

Read-only commands (`current`, `head` without `--reset`, `diff`, `generate-files`, and `revision` after the first) don't need this gate. Their local side effects still follow the rules elsewhere in this file.

### Protocol

Before every Benchling write:

1. **Present an approval request** and nothing else actionable in the same message:

   ```
   Approval needed: Benchling write
   Tenant:    <tenant_name / alias> (<prod | test | dev>)
   Command:   <exact command to run>
   Revision:  <revision_id(s) and file path(s)>, if applicable
   Changes:   <numbered plain-language list of every operation that will run>
   Risks:     <data-bearing archives, required-field changes, type changes, downstream impact; "none identified" if none>
   Rollback:  <downgrade command, or "manual" if not reversible>
   Reply "approve" to run this exact command, or tell me what to change.
   ```

2. **Stop and end your turn.** Don't run the command, start it in the background, or move on to other steps while waiting.
3. **Run it only on an explicit affirmative reply** to that request, such as "approve", "yes, run it", or "go ahead". Treat silence, questions, "looks good so far", partial answers, and approvals with conditions you haven't addressed as **not approved**. Answer or adjust, then ask again.
4. **Report the outcome** after running: the CLI output summary, success or failure, and `liminal current <tenant>`. Then stop again before the next write.

### Scope of an approval

- An approval covers **one command, against one tenant, for the exact operations shown**. It doesn't carry over to another tenant (approving `test` doesn't approve `prod`), another revision, or a retry.
- **Ask again** if anything changes after approval: the revision file is edited, the descriptor changes (e.g. `head` now resolves to a newer revision), or a previous attempt failed.
- Instructions given ahead of time ("migrate everything", "you have permission to upgrade prod", "don't ask me again") are **not** a substitute for the per-write approval request. Acknowledge them, then still ask at each write.
- Never run Benchling writes unattended: no `--yes`-style piping, no background jobs, no CI changes, and no scripts that bundle several writes behind a single approval.

## Project layout

```
<root>/
  liminal/
    env.py                  # BenchlingConnection(s) + imports of all schema classes
    versions/               # revision files, one linear chain
  dropdowns/                # BaseDropdown subclasses
  entity_schemas/           # BaseModel subclasses, grouped by entity type
    custom_entities/ dna_sequences/ aa_sequences/ ...
  results_schemas/          # BaseResultsModel subclasses (no migrations)
```

`env.py` must import every dropdown and entity schema class, e.g. `from pizzahouse.dropdowns import *`. Liminal only sees classes that are imported. **Any Benchling schema or dropdown not imported is treated as deleted from code, and `revision` will generate `ArchiveEntitySchema` / `ArchiveDropdown` operations for it.**

Example `env.py`:

```python
import os

from pizzahouse.dropdowns import *  # noqa: F401,F403
from pizzahouse.entity_schemas import *  # noqa: F401,F403

from liminal.connection import BenchlingConnection, TenantConfigFlags

prod = BenchlingConnection(
    tenant_name="pizzahouse-prod",          # {tenant_name}.benchling.com
    tenant_alias="prod",                    # usable in place of tenant_name in the CLI
    api_client_id=os.environ["BENCHLING_PROD_CLIENT_ID"],
    api_client_secret=os.environ["BENCHLING_PROD_CLIENT_SECRET"],
    warehouse_connection_string=os.environ.get("BENCHLING_PROD_WAREHOUSE_URL"),  # optional
    config_flags=TenantConfigFlags(schemas_enable_change_warehouse_name=False),
)
test = BenchlingConnection(tenant_name="pizzahouse-test", tenant_alias="test", ...)
```

`api_client_id` and `api_client_secret` are required for every CLI command that connects to Benchling. `<tenant>` in the commands below is either a `tenant_name` or a `tenant_alias` from `env.py`.

## CLI reference

| Command | Connects to Benchling | Writes to Benchling (approval gate) | Writes local files |
|---|---|---|---|
| `liminal init` | no | no | yes |
| `liminal generate-files <tenant>` | yes | no | yes |
| `liminal current <tenant>` | yes | no | no |
| `liminal head [--reset]` | no | no | `--reset` deletes a file |
| `liminal diff <tenant>` | yes | no | no |
| `liminal revision <tenant> "<desc>"` | yes | **first run on a fresh timeline only** | yes |
| `liminal upgrade <tenant> <descriptor>` | yes | **yes** | no |
| `liminal downgrade <tenant> <descriptor>` | yes | **yes** | no |
| `liminal live-test <tenant> -e` | yes | **yes** | no |

### `liminal init`

Creates `liminal/`, `liminal/versions/` with an empty initial revision file, and a template `liminal/env.py`. It fails if `liminal/` already exists. Afterwards, fill in `env.py` and add the schema imports.

### `liminal generate-files <tenant> [-p PATH] [-d] [-es] [-rs] [-o]`

Reads the tenant's schemas and writes Python classes into `PATH/dropdowns/`, `PATH/entity_schemas/`, and `PATH/results_schemas/`, regenerating each `__init__.py`.

- `-p, --write-path PATH`: output directory (default `.`). It is created if missing.
- `-d, --dropdowns`, `-es, --entity-schemas`, `-rs, --results-schemas`: limit output to those types. With none of these flags, all three are generated.
- `-o, --overwrite`: **deletes the entire target subdirectory** (e.g. all of `entity_schemas/`) and regenerates it. This wipes hand-written code such as validators, relationships, and custom methods. Without `-o`, existing files are left alone and only new files are written.

Before using `-o`, check that `git status` is clean, warn the user that custom code will be lost, and review the diff afterwards. Generated files use relative imports (`from ...dropdowns import X`), so keep `dropdowns/` and `entity_schemas/` as siblings in the same package. Generate from the production tenant, which is the source of truth.

### `liminal current <tenant>`

Prints the revision_id the tenant is on. It is stored remotely in Benchling in the `liminal_remote` schema. This command is read-only and also a quick way to test connection setup.

### `liminal head [-r | --reset]`

Prints the latest local revision_id. It takes **no tenant argument**.

`--reset` deletes the head revision file, making its `down_revision` the new head, and asks for interactive confirmation. Only use it for a revision that has **not been applied to any tenant**, e.g. a revision the user rejected during review. The initial revision cannot be deleted.

### `liminal diff <tenant> [-d] [-es] [--json]`

Compares the dropdowns and entity schemas imported by `env.py` with the target Benchling tenant. This is read-only: it does not write to Benchling or create a revision file. Use it as the default preflight after changing schema code and before running `revision`.

- With no type flags, compares both dropdowns and entity schemas.
- `-d, --dropdowns`: compare only dropdowns.
- `-es, --entity-schemas`: compare only entity schemas.
- `--json`: writes a machine-readable report to stdout. The report contains the tenant, total difference count, per-type sync state, and each difference's model name, operation class, and description. Use this for CI or when a structured review is useful.
- Exit code `0`: the selected schema types are in sync.
- Exit code `2`: differences were found. This is an expected result, not a command failure; review the printed differences and generate a revision only when the user wants to migrate them.
- Exit code `1`: an error occurred, such as a configuration, connection, or import error.

`diff` uses the same comparison logic as `revision`, so it may identify archive operations when classes are missing from `env.py`. Investigate unexpected differences before creating a revision.

### `liminal revision <tenant> "<description>"`

Compares the classes imported in `env.py` against the tenant and writes `liminal/versions/<id>_<description>.py` with `upgrade()` and `downgrade()` operation lists. Covers dropdowns and entity schemas, not results schemas.

- Preconditions: the tenant's remote revision_id must equal the local head. Otherwise the command errors; upgrade that tenant first, or `head --reset` an unapplied head.
- On a timeline that only has the initial revision, this command writes that initial revision_id to the tenant's `liminal_remote` schema. That makes it a Benchling write, so go through the approval gate first.
- `--autogenerate` is on by default and cannot be disabled from the CLI. To hand-write operations, edit the generated file.
- Multiple tenants share one timeline: generate against production (or whichever tenant acts as prod), then apply to every tenant with `upgrade`.

### `liminal upgrade <tenant> <descriptor>`

Validates and then executes the `upgrade()` operations of each revision from the tenant's current revision up to the target, then updates the remote revision_id. Descriptor values:

- `head`: upgrade to the latest local revision
- `<revision_id>`: e.g. `c3a9cd009713`
- `+N`: upgrade N revisions forward, e.g. `+1`

### `liminal downgrade <tenant> <descriptor>`

Executes the `downgrade()` operations of each revision, newest first, back to the target. Descriptor values:

- `<revision_id>`: the revision to land on
- `-N`: go back N revisions, e.g. `-1`

This is a Benchling write. Use the approval gate and list every `downgrade()` operation that will run.

### Hidden and deprecated commands

- `liminal autogenerate ...`: deprecated and always raises an error. Use `liminal revision`.
- `liminal live-test <tenant> [-es | -d] [-e]`: maintainer smoke test that creates, updates, and archives throwaway `test_dont_touch_*` schemas or dropdowns. It is a dry run unless `-e/--execute` is passed. Do not run it unless the user explicitly asks. `-e` is a Benchling write that needs the approval gate, and never run it against production.

Benchling's v3 API is rate limited, so `generate-files`, `revision`, and `upgrade` can take several minutes on large tenants. Let them finish; don't kill and retry them.

## Groundwork: making schema changes in code

Do this before generating a revision. A Benchling schema change is also a code change: the Python attribute name of a column **is** its warehouse column name, and other code depends on it.

### 1. Pin down the exact change

Restate the requested change as concrete edits and confirm with the user if anything is ambiguous. For example: "Archive the `dough` field on `pizza`; add an optional integer field `Slice Count` (`slice_count`)." If the change is non-trivial, suggest the user prototype it in a dev tenant through the Benchling UI first, then encode the final version in code.

### 2. Edit the schema classes

| Change | How to express it in code |
|---|---|
| Add field | Add a `Column(...)` attribute. Unless `schemas_enable_change_warehouse_name=True`, the attribute name must equal `to_snake_case(name)`. Position in the class sets the field order. |
| Archive field | Delete the attribute, or keep it with `_archived=True` if code still needs to read historical warehouse data. |
| Change display name only | Edit `name=` and keep the attribute name, which keeps the existing warehouse name. |
| Rename warehouse name | Requires `schemas_enable_change_warehouse_name=True` on the connection. Rename the attribute / `warehouse_name`, then **hand-edit the revision file** (see review checklist). |
| Change type, `is_multi`, `required`, `tooltip`, `decimal_places` | Edit the `Column` arguments. |
| Change `unit_name` | **Not possible** once set. Archive the field and add a new one. |
| Reorder fields | Reorder the attribute lines. |
| Add / archive schema | Add or delete the class, and make sure it is (or stops being) imported by `env.py`. `_archived=True` on `SchemaProperties` keeps an archived schema queryable. |
| Dropdown option add / archive / reorder | Edit `__allowed_values__`. Order matters. |
| Rename dropdown option | Edit the value in `__allowed_values__`, then **hand-edit the revision file**. Autogenerate produces an archive + create pair. |
| Rename dropdown | Edit `__benchling_name__`, then **hand-edit the revision file**. Autogenerate produces `CreateDropdown` + `ArchiveDropdown`. |
| Entity link target | `entity_link=` is the target schema's **warehouse_name** string. |
| Name template | Edit `__name_template__`. `FieldPart(wh_field_name=...)` references a warehouse field name. |

### 3. Propagate the change across the codebase

Search the whole repository, not just the schema package, for every identifier the change touches: the class name, the attribute/warehouse name, the old display name, the dropdown class, and each affected dropdown option string. Typical places that need updating:

- **The model's own `__init__`**: generated classes define an `__init__` that takes the fields as parameters. Add, remove, or rename parameters to match, and keep `SomeDropdown.validate(value)` calls in sync.
- **Relationships**: `single_relationship("Target", column)` / `multi_relationship(...)` take the column object and the target class name.
- **Validators**: `@liminal_validator` methods that read `self.<field>`.
- **Other schemas**: `entity_link="<warehouse_name>"`, `dropdown=<DropdownClass>`, `constraint_fields={...}`, and name templates in other classes, including results schemas.
- **Warehouse queries**: SQLAlchemy queries (`Model.field`), `.df()` column names, and any raw SQL, dbt models, or dashboards that reference warehouse table/column names.
- **Benchling SDK / app code**: payloads that use field **display names** or literal dropdown option values (e.g. `fields={"Cook Time": ...}`), and Benchling apps, automations, or integrations that read those fields.
- **Tests and fixtures** that construct models or assert on field names.
- **Package exports**: `__init__.py` files and `env.py` imports for new or deleted modules.

List anything outside the repository that may be affected (dashboards, other services, Benchling-side configuration) and tell the user. You cannot fix those yourself.

### 4. Verify the code before generating the revision

- Run the project's tests, type checker, and linter if they exist.
- Confirm the schema package still imports cleanly; any import error in `env.py` breaks every `liminal` command.
- Show the user the diff of the schema and dependent code changes.

## Two-step migration workflow

Copy this checklist and track progress:

```
- [ ] Groundwork done: schema edits + codebase propagation + tests pass
- [ ] Preflight: `liminal current <tenant>` == `liminal head`
- [ ] Inspect `liminal diff <tenant>` output; investigate every unexpected difference
- [ ] Step 1: `liminal revision <tenant> "<description>"` (approval gate first if this is a fresh timeline)
- [ ] Review: revision file checked against the review checklist
- [ ] GATE: user explicitly approved the revision file contents
- [ ] GATE: approval request for `liminal upgrade <test_tenant> <revision_id>` approved
- [ ] Step 2: upgrade test tenant → user verifies in Benchling
- [ ] GATE: approval request for `liminal upgrade <prod_tenant> <revision_id>` approved
- [ ] Step 2: upgrade prod tenant → user verifies in Benchling
- [ ] `liminal current <tenant>` shows the new revision on every tenant
- [ ] Schema changes + code changes + revision file committed together in one PR
```

### Preflight

Run `liminal current <tenant>` and `liminal head`. They must match before generating a revision. If they don't, there are pending revisions; apply those first (with their own review) or stop and ask the user. Then run `liminal diff <tenant>` and review every reported difference. A `diff` exit code of `2` means differences were found and is expected when code has changed; it is not an error.

### Step 1: generate the revision file

```bash
liminal revision prod "archive dough field on pizza"
```

Open the generated file in `liminal/versions/`. It looks like:

```python
import liminal.external as b

revision = "c3a9cd009713"
down_revision = "d28335bffaba"

def upgrade() -> list[b.BaseOperation]:
    return [b.ArchiveEntitySchemaField('pizza', 'dough')]

def downgrade() -> list[b.BaseOperation]:
    return [b.UnarchiveEntitySchemaField('pizza', 'dough')]
```

If the output says dropdowns and entity schemas are in sync and `upgrade()` is empty, there is nothing to migrate. Tell the user and offer to remove the empty revision with `liminal head --reset`.

### Review checklist

Go through every operation and report the results to the user:

- [ ] Every operation in `upgrade()` maps to a change the user asked for, and nothing they asked for is missing.
- [ ] **No unexpected `ArchiveEntitySchema` / `ArchiveDropdown` / `ArchiveEntitySchemaField` / `ArchiveDropdownOption` operations.** These usually mean a class isn't imported in `env.py`, or the code is stale compared with what someone changed in the Benchling UI. If you find any, stop and investigate. Don't edit them away without understanding why.
- [ ] **Renames:** autogenerate cannot detect renames of warehouse names, dropdown names, or dropdown options. Each one appears as a create + archive pair, which would lose the link to existing data. Replace the pair with an update operation in `upgrade()`, and its inverse (old and new swapped) in `downgrade()`:
  - schema: `b.UpdateEntitySchema('old_wh', b.BaseSchemaProperties(warehouse_name='new_wh'))`
  - field: `b.UpdateEntitySchemaField('schema_wh', 'old_field_wh', b.BaseFieldProperties(warehouse_name='new_field_wh'))`
  - dropdown: `b.UpdateDropdownName('Old Name', 'New Name')`
  - dropdown option: `b.UpdateDropdownOption('Dropdown Name', 'Old Option', 'New Option')`
- [ ] `downgrade()` is the exact inverse of `upgrade()`, in reverse order. Fix it if you hand-edited `upgrade()`.
- [ ] `down_revision` equals the previous head and the tenant's current revision.
- [ ] Flag risky changes to the user: archiving fields or options that hold data, making fields required, changing field types, and anything that affects downstream consumers identified in groundwork step 3.

Then **stop**. Present a plain-language summary of each operation, the file path, and any flagged risks, and ask the user to confirm. If they reject it, edit the code or the revision file and review again, or delete the unapplied revision with `liminal head --reset` (the user confirms the prompt).

### Step 2: apply the revision (one approval per tenant)

Approving the revision file's contents doesn't approve running it. Each upgrade needs its own approval request.

Apply to the test tenant first and target the specific reviewed revision_id rather than `head`, so nothing unreviewed sneaks in. Send the approval request, stop, and run this only after explicit approval:

```bash
liminal upgrade test c3a9cd009713
```

Report the result and have the user verify the change in the Benchling UI. Then send a **new** approval request for production, stop, and run this only after explicit approval:

```bash
liminal upgrade prod c3a9cd009713
```

Then run `liminal current <tenant>` on each tenant to confirm it is on the new revision. Remind the user to commit the schema changes, dependent code changes, and the revision file together in one PR, and to attach evidence of the successful migration.

If several revisions are pending on a tenant, prefer applying them one at a time with `+1`. See the next section for why.

### If an upgrade fails

The remote revision_id is updated only after **every** targeted revision succeeds. After a failure, the tenant's recorded revision is unchanged, even though some operations, or even whole earlier revisions in a multi-revision upgrade, may already have been applied.

1. Do not re-run the same command. Re-executing operations that already succeeded is unsafe.
2. Show the user the error output. The CLI prints which numbered operation failed.
3. Propose commenting out the operations in `upgrade()` that already succeeded. After making the edit, send a new approval request listing only the operations that will now run, and stop. Run `liminal upgrade` again for that revision only after explicit approval.
4. Afterwards, restore the commented-out operations in the file so the revision is complete for other tenants, and confirm with `liminal current`.

## Downgrade workflow

1. Run `liminal current <tenant>` and `liminal head`, and identify the target revision.
2. Send an approval request listing the `downgrade()` operations of every revision that will be reverted, newest first, and stop.
3. After explicit approval, run `liminal downgrade <tenant> -1` (or `<revision_id>`). Do the test tenant first, and get a separate approval for each further tenant.
4. If the code should match the downgraded state, revert the code changes too. Otherwise the next `revision` will try to re-apply them.

## Resyncing a dev or test tenant to code

To bring a scratch tenant back in line with the code after experimenting in the UI:

1. Make sure the tenant is at the local head (`liminal current` == `liminal head`).
2. `liminal revision <dev_tenant> "resync dev"`, then review the file and get approval as usual.
3. Send an approval request, stop, and after explicit approval run `liminal upgrade <dev_tenant> <revision_id>`.
4. This revision is not part of the shared history. With the user's approval, delete it with `liminal head --reset` and don't commit it.

## Results schemas

Liminal does not migrate results schemas. Edit them in the Benchling UI, then regenerate the classes:

```bash
liminal generate-files <tenant> -rs          # only writes new files
liminal generate-files <tenant> -rs -o       # deletes and rebuilds results_schemas/
```

## Troubleshooting

| Error | Fix |
|---|---|
| `/liminal directory not found at current working directory` | `cd` to the Liminal root, or run `liminal init`. |
| `BenchlingConnection with tenant name or alias X not found` | Use a `tenant_name`/`tenant_alias` defined in `env.py`. |
| `api_client_id and api_client_secret must be provided` | Set both on that `BenchlingConnection`. |
| `...not up to date with the local head revision` (on `revision`) | Upgrade that tenant first, or `liminal head --reset` an unapplied head. |
| `revision_id ... does not exist within your revision timeline` | The tenant was migrated from another branch or a deleted revision file. Restore the missing file before doing anything else. |
| `Multiple revisions found that include X as their down_revision_id` | Two branches each added a revision. Point one file's `down_revision` at the other's `revision`, but only if neither has been applied, and confirm with the user. |
| Warehouse name validation error | The change needs `schemas_enable_change_warehouse_name=True`, a tenant flag set by Benchling support. |
| HTTP 429 / slow commands | Benchling v3 API rate limits. Wait and let the command finish. |
