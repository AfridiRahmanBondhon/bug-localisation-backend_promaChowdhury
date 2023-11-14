#!/bin/bash

repo_url="https://github.com/jhy/jsoup"  

writable_dir="/project"  

chmod -R 755 .

# Create the writable directory if it doesn't exist
if [ ! -d "$writable_dir" ]; then
  mkdir -p "$writable_dir"
fi

# Check if the directory was successfully created or already exists
if [ -d "$writable_dir" ]; then
  # Change to the writable directory
  cd "$writable_dir" || exit

  # Clone the GitHub repository into the writable directory
  git clone "$repo_url" .

  # Check if the clone operation was successful
  if [ $? -eq 0 ]; then
    echo "GitHub repository cloned into $writable_dir"
  else
    echo "Failed to clone GitHub repository"
  fi
else
  echo "Failed to create or access the writable directory"
fi
