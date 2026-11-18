# Starter rules

A short, generic subset of the shared rules for someone starting to work with an
AI assistant. It needs no tools, hooks, accounts or scripts.

## Adopt

1. Copy `REGRAS-INICIAIS.md` into the instructions of a Claude Project (or the
   equivalent in another assistant).
2. Fill in the `[ ]` placeholders and keep a line at the top naming the version
   you adopted, e.g. `baseado em starter-v0.1`.
3. Keep personal changes in your own overlay: your instructions, or a private
   file or repository. Never add personal data, paths or accounts here: this
   repository is public.

## Update

1. A change to the starter goes through a reviewed pull request and a new tag
   `starter-vX.Y`, with an entry in `CHANGELOG.md`.
2. Give your assistant the changelog entry and the diff between your tag and the
   new one. It proposes what to change in your instructions; your overlay wins
   on any conflict. You accept or decline.
3. Update the version line in your instructions.

## Scope

Only `starter/` is meant for adoption as is. The rest of this repository is the
full Project Factory rule set and depends on its owner's local tools; read it as
reference, not as instructions to install.
