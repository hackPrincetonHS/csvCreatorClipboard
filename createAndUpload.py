import firebase_admin
from firebase_admin import credentials, firestore, storage, auth

import gspread
from oauth2client.service_account import ServiceAccountCredentials

def lambda_handler(event, context):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)


    cred = credentials.Certificate('./applications-and-checkins-firebase-adminsdk-i9zb0-28d904fdcc.json')
    default_app=firebase_admin.initialize_app(cred, {
        'storageBucket': 'applications-and-checkins.appspot.com'
    })
    db=firestore.client()
    collection_ref=db.collection(u'users')

    bucket = storage.bucket()

    #test_emails=["edgeboi@gmail.com", "stephmorel8910@gmail.com", "step@gmail.com", "team@hackphs.tech", "tester2@gmail.com"]
    test_emails=[]
    properties=["dateCreated", "fullName", "isFullyLoggedIn", "shirtSize", "school", "specialAccomadations", "dietaryRestrictions", "phone", "graduationYear", "latino", "ethnicity", "gender", "githubLink", "studyLevel","", "fullName", "street1", "street2", "city", "state", "zip5", "zip4", "deliveryPoint", "", "email", "resumeLink", "hasVaccine"]

    notLoggedInRow=[""       , ""         , False            ,""          , ""     , ""                     , ""                   , ""    , ""               , ""      , ""         , ""      , ""          , ""          , "email", ""]

    docs=collection_ref.stream()

    csv=[properties]

    def arrayToString(array):
        string=""
        for el in array:
            string+=str(el)+" "
        string=string[:-1]
        return string

    for doc in docs:
        tempDict=doc.to_dict()
        newRow=[]
        for property in properties[:-2]:
            if(property in tempDict):
                if(isinstance(tempDict[property], list)):
                    newRow.append(arrayToString(tempDict[property]))
                else:
                    newRow.append(str(tempDict[property]))
            else:
                newRow.append("")

        newRow.append(str(auth.get_user(tempDict["uid"]).email))

        #skip this row
        if(newRow[-1] in test_emails):
            continue

        if(tempDict["hasResume"]):
            downurl=bucket.blob("resumes/"+tempDict["uid"])
            downurl.reload()
            downurl.make_public()
            newRow.append(downurl.public_url)
        else:
            newRow.append("")

        csv.append(newRow)

    flat_list = []
    for sublist in csv:
        for item in sublist:
            flat_list.append(item)

    for user in auth.list_users().iterate_all():
        if((not user.email in flat_list) and (not user.email in test_emails)):
            csv.append([user.email if x=="email" else x for x in notLoggedInRow])
    print(csv)
    print(len(csv))
    print(len(csv[0]))

    sheet = client.open_by_key("12Du6pww7wz6NHZQATMJqGrU7pViuPooNhUqtZYXGdpk").sheet1
    # Select a cell range
    allCells=sheet.range("A1:Z"+str(len(csv)))
    print(len(allCells))
    for i in range(0, len(csv)*len(csv[0])):
        allCells[i].value=csv[i//len(csv[0])][i%len(csv[0])]
    sheet.update_cells(allCells)

lambda_handler(None, None)
