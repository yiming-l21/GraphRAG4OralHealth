python utils.py --json_path ./dicease_revised.json --store_neo4j 口腔疾病
python utils.py --json_path ./equipment_revised.json --store_neo4j 器械
python utils.py --json_path ./examination_revised.json --store_neo4j 检查
python utils.py --json_path ./medicine_revised.json --store_neo4j 药物
python utils.py --json_path ./department_revised.json --store_neo4j 科室
python utils.py --json_path ./prevention_revised.json --store_neo4j 预防
python utils.py --json_path ./treatment.json --store_neo4j 治疗
python utils.py --json_path ./anatomy.json --store_neo4j 口腔组织
python utils.py --json_path ./symptom.json --store_neo4j 症状
python store_neo4j.py
cd relations
python store_relations.py
cd ..