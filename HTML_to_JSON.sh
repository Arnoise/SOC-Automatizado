echo "$get_oldest_not_readen_mail.body.value.#.body.content" | \
sed 's/&quot;/"/g' | \
sed 's/&nbsp;/ /g' | \
sed 's/<[^>]*>//g' | \
tr -d '\r' | \
sed ':a;N;$!ba;s/\n/ /g' | \
sed 's/\\r\\n//g' | \
sed 's/"time": "\([0-9:]*\)[^"]*"/"time": "\1"/g' | \
sed 's/"identities.label": "\(.*\)"/"identities.label": "\1"/g' | \
tr -s ' ' | \
sed 's/} \([a-zA-Z0-9._-]*\)/}, \1/g' | \
sed 's/^ *//;s/ *$//' | \
jq .   # This will pretty-print the JSON or show an error if it's not valid.
