#!/usr/bin/env python3

# For help:
#
# - Run with no arguments.
# - Ask Everett Hildenbrandt (@ehildenb).

# Goals:
#
# - Validate test inputs with JSON Schemas.
# - Check that tests have been filled.
# - Filter tests based on properties.
# - Convert between various test filler formats.

# Non-goals:
#
# - Test filling.
# - Test post-state checking.

# Dependencies:
#
# - python-json
# - python-yaml
# - python-jsonschema
# - python-pysha3

import sys
import os
import json
import yaml
import jsonschema
import sha3

# Utilities
# =========

# Errors/Reporting

exit_status = 0
error_log   = []

def _report(*msg):
    print("== " + sys.argv[0] + ":", *msg, file=sys.stderr)

def _logerror(*msg):
    global exit_status
    _report("ERROR:", *msg)
    error_log.append(" ".join(msg))
    exit_status = 1

def _die(*msg, exit_code=1):
    _report(*msg)
    _report("exiting...")
    sys.exit(exit_code)

# Filesystem/parsing

def readFile(fname):
    if not os.path.isfile(fname):
        _die("Not a file:", fname)
    with open(fname, "r") as f:
        fcontents = f.read()
        try:
            if fname.endswith(".json"):
                fparsed = json.loads(fcontents)
            elif fname.endswith(".yml"):
                fparsed = yaml.load(fcontents, Loader=yaml.FullLoader)
            else:
                _die("Do not know how to load:", fname)
            return fparsed
        except:
            _die("Could not load file:", fname)

def writeFile(fname, fcontents):
    if not os.path.exists(os.path.dirname(fname)):
        os.makedirs(os.path.dirname(fname))
    with open(fname, "w") as f:
        f.write(json.dumps(fcontents, indent=4, sort_keys=True) + "\n")

# Functionality
# =============

# Listing tests

def findTests(filePrefix=""):
    return [ fullTest for fullTest in [ os.path.join(root, file) for root, _, files in os.walk(".")
                                                                 for file in files
                                                                  if file.endswith(".json") or file.endswith(".yml")
                                      ]
                       if fullTest.startswith(filePrefix)
           ]

def listTests(filePrefixes=[""]):
    return [ test for fPrefix in filePrefixes
                  for test in findTests(filePrefix=fPrefix)
           ]

# Schema Validation

def validateSchema(testFile, schemaFile):
    testSchema = readFile(schemaFile)
    defSchema  = readFile("JSONSchema/definitions.json")
    schema     = { "definitions"        : dict(defSchema["definitions"], **testSchema["definitions"])
                 , "patternProperties"  : testSchema["patternProperties"]
                 }

    testInput  = readFile(testFile)
    try:
        jsonschema.validate(testInput, schema)
    except:
        from jsonschema import Draft4Validator
        _logerror("Validation failed:", "schema", schemaFile, "on", testFile)
        v = Draft4Validator(schema)
        errors = sorted(v.iter_errors(testInput), key=lambda e: e.path)
        for error in errors:
            _logerror(error.message)

def validateTestFile(testFile):
    if testFile.startswith("./src/VMTestsFiller/"):
        schemaFile = "JSONSchema/vm-filler-schema.json"
    elif testFile.startswith("./src/GeneralStateTestsFiller/"):
        schemaFile = "JSONSchema/st-filler-schema.json"
    elif testFile.startswith("./src/BlockchainTestsFiller/"):
        schemaFile = "JSONSchema/bc-filler-schema.json"
    elif testFile.startswith("./VMTests/"):
        schemaFile = "JSONSchema/vm-schema.json"
    elif testFile.startswith("./GeneralStateTests/"):
        schemaFile = "JSONSchema/st-schema.json"
    elif testFile.startswith("./BlockchainTests/"):
        schemaFile = "JSONSchema/bc-schema.json"
    else:
        _logerror("Do not know how to validate file:", testFile)
        return
    validateSchema(testFile, schemaFile)

# Check tests filled

def hashFile(fname):
    with open(fname ,"rb") as f:
        try:
            k = sha3.keccak_256()
            if fname.endswith(".json"):
                s = json.dumps(json.load(f), sort_keys=True, separators=(',', ':'))
            elif fname.endswith(".yml"):
                s = json.dumps(yaml.load(f, Loader=yaml.FullLoader), sort_keys=True, separators=(',', ':'))
            else:
                _die("Do not know how to hash:", fname)
            k.update(s.encode('utf-8'))
            return { 'hash': k.hexdigest(), 'raw': s }
        except Exception as e:
            _logerror("Error getting hash of the yml/json:", fname)
            _logerror("Exception: ", str(e))
            return { 'hash': 'error', 'raw': 'error' }

def checkFilled(jsonFile):
    jsonTest = readFile(jsonFile)
    if not ( jsonFile.startswith("./src/BlockchainTestsFiller/GeneralStateTests/")
        # or jsonFile.startswith("./src/BlockchainTestsFiller/VMTests/")
          or jsonFile.startswith("./VMTests/")
          or jsonFile.startswith("./GeneralStateTests/")
          or jsonFile.startswith("./TransactionTests/")
          or jsonFile.startswith("./BlockchainTests/")
           ):
      # _report("Not a file that is filled:", jsonFile)
        return
    for test in jsonTest:
        if "_info" in jsonTest[test]:
            fillerSource = jsonTest[test]["_info"]["source"]
            fillerHash   = jsonTest[test]["_info"]["sourceHash"]
            resultHash = hashFile(fillerSource)
            if fillerHash != resultHash['hash']:
                _logerror("Filler hash is different:", jsonFile, " HashSrc: '", resultHash['raw'], "'")

# Main
# ====

def _usage():
    usage_lines = [ ""
                  , "    usage: " + sys.argv[0] + " [list|format|validate]  [<TEST_FILE_PREFIX>*]"
                  , "    where:"
                  , "            list:               command to list the matching tests."
                  , "            format:             command to format/sort the JSON/YAML file."
                  , "            validate:           command to check a file against the associated JSON schema (defaults to all files)."
                  , "            <TEST_FILE_PREFIX>: file path prefix to search for tests with."
                  , "                                eg. './src/VMTestsFiller' './VMTests' for all VMTests and their fillers."
                  ]
    _die("\n".join(usage_lines))

def main():
    if len(sys.argv) < 2:
        _usage()
    test_command = sys.argv[1]
    if len(sys.argv) == 2:
        testList = listTests()
    else:
        testList = listTests(filePrefixes=sys.argv[2:])

    if len(testList) == 0:
        _die("No tests listed!!!")

    if test_command == "list":
        testDo = lambda t: print(t)
    elif test_command == "format":
        testDo = lambda t: writeFile(t, readFile(t))
    elif test_command == "validate":
        testDo = validateTestFile
    elif test_command == "checkFilled":
        testDo = checkFilled
    else:
        _usage()

    for test in testList:
        # turn on for more info
        # _report(test_command + ":", test)
        testDo(test)

    if exit_status != 0:
        _die("Errors reported!\n[ERROR] " + "\n[ERROR] ".join(error_log))

if __name__ == "__main__":
    main()
