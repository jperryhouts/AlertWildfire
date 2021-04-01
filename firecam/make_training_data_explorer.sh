#!/bin/bash

set -e
set -x

## Creates html pages for viewing/browsing the training data.
##
## Note: images should be prepped with firecam.ipynb first.

for dataset in non_smoke smoke_cropped; do
    SRC="${HOME}/Data/firecam/${dataset}/"
    BUCKET="s3://storage-9iudgkuqwurq6/firecam/${dataset}/"
    DEST="training/${dataset}.html"
    mkdir -p "$(dirname "$DEST")"

    s3cmd sync --guess-mime-type --no-mime-magic --delete-removed --acl-public "$SRC" "$BUCKET"
    
    echo '.row { width:100%; display:block;
                 margin-left:auto; margin-right:auto; }
          .row > img { width: 9.5%; }' > "$(dirname "$DEST")/style.css"

    echo '<html><head><link rel="stylesheet" href="style.css"></head><body>' > "$DEST"

    script=""
    if [ dataset == "smoke_cropped" ]; then
        script+='{ if((NR-1)%10 == 0) print("<div class=\"row\">") };' ; fi

    script+='{printf("<img src=\"https://storage-9iudgkuqwurq6.s3-us-west-2.amazonaws.com/firecam/'${dataset}'/%s\" />\n",$1)};'

    if [ dataset == "smoke_cropped" ]; then
        script+='{ if((NR-1)%10==9) print("</div>") }' ; fi

    find "$SRC" -type f -iname '*.jpg' | sed -e 's!.*/\([^/]*\.jpg\)$!\1!' \
        | jq -R -r @uri | awk "$script" >> "$DEST"
    echo '</body></html>' >> "$DEST"
done
