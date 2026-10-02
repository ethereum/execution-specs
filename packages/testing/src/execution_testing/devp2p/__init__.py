"""
A deterministic devp2p peer that serves fixture blocks to a client.

The modules here implement just enough of RLPx and the eth wire protocol
for an execution client to full sync a fixture backed chain from this
framework, so that historical blocks reach the client through its
production peer-to-peer ingestion path instead of an offline import.
"""
