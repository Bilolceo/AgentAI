"""Telephony intake abstraction (spike).

Provider-first: a webhook flow that future Twilio/SIP integration can plug into
without touching the existing VoicePipelineService. Mock is the default; Twilio is
a skeleton only (no real external calls, no media streaming, no barge-in).
"""
