Rewrote the `unibox` resource against the real routes. It previously targeted
`/unibox/threads/*`, which does not exist, so every call 404'd. The inbox is
message-centric: `list()`, `retrieve()`, and `thread()` replace the old thread
methods, alongside compose, drafts, agent drafts, snoozes, labels, and
scheduled sends.
