#!/usr/bin/env bash
# Record a pushed image's digest in the step summary and as a JSON file for
# the run's `digests-*` artifacts, so that a moving tag can be traced to the
# exact image it pointed to when a run published it.
#
#   record_image_digest.sh <image> "<tags>" <digest> <commit> <release>
set -euo pipefail

image=$1 tags=$2 digest=$3 commit=$4 release=$5

if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
    {
        echo "| Image | Tags | Digest | Commit | Release |"
        echo "| --- | --- | --- | --- | --- |"
        echo "| \`$image\` | ${tags// /, } | \`$digest\` | \`${commit:0:7}\` | ${release:-} |"
        echo
    } >> "$GITHUB_STEP_SUMMARY"
fi
mkdir -p digests
jq -n --arg image "$image" --arg tags "$tags" --arg digest "$digest" \
    --arg commit "$commit" --arg release "$release" \
    '{image: $image, tags: ($tags | split(" ")), digest: $digest, commit: $commit, release: $release}' \
    > "digests/$(echo "$image" | tr '/:' '__').json"
