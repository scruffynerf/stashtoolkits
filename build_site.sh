#!/bin/bash

# builds a repository of scrapers
# outputs to _site with the following structure:
# scraperindex.yml and pluginindex.yml
# <scraper_id>.zip OR <plugin_id>.zip
# Each zip file contains the scraper.yml file and any other files in the same directory
# OR the plugin.yml file and any other files in the same directory

outdir="$1"
if [ -z "$outdir" ]; then
    outdir="_site"
fi

rm -rf "$outdir"
mkdir -p "$outdir"

buildScraper()
{
    f=$1
    dir=$(dirname "$f")

    # get the scraper id from the filename
    scraper_id=$(basename "$f" .yml)
    versionFile=$f
    if [ "$scraper_id" == "package" ]; then
        scraper_id=$(basename "$dir")
    fi

    if [ "$dir" != "./scrapers" ]; then
        versionFile="$dir"
    fi

    echo "Processing $scraper_id"

    # create a directory for the version
    version=$(git log -n 1 --pretty=format:%h -- "$versionFile")
    updated=$(TZ=UTC0 git log -n 1 --date="format-local:%F %T" --pretty=format:%ad -- "$versionFile")

    # create the zip file
    # copy other files
    zipfile=$(realpath "$outdir/$scraper_id.zip")

    name=$(grep "^name:" "$f" | cut -d' ' -f2- | sed -e 's/\r//' -e 's/^"\(.*\)"$/\1/')
    ignore=$(grep "^# ignore:" "$f" | cut -c 10- | sed -e 's/\r//')
    dep=$(grep "^# requires:" "$f" | cut -c 12- | sed -e 's/\r//')

    # always ignore package file
    ignore="-x $ignore package"

    pushd "$dir" > /dev/null
    if [ "$dir" != "./scrapers" ]; then
        zip -r "$zipfile" . ${ignore} > /dev/null
    else
        zip "$zipfile" "$scraper_id.yml" > /dev/null
    fi
    popd > /dev/null

    # write to spec index
    echo "- id: $scraper_id
  name: $name
  version: $version
  date: $updated
  path: $scraper_id.zip
  sha256: $(sha256sum "$zipfile" | cut -d' ' -f1)" >> "$outdir"/scraperindex.yml

    # handle dependencies
    if [ ! -z "$dep" ]; then
        echo "  requires:" >> "$outdir"/scraperindex.yml
        for d in ${dep//,/ }; do
            echo "    - $d" >> "$outdir"/scraperindex.yml
        done
    fi

    echo "" >> "$outdir"/scraperindex.yml
}

buildPlugin()
{
    f=$1

    if grep -q "^#pkgignore" "$f"; then
        return
    fi

    # get the plugin id from the directory
    dir=$(dirname "$f")
    plugin_id=$(basename "$f" .yml)

    echo "Processing $plugin_id"

    # create a directory for the version
    version=$(git log -n 1 --pretty=format:%h -- "$dir"/*)
    updated=$(TZ=UTC0 git log -n 1 --date="format-local:%F %T" --pretty=format:%ad -- "$dir"/*)

    # create the zip file
    # copy other files
    zipfile=$(realpath "$outdir/$plugin_id.zip")

    pushd "$dir" > /dev/null
    zip -r "$zipfile" . > /dev/null
    popd > /dev/null

    name=$(grep "^name:" "$f" | head -n 1 | cut -d' ' -f2- | sed -e 's/\r//' -e 's/^"\(.*\)"$/\1/')
    description=$(grep "^description:" "$f" | head -n 1 | cut -d' ' -f2- | sed -e 's/\r//' -e 's/^"\(.*\)"$/\1/')
    ymlVersion=$(grep "^version:" "$f" | head -n 1 | cut -d' ' -f2- | sed -e 's/\r//' -e 's/^"\(.*\)"$/\1/')
    version="$ymlVersion-$version"
    dep=$(grep "^# requires:" "$f" | cut -c 12- | sed -e 's/\r//')

    # write to spec index
    echo "- id: $plugin_id
  name: $name
  metadata:
    description: $description
  version: $version
  date: $updated
  path: $plugin_id.zip
  sha256: $(sha256sum "$zipfile" | cut -d' ' -f1)" >> "$outdir"/pluginindex.yml

    # handle dependencies
    if [ ! -z "$dep" ]; then
        echo "  requires:" >> "$outdir"/pluginindex.yml
        for d in ${dep//,/ }; do
            echo "    - $d" >> "$outdir"/pluginindex.yml
        done
    fi

    echo "" >> "$outdir"/pluginindex.yml
}

# now we just call the appropriate commands for each section

find ./UtilitiesToolKit/plugins -mindepth 1 -name *.yml | while read file; do
    buildPlugin "$file"
done
find ./AcquisitionToolKit/plugins -mindepth 1 -name *.yml | while read file; do
    buildPlugin "$file"
done
find ./MovieToolKit/plugins -mindepth 1 -name *.yml | while read file; do
    buildPlugin "$file"
done

find ./UtilitiesToolKit/scrapers/ -mindepth 2 -name *.yml -print0 | while read -d $'\0' f; do
    buildScraper "$f"
done
find ./AcquisitionToolKit/scrapers/ -mindepth 2 -name *.yml -print0 | while read -d $'\0' f; do
    buildScraper "$f"
done
find ./MovieToolKit/scrapers/ -mindepth 2 -name *.yml -print0 | while read -d $'\0' f; do
    buildScraper "$f"
done

# handle dependency packages
#find ./scrapers/ -mindepth 2 -name package -print0 | while read -d $'\0' f; do
#    buildScraper "$f"
#done
