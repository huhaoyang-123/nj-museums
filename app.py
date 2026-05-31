import os
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from services.museum_service import get_all_museums
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
CORS(app)

AMAP_KEY = os.environ.get('AMAP_KEY', '')
APP_PORT = int(os.environ.get('PORT', 5000))
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_API_URL = 'https://api.siliconflow.cn/v1/chat/completions'

@app.route('/api/museums', methods=['GET'])
def list_museums():
    museums = get_all_museums()
    return jsonify(museums)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ask', methods=['POST'])
def ask_ai():
    data = request.get_json()
    question = data.get('question', '')

    if not GROQ_API_KEY:
        return jsonify({"answer": "AI 服务未配置，请联系管理员"}), 500

    if not question.strip():
        return jsonify({"answer": "请输入您的问题"}), 400

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [
            {
                "role": "system",
                "content": "你是一个热情友好的博物馆导览助手。请根据用户的问题，结合博物馆知识，用简洁、有趣的语言回答。如果涉及博物馆推荐，可以结合博物馆的特色和位置来回答。"
            },
            {
                "role": "user",
                "content": question
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        result = response.json()

        if 'choices' in result and len(result['choices']) > 0:
            answer = result['choices'][0]['message']['content']
            return jsonify({"answer": answer})
        else:
            return jsonify({"answer": f"AI 返回格式异常: {result}"}), 500

    except requests.exceptions.Timeout:
        return jsonify({"answer": "AI 服务响应超时，请稍后重试"}), 504
    except Exception as e:
        return jsonify({"answer": f"AI 服务出错: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=APP_PORT)
