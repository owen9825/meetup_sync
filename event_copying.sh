#!/bin/bash
echo "This script should work in Linux or MacOS"

destination_webpage="../BIA_Website/public/index.html"
if [ ! -f "${destination_webpage}" ]; then
  echo "${destination_webpage} does not exist. Please create the file, or update this script with a different destination."
  exit 1
fi

destination_imagery_directory="../BIA_Website/public/images"
if [ ! -d "$destination_imagery_directory" ]; then
    echo "Directory $destination_imagery_directory does not exist. Please create it, or update this script with a different destination."
    exit 1
fi


source_webpage=$(ls *.html | grep "Events")
# When we're copying the imagery later, we'll assert that the image paths mentioned in the file are relative not only to
# the webpage, but also to the place where this script is being executed.
if [ -z "${source_webpage}" ]; then
  echo "No matching files found with name '…Events….html."
  exit 1
fi

python event_copying.py --source "${source_webpage}" --destination "${destination_webpage}" | tee copying.log

# We will update the destination webpage to replace their current paths with this relative path.
relative_imagery_path=$(./path_comparison.sh "${destination_webpage}" "${destination_imagery_directory}")

src_images=$(grep "🖼" copying.log | grep --only-matching --perl-regexp "[^🖼]+$" | sort --unique)
# Loop over each line and echo the src_image
while IFS= read -r src_image; do
    # The images must be relative to where this script is being executed, not just to the webpage.
    path_suffix=`echo ${src_image} | grep --only-matching --perl-regexp "/[^/]+\.[^$]+$"`  # /…/my_image.webp
    path_suffix_length=${#path_suffix}
    path_prefix=${src_image%$path_suffix*}
    echo "We shall save ${path_suffix} in ${destination_imagery_directory}, moving it from ${path_prefix}"
    cp "${src_image}" "${destination_imagery_directory}${path_suffix}"
    revised_img_src="${relative_imagery_path}${path_suffix}"
    echo "Updating img references from ${src_image} to ${revised_img_src}"
    # The fragment identifier (#) is not sent to the web server, so it's a great contender for something that will not
    # be present in the search and replacement strings for sed, when we're replacing image paths.
    sed --in-place "s#${src_image}#${revised_img_src}#g" ${destination_webpage}
done <<< "$src_images"
