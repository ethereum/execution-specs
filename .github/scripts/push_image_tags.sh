#!/usr/bin/env bash
# Push the tags of a locally built image and record the pushed digest with
# record_image_digest.sh.
#
#   push_image_tags.sh <local-ref> <image> "<tags>" <immutable-tag> <commit> <release>
#
# <immutable-tag>, empty outside release runs, is a release tag: it is
# published once and never overwritten, so a re-run cannot change what a
# pinned release tag points to. If it already exists it is skipped with a
# notice; the other tags, channels, move as usual.
set -euo pipefail

local_ref=$1 image=$2 tags=$3 immutable=$4 commit=$5 release=$6
here=$(cd "$(dirname "$0")" && pwd)
log=$(mktemp)
trap 'rm -f "$log"' EXIT

exists() {
    if docker buildx imagetools inspect "$1" > /dev/null 2> "$log"; then
        return 0
    fi
    # A missing tag reads "not found"; a package that does not exist yet is
    # refused ("denied", 403). Any other registry error fails.
    if grep -qiE "not found|denied|403 forbidden" "$log"; then
        return 1
    fi
    cat "$log" >&2
    exit 1
}

pushed=""
for tag in $tags; do
    if [ "$tag" = "$immutable" ] && exists "$image:$tag"; then
        echo "::notice::$image:$tag already exists; release tags are not overwritten"
        continue
    fi
    docker tag "$local_ref" "$image:$tag"
    docker push "$image:$tag"
    pushed="${pushed:+$pushed }$tag"
done

if [ -z "$pushed" ]; then
    exit 0
fi
digest=$(docker buildx imagetools inspect "$image:${pushed%% *}" --format '{{.Manifest.Digest}}')
"$here/record_image_digest.sh" "$image" "$pushed" "$digest" "$commit" "$release"
