import urllib.request
import json
import dml
import prov.model
import datetime
import uuid
import random
from ast import literal_eval

class projectDestinationData(dml.Algorithm):
    contributor = 'cma4_lliu_saragl_tsuen'
    reads = ['cma4_lliu_saragl_tsuen.entertainment', 'cma4_lliu_saragl_tsuen.food']
    writes = ['cma4_lliu_saragl_tsuen.destinationsProjected']

    @staticmethod
    def execute(trial = False):
        '''Retrieve some data sets (not using the API here for the sake of simplicity).'''
        startTime = datetime.datetime.now()

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('cma4_lliu_saragl_tsuen', 'cma4_lliu_saragl_tsuen')

        dataSet = []


        collection = None
        
        if trial:
            collection = repo['cma4_lliu_saragl_tsuen.entertainment'].aggregate([{'$sample': {'size': 1000}}], allowDiskUse=True)
        else:
            collection = repo['cma4_lliu_saragl_tsuen.entertainment'].find()

        # projection
        dataSet = [
        	{'name': row["BUSINESSNAME"],
        	'coords': row["Location"],
            'dest_type': "entertainment"}
        	for row in collection
        ]

        collection2 = None
        if trial:
            collection2 = repo['cma4_lliu_saragl_tsuen.food'].aggregate([{'$sample': {'size': 1000}}], allowDiskUse=True)
        else:
            collection2 = repo['cma4_lliu_saragl_tsuen.food'].find()

        food_data = []
        # joining food.py while filtering it
        food_data = [{"name": field['businessName'], "coords": field['Location'], 'dest_type': 'food'} 
            for field in collection2 if field["RESULT"] is not "HE_Fail"]
        
        for i in range(len(food_data)):
            dataSet.append(food_data[i])


        final = []
        inList = []
        i = 1
        # create tuples out of string coordinates
        Completion = 0
        for entry in dataSet:
            #if i == 2:
            #    break
            
            
            i += 1
            if  i % 170571 == 0:
                Completion += 33
                print(str(Completion) + "% Complete")
            
            if entry['name'] not in inList:
                if entry['coords'] != "NULL":
                    inList.append(entry['name'])
                    stringCoords = entry['coords']
                    la = stringCoords[1:13]
                    lo = stringCoords[15:-1]
                    if la == '' or lo == '':
                        continue
                    entry['coords'] = (float(la),float(lo))
                    #print(entry)
                    final.append(entry)
        print(final)

        repo.dropCollection("cma4_lliu_saragl_tsuen.destinationsProjected")
        repo.createCollection("cma4_lliu_saragl_tsuen.destinationsProjected")
        repo['cma4_lliu_saragl_tsuen.destinationsProjected'].insert_many(final)
        repo['cma4_lliu_saragl_tsuen.destinationsProjected'].metadata({'complete':True})
        print(repo['cma4_lliu_saragl_tsuen.destinationsProjected'].metadata())

        repo.logout()

        endTime = datetime.datetime.now()

        return {"start":startTime, "end":endTime}
    
    @staticmethod
    def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):
        '''
            Create the provenance document describing everything happening
            in this script. Each run of the script will generate a new
            document describing that invocation event.
            '''

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('cma4_lliu_saragl_tsuen', 'cma4_lliu_saragl_tsuen')
        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/') # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/') # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont', 'http://datamechanics.io/ontology#') # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/') # The event log.
        doc.add_namespace('destinations', 'http://datamechanics.io/')

        this_script = doc.agent('alg:cma4_lliu_saragl_tsuen#projectDestinationData', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})
        resource = doc.entity('dat:entertainment', {'prov:label':'Destinations Entertainment Name and Coords', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        resource2 = doc.entity('dat:food', {'prov:label':'Destinations Food Name and Data', prov.model.PROV_TYPE:'ont:DataSet'})
        get_dests = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        doc.wasAssociatedWith(get_dests, this_script)
        doc.usage(get_dests, resource, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Retrieval'
                  }
                  )
        doc.usage(get_dests, resource2, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Computation'
                  }
                  )

        entertainment = doc.entity('dat:cma4_lliu_saragl_tsuen#entertainment', {prov.model.PROV_LABEL:'Filtered Entertainment Dests', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(entertainment, this_script)
        doc.wasGeneratedBy(entertainment, get_dests, endTime)
        doc.wasDerivedFrom(entertainment, resource, get_dests, get_dests, get_dests)

        food = doc.entity('dat:cma4_lliu_saragl_tsuen#food', {prov.model.PROV_LABEL:'Filtered Food Dests', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(food, this_script)
        doc.wasGeneratedBy(food, get_dests, endTime)
        doc.wasDerivedFrom(food, resource, get_dests, get_dests, get_dests)

        repo.logout()
                  
        return doc

projectDestinationData.execute()
doc = projectDestinationData.provenance()
print(doc.get_provn())
print(json.dumps(json.loads(doc.serialize()), indent=4))

## eof