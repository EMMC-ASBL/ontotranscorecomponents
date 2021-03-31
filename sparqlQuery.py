#sparqlQuery.py

import stardog
import json

conn_details = {
  'endpoint': 'http://localhost:5820',
  'username': 'admin',
  'password': 'admin'
}
#connects to the database
conn = stardog.Connection('emmo-db', **conn_details)
#executes SELECT query
print(conn.select("SELECT ?subClass WHERE { ?subClass rdfs:subClassOf* <http://emmo.info/emmo/middle/siunits#SIBaseUnit> }"))
