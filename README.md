# SAFG World

Community submissions for SAFG:RPG. Fork this repository and open a pull request.

**New here? [Read the step-by-step player guide](docs/PLAYER-GUIDE.md)** for
forking, uploads, PRs and requesting in-game approval.

## Gang/squad skin shaders and base maps

Leaders request these in **Level Settings > Skins & Base** in game. They use
organization rewards, not donation points. Keep the organization name exactly
as shown in game. Each request needs a unique release key and its SAFG-World PR
URL. Two approvals are required: GitHub review/merge by InfinityPR, followed by
in-game management approval after the publisher has deployed the release.
Unmerged PRs never activate anything. Pending/denied edits keep the old approved
settings active.

### Skin shaders

Use `shaders/<unique-release-key>/request.json` and a PNG/DDS livery texture;
copy `examples/organization-skin-request.json`. Set `organization` and the exact
GTA skin `model`. Organization requests use `target: "skin"`, `kind: "livery"`.
The optional FX follows the existing shader review rules below.

In game, enter the release key and PR URL against the corresponding spawn/skin
slot. Shaders unlock with that spawn (Levels 1, 5 and 7); its second skin also
requires Level 4. Approved organization level payments and spawn rank permissions
still apply. Changing the spawn's skin requires a release for the new model.
Shaders do not grant a model or spawn permission. Personal donated liveries keep
precedence over organization liveries.

### Base maps

Create `bases/<unique-release-key>/request.json` and a converter-exported `.lua`
file; copy `examples/base-request.json` and `examples/base.lua`. The schema is:
`organization`, `github`, `level`, `map` (a plain local filename).

| Required organization level | Maximum original .lua size |
| --- | --- |
| 2 | 75 KB |
| 3 | 100 KB |
| 4 | 150 KB |
| 5 | 200 KB |
| 6 | 250 KB |
| 7 | 300 KB |

KB means 1,024 bytes; comments and converter wrappers count toward the limit.
The importer reads literal `local objects = {...}` and optional
`local removals = {...}` arrays. It **never executes uploaded Lua**. Custom
functions, timers, shaders, vehicles, peds and script side effects are not
imported. Only the converter object/removal data is used. Up to 4,000 objects,
512 removals, scale 0.05?10, and removal radius up to 150m are supported.

Object columns: `model,x,y,z,rx,ry,rz,scale,breakable,doubleSided,collisions,alpha,interior,dimension,frozen`.
The first seven are required; remaining columns are optional in that order.
Removal columns: `model,radius,x,y,z,interior`.

Open a PR, update `github` to that PR's URL and push. Enter its release key and
URL in the in-game Base field and submit settings. After review, merge and
publication to SAFGmaps, managers can approve it. Only the approved base is
instantiated, and only while the organization has its required paid level and
size allowance. Existing manually placed bases are not replaced or removed by
this workflow; coordinate replacement of those with staff.

## Donation vehicle and skin shaders

1. Fork the repository and create `shaders/<unique-release-key>/` on a branch.
2. Add `request.json`, a local `.fx` shader and, for liveries, a PNG/DDS texture.
   Copy the schema from `examples/request.json`; do not copy example metadata
   into the real catalog without replacing it.
3. Open a PR, then set `github` in your JSON to that PR's URL and push the update.
4. Staff review the visual result, texture targets, shader cost and assets. Once
   merged into **main**, the private server publisher imports the validated files
   into `SAFGworldShaders` automatically. Fork pushes and unmerged PRs never deploy.
5. In game, open `/donationshaders`. Choose your approved donation vehicle or a
   GTA skin model, enter the release key and the same PR URL, and submit.
   Each request reserves **0.5 donation points**. Staff approve it in
   `/donationadmin`; rejection/cancellation returns points only.

A skin shader is account-bound and only appears while you use the approved skin
model. It does not grant a police/medic skin or change your job's spawn model.
Vehicle shaders remain limited to approved donation vehicles owned by the account.
One livery and one FX effect may be assigned per vehicle or per account/skin model.

Use a **new release key** for every revision. Merged releases are immutable and
must remain available for existing approved players. Do not replace/delete old
assets. The importer pins commits and hashes; changing bytes cannot silently
replace someone else's approved shader.

Limits: 128 KiB UTF-8 FX, one PNG/DDS texture up to **512×512 for vehicles** or
**256×256 for skins**, with a 4 MiB file-size ceiling, 1–8
explicit texture names/patterns (never a lone `*`). No Lua, JavaScript, DFF/TXD,
executables, remote URLs, credentials or payment details in shader submissions.
Texture validation is not proof that an arbitrary FX is fast or crash-free;
maintainers must test custom effects in MTA before merging.

Run `python -m pip install -r tools/requirements.txt` then
`python tools/validate.py --world .` to check shader and base data. CI validates submissions without deployment secrets.
The private publisher creates pinned shader assets and base data, never executable map scripts.

Standard skin/vehicle liveries only require `request.json` plus one PNG/DDS.
Omit `fx` to use the server-supplied shader. Custom effects need reviewed FX.
