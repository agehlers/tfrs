#!/bin/bash

echo Prerequisites for running this script:
echo 1.  Python 2.7 is installed - assumes it is called python
echo 2.  Mustache is available from the command line
echo
echo This system uses the Node.js version of Mustache
echo 
echo To install, run: npm install mustache -g 
echo 

OUTPUT_FILE="TFRSswagger.yaml"

#  make a backup of the current output file.

cp $OUTPUT_FILE "$OUTPUT_FILE".bck

PYTHONCMD=python

#  convert csv files to json

#  IMPORTANT - do not add the yes parameter here, as it will result in empty yaml output
$PYTHONCMD TestData/csv2json.py in/model.csv 
$PYTHONCMD TestData/csv2json.py in/api.csv 

#  generate sections of swagger files

echo Generating Model YAML

mustache "model/model_Defs.json" "templates/model.mustache" >model.yaml

echo Generating API YAML

mustache "api/api_Defs.json" "templates/api.mustache" >api.yaml

echo Merging YAML


#  file definitions:
#  header.yaml - edit this to change the upper portion of the output
#  api.yaml - generated by the above script
#  postapi.yaml - edit this to change the static text included after the generated
#  model.yaml - generated by the above script
#  footer.yaml - edit this to change the footer.
cat header.yaml api.yaml postapi.yaml model.yaml footer.yaml >$OUTPUT_FILE
