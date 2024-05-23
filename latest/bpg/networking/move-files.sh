for dir in */; do
    if [ -f "${dir}index.adoc" ]; then
        mv "${dir}index.adoc" "${dir%/}.adoc"
    fi
done

