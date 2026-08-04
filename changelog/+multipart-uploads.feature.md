Added multipart support to the transport, so campaign attachments, contact
CSV imports, and OAuth application logos upload as real files rather than JSON.
`client.contacts.export()` returns the encoded bytes, so `xlsx` survives intact.
