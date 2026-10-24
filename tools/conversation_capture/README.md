# Conversation capture utility

This macOS utility prepares a Codex JSONL conversation in memory, redacts
recognized credential forms, and preserves the record structure. It never
writes a transcript to a scratch file. A reviewed export can write directly to
an owner-only Google Drive folder mounted by Drive for desktop.

The folder ID, owner address, and mount path belong in a private JSON config
outside this repository:

```json
{"folder_id":"<drive-folder-id>","owner_email":"<owner-address>","mount":"<absolute-local-mount-path>"}
```

Use `capture_cli.py summary SOURCE --records N` to get hashes for a fixed
prefix of an active chat. Use `review` with the same source and record count to
inspect the redacted output in a pager; it stays in memory. `write` requires
the same range; a later segment uses `--start-record N+1 --records END`. It also requires
the exact reviewed source and output hashes, private config, and fresh Drive
metadata containing the folder ID, folder type, active account, sole-owner
permission, and a `checked_at_epoch` within 30 seconds. A caller must obtain
that metadata from the Drive connector immediately before the write. The code
checks the mounted folder's Drive item ID, Unix owner, and permissions again
through its directory descriptor. The target file is created with mode `0600`.

The regex pass does not establish that an arbitrary conversation is free of
unknown or fragmented credentials. A human must review the exact output before
export. A local write also needs remote Drive readback, including file ID,
parent and size, before it counts as synced; compare a remote checksum when the
connection exposes one. The native conversation should remain in
place. This utility does not delete or schedule deletion of any record.

Run the synthetic checks with
`python3 -m unittest discover -s . -p 'test_safe_export.py' -v`.
These checks do not prove live capture or full conversation coverage.
