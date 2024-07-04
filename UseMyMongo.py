from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from flask import Flask, jsonify, request
from bson.json_util import dumps
import json
from flask_cors import CORS

import os # 可以拿到環境變數


#開啟後端
app = Flask(__name__)
CORS(app)  # 允許跨域請求

# mongo秘鑰 (把秘鑰放到環境變數中)
uri = os.environ.get('MONGODB_URI')


#連到mongodb
client = MongoClient(uri, server_api=ServerApi('1'))
db = client['firstTry']
collection = db['AmyLifeCarer']

# get_data
@app.route('/get_childhood_story', methods=['GET'])
def get_childhood_story():
    try:
        # 取得 amy 的資料
        data = collection.find_one({"name": "amy"})
        if data:
            # 取得原史文檔和整理後的文檔
            original_document = data["elders"][0]["lifeStoryBook"]["childhood"]["originalDocument"]
            organized_document = data["elders"][0]["lifeStoryBook"]["childhood"]["organizedDocument"]
            
            # 構建要返回的資料
            result = {
                "originalDocument": original_document,
                "organizedDocument": organized_document
            }
            return jsonify(result)
        else:
            return jsonify({"error": "No data found"}), 404
    except (KeyError, IndexError) as e:
        return jsonify({"error": str(e)}), 500
    
# append_childhood 路由
@app.route('/append_childhood', methods=['POST'])
def append_childhood():
    try:
        # 從請求中獲得 JSON 数据
        print("haha")
        raw_data = request.get_data()
        data = json.loads(raw_data)
        print(data)

        # 定義追加字段 从收到的 JSON 数据中提取 organizedDocument 和 originalDocument 字段。如果这些字段不存在，默认值是空数组 []
        organized_document = data.get("organizedDocument", [])
        original_document = data.get("originalDocument", [])
        original_Audio = data.get("originalAudio", [])
        
        # 使用 $push 操作符追加数组元素
        update_result = collection.update_one(
            {"name": "amy"},
            {
                "$push": {
                    "elders.0.lifeStoryBook.childhood.originalAudio": {"$each": original_Audio},
                    "elders.0.lifeStoryBook.childhood.organizedDocument": {"$each": organized_document},
                    "elders.0.lifeStoryBook.childhood.originalDocument": {"$each": original_document}
                }
            }
        )
        
        if update_result.matched_count > 0:
            return jsonify({"message": "Childhood data appended successfully"}), 200
        else:
            return jsonify({"error": "No data found to update"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# delete_childhood 中的其中一則故事
@app.route('/delete_childhood', methods=['POST'])
def delete_childhood():

#取得要刪除的編號
    data = request.get_json()
    index = data.get('index_to_delete')

    if index is None:
        return jsonify({'error': 'index_to_delete is required.'}), 400
    
# 查找需要修改的文檔
    query = {'name': 'amy'}
    
    # 使用 $unset 操作符將指定索引的值設置為 null
    update = {
        '$unset': {
            f'elders.0.lifeStoryBook.childhood.originalAudio.{index}': '',
            f'elders.0.lifeStoryBook.childhood.originalDocument.{index}': '',
            f'elders.0.lifeStoryBook.childhood.organizedDocument.{index}': ''
        }
    }
    
    # 執行更新操作
    result = collection.update_one(query, update)

    # 如果有做更新，那就把剛剛變成null的值移出
    if result.modified_count > 0:
        # 使用 $pull 操作符移除陣列中的 null 值
        cleanup = {
            '$pull': {
                'elders.0.lifeStoryBook.childhood.originalAudio': None,
                'elders.0.lifeStoryBook.childhood.originalDocument': None,
                'elders.0.lifeStoryBook.childhood.organizedDocument': None
            }
        }
        collection.update_one(query, cleanup)

        return jsonify({'message': 'Successfully deleted the value at the specified index.'}), 200
    else:
        return jsonify({'error': 'No documents matched the query or no modifications were made.'}), 404


if __name__ == '__main__':

    #許多雲平台（如 Heroku、Railway 等）會動態分配一個端口給你的應用。這個端口通常通過環境變量提供。
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))


# 關閉MongoDB連接
#client.close()


#################  新增到childhood的json的範例  #######################
# {
#     "originalAudio":["path/to/tom/childhood/new_audio"],   !!記得都要加[]上面才能用 "$each" 
#     "organizedDocument": [
#         {
#             "storyTitle": "新的故事标题",
#             "storySummary": "新的故事总结...",
#             "storyTime": "童年",
#             "keywords": ["关键词1", "关键词2"],
#             "historicalBackground": "历史背景...",
#             "emotionalAnalysis": {
#                 "情绪1": 0.5,
#                 "情绪2": 0.5
#             }
#         }
#     ],
#     "originalDocument": [
#         "这是一个新的原始文档文本..."
#     ]
# }
#################  新增到childhood的json的範例  #######################

#################  要這樣讀app inventor 傳來的data !!  #######################

        # raw_data = request.get_data()
        # data = json.loads(raw_data)

        # 不能用 (因為app inventor 傳來的沒有JSON的 head !)
        # data = request.get_json()
        # index = data.get('index_to_delete')

#################  要這樣讀app inventor 傳來的data !!  #######################

#################  刪除到childhood的json的範例  #######################
# {
#  "index_to_delete" :"5"
# }
#################  刪除到childhood的json的範例  #######################