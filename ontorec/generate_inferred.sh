#!/bin/bash

echo "Starting..."
cd /app/reasoner/
java -jar factplusplus.jar -s /app/tmp/$1 -d /app/inferred -f rdf -r
echo "End with status $?"