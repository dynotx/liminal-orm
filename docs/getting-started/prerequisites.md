1. **Benchling Admin Account**: Liminal builds on top of Benchling's LIMS system. You will need access and credentials to an admin account for your Benchling tenant(s). Liminal needs credentials with full admin priveleges in order to manipulate Benchling schemas through their API.

2. **SSO optional**: A requirement for Liminal's migration service to work is for your Benchling tenant to have SSO optional or disabled. At the moment, a part of Liminal's API connection requires the admin email and password and is unable to be authenticated when SSO is required. You can message Benchling support to request that your tenant be configured to be SSO optional or disabled.

3. **Python**: Liminal is built using Python. You will need Python 3.9 or later installed on your machine.

### Notes

- It is important to note that Liminal only supports Benchling entity schemas and dropdowns at the moment. Future plans are to expand support to include all Benchling schema types and have 100% schema coverage. Leave a comment on the [Discussions](https://github.com/dynotx/liminal-orm/discussions) forum on your vote for what should be supported next, or what is blocking you from using Liminal!
