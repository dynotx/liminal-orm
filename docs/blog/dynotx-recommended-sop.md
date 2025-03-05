Below, you will find the SOP Dyno Therapeutics follows for using Liminal to manage their Benchling schemas. This SOP assumes that you have already set up Liminal.

## Dyno Therapeutics Benchling Change Management SOP

Written: 07.24.2024
Author: Nirmit Damania

Dyno's Benchling tenants are set up as a Dev, Test, and Prod environments. All scientists and a select number of engineers have access to the PROD tenant, and all work is done in PROD. The Dev and Test tenants are used for development and testing of new features before merging into PROD. Liminal is used to keep the Test and Prod tenants in sync, while Dev is used for development/testing. Dyno uses a ticketing system through a Slack channel for Benchling schema change requests. The Benchling Admin is responsible for managing the Benchling environment and implementing the requested changes.

Let's say a change has to be made to a Benchling schema...

### Pre-work

1. If the change is non-trivial, the Benchling Admin will modify the Liminal schemas in the Dev tenant on the Benchling UI. This allows them to try changes and iterate in a safe environment until the final changes are settled.

2. Once they are confident in the exact changes needed to be made to the Liminal schemas, they move onto the migration step. As a safeguard, Liminal offers the ability to revert back to the original state automatically.

### Migration

1. Make change(s) to the Liminal schemas in code.

2. Run `liminal revision PROD 'description'`. This will generate a revision file, and create a list of operations to migrate PROD to be in sync with the schemas defined in code.

    !!! question "Why point to PROD?"
        The PROD tenant is the tenant that users interact with, meaning it should always be in sync with the code. This means when we autogenerate against PROD, we are comparing the Liminal schemas in code against the actual Benchling schemas in PROD. `autogenerate` creates a diff (a computed difference) and generates a list of operations for what needs to be done to make the PROD tenant match the Liminal schemas in code.

3. Create a PR in GitHub with schema changes and revision file.

4. Run `liminal upgrade TEST`. Dyno keeps TEST in sync with PROD, for easy testing of new features. This runs the generated list of operations in the generated revision file against the TEST tenant.

5. Review the changes in TEST.

6. If the changes look good, run `liminal upgrade PROD`. This will apply the operations to the PROD tenant.

7. Add screenshots of successful migration to the PR.

8. Merge the PR.

### Reverting Tenant to the current state

Let's say you are making some changes in the DEV tenant, but you need to revert back to the current state of your schemas defined in code. Liminal offers a way to quickly migrate the tenant back/forward to the current state.

1. Run `liminal revision TEST 'description'`. This will generate a revision file, and create a list of operations to migrate TEST to be in sync with the schemas defined in code.

2. Run `liminal upgrade TEST`. This will apply the operations to the TEST tenant.

3. Delete the revision file created in step 1.

!!! question "Why delete the revision file?"
    Liminal only keeps of 1 linear history of changes. This "cleanup" migration is not part of the linear history, so it should be deleted.
