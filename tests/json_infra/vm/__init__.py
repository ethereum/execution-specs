"""
VM tests forks configuration.
These tests are only run for legacy forks up to Constantinople.
"""

FORKS = [
    ("ConstantinopleFix", "constantinople"),
    ("Byzantium", "byzantium"),
    ("EIP158", "spurious_dragon"),
    ("EIP150", "tangerine_whistle"),
    ("Homestead", "homestead"),
    ("Frontier", "frontier"),
]
