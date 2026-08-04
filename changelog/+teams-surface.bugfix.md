Rewrote the `teams` resource. It targeted `/teams/members`, `/teams/invitations`,
and `/teams/roles`, none of which exist; teams are CRUD at `/teams` with
membership managed per team.
