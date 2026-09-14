"""SSTProt (Sesotec SST-Protocol) v1.54 client.

Source: official "SSTProt V1.54.pdf" (Sesotec GmbH), provided by the user
from a prior integration project
(`OneDrive/Omikron/Industria 4.0/90 Progetti Collegati/Metaldetector/`),
plus a real captured example (`sstprot_function_final_report.md`) from a
working GeniusOne device at 192.168.1.125.

Every field name/command/entry code in this package is taken from that
official documentation — nothing here is guessed. Where the documentation
itself was ambiguous (see `frame.py` docstring on logbook entry trailing
bytes), it is called out explicitly rather than silently assumed.
"""
