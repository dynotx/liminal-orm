Below, you will find the SOP Dyno Therapeutics follows for using Liminal to manage their Benchling schemas. This SOP assumes that you have already set up Liminal.

## Dyno Therapeutics Benchling Change Management SOP
(since 07.24.2024)

Dyno's Benchling tenants are set up as a Dev, Test, and Prod environments. All scientists and a select number of engineers have access to the PROD tenant, and all work is done in PROD. The Dev and Test tenants are used for development and testing of new features before merging into PROD. Liminal is used to keep the Test and Prod tenants in sync, while Dev is used for development/testing. Dyno uses a Slack channel for requesting changes to Benchling schemas. There is one Benchling Admin who is responsible for managing the Benchling environment.

Let's say a change has to be made to the Benchling schema...

### Pre-work

1. If the change is non-trivial, the Benchling Admin will modify the Liminal schemas in the Test tenant on the Benchling website. This allows for them to try changes and iterate in a safe environment, where they finally settle on the right schema change(s).

2. If they are confident that they know the exact changes needed to be made to the Liminal schemas in order to reflect their changes in TEST, they move onto the migration step, and only migrate the changes to PROD. However if they are not 100% confident, Liminal offers the ability to revert back to the original state automatically.

    **Reverting Test to the original state**

    a. Run `liminal autogenerate TEST 'description'`. This will generate a revision file, and create a list of operations to migrate TEST to be in sync with the schemas defined in code.

    b. Run `liminal upgrade TEST`. This will apply the operations to the TEST tenant.

    c. Delete the revision file created in step a.

    !!! question "Why delete the revision file?"
        Liminal only keeps of 1 linear history of changes. This "cleanup" migration is not part of the linear history, so it should be deleted.

### Migration

1. Make change(s) to the Liminal schemas in code.

2. Run `liminal autogenerate PROD 'description'`. This will generate a revision file, and create a list of operations to migrate PROD to be in sync with the schemas defined in code.

    !!! question "Why point to PROD?"
        The PROD tenant is the tenant that users interact with, meaning it should always be in sync with the code. This means when we autogenerate against PROD, we are comparing the Liminal schemas in code against the actual Benchling schemas in PROD. `autogenerate` creates a diff (a computed difference) and generates a list of operations for what needs to be done to make the PROD tenant match the Liminal schemas in code.

3. Create a PR in GitHub with schema changes and revision filee.

4. Run `liminal upgrade TEST`. Dyno keeps TEST in sync with PROD, for easy testing of new features. This runs the generated list of operations in the generated revision file against the TEST tenant.

5. Review the changes in TEST.

6. If the changes look good, run `liminal upgrade PROD`. This will apply the operations to the PROD tenant.

7. Add screenshots of successful migration to the PR.

8. Merge the PR.
