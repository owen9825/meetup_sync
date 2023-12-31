#!/bin/bash
# This script receives two paths, eg `../my_website/index.html` and ../my_website/images`, then compares the two paths
# to determine the 2nd path relative to the first (= `./images`)

# Check if two arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 path1 path2"
    exit 1
fi

# Input paths
path1=$1
path2=$2

# Convert paths to arrays
IFS='/' read -ra ADDR1 <<< "$path1"
IFS='/' read -ra ADDR2 <<< "$path2"

# Find the length of the shortest path
min_length=${#ADDR1[@]}
if [ ${#ADDR2[@]} -lt $min_length ]; then
    min_length=${#ADDR2[@]}
fi

# Find common path
common_path=""
for (( i=0; i<$min_length; i++ )); do
    if [ "${ADDR1[$i]}" == "${ADDR2[$i]}" ]; then
        common_path="$common_path/${ADDR1[$i]}"
    else
        break
    fi
done

# Construct the relative path
relative_path="."
for (( i=${#common_path}; i<${#path1}; i++ )); do
    if [ "${path1:$i:1}" == "/" ]; then
        relative_path="$relative_path/.."
    fi
done
relative_path="$relative_path/${path2:${#common_path}}"

# Remove double slashes, if any
relative_path="${relative_path//\/\///}"

echo "${relative_path}"
