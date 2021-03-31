#!/usr/bin/env bash

# Description
#  This tool automates the import process of the public EMMO
#  thanks to the D. Toti's standalone (Fact++ based) reasoner, this tool
#  let import directly on a live Stardog server a ready-to-run
#  European Materials & Modelling Ontology in one CLI line.

# Workflow
#  Fetches the ontology, converts it then creates a new db on Stardog,
#  imports the converted ontology in it.

# How to use it
#  Must be run in the same dir of factplusplus.jar !
#  Default: exec the script w\o any parameter to make it fetch the master release
#  -o to specify a path for the onotlogy to collect (local or online)
#  -d to choose a name for the Stardog database

echo "++ EMMO2Stardog ++"

 ###$src_ontology=$1
while getopts o:d: flag
do
  case "${flag}" in
     o) src_ontology=${OPTARG};;
     d) new_db=${OPTARG};;
  esac
done

#TODO if db already exist ask for name - use a var for emmo-d
result="$(/opt/stardog/bin/stardog-admin db status ${new_db:-"emmo-db"})"
wait
if [[ $result == *does\ not\ exist* ]]; then
	#$db_name=$2
	#&& ./$STARDOG_HOME/stardog-admin db list | grep $db_name

  java -jar factplusplus.jar -s ${src_ontology:-"https://emmo.info/emmo"} 
  wait
  if [[ -f emmo-inferred.rdf ]]
    then
    #./$STARDOG_HOME/stardog-admin db list | grep ${db_name:-emmo-db}
    /opt/stardog/bin/stardog-admin db create -n ${new_db:-"emmo-db"} emmo-inferred.rdf
    wait
    rm emmo-inferred.rdf
    echo "Ontology successfully imported to Stardog database \"${new_db:-"emmo-db"}\""
  fi
else
  echo "Database already exist! Please specify another name"
fi
echo "terminated"

