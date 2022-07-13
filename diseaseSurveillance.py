import os
import csv
import json
import xmltodict
from pprint import pprint

# Config ################################################################################################################
with open("DiseaseSurveillanceModel_EPI_IMM-16926.xml") as xml_file:
    data_dict = xmltodict.parse(xml_file.read())

xml_file.close()
json_data = json.dumps(data_dict)


with open("DiseaseSurveillance.json", "w") as json_file:
    json_file.write(json_data)
    json_file.close()

dis_Surv_JSON = open("DiseaseSurveillance.json")
data = json.load(dis_Surv_JSON)


question_variable = data['Model']['QuestionPackages']['QuestionPackage']

fieldnames = ["questionPackageUniqueID", "questiionUniqueID", "ReportLabel", "AnswerUniqueID", "AnswerSlectionValue"]
answer_Select = []
list_of_dicts = []

question_Number = 0



#Main
for items in question_variable:
    print("\n"+f"record number {number}"+"\n")
    #print(f"Question Variable Keys:/n {items.keys()}")
    #print(items['@UniqueID'])
    question_Package_Name = items['@UniqueID']

    # only grab items that have a "Question attached to them"
    if 'Question' in items.keys():
        #print(items["Question"])
        questions = items["Question"]


        #for each question, we get the necessary values
        for question in questions:
            # print(question)
            # print(type(question))


            #only want values that have an ID and an AnswerSelection component
            try:
                question["@UniqueID"] and question["AnswerSelection"]
                #print(question.keys())
                unique_ID = question["@UniqueID"]
                AnswerSelection = question["AnswerSelection"]
                AnswerSelectKeys = AnswerSelection.keys()

                # We don't mind if it doesn't have a report label but we want to grab it if it does have one.
                try:
                    Report_Label = question['@ReportLabel']
                    #print(question['@ReportLabel'])
                    question['@ReportLabel']
                except:
                    Report_Label = None

                for selection in AnswerSelectKeys:
                    # We need to have an idea of available selections, so I created a list, which is populated with all options
                    if selection not in answer_Select:
                        answer_Select.append(selection)

                    if selection == 'SelectionChoice':
                        selection_Choice = AnswerSelection[selection]
                        #print(selection_Choice)
                        for select in selection_Choice:
                            selection_Unique_ID = select['@UniqueID']
                            selection_Value = select["@Value"]
                            #print(selection_Value)
                            list_of_dicts.append({
                                               "questionPackageUniqueID": question_Package_Name,
                                               "questiionUniqueID": unique_ID,
                                               "ReportLabel": Report_Label,
                                               "AnswerUniqueID": selection_Unique_ID,
                                               "AnswerSlectionValue": selection_Value})

                    # print(selection)
                    # print(AnswerSelection[selection])
            except:
               # print("Record Passed")
                pass
        #print(len(items["Question"]))
    question_Number += 1

#print(questions)
#pprint(question_Names)
#print(len(question_Names))
print(answer_Select)
pprint(list_of_dicts)


with open("DiseaseSurveillanceFlatFile.csv", 'w', encoding="UTF8", newline='') as f:
    writer = csv.DictWriter(f, fieldnames)
    writer.writeheader()
    writer.writerows(list_of_dicts)
