#!/usr/bin/env bash
#
# extract-highlights.sh
# Usage: ./extract-highlights.sh > highlights.txt

docker compose logs extractor \
  | sed 's/^extractor-1  | //' \
  | awk '
    # STATE 0 → look for the start‐of‐highlight header
    /^=+$/ && p==0 {
      buf=$0
      getline hdr
      if (hdr ~ /^HIGHLIGHTS FOR:/) {
        # found the header block: print it
        print buf      # ========
        print hdr      # HIGHLIGHTS FOR: …
        getline sep
        print sep      # ========
        p=1            # enter printing mode
      }
      next
    }
    # STATE 1 → we are inside a highlight block
    p==1 {
      # if we hit another separator, print it and exit block
      if (/^=+$/) {
        print
        p=0
      }
      # otherwise print any non-blank line
      else if (NF) {
        print
      }
    }'
